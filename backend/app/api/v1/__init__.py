"""
API v1 Router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    quotes,
    sales_orders,
    integration,
    production_orders,
    print_jobs,
    inventory,
    products,
    items,
    materials,
    payments,
    shipping,
    internal,
    vendors,
    purchase_orders,
    amazon_import,
    work_centers,
    routings,
    mrp,
)
from app.api.v1.endpoints.admin import router as admin_router

router = APIRouter()

# Include endpoint routers

# Authentication (no additional prefix, uses /auth from router)
router.include_router(auth.router)

# Quote System (Phase 2B - no additional prefix, uses /quotes from router)
router.include_router(quotes.router)

# Sales Order System (Phase 2C - no additional prefix, uses /sales-orders from router)
router.include_router(sales_orders.router)

router.include_router(
    products.router,
    prefix="/products",
    tags=["products"]
)

# Items API (Phase 4 - unified item management with categories)
router.include_router(
    items.router,
    prefix="/items",
    tags=["items"]
)

router.include_router(
    integration.router,
    prefix="/integration",
    tags=["integration"]
)

router.include_router(
    production_orders.router,
    prefix="/production-orders",
    tags=["production"]
)

router.include_router(
    print_jobs.router,
    prefix="/print-jobs",
    tags=["print-jobs"]
)

router.include_router(
    inventory.router,
    prefix="/inventory",
    tags=["inventory"]
)

router.include_router(
    materials.router,
    prefix="/materials",
    tags=["materials"]
)

# Payments (Stripe integration)
router.include_router(payments.router)

# Shipping (EasyPost integration)
router.include_router(shipping.router)

# Admin (BOM management, dashboard, etc. - requires admin auth)
router.include_router(
    admin_router,
    prefix="/admin",
    tags=["admin"]
)

# Internal API (service-to-service communication - ML Dashboard, etc.)
# See FUTURE_ARCHITECTURE.md for architectural decisions
router.include_router(internal.router)

# Purchasing Module (Phase 4B)
router.include_router(
    vendors.router,
    prefix="/vendors",
    tags=["vendors"]
)

router.include_router(
    purchase_orders.router,
    prefix="/purchase-orders",
    tags=["purchase-orders"]
)

# Amazon Import (CSV import for purchasing)
router.include_router(
    amazon_import.router,
    prefix="/import/amazon",
    tags=["import"]
)

# Manufacturing Routes (Phase 4C)
router.include_router(
    work_centers.router,
    prefix="/work-centers",
    tags=["manufacturing"]
)

router.include_router(
    routings.router,
    prefix="/routings",
    tags=["manufacturing"]
)

# MRP (Material Requirements Planning) - Phase 5B
router.include_router(mrp.router)
