"""
Payment endpoints for Stripe integration

Handles checkout sessions, payment verification, and webhooks
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel

from app.db.session import get_db
from app.models.quote import Quote
from app.models.sales_order import SalesOrder
from app.models.user import User
from app.services.stripe_service import stripe_service
from app.services.bom_service import auto_create_product_and_bom
from app.services.quote_conversion_service import convert_quote_to_order
from app.core.config import settings

router = APIRouter(prefix="/payments", tags=["Payments"])


# ============================================================================
# SCHEMAS
# ============================================================================

class CreateCheckoutRequest(BaseModel):
    """Request to create a Stripe checkout session"""
    quote_id: int
    shipping_cost: Optional[float] = None


class CheckoutSessionResponse(BaseModel):
    """Response with checkout session URL"""
    checkout_url: str
    session_id: str


class VerifyPaymentRequest(BaseModel):
    """Request to verify a payment"""
    session_id: str
    quote_id: int


class PaymentStatusResponse(BaseModel):
    """Response with payment status"""
    success: bool
    payment_status: str
    order_number: Optional[str] = None
    message: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_order_number(db: Session) -> str:
    """Generate next sequential order number (SO-YYYY-NNN)"""
    year = datetime.utcnow().year
    last_order = (
        db.query(SalesOrder)
        .filter(SalesOrder.order_number.like(f"SO-{year}-%"))
        .order_by(desc(SalesOrder.order_number))
        .first()
    )
    if last_order:
        try:
            last_num = int(last_order.order_number.split("-")[2])
            next_num = last_num + 1
        except (ValueError, IndexError):
            next_num = 1
    else:
        next_num = 1
    return f"SO-{year}-{next_num:03d}"


def create_sales_order_from_quote(quote: Quote, payment_intent_id: str, db: Session) -> SalesOrder:
    """
    Create a sales order from a paid quote.

    Args:
        quote: The accepted quote
        payment_intent_id: Stripe payment intent ID
        db: Database session

    Returns:
        Created SalesOrder
    """
    order_number = generate_order_number(db)

    # Calculate grand total (product + shipping)
    product_total = float(quote.total_price) if quote.total_price else 0
    shipping_cost = float(quote.shipping_cost) if quote.shipping_cost else 0
    grand_total = product_total + shipping_cost

    sales_order = SalesOrder(
        user_id=quote.user_id,
        quote_id=quote.id,
        order_number=order_number,
        order_type="quote_based",
        source="portal",
        # Product info from quote
        product_name=quote.product_name,
        quantity=quote.quantity,
        material_type=quote.material_type,
        finish=quote.finish,
        # Pricing
        unit_price=quote.unit_price or quote.total_price,
        total_price=quote.total_price,
        shipping_cost=quote.shipping_cost,
        grand_total=grand_total,
        # Payment - PAID!
        status="confirmed",
        payment_status="paid",
        payment_method="stripe",
        payment_transaction_id=payment_intent_id,
        paid_at=datetime.utcnow(),
        confirmed_at=datetime.utcnow(),
        # Rush
        rush_level=quote.rush_level,
        # Shipping from quote
        shipping_address_line1=quote.shipping_address_line1,
        shipping_address_line2=quote.shipping_address_line2,
        shipping_city=quote.shipping_city,
        shipping_state=quote.shipping_state,
        shipping_zip=quote.shipping_zip,
        shipping_country=quote.shipping_country,
        carrier=quote.shipping_carrier,
        # Notes
        customer_notes=quote.customer_notes,
    )

    db.add(sales_order)
    db.flush()  # Get the ID

    # Update quote with sales order reference
    quote.sales_order_id = sales_order.id
    quote.converted_at = datetime.utcnow()
    quote.status = "converted"

    return sales_order


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/create-checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CreateCheckoutRequest,
    db: Session = Depends(get_db),
):
    """
    Create a Stripe Checkout session for a quote.

    The customer will be redirected to Stripe's hosted checkout page.
    On success, they'll be redirected back to /payment/success.
    """
    # Get the quote
    quote = db.query(Quote).filter(Quote.id == request.quote_id).first()
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )

    # Verify quote is in acceptable state
    if quote.status not in ["accepted", "pending", "approved"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot pay for quote with status '{quote.status}'"
        )

    # Check expiration
    if quote.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quote has expired. Please request a new quote."
        )

    # Get customer email
    customer_email = None
    if quote.user_id:
        user = db.query(User).filter(User.id == quote.user_id).first()
        if user:
            customer_email = user.email

    # Calculate total with shipping
    product_amount = float(quote.total_price)
    shipping_amount = request.shipping_cost or 0.0
    total_amount = product_amount + shipping_amount

    # Store shipping cost on quote for reference
    if request.shipping_cost:
        quote.shipping_cost = request.shipping_cost
        db.commit()

    # Create or get Stripe Customer with shipping address for tax calculation
    # Stripe Tax uses the customer's shipping address to determine tax rates
    stripe_customer_id = None
    if customer_email and quote.shipping_address_line1:
        try:
            customer = stripe_service.get_or_create_customer(
                email=customer_email,
                name=quote.shipping_name,
                shipping_address={
                    "line1": quote.shipping_address_line1,
                    "line2": quote.shipping_address_line2,
                    "city": quote.shipping_city,
                    "state": quote.shipping_state,
                    "postal_code": quote.shipping_zip,
                    "country": quote.shipping_country or "US",
                }
            )
            stripe_customer_id = customer.id
        except Exception as e:
            # If customer creation fails, proceed without (tax may not be calculated)
            print(f"[PAYMENT] Warning: Could not create Stripe customer for tax: {e}")

    # Create Stripe checkout session
    try:
        session = stripe_service.create_checkout_session(
            quote_id=quote.id,
            quote_number=quote.quote_number,
            amount_dollars=total_amount,
            customer_email=customer_email,
            customer_id=stripe_customer_id,
            product_name=quote.product_name,
            material=quote.material_type,
            quantity=quote.quantity,
            shipping_cost=shipping_amount if shipping_amount > 0 else None,
        )

        return CheckoutSessionResponse(
            checkout_url=session.url,
            session_id=session.id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@router.post("/verify", response_model=PaymentStatusResponse)
async def verify_payment(
    request: VerifyPaymentRequest,
    db: Session = Depends(get_db),
):
    """
    Verify a payment after customer returns from Stripe checkout.

    This is called when the customer lands on the success page.
    It creates the sales order if payment was successful.
    """
    try:
        # Retrieve the session from Stripe
        session = stripe_service.retrieve_session(request.session_id)

        # Check payment status
        if session.payment_status != "paid":
            return PaymentStatusResponse(
                success=False,
                payment_status=session.payment_status,
                message="Payment not completed"
            )

        # Get the quote
        quote = db.query(Quote).filter(Quote.id == request.quote_id).first()
        if not quote:
            return PaymentStatusResponse(
                success=False,
                payment_status="error",
                message="Quote not found"
            )

        # Check if already converted
        if quote.status == "converted" and quote.sales_order_id:
            # Already processed, return success
            order = db.query(SalesOrder).filter(SalesOrder.id == quote.sales_order_id).first()
            return PaymentStatusResponse(
                success=True,
                payment_status="paid",
                order_number=order.order_number if order else None,
                message="Order already created"
            )

        # Use the unified conversion service (creates Product, BOM, Sales Order, Production Order)
        payment_intent_id = session.payment_intent
        result = convert_quote_to_order(
            quote=quote,
            db=db,
            payment_status="paid",
            auto_confirm=True,
        )

        if not result.success:
            return PaymentStatusResponse(
                success=False,
                payment_status="error",
                message=f"Conversion failed: {result.error_message}"
            )

        # Update payment details on the sales order
        if result.sales_order:
            result.sales_order.payment_method = "stripe"
            result.sales_order.payment_transaction_id = payment_intent_id
            result.sales_order.paid_at = datetime.utcnow()

            # Capture tax amount from Stripe (if automatic_tax was used)
            if hasattr(session, 'total_details') and session.total_details:
                tax_cents = session.total_details.amount_tax or 0
                if tax_cents > 0:
                    result.sales_order.tax_amount = tax_cents / 100.0
                    # Recalculate grand total to include tax
                    result.sales_order.grand_total = (
                        float(result.sales_order.total_price or 0) +
                        float(result.sales_order.shipping_cost or 0) +
                        float(result.sales_order.tax_amount)
                    )
                    print(f"[PAYMENT] Tax applied: ${result.sales_order.tax_amount:.2f}")

            db.commit()

        print(f"[PAYMENT] Quote {quote.quote_number} paid -> Order {result.sales_order.order_number} -> PO {result.production_order.code}")

        return PaymentStatusResponse(
            success=True,
            payment_status="paid",
            order_number=result.sales_order.order_number,
            message="Payment successful! Order and production order created."
        )

    except Exception as e:
        db.rollback()
        print(f"[PAYMENT] Verification error: {e}")
        return PaymentStatusResponse(
            success=False,
            payment_status="error",
            message=f"Error verifying payment: {str(e)}"
        )


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Stripe webhook events.

    This is called by Stripe when payment events occur.
    Primarily handles checkout.session.completed events.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe_service.verify_webhook_signature(payload, sig_header)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Handle the event
    event_type = event.get("type") if isinstance(event, dict) else event.type
    data = event.get("data", {}) if isinstance(event, dict) else event.data

    print(f"[STRIPE WEBHOOK] Received event: {event_type}")

    if event_type == "checkout.session.completed":
        session = data.get("object") if isinstance(data, dict) else data.object

        # Get quote ID from metadata
        metadata = session.get("metadata", {}) if isinstance(session, dict) else session.metadata
        quote_id = metadata.get("quote_id")

        if quote_id:
            quote_id = int(quote_id)
            quote = db.query(Quote).filter(Quote.id == quote_id).first()

            if quote and quote.status != "converted":
                # Get payment intent ID
                payment_intent_id = (
                    session.get("payment_intent")
                    if isinstance(session, dict)
                    else session.payment_intent
                )

                # Use unified conversion service (creates Product, BOM, Sales Order, Production Order)
                result = convert_quote_to_order(
                    quote=quote,
                    db=db,
                    payment_status="paid",
                    auto_confirm=True,
                )

                if result.success and result.sales_order:
                    result.sales_order.payment_method = "stripe"
                    result.sales_order.payment_transaction_id = payment_intent_id
                    result.sales_order.paid_at = datetime.utcnow()

                    # Capture tax amount from Stripe session
                    total_details = (
                        session.get("total_details") if isinstance(session, dict)
                        else getattr(session, "total_details", None)
                    )
                    if total_details:
                        tax_cents = (
                            total_details.get("amount_tax", 0) if isinstance(total_details, dict)
                            else getattr(total_details, "amount_tax", 0)
                        ) or 0
                        if tax_cents > 0:
                            result.sales_order.tax_amount = tax_cents / 100.0
                            result.sales_order.grand_total = (
                                float(result.sales_order.total_price or 0) +
                                float(result.sales_order.shipping_cost or 0) +
                                float(result.sales_order.tax_amount)
                            )
                            print(f"[WEBHOOK] Tax applied: ${result.sales_order.tax_amount:.2f}")

                    db.commit()
                    print(f"[WEBHOOK] Quote {quote.quote_number} -> Order {result.sales_order.order_number} -> PO {result.production_order.code if result.production_order else 'N/A'}")
                else:
                    print(f"[WEBHOOK] Conversion failed for quote {quote.quote_number}: {result.error_message}")

    elif event_type == "payment_intent.payment_failed":
        print(f"[WEBHOOK] Payment failed: {data}")

    return {"status": "ok"}


@router.get("/config")
async def get_stripe_config():
    """
    Get Stripe publishable key for frontend.

    The frontend needs this to initialize Stripe.js
    """
    return {
        "publishable_key": settings.STRIPE_PUBLISHABLE_KEY
    }
