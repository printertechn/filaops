"""
Shipping endpoints for EasyPost integration

Handles rate calculation and label generation
"""
from typing import List, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.models.quote import Quote
from app.models.sales_order import SalesOrder
from app.services.shipping_service import shipping_service, ShippingRate

router = APIRouter(prefix="/shipping", tags=["Shipping"])


# ============================================================================
# SCHEMAS
# ============================================================================

class AddressInput(BaseModel):
    """Shipping address input"""
    name: str = Field(..., max_length=100)
    street1: str = Field(..., max_length=255)
    street2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=50)
    zip: str = Field(..., max_length=20)
    country: str = Field("US", max_length=2)


class PackageInput(BaseModel):
    """Package dimensions and weight"""
    weight_oz: float = Field(16.0, description="Weight in ounces")
    length: float = Field(10.0, description="Length in inches")
    width: float = Field(8.0, description="Width in inches")
    height: float = Field(4.0, description="Height in inches")


class GetRatesRequest(BaseModel):
    """Request to get shipping rates"""
    address: AddressInput
    package: Optional[PackageInput] = None
    # Or calculate from quote
    quote_id: Optional[int] = None


class RateResponse(BaseModel):
    """Single shipping rate option"""
    carrier: str
    service: str
    rate: float
    est_delivery_days: Optional[int]
    rate_id: str
    display_name: str  # Friendly name like "USPS Priority Mail"


class RatesResponse(BaseModel):
    """Response with available shipping rates"""
    success: bool
    rates: List[RateResponse]
    shipment_id: Optional[str] = None
    error: Optional[str] = None


class BuyLabelRequest(BaseModel):
    """Request to purchase a shipping label"""
    rate_id: str
    shipment_id: Optional[str] = None
    order_id: Optional[int] = None  # Update order with tracking


class LabelResponse(BaseModel):
    """Response with shipping label"""
    success: bool
    tracking_number: Optional[str] = None
    label_url: Optional[str] = None
    carrier: Optional[str] = None
    service: Optional[str] = None
    rate: Optional[float] = None
    error: Optional[str] = None


class QuoteRatesRequest(BaseModel):
    """Get rates for a specific quote"""
    quote_id: int


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_rate_display(carrier: str, service: str) -> str:
    """Create friendly display name for rate"""
    # Clean up service names
    service_map = {
        "First": "First Class",
        "Priority": "Priority Mail",
        "Express": "Express Mail",
        "ParcelSelect": "Parcel Select Ground",
        "Ground": "Ground",
        "GroundSaver": "Ground Saver",
        "UPSSaver": "UPS Saver",
        "NextDayAir": "Next Day Air",
        "2ndDayAir": "2nd Day Air",
    }

    display_service = service
    for key, value in service_map.items():
        if key.lower() in service.lower():
            display_service = value
            break

    return f"{carrier} {display_service}"


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/rates", response_model=RatesResponse)
async def get_shipping_rates(
    request: GetRatesRequest,
    db: Session = Depends(get_db),
):
    """
    Get available shipping rates for an address.

    Can provide package dimensions directly, or pass a quote_id
    to auto-calculate based on the print weight/dimensions.
    """
    # Determine package size
    weight_oz = 16.0  # Default 1 lb
    length, width, height = 10.0, 8.0, 4.0

    if request.package:
        weight_oz = request.package.weight_oz
        length = request.package.length
        width = request.package.width
        height = request.package.height
    elif request.quote_id:
        # Calculate from quote
        quote = db.query(Quote).filter(Quote.id == request.quote_id).first()
        if quote:
            # Estimate weight from material
            if quote.material_grams:
                weight_oz = shipping_service.estimate_weight_oz(
                    float(quote.material_grams),
                    quote.quantity
                )

            # Estimate box from dimensions
            if quote.dimensions_x and quote.dimensions_y and quote.dimensions_z:
                length, width, height = shipping_service.estimate_box_size(
                    (float(quote.dimensions_x), float(quote.dimensions_y), float(quote.dimensions_z)),
                    quote.quantity
                )

    # Get rates from EasyPost (returns tuple of rates and shipment_id)
    rates, shipment_id = shipping_service.get_shipping_rates(
        to_name=request.address.name,
        to_street1=request.address.street1,
        to_street2=request.address.street2,
        to_city=request.address.city,
        to_state=request.address.state,
        to_zip=request.address.zip,
        to_country=request.address.country,
        weight_oz=weight_oz,
        length=length,
        width=width,
        height=height,
    )

    if not rates:
        return RatesResponse(
            success=False,
            rates=[],
            error="No shipping rates available. Please verify the address."
        )

    # Format response
    rate_responses = [
        RateResponse(
            carrier=r.carrier,
            service=r.service,
            rate=float(r.rate),
            est_delivery_days=r.est_delivery_days,
            rate_id=r.rate_id,
            display_name=format_rate_display(r.carrier, r.service),
        )
        for r in rates
    ]

    return RatesResponse(
        success=True,
        rates=rate_responses,
        shipment_id=shipment_id,
    )


@router.post("/rates/quote/{quote_id}", response_model=RatesResponse)
async def get_rates_for_quote(
    quote_id: int,
    db: Session = Depends(get_db),
):
    """
    Get shipping rates for a specific quote.

    Uses the quote's shipping address and calculates package
    size from the print dimensions/weight.
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    # Check for shipping address
    if not quote.shipping_address_line1:
        raise HTTPException(
            status_code=400,
            detail="Quote has no shipping address"
        )

    # Calculate package dimensions
    weight_oz = 16.0
    length, width, height = 10.0, 8.0, 4.0

    if quote.material_grams:
        weight_oz = shipping_service.estimate_weight_oz(
            float(quote.material_grams),
            quote.quantity
        )

    if quote.dimensions_x and quote.dimensions_y and quote.dimensions_z:
        length, width, height = shipping_service.estimate_box_size(
            (float(quote.dimensions_x), float(quote.dimensions_y), float(quote.dimensions_z)),
            quote.quantity
        )

    # Get rates (returns tuple of rates and shipment_id)
    rates, shipment_id = shipping_service.get_shipping_rates(
        to_name=quote.shipping_name or "Customer",
        to_street1=quote.shipping_address_line1,
        to_street2=quote.shipping_address_line2,
        to_city=quote.shipping_city,
        to_state=quote.shipping_state,
        to_zip=quote.shipping_zip,
        to_country=quote.shipping_country or "US",
        weight_oz=weight_oz,
        length=length,
        width=width,
        height=height,
    )

    if not rates:
        return RatesResponse(
            success=False,
            rates=[],
            error="No shipping rates available. Please verify the address."
        )

    rate_responses = [
        RateResponse(
            carrier=r.carrier,
            service=r.service,
            rate=float(r.rate),
            est_delivery_days=r.est_delivery_days,
            rate_id=r.rate_id,
            display_name=format_rate_display(r.carrier, r.service),
        )
        for r in rates
    ]

    return RatesResponse(
        success=True,
        rates=rate_responses,
        shipment_id=shipment_id,
    )


@router.post("/buy", response_model=LabelResponse)
async def buy_shipping_label(
    request: BuyLabelRequest,
    db: Session = Depends(get_db),
):
    """
    Purchase a shipping label for a selected rate.

    Optionally pass order_id to update the order with tracking info.
    """
    result = shipping_service.buy_label(
        rate_id=request.rate_id,
        shipment_id=request.shipment_id,
    )

    if not result.success:
        return LabelResponse(
            success=False,
            error=result.error or "Failed to purchase label"
        )

    # Update order with tracking if provided
    if request.order_id:
        order = db.query(SalesOrder).filter(SalesOrder.id == request.order_id).first()
        if order:
            order.tracking_number = result.tracking_number
            order.carrier = result.carrier
            db.commit()

    return LabelResponse(
        success=True,
        tracking_number=result.tracking_number,
        label_url=result.label_url,
        carrier=result.carrier,
        service=result.service,
        rate=float(result.rate) if result.rate else None,
    )


@router.post("/label/order/{order_id}", response_model=LabelResponse)
async def create_label_for_order(
    order_id: int,
    carrier_preference: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Create and purchase the cheapest shipping label for an order.

    Uses the order's shipping address and estimates package size.
    Optionally filter by carrier (USPS, UPS, FedEx).
    """
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not order.shipping_address_line1:
        raise HTTPException(status_code=400, detail="Order has no shipping address")

    # Estimate package size (default for now, can enhance later)
    weight_oz = 16.0  # 1 lb default
    length, width, height = 10.0, 8.0, 4.0

    # If order has a quote, use its dimensions
    if order.quote_id:
        quote = db.query(Quote).filter(Quote.id == order.quote_id).first()
        if quote and quote.material_grams:
            weight_oz = shipping_service.estimate_weight_oz(
                float(quote.material_grams),
                order.quantity
            )
        if quote and quote.dimensions_x:
            length, width, height = shipping_service.estimate_box_size(
                (float(quote.dimensions_x), float(quote.dimensions_y), float(quote.dimensions_z)),
                order.quantity
            )

    # Create and buy
    carrier_filter = [carrier_preference] if carrier_preference else None
    result = shipping_service.create_and_buy_cheapest(
        to_name=order.shipping_address_line1.split('\n')[0] if '\n' in (order.shipping_address_line1 or '') else "Customer",
        to_street1=order.shipping_address_line1,
        to_street2=order.shipping_address_line2,
        to_city=order.shipping_city,
        to_state=order.shipping_state,
        to_zip=order.shipping_zip,
        to_country=order.shipping_country or "US",
        weight_oz=weight_oz,
        length=length,
        width=width,
        height=height,
        carrier_filter=carrier_filter,
    )

    if not result.success:
        return LabelResponse(
            success=False,
            error=result.error or "Failed to create label"
        )

    # Update order with tracking
    order.tracking_number = result.tracking_number
    order.carrier = result.carrier
    order.shipping_cost = result.rate
    db.commit()

    return LabelResponse(
        success=True,
        tracking_number=result.tracking_number,
        label_url=result.label_url,
        carrier=result.carrier,
        service=result.service,
        rate=float(result.rate) if result.rate else None,
    )
