<h1 align="center">
  <span style="color:#A07320">RGMC GCP API</span>
</h1>

<p align="center">
  <span style="color:#666">A unified FastAPI backend bridging Business Central, Trade Portal, SBIC, and Google Cloud — deployed on Cloud Run.</span>
</p>

<p align="center">
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.128.0-009688?logo=fastapi&logoColor=white" alt="FastAPI"/></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python"/></a>
  <a href="https://cloud.google.com/run"><img src="https://img.shields.io/badge/Cloud%20Run-Deployed-4285F4?logo=googlecloud&logoColor=white" alt="Cloud Run"/></a>
  <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white" alt="Docker"/></a>
  <a href="https://learn.microsoft.com/en-us/dynamics365/business-central/"><img src="https://img.shields.io/badge/Business%20Central-OData%20v2.0-00BCF2?logo=microsoft&logoColor=white" alt="Business Central"/></a>
  <a href="https://pydantic.dev/"><img src="https://img.shields.io/badge/Pydantic-2.12.5-E92063?logo=pydantic&logoColor=white" alt="Pydantic"/></a>
</p>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture at a Glance](#-architecture-at-a-glance)
- [Tech Stack](#-tech-stack)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Setup & Installation](#-setup--installation)
- [Environment Variables](#-environment-variables)
- [Running the App](#-running-the-app)
- [Building for Production](#-building-for-production)
- [Deploying to Cloud Run](#-deploying-to-cloud-run)
- [API Endpoints](#-api-endpoints)
  - [System & Health](#system--health)
  - [SBIC Routes](#sbic-routes)
  - [Trade Portal Routes](#trade-portal-routes)
  - [Business Central — Standard API](#business-central--standard-api-v20)
  - [Business Central — RGMC Custom API](#business-central--rgmc-custom-api)
- [Business Central Authentication Flow](#-business-central-authentication-flow)
- [Data Flow: A Request End-to-End](#-data-flow-a-request-end-to-end)
- [OData Query Parameters](#-odata-query-parameters)
- [API Groups & BC Page Map](#-api-groups--bc-page-map)

---

## 🔍 Overview

The RGMC GCP API is the central nervous system of RGMC's cloud operations. It exposes a single, versioned REST API that talks to three distinct backends:

| Backend | What it serves |
|---|---|
| **Microsoft Business Central** | ERP data — sales orders, customers, contacts, items, credit memos, return orders, dimensions |
| **Trade Portal (MSSQL)** | Internal product catalog — brands, SKUs, packing lists, seasons, pull-outs, markdowns |
| **SBIC BigQuery** | Document AI pipeline for customer PO upload and remittance advice bridging |

Everything runs inside a Docker container, deployed to Google Cloud Run. The Swagger UI lives at `/swagger`. Process timing is injected into every response via the `X-Process-Time` header.

> 💡 **Why two BC API prefixes?** `/bc/*` targets BC's standard `api/v2.0` namespace. `/bc/custom/*` targets RGMC's in-house AL extensions at `api/rgmc/rgmccustom/v1.0` — these are custom pages not available in the standard API.

---

## 🏗 Architecture at a Glance

```
                        +---------------------------+
  Client / App          |      RGMC GCP API         |
  (Mobile / Web)        |   FastAPI + uvicorn        |
        |               |   Cloud Run :: port 8080   |
        +-------------> +------------+--------------+
                                     |
              +----------------------+---------------------+
              |                      |                     |
    +---------v---------+  +---------v--------+  +---------v---------+
    | Business Central  |  |  Trade Portal    |  |   SBIC BigQuery   |
    |  OData API v2.0   |  |  MSSQL Database  |  |   Document AI     |
    |  + RGMC Custom AL |  |  (SQLAlchemy)    |  |   Pipeline        |
    +-------------------+  +------------------+  +-------------------+
              |
     OAuth2 Client Credentials
     (Bearer token cached in-memory,
      auto-refreshed 60s before expiry)
```

---

## 🛠 Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Web Framework | FastAPI | 0.128.0 |
| Language | Python | 3.12.6 |
| ASGI Server | uvicorn + gunicorn | 0.40.0 |
| Data Validation | Pydantic | 2.12.5 |
| SQL ORM | SQLAlchemy | 2.0.46 |
| MSSQL Driver | pyodbc | 5.3.0 |
| HTTP Client | requests | 2.32.5 |
| BigQuery | google-cloud-bigquery + pandas-gbq | 3.38.0 / 0.31.0 |
| Cloud Logging | google-cloud-logging | 3.13.0 |
| Cloud Storage | google-cloud-storage | 3.9.0 |
| Data Frames | pandas | 2.3.3 |
| File Upload | python-multipart | 0.0.20 |
| Container | Docker (python:3.12.6-slim) | — |
| Deployment | Google Cloud Run | — |

---

## ✨ Features

### <span style="color:#2a9d8f">🔗 Business Central Integration</span>

- **Token caching** — OAuth2 client credentials token cached in-memory, refreshed 60 seconds before expiry. Thread-safe via `threading.Lock()`.
- **Company ID caching** — BC company GUID resolved once per company name, then cached for the process lifetime.
- **OData pagination** — `_fetch_all_pages()` follows `@odata.nextLink` automatically; callers always get the full result set, even across thousands of records.
- **Dual API namespaces** — Standard `api/v2.0` functions (`bc_*`) and RGMC custom AL extension functions (`rgmc_*`) with identical call signatures.
- **Contact pictures** — Binary image served with auto-detected `Content-Type` (JPEG, PNG, GIF, BMP, WebP via magic bytes). Uploaded as base64 via multipart form.
- **Two-step order creation** — Sales orders and return orders POST the header first, then create each line item under the returned order ID to satisfy BC's data model.

### <span style="color:#2a9d8f">🏪 Trade Portal</span>

- Password-based login with symmetric decryption (`decrypt()` in `generic_functions.py`).
- Read-only endpoints for the full product catalog: brands, categories, colors, companies, customers, locations, products, SKUs, seasons, sizes, packing lists, pull-outs, and markdowns.
- Filterable list endpoints — most accept `is_active`, `brand_id`, `season_id`, and similar query parameters.

### <span style="color:#2a9d8f">📊 SBIC / BigQuery</span>

- Trigger-based architecture: POST endpoints fire BigQuery bridge jobs on demand or on schedule.
- Rate-limited remittance advice endpoint (`rate_limiter.py`).
- Cloud Logging integration for audit trails.

### <span style="color:#2a9d8f">🚀 Infrastructure</span>

- Cloud Run revision code surfaced in the API title (`K_REVISION` env var).
- `X-Process-Time` header on every response via FastAPI middleware.
- Gunicorn with 3 workers × 2 threads, uvicorn worker class, 30-second timeout.
- Non-privileged `appuser` in Docker (UID 10001) for container security.

---

## 📁 Project Structure

```
rgmc-gcp-api/
├── Dockerfile                           # python:3.12.6-slim, port 8080, non-root user
├── compose.yaml                         # Docker Compose for local dev (port 8080:8080)
├── requirements.txt                     # All Python dependencies (pinned versions)
└── src/
    ├── main.py                          # FastAPI app init, router registration, middleware
    ├── config.py                        # All env vars with sensible defaults
    ├── logger.py                        # Structured logging setup
    ├── gunicorn_config.py               # 3 workers, 2 threads, uvicorn worker class
    ├── types_py.py                      # Shared Pydantic types (HealthcheckResponse, etc.)
    ├── mappings.py                      # Field-name mapping utilities
    ├── db/
    │   └── dbconn.py                    # MSSQL connection factory (SQLAlchemy + pyodbc)
    ├── services/
    │   ├── bc_functions.py              # All BC API calls — token, company lookup, CRUD helpers
    │   ├── bc_api.py                    # Lower-level BC HTTP utilities
    │   ├── generic_functions.py         # encrypt/decrypt and other shared utilities
    │   └── send_mail.py                 # SMTP email sender
    ├── models/
    │   ├── bc_models/
    │   │   ├── customer_models.py       # CustomerCreate, CustomerUpdate
    │   │   ├── item_models.py           # ItemCreate, ItemUpdate
    │   │   ├── item_category_models.py  # ItemCategoryCreate, ItemCategoryUpdate
    │   │   ├── retail_customer_models.py
    │   │   ├── rgmc_contact_models.py   # RgmcContactCreate, RgmcContactUpdate
    │   │   ├── sales_credit_memo_models.py
    │   │   ├── sales_order_models.py    # SalesOrderCreate + SalesOrderLineCreate
    │   │   └── sales_return_order_models.py
    │   ├── sbic_models/
    │   │   ├── Company.py
    │   │   └── CustomerPOUL.py
    │   └── tradeportal_models/
    │       ├── brand_models.py          # Brand, BrandLookUpSM, KCCBrandLookUp, etc.
    │       ├── category_models.py
    │       ├── color_models.py
    │       ├── company_models.py
    │       ├── customer_models.py
    │       ├── location_models.py
    │       ├── markdown_models.py
    │       ├── packing_list_models.py
    │       ├── product_models.py        # Season, Size, SMSize, Product, ProductPrice
    │       ├── pullout_models.py
    │       ├── sku_models.py
    │       └── system_models.py
    └── routers/
        ├── health.py                    # GET /healthcheck
        ├── bigquery_bridge.py           # BigQuery bridge runner
        ├── sbic_routes/
        │   ├── CustomerPOUL.py          # POST /customerpoul/runbridge/
        │   ├── CustomerRA.py            # POST /customerra/runbridge/
        │   ├── handoff.py               # SBIC handoff endpoints
        │   └── rate_limiter.py          # Request rate limiter (CustomerRA)
        ├── tradeportal_routes/
        │   ├── auth_routes.py           # POST /tradeportal/login
        │   ├── brand_routes.py          # GET /tradeportal/brands/*
        │   ├── category_routes.py
        │   ├── color_routes.py
        │   ├── company_routes.py
        │   ├── customer_routes.py
        │   ├── location_routes.py
        │   ├── markdown_routes.py
        │   ├── packing_list_routes.py
        │   ├── product_routes.py        # seasons, sizes, sm-sizes, products, product-prices
        │   ├── pullout_routes.py
        │   ├── sku_routes.py
        │   └── system_routes.py
        └── bc_routes/
            ├── bc_routes.py              # /bc/token, companies, brands, departments, contacts
            ├── sales_order_routes.py     # /bc/sales-orders CRUD + lines CRUD
            ├── item_routes.py            # /bc/items CRUD
            ├── customer_routes.py        # /bc/customers CRUD
            ├── sales_credit_memo_routes.py  # /bc/sales-credit-memos CRUD
            ├── item_category_routes.py   # /bc/item-categories CRUD
            ├── retail_customer_routes.py # /bc/custom/retail-customers CRUD
            ├── sales_return_order_routes.py # /bc/custom/sales-return-orders CRUD + lines
            ├── rgmc_contact_routes.py    # /bc/custom/contacts CRUD + picture endpoints
            ├── rgmc_item_routes.py       # /bc/custom/items (read-only)
            └── rgmc_item_family_routes.py # /bc/custom/item-families (read-only)
```

---

## ⚙️ Setup & Installation

### Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.12+ | Runtime |
| pip | latest | Package manager |
| Docker | 24+ | Containerization |
| ODBC Driver 17 | — | MSSQL connectivity |
| gcloud CLI | latest | Cloud Run deployment |

```bash
# 1. Clone the repository
git clone <repo-url>
cd rgmc-gcp-api

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 3. Install all dependencies
pip install -r requirements.txt
```

> ⚠️ **ODBC Driver required.** MSSQL connectivity via `pyodbc` requires **ODBC Driver 17 for SQL Server** installed on the host. Download it from Microsoft for Windows, macOS, or Linux before running locally.

---

## 🔐 Environment Variables

All variables are read in `src/config.py`. Every variable has a fallback default so the app starts without a `.env` file, but production values must be set as Cloud Run environment variables or secrets.

| Variable | Default | Description |
|---|---|---|
| `API_TAG_VERSION` | `0.1.0` | Displayed in Swagger UI version badge |
| `PROJECT_ID` | `RGMC0001` | Internal project identifier |
| `K_REVISION` | `00001` | Cloud Run revision — shown in API title as `Release - {code}` |
| **MSSQL** | | |
| `MSSQL_SERVER` | `localhost` | SQL Server hostname or IP |
| `MSSQL_USER` | `sa` | SQL Server login username |
| `MSSQL_PASSWORD` | `sqlserver` | SQL Server login password |
| `MSSQL_DRIVER` | `ODBC Driver 17 for SQL Server` | pyodbc driver string |
| `MSSQL_INSTANCE` | _(empty)_ | Named instance (e.g. `SQLEXPRESS`), leave blank for default |
| **BigQuery** | | |
| `BIGQUERY_PROJECT_ID` | `default_project` | GCP project ID for BigQuery queries |
| `BIGQUERY_DATASET_ID` | `default_dataset` | BigQuery dataset name |
| `BQ_TABLE_VERSION` | `v1` | Table version suffix |
| **Email** | | |
| `MAIL_RECIPIENT` | `it.arellanoerwin@gmail.com` | Default notification recipient |
| `MAIL_SENDER` | `rgmc.apps@gmail.com` | Outbound email address |
| `MAIL_PASSWORD` | `password` | SMTP app password |
| `MAIL_PORT` | `587` | SMTP port (587 = STARTTLS, 465 = SSL) |
| `MAIL_SERVER` | `smtp.gmail.com` | SMTP server hostname |
| **Security** | | |
| `PASS_KEY` | `default_pass_key` | Symmetric key for Trade Portal password encryption |
| **Business Central** | | |
| `BC_CLIENT_ID` | _(see config.py)_ | Azure AD app registration client ID |
| `BC_CLIENT_SECRET` | _(see config.py)_ | Azure AD app registration client secret |
| `BC_TENANT_ID` | _(see config.py)_ | Azure AD tenant ID |
| `BC_SCOPE` | `https://api.businesscentral.dynamics.com/.default` | OAuth2 scope for BC |
| `BC_AUTH_URL` | `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token` | Token endpoint (auto-built from BC_TENANT_ID) |
| `BC_ENVIRONMENT` | `UAT` | BC environment name (e.g. `Production`, `UAT`) |
| `BC_COMPANY` | `CGI` | Default BC company name used when `?company=` is not specified |

> 📌 **Production note:** `BC_CLIENT_ID`, `BC_CLIENT_SECRET`, and `BC_TENANT_ID` have non-empty defaults in `config.py` for development convenience. Always override these via Cloud Run secrets in production environments.

---

## 🚀 Running the App

### Local — uvicorn with hot reload

```bash
uvicorn src.main:api --host 0.0.0.0 --port 8080 --reload
```

Swagger UI: [http://localhost:8080/swagger](http://localhost:8080/swagger)

### Local — Docker Compose

```bash
docker compose up --build
```

The `compose.yaml` maps container port `8080` to host port `8080`.

### Local — gunicorn (production-like)

```bash
gunicorn src.main:api \
  --workers 3 \
  --threads 2 \
  --timeout 30 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8080
```

### Verify the app is running

```bash
curl http://localhost:8080/healthcheck
# {"message":"We're on the air.","version":"0.1.0","time":"2026-06-05T..."}

curl http://localhost:8080/index
# {"status":"Api is running"}

curl http://localhost:8080/checkdb
# {"database_status":"connected","result":["SBIC",...]}
```

---

## 🐳 Building for Production

```bash
# Build the Docker image
docker build -t rgmc-gcp-api .

# Run locally to verify before pushing
docker run -p 8080:8080 \
  -e BC_CLIENT_ID=your-client-id \
  -e BC_CLIENT_SECRET=your-secret \
  -e BC_TENANT_ID=your-tenant-id \
  -e BC_ENVIRONMENT=Production \
  -e BC_COMPANY=RGMC \
  -e MSSQL_SERVER=your-sql-server \
  -e MSSQL_USER=your-user \
  -e MSSQL_PASSWORD=your-password \
  rgmc-gcp-api
```

The Docker image:
- Base image: `python:3.12.6-slim`
- Dependencies installed in a cached layer (cache-mounted `pip`)
- Runs as non-privileged `appuser` (UID 10001) — no root access
- Exposes port `8080`
- CMD: `uvicorn src.main:api --host=0.0.0.0 --port=8080`

---

## ☁️ Deploying to Cloud Run

```bash
# Step 1: Authenticate
gcloud auth login
gcloud auth configure-docker us-central1-docker.pkg.dev

# Step 2: Build and push to Artifact Registry
gcloud builds submit --tag gcr.io/<PROJECT_ID>/rgmc-gcp-api

# Step 3: Deploy to Cloud Run
gcloud run deploy rgmc-gcp-api \
  --image gcr.io/<PROJECT_ID>/rgmc-gcp-api \
  --platform managed \
  --region us-central1 \
  --port 8080 \
  --set-env-vars BC_ENVIRONMENT=Production,BC_COMPANY=RGMC \
  --set-secrets BC_CLIENT_SECRET=bc-client-secret:latest,MSSQL_PASSWORD=mssql-password:latest \
  --allow-unauthenticated
```

The `K_REVISION` env var is injected automatically by Cloud Run — it appears in the API title as `RGMC API : (Release - <revision>)`.

---

## 📡 API Endpoints

> 💡 All BC endpoints accept an optional `?company=<name>` query parameter to override the default `BC_COMPANY`. The interactive Swagger docs are at `/swagger`.

---

### System & Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/index` | Liveness check — `{"status": "Api is running"}` |
| `GET` | `/healthcheck` | Health check with API version and current timestamp |
| `GET` | `/checkdb` | Tests MSSQL connection — returns first column of `Company` table |
| `GET` | `/checkBigQuery` | Tests BigQuery — returns 5 rows from `int_document_ai_detail` |

---

### SBIC Routes

#### <span style="color:#555">Customer PO Upload (POUL)</span>

| Method | Path | Description |
|---|---|---|
| `POST` | `/customerpoul/runbridge/` | Trigger the CustomerPOUL BigQuery bridge job |
| `POST` | `/customerpoul/runbridge/onlinesalespo/` | Trigger the Online Sales PO bridge job |

**Query param:** `?method=manual` (default) or `?method=auto`

#### <span style="color:#555">Customer Remittance Advice (RA)</span>

| Method | Path | Description |
|---|---|---|
| `POST` | `/customerra/runbridge/` | Trigger the Customer RA bridge job _(rate-limited)_ |

---

### Trade Portal Routes

All Trade Portal routes are prefixed with `/tradeportal`.

#### <span style="color:#555">🔑 Authentication</span>

| Method | Path | Description |
|---|---|---|
| `POST` | `/tradeportal/login` | Validate `secCode` + `password`, return user profile |

```json
// POST /tradeportal/login — request body
{
  "secCode": "USR001",
  "password": "yourpassword"
}

// 200 Response
{
  "secCode": "USR001",
  "typeCode": "ADMIN",
  "name": "Juan dela Cruz",
  "isActive": true,
  "expirationDate": "2026-12-31"
}
```

#### <span style="color:#555">🏷 Brands</span>

| Method | Path | Query Params | Description |
|---|---|---|---|
| `GET` | `/tradeportal/brands` | `?is_active=true` | List all brands |
| `GET` | `/tradeportal/brands/{brand_id}` | — | Get brand by ID |
| `GET` | `/tradeportal/brand-lookups-sm` | `?brand_id=` | SM brand lookup |
| `GET` | `/tradeportal/kcc-brand-lookups` | `?brand_id=` | KCC brand lookup |
| `GET` | `/tradeportal/sm-brand-subclasses` | `?brand_id=` | SM brand sub-classes |
| `GET` | `/tradeportal/lm-brand-site-lookups` | `?brand_id=&customer_site_id=` | LM brand-site lookup |

#### <span style="color:#555">🛍 Products</span>

| Method | Path | Query Params | Description |
|---|---|---|---|
| `GET` | `/tradeportal/seasons` | `?is_active=true` | List seasons |
| `GET` | `/tradeportal/seasons/{season_id}` | — | Get season by ID |
| `GET` | `/tradeportal/sizes` | `?item_group_id=&is_active=` | List sizes |
| `GET` | `/tradeportal/sizes/{size_id}` | — | Get size by ID |
| `GET` | `/tradeportal/sm-sizes` | — | List SM sizes |
| `GET` | `/tradeportal/products` | `?brand_id=&category_id=&season_id=&is_active=&is_markdown=` | List products with filters |
| `GET` | `/tradeportal/products/{product_id}` | — | Get product by ID |
| `GET` | `/tradeportal/product-prices` | `?product_id=&is_active=` | List product prices |

#### <span style="color:#555">📦 Catalog & Operations</span>

| Method | Path | Description |
|---|---|---|
| `GET` | `/tradeportal/categories` | List product categories |
| `GET` | `/tradeportal/categories/{id}` | Get category by ID |
| `GET` | `/tradeportal/colors` | List colors |
| `GET` | `/tradeportal/colors/{id}` | Get color by ID |
| `GET` | `/tradeportal/companies` | List Trade Portal companies |
| `GET` | `/tradeportal/companies/{id}` | Get company by ID |
| `GET` | `/tradeportal/customers` | List Trade Portal customers |
| `GET` | `/tradeportal/customers/{id}` | Get customer by ID |
| `GET` | `/tradeportal/locations` | List locations |
| `GET` | `/tradeportal/locations/{id}` | Get location by ID |
| `GET` | `/tradeportal/skus` | List SKUs |
| `GET` | `/tradeportal/skus/{id}` | Get SKU by ID |
| `GET` | `/tradeportal/packing-lists` | List packing lists |
| `GET` | `/tradeportal/packing-lists/{id}` | Get packing list by ID |
| `GET` | `/tradeportal/pullouts` | List pull-out records |
| `GET` | `/tradeportal/pullouts/{id}` | Get pull-out by ID |
| `GET` | `/tradeportal/markdowns` | List markdown records |
| `GET` | `/tradeportal/markdowns/{id}` | Get markdown by ID |
| `GET` | `/tradeportal/system` | System table data |

---

### Business Central — Standard API (v2.0)

Routes hit BC's `api/v2.0` namespace. Prefix: `/bc`.

#### <span style="color:#555">🔧 Utility</span>

| Method | Path | Description |
|---|---|---|
| `GET` | `/bc/token` | Returns a valid BC Bearer token (for debugging) |
| `GET` | `/bc/companies` | List all BC companies |
| `GET` | `/bc/companies/{company_id}` | Get a specific BC company by GUID |
| `GET` | `/bc/dimensions` | All BC dimension codes |
| `GET` | `/bc/brands` | Dimension values for the `BRAND` dimension code |
| `GET` | `/bc/departments` | Dimension values for the `DEPARTMENT` dimension code |
| `GET` | `/bc/contacts` | Standard BC contacts (v2.0 namespace) |

#### <span style="color:#555">🛒 Sales Orders</span>

| Method | Path | Query Params | Description |
|---|---|---|---|
| `GET` | `/bc/sales-orders` | `?filter=&expand=salesOrderLines&select=` | List sales orders |
| `GET` | `/bc/sales-orders/{order_id}` | `?expand=salesOrderLines` | Get sales order by GUID |
| `POST` | `/bc/sales-orders` | — | Create a sales order (with optional lines) |
| `PATCH` | `/bc/sales-orders/{order_id}` | — | Update a sales order |
| `DELETE` | `/bc/sales-orders/{order_id}` | — | Delete a sales order |
| `GET` | `/bc/sales-orders/{order_id}/lines` | `?select=` | List all lines for an order |
| `POST` | `/bc/sales-orders/{order_id}/lines` | — | Add a line to an order |
| `PATCH` | `/bc/sales-orders/{order_id}/lines/{line_id}` | — | Update a line |
| `DELETE` | `/bc/sales-orders/{order_id}/lines/{line_id}` | — | Delete a line |

```json
// POST /bc/sales-orders — request body
{
  "customerNumber": "C00010",
  "orderDate": "2026-06-05",
  "requestedDeliveryDate": "2026-06-20",
  "lines": [
    {
      "itemNumber": "ITEM-001",
      "description": "Blue Polo Shirt",
      "quantity": 10,
      "unitPrice": 599.00,
      "discountPercent": 5
    }
  ]
}
```

> 📌 Lines sent in the `POST` body are created after the order header. Each line is a separate BC API call. The `lineType` is hardcoded to `"Item"`.

#### <span style="color:#555">📦 Items</span>

| Method | Path | Query Params | Description |
|---|---|---|---|
| `GET` | `/bc/items` | `?filter=&expand=&select=&category_code=` | List items; `category_code` is a shorthand filter |
| `GET` | `/bc/items/{item_id}` | `?expand=itemVariants` | Get item by GUID |
| `POST` | `/bc/items` | — | Create an item |
| `PATCH` | `/bc/items/{item_id}` | — | Update an item |
| `DELETE` | `/bc/items/{item_id}` | — | Delete an item |

#### <span style="color:#555">👤 Customers</span>

| Method | Path | Description |
|---|---|---|
| `GET` | `/bc/customers` | List all BC customers |
| `GET` | `/bc/customers/{customer_id}` | Get customer by GUID |
| `POST` | `/bc/customers` | Create a customer |
| `PATCH` | `/bc/customers/{customer_id}` | Update a customer |
| `DELETE` | `/bc/customers/{customer_id}` | Delete a customer |

#### <span style="color:#555">🧾 Sales Credit Memos</span>

| Method | Path | Description |
|---|---|---|
| `GET` | `/bc/sales-credit-memos` | List all sales credit memos |
| `GET` | `/bc/sales-credit-memos/{memo_id}` | Get credit memo by GUID |
| `POST` | `/bc/sales-credit-memos` | Create a credit memo |
| `PATCH` | `/bc/sales-credit-memos/{memo_id}` | Update a credit memo |
| `DELETE` | `/bc/sales-credit-memos/{memo_id}` | Delete a credit memo |

#### <span style="color:#555">🗂 Item Categories</span>

| Method | Path | Description |
|---|---|---|
| `GET` | `/bc/item-categories` | List all item categories |
| `GET` | `/bc/item-categories/{category_id}` | Get item category by GUID |
| `POST` | `/bc/item-categories` | Create an item category |
| `PATCH` | `/bc/item-categories/{category_id}` | Update an item category |
| `DELETE` | `/bc/item-categories/{category_id}` | Delete an item category |

---

### Business Central — RGMC Custom API

Routes hit RGMC's AL extension pages at `api/rgmc/rgmccustom/v1.0`. Prefix: `/bc/custom`.

#### <span style="color:#555">🛍 Retail Customers — Pag50200</span>

| Method | Path | Description |
|---|---|---|
| `GET` | `/bc/custom/retail-customers` | List RGMC retail customers |
| `GET` | `/bc/custom/retail-customers/{customer_id}` | Get retail customer by SystemId GUID |
| `POST` | `/bc/custom/retail-customers` | Create a retail customer |
| `PATCH` | `/bc/custom/retail-customers/{customer_id}` | Update a retail customer |
| `DELETE` | `/bc/custom/retail-customers/{customer_id}` | Delete a retail customer |

#### <span style="color:#555">↩️ Sales Return Orders — Pag50201 / Pag50202</span>

| Method | Path | Description |
|---|---|---|
| `GET` | `/bc/custom/sales-return-orders` | List return orders |
| `GET` | `/bc/custom/sales-return-orders/{order_id}` | Get return order by SystemId |
| `POST` | `/bc/custom/sales-return-orders` | Create a return order (with optional lines) |
| `PATCH` | `/bc/custom/sales-return-orders/{order_id}` | Update return order header |
| `DELETE` | `/bc/custom/sales-return-orders/{order_id}` | Delete return order |
| `GET` | `/bc/custom/sales-return-orders/{order_id}/lines` | List all lines |
| `GET` | `/bc/custom/sales-return-orders/{order_id}/lines/{line_id}` | Get a specific line |
| `POST` | `/bc/custom/sales-return-orders/{order_id}/lines` | Add a line |
| `PATCH` | `/bc/custom/sales-return-orders/{order_id}/lines/{line_id}` | Update a line |
| `DELETE` | `/bc/custom/sales-return-orders/{order_id}/lines/{line_id}` | Delete a line |

```json
// POST /bc/custom/sales-return-orders — request body
{
  "customerNumber": "RC00001",
  "lines": [
    {
      "itemNumber": "ITEM-005",
      "quantity": 2,
      "unitPrice": 799.00
    }
  ]
}
```

> 📌 The frontend field `customerNumber` is mapped internally to BC's `sellToCustomerNo` before the POST is sent.

#### <span style="color:#555">👥 Contacts — Pag50203 / Pag50204</span>

| Method | Path | Description |
|---|---|---|
| `GET` | `/bc/custom/contacts` | List RGMC contacts |
| `GET` | `/bc/custom/contacts/{contact_id}` | Get contact by SystemId |
| `POST` | `/bc/custom/contacts` | Create a contact |
| `PATCH` | `/bc/custom/contacts/{contact_id}` | Update a contact |
| `DELETE` | `/bc/custom/contacts/{contact_id}` | Delete a contact |
| `GET` | `/bc/custom/contacts/{contact_id}/picture` | Get contact photo — returns raw binary image |
| `PATCH` | `/bc/custom/contacts/{contact_id}/picture` | Upload contact photo (`multipart/form-data`, field: `file`) |
| `GET` | `/bc/custom/contacts/{contact_id}/picture/debug` | Debug — returns raw BC picture response metadata |

```bash
# Download a contact's photo as a JPEG file
curl "https://<service>/bc/custom/contacts/<guid>/picture?company=RGMC" \
  --output contact.jpg

# Upload a new photo (multipart form-data)
curl -X PATCH "https://<service>/bc/custom/contacts/<guid>/picture?company=RGMC" \
  -F "file=@photo.jpg"
```

```json
// GET .../picture/debug — response shape
{
  "bc_http_status": 200,
  "picture_b64_length": 174762,
  "picture_b64_prefix": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMC",
  "decoded_bytes": 130971,
  "hex_header": "ffd8ffe000104a464946000101",
  "detected_media_type": "image/jpeg",
  "bc_fields": ["id", "contactNo", "picture"]
}
```

> ⚠️ **Insert and Delete are disabled** on `contactPictures` (Page 50204). Only `GET` and `PATCH` are valid. The `{contact_id}` must be the contact's `SystemId` GUID — not the contact `No.` field.

#### <span style="color:#555">🏷 RGMC Items — Pag50205 (read-only)</span>

| Method | Path | Query Params | Description |
|---|---|---|---|
| `GET` | `/bc/custom/items` | `?category_code=&family_code=&filter=&select=` | List RGMC items with optional filters |
| `GET` | `/bc/custom/items/{item_id}` | — | Get RGMC item by SystemId |

#### <span style="color:#555">🗃 RGMC Item Families — Pag50206 (read-only)</span>

| Method | Path | Description |
|---|---|---|
| `GET` | `/bc/custom/item-families` | List RGMC item families |
| `GET` | `/bc/custom/item-families/{family_id}` | Get RGMC item family by SystemId |

---

## 🔐 Business Central Authentication Flow

BC uses OAuth2 Client Credentials. No user login — the API authenticates as an app with a client secret.

```
1. Client calls any /bc/* or /bc/custom/* endpoint
       |
       v
2. bc_functions.get_access_token() is called
       |
       +-- Is cached token still valid? (expires_at - 60s > now)
       |        YES -> return _token_cache["token"]  [no network call]
       |        NO  -> acquire new token
       |
       v
3. POST https://login.microsoftonline.com/{BC_TENANT_ID}/oauth2/v2.0/token
   Body: grant_type    = client_credentials
         client_id     = BC_CLIENT_ID
         client_secret = BC_CLIENT_SECRET
         scope         = https://api.businesscentral.dynamics.com/.default
       |
       v
4. Token stored in _token_cache with expiry = now + expires_in (typically 3600s)
   threading.Lock() ensures only one thread fetches at a time
       |
       v
5. Authorization: Bearer <token>
   added to every BC HTTP request via _auth_headers()
       |
       v
6. Company-scoped calls: get_company_id(company_name)
   Calls /api/v2.0/companies once, finds GUID by name
   Result cached in _company_id_cache (never expires in-process)
       |
       v
7. Final URL pattern:
   Standard:  .../v2.0/{tenant}/{env}/api/v2.0/companies({guid})/{table}
   RGMC Custom: .../v2.0/{tenant}/{env}/api/rgmc/rgmccustom/v1.0/companies({guid})/{table}
```

---

## 🔄 Data Flow: A Request End-to-End

Here's exactly what happens when a client calls `GET /bc/custom/contacts/{id}/picture`:

```
Client
  |
  | GET /bc/custom/contacts/{guid}/picture?company=RGMC
  v
FastAPI middleware (main.py)
  |-- timer starts for X-Process-Time header
  |
  v
rgmc_contact_router (rgmc_contact_routes.py)
  |-- route matched: /{contact_id}/picture
  |-- calls rgmc_get_contact_picture(contact_id, company_name="RGMC")
  |
  v
bc_functions.py :: rgmc_get_contact_picture()
  |-- get_company_id("RGMC") -> cached GUID
  |-- builds URL: .../api/rgmc/rgmccustom/v1.0/companies({guid})/contactPictures({contact_id})
  |-- GET with Bearer token
  |-- _safe_json(response) -> {"id":..., "contactNo":..., "picture":"<base64 string>"}
  |
  v
rgmc_contact_routes.py :: get_contact_picture()
  |-- reads data["picture"]  (base64 string from BC)
  |-- base64.b64decode() -> raw bytes
  |-- _detect_media_type(bytes) -> "image/jpeg"  (magic bytes: FF D8 FF)
  |-- validates len(bytes) >= 64  (guards against AL Text field truncation)
  |
  v
FastAPI Response(content=<bytes>, media_type="image/jpeg")
  |-- X-Process-Time: 0.342 header added
  |
  v
Client receives binary JPEG image
```

---

## 🔎 OData Query Parameters

All BC list endpoints accept OData query parameters as URL query strings:

| Parameter | Example | Effect |
|---|---|---|
| `filter` | `?filter=customerNo eq 'C00001'` | OData `$filter` — server-side record filtering |
| `expand` | `?expand=salesOrderLines` | OData `$expand` — inline related records |
| `select` | `?select=id,number,customerNo` | OData `$select` — return only specific fields |
| `category_code` | `?category_code=APPAREL` | Shorthand: builds `itemCategoryCode eq 'APPAREL'` filter |
| `family_code` | `?family_code=POLO` | Shorthand: builds `familyCode eq 'POLO'` filter |
| `company` | `?company=RGMC` | Override default `BC_COMPANY` env var for this request only |

---

## 📊 API Groups & BC Page Map

```
 BC Standard API (api/v2.0)               RGMC Custom AL (api/rgmc/rgmccustom/v1.0)
 ====================================      =============================================
 /bc/companies     -> companies            /bc/custom/retail-customers   -> Pag50200
 /bc/contacts      -> contacts             /bc/custom/sales-return-orders -> Pag50201
 /bc/brands        -> dimensionValues      /bc/custom/sales-return-orders/*/lines -> Pag50202
 /bc/departments   -> dimensionValues      /bc/custom/contacts            -> Pag50203
 /bc/items         -> items                /bc/custom/contacts/*/picture  -> Pag50204
 /bc/item-categories -> itemCategories     /bc/custom/items               -> Pag50205
 /bc/customers     -> customers            /bc/custom/item-families       -> Pag50206
 /bc/sales-orders  -> salesOrders
 /bc/sales-orders/*/lines -> salesOrderLines
 /bc/sales-credit-memos -> salesCreditMemos
```

---

## 📄 License

Private — RGMC Internal Use Only.
All rights reserved © RGMC.
