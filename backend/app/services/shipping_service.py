"""
EasyPost shipping integration service

Handles rate calculation, label generation, and tracking
"""
import easypost
from typing import List, Optional, Dict, Any
from decimal import Decimal
from dataclasses import dataclass

from app.core.config import settings

# Initialize EasyPost client
client = easypost.EasyPostClient(api_key=settings.EASYPOST_API_KEY)


@dataclass
class ShippingRate:
    """Shipping rate option"""
    carrier: str
    service: str
    rate: Decimal
    est_delivery_days: Optional[int]
    rate_id: str  # EasyPost rate ID for purchasing


@dataclass
class ShipmentResult:
    """Result of creating/buying a shipment"""
    success: bool
    tracking_number: Optional[str] = None
    label_url: Optional[str] = None
    shipment_id: Optional[str] = None
    carrier: Optional[str] = None
    service: Optional[str] = None
    rate: Optional[Decimal] = None
    error: Optional[str] = None


class ShippingService:
    """Service for EasyPost shipping operations"""

    def __init__(self):
        self.client = client

    def get_from_address(self) -> Dict[str, str]:
        """Get the ship-from address from config"""
        return {
            "name": settings.SHIP_FROM_NAME,
            "street1": settings.SHIP_FROM_STREET1,
            "city": settings.SHIP_FROM_CITY,
            "state": settings.SHIP_FROM_STATE,
            "zip": settings.SHIP_FROM_ZIP,
            "country": settings.SHIP_FROM_COUNTRY,
            "phone": settings.SHIP_FROM_PHONE,
        }

    def get_shipping_rates(
        self,
        to_name: str,
        to_street1: str,
        to_city: str,
        to_state: str,
        to_zip: str,
        to_country: str = "US",
        to_street2: Optional[str] = None,
        weight_oz: float = 16.0,  # Default 1 lb
        length: float = 10.0,
        width: float = 8.0,
        height: float = 4.0,
    ) -> List[ShippingRate]:
        """
        Get shipping rates for a destination.

        Args:
            to_*: Destination address fields
            weight_oz: Package weight in ounces
            length, width, height: Package dimensions in inches

        Returns:
            List of available shipping rates sorted by price
        """
        try:
            # Create shipment to get rates
            shipment = self.client.shipment.create(
                from_address=self.get_from_address(),
                to_address={
                    "name": to_name,
                    "street1": to_street1,
                    "street2": to_street2 or "",
                    "city": to_city,
                    "state": to_state,
                    "zip": to_zip,
                    "country": to_country,
                },
                parcel={
                    "length": length,
                    "width": width,
                    "height": height,
                    "weight": weight_oz,
                },
            )

            # Parse rates
            rates = []
            for rate in shipment.rates:
                # Parse delivery days
                est_days = None
                if rate.delivery_days:
                    est_days = int(rate.delivery_days)

                rates.append(ShippingRate(
                    carrier=rate.carrier,
                    service=rate.service,
                    rate=Decimal(rate.rate),
                    est_delivery_days=est_days,
                    rate_id=rate.id,
                ))

            # Sort by price
            rates.sort(key=lambda r: r.rate)

            # Return rates with shipment ID (needed for buy_label)
            return rates, shipment.id

        except easypost.errors.api.ApiError as e:
            print(f"[EASYPOST] Rate error: {e}")
            return [], None

    def buy_label(
        self,
        rate_id: str,
        shipment_id: str,
    ) -> ShipmentResult:
        """
        Purchase a shipping label for a rate.

        Args:
            rate_id: The EasyPost rate ID to purchase
            shipment_id: The shipment ID from get_shipping_rates

        Returns:
            ShipmentResult with tracking number and label URL
        """
        try:
            if not shipment_id:
                return ShipmentResult(success=False, error="No shipment ID provided")

            # Retrieve and buy - rate must be passed as dict with id
            shipment = self.client.shipment.retrieve(shipment_id)
            bought = self.client.shipment.buy(shipment_id, rate={"id": rate_id})

            return ShipmentResult(
                success=True,
                tracking_number=bought.tracking_code,
                label_url=bought.postage_label.label_url if bought.postage_label else None,
                shipment_id=bought.id,
                carrier=bought.selected_rate.carrier if bought.selected_rate else None,
                service=bought.selected_rate.service if bought.selected_rate else None,
                rate=Decimal(bought.selected_rate.rate) if bought.selected_rate else None,
            )

        except easypost.errors.api.ApiError as e:
            print(f"[EASYPOST] Buy error: {e}")
            return ShipmentResult(success=False, error=str(e))

    def create_and_buy_cheapest(
        self,
        to_name: str,
        to_street1: str,
        to_city: str,
        to_state: str,
        to_zip: str,
        to_country: str = "US",
        to_street2: Optional[str] = None,
        weight_oz: float = 16.0,
        length: float = 10.0,
        width: float = 8.0,
        height: float = 4.0,
        carrier_filter: Optional[List[str]] = None,
    ) -> ShipmentResult:
        """
        Create a shipment and buy the cheapest rate.

        Args:
            to_*: Destination address fields
            weight_oz: Package weight in ounces
            dimensions: Package size in inches
            carrier_filter: Optional list of carriers to consider (e.g., ["USPS", "UPS"])

        Returns:
            ShipmentResult with tracking and label
        """
        try:
            shipment = self.client.shipment.create(
                from_address=self.get_from_address(),
                to_address={
                    "name": to_name,
                    "street1": to_street1,
                    "street2": to_street2 or "",
                    "city": to_city,
                    "state": to_state,
                    "zip": to_zip,
                    "country": to_country,
                },
                parcel={
                    "length": length,
                    "width": width,
                    "height": height,
                    "weight": weight_oz,
                },
            )

            # Filter rates if carrier specified
            rates = shipment.rates
            if carrier_filter:
                rates = [r for r in rates if r.carrier in carrier_filter]

            if not rates:
                return ShipmentResult(success=False, error="No rates available")

            # Find cheapest
            cheapest = min(rates, key=lambda r: float(r.rate))

            # Buy it
            bought = self.client.shipment.buy(shipment.id, rate=cheapest.id)

            return ShipmentResult(
                success=True,
                tracking_number=bought.tracking_code,
                label_url=bought.postage_label.label_url if bought.postage_label else None,
                shipment_id=bought.id,
                carrier=bought.selected_rate.carrier if bought.selected_rate else None,
                service=bought.selected_rate.service if bought.selected_rate else None,
                rate=Decimal(bought.selected_rate.rate) if bought.selected_rate else None,
            )

        except easypost.errors.api.ApiError as e:
            print(f"[EASYPOST] Create/buy error: {e}")
            return ShipmentResult(success=False, error=str(e))

    def get_tracking(self, tracking_number: str, carrier: str) -> Dict[str, Any]:
        """
        Get tracking info for a shipment.

        Args:
            tracking_number: The tracking number
            carrier: Carrier code (USPS, UPS, FedEx)

        Returns:
            Tracking details dict
        """
        try:
            tracker = self.client.tracker.create(
                tracking_code=tracking_number,
                carrier=carrier,
            )

            return {
                "status": tracker.status,
                "status_detail": tracker.status_detail,
                "est_delivery_date": tracker.est_delivery_date,
                "tracking_details": [
                    {
                        "datetime": td.datetime,
                        "message": td.message,
                        "status": td.status,
                        "city": td.tracking_location.city if td.tracking_location else None,
                        "state": td.tracking_location.state if td.tracking_location else None,
                    }
                    for td in (tracker.tracking_details or [])
                ],
            }

        except easypost.errors.api.ApiError as e:
            print(f"[EASYPOST] Tracking error: {e}")
            return {"error": str(e)}

    def estimate_weight_oz(self, material_grams: float, quantity: int = 1) -> float:
        """
        Estimate package weight based on material weight.

        Adds packaging overhead (~50g for box + padding)

        Args:
            material_grams: Weight of printed parts in grams
            quantity: Number of units

        Returns:
            Estimated total weight in ounces
        """
        # Material weight + packaging (50g base + 10g per item)
        total_grams = material_grams * quantity + 50 + (10 * quantity)

        # Convert to ounces (1 oz = 28.35g)
        return total_grams / 28.35

    def estimate_box_size(self, dimensions_mm: tuple, quantity: int = 1) -> tuple:
        """
        Estimate box size based on part dimensions.

        Args:
            dimensions_mm: (x, y, z) in millimeters
            quantity: Number of units

        Returns:
            (length, width, height) in inches with padding
        """
        x_mm, y_mm, z_mm = dimensions_mm

        # Convert to inches and add padding (1 inch each side)
        length = (x_mm / 25.4) + 2
        width = (y_mm / 25.4) + 2
        height = (z_mm / 25.4) * quantity + 2  # Stack height for multiple

        # Minimum box size
        length = max(length, 6)
        width = max(width, 4)
        height = max(height, 2)

        return (round(length, 1), round(width, 1), round(height, 1))


# Singleton instance
shipping_service = ShippingService()
