"""
Sales Order Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


# ============================================================================
# Request Schemas
# ============================================================================

class SalesOrderConvert(BaseModel):
    """Request to convert quote to sales order"""
    shipping_address_line1: Optional[str] = Field(None, max_length=255)
    shipping_address_line2: Optional[str] = Field(None, max_length=255)
    shipping_city: Optional[str] = Field(None, max_length=100)
    shipping_state: Optional[str] = Field(None, max_length=50)
    shipping_zip: Optional[str] = Field(None, max_length=20)
    shipping_country: Optional[str] = Field("USA", max_length=100)
    customer_notes: Optional[str] = Field(None, max_length=5000)


class SalesOrderUpdateStatus(BaseModel):
    """Update sales order status (admin)"""
    status: str = Field(..., description="Order status")
    internal_notes: Optional[str] = Field(None, description="Internal notes")
    production_notes: Optional[str] = Field(None, description="Production notes")


class SalesOrderUpdatePayment(BaseModel):
    """Update payment information"""
    payment_status: str = Field(..., description="Payment status")
    payment_method: Optional[str] = Field(None, description="Payment method")
    payment_transaction_id: Optional[str] = Field(None, description="Transaction ID")


class SalesOrderUpdateShipping(BaseModel):
    """Update shipping information"""
    tracking_number: Optional[str] = Field(None, max_length=255)
    carrier: Optional[str] = Field(None, max_length=100)
    shipped_at: Optional[datetime] = None


class SalesOrderCancel(BaseModel):
    """Cancel sales order"""
    cancellation_reason: str = Field(..., max_length=1000)


# ============================================================================
# Response Schemas
# ============================================================================

class SalesOrderBase(BaseModel):
    """Base sales order fields"""
    order_number: str
    product_name: Optional[str]
    quantity: int
    material_type: str
    finish: str
    unit_price: Decimal
    total_price: Decimal
    tax_amount: Decimal
    shipping_cost: Decimal
    grand_total: Decimal
    status: str
    payment_status: str
    rush_level: str


class SalesOrderListResponse(SalesOrderBase):
    """Sales order list item"""
    id: int
    quote_id: Optional[int]
    created_at: datetime
    confirmed_at: Optional[datetime]
    estimated_completion_date: Optional[datetime]

    class Config:
        from_attributes = True


class SalesOrderResponse(SalesOrderBase):
    """Full sales order details"""
    id: int
    user_id: int
    quote_id: Optional[int]

    # Payment
    payment_method: Optional[str]
    payment_transaction_id: Optional[str]
    paid_at: Optional[datetime]

    # Production
    estimated_completion_date: Optional[datetime]
    actual_completion_date: Optional[datetime]

    # Shipping
    shipping_address_line1: Optional[str]
    shipping_address_line2: Optional[str]
    shipping_city: Optional[str]
    shipping_state: Optional[str]
    shipping_zip: Optional[str]
    shipping_country: Optional[str]
    tracking_number: Optional[str]
    carrier: Optional[str]
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]

    # Notes
    customer_notes: Optional[str]
    internal_notes: Optional[str]
    production_notes: Optional[str]

    # Cancellation
    cancelled_at: Optional[datetime]
    cancellation_reason: Optional[str]

    # Timestamps
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime]

    class Config:
        from_attributes = True


class SalesOrderStatsResponse(BaseModel):
    """Sales order statistics"""
    total_orders: int
    pending_orders: int
    confirmed_orders: int
    in_production_orders: int
    completed_orders: int
    cancelled_orders: int
    total_revenue: Decimal
    pending_revenue: Decimal
