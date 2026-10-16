# Handoff

## Goal

This session had two separate threads, in order:

**Thread A (resumed from prior handoff, left unresolved)**: The previous `handoff.md` described
Goal 1 as "verify committed RGMC custom API endpoints work against live Business Central — deploy +
smoke test." On resume, this session found the handoff was stale: 5 commits had landed on `main`
after the handoff was written (`d8b7d27` through `ffa7655`), adding features the handoff never
mentioned (BigQuery↔BC buffer integration, a creatives route, an MTC-routing fix, email sending). The
session flagged this drift to the user and asked whether deploy/smoke-testing had already happened.
**The user never answered this question** — they moved directly to Thread B instead. Thread A's
status (is `rgmc-gcp-api` deployed to Cloud Run with the custom BC endpoints live and smoke-tested?)
is still open and unconfirmed.

**Thread B (the actual work done this session)**: The user asked to analyze a vendor Integration
Specification Document — `C:\Users\erarellano\Downloads\ISD_RGMC ANTZ SCM_v1.0.1.pdf` (Inchz IoT's
"ANTZ RFID Supply Chain Management System", v1.0.1, 5-Oct-2026) — and produce:
1. A detailed list of credentials/tokens/setup items RGMC needs to request from the ANTZ vendor to
   consume their API, for both `rgmc-gcp-api` (this repo) and `C:\claude\rgmc-bc-api` (a separate,
   out-of-scope-to-edit production repo).
2. A concrete execution plan for integrating ANTZ into `rgmc-gcp-api` specifically, including required
   environment variables, saved to an md file.
3. Other factors/questions to ask the vendor to make the integration smooth.
All three were combined into one file per the user's phrasing ("save all of your findings... on an md
file"). This is **pure planning/documentation work — no integration code was written**, and none was
requested yet.

## Current State

**Thread A**: Unresolved. `rgmc-gcp-api` is on `main`, working tree was clean at session start
(`ffa7655 DI-0143 added email sending`). Whether it's deployed to Cloud Run / smoke-tested against
live BC is unknown — never confirmed by the user this session or the last.

**Thread B**: Complete and delivered. `C:\RGMC\Source\git\rgmc-gcp-api\ANTZ_Integration_Plan.md` was
written, covering:
- §1: credential/access checklist to request from Inchz IoT (UAT+Prod base URLs, GetToken
  username/password per environment, `x-api-key`, WebSocket host/port if in scope, token TTL, IP
  allowlist info both directions, the 3 inbound webhook URLs RGMC itself must design and hand to ANTZ,
  the API key RGMC must issue to ANTZ for those webhooks) plus a numbered list of business-rule
  clarifications to request (items 11–21: adjustment-type stability, UOM matching rules, timestamp
  timezone consistency, webhook retry/idempotency contract, error response shape, the "no order
  reversal" SOP, WebSocket/POS scope, rate limits, which RGMC company/site is in scope, support SLA,
  pre-seeding master data).
- §2: execution plan for `rgmc-gcp-api` — new `src/routers/antz_routes/` module mirroring the existing
  `bc_functions.py` client pattern (token-cache dict + `threading.Lock`, sync `requests`), inbound
  webhook auth modeled on `rgmc-bc-api`'s `X-Task-Secret` header-check pattern (this repo currently has
  *no* inbound auth — only a 30s rate limiter), a table of new `ANTZ_*` env vars to add to
  `src/config.py` and GCP Secret Manager, and a 10-phase build plan (credentials → config/secrets →
  client module → master-data sync → outbound order push → inbound webhooks → inventory read
  endpoints → UAT testing → hardening → prod cutover).
- §3: a short "blocking vs. non-blocking" summary of the open questions.

An explicit open architecture question was flagged rather than resolved: **BC has no native outbound
webhook mechanism**, so something must trigger the Create Receiving/Transfer Order push to ANTZ when a
PO/TO is created in BC — either a new AL event calling out to `rgmc-gcp-api`, or a Cloud
Scheduler-driven polling job using the incremental-cursor pattern already used elsewhere in
`rgmc-bc-api`'s `custom_connector_*` routers. This needs a decision with whoever owns the AL side
before any Phase 4 (outbound order push) work starts.

**Git state surprise found while writing this handoff**: `ANTZ_Integration_Plan.md` is no longer an
untracked loose file — it is now committed at `HEAD` (`bec38e9 DI-0205 added ship-to address fix`,
author `erar404`, 2026-10-15 15:53:09+08:00). This commit was made by the user directly (not by this
Claude session — no git commands were run here to commit it), and it bundles two unrelated changes
under one message that only describes the second one:
- `ANTZ_Integration_Plan.md` (177 lines added) — this session's deliverable
- `src/routers/sbic_routes/CustomerPOUL.py` (35 lines added) — a "ship-to address fix," unrelated to
  ANTZ, that this session did not touch or review
`git log --oneline -10` now shows `bec38e9` as the tip, one commit ahead of the `ffa7655` HEAD this
session started from. Working tree is clean (`git status -s` empty).

## Files Actively Being Edited

No files are mid-edit. Everything from this session is committed.

- `ANTZ_Integration_Plan.md` (repo root) — created this session, now committed in `bec38e9` alongside
  an unrelated `CustomerPOUL.py` change the user apparently made outside this session.
- `src/routers/sbic_routes/CustomerPOUL.py` — modified in the same commit `bec38e9`, but **not by this
  session**. This session never opened or edited this file. Its "ship-to address fix" content is
  unreviewed from this session's perspective — if asked about it, read it fresh rather than assuming
  context.

## Failed Attempts

- **What was tried**: Treating the handoff.md from the prior session as current and proceeding straight
  to its "Next Step" (run the queued `gcloud run deploy` / smoke-test commands) — **Why it didn't
  happen**: before acting, a drift check (`git log`, diffing router registrations) showed 5 unmentioned
  commits had landed since that handoff was written, so the plan was stopped and the user was asked to
  confirm current status instead of guessing. The user then redirected to Thread B without answering,
  so Thread A remains genuinely unresolved, not silently dropped.
- No failed technical attempts in Thread B — this was pure document analysis and planning, no code was
  run against a live ANTZ endpoint (no credentials exist yet to do so).

## Next Step

Two independent threads to pick up — ask the user which to prioritize, or handle both:

1. **Thread A**: Ask the user directly: "Has `rgmc-gcp-api` been deployed to Cloud Run and smoke-tested
   against live BC since `ffa7655`? Should I pick up the original deploy+smoke-test plan, or is that
   already done/no longer relevant given the newer commits (DI-0172, DI-0183, DI-0205, etc.)?" Do not
   assume either way.
2. **Thread B**: The deliverable (`ANTZ_Integration_Plan.md`) is done. The logical next action is for
   the user to send §1's question list to Inchz IoT (ANTZ vendor) and obtain UAT credentials — this
   session cannot proceed further without them. If the user wants to start building ahead of
   credentials, the only safe starting point is **Phase 1** from the plan (add `ANTZ_*` env var
   placeholders to `src/config.py` and stub out `src/routers/antz_routes/` module skeleton) since Phase
   2+ requires a real UAT token to test against.
3. **Separately, flag to the user** (don't just silently accept) that commit `bec38e9` bundles the
   unrelated `CustomerPOUL.py` ship-to-address change with the ANTZ plan file under a commit message
   that only names the former. Confirmed via `git log origin/main..HEAD` (empty output) that this
   commit is **already pushed to `origin/main`** — so a rewrite/split would require a force-push or a
   follow-up corrective commit, not a simple local amend. Only raise this if the user cares about clean
   history; don't take any corrective git action unprompted.

## Context & Gotchas

- **`ANTZ_Integration_Plan.md` is a planning doc, not a spec RGMC has accepted.** The source PDF
  (`ISD_RGMC ANTZ SCM_v1.0.1.pdf`) itself is an unsigned draft — its own Acceptance page (§4.0) has
  RGMC Group's approval signatures blank, only Inchz IoT's are filled in. Don't treat anything in the
  ISD as finalized/contractual when advising the user.
- **Which RGMC company/site ANTZ covers is never stated in the ISD** — the plan document guesses SBIC
  (Suncoast Brands International Corp., FMCG distribution/warehousing) based on subject matter (Goods
  Receiving/Issuance, RFID warehouse ops) but this is explicitly flagged as unconfirmed and is item #19
  in the plan's question list. Don't assume SBIC without the user confirming.
- **`rgmc-gcp-api` has two separate BC client implementations across two repos** — this repo's own
  `src/services/bc_functions.py` and `C:\claude\rgmc-bc-api`'s equivalent are not shared code. The ANTZ
  plan deliberately builds on *this* repo's copy (per the user's explicit ask to integrate into
  `rgmc-gcp-api`) and does not attempt to deduplicate or route through `rgmc-bc-api` — that's a known,
  accepted architectural wart, not an oversight.
- **This repo has no inbound API-key/auth mechanism today.** `src/routers/sbic_routes/rate_limiter.py`
  is a 30-second per-path cooldown throttle only — it is not authentication. Any new inbound webhook
  route (the 3 `[RGMC]` ANTZ push endpoints) needs new auth code; the plan specifies copying
  `rgmc-bc-api`'s `X-Task-Secret` inline-header-check pattern (see `rgmc-bc-api`'s
  `src/routers/bc_routes/task_routes.py`) since nothing equivalent exists here yet.
- **`C:\claude\rgmc-bc-api` is out of scope to modify** per earlier session guidance (it's the real
  production BC gateway repo, not a scratch project) — it was only read for pattern reference during
  this session's research (its `task_routes.py` auth pattern and its `custom_connector_bin_routes.py`
  / `custom_connector_warehouse_entry_routes.py`, which already expose BC Bin/Warehouse Entry data that
  could be relevant to ANTZ's warehouse-location reconciliation — worth mentioning to the user as a
  "don't rebuild this" pointer if ANTZ inventory-location work comes up later).
- **No `.env`/`.env.example` exists in `rgmc-gcp-api`**, and no pydantic Settings/dotenv convention —
  all config is plain `os.getenv(...)` with hardcoded fallback defaults in `src/config.py` (including a
  known anti-pattern of real-looking BC secret defaults baked in, already flagged in `README.md:298`).
  Any new `ANTZ_*` vars should follow this same plain-`os.getenv` style, not introduce a new pattern.
- **Deployment is manual** (`gcloud builds submit` / `gcloud run deploy` with `--set-secrets` for
  Secret Manager-backed values) — no CI/CD pipeline exists for this repo. New `ANTZ_*` secrets will need
  to be created in Secret Manager by hand and added to the documented deploy command in `README.md`.
