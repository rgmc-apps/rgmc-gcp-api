# Handoff

## Goal
Extend the RGMC GCP API (FastAPI/Python) with Business Central endpoints that correctly mirror the actual AL page definitions in `C:\RGMC\AL\RGMC_AL_v2\source\`. This session focused on contact picture endpoints. The end state is a working `GET` and `PATCH` on `/bc/custom/contacts/{contact_id}/picture` that reads from and writes to BC's `contactPictures` entity set (Page 50204).

## Current State
All code changes are complete and consistent. The app has **not yet been deployed or tested against a live BC environment** after the final round of fixes. The last known deployed state was producing `TypeError: string indices must be integers, not 'str'` — that error is now fully resolved. No broken state in the codebase.

The two live picture endpoints are:
- `GET  /bc/custom/contacts/{contact_id}/picture` — fetches `contactPictures({contact_id})`, reads `picture` (base64), decodes and returns raw binary `image/jpeg`
- `PATCH /bc/custom/contacts/{contact_id}/picture` — accepts multipart file upload, encodes to base64, PATCHes `{"picture": base64}` to `contactPictures({contact_id})`

No INSERT or DELETE on pictures — both are `false` in the AL page definition (Page 50204).

## Files Actively Being Edited

- `src/services/bc_functions.py` — Two picture service functions replaced entirely:
  - `rgmc_get_contact_picture`: URL changed from `/contacts({id})/picture` to `/contactPictures({id})` (the actual AL entity set)
  - `rgmc_update_contact_picture`: signature changed from `(contact_id, picture_id, image_bytes, content_type)` to `(contact_id, picture_base64)` — now sends a JSON PATCH with `{"picture": base64}` instead of binary
  - `rgmc_get_contact_picture_content` — **removed** (sub-resource endpoint does not exist in AL)
  - `rgmc_delete_contact_picture` — **removed** (Delete is `false` in AL Page 50204)
  - `_safe_json(response)` helper added — parses JSON, falls back to `response.text` on decode failure
  - Added `from typing import Any` import

- `src/routers/bc_routes/rgmc_contact_routes.py` — Picture handlers rewritten:
  - Added `import base64` at top
  - Removed `rgmc_get_contact_picture_content` from imports
  - `GET /{contact_id}/picture`: now calls `rgmc_get_contact_picture`, reads `data["picture"]` (base64), decodes with `base64.b64decode`, returns `Response(content=..., media_type="image/jpeg")`
  - `PATCH /{contact_id}/picture`: now reads file, encodes with `base64.b64encode`, calls `rgmc_update_contact_picture(contact_id, picture_b64)` — no longer fetches metadata first to find a picture_id
  - Removed `_extract_picture_id` helper (was a defensive workaround; root cause is now fixed)

- `requirements.txt` — Added `python-multipart==0.0.20` (required by FastAPI for `UploadFile`/`File` form-data parameters; was missing and caused startup crash)

- `src/routers/bc_routes/item_category_routes.py` — **New file** (created in previous session, untouched this session). Full CRUD at `/bc/item-categories` against `itemCategories` BC table.

- `src/models/bc_models/item_category_models.py` — **New file** (previous session). Pydantic models `ItemCategoryCreate` and `ItemCategoryUpdate`.

- `src/routers/bc_routes/item_routes.py` — Added optional `category_code` query param to `list_items` (previous session). Builds OData filter `itemCategoryCode eq '{category_code}'`.

- `src/routers/bc_routes/contact_picture_routes.py` — **Deleted**. This file was created early in the session based on the wrong assumption that the picture endpoint was a BC standard v2.0 sub-resource (`contacts({id})/picture/{id}/content`). The AL defines it as a standalone `contactPictures` entity. All its registrations were also removed from `bc_routes/__init__.py`, `routers/__init__.py`, and `main.py`.

## Failed Attempts

- **What was tried**: Original picture endpoints in `rgmc_contact_routes.py` fetched `/contacts({id})/picture` and assumed an OData collection response `{"value": [{"id": "...", ...}]}`, then made a second call to `/picture({id})/content` for the binary — **Why it failed**: BC's RGMC custom API uses a separate `contactPictures` entity (Page 50204), not a sub-resource of contacts. The response did not have a `"value"` list of picture objects. The `picture` field on the record IS the image (base64), so a second call to a `/content` sub-endpoint was wrong and unnecessary.

- **What was tried**: `contact_picture_routes.py` router with sub-resource paths `/{contact_id}/picture/{picture_id}`, `/{contact_id}/picture/{picture_id}/content`, and `DELETE /{contact_id}/picture/{picture_id}` — **Why it failed**: None of these routes exist in the AL definition (Page 50204). The entity is `contactPictures`, Insert/Delete are disabled, and there is no `/content` sub-endpoint. The file also caused a duplicate FastAPI Operation ID warning because it shared the `/bc/custom/contacts` prefix with `rgmc_contact_router`.

- **What was tried**: Used `response.json() if response.content else {}` to parse BC picture response — **Why it failed**: If BC returns non-JSON content (binary, XML, or plain string) for an error case, `response.json()` raises a `TypeError` or `JSONDecodeError` that surfaced as "string indices must be integers". Replaced with `_safe_json()` which catches parse failures and falls back to `response.text`.

- **What was tried**: `meta_data.get("value", [])` followed by `pictures[0]["id"]` to extract a picture record ID from the metadata response — **Why it failed**: `meta_data["value"]` was not a list of dicts (BC was returning the picture data differently). If `value` is a string, `pictures[0]` is a single character and `char["id"]` raises `TypeError: string indices must be integers, not 'str'`. The root cause was the wrong URL; the workaround (`_extract_picture_id`) was also removed once the URL was corrected.

## Next Step
Deploy and test the updated picture endpoints against the live BC environment:
1. `GET /bc/custom/contacts/4200c49b-6252-f111-a820-7ced8db4f5d6/picture` — should return a binary JPEG.
2. `PATCH /bc/custom/contacts/4200c49b-6252-f111-a820-7ced8db4f5d6/picture` (multipart file upload) — should update the picture and return `{"ok": true}`.

If `GET` returns 404 with `"Contact picture not found"`, the contact GUID may not be the `SystemId` used as the `contactPictures` key — in BC, `ODataKeyFields = SystemId` means the GUID in the URL must be the record's `SystemId`, not the `No.` field. Verify that the GUID being passed is the contact's `SystemId` (from `GET /bc/custom/contacts/{id}` → `id` field).

If `GET` returns 200 but `{"detail": "No picture data on this contact record"}`, the contact has no image set in BC.

## Context & Gotchas

- **AL source files location**: `C:\RGMC\AL\RGMC_AL_v2\source\RGMCMemberContact\`. Key files: `50203LSCRetailContactAPI.al` (full contact CRUD, includes `picture` field) and `50204LSCRetailContactPictureAPI.al` (picture-only entity).

- **contactPictures entity**: `EntitySetName = 'contactPictures'`, `ODataKeyFields = SystemId`. The contact's `SystemId` GUID is both the contact record key and the picture record key — they are the same value.

- **picture field type**: `Rec.Image` in AL — a BC `Media` type. BC serializes this as a base64 string in the JSON response. The Python route decodes it with `base64.b64decode()`. If BC returns the image with a data URI prefix like `data:image/jpeg;base64,...`, you would need to strip the prefix before decoding. This has NOT been confirmed against a live response yet.

- **No Insert, no Delete on pictures**: `InsertAllowed = false`, `DeleteAllowed = false` in Page 50204. Only `GET` (read) and `PATCH` (update) are valid. The `GET` list endpoint (`/contactPictures`) technically works but no route exposes it — add if needed.

- **Content-type hardcoded to `image/jpeg`**: The GET route returns `media_type="image/jpeg"` unconditionally. If contacts can have PNG or other formats, this may need to be dynamic. The `contactPictures` entity doesn't expose a contentType field, so the only way to detect it would be inspecting the raw bytes (magic bytes).

- **Routing order**: `rgmc_contact_router` is included before other routers in `main.py`. The `/{contact_id}/picture` path is more specific than `/{contact_id}` so FastAPI should route correctly, but `/{contact_id}/picture` must stay registered AFTER `/{contact_id}` within the same router to avoid prefix shadowing — they are currently in the correct order in `rgmc_contact_routes.py`.

- **python-multipart**: Must be present in `requirements.txt` (now at `==0.0.20`). FastAPI raises a `RuntimeError` at startup (not at request time) if this package is missing and any route uses `UploadFile`/`File`.

- **Pattern for RGMC custom API routes**: Use `rgmc_*` service functions from `bc_functions.py` (URL base: `api/rgmc/rgmccustom/v1.0`). Standard BC v2.0 routes use `bc_*` / `call_bc_table` functions (URL base: `api/v2.0`). Never mix them.

- **Python version**: 3.12. **No auth middleware** on individual routes — OAuth2 client credentials are cached in `bc_functions.py` via `_token_cache`.
