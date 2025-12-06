"""
Admin Dashboard Endpoints

Central hub for admin operations - provides summary data and navigation context
"""
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User
from app.models.quote import Quote
from app.models.sales_order import SalesOrder
from app.models.production_order import ProductionOrder
from app.models.bom import BOM
from app.models.product import Product
from app.api.v1.endpoints.auth import get_current_admin_user

router = APIRouter(prefix="/dashboard", tags=["Admin - Dashboard"])


# ============================================================================
# SCHEMAS
# ============================================================================

class ModuleInfo(BaseModel):
    """Info about an admin module"""
    name: str
    description: str
    route: str
    icon: str
    badge_count: Optional[int] = None
    badge_type: Optional[str] = None  # info, warning, error


class DashboardSummary(BaseModel):
    """Summary counts for dashboard"""
    # Quotes
    pending_quotes: int
    quotes_today: int

    # Orders
    pending_orders: int
    orders_needing_review: int
    orders_in_production: int
    orders_ready_to_ship: int

    # Production
    active_production_orders: int
    boms_needing_review: int

    # Revenue (last 30 days)
    revenue_30_days: Decimal
    orders_30_days: int


class DashboardResponse(BaseModel):
    """Full dashboard response"""
    summary: DashboardSummary
    modules: List[ModuleInfo]
    recent_orders: List[dict]
    pending_bom_reviews: List[dict]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/", response_model=DashboardResponse)
async def get_dashboard(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get admin dashboard with summary stats and module navigation.

    Admin only. This is the main hub for backoffice operations.
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    thirty_days_ago = now - timedelta(days=30)

    # ========== SUMMARY STATS ==========

    # Quotes
    pending_quotes = db.query(Quote).filter(Quote.status == "pending").count()
    quotes_today = db.query(Quote).filter(Quote.created_at >= today_start).count()

    # Orders needing attention
    pending_orders = db.query(SalesOrder).filter(
        SalesOrder.status.in_(["pending", "confirmed"])
    ).count()

    # Orders where BOM might need review (quote-based without approved BOM)
    orders_needing_review = (
        db.query(SalesOrder)
        .filter(
            SalesOrder.order_type == "quote_based",
            SalesOrder.status.in_(["pending", "confirmed"]),
        )
        .count()
    )

    orders_in_production = db.query(SalesOrder).filter(
        SalesOrder.status == "in_production"
    ).count()

    orders_ready_to_ship = db.query(SalesOrder).filter(
        SalesOrder.status == "ready_to_ship"
    ).count()

    # Production
    active_production_orders = db.query(ProductionOrder).filter(
        ProductionOrder.status.in_(["pending", "released", "in_progress"])
    ).count()

    # BOMs for custom products that might need review
    boms_needing_review = (
        db.query(BOM)
        .join(Product)
        .filter(
            Product.type == "custom",
            BOM.active == True,
        )
        .count()
    )

    # Revenue (last 30 days)
    revenue_result = (
        db.query(func.sum(SalesOrder.grand_total))
        .filter(
            SalesOrder.payment_status == "paid",
            SalesOrder.paid_at >= thirty_days_ago,
        )
        .scalar()
    )
    revenue_30_days = revenue_result or Decimal("0")

    orders_30_days = (
        db.query(SalesOrder)
        .filter(SalesOrder.created_at >= thirty_days_ago)
        .count()
    )

    summary = DashboardSummary(
        pending_quotes=pending_quotes,
        quotes_today=quotes_today,
        pending_orders=pending_orders,
        orders_needing_review=orders_needing_review,
        orders_in_production=orders_in_production,
        orders_ready_to_ship=orders_ready_to_ship,
        active_production_orders=active_production_orders,
        boms_needing_review=boms_needing_review,
        revenue_30_days=revenue_30_days,
        orders_30_days=orders_30_days,
    )

    # ========== MODULES ==========

    modules = [
        ModuleInfo(
            name="BOM Management",
            description="View and edit Bills of Materials",
            route="/admin/bom",
            icon="list",
            badge_count=boms_needing_review if boms_needing_review > 0 else None,
            badge_type="warning" if boms_needing_review > 0 else None,
        ),
        ModuleInfo(
            name="Order Review",
            description="Review and release orders to production",
            route="/admin/orders",
            icon="clipboard-check",
            badge_count=orders_needing_review if orders_needing_review > 0 else None,
            badge_type="info" if orders_needing_review > 0 else None,
        ),
        ModuleInfo(
            name="Production",
            description="Manage production orders and print jobs",
            route="/admin/production",
            icon="printer",
            badge_count=active_production_orders if active_production_orders > 0 else None,
            badge_type="info",
        ),
        ModuleInfo(
            name="Shipping",
            description="Create labels and ship orders",
            route="/admin/shipping",
            icon="truck",
            badge_count=orders_ready_to_ship if orders_ready_to_ship > 0 else None,
            badge_type="warning" if orders_ready_to_ship > 0 else None,
        ),
        ModuleInfo(
            name="Inventory",
            description="View stock levels and transactions",
            route="/admin/inventory",
            icon="archive",
        ),
        ModuleInfo(
            name="Products",
            description="Manage products and materials",
            route="/admin/products",
            icon="cube",
        ),
        ModuleInfo(
            name="Customers",
            description="View and manage customer accounts",
            route="/admin/customers",
            icon="users",
        ),
        ModuleInfo(
            name="Reports",
            description="Sales, production, and financial reports",
            route="/admin/reports",
            icon="chart-bar",
        ),
    ]

    # ========== RECENT ORDERS ==========

    recent_orders_query = (
        db.query(SalesOrder)
        .filter(SalesOrder.status.in_(["pending", "confirmed", "in_production"]))
        .order_by(desc(SalesOrder.created_at))
        .limit(10)
        .all()
    )

    recent_orders = [
        {
            "id": order.id,
            "order_number": order.order_number,
            "product_name": order.product_name,
            "status": order.status,
            "payment_status": order.payment_status,
            "grand_total": float(order.grand_total) if order.grand_total else 0,
            "created_at": order.created_at.isoformat(),
        }
        for order in recent_orders_query
    ]

    # ========== PENDING BOM REVIEWS ==========

    pending_bom_query = (
        db.query(BOM)
        .join(Product)
        .filter(
            Product.type == "custom",
            BOM.active == True,
        )
        .order_by(desc(BOM.created_at))
        .limit(10)
        .all()
    )

    pending_bom_reviews = [
        {
            "bom_id": bom.id,
            "product_sku": bom.product.sku if bom.product else None,
            "product_name": bom.product.name if bom.product else None,
            "total_cost": float(bom.total_cost) if bom.total_cost else None,
            "line_count": len(bom.lines),
            "created_at": bom.created_at.isoformat(),
        }
        for bom in pending_bom_query
    ]

    return DashboardResponse(
        summary=summary,
        modules=modules,
        recent_orders=recent_orders,
        pending_bom_reviews=pending_bom_reviews,
    )


@router.get("/summary")
async def get_dashboard_summary(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get dashboard summary stats organized by module.

    Returns counts for quotes, orders, production, and BOMs.
    """
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    # Quotes
    pending_quotes = db.query(Quote).filter(Quote.status == "pending").count()
    quotes_this_week = db.query(Quote).filter(Quote.created_at >= week_ago).count()

    # Orders
    confirmed_orders = db.query(SalesOrder).filter(SalesOrder.status == "confirmed").count()
    in_production_orders = db.query(SalesOrder).filter(SalesOrder.status == "in_production").count()
    ready_to_ship_orders = db.query(SalesOrder).filter(SalesOrder.status == "ready_to_ship").count()

    # Production
    production_in_progress = db.query(ProductionOrder).filter(
        ProductionOrder.status == "in_progress"
    ).count()
    production_scheduled = db.query(ProductionOrder).filter(
        ProductionOrder.status.in_(["pending", "released"])
    ).count()

    # BOMs
    boms_needing_review = (
        db.query(BOM)
        .join(Product)
        .filter(Product.type == "custom", BOM.active == True)
        .count()
    )
    active_boms = db.query(BOM).filter(BOM.active == True).count()

    return {
        "quotes": {
            "pending": pending_quotes,
            "this_week": quotes_this_week,
        },
        "orders": {
            "confirmed": confirmed_orders,
            "in_production": in_production_orders,
            "ready_to_ship": ready_to_ship_orders,
        },
        "production": {
            "in_progress": production_in_progress,
            "scheduled": production_scheduled,
        },
        "boms": {
            "needs_review": boms_needing_review,
            "active": active_boms,
        },
    }


@router.get("/recent-orders")
async def get_recent_orders(
    limit: int = 5,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get recent orders for dashboard display.
    """
    orders = (
        db.query(SalesOrder)
        .order_by(desc(SalesOrder.created_at))
        .limit(limit)
        .all()
    )

    return [
        {
            "id": order.id,
            "order_number": order.order_number,
            "product_name": order.product_name,
            "customer_name": order.user.full_name if order.user else "Unknown",
            "status": order.status,
            "payment_status": order.payment_status,
            "grand_total": float(order.grand_total) if order.grand_total else 0,
            "total_price": float(order.grand_total) if order.grand_total else 0,
            "created_at": order.created_at.isoformat() if order.created_at else None,
        }
        for order in orders
    ]


@router.get("/pending-bom-reviews")
async def get_pending_bom_reviews(
    limit: int = 5,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get BOMs that need admin review.
    """
    boms = (
        db.query(BOM)
        .filter(BOM.active == True)
        .order_by(desc(BOM.created_at))
        .limit(limit)
        .all()
    )

    return [
        {
            "id": bom.id,
            "code": bom.code,
            "name": bom.name,
            "total_cost": float(bom.total_cost) if bom.total_cost else 0,
            "line_count": len(bom.lines) if bom.lines else 0,
            "created_at": bom.created_at.isoformat() if bom.created_at else None,
        }
        for bom in boms
    ]


@router.get("/stats")
async def get_quick_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get quick stats for dashboard header.

    Admin only. Lightweight endpoint for real-time updates.
    """
    pending_quotes = db.query(Quote).filter(Quote.status == "pending").count()
    pending_orders = db.query(SalesOrder).filter(
        SalesOrder.status.in_(["pending", "confirmed"])
    ).count()
    ready_to_ship = db.query(SalesOrder).filter(
        SalesOrder.status == "ready_to_ship"
    ).count()

    return {
        "pending_quotes": pending_quotes,
        "pending_orders": pending_orders,
        "ready_to_ship": ready_to_ship,
    }


@router.get("/modules")
async def get_modules(
    current_admin: User = Depends(get_current_admin_user),
):
    """
    Get list of available admin modules.

    Admin only. For building navigation UI.
    """
    return [
        {
            "name": "BOM Management",
            "key": "bom",
            "description": "View and edit Bills of Materials for products",
            "api_route": "/api/v1/admin/bom",
            "icon": "list",
        },
        {
            "name": "Order Review",
            "key": "orders",
            "description": "Review orders and release to production",
            "api_route": "/api/v1/sales-orders",
            "icon": "clipboard-check",
        },
        {
            "name": "Production",
            "key": "production",
            "description": "Manage production orders and print jobs",
            "api_route": "/api/v1/production-orders",
            "icon": "printer",
        },
        {
            "name": "Shipping",
            "key": "shipping",
            "description": "Create shipping labels and track shipments",
            "api_route": "/api/v1/shipping",
            "icon": "truck",
        },
        {
            "name": "Inventory",
            "key": "inventory",
            "description": "View stock levels and manage inventory",
            "api_route": "/api/v1/inventory",
            "icon": "archive",
        },
        {
            "name": "Products",
            "key": "products",
            "description": "Manage products, materials, and pricing",
            "api_route": "/api/v1/products",
            "icon": "cube",
        },
        {
            "name": "Customers",
            "key": "customers",
            "description": "View and manage customer accounts",
            "api_route": "/api/v1/auth/portal/customer",
            "icon": "users",
        },
    ]
