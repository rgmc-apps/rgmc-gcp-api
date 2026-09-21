"""CustomerPOUL Related Queries and Functions."""
import logging
from typing import Optional
from google.cloud import logging as cloud_logging
from fastapi import HTTPException, Query, Request, status, Depends, APIRouter
from src.routers.bigquery_bridge import BigqueryBridge
from src.config import pass_key
from src.routers.sbic_routes.rate_limiter import rate_limit
from src.routers.sbic_routes._db import run_query
from src.services.bc_functions import call_bc_table, call_rgmc_table
from src.services.fuzzy_match import DEFAULT_THRESHOLD, best_matches

# Instantiate a Cloud Logging client
client = cloud_logging.Client()
client.setup_logging()

logger = logging.getLogger('customerpoul')

customerpoul_router = APIRouter(prefix="/customerpoul", tags=["CustomerPOUL"])

# Company routing rule mirrored from the SO import worker (mssql_bc_mapping.txt §5):
# CustomerPOUL.companyName contains one of these keywords -> BC company code.
# Checked in order; first match wins.
_COMPANY_KEYWORD_MAP: list[tuple[str, str]] = [
    ("SUNCOAST", "SBIC"),
    ("SBIC", "SBIC"),
    ("MANILA", "MTC"),
    ("MTC", "MTC"),
]


def _resolve_bc_company(source_company_name: Optional[str]) -> Optional[str]:
    upper = (source_company_name or "").upper()
    for keyword, bc_company in _COMPANY_KEYWORD_MAP:
        if keyword in upper:
            return bc_company
    return None


def _get_latest_header(po_ref_number: str) -> dict:
    rows = run_query(
        "SELECT TOP 1 * FROM CustomerPOUL WHERE poRefNumber = :po_ref_number ORDER BY customerPOId DESC",
        {"po_ref_number": po_ref_number},
    )
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No CustomerPOUL row found for poRefNumber={po_ref_number!r}",
        )
    return rows[0]

@customerpoul_router.post("/runbridge/")
async def run_customerpoul_bridge(request: Request, method: str = 'manual'):
    try:
        bridge = BigqueryBridge(logger, method, group_code='customerpoul')
        result = bridge.main()
        return result
    except Exception as e:
        logger.error(f"Error running BigQuery bridge: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@customerpoul_router.post("/runbridge/onlinesalespo/")
async def run_online_sales_po_bridge(request: Request, method: str = 'manual'):
    try:
        bridge = BigqueryBridge(logger, method, group_code='onlinesalespo')
        result = bridge.main()
        return result
    except Exception as e:
        logger.error(f"Error running BigQuery bridge: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@customerpoul_router.get("", summary="List CustomerPOUL headers")
def list_customerpoul(
    po_ref_number: Optional[str] = Query(None, description="Exact poRefNumber match"),
    customer_name: Optional[str] = Query(None, description="Substring match on customerName"),
    customer_id: Optional[int] = Query(None, description="Exact customerId match"),
    po_status: Optional[str] = Query(None, description="Exact poStatus match"),
    limit: int = Query(100, ge=1, le=1000),
):
    conditions: list[str] = []
    params: dict = {}
    if po_ref_number:
        conditions.append("poRefNumber = :po_ref_number")
        params["po_ref_number"] = po_ref_number
    if customer_name:
        conditions.append("customerName LIKE :customer_name")
        params["customer_name"] = f"%{customer_name}%"
    if customer_id is not None:
        conditions.append("customerId = :customer_id")
        params["customer_id"] = customer_id
    if po_status:
        conditions.append("poStatus = :po_status")
        params["po_status"] = po_status
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = run_query(f"SELECT TOP {limit} * FROM CustomerPOUL {where} ORDER BY customerPOId DESC", params)
    return {"record_count": len(rows), "data": rows}


@customerpoul_router.get("/{po_ref_number}", summary="Get CustomerPOUL header(s) by PO ref number")
def get_customerpoul_by_ref(po_ref_number: str):
    rows = run_query(
        "SELECT * FROM CustomerPOUL WHERE poRefNumber = :po_ref_number ORDER BY customerPOId DESC",
        {"po_ref_number": po_ref_number},
    )
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No CustomerPOUL row found for poRefNumber={po_ref_number!r}",
        )
    return {"record_count": len(rows), "data": rows}


@customerpoul_router.get(
    "/{po_ref_number}/shipto-match",
    summary="Fuzzy-match this PO's customerBranchName to a BC Ship-To Address",
)
def match_shipto(
    po_ref_number: str,
    company: Optional[str] = Query(None, description="Override BC company (defaults to routing from companyName)"),
    threshold: float = Query(DEFAULT_THRESHOLD, ge=0.0, le=1.0, description="Minimum fuzzy score to include a match"),
    top: int = Query(5, ge=1, le=20, description="Max number of fuzzy candidates to return"),
):
    header = _get_latest_header(po_ref_number)
    branch_name = header.get("customerBranchName") or ""
    branch_code = (header.get("customerBranchLookUpCode") or "").strip()

    bc_company = company or _resolve_bc_company(header.get("companyName"))
    if not bc_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not resolve a BC company from companyName={header.get('companyName')!r}; pass ?company=",
        )

    try:
        http_status, data = call_rgmc_table("shipToAddresses", company_name=bc_company)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching BC ship-to addresses for {bc_company}: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    if http_status != 200:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"BC returned {http_status}: {data}")
    ship_tos = data.get("value", [])

    exact_code_match = None
    if branch_code:
        for ship_to in ship_tos:
            if (ship_to.get("code") or "").strip().upper() == branch_code.upper():
                exact_code_match = ship_to
                break

    candidates = [(ship_to.get("name") or "", ship_to) for ship_to in ship_tos]
    matches = best_matches(branch_name, candidates, threshold=threshold, top_n=top)

    return {
        "poRefNumber": po_ref_number,
        "customerBranchName": branch_name,
        "customerBranchLookUpCode": branch_code,
        "bcCompany": bc_company,
        "exactCodeMatch": exact_code_match,
        "fuzzyMatches": matches,
    }


@customerpoul_router.get(
    "/{po_ref_number}/item-match",
    summary="Fuzzy-match this PO's line customerSKUDesc values to BC Items",
)
def match_items(
    po_ref_number: str,
    company: Optional[str] = Query(None, description="Override BC company (defaults to routing from companyName)"),
    threshold: float = Query(DEFAULT_THRESHOLD, ge=0.0, le=1.0, description="Minimum fuzzy score to include a match"),
    top: int = Query(3, ge=1, le=20, description="Max number of fuzzy candidates to return per line"),
):
    header = _get_latest_header(po_ref_number)
    lines = run_query(
        "SELECT * FROM CustomerPOULDetail WHERE poRefNumber = :po_ref_number",
        {"po_ref_number": po_ref_number},
    )
    if not lines:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No CustomerPOULDetail rows found for poRefNumber={po_ref_number!r}",
        )

    bc_company = company or _resolve_bc_company(header.get("companyName"))
    if not bc_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not resolve a BC company from companyName={header.get('companyName')!r}; pass ?company=",
        )

    try:
        http_status, data = call_bc_table(
            "items", company_name=bc_company, select="number,displayName,displayName2,blocked"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching BC items for {bc_company}: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    if http_status != 200:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"BC returned {http_status}: {data}")
    items = data.get("value", [])
    candidates = [(item.get("displayName") or "", item) for item in items]

    results = []
    for line in lines:
        sku_desc = line.get("customerSKUDesc") or ""
        results.append({
            "customerSKUCode": line.get("customerSKUCode"),
            "customerSKUDesc": sku_desc,
            "fuzzyMatches": best_matches(sku_desc, candidates, threshold=threshold, top_n=top),
        })

    return {"poRefNumber": po_ref_number, "bcCompany": bc_company, "lines": results}