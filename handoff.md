# Handoff

## Goal
Extend the RGMC GCP API (FastAPI/Python) with Business Central endpoints that correctly mirror the actual AL page definitions in `C:\RGMC\AL\RGMC_AL_v2\source\`. The broader goal is a fully working set of RGMC custom API endpoints for contacts (including picture and brand tags), items (including item prices), and sales orders — all routed through the correct RGMC custom API base (`api/rgmc/rgmccustom/v1.0`) rather than the standard BC v2.0 API.

## Current State

All committed code is clean and on `main`, up to date with `origin/main`. The working tree has one untracked file (see below).

### What is working and committed

**Contact picture endpoints** (all committed as of `a48a53f` and earlier):
- `GET /bc/custom/contacts/{contact_id}/picture` — fetches `contactPictures({contact_id})`, decodes base64 `picture` field, returns binary image with auto-detected media type
- `GET /bc/custom/contacts/{contact_id}/picture/debug` — raw BC response debug dump (bc_http_status, b64 length, hex header, decoded byte count, detected media type)
- `PATCH /bc/custom/contacts/{contact_id}/picture` — multipart file upload, base64-encodes and PATCHes `{"picture": base64}` to `contactPictures({contact_id})`
- Has truncation detection: if `decoded_bytes < _MIN_IMAGE_BYTES`, returns 502 with a note to check AL page 50204 Text field length
- **Not yet tested against live BC environment**

**Contact brand tag endpoints** (committed `01e5b7c`):
- `GET /bc/custom/contacts/{contact_id}/brand-tags` — lists all brand tags for a contact via `contacts({id})/contactBrandTags`
- `POST /bc/custom/contacts/{contact_id}/brand-tags` — adds a brand tag (`{"brandCode": "..."}`)
- `DELETE /bc/custom/contacts/{contact_id}/brand-tags/{tag_id}` — removes a brand tag
- **Not yet tested against live BC**

**Item price endpoints** (committed `01e5b7c`, fixed in `8e50a2e`):
- `GET /bc/custom/item-prices` — lists item prices, optional `product_no`, `on_date`, `filter` params
- `GET /bc/custom/item-prices/active?product_no=...&on_date=YYYY-MM-DD` — returns the single active price record
- OData filter uses both date bounds: `startingDate le {date} and (endingDate ge {date} or endingDate eq 0001-01-01)` — `0001-01-01` is BC's representation of a blank/open-ended ending date
- Registered in `main.py` and `bc_routes/__init__.py` as `rgmc_item_price_router`
- **Not yet tested against live BC**

**Sales order endpoints** (committed `01e5b7c`, updated in `054f489` and `f77ecca`):
- Full CRUD at `/bc/sales-orders` and `/bc/sales-orders/{order_id}/lines`
- As of `f77ecca`: routes now use `rgmc_create_record`, `rgmc_update_record`, `rgmc_delete_record`, `call_rgmc_table` (RGMC custom API, not BC v2.0)
- Field mapping in route handlers: `customerNumber` → `sellToCustomerNo`, `externalDocumentNumber` → `externalDocumentNo`
- `yourReference` removed from `SalesOrderCreate` (`054f489`) — BC v2.0 rejected it with 400: "The property 'yourReference' does not exist on type 'Microsoft.NAV.salesOrder'"
- Current models in use: `SalesOrderCreate` / `SalesOrderUpdate` from `src/models/bc_models/sales_order_models.py` (frontend-friendly names with in-route mapping)

### Untracked file (not committed, not wired up)

- `src/models/bc_models/rgmc_sales_order_models.py` — new Pydantic models using raw RGMC field names directly (`sellToCustomerNo`, `externalDocumentNo`, `number`, `lineDiscountPercent`, etc.). Contains `RgmcSalesOrderCreate`, `RgmcSalesOrderUpdate`, `RgmcSalesOrderLineCreate`, `RgmcSalesOrderLineUpdate`. This is **not referenced anywhere** — it appears to be a planned refactor to eliminate the in-route field mapping in `sales_order_routes.py` by using RGMC-native field names in the request body instead. Decision pending: wire it up (replacing `SalesOrderCreate`) or delete it.

## Files Actively Being Edited

No files are mid-edit. All changes are committed except the untracked file below.

- `src/models/bc_models/rgmc_sales_order_models.py` — **Untracked, uncommitted.** New models with RGMC-native field names. Not yet referenced by any route. Decide to wire up or delete.

## Failed Attempts

- **What was tried**: Original picture endpoints fetched `/contacts({id})/picture` and assumed `{"value": [{...}]}` OData collection response, then made a second call to `/picture({id})/content` — **Why it failed**: BC's RGMC custom API uses a separate `contactPictures` entity (Page 50204). The `picture` field on the record IS the image (base64); no `/content` sub-endpoint exists.

- **What was tried**: `contact_picture_routes.py` with sub-resource paths `/{contact_id}/picture/{picture_id}`, `/content`, and DELETE — **Why it failed**: None of these exist in AL Page 50204. Insert and Delete are `false`. Also caused duplicate FastAPI Operation ID warnings.

- **What was tried**: `response.json() if response.content else {}` to parse BC picture responses — **Why it failed**: BC can return non-JSON for error cases; `.json()` raises `JSONDecodeError` surfacing as `TypeError: string indices must be integers`. Replaced with `_safe_json()` helper that falls back to `response.text`.

- **What was tried**: `meta_data.get("value", [])` then `pictures[0]["id"]` to get picture record ID — **Why it failed**: When `value` is a string, `pictures[0]` is a single char and `char["id"]` raises `TypeError: string indices must be integers, not 'str'`. Root cause was wrong URL; entire workaround removed.

- **What was tried**: `yourReference` field on `SalesOrderCreate` sent to BC v2.0 sales orders — **Why it failed**: BC returned 400 "The property 'yourReference' does not exist on type 'Microsoft.NAV.salesOrder'". This field does not exist in the standard v2.0 API.

- **What was tried**: Item price filter only using `startingDate le {date}` — **Why it failed**: BC returned 400; the effectivity window requires both bounds: `startingDate le on_date AND (endingDate ge on_date OR endingDate eq 0001-01-01)`.

## Next Step

**Decision required on `rgmc_sales_order_models.py`** — then deploy and test.

Option A (wire it up): Replace `SalesOrderCreate`/`SalesOrderUpdate` in `sales_order_routes.py` with `RgmcSalesOrderCreate`/`RgmcSalesOrderUpdate` from `rgmc_sales_order_models.py`. This removes the in-route field-mapping (`customerNumber` → `sellToCustomerNo`) since the model already uses RGMC native names. Then commit and deploy.

Option B (delete it): Delete `rgmc_sales_order_models.py` and keep the current approach (frontend-friendly model + in-route mapping). Commit the deletion, then deploy.

After that decision: deploy and run these smoke tests:
1. `GET /bc/custom/contacts/4200c49b-6252-f111-a820-7ced8db4f5d6/picture/debug` — check `decoded_bytes` is large (> 1000); if small, AL page 50204 Text field is truncating
2. `GET /bc/custom/contacts/4200c49b-6252-f111-a820-7ced8db4f5d6/picture` — should return binary JPEG
3. `PATCH /bc/custom/contacts/4200c49b-6252-f111-a820-7ced8db4f5d6/picture` (multipart) — should return `{"ok": true}`
4. `GET /bc/custom/contacts/{contact_id}/brand-tags` — verify `contactBrandTags` sub-resource works
5. `GET /bc/custom/item-prices/active?product_no=ITEM001&on_date=2026-06-08` — verify date filter works

## Context & Gotchas

- **API prefixes**: `/bc/*` → standard BC `api/v2.0`. `/bc/custom/*` → RGMC in-house extensions at `api/rgmc/rgmccustom/v1.0`. Never mix. Service functions: `bc_*` / `call_bc_table` for v2.0; `rgmc_*` / `call_rgmc_table` for RGMC custom.

- **AL source location**: `C:\RGMC\AL\RGMC_AL_v2\source\`. Key files: `50203LSCRetailContactAPI.al` (full contact CRUD, includes `picture` field), `50204LSCRetailContactPictureAPI.al` (picture-only entity, Insert/Delete `false`), `50209` (contactBrandTags sub-resource), `50210` (item prices), `50216/50217` (sales order header/lines).

- **contactPictures entity**: `EntitySetName = 'contactPictures'`, `ODataKeyFields = SystemId`. The contact GUID passed in the URL must be the contact's `SystemId`, not the `No.` field. If `GET /picture` returns 404, verify the GUID is the contact's `SystemId` (from `GET /bc/custom/contacts/{id}` → `id` field).

- **picture field**: BC serializes `Rec.Image` (Media type) as base64 in JSON. If BC returns a data URI prefix (`data:image/jpeg;base64,...`), strip it before decoding. Not confirmed against live BC yet. Routes use `_detect_media_type()` on raw bytes for dynamic content-type.

- **Truncation risk**: AL page 50204 may have a `Text[X]` field length limit on the `picture` field. The debug endpoint (`/picture/debug`) reports `decoded_bytes` — if it's tiny (< 100), the base64 is being truncated in AL. Fix requires increasing the field length in the AL page.

- **Brand tag OData key**: `contactBrandTags({tag_id})` — the `tag_id` is the BC record `SystemId` returned from the GET list response.

- **Item price endingDate**: BC stores a blank ending date as `0001-01-01`. The OData filter `endingDate eq 0001-01-01` catches open-ended prices. Without this, open-ended prices (most common) would be excluded from the active price lookup.

- **Sales order field mapping**: `sales_order_routes.py` currently maps `customerNumber` → `sellToCustomerNo` and `externalDocumentNumber` → `externalDocumentNo` in-route before calling `rgmc_create_record` / `rgmc_update_record`. The untracked `rgmc_sales_order_models.py` would eliminate this mapping by using native field names in the request body directly.

- **python-multipart**: Required for `UploadFile`/`File` in FastAPI. Already in `requirements.txt` at `==0.0.20`. FastAPI raises `RuntimeError` at startup if missing.

- **`_safe_json(response)`**: Helper in `bc_functions.py` (line ~190). Tries `response.json()`, falls back to `response.text` on any parse failure. Use it for all RGMC custom API calls that return body content.

- **Python version**: 3.12. No per-route auth middleware — OAuth2 client credentials are cached in `_token_cache` in `bc_functions.py`.

- **Deployment**: Docker-based, deployed to Google Cloud Run. Build with `gcloud builds submit --tag gcr.io/<PROJECT_ID>/rgmc-gcp-api`, deploy with `gcloud run deploy rgmc-gcp-api ...`. Swagger UI at `/swagger`.
