# rgmc-gcp-api
A scaffold fast api python services to be deployed via google cloud platform

# Target Modules
 - SBIC Data Bridge
 - Trade Portal API
 - Document AI helper

# Target Data Sources
 - Cloud SQL
 - Bigquery

---

# Business Central Endpoints

All BC endpoints are accessible via the `/swagger` docs page. An optional `company` query parameter is available on every endpoint to override the default configured company.

## BC Item Categories — `/bc/item-categories`

CRUD endpoints for the Business Central `itemCategories` table (standard BC API v2.0).

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/bc/item-categories` | List all item categories. Supports `filter` (OData `$filter`) and `select` (`$select`) query params. |
| `GET` | `/bc/item-categories/{category_id}` | Get a single item category by GUID. |
| `POST` | `/bc/item-categories` | Create a new item category. Body fields: `code`, `displayName`, `parentCategory`. |
| `PATCH` | `/bc/item-categories/{category_id}` | Update an item category. Body fields: `displayName`, `parentCategory`. |
| `DELETE` | `/bc/item-categories/{category_id}` | Delete an item category. Returns 204 on success. |

## BC RGMC Contact Pictures — `/bc/custom/contacts/{contact_id}/picture`

Sub-resource endpoints for managing profile pictures on RGMC custom API contacts (`api/rgmc/rgmccustom/v1.0`). Picture records are owned by BC — a picture record is created automatically when the contact is created; use the metadata endpoint to retrieve the picture ID before calling the content/update/delete endpoints.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/bc/custom/contacts/{contact_id}/picture` | Get picture metadata for a contact (id, width, height, contentType). |
| `GET` | `/bc/custom/contacts/{contact_id}/picture/{picture_id}/content` | Download the raw image bytes. Response content-type matches the stored image type. |
| `PATCH` | `/bc/custom/contacts/{contact_id}/picture/{picture_id}` | Upload or replace the contact's picture. Accepts `multipart/form-data` with an image file field. |
| `DELETE` | `/bc/custom/contacts/{contact_id}/picture/{picture_id}` | Delete the contact's picture. Returns 204 on success. |
