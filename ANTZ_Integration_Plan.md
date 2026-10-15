# ANTZ RFID SCM Integration — Findings, Plan & Open Questions

Source document: `ISD_RGMC ANTZ SCM_v1.0.1.pdf` (Inchz IoT, v1.0.1, dated 5-Oct-2026).
Status of that document: **not yet formally accepted** — the Acceptance page (§4.0) has RGMC Group's
approval block blank (only Inchz IoT's Prepared/Reviewed signatures are filled in). Treat all of the
below as planning against a draft spec until RGMC signs off.

Scope note: the ISD does not state which RGMC Group company/site this integration covers. Given the
subject matter (Goods Receiving/Issuance, warehouse, RFID, PO/TO), this is almost certainly
**Suncoast Brands International Corp. (SBIC)** (FMCG distribution/warehousing) and/or
**Manila Taste Curators Inc.** (shared SBIC sales ops), but this must be confirmed — see Q&A list below.

---

## 1. What RGMC needs to request from ANTZ (Inchz IoT)

### 1.1 Access & credentials (applies to both `rgmc-gcp-api` and `rgmc-bc-api`)

| # | Item | Why it's needed | ISD reference |
|---|---|---|---|
| 1 | **UAT base URL** (`{{baseUrl}}`) | REST calls in non-prod | §1.1, §3.1.2 |
| 2 | **Production base URL** (`{{baseUrl}}`) | REST calls in prod | §1.1 |
| 3 | **Username + password** for `GET /api/v3/Authenticate/GetToken` (separate pair per environment — UAT and Prod cannot share) | Bearer-token auth for every REST call | §3.1.2 |
| 4 | **`x-api-key`** value, issued by "ANTZ System Manager" | Sent alongside bearer token on every request per the header table in §3.1.1; doc marks it "Optional" but doesn't say when it's actually required — must clarify | §3.1.1 |
| 5 | **WebSocket host:port**, if RGMC is in scope for the POS RFID stream | `ws://{{host}}:{{port}}` handshake, `protocol: "json"`, `version: "1.0"`; an API key must also be passed on this connection (header or query param, unspecified which) | §3.2 |
| 6 | **Token expiry/TTL value** | Doc says tokens expire and a refresh mechanism is required, but never states the duration — needed to size our token-cache/refresh logic | §3.1.2 Notes |
| 7 | **IP allowlist info — both directions**: (a) what IP(s)/CIDR ANTZ's inbound webhook calls will originate from, so we can firewall our receiver; (b) whether ANTZ enforces IP allowlisting on their side, and if so, our Cloud Run egress IP(s) to give them (Cloud Run has no static egress IP by default — would need Cloud NAT) | "IP whitelisting may be enforced depending on customer configuration" | §3.1.2, §3.2 Notes |
| 8 | **The actual webhook receiver URLs RGMC will host**, to hand back to ANTZ | The ISD literally shows `Endpoint: https://{baseURL}/endpoints (from RGMC)` as a placeholder for all 3 `[RGMC]` push endpoints — RGMC must design, build, and supply these URLs | §3.4.4, §3.5.9, §3.7.3 |
| 9 | **The API key RGMC will issue to ANTZ** for those 3 inbound webhooks (`Authentication: API Key`) — RGMC generates this, not ANTZ | Same sections | — |
| 10 | Whether a **Postman collection / sandbox test tool** exists | Doc only gives per-endpoint request/response samples; a collection would de-risk implementation significantly | implied by §1.1 "Postman, cURL" |

### 1.2 Master-data & business-rule clarifications to request

| # | Question | Why |
|---|---|---|
| 11 | Confirm **adjustment type list stability** — is `GET /AdjustmentType` the source of truth RGMC should pull and cache, or will ANTZ notify us of changes? | §3.3.1, needed to build the `adjustmentTypeCode → BC Item Journal/bin` mapping table referenced in §3.7.3 |
| 12 | Confirm **UOM code matching rules** — does `itemUomCode` sent to ANTZ have to exactly match a code already registered on that Item Master in ANTZ (via `itemUomList`), or will ANTZ auto-create unknown UOM codes? | §3.3.3's "Base UOM" notes + §3.4.4/§3.5.9's "all quantities strictly in Base UOM" |
| 13 | Confirm **timestamp format/timezone** for all timestamps (UTC vs Asia/Manila), since `approvedDate` sample uses a `Z` suffix (UTC) but other datetime samples (`createdDate`, etc.) have no offset at all | §3.7.3 payload sample vs. all GET response samples |
| 14 | Confirm **webhook retry/idempotency contract**: if RGMC's receiver times out, returns 5xx, or returns `success: false`, does ANTZ retry? With what backoff/max attempts? Is `transactionId`/`refNo` safe to use as a dedupe key on our side? | §3.4.4, §3.5.9, §3.7.3 — none of this is specified |
| 15 | Confirm **error response contract** ANTZ expects from our webhook receiver on validation failure (HTTP status code + body shape) — only the happy-path `{success:true, message:...}` sample is given | same sections |
| 16 | Confirm **"No Order Reversal" / "No Reversals" operational workaround** in writing: once an order is `CLOSE`d in ANTZ or a Transfer Order chamber-scan is committed, the only fix is a brand-new return/reversing document in BC — get this as a documented SOP, not just a footnote, since it affects BC process design | §3.4.4, §3.5.9 |
| 17 | Confirm **scope of the WebSocket/POS integration** — is this RGMC's responsibility at all, or purely between ANTZ and a separate POS vendor? If RGMC isn't building a POS, this whole §3.2 may be out of scope | §2.2, §3.2 |
| 18 | Confirm **rate limits beyond the stated batch-size-100 limits** (requests/min, requests/day) for both REST calls and webhook delivery volume | implied, not stated |
| 19 | Confirm which **RGMC company/site(s)** (BC company code) this integration covers, and get the actual `siteCode`/`entityCode`/`regionCode` values ANTZ expects us to use, since those are free-text codes ANTZ will store as-is | §1.3, §3.3.4 |
| 20 | Confirm **support/escalation contact and SLA** for API incidents, and the versioning/deprecation policy for this v3 API | general |
| 21 | Confirm whether RGMC needs to **pre-seed ANTZ with existing BC master data** (Items, Customers, Vendors, Sites, Adjustment Types) before go-live via the POST endpoints, or whether ANTZ will provide an initial bulk-load mechanism | §3.3.1–3.3.5 |

---

## 2. Execution plan — integrating ANTZ into `rgmc-gcp-api`

### 2.1 Architectural decisions (made for planning purposes — confirm before building)

- **This repo (`rgmc-gcp-api`) will own the ANTZ integration**, not `rgmc-bc-api`. Rationale: the user's
  ask targets this codebase, and `rgmc-gcp-api` already has its own complete `bc_functions.py` BC
  OAuth2 client and a full set of `bc_routes/*` CRUD routers (sales orders, items, customers, etc.) — so
  it can call BC directly without routing through `rgmc-bc-api`. **Known duplication risk**: both repos
  maintain separate BC client code; this integration will not resolve that, just build on the copy that
  lives here.
- **New ANTZ client module mirrors the existing `bc_functions.py` shape**: module-level token-cache
  dict + `threading.Lock()`, refresh N seconds before expiry, plain synchronous `requests` (matching
  this repo's existing convention — no `httpx` anywhere in it), tuple-style `(status, data)` returns on
  error so routers translate to `HTTPException`.
- **Inbound webhook auth copies `rgmc-bc-api`'s `X-Task-Secret` pattern** (this repo currently has *no*
  inbound auth mechanism at all — `sbic_routes/rate_limiter.py` is a 30s cooldown throttle, not
  authentication). New routes will do the same inline header check: reject with 403 if
  `X-Antz-Api-Key` header ≠ `config.ANTZ_WEBHOOK_API_KEY`.
- **No in-process scheduler** — neither repo uses APScheduler; both rely on Cloud Scheduler hitting
  plain HTTP endpoints. Any periodic ANTZ sync (e.g. re-pushing master data, polling for new BC
  POs/TOs to push) follows the same model: a `POST /antz/sync/...` endpoint triggered externally by
  Cloud Scheduler, same as `bigquery_bridge.py`'s `/customerpoul/runbridge/` pattern.
- **Open architecture question, not yet resolved**: BC has no native outbound-webhook mechanism.
  "BC must push POs and TOs prior to physical warehouse processing" (ISD §1.3) implies something in
  BC needs to *trigger* the Create Receiving Order / Create Transfer Order calls to ANTZ when a PO/TO
  is created or released. Two options to evaluate with the BC/AL team:
  - (a) A new AL event (`OnAfterInsert`/`OnAfterRelease` on Purchase/Transfer Header) calls out to a
    new `rgmc-gcp-api` endpoint synchronously or via an HTTP job queue entry; or
  - (b) `rgmc-gcp-api` polls BC on a schedule (Cloud Scheduler) for new/updated POs/TOs using the
    existing `custom_connector_*` style incremental-cursor pattern seen in `rgmc-bc-api`
    (`modified_from` param) and pushes any it hasn't sent yet.
  (a) is lower-latency and matches "BC must push... prior to physical warehouse processing"; (b) needs
  no AL changes. **Needs a decision with the BC/AL developer before Phase 4 below starts.**

### 2.2 New files/modules

```
src/routers/antz_routes/
  __init__.py                    # exports antz_router, antz_webhook_router
  antz_functions.py              # ANTZ REST client: token mgmt, generic get/post/put, cursor pagination helper
  antz_master_data_routes.py     # proxy/sync endpoints for Adjustment Type, Customer, Item Master, Site, Vendor
  antz_receiving_routes.py       # Create/Update/Get Receiving Order (BC PO <-> ANTZ)
  antz_outbound_routes.py        # Create/Update/Get Sales Order & Transfer Order, Get Picking/Delivery Order
  antz_inventory_routes.py       # Get Inventory by Details/SKU, Get Serial Details, Get Item Transactions
  antz_webhook_routes.py         # [RGMC] inbound: Push Receiving Order Status, Push Transfer Order Status,
                                  #                 Push Inventory Adjustment — API-key protected
```

Wire into `src/routers/__init__.py` and `src/main.py` the same way `bigquery_router`/`mssql_router`
were added (import + `api.include_router(...)`).

### 2.3 New environment variables (plain `os.getenv`, matching `src/config.py` convention)

| Variable | Purpose | Secret? |
|---|---|---|
| `ANTZ_ENVIRONMENT` | `UAT` or `Production` — selects which base URL to use (mirrors `BC_ENVIRONMENT`) | no |
| `ANTZ_BASE_URL_UAT` | `{{baseUrl}}` for UAT | no |
| `ANTZ_BASE_URL_PROD` | `{{baseUrl}}` for Production | no |
| `ANTZ_USERNAME` | `GetToken` username | yes (Secret Manager) |
| `ANTZ_PASSWORD` | `GetToken` password | yes (Secret Manager) |
| `ANTZ_API_KEY` | `x-api-key` header value | yes (Secret Manager) |
| `ANTZ_WEBHOOK_API_KEY` | Key RGMC issues to ANTZ; validated on the 3 inbound `[RGMC]` endpoints | yes (Secret Manager) |
| `ANTZ_SITE_CODE_<COMPANY>` or a mapping table | BC Site/Location → ANTZ `siteCode` mapping, if not 1:1 | no, but see §2.4 |
| `ANTZ_WS_HOST` / `ANTZ_WS_PORT` / `ANTZ_WS_API_KEY` | only if the WebSocket/POS scope applies to RGMC (Q17) | yes for key |

Add all of these to `README.md`'s Environment Variables section (which is already slightly stale per
the earlier codebase survey) and to the `gcloud run deploy --set-env-vars / --set-secrets` command.

### 2.4 Master-data mapping

Codes exchanged with ANTZ (`itemMasterCode`, `customerCode`, `vendorCode`, `siteCode`) are free text —
the plan is to use BC's own `No.` fields directly as these codes rather than maintaining a separate
translation table, **provided** ANTZ's character limits aren't violated (all ≤100 chars per the ISD,
BC `No.` fields are well under that). Confirm with ANTZ (Q12) whether this 1:1 approach is acceptable
before building. If not, add a small lookup table (same shape as `src/mappings.py`'s `db_mappings`)
rather than hardcoding.

### 2.5 Phased build plan

1. **Phase 0 — Clarify & obtain credentials.** Send the Q&A list in §1 to Inchz IoT; get UAT
   credentials first. Do not start Phase 2+ without a working UAT token.
2. **Phase 1 — Config & secrets.** Add the env vars above to `src/config.py`; create the Secret
   Manager secrets (`antz-password`, `antz-api-key`, `antz-webhook-api-key`); update the documented
   deploy command.
3. **Phase 2 — Build `antz_functions.py`.** Token acquisition + cache + refresh (mirror
   `bc_functions.py:get_access_token`), generic `_antz_get`/`_antz_post`/`_antz_put` helpers, and a
   cursor-pagination loop helper (ANTZ's `cursor`/`nextCursor`/`hasMore` shape, analogous to
   `bc_functions.py`'s `@odata.nextLink`-following `_fetch_all_pages`).
4. **Phase 3 — Master data push.** One-time backfill + incremental (`LastUpdatedDate` filter) sync of
   Adjustment Type (read-only, cache locally), Customer, Item Master (incl. UOM list + BC→Base UOM
   conversion per §1.3's "BC is the source of truth" rule), Site, Vendor — from BC into ANTZ via the
   POST/PUT endpoints in §3.3.
5. **Phase 4 — Outbound order push.** Create/Update Receiving Order (from BC PO) and Create/Update
   Transfer Order (from BC TO), gated on the architecture decision in §2.1. Add Get Receiving
   Order/Sales Order/Transfer Order/Picking Order/Delivery Order as read endpoints for reconciliation
   and troubleshooting.
6. **Phase 5 — Inbound webhooks.** Build the 3 `[RGMC]` receivers with API-key auth, idempotency
   checks keyed on `transactionId`/`refNo`, and the actual BC-side effects:
   - Push Receiving Order Status and Quantities → update/post the BC PO line via `bc_functions.py`.
   - Push Transfer Order Status and Issued Quantities → trigger BC TO shipment/receipt posting.
   - Push Inventory Adjustment → post to the mapped BC Item Journal/bin per `adjustmentTypeCode`.
   Reuse the existing `error_email_middleware`/`notify_error()` pattern so webhook failures alert
   someone, and the existing `rate_limiter.py` dependency to protect these routes from abuse.
7. **Phase 6 — Inventory/Item Movement read endpoints.** Get Inventory by Details/SKU, Get Serial
   Details, Get Item Transactions — expose for internal reporting/reconciliation tooling as needed.
8. **Phase 7 — UAT testing.** Auth + token refresh under load, full master-data CRUD round trip, a
   complete PO→Receiving→putaway→webhook-status cycle and SO/TO→picking→issuance→webhook-status
   cycle, webhook idempotency (replay the same payload twice), and failure-path behavior (ANTZ down,
   malformed webhook payload, expired token mid-batch).
9. **Phase 8 — Security hardening & go-live readiness.** Confirm IP allowlisting both directions,
   verify secrets are never logged, confirm IsActive/soft-delete semantics don't desync between BC and
   ANTZ, document the "no reversal" SOP from Q16 for warehouse ops.
10. **Phase 9 — Production cutover.** Switch `ANTZ_ENVIRONMENT=Production`, re-point secrets, run the
    same smoke tests against Production, define rollback (what happens if ANTZ integration needs to be
    disabled — a feature flag/env var to short-circuit the webhook routes and order-push calls is
    recommended).

---

## 3. Summary — what's genuinely blocking vs. what's just detail

**Blocking** (can't start building against real ANTZ endpoints without these): items 1–4, 8, 9 in §1.1.

**Should resolve before Phase 4** (affects architecture): item 17 (WebSocket scope), the BC-trigger
decision in §2.1, and item 19 (which BC company/site).

**Can be resolved in parallel with early build work**: items 11–16, 18, 20, 21 — these affect mapping
tables, retry logic, and SOPs but don't block getting a token and listing master data in UAT.
