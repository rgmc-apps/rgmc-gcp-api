"""BigQuery direct-read endpoints."""
import logging
import re
import pandas_gbq
import src.config as config
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from google.cloud import logging as cloud_logging

client = cloud_logging.Client()
client.setup_logging()

logger = logging.getLogger("bigquery_routes")

bigquery_router = APIRouter(prefix="/bigquery_routes", tags=["BigQuery"])


def _run_parameterized(query: str, query_parameters: list) -> "pandas.DataFrame":
    """read_gbq with NAMED query parameters — every WHERE value here is user-supplied
    (po_ref_number/customer_name/dates from a web form), so this must never fall back
    to the by_table/value-style raw string formatting used elsewhere in this file."""
    configuration = {"query": {"parameterMode": "NAMED", "queryParameters": query_parameters}} if query_parameters else None
    return pandas_gbq.read_gbq(
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
        df = pandas_gbq.read_gbq(query, project_id=config.bigquery_project_id, dialect="standard")
        return {"record_count": len(df), "data": df.to_dict(orient="records")}
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
        df = pandas_gbq.read_gbq(query, project_id=config.bigquery_project_id, dialect="standard")
        return {"record_count": len(df), "data": df.to_dict(orient="records")}
    except Exception as e:
        logger.error(f"BigQuery query error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
