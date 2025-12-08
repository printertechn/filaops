"""
Sales Order Management Endpoints

Handles converting quotes to sales orders and order lifecycle management
"""
from datetime import datetime
from typing import List, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db
from app.models.user import User
from app.models.quote import Quote
from app.models.sales_order import SalesOrder, SalesOrderLine
from app.models.production_order import ProductionOrder
from app.models.product import Product
from app.models.bom import BOM
from app.schemas.sales_order import (
    SalesOrderCreate,
    SalesOrderConvert,
    SalesOrderResponse,
    SalesOrderLineResponse,
    SalesOrderListResponse,
    SalesOrderUpdateStatus,
    SalesOrderUpdatePayment,
    SalesOrderUpdateShipping,
    SalesOrderCancel,
)
from app.api.v1.endpoints.auth import get_current_user
from app.models.manufacturing import Routing

router = APIRouter(prefix="/sales-orders", tags=["Sales Orders"])


# ============================================================================
# ENDPOINT: Create Manual Sales Order
# ============================================================================

@router.post("/", response_model=SalesOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_sales_order(
    request: SalesOrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a manual sales order (line_item type)

    This endpoint creates a line-item based sales order for standard products.
    Use this for orders from manual entry, Squarespace, WooCommerce, etc.

    For custom quote-based orders, use POST /convert/{quote_id} instead.

    Returns:
        Sales order with status 'pending'
    """
    # Validate all products exist and get their details
    line_products = []
    total_price = Decimal("0")
    total_quantity = 0

    for line in request.lines:
        product = db.query(Product).filter(Product.id == line.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product ID {line.product_id} not found"
            )

        # Use provided price or fall back to product's selling price
        unit_price = line.unit_price if line.unit_price is not None else (product.selling_price or Decimal("0"))
        line_total = unit_price * line.quantity

        line_products.append({
            "product": product,
            "quantity": line.quantity,
            "unit_price": unit_price,
            "line_total": line_total,
            "notes": line.notes,
        })

        total_price += line_total
        total_quantity += line.quantity

    # Generate order number
    year = datetime.utcnow().year
    last_order = (
        db.query(SalesOrder)
        .filter(SalesOrder.order_number.like(f"SO-{year}-%"))
        .order_by(desc(SalesOrder.order_number))
        .first()
    )

    if last_order:
        last_num = int(last_order.order_number.split("-")[2])
        next_num = last_num + 1
    else:
        next_num = 1

    order_number = f"SO-{year}-{next_num:03d}"

    # Calculate totals
    shipping_cost = request.shipping_cost or Decimal("0")
    tax_amount = Decimal("0")  # TODO: Calculate tax if needed
    grand_total = total_price + shipping_cost + tax_amount

    # Build product name summary from lines
    if len(line_products) == 1:
        product_name = f"{line_products[0]['product'].name} x{line_products[0]['quantity']}"
    else:
        product_name = f"{len(line_products)} items"

    # Get first product for material_type fallback
    first_product = line_products[0]["product"]

    # Determine user_id: use customer_id if provided, otherwise current admin
    user_id = request.customer_id if request.customer_id else current_user.id

    # Create sales order
    sales_order = SalesOrder(
        user_id=user_id,
        order_number=order_number,
        order_type="line_item",
        source=request.source or "manual",
        source_order_id=request.source_order_id,
        product_name=product_name,
        quantity=total_quantity,
        material_type=first_product.category or "PLA",  # Use category as material type fallback
        finish="standard",
        unit_price=total_price / total_quantity if total_quantity > 0 else Decimal("0"),
        total_price=total_price,
        tax_amount=tax_amount,
        shipping_cost=shipping_cost,
        grand_total=grand_total,
        status="pending",
        payment_status="pending",
        rush_level="standard",
        shipping_address_line1=request.shipping_address_line1,
        shipping_address_line2=request.shipping_address_line2,
        shipping_city=request.shipping_city,
        shipping_state=request.shipping_state,
        shipping_zip=request.shipping_zip,
        shipping_country=request.shipping_country or "USA",
        customer_notes=request.customer_notes,
        internal_notes=request.internal_notes,
    )

    db.add(sales_order)
    db.flush()  # Get sales_order.id

    # Create order lines
    for idx, line_data in enumerate(line_products, start=1):
        order_line = SalesOrderLine(
            sales_order_id=sales_order.id,
            product_id=line_data["product"].id,
            line_number=idx,
            quantity=line_data["quantity"],
            unit_price=line_data["unit_price"],
            total_price=line_data["line_total"],
            product_sku=line_data["product"].sku,
            product_name=line_data["product"].name,
            notes=line_data["notes"],
        )
        db.add(order_line)

    db.commit()
    db.refresh(sales_order)

    return sales_order


# ============================================================================
# ENDPOINT: Convert Quote to Sales Order
# ============================================================================

@router.post("/convert/{quote_id}", response_model=SalesOrderResponse, status_code=status.HTTP_201_CREATED)
async def convert_quote_to_sales_order(
    quote_id: int,
    convert_request: SalesOrderConvert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Convert an accepted quote to a sales order

    This endpoint creates a quote-based sales order from an accepted quote.
    The quote must have already been accepted (which auto-creates product + BOM).

    Requirements:
    - Quote must exist and belong to current user
    - Quote must be in 'accepted' status
    - Quote must have associated product (created during acceptance)
    - Quote must not be expired
    - Quote must not already be converted

    The sales order will be created with:
    - order_type = 'quote_based'
    - source = 'portal'
    - source_order_id = quote number

    Returns:
        Sales order with status 'pending'
    """
    # Get quote
    quote = db.query(Quote).filter(Quote.id == quote_id).first()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )

    # Verify ownership
    if quote.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to convert this quote"
        )

    # Check if quote is accepted
    if quote.status != "accepted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot convert quote with status '{quote.status}'. Must be 'accepted'."
        )

    # Check if quote is expired
    if quote.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quote has expired. Please request a new quote."
        )

    # Check if quote is already converted
    if quote.sales_order_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Quote already converted to sales order"
        )

    # Verify quote has product_id (created during acceptance)
    if not quote.product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quote does not have an associated product. This should have been created during acceptance."
        )

    # Generate sales order number
    year = datetime.utcnow().year
    last_order = (
        db.query(SalesOrder)
        .filter(SalesOrder.order_number.like(f"SO-{year}-%"))
        .order_by(desc(SalesOrder.order_number))
        .first()
    )

    if last_order:
        last_num = int(last_order.order_number.split("-")[2])
        next_num = last_num + 1
    else:
        next_num = 1

    order_number = f"SO-{year}-{next_num:03d}"

    # Calculate grand total (no tax/shipping for now, but structure is ready)
    grand_total = quote.total_price

    # Create sales order
    sales_order = SalesOrder(
        user_id=current_user.id,
        quote_id=quote.id,
        order_number=order_number,
        product_name=quote.product_name,
        quantity=quote.quantity,
        material_type=quote.material_type,
        finish=quote.finish,
        unit_price=quote.unit_price,
        total_price=quote.total_price,
        tax_amount=Decimal('0.00'),
        shipping_cost=Decimal('0.00'),
        grand_total=grand_total,
        status="pending",
        payment_status="pending",
        rush_level=quote.rush_level,
        shipping_address_line1=convert_request.shipping_address_line1,
        shipping_address_line2=convert_request.shipping_address_line2,
        shipping_city=convert_request.shipping_city,
        shipping_state=convert_request.shipping_state,
        shipping_zip=convert_request.shipping_zip,
        shipping_country=convert_request.shipping_country or "USA",
        customer_notes=convert_request.customer_notes or quote.customer_notes,
        # Hybrid architecture fields
        order_type="quote_based",
        source="portal",
        source_order_id=quote.quote_number,
    )

    db.add(sales_order)
    db.flush()  # Get sales_order.id

    # Update quote to mark as converted
    quote.sales_order_id = sales_order.id
    quote.converted_at = datetime.utcnow()

    # =========================================================================
    # Create Production Order
    # =========================================================================
    # Find the BOM for this product
    bom = db.query(BOM).filter(
        BOM.product_id == quote.product_id,
        BOM.active == True
    ).first()

    # Generate production order code
    last_po = (
        db.query(ProductionOrder)
        .filter(ProductionOrder.code.like(f"PO-{year}-%"))
        .order_by(desc(ProductionOrder.code))
        .first()
    )

    if last_po:
        last_po_num = int(last_po.code.split("-")[2])
        next_po_num = last_po_num + 1
    else:
        next_po_num = 1

    po_code = f"PO-{year}-{next_po_num:03d}"

    # Calculate estimated print time from quote
    estimated_time_minutes = int(quote.print_time_hours * 60) if quote.print_time_hours else None

    # Create production order
    production_order = ProductionOrder(
        code=po_code,
        product_id=quote.product_id,
        bom_id=bom.id if bom else None,
        sales_order_id=sales_order.id,  # Link to sales order for transaction tracking
        quantity=quote.quantity,
        status="scheduled",  # Ready for production
        priority="normal" if quote.rush_level == "standard" else "high",
        estimated_time_minutes=estimated_time_minutes,
        notes=f"Auto-created from Sales Order {order_number}. Quote: {quote.quote_number}",
        created_by=current_user.email,
    )

    db.add(production_order)

    # Log the creation
    print(f"[PRODUCTION] Created {po_code} for SO {order_number}, Product ID: {quote.product_id}")

    db.commit()
    db.refresh(sales_order)

    return sales_order


# ============================================================================
# ENDPOINT: Get User's Sales Orders
# ============================================================================

@router.get("/", response_model=List[SalesOrderListResponse])
async def get_user_sales_orders(
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get list of sales orders

    Query parameters:
    - skip: Pagination offset (default: 0)
    - limit: Max results (default: 50, max: 100)
    - status_filter: Filter by status (pending, confirmed, in_production, etc.)

    Returns:
        List of sales orders ordered by creation date (newest first)
        - Admin users see ALL orders
        - Regular users see only their own orders
    """
    if limit > 100:
        limit = 100

    query = db.query(SalesOrder)

    # Admin users can see all orders, regular users only see their own
    if current_user.account_type != "admin":
        query = query.filter(SalesOrder.user_id == current_user.id)

    if status_filter:
        query = query.filter(SalesOrder.status == status_filter)

    orders = (
        query
        .order_by(desc(SalesOrder.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    return orders


# ============================================================================
# ENDPOINT: Get Sales Order Details
# ============================================================================

@router.get("/{order_id}", response_model=SalesOrderResponse)
async def get_sales_order_details(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific sales order

    Returns:
        Complete sales order data including shipping and payment info
    """
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales order not found"
        )

    # Verify user owns this order
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order"
        )

    return order


# ============================================================================
# ENDPOINT: Update Order Status (Admin)
# ============================================================================

@router.patch("/{order_id}/status", response_model=SalesOrderResponse)
async def update_order_status(
    order_id: int,
    update: SalesOrderUpdateStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update sales order status (admin only)

    Allowed status transitions:
    - pending → confirmed
    - confirmed → in_production
    - in_production → quality_check
    - quality_check → shipped
    - shipped → delivered
    - delivered → completed
    - Any → on_hold, cancelled

    Returns:
        Updated sales order
    """
    # TODO: Add admin role check
    # For now, any authenticated user can update

    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales order not found"
        )

    # Update status
    old_status = order.status
    order.status = update.status

    # Set timestamps based on status
    if update.status == "confirmed" and old_status == "pending":
        order.confirmed_at = datetime.utcnow()

    if update.status == "shipped":
        order.shipped_at = datetime.utcnow()

    if update.status == "delivered":
        order.delivered_at = datetime.utcnow()

    if update.status == "completed":
        order.actual_completion_date = datetime.utcnow()

    # Update notes
    if update.internal_notes:
        order.internal_notes = update.internal_notes

    if update.production_notes:
        order.production_notes = update.production_notes

    db.commit()
    db.refresh(order)

    return order


# ============================================================================
# ENDPOINT: Update Payment Information
# ============================================================================

@router.patch("/{order_id}/payment", response_model=SalesOrderResponse)
async def update_payment_info(
    order_id: int,
    update: SalesOrderUpdatePayment,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update payment information for an order

    Returns:
        Updated sales order
    """
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales order not found"
        )

    # Update payment info
    order.payment_status = update.payment_status

    if update.payment_method:
        order.payment_method = update.payment_method

    if update.payment_transaction_id:
        order.payment_transaction_id = update.payment_transaction_id

    if update.payment_status == "paid":
        order.paid_at = datetime.utcnow()

    db.commit()
    db.refresh(order)

    return order


# ============================================================================
# ENDPOINT: Update Shipping Information
# ============================================================================

@router.patch("/{order_id}/shipping", response_model=SalesOrderResponse)
async def update_shipping_info(
    order_id: int,
    update: SalesOrderUpdateShipping,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update shipping information for an order

    Returns:
        Updated sales order
    """
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales order not found"
        )

    # Update shipping info
    if update.tracking_number:
        order.tracking_number = update.tracking_number

    if update.carrier:
        order.carrier = update.carrier

    if update.shipped_at:
        order.shipped_at = update.shipped_at
        order.status = "shipped"

    db.commit()
    db.refresh(order)

    return order


# ============================================================================
# ENDPOINT: Cancel Sales Order
# ============================================================================

@router.post("/{order_id}/cancel", response_model=SalesOrderResponse)
async def cancel_sales_order(
    order_id: int,
    cancel_request: SalesOrderCancel,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cancel a sales order

    Requirements:
    - Order must be cancellable (pending, confirmed, or on_hold)
    - User must own the order

    Returns:
        Cancelled sales order
    """
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales order not found"
        )

    # Verify ownership
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this order"
        )

    # Check if order can be cancelled
    if not order.is_cancellable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status '{order.status}'"
        )

    # Cancel order
    order.status = "cancelled"
    order.cancelled_at = datetime.utcnow()
    order.cancellation_reason = cancel_request.cancellation_reason

    db.commit()
    db.refresh(order)

    return order


# ============================================================================
# ENDPOINT: Generate Production Orders from Sales Order
# ============================================================================

@router.post("/{order_id}/generate-production-orders")
async def generate_production_orders(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate production orders from a sales order.

    For line_item orders: Creates one production order per line item.
    For quote_based orders: Creates a single production order.

    Requirements:
    - Sales order must exist
    - Sales order must not be cancelled
    - Line items must have valid products
    - No duplicate production orders (checks existing)

    Returns:
        List of created production order codes
    """
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales order not found"
        )

    if order.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot generate production orders for cancelled sales order"
        )

    # Check if production orders already exist for this sales order
    existing_pos = db.query(ProductionOrder).filter(
        ProductionOrder.sales_order_id == order_id
    ).all()

    if existing_pos:
        return {
            "message": "Production orders already exist",
            "existing_orders": [po.code for po in existing_pos],
            "created_orders": []
        }

    created_orders = []
    year = datetime.utcnow().year

    # Helper to generate next PO code
    def get_next_po_code():
        last_po = (
            db.query(ProductionOrder)
            .filter(ProductionOrder.code.like(f"PO-{year}-%"))
            .order_by(desc(ProductionOrder.code))
            .first()
        )
        if last_po:
            last_num = int(last_po.code.split("-")[2])
            next_num = last_num + 1
        else:
            next_num = 1
        return f"PO-{year}-{next_num:04d}"

    if order.order_type == "line_item":
        # Get all lines for this order
        lines = db.query(SalesOrderLine).filter(
            SalesOrderLine.sales_order_id == order_id
        ).order_by(SalesOrderLine.line_number).all()

        if not lines:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sales order has no line items"
            )

        for line in lines:
            product = db.query(Product).filter(Product.id == line.product_id).first()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product ID {line.product_id} not found for line {line.line_number}"
                )

            # Find BOM for product (first active one)
            bom = db.query(BOM).filter(
                BOM.product_id == line.product_id,
                BOM.active == True
            ).first()

            routing = db.query(Routing).filter(
                Routing.product_id == line.product_id,
                Routing.is_active == True
            ).first()

            po_code = get_next_po_code()

            production_order = ProductionOrder(
                code=po_code,
                product_id=line.product_id,
                bom_id=bom.id if bom else None,
                routing_id=routing.id if routing else None,
                sales_order_id=order.id,
                sales_order_line_id=line.id,
                quantity_ordered=line.quantity,
                quantity_completed=0,
                quantity_scrapped=0,
                source="sales_order",
                status="draft",
                priority=3,  # Normal priority
                notes=f"Generated from {order.order_number} Line {line.line_number}",
                created_by=current_user.email,
            )

            db.add(production_order)
            db.flush()  # Get the ID for the next PO code lookup
            created_orders.append(po_code)

    else:
        # quote_based order - should already have production order from convert
        # But we can create one if it doesn't exist

        # For quote-based, we need to find the product_id from the quote
        if order.quote_id:
            quote = db.query(Quote).filter(Quote.id == order.quote_id).first()
            if quote and quote.product_id:
                product_id = quote.product_id

                bom = db.query(BOM).filter(
                    BOM.product_id == product_id,
                    BOM.active == True
                ).first()

                routing = db.query(Routing).filter(
                    Routing.product_id == product_id,
                    Routing.is_active == True
                ).first()

                po_code = get_next_po_code()

                production_order = ProductionOrder(
                    code=po_code,
                    product_id=product_id,
                    bom_id=bom.id if bom else None,
                    routing_id=routing.id if routing else None,
                    sales_order_id=order.id,
                    quantity_ordered=order.quantity,
                    quantity_completed=0,
                    quantity_scrapped=0,
                    source="sales_order",
                    status="draft",
                    priority=3,
                    notes=f"Generated from {order.order_number}",
                    created_by=current_user.email,
                )

                db.add(production_order)
                created_orders.append(po_code)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quote-based order has no product. Please accept the quote first."
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quote-based order has no associated quote"
            )

    db.commit()

    # Update order status to confirmed if pending
    if order.status == "pending":
        order.status = "confirmed"
        order.confirmed_at = datetime.utcnow()
        db.commit()

    return {
        "message": f"Created {len(created_orders)} production order(s)",
        "created_orders": created_orders,
        "existing_orders": []
    }


# ============================================================================
# Helper: Build response with lines
# ============================================================================

def build_sales_order_response(order: SalesOrder, db: Session) -> dict:
    """Build sales order response with line items"""
    lines = []
    if order.order_type == "line_item":
        order_lines = db.query(SalesOrderLine).filter(
            SalesOrderLine.sales_order_id == order.id
        ).order_by(SalesOrderLine.line_number).all()

        for line in order_lines:
            product = db.query(Product).filter(Product.id == line.product_id).first()
            lines.append(SalesOrderLineResponse(
                id=line.id,
                line_number=line.line_number,
                product_id=line.product_id,
                product_sku=product.sku if product else line.product_sku,
                product_name=product.name if product else line.product_name,
                quantity=line.quantity,
                unit_price=line.unit_price,
                total_price=line.total_price,
                notes=line.notes,
            ))

    return {
        **order.__dict__,
        "lines": lines,
    }
