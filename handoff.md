# Handoff

## Goal

Two parallel goals:

**Goal 1 — rgmc-gcp-api smoke tests**: Verify that the committed RGMC custom API endpoints work correctly against the live Business Central environment. All code is committed on `main`. No code changes needed — this is purely deploy + test.

**Goal 2 — rgmc-bc-api standalone project**: A new standalone FastAPI project was created at `C:\claude\rgmc-bc-api` that contains only the Business Central endpoints extracted from `rgmc-gcp-api`. It needs to be initialized as a git repo, have its `.env` filled in, and be verified that it starts up cleanly.

## Current State

### rgmc-gcp-api (C:\RGMC\Source\git\rgmc-gcp-api)

All code is clean, committed, on `main`, up to date with `origin/main`. Only `.claude/settings.local.json` is modified (unrelated to API). The working tree is otherwise clean.

**What is implemented and committed (never tested against live BC):**

- `GET/PATCH /bc/custom/contacts/{contact_id}/picture` — fetches `contactPictures({id})`, decodes base64, returns binary image; PATCH uploads multipart file and encodes to base64
- `GET /bc/custom/contacts/{contact_id}/picture/debug` — debug dump: bc_http_status, b64 length, hex header, decoded bytes, detected media type
- `GET /bc/custom/contacts/{contact_id}/brand-tags` — lists all brand tags via `contacts({id})/contactBrandTags`
- `POST /bc/custom/contacts/{contact_id}/brand-tags` — adds `{"brandCode": "..."}`
- `DELETE /bc/custom/contacts/{contact_id}/brand-tags/{tag_id}` — removes tag
- `GET /bc/custom/item-prices` — lists prices with optional `product_no`, `on_date`, `filter`
- `GET /bc/custom/item-prices/active?product_no=...&on_date=YYYY-MM-DD` — single active price
- `GET|POST|PATCH|DELETE /bc/sales-orders` — sales orders (frontend-friendly field names, mapped in-route)
- `GET|POST|PATCH|DELETE /bc/custom/sales-orders` — sales orders (RGMC-native field names, no mapping)
- Error email middleware — on 500/502, fires `notify_error()` in daemon thread

**Recent commits since last handoff:**
- `5759e16` added email sending (error notification middleware in `src/main.py`)
- `bd04291` added sales line number to `sales_order_routes.py` and `sales_return_order_routes.py`
- `40d104d` removed top results for api
- `7976911` improved item price endpoints
- `1bd6983` added top filter for BC endpoints

### rgmc-bc-api (C:\claude\rgmc-bc-api)

**New standalone project created this session.** 43 files written. NOT a git repo yet. NOT tested. No `.env` file yet.

**What it contains:**
- Exact copy of all BC endpoints, models, and services from `rgmc-gcp-api`
- No SBIC/BigQuery/MSSQL/tradeportal code
- `requirements.txt` trimmed to 9 packages (fastapi, uvicorn, pydantic, requests, python-multipart, oauthlib, email-validator, starlette)
- `config.py` — BC-only env vars (no MSSQL, no BigQuery)
- `src/mappings.py` — minimal stub (`module_mappings: dict = {}`) to satisfy `send_mail` import
- `.env.example` — all env vars documented
- `compose.yaml` — includes `env_file: .env`
- Same `src/` layout as `rgmc-gcp-api`: `config.py`, `logger.py`, `gunicorn_config.py`, `main.py`, `types_py.py`, `mappings.py`, `models/bc_models/`, `routers/bc_routes/`, `services/`

**Route inventory in rgmc-bc-api:**
- `/bc` — token, companies, dimensions, brands, departments, contacts (standard v2.0)
- `/bc/items`, `/bc/customers`, `/bc/sales-credit-memos` — standard v2.0 CRUD
- `/bc/sales-orders` — v2.0-style CRUD with frontend-friendly field names
- `/bc/item-categories` — v2.0 CRUD
- `/bc/custom/retail-customers` — RGMC Pag50200
- `/bc/custom/sales-return-orders` + lines — RGMC Pag50201/50202
- `/bc/custom/contacts` + picture + brand-tags — RGMC Pag50203/50204/50209
- `/bc/custom/items`, `/bc/custom/item-families` — RGMC Pag50205/50206
- `/bc/custom/item-prices` + active + cache — RGMC Pag50210
- `/bc/custom/sales-orders` + lines — RGMC Pag50216/50217

## Files Actively Being Edited

No files are mid-edit in `rgmc-gcp-api`. All changes are committed.

**New files created in `C:\claude\rgmc-bc-api` this session (all new, none mid-edit):**
- `Dockerfile` — identical to source project
- `compose.yaml` — with `env_file: .env` added
- `requirements.txt` — trimmed to BC-only deps
- `.env.example` — all env vars documented
- `__init__.py` — empty root marker
- `src/__init__.py`, `src/config.py`, `src/logger.py`, `src/gunicorn_config.py`, `src/types_py.py`, `src/mappings.py` — framework files, BC-only config
- `src/main.py` — registers all 13 BC routers + process-time header + error email middleware
- `src/models/__init__.py`, `src/models/bc_models/__init__.py` — model package init
- `src/models/bc_models/*.py` — 11 model files (exact copies)
- `src/routers/__init__.py`, `src/routers/health.py` — router package
- `src/routers/bc_routes/__init__.py` — exports all 13 route routers
- `src/routers/bc_routes/*.py` — 13 route files (exact copies)
- `src/services/bc_functions.py` — exact copy
- `src/services/send_mail.py` — copy with `oauthlib.uri_validate` import removed (was unused)

## Failed Attempts

*(From previous sessions — still relevant)*

- **What was tried**: Fetching contact picture via `/contacts({id})/picture` with sub-endpoint `/picture({id})/content` — **Why it failed**: BC's RGMC custom API uses a separate `contactPictures` entity (Page 50204). The `picture` field on the record IS the base64 image; no `/content` sub-endpoint exists.

- **What was tried**: `response.json()` for BC picture responses — **Why it failed**: BC can return non-JSON on errors; raises `JSONDecodeError` surfacing as `TypeError`. Replaced with `_safe_json()` helper in `bc_functions.py`.

- **What was tried**: `yourReference` field on sales orders — **Why it failed**: BC v2.0 returned 400 "The property 'yourReference' does not exist on type 'Microsoft.NAV.salesOrder'".

- **What was tried**: Item price filter with only `startingDate le {date}` — **Why it failed**: BC returned 400. Requires both bounds: `startingDate le on_date AND (endingDate ge on_date OR endingDate eq 0001-01-01)`.

*(No new failures this session — the session was a file creation task, no runtime errors.)*

## Next Step

**For rgmc-bc-api — verify it starts cleanly:**

1. Copy `.env.example` to `.env` and fill in the BC credentials:
   ```
   BC_CLIENT_ID=1dbc90f8-3822-4c1b-b4f6-5156971b7212
   BC_CLIENT_SECRET=<secret>
   BC_TENANT_ID=ca3ca144-09d9-42dd-920a-c72aedd54dd6
   BC_ENVIRONMENT=UAT
   BC_COMPANY=CGI
   ```
2. Run `pip install -r requirements.txt` and then `uvicorn src.main:api --port 8080` from `C:\claude\rgmc-bc-api`
3. Hit `http://localhost:8080/swagger` — confirm all 13 route groups appear
4. Optionally `git init && git add . && git commit -m "initial BC API project"` to track it

**For rgmc-gcp-api — smoke tests (deploy first):**
Run these against the deployed API after the next Cloud Run deploy:
1. `GET /bc/custom/contacts/4200c49b-6252-f111-a820-7ced8db4f5d6/picture/debug` — check `decoded_bytes` > 1000; if small, AL page 50204 Text field is truncating
2. `GET /bc/custom/contacts/4200c49b-6252-f111-a820-7ced8db4f5d6/picture` — should return binary JPEG
3. `PATCH /bc/custom/contacts/4200c49b-6252-f111-a820-7ced8db4f5d6/picture` (multipart) — should return `{"ok": true}`
4. `GET /bc/custom/contacts/{contact_id}/brand-tags` — verify `contactBrandTags` sub-resource works
5. `GET /bc/custom/item-prices/active?product_no=ITEM001&on_date=2026-06-08` — verify date filter works

## Context & Gotchas

**API prefixes (critical):**
- `/bc/*` → standard BC `api/v2.0` — use `bc_*` / `call_bc_table` service functions
- `/bc/custom/*` → RGMC in-house `api/rgmc/rgmccustom/v1.0` — use `rgmc_*` / `call_rgmc_table` service functions. Never mix.

**AL source location**: `C:\RGMC\AL\RGMC_AL_v2\source\`
Key pages: 50203 (contacts), 50204 (contact pictures — Insert/Delete = false), 50209 (brand tags), 50210 (item prices), 50216/50217 (sales order header/lines).

**contactPictures OData key**: The contact GUID passed in the URL must be the contact's `SystemId`, not the `No.` field. If GET returns 404, verify the GUID is from `GET /bc/custom/contacts/{id}` → `id` field.

**Picture field truncation risk**: AL page 50204 may have a `Text[X]` length limit. The debug endpoint reports `decoded_bytes` — if < 100, the base64 is truncated in AL. Fix requires increasing the field length in the AL page.

**endingDate = 0001-01-01**: BC stores a blank ending date as `0001-01-01` (meaning open-ended). The item price filter always includes `(endingDate ge {date} or endingDate eq 0001-01-01)`.

**rgmc-bc-api `send_mail.py`**: The original `send_mail.py` imported `from oauthlib.uri_validate import port` (unused). This import was removed in the standalone copy. `oauthlib` package is still in `requirements.txt` because the package may be needed transitively, but the specific unused import is gone.

**rgmc-bc-api `mappings.py`**: Is a minimal stub (`module_mappings: dict = {}`). The original `mappings.py` is 336 lines of SBIC/BigQuery table mappings — all irrelevant to BC. Only `module_mappings` is referenced in `send_mail.send_mail()`.

**Python version**: 3.12. No per-route auth middleware — OAuth2 client credentials are cached in `_token_cache` in `bc_functions.py`.

**Deployment (rgmc-gcp-api)**: Docker → Google Cloud Run. Build with `gcloud builds submit --tag gcr.io/<PROJECT_ID>/rgmc-gcp-api`, deploy with `gcloud run deploy rgmc-gcp-api ...`. Swagger UI at `/swagger`.

**Two sales-order route sets in both projects:**
- `/bc/sales-orders` — uses `SalesOrderCreate` (frontend-friendly names: `customerNumber`, `externalDocumentNumber`). Maps them in-route to BC field names before calling `rgmc_create_record`.
- `/bc/custom/sales-orders` — uses `RgmcSalesOrderCreate` (RGMC-native names: `sellToCustomerNo`, `externalDocumentNo`). No mapping needed.
