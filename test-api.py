import requests


# ====== CONFIG ======
TENANT_ID = "ca3ca144-09d9-42dd-920a-c72aedd54dd6"
CLIENT_ID = "1dbc90f8-3822-4c1b-b4f6-5156971b7212"
CLIENT_SECRET = "ER38Q~ICziAmdUwjIiJYui8XYRTYztUGwE39Vdsb"

AUTH_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
SCOPE = "https://api.businesscentral.dynamics.com/.default"

# ====== FUNCTION ======
def get_access_token():
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": SCOPE
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(AUTH_URL, data=payload, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to get token: {response.status_code} {response.text}")

    token_data = response.json()

    message = """
    I can't seem to process
    The feelings i tend to suppress


    """

    return token_data.get("access_token", '')


if __name__ == "__main__":
    token = get_access_token()
    
    headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
    }
    company = 'RGMC - Core Build'
    brandid = 27
    dimension = 'BRAND'


    
    # print(headers)

    # print("Access Token:\n {}".format(headers))

    # url = f"https://api.businesscentral.dynamics.com/v2.0/{TENANT_ID}/DEV/api/v2.0/customers"
    url = f"https://api.businesscentral.dynamics.com/v2.0/{TENANT_ID}/Production/api/v2.0/companies/"
    url2 = f"https://api.businesscentral.dynamics.com/{TENANT_ID}/Production/api/v2.0/companies"
    url3 = f"https://api.businesscentral.dynamics.com/v2.0/ca3ca144-09d9-42dd-920a-c72aedd54dd6/DEV/ODataV4/Company('CGI')/SalesOrder"
    url3 = f"https://api.businesscentral.dynamics.com/v2.0/ca3ca144-09d9-42dd-920a-c72aedd54dd6/DEV/ODataV4/Company('{company}')"

    response = requests.get(url3, headers=headers)

    # print(response)
    # print(response.status_code)
    print(response.json())