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
    return response.status_code, response.json()


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
    """GET picture metadata for a contact (returns JSON value array)."""
    company_id = get_company_id(company_name)
    url = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/{_RGMC_CUSTOM_API}/companies({company_id})/contacts({contact_id})/picture"
    response = requests.get(url, headers=_auth_headers())
    return response.status_code, _safe_json(response)


def rgmc_get_contact_picture_content(contact_id: str, picture_id: str, company_name: str = None):
    """GET binary image bytes for a contact picture. Returns (status, bytes, content_type)."""
    company_id = get_company_id(company_name)
    url = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/{_RGMC_CUSTOM_API}/companies({company_id})/contacts({contact_id})/picture({picture_id})/content"
    headers = {**_auth_headers(), "Accept": "image/*"}
    response = requests.get(url, headers=headers)
    return response.status_code, response.content, response.headers.get("Content-Type", "image/jpeg")


def rgmc_update_contact_picture(contact_id: str, picture_id: str, image_bytes: bytes, content_type: str, company_name: str = None):
    """PATCH binary image data onto a contact picture record."""
    company_id = get_company_id(company_name)
    url = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/{_RGMC_CUSTOM_API}/companies({company_id})/contacts({contact_id})/picture({picture_id})"
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": content_type,
        "If-Match": "*",
    }
    response = requests.patch(url, data=image_bytes, headers=headers)
    return response.status_code, _safe_json(response)


def rgmc_delete_contact_picture(contact_id: str, picture_id: str, company_name: str = None):
    """DELETE a contact picture from RGMC custom API."""
    company_id = get_company_id(company_name)
    url = f"{_BC_BASE}/{BC_TENANT_ID}/{BC_ENVIRONMENT}/{_RGMC_CUSTOM_API}/companies({company_id})/contacts({contact_id})/picture({picture_id})"
    response = requests.delete(url, headers=_auth_headers())
    return response.status_code


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