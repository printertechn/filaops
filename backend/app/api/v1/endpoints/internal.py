"""
Internal API Endpoints for Service-to-Service Communication

These endpoints are intended for internal services (e.g., ML Dashboard) to access
ERP data without requiring user authentication. They should be protected by:
- Network-level restrictions (only allow from localhost/internal network)
- API key validation (optional, for production)

This enables the ML Dashboard to read business data from the ERP as the source of truth,
while maintaining the separation of concerns between business logic (ERP) and
ML/print operations (ML Dashboard).

See FUTURE_ARCHITECTURE.md for the full architectural vision.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, text

from app.db.session import get_db
from app.models.sales_order import SalesOrder
from app.models.quote import Quote
from app.models.user import User
from app.models.product import Product
from app.models.bom import BOM, BOMLine
from app.models.production_order import ProductionOrder
from app.models.inventory import Inventory, InventoryTransaction
from app.core.config import settings

router = APIRouter(prefix="/internal", tags=["Internal API"])


# ============================================================================
# OPTIONAL: API Key validation for production
# ============================================================================

async def validate_internal_api_key(
    x_internal_api_key: Optional[str] = Header(None, alias="X-Internal-API-Key")
):
    """
    Validate internal API key if configured.
    
    In development, this is optional. In production, set INTERNAL_API_KEY env var.
    """
    # If no key is configured, allow all requests (development mode)
    internal_key = getattr(settings, 'INTERNAL_API_KEY', None)
    if not internal_key:
        return True
    
    # If key is configured, validate it
    if x_internal_api_key != internal_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing internal API key"
        )
    
    return True


# ============================================================================
# SALES ORDERS - For ML Dashboard Order Management
# ============================================================================

@router.get("/sales-orders")
async def get_all_sales_orders(
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    _: bool = Depends(validate_internal_api_key),
    db: Session = Depends(get_db),
):
    """
    Get all sales orders for internal services (ML Dashboard).
    
    This endpoint provides the same data as the user endpoint but without
    requiring user authentication, allowing service-to-service communication.
    
    Query parameters:
    - skip: Pagination offset
    - limit: Max results (default 100, max 500)
    - status_filter: Filter by status (pending, confirmed, in_production, etc.)
    - search: Search by order number or customer name
    
    Returns:
        List of sales orders in ML Dashboard compatible format
    """
    query = db.query(SalesOrder).options(joinedload(SalesOrder.user))
    
    if status_filter and status_filter != 'all':
        query = query.filter(SalesOrder.status == status_filter)
    
    if search:
        query = query.filter(
            (SalesOrder.order_number.ilike(f"%{search}%")) |
            (SalesOrder.product_name.ilike(f"%{search}%"))
        )
    
    total_count = query.count()
    
    orders = (
        query
        .order_by(desc(SalesOrder.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # Transform to ML Dashboard expected format
    result = []
    for order in orders:
        customer_name = "Unknown"
        customer_email = ""
        if order.user:
            customer_name = order.user.full_name or order.user.email
            customer_email = order.user.email
        
        result.append({
            "id": order.id,
            "order_number": order.order_number,
            "customer_id": order.user_id,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "status": order.status,
            "payment_status": order.payment_status,
            "priority": order.rush_level or "normal",
            "total": float(order.grand_total) if order.grand_total else 0,
            "subtotal": float(order.total_price) if order.total_price else 0,
            "tax": float(order.tax_amount) if order.tax_amount else 0,
            "shipping": float(order.shipping_cost) if order.shipping_cost else 0,
            "total_items": order.quantity or 1,
            "product_name": order.product_name,
            "material_type": order.material_type,
            "quantity": order.quantity,
            "notes": order.customer_notes,
            "internal_notes": order.internal_notes,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
            "source": order.source or "portal",
            "order_type": order.order_type or "quote_based",
            # Shipping info
            "shipping_address": {
                "line1": order.shipping_address_line1,
                "line2": order.shipping_address_line2,
                "city": order.shipping_city,
                "state": order.shipping_state,
                "zip": order.shipping_zip,
                "country": order.shipping_country,
            },
            "tracking_number": order.tracking_number,
            "carrier": order.carrier,
        })
    
    return {
        "success": True,
        "orders": result,
        "total_count": total_count,
        "has_more": (skip + limit) < total_count,
    }


@router.get("/sales-orders/{order_id}")
async def get_sales_order_detail(
    order_id: int,
    _: bool = Depends(validate_internal_api_key),
    db: Session = Depends(get_db),
):
    """
    Get detailed sales order information for internal services.
    
    Returns:
        Complete order with lines (for quote-based, this is a single item)
    """
    order = (
        db.query(SalesOrder)
        .options(joinedload(SalesOrder.user))
        .filter(SalesOrder.id == order_id)
        .first()
    )
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales order not found"
        )
    
    customer_name = "Unknown"
    customer_email = ""
    if order.user:
        customer_name = order.user.full_name or order.user.email
        customer_email = order.user.email
    
    # Build lines (for quote-based orders, create a single line from order data)
    lines = []
    if order.order_type == "quote_based":
        # Quote-based orders have product info directly on the order
        lines.append({
            "id": order.id,  # Use order ID as line ID for simplicity
            "product_name": order.product_name,
            "product_sku": f"QUOTE-{order.quote_id}" if order.quote_id else "CUSTOM",
            "quantity": order.quantity or 1,
            "unit_price": float(order.unit_price) if order.unit_price else 0,
            "total": float(order.total_price) if order.total_price else 0,
            "material_type": order.material_type,
        })
    # TODO: For line_item orders, load from sales_order_lines table
    
    # Get production order if exists
    production_order = (
        db.query(ProductionOrder)
        .filter(ProductionOrder.sales_order_id == order.id)
        .first()
    )
    
    return {
        "success": True,
        "order": {
            "id": order.id,
            "order_number": order.order_number,
            "customer_id": order.user_id,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "status": order.status,
            "payment_status": order.payment_status,
            "priority": order.rush_level or "normal",
            "subtotal": float(order.total_price) if order.total_price else 0,
            "tax": float(order.tax_amount) if order.tax_amount else 0,
            "shipping_cost": float(order.shipping_cost) if order.shipping_cost else 0,
            "total": float(order.grand_total) if order.grand_total else 0,
            "notes": order.customer_notes,
            "internal_notes": order.internal_notes,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
            "source": order.source or "portal",
            "order_type": order.order_type or "quote_based",
            "lines": lines,
            # Shipping info
            "shipping_address": {
                "line1": order.shipping_address_line1,
                "line2": order.shipping_address_line2,
                "city": order.shipping_city,
                "state": order.shipping_state,
                "zip": order.shipping_zip,
                "country": order.shipping_country,
            },
            "tracking_number": order.tracking_number,
            "carrier": order.carrier,
            # Production info
            "materials_allocated": production_order is not None,
            "production_order_id": production_order.id if production_order else None,
            "production_order_code": production_order.code if production_order else None,
            "production_status": production_order.status if production_order else None,
        }
    }


# ============================================================================
# ANALYTICS - For ML Dashboard Summary Cards
# ============================================================================

@router.get("/sales-orders/analytics/summary")
async def get_orders_summary(
    _: bool = Depends(validate_internal_api_key),
    db: Session = Depends(get_db),
):
    """
    Get order analytics summary for dashboard cards.
    
    Returns counts and totals for various order states.
    """
    # Total orders
    total_orders = db.query(SalesOrder).count()
    
    # Total revenue (paid orders)
    revenue_result = (
        db.query(func.sum(SalesOrder.grand_total))
        .filter(SalesOrder.payment_status == "paid")
        .scalar()
    )
    total_revenue = float(revenue_result) if revenue_result else 0
    
    # Status counts
    pending_count = db.query(SalesOrder).filter(SalesOrder.status == "pending").count()
    confirmed_count = db.query(SalesOrder).filter(SalesOrder.status == "confirmed").count()
    in_production_count = db.query(SalesOrder).filter(SalesOrder.status == "in_production").count()
    ready_to_ship_count = db.query(SalesOrder).filter(SalesOrder.status == "ready_to_ship").count()
    shipped_count = db.query(SalesOrder).filter(SalesOrder.status == "shipped").count()
    completed_count = db.query(SalesOrder).filter(SalesOrder.status.in_(["delivered", "completed"])).count()
    
    return {
        "success": True,
        "summary": {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "pending_count": pending_count,
            "confirmed_count": confirmed_count,
            "in_production_count": in_production_count,
            "ready_to_ship_count": ready_to_ship_count,
            "shipped_count": shipped_count,
            "completed_count": completed_count,
        }
    }


# ============================================================================
# CUSTOMERS - For ML Dashboard Customer Management
# ============================================================================

@router.get("/customers")
async def get_all_customers(
    limit: int = Query(default=100, le=500),
    _: bool = Depends(validate_internal_api_key),
    db: Session = Depends(get_db),
):
    """
    Get all customers for internal services (ML Dashboard).
    
    Returns customers who have placed orders (users with sales_orders).
    """
    # Get users who have orders
    customers_with_orders = (
        db.query(User)
        .join(SalesOrder, User.id == SalesOrder.user_id)
        .distinct()
        .limit(limit)
        .all()
    )
    
    result = []
    for user in customers_with_orders:
        # Get order count and total spent
        order_stats = (
            db.query(
                func.count(SalesOrder.id).label('order_count'),
                func.sum(SalesOrder.grand_total).label('total_spent')
            )
            .filter(SalesOrder.user_id == user.id)
            .first()
        )
        
        result.append({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name or user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "company": user.company_name,
            "order_count": order_stats.order_count if order_stats else 0,
            "total_spent": float(order_stats.total_spent) if order_stats and order_stats.total_spent else 0,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        })
    
    return {
        "success": True,
        "customers": result,
    }


# ============================================================================
# BOMS - For ML Dashboard Product/BOM Selection
# ============================================================================

@router.get("/boms")
async def get_all_boms(
    active_only: bool = True,
    _: bool = Depends(validate_internal_api_key),
    db: Session = Depends(get_db),
):
    """
    Get all BOMs for internal services (ML Dashboard).
    
    Used for product selection when creating orders manually.
    """
    query = db.query(BOM).options(
        joinedload(BOM.product),
        joinedload(BOM.lines)
    )
    
    if active_only:
        query = query.filter(BOM.active == True)
    
    boms = query.order_by(BOM.code).all()
    
    result = []
    for bom in boms:
        # Calculate total cost from lines if not stored on BOM
        total_cost = Decimal("0")
        if bom.lines:
            for line in bom.lines:
                # Get component cost
                component = db.query(Product).filter(Product.id == line.component_id).first()
                if component and component.cost and line.quantity:
                    total_cost += component.cost * line.quantity

        # Use calculated cost or stored cost
        final_cost = float(total_cost) if total_cost > 0 else (float(bom.total_cost) if bom.total_cost else 0)

        result.append({
            "id": bom.id,
            "bom_number": bom.code,
            "product_id": bom.product_id,
            "product_name": bom.product.name if bom.product else bom.name,
            "product_sku": bom.product.sku if bom.product else None,
            "product_description": bom.product.description if bom.product else None,
            "is_active": bom.active,
            "total_cost": final_cost,
            "total_lines": len(bom.lines) if bom.lines else 0,  # UI expects total_lines
            "line_count": len(bom.lines) if bom.lines else 0,   # Keep for backwards compat
            "created_at": bom.created_at.isoformat() if bom.created_at else None,
        })
    
    return {
        "success": True,
        "boms": result,
        "data": result,  # Alias for compatibility
    }


@router.get("/boms/{bom_id}")
async def get_bom_detail(
    bom_id: int,
    _: bool = Depends(validate_internal_api_key),
    db: Session = Depends(get_db),
):
    """
    Get a single BOM with all details and lines.

    Returns BOM in format expected by ML Dashboard BOMManagement UI.
    """
    bom = (
        db.query(BOM)
        .options(joinedload(BOM.product), joinedload(BOM.lines))
        .filter(BOM.id == bom_id)
        .first()
    )

    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")

    # Build lines with full details
    lines = []
    total_material_cost = Decimal("0")
    total_labor_cost = Decimal("0")

    for i, line in enumerate(bom.lines, 1):
        component = db.query(Product).filter(Product.id == line.component_id).first()
        unit_cost = float(component.cost) if component and component.cost else 0
        line_cost = unit_cost * float(line.quantity or 0)
        total_material_cost += Decimal(str(line_cost))

        lines.append({
            "id": line.id,
            "line_number": i,
            "bom_id": line.bom_id,
            "inventory_item_id": line.component_id,
            "item_name": component.name if component else None,
            "item_sku": component.sku if component else None,
            "quantity_required": float(line.quantity) if line.quantity else 0,
            "unit_of_measure": component.unit if component else "units",
            "unit_cost": unit_cost,
            "line_cost": line_cost,
            "scrap_percentage": float(line.scrap_factor) if line.scrap_factor else 0,
            "is_critical": False,
            "is_purchased": True,
            "notes": line.notes,
        })

    # Calculate labor cost if assembly time is set
    hourly_rate = 25  # Default labor rate
    if bom.assembly_time_minutes:
        total_labor_cost = Decimal(str(bom.assembly_time_minutes)) / 60 * hourly_rate

    total_cost = total_material_cost + total_labor_cost
    batch_size = 1  # Default

    return {
        "id": bom.id,
        "bom_number": bom.code,
        "product_id": bom.product_id,
        "product_name": bom.product.name if bom.product else bom.name,
        "product_sku": bom.product.sku if bom.product else None,
        "product_description": bom.product.description if bom.product else None,
        "version": bom.version or 1,
        "revision": bom.revision or "A",
        "is_active": bom.active,
        "batch_size": batch_size,
        "assembly_time_minutes": bom.assembly_time_minutes,
        "total_material_cost": float(total_material_cost),
        "total_labor_cost": float(total_labor_cost),
        "total_cost": float(total_cost),
        "total_cost_per_unit": float(total_cost / batch_size) if batch_size else float(total_cost),
        "lines": lines,
        "created_at": bom.created_at.isoformat() if bom.created_at else None,
    }


@router.post("/boms")
async def create_bom(
    bom_data: dict,
    _: bool = Depends(validate_internal_api_key),
    db: Session = Depends(get_db),
):
    """
    Create a new BOM (and product if needed).

    The UI sends:
    - product_name: Name for the product
    - product_description: Optional description
    - product_sku: Optional SKU (will be auto-generated if not provided)
    - batch_size: Batch size (default 1)
    - assembly_time_minutes: Optional assembly time

    This endpoint will:
    1. Create a product if SKU doesn't exist
    2. Create a BOM for that product
    """
    product_name = bom_data.get("product_name")
    product_description = bom_data.get("product_description")
    product_sku = bom_data.get("product_sku")
    batch_size = bom_data.get("batch_size", 1)
    assembly_time_minutes = bom_data.get("assembly_time_minutes")

    if not product_name:
        raise HTTPException(status_code=400, detail="product_name is required")

    # Generate SKU if not provided
    if not product_sku:
        year = datetime.utcnow().year
        last_product = db.query(Product).filter(
            Product.sku.like(f"FG-{year}-%")
        ).order_by(desc(Product.sku)).first()

        next_num = 1
        if last_product:
            try:
                next_num = int(last_product.sku.split("-")[2]) + 1
            except:
                pass

        product_sku = f"FG-{year}-{next_num:04d}"

    # Check if product exists
    product = db.query(Product).filter(Product.sku == product_sku).first()

    if not product:
        # Create new product
        product = Product(
            sku=product_sku,
            name=product_name,
            description=product_description,
            category="Finished Goods",
            type="manufactured",
            unit="units",
            has_bom=True,
            active=True,
        )
        db.add(product)
        db.flush()

    # Generate BOM code
    year = datetime.utcnow().year
    last_bom = db.query(BOM).filter(
        BOM.code.like(f"BOM-{year}-%")
    ).order_by(desc(BOM.code)).first()

    next_num = 1
    if last_bom:
        try:
            next_num = int(last_bom.code.split("-")[2]) + 1
        except:
            pass

    bom_code = f"BOM-{year}-{next_num:04d}"

    # Create BOM
    bom = BOM(
        product_id=product.id,
        code=bom_code,
        name=product_name,
        version=1,
        revision="A",
        assembly_time_minutes=assembly_time_minutes,
        active=True,
        total_cost=Decimal("0"),
    )
    db.add(bom)
    db.commit()
    db.refresh(bom)

    return {
        "success": True,
        "id": bom.id,
        "bom_number": bom.code,
        "product_id": product.id,
        "product_sku": product.sku,
        "product_name": product.name,
        "message": f"BOM {bom.code} created for product {product.sku}",
    }


@router.post("/boms/{bom_id}/lines")
async def add_bom_line(
    bom_id: int,
    line_data: dict,
    _: bool = Depends(validate_internal_api_key),
    db: Session = Depends(get_db),
):
    """
    Add a line to a BOM.

    The UI sends:
    - inventory_item_id: Product ID of component (optional if item_sku provided)
    - item_name: Component name
    - item_sku: Component SKU
    - quantity_required: Quantity needed per unit
    - unit_of_measure: Unit of measure
    - unit_cost: Cost per unit
    - is_purchased: Whether purchased externally
    - is_critical: Whether critical path item
    - scrap_percentage: Scrap factor
    """
    # Validate BOM exists
    bom = db.query(BOM).filter(BOM.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")

    # Get or find the component
    component_id = line_data.get("inventory_item_id")
    item_sku = line_data.get("item_sku")

    if not component_id and item_sku:
        component = db.query(Product).filter(Product.sku == item_sku).first()
        if component:
            component_id = component.id

    if not component_id:
        raise HTTPException(status_code=400, detail="Component not found. Provide inventory_item_id or valid item_sku")

    quantity = line_data.get("quantity_required", 1)
    scrap = line_data.get("scrap_percentage", 0)
    notes = line_data.get("notes")

    # Get next sequence
    max_seq = db.query(BOMLine).filter(BOMLine.bom_id == bom_id).count()

    # Create line
    line = BOMLine(
        bom_id=bom_id,
        component_id=component_id,
        quantity=Decimal(str(quantity)),
        sequence=max_seq + 1,
        scrap_factor=Decimal(str(scrap)) if scrap else None,
        notes=notes,
    )
    db.add(line)

    # Recalculate BOM total cost
    db.flush()
    total_cost = Decimal("0")
    for l in db.query(BOMLine).filter(BOMLine.bom_id == bom_id).all():
        comp = db.query(Product).filter(Product.id == l.component_id).first()
        if comp and comp.cost and l.quantity:
            total_cost += comp.cost * l.quantity

    bom.total_cost = total_cost
    db.commit()
    db.refresh(line)

    # Get component for response
    component = db.query(Product).filter(Product.id == component_id).first()
    unit_cost = float(component.cost) if component and component.cost else 0

    return {
        "success": True,
        "id": line.id,
        "line_number": line.sequence,
        "bom_id": line.bom_id,
        "item_name": component.name if component else None,
        "item_sku": component.sku if component else None,
        "quantity_required": float(line.quantity),
        "unit_cost": unit_cost,
        "line_cost": unit_cost * float(line.quantity),
    }


@router.delete("/boms/{bom_id}/lines/{line_id}")
async def delete_bom_line(
    bom_id: int,
    line_id: int,
    _: bool = Depends(validate_internal_api_key),
    db: Session = Depends(get_db),
):
    """
    Delete a line from a BOM.
    """
    line = db.query(BOMLine).filter(
        BOMLine.id == line_id,
        BOMLine.bom_id == bom_id
    ).first()

    if not line:
        raise HTTPException(status_code=404, detail="BOM line not found")

    db.delete(line)

    # Recalculate BOM total cost
    bom = db.query(BOM).filter(BOM.id == bom_id).first()
    db.flush()

    total_cost = Decimal("0")
    for l in db.query(BOMLine).filter(BOMLine.bom_id == bom_id).all():
        comp = db.query(Product).filter(Product.id == l.component_id).first()
        if comp and comp.cost and l.quantity:
            total_cost += comp.cost * l.quantity

    bom.total_cost = total_cost
    db.commit()

    return {"success": True, "message": f"BOM line {line_id} deleted"}


@router.get("/boms/{bom_id}/explode")
async def explode_bom(
    bom_id: int,
    quantity: int = 1,
    _: bool = Depends(validate_internal_api_key),
    db: Session = Depends(get_db),
):
    """
    Explode a BOM to show all required components with availability.

    Returns flat list of components with:
    - Required quantities (scaled by requested quantity)
    - Available inventory
    - Shortage amounts
    """
    bom = db.query(BOM).options(joinedload(BOM.lines)).filter(BOM.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")

    items = []
    shortages = []
    total_cost = Decimal("0")

    for line in bom.lines:
        component = db.query(Product).filter(Product.id == line.component_id).first()
        if not component:
            continue

        # Calculate required with scrap factor
        base_qty = float(line.quantity or 0) * quantity
        scrap = float(line.scrap_factor or 0) / 100
        qty_required = base_qty * (1 + scrap)

        # Get available inventory
        inv = db.query(
            func.sum(Inventory.available_quantity)
        ).filter(Inventory.product_id == component.id).scalar() or 0

        available = float(inv)
        shortage = max(0, qty_required - available)
        in_stock = shortage == 0

        unit_cost = float(component.cost) if component.cost else 0
        line_total = qty_required * unit_cost
        total_cost += Decimal(str(line_total))

        item = {
            "component_id": component.id,
            "name": component.name,
            "sku": component.sku,
            "category": component.category or "Component",
            "unit_of_measure": component.unit or "units",
            "quantity_required": qty_required,
            "available_quantity": available,
            "in_stock": in_stock,
            "shortage": shortage,
            "unit_cost": unit_cost,
            "total_cost": line_total,
        }
        items.append(item)

        if shortage > 0:
            shortages.append({
                "component": component.name,
                "sku": component.sku,
                "required": qty_required,
                "available": available,
                "shortage": shortage,
            })

    return {
        "bom_id": bom_id,
        "quantity": quantity,
        "items": items,
        "total_cost": float(total_cost),
        "has_shortages": len(shortages) > 0,
        "shortages": shortages,
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def internal_health_check():
    """
    Health check endpoint for internal services.
    """
    return {
        "status": "healthy",
        "service": "blb3d-erp",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# INVENTORY - For ML Dashboard Inventory Management
# ============================================================================

@router.get("/inventory/items")
async def get_inventory_items(
    category: Optional[str] = None,
    _: bool = Depends(validate_internal_api_key),
    db: Session = Depends(get_db),
):
    """
    Get all inventory items grouped by category.
    
    Returns inventory with product details, organized by product category.
    """
    # Use raw SQL to avoid model/schema mismatch issues
    
    sql = """
    SELECT 
        i.id,
        i.product_id,
        i.location_id,
        i.on_hand_quantity,
        i.allocated_quantity,
        i.available_quantity,
        p.sku,
        p.name,
        p.category,
        p.unit
    FROM inventory i
    JOIN products p ON p.id = i.product_id
    """
    
    if category:
        sql += " WHERE p.category = :category"
        result = db.execute(text(sql), {"category": category}).fetchall()
    else:
        result = db.execute(text(sql)).fetchall()
    
    # Group by category
    categories = {}
    for row in result:
        cat = row.category or "uncategorized"
        if cat not in categories:
            categories[cat] = []
        
        categories[cat].append({
            "id": row.id,
            "product_id": row.product_id,
            "sku": row.sku,
            "name": row.name,
            "category": cat,
            "on_hand": float(row.on_hand_quantity) if row.on_hand_quantity else 0,
            "allocated": float(row.allocated_quantity) if row.allocated_quantity else 0,
            "available": float(row.available_quantity) if row.available_quantity else 0,
            "unit": row.unit or "ea",
        })
    
    return {
        "success": True,
        "data": categories,
        "total_items": len(result),
    }


@router.get("/inventory/summary")
async def get_inventory_summary(
    _: bool = Depends(validate_internal_api_key),
    db: Session = Depends(get_db),
):
    """
    Get inventory summary statistics.
    """
    # Use raw SQL to avoid model/schema mismatch
    sql = """
    SELECT 
        COUNT(*) as total_items,
        SUM(CASE WHEN available_quantity <= 0 THEN 1 ELSE 0 END) as low_stock_count,
        SUM(on_hand_quantity) as total_on_hand,
        SUM(allocated_quantity) as total_allocated,
        SUM(available_quantity) as total_available
    FROM inventory
    """
    
    result = db.execute(text(sql)).fetchone()
    
    return {
        "success": True,
        "summary": {
            "total_items": result.total_items or 0,
            "low_stock_count": result.low_stock_count or 0,
            "total_on_hand": float(result.total_on_hand) if result.total_on_hand else 0,
            "total_allocated": float(result.total_allocated) if result.total_allocated else 0,
            "total_available": float(result.total_available) if result.total_available else 0,
        }
    }


# ============================================================================
# INVENTORY TRANSACTIONS - For ML Dashboard Transaction History
# ============================================================================

@router.get("/inventory/transactions")
async def get_inventory_transactions(
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    transaction_type: Optional[str] = None,
    product_id: Optional[int] = None,
    _: bool = Depends(validate_internal_api_key),
    db: Session = Depends(get_db),
):
    """
    Get inventory transactions for audit/history.
    
    Query parameters:
    - transaction_type: Filter by type (receipt, shipment, adjustment, consumption, transfer)
    - product_id: Filter by product
    """
    # First, discover what columns exist in the table
    try:
        schema_sql = """
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'inventory_transactions'
        """
        columns = [row[0] for row in db.execute(text(schema_sql)).fetchall()]
        
        # Build SELECT based on available columns
        select_cols = ["t.id", "t.product_id", "t.transaction_type", "t.quantity"]
        
        # Add optional columns if they exist
        if "inventory_id" in columns:
            select_cols.append("t.inventory_id")
        if "reference_type" in columns:
            select_cols.append("t.reference_type")
        if "reference_id" in columns:
            select_cols.append("t.reference_id")
        if "unit_cost" in columns:
            select_cols.append("t.unit_cost")
        if "from_location" in columns:
            select_cols.append("t.from_location")
        if "to_location" in columns:
            select_cols.append("t.to_location")
        if "notes" in columns:
            select_cols.append("t.notes")
        if "transaction_date" in columns:
            select_cols.append("t.transaction_date")
        if "created_at" in columns:
            select_cols.append("t.created_at as transaction_date")
        if "created_by" in columns:
            select_cols.append("t.created_by")
        
        # Add product info
        select_cols.extend(["p.sku as product_sku", "p.name as product_name"])
        
        sql = f"""
        SELECT {', '.join(select_cols)}
        FROM inventory_transactions t
        LEFT JOIN products p ON p.id = t.product_id
        WHERE 1=1
        """
        
        params = {"skip": skip, "limit": limit}
        
        if transaction_type:
            sql += " AND t.transaction_type = :transaction_type"
            params["transaction_type"] = transaction_type
        
        if product_id:
            sql += " AND t.product_id = :product_id"
            params["product_id"] = product_id
        
        # Get count first
        count_sql = "SELECT COUNT(*) as cnt FROM inventory_transactions t WHERE 1=1"
        if transaction_type:
            count_sql += " AND t.transaction_type = :transaction_type"
        if product_id:
            count_sql += " AND t.product_id = :product_id"
        
        total_count = db.execute(text(count_sql), params).fetchone().cnt
        
        # Add ordering and pagination - use created_at if transaction_date doesn't exist
        order_col = "t.transaction_date" if "transaction_date" in columns else "t.created_at" if "created_at" in columns else "t.id"
        sql += f" ORDER BY {order_col} DESC OFFSET :skip ROWS FETCH NEXT :limit ROWS ONLY"
        
        rows = db.execute(text(sql), params).fetchall()
        
        result = []
        for row in rows:
            row_dict = row._mapping
            result.append({
                "id": row_dict.get("id"),
                "product_id": row_dict.get("product_id"),
                "product_sku": row_dict.get("product_sku"),
                "product_name": row_dict.get("product_name") or "Unknown",
                "transaction_type": row_dict.get("transaction_type"),
                "reference_type": row_dict.get("reference_type"),
                "reference_id": row_dict.get("reference_id"),
                "quantity": float(row_dict.get("quantity")) if row_dict.get("quantity") else 0,
                "unit_cost": float(row_dict.get("unit_cost")) if row_dict.get("unit_cost") else None,
                "from_location": row_dict.get("from_location"),
                "to_location": row_dict.get("to_location"),
                "notes": row_dict.get("notes"),
                "transaction_date": row_dict.get("transaction_date").isoformat() if row_dict.get("transaction_date") else None,
                "created_by": row_dict.get("created_by"),
            })
        
        return {
            "success": True,
            "transactions": result,
            "total_count": total_count,
            "has_more": (skip + limit) < total_count,
            "available_columns": columns,  # Include for debugging
        }
    except Exception as e:
        # If table doesn't exist or other error, return empty
        return {
            "success": True,
            "transactions": [],
            "total_count": 0,
            "has_more": False,
            "error": str(e),
        }


# ============================================================================
# MATERIAL INVENTORY - For ML Dashboard Material Management
# ============================================================================

@router.get("/materials")
async def get_material_inventory(
    _: bool = Depends(validate_internal_api_key),
    db: Session = Depends(get_db),
):
    """
    Get all material inventory items (filaments).
    
    This is separate from general inventory - these are 3D printing materials
    stored in material_inventory table with material_types and colors.
    
    Returns materials grouped by base material type (PLA, PETG, ABS, etc.)
    """
    try:
        sql = """
        SELECT 
            mi.id,
            mi.sku,
            mi.in_stock,
            mi.quantity_kg,
            mi.reorder_point_kg,
            mi.cost_per_kg,
            mi.active,
            mt.id as material_type_id,
            mt.code as material_type_code,
            mt.name as material_type_name,
            mt.base_material,
            mt.density,
            mt.price_multiplier,
            mt.base_price_per_kg,
            c.id as color_id,
            c.code as color_code,
            c.name as color_name,
            c.hex_code
        FROM material_inventory mi
        JOIN material_types mt ON mt.id = mi.material_type_id
        JOIN colors c ON c.id = mi.color_id
        WHERE mi.active = 1
        ORDER BY mt.base_material, mt.code, c.name
        """
        
        rows = db.execute(text(sql)).fetchall()
        
        # Group by base material
        by_base_material = {}
        for row in rows:
            base = row.base_material or "Other"
            if base not in by_base_material:
                by_base_material[base] = []
            
            # Calculate spool count (assuming 1kg spools)
            qty_kg = float(row.quantity_kg) if row.quantity_kg else 0
            spool_weight = 1.0  # Default 1kg spools
            spool_count = int(qty_kg / spool_weight) if qty_kg > 0 else 0
            
            by_base_material[base].append({
                "id": row.id,
                "sku": row.sku,
                "name": f"{row.material_type_name} - {row.color_name}",
                "material_type": row.material_type_code,
                "material_type_name": row.material_type_name,
                "base_material": base,
                "color": row.color_name,
                "color_code": row.color_code,
                "hex_code": row.hex_code,
                "in_stock": bool(row.in_stock),
                "quantity_kg": qty_kg,
                "spool_count": spool_count,
                "spool_weight_kg": spool_weight,
                "reorder_point_kg": float(row.reorder_point_kg) if row.reorder_point_kg else 1.0,
                "cost_per_kg": float(row.cost_per_kg) if row.cost_per_kg else float(row.base_price_per_kg) if row.base_price_per_kg else 0,
                "density": float(row.density) if row.density else 1.24,
                "price_multiplier": float(row.price_multiplier) if row.price_multiplier else 1.0,
                "needs_reorder": qty_kg < (float(row.reorder_point_kg) if row.reorder_point_kg else 1.0),
                # For frontend compatibility
                "on_hand": spool_count,
                "available": spool_count,
                "allocated": 0,
                "category": "material",
                "unit": "kg",
            })
        
        # Calculate totals
        total_items = len(rows)
        total_kg = sum(float(r.quantity_kg) if r.quantity_kg else 0 for r in rows)
        low_stock = sum(1 for r in rows if (float(r.quantity_kg) if r.quantity_kg else 0) < (float(r.reorder_point_kg) if r.reorder_point_kg else 1.0))
        
        return {
            "success": True,
            "data": by_base_material,
            "summary": {
                "total_skus": total_items,
                "total_kg": total_kg,
                "low_stock_count": low_stock,
                "by_base_material": {k: len(v) for k, v in by_base_material.items()}
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": {}
        }


@router.get("/inventory/all")
async def get_all_inventory_combined(
    _: bool = Depends(validate_internal_api_key),
    db: Session = Depends(get_db),
):
    """
    Get ALL inventory combined: general inventory + material inventory.
    
    This is the unified view for the ML Dashboard inventory tab.
    Materials appear under the 'Materials' category with proper formatting.
    """
    # First get general inventory
    # Use LEFT JOIN to include products without inventory records (e.g., Finished Goods awaiting production)
    general_sql = """
    SELECT
        COALESCE(i.id, 0) as id,
        p.id as product_id,
        COALESCE(i.on_hand_quantity, 0) as on_hand_quantity,
        COALESCE(i.allocated_quantity, 0) as allocated_quantity,
        COALESCE(i.available_quantity, 0) as available_quantity,
        p.sku,
        p.name,
        p.category,
        p.unit
    FROM products p
    LEFT JOIN inventory i ON p.id = i.product_id
    WHERE p.category IS NOT NULL
    """
    general_rows = db.execute(text(general_sql)).fetchall()
    
    # Group general inventory by category
    categories = {}
    for row in general_rows:
        cat = row.category or "Uncategorized"
        if cat not in categories:
            categories[cat] = []
        
        categories[cat].append({
            "id": row.id,
            "product_id": row.product_id,
            "sku": row.sku,
            "name": row.name,
            "category": cat,
            "on_hand": float(row.on_hand_quantity) if row.on_hand_quantity else 0,
            "allocated": float(row.allocated_quantity) if row.allocated_quantity else 0,
            "available": float(row.available_quantity) if row.available_quantity else 0,
            "unit": row.unit or "ea",
        })
    
    # Now get material inventory
    material_sql = """
    SELECT 
        mi.id,
        mi.sku,
        mi.in_stock,
        mi.quantity_kg,
        mi.reorder_point_kg,
        mi.cost_per_kg,
        mt.code as material_type_code,
        mt.name as material_type_name,
        mt.base_material,
        mt.base_price_per_kg,
        c.name as color_name,
        c.code as color_code,
        c.hex_code
    FROM material_inventory mi
    JOIN material_types mt ON mt.id = mi.material_type_id
    JOIN colors c ON c.id = mi.color_id
    WHERE mi.active = 1
    ORDER BY mt.base_material, mt.code, c.name
    """
    material_rows = db.execute(text(material_sql)).fetchall()
    
    # Add materials to 'Raw Materials' category (matching frontend expectations)
    if "Raw Materials" not in categories:
        categories["Raw Materials"] = []
    
    for row in material_rows:
        qty_kg = float(row.quantity_kg) if row.quantity_kg else 0
        spool_weight = 1.0
        spool_count = int(qty_kg / spool_weight) if qty_kg > 0 else 0
        
        categories["Raw Materials"].append({
            "id": f"mat-{row.id}",  # Prefix to avoid ID collision
            "sku": row.sku,
            "name": f"{row.material_type_name} - {row.color_name}",
            "category": "Raw Materials",
            "material_type": row.material_type_code,
            "base_material": row.base_material,
            "color": row.color_name,
            "color_code": row.color_code,
            "hex_code": row.hex_code,
            "on_hand": spool_count,
            "quantity": spool_count,  # Alias for compatibility
            "allocated": 0,
            "available": spool_count,
            "spool_weight_kg": spool_weight,
            "quantity_kg": qty_kg,
            "cost_per_kg": float(row.cost_per_kg) if row.cost_per_kg else float(row.base_price_per_kg) if row.base_price_per_kg else 0,
            "unit": "spools",
            "needs_reorder": qty_kg < (float(row.reorder_point_kg) if row.reorder_point_kg else 1.0),
            "is_material": True,  # Flag to identify material items
        })
    
    total_general = len(general_rows)
    total_materials = len(material_rows)
    
    return {
        "success": True,
        "data": categories,
        "total_items": total_general + total_materials,
        "breakdown": {
            "general_inventory": total_general,
            "material_inventory": total_materials,
        }
    }


# ============================================================================
# PRODUCTION ORDERS - For ML Dashboard Production Queue
# ============================================================================

@router.get("/production-orders")
async def get_production_orders(
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    status_filter: Optional[str] = None,
    _: bool = Depends(validate_internal_api_key),
    db: Session = Depends(get_db),
):
    """
    Get all production orders for internal services (ML Dashboard).
    
    Query parameters:
    - status_filter: Filter by status (queued, scheduled, printing, completed, etc.)
    """
    try:
        query = db.query(ProductionOrder).options(
            joinedload(ProductionOrder.product),
            joinedload(ProductionOrder.bom)
        )

        if status_filter and status_filter != 'all':
            query = query.filter(ProductionOrder.status == status_filter)

        total_count = query.count()

        orders = (
            query
            .order_by(desc(ProductionOrder.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

        result = []
        for po in orders:
            result.append({
                "id": po.id,
                "code": po.code,
                "status": po.status,
                "product_id": po.product_id,
                "product_name": po.product.name if po.product else None,
                "product_sku": po.product.sku if po.product else None,
                "quantity": float(po.quantity) if po.quantity else 0,
                "bom_id": po.bom_id,
                "priority": po.priority or "normal",
                "due_date": po.due_date.isoformat() if po.due_date else None,
                "start_date": po.start_date.isoformat() if po.start_date else None,
                "finish_date": po.finish_date.isoformat() if po.finish_date else None,
                "estimated_time_minutes": po.estimated_time_minutes,
                "actual_time_minutes": po.actual_time_minutes,
                "assigned_to": po.assigned_to,
                "notes": po.notes,
                "created_at": po.created_at.isoformat() if po.created_at else None,
            })
        
        return {
            "success": True,
            "production_orders": result,
            "total_count": total_count,
            "has_more": (skip + limit) < total_count,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "production_orders": [],
            "total_count": 0,
        }


# ============================================================================
# QUOTES - For ML Dashboard Quote Management
# ============================================================================

@router.get("/quotes")
async def get_quotes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status_filter: Optional[str] = None,
    _: bool = Depends(validate_internal_api_key),
    db: Session = Depends(get_db),
):
    """
    Get all quotes for ML Dashboard.

    Returns quotes with customer info, pricing, and linked BOM/order status.
    """
    try:
        query = db.query(Quote).options(
            joinedload(Quote.user),
            joinedload(Quote.materials),
        )

        if status_filter and status_filter != "all":
            query = query.filter(Quote.status == status_filter)

        total_count = query.count()

        quotes = (
            query
            .order_by(desc(Quote.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

        result = []
        for q in quotes:
            # Get linked BOM if exists
            bom = None
            if q.product_id:
                bom = db.query(BOM).filter(BOM.product_id == q.product_id).first()

            result.append({
                "id": q.id,
                "quote_number": q.quote_number,
                "status": q.status,
                "product_name": q.product_name,
                "quantity": q.quantity,
                # Material info
                "material_type": q.material_type,
                "color": q.color,
                "material_grams": float(q.material_grams) if q.material_grams else None,
                "print_time_hours": float(q.print_time_hours) if q.print_time_hours else None,
                # Pricing
                "unit_price": float(q.unit_price) if q.unit_price else None,
                "total_price": float(q.total_price) if q.total_price else None,
                "margin_percent": float(q.margin_percent) if q.margin_percent else None,
                # Dimensions
                "dimensions": {
                    "x": float(q.dimensions_x) if q.dimensions_x else None,
                    "y": float(q.dimensions_y) if q.dimensions_y else None,
                    "z": float(q.dimensions_z) if q.dimensions_z else None,
                },
                # Customer info
                "customer_email": q.customer_email or (q.user.email if q.user else None),
                "customer_name": q.customer_name or (f"{q.user.first_name} {q.user.last_name}" if q.user else None),
                # Workflow
                "auto_approved": q.auto_approved,
                "requires_review_reason": q.requires_review_reason,
                "rush_level": q.rush_level,
                # Links
                "product_id": q.product_id,
                "bom_id": bom.id if bom else None,
                "sales_order_id": q.sales_order_id,
                # Multi-material count
                "material_count": len(q.materials) if q.materials else 1,
                # Timestamps
                "created_at": q.created_at.isoformat() if q.created_at else None,
                "expires_at": q.expires_at.isoformat() if q.expires_at else None,
                "converted_at": q.converted_at.isoformat() if q.converted_at else None,
            })

        return {
            "success": True,
            "quotes": result,
            "total_count": total_count,
            "has_more": (skip + limit) < total_count,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "quotes": [],
            "total_count": 0,
        }


@router.get("/quotes/{quote_id}")
async def get_quote_detail(
    quote_id: int,
    _: bool = Depends(validate_internal_api_key),
    db: Session = Depends(get_db),
):
    """
    Get detailed quote information including multi-material breakdown.
    """
    quote = (
        db.query(Quote)
        .options(
            joinedload(Quote.user),
            joinedload(Quote.materials),
            joinedload(Quote.files),
        )
        .filter(Quote.id == quote_id)
        .first()
    )

    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    # Get linked BOM with lines
    bom = None
    bom_lines = []
    bom_total_cost = 0
    if quote.product_id:
        bom = db.query(BOM).options(joinedload(BOM.lines)).filter(BOM.product_id == quote.product_id).first()
        if bom:
            for line in bom.lines:
                component = db.query(Product).filter(Product.id == line.component_id).first()
                unit_cost = float(component.cost) if component and component.cost else 0
                line_cost = unit_cost * float(line.quantity or 0)
                bom_total_cost += line_cost
                bom_lines.append({
                    "id": line.id,
                    "component_name": component.name if component else None,
                    "component_sku": component.sku if component else None,
                    "quantity": float(line.quantity) if line.quantity else 0,
                    "unit": component.unit if component else "units",
                    "unit_cost": unit_cost,
                    "line_cost": line_cost,
                    "notes": line.notes,
                })

    # Build materials breakdown
    materials = []
    for qm in (quote.materials or []):
        materials.append({
            "slot_number": qm.slot_number,
            "is_primary": qm.is_primary,
            "material_type": qm.material_type,
            "color_code": qm.color_code,
            "color_name": qm.color_name,
            "color_hex": qm.color_hex,
            "material_grams": float(qm.material_grams) if qm.material_grams else 0,
        })

    # Build files list
    files = []
    for f in (quote.files or []):
        files.append({
            "id": f.id,
            "filename": f.original_filename,
            "file_format": f.file_format,
            "file_size_mb": f.file_size_mb,
            "is_valid": f.is_valid,
            "processed": f.processed,
        })

    return {
        "id": quote.id,
        "quote_number": quote.quote_number,
        "status": quote.status,
        "product_name": quote.product_name,
        "quantity": quote.quantity,
        # Material info (primary/legacy)
        "material_type": quote.material_type,
        "color": quote.color,
        "material_grams": float(quote.material_grams) if quote.material_grams else None,
        "print_time_hours": float(quote.print_time_hours) if quote.print_time_hours else None,
        # Multi-material breakdown
        "materials": materials,
        "is_multi_material": len(materials) > 1,
        # Pricing
        "unit_price": float(quote.unit_price) if quote.unit_price else None,
        "total_price": float(quote.total_price) if quote.total_price else None,
        "margin_percent": float(quote.margin_percent) if quote.margin_percent else None,
        # Dimensions
        "dimensions": {
            "x": float(quote.dimensions_x) if quote.dimensions_x else None,
            "y": float(quote.dimensions_y) if quote.dimensions_y else None,
            "z": float(quote.dimensions_z) if quote.dimensions_z else None,
        },
        "file_format": quote.file_format,
        "file_size_mb": quote.file_size_bytes / (1024 * 1024) if quote.file_size_bytes else None,
        # Files
        "files": files,
        # Customer info
        "customer_email": quote.customer_email or (quote.user.email if quote.user else None),
        "customer_name": quote.customer_name or (f"{quote.user.first_name} {quote.user.last_name}" if quote.user else None),
        "customer_notes": quote.customer_notes,
        # Shipping
        "shipping": {
            "name": quote.shipping_name,
            "address_line1": quote.shipping_address_line1,
            "address_line2": quote.shipping_address_line2,
            "city": quote.shipping_city,
            "state": quote.shipping_state,
            "zip": quote.shipping_zip,
            "country": quote.shipping_country,
            "phone": quote.shipping_phone,
            "carrier": quote.shipping_carrier,
            "service": quote.shipping_service,
            "cost": float(quote.shipping_cost) if quote.shipping_cost else None,
        },
        # Workflow
        "auto_approved": quote.auto_approved,
        "auto_approve_eligible": quote.auto_approve_eligible,
        "requires_review_reason": quote.requires_review_reason,
        "approval_method": quote.approval_method,
        "approved_by": quote.approved_by,
        "approved_at": quote.approved_at.isoformat() if quote.approved_at else None,
        "rejection_reason": quote.rejection_reason,
        "rush_level": quote.rush_level,
        "requested_delivery_date": quote.requested_delivery_date.isoformat() if quote.requested_delivery_date else None,
        # Admin notes
        "admin_notes": quote.admin_notes,
        "internal_notes": quote.internal_notes,
        # Links
        "product_id": quote.product_id,
        "sales_order_id": quote.sales_order_id,
        "gcode_file_path": quote.gcode_file_path,
        # BOM info
        "bom": {
            "id": bom.id,
            "code": bom.code,
            "total_cost": bom_total_cost,
            "lines": bom_lines,
        } if bom else None,
        # Timestamps
        "created_at": quote.created_at.isoformat() if quote.created_at else None,
        "updated_at": quote.updated_at.isoformat() if quote.updated_at else None,
        "expires_at": quote.expires_at.isoformat() if quote.expires_at else None,
        "converted_at": quote.converted_at.isoformat() if quote.converted_at else None,
    }

