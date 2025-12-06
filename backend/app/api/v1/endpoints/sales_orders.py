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
from app.models.sales_order import SalesOrder
from app.models.production_order import ProductionOrder
from app.models.bom import BOM
from app.schemas.sales_order import (
    SalesOrderConvert,
    SalesOrderResponse,
    SalesOrderListResponse,
    SalesOrderUpdateStatus,
    SalesOrderUpdatePayment,
    SalesOrderUpdateShipping,
    SalesOrderCancel,
)
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter(prefix="/sales-orders", tags=["Sales Orders"])


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
    Get list of sales orders for current user

    Query parameters:
    - skip: Pagination offset (default: 0)
    - limit: Max results (default: 50, max: 100)
    - status_filter: Filter by status (pending, confirmed, in_production, etc.)

    Returns:
        List of sales orders ordered by creation date (newest first)
    """
    if limit > 100:
        limit = 100

    query = db.query(SalesOrder).filter(SalesOrder.user_id == current_user.id)

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
