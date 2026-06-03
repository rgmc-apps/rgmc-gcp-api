"""Routers Init."""

from .health import healthrouter
from .sbic_routes.CustomerPOUL import customerpoul_router
from .sbic_routes.CustomerRA import customer_ra_router
from .bigquery_bridge import BigqueryBridge
from .tradeportal_routes import tradeportal_router
from .sbic_routes.handoff import handoff_router
from .bc_routes import bc_router, sales_order_router, item_router, customer_router, sales_credit_memo_router, retail_customer_router, sales_return_order_router, rgmc_contact_router, item_category_router, contact_picture_router