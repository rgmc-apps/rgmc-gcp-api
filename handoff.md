# Handoff

## Goal

**Goal 1 — rgmc-gcp-api smoke tests**: Verify that the committed RGMC custom API endpoints work correctly against the live Business Central environment. All code is committed on `main`. No code changes needed — this is purely deploy + test.

**Goal 2 — DROPPED (2026-10-01)**: The handoff previously described a "new standalone FastAPI project" at `C:\claude\rgmc-bc-api` needing git init + `.env` + startup verification. On resume, that path was found to actually be the real `rgmc-apps/rgmc-bc-api` production repo (git history with PRs, `staging` branch, GitHub remote, commits up to "added buffer changes" on 2026-10-01) — not an empty extraction scaffold. Whatever scaffold work the original handoff referred to is gone/superseded. User confirmed: drop Goal 2 entirely, do not touch that directory as part of this work.

**Goal 3 — Generic direct-read query endpoints (completed previous session)**: Added two new router modules to `rgmc-gcp-api` for querying BigQuery and all MSSQL databases directly by table without bespoke route code per table.

## Current State

### rgmc-gcp-api (C:\RGMC\Source\git\rgmc-gcp-api)

All code is clean on `main`. Working tree is clean.

**New endpoints added this session (wired and complete):**

**BigQuery** (`src/routers/bigquery_routes/bigquery_routes.py`):
- `GET /bigquery_routes/by_table/value?table_name=&where_column=&where_value=`
- `GET /bigquery_routes/by_table/latest?table_name=&date_column=` (hardcoded LIMIT 100)

**MSSQL** (`src/routers/mssql_routes/mssql_routes.py`):
- `GET /{db_name}/by_table/value?table_name=&where_column=&where_value=`
- `GET /{db_name}/by_table/latest?table_name=&date_column=&number_of_rows=100`
- `db_name` must be a key from `src/mappings.py > db_mappings`: `sbic`, `tradeportal`, `travelandexpense`, `creative`, `accounting`, `production`, `masterfile`

**Previously implemented and committed (never tested against live BC):**

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

### rgmc-bc-api (C:\claude\rgmc-bc-api)

Out of scope — see Goal 2 note above. This is the real production repo, not a scratch project; leave it alone unless separately instructed.

## Files Actively Being Edited

No files are mid-edit. All changes are complete.

**Created this session in `rgmc-gcp-api`:**
- `src/routers/bigquery_routes/bigquery_routes.py` — two BigQuery read endpoints using `pandas_gbq.read_gbq` with `config.bigquery_dataset_id` / `config.bigquery_project_id`
- `src/routers/bigquery_routes/__init__.py` — exports `bigquery_router`
- `src/routers/mssql_routes/mssql_routes.py` — generic MSSQL router parameterized by `db_name`. Linter added `_invalidate_engine`, `_handle_db_error`, and 403 handling for login-failed / cannot-open-database errors. Engines cached per `db_name` in module-level `_engines` dict
- `src/routers/mssql_routes/__init__.py` — exports `mssql_router`
- `src/routers/sbic_routes/sbic_routes.py` — **deleted**; was an intermediate sbic-specific router replaced by the generic `mssql_routes` version

**Modified this session in `rgmc-gcp-api`:**
- `src/routers/__init__.py` — added `from .bigquery_routes import bigquery_router` and `from .mssql_routes import mssql_router`
- `src/main.py` — added `bigquery_router` and `mssql_router` to the import line and `api.include_router()` calls inside the try block

## Failed Attempts

*(From previous sessions — still relevant)*

- **What was tried**: Fetching contact picture via `/contacts({id})/picture` with sub-endpoint `/picture({id})/content` — **Why it failed**: BC's RGMC custom API uses a separate `contactPictures` entity (Page 50204). The `picture` field on the record IS the base64 image; no `/content` sub-endpoint exists.
- **What was tried**: `response.json()` for BC picture responses — **Why it failed**: BC can return non-JSON on errors; raises `JSONDecodeError` surfacing as `TypeError`. Replaced with `_safe_json()` helper in `bc_functions.py`.
- **What was tried**: `yourReference` field on sales orders — **Why it failed**: BC v2.0 returned 400 "The property 'yourReference' does not exist on type 'Microsoft.NAV.salesOrder'".
- **What was tried**: Item price filter with only `startingDate le {date}` — **Why it failed**: BC returned 400. Requires both bounds: `startingDate le on_date AND (endingDate ge on_date OR endingDate eq 0001-01-01)`.

*(This session — router refactors)*
- **What was tried**: Created a sbic-specific router at `src/routers/sbic_routes/sbic_routes.py` with prefix `/sbic` — **Why it failed**: User requested the same endpoints for all databases in `db_mappings`, making a single-db router the wrong abstraction. Replaced with `/{db_name}/...` pattern.
- **What was tried**: Placed the generic router under `sbic_routes/` — **Why it failed**: User asked to move it to `mssql_routes/`. File relocated and old one deleted.

## Next Step

**Deploy is on hold** — user chose not to deploy in-session (deploying affects shared infra). Deploy command is ready below for the user to run themselves (gcloud CLI isn't usable from this shell — `gcloud` invocation errors with "Python was not found", so it can't be run by Claude here anyway).

```bash
gcloud auth login
gcloud auth configure-docker us-central1-docker.pkg.dev
gcloud builds submit --tag gcr.io/<PROJECT_ID>/rgmc-gcp-api
gcloud run deploy rgmc-gcp-api \
  --image gcr.io/<PROJECT_ID>/rgmc-gcp-api \
  --platform managed \
  --region us-central1 \
  --port 8080 \
  --set-env-vars BC_ENVIRONMENT=Production,BC_COMPANY=RGMC \
  --set-secrets BC_CLIENT_SECRET=bc-client-secret:latest,MSSQL_PASSWORD=mssql-password:latest \
  --allow-unauthenticated
```
`<PROJECT_ID>` above is the actual GCP project id (not the app's internal `PROJECT_ID` env var, which defaults to `RGMC0001`) — not recorded anywhere in this repo, user needs to fill it in.

**After deploy — smoke tests:**
1. `GET /bc/custom/contacts/4200c49b-6252-f111-a820-7ced8db4f5d6/picture/debug` — check `decoded_bytes` > 1000
2. `GET /bc/custom/item-prices/active?product_no=ITEM001&on_date=2026-06-08` — verify date filter works

**Potential follow-ups for the new endpoints (not yet requested):**
1. Add a `number_of_rows` query param to `GET /bigquery_routes/by_table/latest` (currently hardcoded `LIMIT 100`, unlike the MSSQL equivalent which accepts `number_of_rows`)
2. Add auth/rate limiting to `bigquery_routes` and `mssql_routes` (other routes use `rate_limit` from `src/routers/sbic_routes/rate_limiter.py`)

## Context & Gotchas

**New MSSQL router details:**
- `mssql_router` has no `prefix` set — `db_name` path segment acts as the prefix (e.g. `/sbic/by_table/value`)
- `bigquery_router` uses prefix `/bigquery_routes`
- `where_value` in MSSQL endpoint is bound via SQLAlchemy named parameter (`:where_value`) — safe from injection. `table_name`, `where_column`, `date_column` are interpolated as identifiers — acceptable for internal use
- BigQuery `where_value` is string-interpolated (single-quoted). If endpoints become externally exposed, switch to BigQuery parameterized queries
- MSSQL engines are cached in module-level `_engines` dict; `_invalidate_engine()` removes a broken cached engine on login failure so next request retries

**API prefixes (critical):**
- `/bc/*` → standard BC `api/v2.0` — use `bc_*` / `call_bc_table` service functions
- `/bc/custom/*` → RGMC in-house `api/rgmc/rgmccustom/v1.0` — use `rgmc_*` / `call_rgmc_table` service functions. Never mix.

**AL source location**: `C:\RGMC\AL\RGMC_AL_v2\source\`
Key pages: 50203 (contacts), 50204 (contact pictures — Insert/Delete = false), 50209 (brand tags), 50210 (item prices), 50216/50217 (sales order header/lines).

**endingDate = 0001-01-01**: BC stores a blank ending date as `0001-01-01` (meaning open-ended). The item price filter always includes `(endingDate ge {date} or endingDate eq 0001-01-01)`.

**Deployment (rgmc-gcp-api)**: Docker → Google Cloud Run. Build with `gcloud builds submit --tag gcr.io/<PROJECT_ID>/rgmc-gcp-api`, deploy with `gcloud run deploy rgmc-gcp-api ...`. Swagger UI at `/swagger`.

**Two sales-order route sets:**
- `/bc/sales-orders` — uses `SalesOrderCreate` (frontend-friendly names). Maps them in-route to BC field names before calling `rgmc_create_record`.
- `/bc/custom/sales-orders` — uses `RgmcSalesOrderCreate` (RGMC-native names). No mapping needed.
