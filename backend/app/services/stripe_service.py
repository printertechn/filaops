"""
Stripe payment integration service

Handles checkout sessions, webhooks, and payment verification
"""
import stripe
from decimal import Decimal
from typing import Optional
from datetime import datetime

from app.core.config import settings

# Initialize Stripe with secret key
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Service for Stripe payment operations"""

    @staticmethod
    def get_or_create_customer(
        email: str,
        name: Optional[str] = None,
        shipping_address: Optional[dict] = None,
    ) -> stripe.Customer:
        """
        Get or create a Stripe Customer.

        Args:
            email: Customer email (used as lookup key)
            name: Customer name
            shipping_address: Dict with address fields
                {line1, line2, city, state, postal_code, country}

        Returns:
            Stripe Customer object
        """
        # Check if customer already exists
        existing = stripe.Customer.list(email=email, limit=1)
        if existing.data:
            customer = existing.data[0]
            # Update shipping address if provided
            if shipping_address:
                stripe.Customer.modify(
                    customer.id,
                    shipping={
                        "name": name or email,
                        "address": {
                            "line1": shipping_address.get("line1", ""),
                            "line2": shipping_address.get("line2") or "",
                            "city": shipping_address.get("city", ""),
                            "state": shipping_address.get("state", ""),
                            "postal_code": shipping_address.get("postal_code", ""),
                            "country": shipping_address.get("country", "US"),
                        }
                    }
                )
            return customer

        # Create new customer
        customer_params = {"email": email}
        if name:
            customer_params["name"] = name

        if shipping_address:
            customer_params["shipping"] = {
                "name": name or email,
                "address": {
                    "line1": shipping_address.get("line1", ""),
                    "line2": shipping_address.get("line2") or "",
                    "city": shipping_address.get("city", ""),
                    "state": shipping_address.get("state", ""),
                    "postal_code": shipping_address.get("postal_code", ""),
                    "country": shipping_address.get("country", "US"),
                }
            }

        return stripe.Customer.create(**customer_params)

    @staticmethod
    def create_checkout_session(
        quote_id: int,
        quote_number: str,
        amount_dollars: Decimal,
        customer_email: Optional[str] = None,
        customer_id: Optional[str] = None,
        product_name: Optional[str] = None,
        material: Optional[str] = None,
        quantity: int = 1,
        shipping_cost: Optional[float] = None,
    ) -> stripe.checkout.Session:
        """
        Create a Stripe Checkout session for a quote.

        Args:
            quote_id: Internal quote ID (for metadata)
            quote_number: Quote number for display (Q-2025-001)
            amount_dollars: Total amount in dollars (product only, excluding shipping)
            customer_email: Pre-fill customer email (if no customer_id)
            customer_id: Stripe Customer ID (preferred - enables tax from saved address)
            product_name: Product/file name for line item
            material: Material type for description
            quantity: Number of units
            shipping_cost: Shipping cost in dollars (separate line item)

        Returns:
            Stripe Checkout Session object with URL to redirect customer

        Note:
            Stripe Tax must be enabled in your Stripe Dashboard for automatic
            tax calculation to work. Configure your tax registrations there.
            For accurate tax calculation, use get_or_create_customer() first
            to set up the customer with their shipping address.
        """
        # Calculate product amount (total minus shipping if included)
        if shipping_cost:
            product_amount = float(amount_dollars) - float(shipping_cost)
        else:
            product_amount = float(amount_dollars)

        # Convert to cents for Stripe
        product_cents = int(product_amount * 100)

        # Build product description
        description = f"3D Print Quote {quote_number}"
        if material:
            description += f" - {material}"
        if quantity > 1:
            description += f" (x{quantity})"

        # Create line items
        line_items = [
            {
                "price_data": {
                    "currency": "usd",
                    "unit_amount": product_cents,
                    "product_data": {
                        "name": product_name or f"Quote {quote_number}",
                        "description": description,
                    },
                },
                "quantity": 1,  # Total price already includes quantity
            }
        ]

        # Add shipping as separate line item
        if shipping_cost and shipping_cost > 0:
            shipping_cents = int(float(shipping_cost) * 100)
            line_items.append({
                "price_data": {
                    "currency": "usd",
                    "unit_amount": shipping_cents,
                    "product_data": {
                        "name": "Shipping",
                        "description": "Standard shipping",
                    },
                },
                "quantity": 1,
            })

        # Build session parameters
        session_params = {
            "payment_method_types": ["card"],
            "line_items": line_items,
            "mode": "payment",
            "success_url": f"{settings.FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}&quote_id={quote_id}",
            "cancel_url": f"{settings.FRONTEND_URL}/payment/cancelled?quote_id={quote_id}",
            "metadata": {
                "quote_id": str(quote_id),
                "quote_number": quote_number,
            },
            "payment_intent_data": {
                "metadata": {
                    "quote_id": str(quote_id),
                    "quote_number": quote_number,
                }
            },
            # Enable automatic tax calculation (requires Stripe Tax setup in Dashboard)
            "automatic_tax": {"enabled": True},
        }

        # Use customer ID if provided (preferred for tax calculation)
        # Otherwise fall back to customer email
        if customer_id:
            session_params["customer"] = customer_id
        elif customer_email:
            session_params["customer_email"] = customer_email

        # Create the session
        session = stripe.checkout.Session.create(**session_params)

        return session

    @staticmethod
    def retrieve_session(session_id: str) -> stripe.checkout.Session:
        """
        Retrieve a checkout session by ID.

        Args:
            session_id: Stripe checkout session ID

        Returns:
            Checkout Session object
        """
        return stripe.checkout.Session.retrieve(session_id)

    @staticmethod
    def verify_webhook_signature(payload: bytes, sig_header: str) -> dict:
        """
        Verify and parse a Stripe webhook event.

        Args:
            payload: Raw request body
            sig_header: Stripe-Signature header value

        Returns:
            Parsed event object

        Raises:
            ValueError: If signature verification fails
        """
        if not settings.STRIPE_WEBHOOK_SECRET:
            # In development without webhook secret, parse without verification
            import json
            return json.loads(payload)

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except stripe.error.SignatureVerificationError as e:
            raise ValueError(f"Invalid webhook signature: {e}")

    @staticmethod
    def get_payment_intent(payment_intent_id: str) -> stripe.PaymentIntent:
        """
        Retrieve a payment intent by ID.

        Args:
            payment_intent_id: Stripe PaymentIntent ID

        Returns:
            PaymentIntent object
        """
        return stripe.PaymentIntent.retrieve(payment_intent_id)


# Singleton instance
stripe_service = StripeService()
