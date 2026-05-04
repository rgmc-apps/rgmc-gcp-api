"""Trade Portal Routes."""
from fastapi import APIRouter
from .auth_routes import auth_router
from .brand_routes import brand_router
from .category_routes import category_router
from .color_routes import color_router
from .company_routes import company_router
from .customer_routes import customer_router
from .location_routes import location_router
from .product_routes import product_router
from .sku_routes import sku_router
from .packing_list_routes import packing_list_router
from .pullout_routes import pullout_router
from .markdown_routes import markdown_router
from .system_routes import system_router

tradeportal_router = APIRouter(prefix="/tradeportal")
tradeportal_router.include_router(auth_router)
tradeportal_router.include_router(brand_router)
tradeportal_router.include_router(category_router)
tradeportal_router.include_router(color_router)
tradeportal_router.include_router(company_router)
tradeportal_router.include_router(customer_router)
tradeportal_router.include_router(location_router)
tradeportal_router.include_router(product_router)
tradeportal_router.include_router(sku_router)
tradeportal_router.include_router(packing_list_router)
tradeportal_router.include_router(pullout_router)
tradeportal_router.include_router(markdown_router)
tradeportal_router.include_router(system_router)
