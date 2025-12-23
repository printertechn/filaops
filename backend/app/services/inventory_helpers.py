"""
Inventory Helper Functions

Utilities for handling material vs. non-material items in the inventory system.
"""
from sqlalchemy.orm import Session
from app.models.product import Product


def is_material(product: Product) -> bool:
    """
    Check if a product is a material/filament.
    
    Materials are identified by having a material_type_id (they're filament).
    All materials should use grams as their transaction unit.
    
    Args:
        product: Product model instance
    
    Returns:
        True if product is a material (filament), False otherwise
    """
    return product.material_type_id is not None


def get_transaction_unit(product: Product) -> str:
    """
    Get the unit to use for transactions.
    
    - Materials: Always "G" (grams)
    - Other items: Use product.unit (EA, etc.)
    
    Args:
        product: Product model instance
    
    Returns:
        Unit string ("G" for materials, product.unit for others)
    """
    if is_material(product):
        return "G"
    return product.unit or "EA"


def convert_to_transaction_unit(quantity: float, from_unit: str, product: Product) -> float:
    """
    Convert quantity to the transaction unit for a product.
    
    - Materials: Convert to grams (G)
    - Other items: Convert to product.unit if needed, or use as-is
    
    Args:
        quantity: Quantity in from_unit
        from_unit: Source unit (KG, LB, EA, etc.)
        product: Product model instance
    
    Returns:
        Quantity in transaction unit (G for materials, product.unit for others)
    """
    if is_material(product):
        # Materials: Always convert to grams
        from_unit_upper = from_unit.upper()
        if from_unit_upper == "KG":
            return quantity * 1000
        elif from_unit_upper == "LB":
            return quantity * 453.592  # 1 lb = 453.592 g
        elif from_unit_upper == "OZ":
            return quantity * 28.3495  # 1 oz = 28.3495 g
        elif from_unit_upper == "G":
            return quantity
        else:
            # Unknown unit, assume grams
            return quantity
    else:
        # Non-materials: Use product's unit (usually no conversion needed)
        # If conversion is needed, it should be handled by UOM service
        return quantity

