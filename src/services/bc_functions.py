"""All Business Central API related functions."""
import time
import threading
from typing import Any
import requests
from src.config import BC_CLIENT_ID, BC_TENANT_ID, BC_CLIENT_SECRET, BC_SCOPE, BC_AUTH_URL, BC_ENVIRONMENT, BC_COMPANY

_BC_BASE = "https://api.businesscentral.dynamics.com/v2.0"

_token_lock = threading.Lock()
_token_cache: dict = {"token": None, "expires_at": 0.0}
_company_id_cache: dict = {}
_item_price_cache: dict = {}


def get_access_token() -> str:
    with _token_lock:
        if time.time() < _token_cache["expires_at"] - 60:
            return _token_cache["token"]
        payload = {
            "grant_type": "client_credentials",
            "client_id": BC_CLIENT_ID,
            "client_secret": BC_CLIENT_SECRET,
            "scope": BC_SCOPE
        }
        response = requests.post(
            BC_AUTH_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        data = response.json()
        _token_cache["token"] = data["access_token"]
        _token_cache["expires_at"] = time.time() + data.get("expires_in", 3600)
        return _token_cache["token"]


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {get_access_token()}", "Accept": "application/json"}


def call_business_central_api(endpoint: str):
    url = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/api/v2.0/{endpoint}"
    response = requests.get(url, headers=_auth_headers())
    return response.status_code, response.json()


def get_company_id(company_name: str = None) -> str:
    """Return the BC company GUID for the configured (or given) company name."""
    name = (company_name or BC_COMPANY).upper()
    if name in _company_id_cache:
        return _company_id_cache[name]
    status, data = call_business_central_api("companies")
    if status != 200:
        raise RuntimeError(f"BC companies call failed ({status}): {data}")
    for c in data.get("value", []):
        if c.get("name", "").upper() == name:
            _company_id_cache[name] = c["id"]
            return c["id"]
    raise ValueError(f"Company '{name}' not found in Business Central")


def _fetch_all_pages(url: str) -> list:
    """Follow @odata.nextLink pages and return the combined value list."""
    all_records = []
    while url:
        print(f"Fetching BC data from: {url}")
        response = requests.get(url, headers=_auth_headers())
        response.raise_for_status()
        data = response.json()
        all_records.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
    return all_records


def call_bc_table(table_endpoint: str, company_name: str = None, odata_filter: str = None, expand: str = None, select: str = None):
    """Call a company-scoped BC table endpoint and return (status, value_list)."""
    company_id = get_company_id(company_name)
    url = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/api/v2.0/companies({company_id})/{table_endpoint}"
    params = []
    if odata_filter:
        params.append(f"$filter={odata_filter}")
    if expand:
        params.append(f"$expand={expand}")
    if select:
        params.append(f"$select={select}")
    if params:
        url += "?" + "&".join(params)
    try:
        records = _fetch_all_pages(url)
        return 200, {"value": records}
    except requests.HTTPError as e:
        return e.response.status_code, e.response.json()


def bc_get_record(table_endpoint: str, record_id: str, company_name: str = None):
    """GET a single record by GUID from a company-scoped BC table."""
    company_id = get_company_id(company_name)
    url = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/api/v2.0/companies({company_id})/{table_endpoint}({record_id})"
    response = requests.get(url, headers=_auth_headers())
    return response.status_code, response.json()


def bc_create_record(table_endpoint: str, payload: dict, company_name: str = None):
    """POST a new record to a company-scoped BC table."""
    company_id = get_company_id(company_name)
    url = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/api/v2.0/companies({company_id})/{table_endpoint}"
    headers = {**_auth_headers(), "Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code, response.json()


def bc_update_record(table_endpoint: str, record_id: str, payload: dict, company_name: str = None):
    """PATCH an existing record in a company-scoped BC table."""
    company_id = get_company_id(company_name)
    url = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/api/v2.0/companies({company_id})/{table_endpoint}({record_id})"
    headers = {**_auth_headers(), "Content-Type": "application/json", "If-Match": "*"}
    response = requests.patch(url, json=payload, headers=headers)
    return response.status_code, response.json() if response.content else {}


def bc_delete_record(table_endpoint: str, record_id: str, company_name: str = None):
    """DELETE a record from a company-scoped BC table."""
    company_id = get_company_id(company_name)
    url = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/api/v2.0/companies({company_id})/{table_endpoint}({record_id})"
    response = requests.delete(url, headers=_auth_headers())
    return response.status_code


_RGMC_CUSTOM_API = "api/rgmc/rgmccustom/v1.0"


def call_rgmc_table(table_endpoint: str, company_name: str = None, odata_filter: str = None, expand: str = None, select: str = None):
    """Call a company-scoped RGMC custom API table and return (status, value_list)."""
    company_id = get_company_id(company_name)
    url = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/{_RGMC_CUSTOM_API}/companies({company_id})/{table_endpoint}"
    params = []
    if odata_filter:
        params.append(f"$filter={odata_filter}")
    if expand:
        params.append(f"$expand={expand}")
    if select:
        params.append(f"$select={select}")
    if params:
        url += "?" + "&".join(params)
    try:
        records = _fetch_all_pages(url)
        return 200, {"value": records}
    except requests.HTTPError as e:
        return e.response.status_code, e.response.json()


def rgmc_get_record(table_endpoint: str, record_id: str, company_name: str = None):
    """GET a single record by GUID from a RGMC custom API table."""
    company_id = get_company_id(company_name)
    url = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/{_RGMC_CUSTOM_API}/companies({company_id})/{table_endpoint}({record_id})"
    response = requests.get(url, headers=_auth_headers())
    return response.status_code, response.json()


def rgmc_create_record(table_endpoint: str, payload: dict, company_name: str = None):
    """POST a new record to a RGMC custom API table."""
    company_id = get_company_id(company_name)
    url = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/{_RGMC_CUSTOM_API}/companies({company_id})/{table_endpoint}"
    headers = {**_auth_headers(), "Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code, _safe_json(response)


def rgmc_update_record(table_endpoint: str, record_id: str, payload: dict, company_name: str = None):
    """PATCH an existing record in a RGMC custom API table."""
    company_id = get_company_id(company_name)
    url = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/{_RGMC_CUSTOM_API}/companies({company_id})/{table_endpoint}({record_id})"
    headers = {**_auth_headers(), "Content-Type": "application/json", "If-Match": "*"}
    response = requests.patch(url, json=payload, headers=headers)
    return response.status_code, response.json() if response.content else {}


def rgmc_delete_record(table_endpoint: str, record_id: str, company_name: str = None):
    """DELETE a record from a RGMC custom API table."""
    company_id = get_company_id(company_name)
    url = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/{_RGMC_CUSTOM_API}/companies({company_id})/{table_endpoint}({record_id})"
    response = requests.delete(url, headers=_auth_headers())
    return response.status_code


def _safe_json(response) -> Any:
    """Parse response body as JSON; fall back to raw text on decode failure."""
    if not response.content:
        return {}
    try:
        return response.json()
    except Exception:
        return response.text


def rgmc_get_contact_picture(contact_id: str, company_name: str = None):
    """GET contactPictures({contact_id}) — returns {id, contactNo, picture} where picture is base64."""
    company_id = get_company_id(company_name)
    url = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/{_RGMC_CUSTOM_API}/companies({company_id})/contactPictures({contact_id})"
    response = requests.get(url, headers=_auth_headers())
    return response.status_code, _safe_json(response)


def rgmc_update_contact_picture(contact_id: str, picture_base64: str, company_name: str = None):
    """PATCH contactPictures({contact_id}) with a base64-encoded image string. Insert/Delete not allowed by AL."""
    company_id = get_company_id(company_name)
    url = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/{_RGMC_CUSTOM_API}/companies({company_id})/contactPictures({contact_id})"
    headers = {**_auth_headers(), "Content-Type": "application/json", "If-Match": "*"}
    response = requests.patch(url, json={"picture": picture_base64}, headers=headers)
    return response.status_code, _safe_json(response)


def rgmc_list_contact_brand_tags(contact_id: str, company_name: str = None):
    """GET contacts({contact_id})/contactBrandTags — all brand tags for a contact (Pag50209)."""
    company_id = get_company_id(company_name)
    url = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/{_RGMC_CUSTOM_API}/companies({company_id})/contacts({contact_id})/contactBrandTags"
    response = requests.get(url, headers=_auth_headers())
    return response.status_code, _safe_json(response)


def rgmc_add_contact_brand_tag(contact_id: str, brand_code: str, company_name: str = None):
    """POST contacts({contact_id})/contactBrandTags — add a brand tag to a contact (Pag50209)."""
    company_id = get_company_id(company_name)
    url = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/{_RGMC_CUSTOM_API}/companies({company_id})/contacts({contact_id})/contactBrandTags"
    headers = {**_auth_headers(), "Content-Type": "application/json"}
    response = requests.post(url, json={"brandCode": brand_code}, headers=headers)
    return response.status_code, _safe_json(response)


def rgmc_delete_contact_brand_tag(contact_id: str, tag_id: str, company_name: str = None):
    """DELETE contacts({contact_id})/contactBrandTags({tag_id}) — remove a brand tag (Pag50209)."""
    company_id = get_company_id(company_name)
    url = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/{_RGMC_CUSTOM_API}/companies({company_id})/contacts({contact_id})/contactBrandTags({tag_id})"
    response = requests.delete(url, headers=_auth_headers())
    return response.status_code


def rgmc_list_item_prices(
    company_name: str = None,
    product_no: str = None,
    on_date: str = None,
    odata_filter: str = None,
    top: int = None,
):
    """GET itemPrices filtered to the price effectivity window (Pag50210).

    When on_date is provided the filter enforces:
        startingDate <= on_date <= endingDate
    A blank endingDate is stored by BC as 0001-01-01 (meaning "open-ended"),
    so records with endingDate eq 0001-01-01 are always included.
    Results are ordered startingDate desc so the most-recent effective price
    comes first when the caller uses $top=1.
    """
    cache_key = (company_name or BC_COMPANY, product_no, on_date, odata_filter, top)
    try:
        company_id = get_company_id(company_name)
        url = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/{_RGMC_CUSTOM_API}/companies({company_id})/itemPrices"
        params = []
        filters = []
        if product_no:
            filters.append(f"productNo eq '{product_no}'")
        if on_date:
            filters.append(f"startingDate le {on_date}")
            filters.append(f"(endingDate ge {on_date} or endingDate eq 0001-01-01)")
        if odata_filter:
            filters.append(odata_filter)
        if filters:
            params.append(f"$filter={' and '.join(filters)}")
        params.append("$orderby=startingDate desc")
        if top:
            params.append(f"$top={top}")
        url += "?" + "&".join(params)
        response = requests.get(url, headers=_auth_headers())
        data = _safe_json(response)
        if response.ok:
            _item_price_cache[cache_key] = data
        return response.status_code, data
    except Exception:
        cached = _item_price_cache.get(cache_key)
        if cached is not None:
            return 200, cached
        raise


def update_cached_item_price(
    product_no: str,
    updated_fields: dict,
    company_name: str = None,
    on_date: str = None,
) -> int:
    """Merge updated_fields into every cached price record that matches product_no.

    Matches all cache entries for the item regardless of odata_filter / top so
    that callers don't need to know the exact parameters used at lookup time.
    Optionally narrow to a specific on_date. Returns the number of cache entries
    that were updated (0 means the item has never been looked up / cached).
    """
    target_company = (company_name or BC_COMPANY).upper()
    count = 0
    for cache_key, cached_data in _item_price_cache.items():
        key_company, key_product_no, key_on_date = cache_key[0], cache_key[1], cache_key[2]
        if key_company.upper() != target_company:
            continue
        if key_product_no != product_no:
            continue
        if on_date and key_on_date != on_date:
            continue
        for record in cached_data.get("value", []):
            record.update(updated_fields)
        count += 1
    return count


def get_dimension_values_by_code(dimension_code: str, company_name: str = None):
    """Return all dimension values for the given dimension code (e.g. 'BRAND').

    Fetches the flat /dimensionValues collection and filters client-side by dimensionId.
    This covers records whose dimensionId was zeroed out during BC migrations.
    """
    company_id = get_company_id(company_name)
    base = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/api/v2.0/companies({company_id})"

    all_dims = _fetch_all_pages(f"{base}/dimensions")
    dims = [d for d in all_dims if d.get("code", "").upper() == dimension_code.upper()]
    if not dims:
        available = [d.get("code") for d in all_dims]
        raise ValueError(f"Dimension '{dimension_code}' not found. Available codes: {available}")
    dimension_id = dims[0]["id"]

    all_values = _fetch_all_pages(f"{base}/dimensionValues")
    records = [v for v in all_values if v.get("dimensionId") == dimension_id]
    return 200, {"value": records}