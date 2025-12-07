"""
API v1 Router - FilaOps Open Source
"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    sales_orders,
    production_orders,
    inventory,
    products,
    items,
    materials,
    vendors,
    purchase_orders,
    amazon_import,
    work_centers,
    routings,
    mrp,
)
from app.api.v1.endpoints.admin import router as admin_router

router = APIRouter()

# Authentication
router.include_router(auth.router)

# Sales Orders
router.include_router(sales_orders.router)

# Products
router.include_router(
    products.router,
    prefix="/products",
    tags=["products"]
)

# Items (unified item management)
router.include_router(
    items.router,
    prefix="/items",
    tags=["items"]
)

# Production Orders
router.include_router(
    production_orders.router,
    prefix="/production-orders",
    tags=["production"]
)

# Inventory
router.include_router(
    inventory.router,
    prefix="/inventory",
    tags=["inventory"]
)

# Materials
router.include_router(
    materials.router,
    prefix="/materials",
    tags=["materials"]
)

# Admin (BOM management, dashboard, traceability)
router.include_router(
    admin_router,
    prefix="/admin",
    tags=["admin"]
)

# Vendors
router.include_router(
    vendors.router,
    prefix="/vendors",
    tags=["vendors"]
)

# Purchase Orders
router.include_router(
    purchase_orders.router,
    prefix="/purchase-orders",
    tags=["purchase-orders"]
)

# Amazon Import
router.include_router(
    amazon_import.router,
    prefix="/import/amazon",
    tags=["import"]
)

# Work Centers
router.include_router(
    work_centers.router,
    prefix="/work-centers",
    tags=["manufacturing"]
)

# Routings
router.include_router(
    routings.router,
    prefix="/routings",
    tags=["manufacturing"]
)

# MRP (Material Requirements Planning)
router.include_router(mrp.router)
