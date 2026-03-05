"""Routers Init."""

from .health import healthrouter
from .sbic_routes.CustomerPOUL import customerpoul_router
from .sbic_routes.CustomerRA import customer_ra_router
from .bigquery_bridge import BigqueryBridge
