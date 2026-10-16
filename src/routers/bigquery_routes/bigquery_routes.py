"""BigQuery direct-read endpoints."""
import logging
import re
from datetime import timedelta
import src.config as config
from typing import Optional
import google.auth
from google.auth import impersonated_credentials
from google.auth.transport import requests as google_auth_requests
from fastapi import APIRouter, HTTPException, Query, status
from google.cloud import logging as cloud_logging
from google.cloud import storage
from src.services.bq_read import read_gbq_with_timeout

client = cloud_logging.Client()
client.setup_logging()

logger = logging.getLogger("bigquery_routes")

bigquery_router = APIRouter(prefix="/bigquery_routes", tags=["BigQuery"])

# Upload Monitoring Dashboard (sbic-manual-trigger-page's "/" dashboard) — one entry per
# upload_type, naming each pipeline's BigQuery header/detail tables and its join-ref
# column. ra_xml is included even though it's currently empty (confirmed via `bq show`,
# 2026-10-16) so the dashboard can already offer it once that pipeline has real data.
UPLOAD_TYPE_TABLES = {
    "po": {"header": "int_document_ai", "detail": "int_document_ai_detail", "ref_column": "po_ref_number"},
    "ra": {"header": "int_document_ai_ra", "detail": "int_document_ai_ra_detail", "ref_column": "ra_ref_number"},
    "ra_xml": {"header": "int_document_ai_ra_xml", "detail": "int_document_ai_ra_xml_detail", "ref_column": "ra_ref_number"},
}

# Input (original-upload) GCS buckets per upload_type, for the dashboard's "View file"
# link — confirmed live via gsutil that both follow the same portal/{basename}.{ext}
# layout. ra_xml has no known bucket yet (empty table, no Eventarc trigger found) and is
# deliberately left out here rather than guessed.
UPLOAD_TYPE_INPUT_BUCKETS = {
    "po": "sbic-po-parser-in-v2",
    "ra": "sbic-ra-parser-in",
}

# Document AI batch output objects are named {basename}-{page}.json; stripping this
# suffix recovers the original input object's basename (see po_upload_plan.md).
_PAGE_SUFFIX_RE = re.compile(r"-\d+\.json$")


def _get_signing_credentials():
    """Self-impersonating credentials for Cloud Storage signed-URL generation.

    Confirmed live (2026-10-16) that this is NOT optional: google.auth.compute_engine
    .Credentials (the ambient credentials on Cloud Run) has no sign_bytes implementation
    at all, so a plain blob.generate_signed_url() always fails with "you need a private
    key to sign credentials" regardless of IAM permissions -- passing
    service_account_email alone doesn't fix it either. The documented no-key-file
    workaround is to wrap the ambient credentials in impersonated_credentials.Credentials
    targeting this SA's own email, which signs via the IAM Credentials API's signBlob
    method -- already permitted by roles/iam.serviceAccountTokenCreator granted to this
    SA on itself (set up for Cloud Tasks' OIDC tokens, reused here for the same reason).
    Built fresh per call rather than cached, to sidestep any question of whether the
    impersonated token's own `lifetime` needs manual re-refresh after it elapses.
    """
    source_credentials, _ = google.auth.default()
    source_credentials.refresh(google_auth_requests.Request())
    return impersonated_credentials.Credentials(
        source_credentials=source_credentials,
        target_principal=config.runbridge_invoker_service_account,
        target_scopes=["https://www.googleapis.com/auth/devstorage.read_only"],
        lifetime=900,
    )


def _run_parameterized(query: str, query_parameters: list) -> "pandas.DataFrame":
    """read_gbq with NAMED query parameters — every WHERE value here is user-supplied
    (po_ref_number/customer_name/dates from a web form), so this must never fall back
    to the by_table/value-style raw string formatting used elsewhere in this file."""
    configuration = {"query": {"parameterMode": "NAMED", "queryParameters": query_parameters}} if query_parameters else None
    return read_gbq_with_timeout(
        query, project_id=config.bigquery_project_id, dialect="standard", configuration=configuration,
    )


@bigquery_router.get("/document-ai/search", summary="Search int_document_ai headers (+ their int_document_ai_detail lines)")
async def search_document_ai(
    po_ref_number: Optional[str] = Query(None, description="One or more exact poRefNumber values — comma/newline/whitespace separated for multiple"),
    customer_name: Optional[str] = Query(None, description="Substring match against customer_name"),
    date_from: Optional[str] = Query(None, description="created_at >= this date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="created_at <= this date (YYYY-MM-DD), inclusive"),
    limit: int = Query(200, ge=1, le=1000),
):
    conditions = []
    params = []
    if po_ref_number:
        po_refs = [p for p in re.split(r"[,\s]+", po_ref_number.strip()) if p]
        conditions.append("po_ref_number IN UNNEST(@po_ref_numbers)")
        params.append({
            "name": "po_ref_numbers",
            "parameterType": {"type": "ARRAY", "arrayType": {"type": "STRING"}},
            "parameterValue": {"arrayValues": [{"value": p} for p in po_refs]},
        })
    if customer_name:
        conditions.append("LOWER(customer_name) LIKE @customer_name")
        params.append({"name": "customer_name", "parameterType": {"type": "STRING"}, "parameterValue": {"value": f"%{customer_name.lower()}%"}})
    if date_from:
        conditions.append("DATE(created_at) >= @date_from")
        params.append({"name": "date_from", "parameterType": {"type": "DATE"}, "parameterValue": {"value": date_from}})
    if date_to:
        conditions.append("DATE(created_at) <= @date_to")
        params.append({"name": "date_to", "parameterType": {"type": "DATE"}, "parameterValue": {"value": date_to}})

    # config.bigquery_dataset_id is already a fully-qualified "project.dataset" string
    # (confirmed live — a separate `{project_id}.{dataset_id}` prefix 500'd with a
    # doubled-up "project:project.dataset" BigQuery error), same as the pre-existing
    # by_table/value and by_table/latest routes below, which only ever do
    # `{dataset_id}.{table_name}` with no separate project prefix.
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    header_query = (
        f"SELECT * FROM `{config.bigquery_dataset_id}.int_document_ai` "
        f"{where} ORDER BY created_at DESC LIMIT @limit"
    )
    header_params = params + [{"name": "limit", "parameterType": {"type": "INT64"}, "parameterValue": {"value": str(limit)}}]

    try:
        header_df = _run_parameterized(header_query, header_params)
        headers = header_df.to_dict(orient="records")
        po_refs = sorted({h["po_ref_number"] for h in headers if h.get("po_ref_number")})
        details: list = []
        if po_refs:
            detail_query = (
                f"SELECT * FROM `{config.bigquery_dataset_id}.int_document_ai_detail` "
                "WHERE po_ref_number IN UNNEST(@po_refs)"
            )
            detail_params = [{
                "name": "po_refs",
                "parameterType": {"type": "ARRAY", "arrayType": {"type": "STRING"}},
                "parameterValue": {"arrayValues": [{"value": r} for r in po_refs]},
            }]
            detail_df = _run_parameterized(detail_query, detail_params)
            details = detail_df.to_dict(orient="records")
        return {"record_count": len(headers), "data": headers, "detail_data": details}
    except TimeoutError as e:
        logger.error(f"BigQuery document-ai search timed out: {e}")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(e))
    except Exception as e:
        logger.error(f"BigQuery document-ai search error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@bigquery_router.get("/by_table/value")
async def get_by_value(
    table_name: str = Query(...),
    where_column: str = Query(...),
    where_value: str = Query(...),
):
    try:
        query = "SELECT * FROM `{}.{}` WHERE {} = '{}'".format(
            config.bigquery_dataset_id, table_name, where_column, where_value
        )
        df = read_gbq_with_timeout(query, project_id=config.bigquery_project_id, dialect="standard")
        return {"record_count": len(df), "data": df.to_dict(orient="records")}
    except TimeoutError as e:
        logger.error(f"BigQuery by_table/value timed out (table={table_name}): {e}")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(e))
    except Exception as e:
        logger.error(f"BigQuery query error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@bigquery_router.get("/by_table/latest")
async def get_latest(
    table_name: str = Query(...),
    date_column: str = Query(...),
):
    try:
        query = "SELECT * FROM `{}.{}` ORDER BY {} DESC LIMIT 100".format(
            config.bigquery_dataset_id, table_name, date_column
        )
        df = read_gbq_with_timeout(query, project_id=config.bigquery_project_id, dialect="standard")
        return {"record_count": len(df), "data": df.to_dict(orient="records")}
    except TimeoutError as e:
        logger.error(f"BigQuery by_table/latest timed out (table={table_name}): {e}")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(e))
    except Exception as e:
        logger.error(f"BigQuery query error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@bigquery_router.get(
    "/upload-dashboard/files",
    summary="Distinct uploaded file names for one Document AI upload pipeline, grouped with counts",
)
async def list_upload_dashboard_files(
    upload_type: str = Query(..., description="po, ra, or ra_xml"),
    ref_values: Optional[str] = Query(
        None, description="Comma-separated exact PO/RA ref numbers — restricts results to files "
                           "containing ANY of these refs (matched against UPLOAD_TYPE_TABLES[upload_type]['ref_column'])",
    ),
    company_terms: Optional[str] = Query(
        None, description="Comma-separated, already-uppercased company-name substrings to match "
                           "(po only — int_document_ai_ra/_ra_xml have no company_name column at all)",
    ),
    date_from: Optional[str] = Query(None, description="created_at >= this date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="created_at <= this date (YYYY-MM-DD), inclusive"),
    limit: int = Query(500, ge=1, le=5000),
):
    tables = UPLOAD_TYPE_TABLES.get(upload_type)
    if not tables:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"upload_type must be one of {sorted(UPLOAD_TYPE_TABLES)}",
        )
    if company_terms and upload_type != "po":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="company filtering is only supported for upload_type=po — "
                   f"{tables['header']} has no company_name column",
        )

    conditions = []
    params = []
    if ref_values:
        refs = [r.strip() for r in ref_values.split(",") if r.strip()]
        if refs:
            conditions.append(f"{tables['ref_column']} IN UNNEST(@ref_values)")
            params.append({
                "name": "ref_values",
                "parameterType": {"type": "ARRAY", "arrayType": {"type": "STRING"}},
                "parameterValue": {"arrayValues": [{"value": r} for r in refs]},
            })
    if date_from:
        conditions.append("created_at >= @date_from")
        params.append({"name": "date_from", "parameterType": {"type": "DATE"}, "parameterValue": {"value": date_from}})
    if date_to:
        conditions.append("created_at <= @date_to")
        params.append({"name": "date_to", "parameterType": {"type": "DATE"}, "parameterValue": {"value": date_to}})
    if company_terms:
        terms = [t.strip().upper() for t in company_terms.split(",") if t.strip()]
        if terms:
            or_clauses = []
            for i, term in enumerate(terms):
                pname = f"company_term_{i}"
                or_clauses.append(f"UPPER(company_name) LIKE @{pname}")
                params.append({"name": pname, "parameterType": {"type": "STRING"}, "parameterValue": {"value": f"%{term}%"}})
            conditions.append("(" + " OR ".join(or_clauses) + ")")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = (
        f"SELECT file_name, COUNT(*) AS record_count, "
        f"MIN(created_at) AS first_created_at, MAX(created_at) AS last_created_at "
        f"FROM `{config.bigquery_dataset_id}.{tables['header']}` "
        f"{where} GROUP BY file_name ORDER BY file_name DESC LIMIT @limit"
    )
    params.append({"name": "limit", "parameterType": {"type": "INT64"}, "parameterValue": {"value": str(limit)}})

    try:
        df = _run_parameterized(query, params)
        return {"data": df.to_dict(orient="records"), "total": len(df)}
    except TimeoutError as e:
        logger.error(f"Upload dashboard files query timed out (upload_type={upload_type}): {e}")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(e))
    except Exception as e:
        logger.error(f"Upload dashboard files query error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@bigquery_router.get(
    "/document-ai/source-file",
    summary="Signed URL to the original uploaded file behind a Document AI file_name (the parsed OUTPUT path, not the upload itself)",
)
async def get_document_ai_source_file(
    file_name: str = Query(..., description="The file_name column value — a Document AI batch OUTPUT path, e.g. portal/batch/.../basename-0.json"),
    upload_type: str = Query("po", description="po or ra — selects which input bucket to search. ra_xml has no known bucket yet."),
):
    """Reverses the Document AI batch-output naming convention
    (portal/batch/{batch}/{job}/{shard}/{basename}-{page}.json) to find the real
    original upload (portal/{basename}.{ext}) in the matching input bucket, confirmed
    live via gsutil for both po and ra (see UPLOAD_TYPE_INPUT_BUCKETS). Extension isn't
    guessable (seen .pdf; could be an image), so this lists the bucket by prefix instead
    of constructing a path. Returns a short-lived v4 signed URL — signed via the IAM
    Credentials API (this service account has no private key file), using the same
    iam.serviceAccountTokenCreator self-grant already in place for Cloud Tasks.
    """
    if upload_type == "ra_xml":
        return {"status": "not_available", "message": "RA (xml) has no known upload bucket yet — this pipeline has no live data to point at."}
    bucket_name = UPLOAD_TYPE_INPUT_BUCKETS.get(upload_type)
    if not bucket_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"upload_type must be one of {sorted(UPLOAD_TYPE_INPUT_BUCKETS)} (or ra_xml, not yet available)",
        )

    last_segment = file_name.rsplit("/", 1)[-1]
    basename = _PAGE_SUFFIX_RE.sub("", last_segment)
    if not basename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not derive a basename from file_name")

    try:
        client_storage = storage.Client()
        blobs = list(client_storage.list_blobs(bucket_name, prefix=f"portal/{basename}"))
    except Exception as e:
        logger.error(f"Error listing gs://{bucket_name}/portal/{basename}* for file_name={file_name}: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    if not blobs:
        return {"status": "not_found", "output_file": file_name}

    blob = blobs[0]
    if len(blobs) > 1:
        blob = max(blobs, key=lambda b: b.updated)
        logger.warning(f"Multiple input objects matched gs://{bucket_name}/portal/{basename}* — using most recently updated: {blob.name}")

    try:
        url = blob.generate_signed_url(
            version="v4", expiration=timedelta(minutes=15), method="GET",
            credentials=_get_signing_credentials(),
        )
    except Exception as e:
        logger.error(f"Error signing URL for gs://{bucket_name}/{blob.name}: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    return {"status": "found", "url": url, "object": blob.name}
