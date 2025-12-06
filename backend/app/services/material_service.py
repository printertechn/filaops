"""
Material Service

Handles material lookups, availability checks, and pricing for the quote-to-order workflow.
This is the central service for mapping customer material/color selections to actual inventory.
"""
from typing import Optional, List, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.material import MaterialType, Color, MaterialColor, MaterialInventory
from app.models.product import Product
from app.models.inventory import Inventory


class MaterialNotFoundError(Exception):
    """Raised when a material type is not found"""
    pass


class ColorNotFoundError(Exception):
    """Raised when a color is not found"""
    pass


class MaterialColorNotAvailableError(Exception):
    """Raised when a material-color combination is not available"""
    pass


class MaterialNotInStockError(Exception):
    """Raised when a material-color combination is not in stock"""
    pass


def resolve_material_code(db: Session, code: str) -> str:
    """
    Resolve a simple material name to its full database code.

    The portal UI sends simple names like 'PLA', 'PETG', etc.
    The database uses specific codes like 'PLA_BASIC', 'PETG_HF'.

    This function handles the mapping:
    - 'PLA' -> 'PLA_BASIC' (default PLA variant)
    - 'PETG' -> 'PETG_HF' (default PETG variant)
    - 'PLA_BASIC' -> 'PLA_BASIC' (already full code, pass through)

    Args:
        db: Database session
        code: Material code from portal (simple or full)

    Returns:
        Full material type code

    Raises:
        MaterialNotFoundError: If no matching material found
    """
    code_upper = code.upper()

    # First try exact match (already a full code)
    material = db.query(MaterialType).filter(
        MaterialType.code == code_upper,
        MaterialType.active == True
    ).first()

    if material:
        return material.code

    # Try matching by base_material (e.g., 'PLA' matches base_material='PLA')
    material = db.query(MaterialType).filter(
        MaterialType.base_material == code_upper,
        MaterialType.active == True,
        MaterialType.is_customer_visible == True  # Prefer customer-visible variants
    ).order_by(MaterialType.display_order).first()

    if material:
        return material.code

    # Fallback: Try without customer_visible filter
    material = db.query(MaterialType).filter(
        MaterialType.base_material == code_upper,
        MaterialType.active == True
    ).order_by(MaterialType.display_order).first()

    if material:
        return material.code

    raise MaterialNotFoundError(f"Material type not found: {code}")


def get_material_type(db: Session, code: str) -> MaterialType:
    """
    Get a material type by code

    Args:
        db: Database session
        code: Material type code (e.g., 'PLA_BASIC', 'PETG_HF') or simple name ('PLA', 'PETG')

    Returns:
        MaterialType object

    Raises:
        MaterialNotFoundError: If material type not found
    """
    # Resolve simple names to full codes
    resolved_code = resolve_material_code(db, code)

    material = db.query(MaterialType).filter(
        MaterialType.code == resolved_code,
        MaterialType.active == True
    ).first()

    if not material:
        raise MaterialNotFoundError(f"Material type not found: {code}")

    return material


def get_color(db: Session, code: str) -> Color:
    """
    Get a color by code
    
    Args:
        db: Database session
        code: Color code (e.g., 'BLK', 'WHT', 'CHARCOAL')
    
    Returns:
        Color object
    
    Raises:
        ColorNotFoundError: If color not found
    """
    color = db.query(Color).filter(
        Color.code == code,
        Color.active == True
    ).first()
    
    if not color:
        raise ColorNotFoundError(f"Color not found: {code}")
    
    return color


def get_available_material_types(db: Session, customer_visible_only: bool = True) -> List[MaterialType]:
    """
    Get all available material types for dropdown
    
    Args:
        db: Database session
        customer_visible_only: If True, only return customer-visible materials
    
    Returns:
        List of MaterialType objects ordered by display_order
    """
    query = db.query(MaterialType).filter(MaterialType.active == True)
    
    if customer_visible_only:
        query = query.filter(MaterialType.is_customer_visible == True)
    
    return query.order_by(MaterialType.display_order).all()


def get_available_colors_for_material(
    db: Session, 
    material_type_code: str,
    in_stock_only: bool = False,
    customer_visible_only: bool = True
) -> List[Color]:
    """
    Get available colors for a specific material type
    
    This is used to populate the color dropdown after material is selected.
    
    Args:
        db: Database session
        material_type_code: Material type code (e.g., 'PLA_BASIC')
        in_stock_only: If True, only return colors that are in stock
        customer_visible_only: If True, only return customer-visible colors
    
    Returns:
        List of Color objects ordered by display_order
    """
    # Get material type
    material = get_material_type(db, material_type_code)
    
    # Build query through junction table
    query = db.query(Color).join(
        MaterialColor,
        and_(
            MaterialColor.color_id == Color.id,
            MaterialColor.material_type_id == material.id,
            MaterialColor.active == True
        )
    ).filter(
        Color.active == True
    )
    
    if customer_visible_only:
        query = query.filter(
            Color.is_customer_visible == True,
            MaterialColor.is_customer_visible == True
        )
    
    if in_stock_only:
        # Join to inventory to check stock
        query = query.join(
            MaterialInventory,
            and_(
                MaterialInventory.material_type_id == material.id,
                MaterialInventory.color_id == Color.id,
                MaterialInventory.in_stock == True,
                MaterialInventory.active == True
            )
        )
    
    return query.order_by(Color.display_order, Color.name).all()


def get_material_inventory(
    db: Session,
    material_type_code: str,
    color_code: str
) -> MaterialInventory:
    """
    Get the material inventory record for a material-color combination
    
    Args:
        db: Database session
        material_type_code: Material type code (e.g., 'PLA_BASIC')
        color_code: Color code (e.g., 'BLK')
    
    Returns:
        MaterialInventory object
    
    Raises:
        MaterialColorNotAvailableError: If combination doesn't exist
    """
    material = get_material_type(db, material_type_code)
    color = get_color(db, color_code)
    
    inventory = db.query(MaterialInventory).filter(
        MaterialInventory.material_type_id == material.id,
        MaterialInventory.color_id == color.id,
        MaterialInventory.active == True
    ).first()
    
    if not inventory:
        raise MaterialColorNotAvailableError(
            f"Material-color combination not available: {material_type_code} + {color_code}"
        )
    
    return inventory


def get_material_product_for_bom(
    db: Session,
    material_type_code: str,
    color_code: str,
    require_in_stock: bool = False
) -> Tuple[Product, MaterialInventory]:
    """
    Get the Product record for BOM creation based on material and color
    
    This is the main function used by the BOM service to find the right material product.
    
    IMPORTANT: This function also ensures an Inventory record exists for the product,
    synced with MaterialInventory.quantity_kg. This is required for BOM explosion
    to find available stock.
    
    Args:
        db: Database session
        material_type_code: Material type code (e.g., 'PLA_BASIC')
        color_code: Color code (e.g., 'BLK')
        require_in_stock: If True, raises error if not in stock
    
    Returns:
        Tuple of (Product, MaterialInventory)
    
    Raises:
        MaterialColorNotAvailableError: If combination doesn't exist
        MaterialNotInStockError: If require_in_stock and not in stock
    """
    inventory = get_material_inventory(db, material_type_code, color_code)
    
    if require_in_stock and not inventory.in_stock:
        raise MaterialNotInStockError(
            f"Material not in stock: {material_type_code} + {color_code}"
        )
    
    # Get or create the product
    product = None
    if inventory.product_id:
        product = db.query(Product).get(inventory.product_id)
    
    if not product:
        # Try to find by SKU
        product = db.query(Product).filter(
            Product.sku == inventory.sku,
            Product.active == True
        ).first()
    
    if not product:
        # Create the product if it doesn't exist
        material = get_material_type(db, material_type_code)
        color = get_color(db, color_code)
        
        product = Product(
            sku=inventory.sku,
            name=f"{material.name} - {color.name}",
            description=f"{material.name} filament in {color.name}",
            category="Raw Materials",
            unit="kg",
            cost=inventory.cost_per_kg or material.base_price_per_kg,
            selling_price=material.base_price_per_kg,
            weight=Decimal("1.0"),  # 1kg per unit
            is_raw_material=True,
            has_bom=False,
            active=True
        )
        db.add(product)
        db.flush()  # Get product.id
    
    # Link product to MaterialInventory if not already linked
    if inventory.product_id != product.id:
        inventory.product_id = product.id
    
    # =========================================================================
    # BUG FIX #2: Ensure Inventory record exists for BOM explosion
    # 
    # The BOM explosion in start_production() queries the Inventory table,
    # NOT MaterialInventory. Without an Inventory record, materials show as
    # "insufficient" even when MaterialInventory has stock.
    # =========================================================================
    inv_record = db.query(Inventory).filter(
        Inventory.product_id == product.id
    ).first()
    
    if not inv_record:
        # Create Inventory record, synced with MaterialInventory
        inv_record = Inventory(
            product_id=product.id,
            location_id=1,  # Default raw materials location (TODO: make configurable)
            on_hand_quantity=inventory.quantity_kg or Decimal("0"),
            allocated_quantity=Decimal("0"),
        )
        db.add(inv_record)
    else:
        # Sync quantities: MaterialInventory is source of truth for raw materials
        # Only sync if Inventory is lower (don't overwrite if production consumed)
        # Actually, just ensure they match - MaterialInventory is the master
        if inv_record.on_hand_quantity != inventory.quantity_kg:
            # Log discrepancy but sync from MaterialInventory
            inv_record.on_hand_quantity = inventory.quantity_kg or Decimal("0")
    
    db.commit()
    
    return product, inventory


def get_material_cost_per_kg(
    db: Session,
    material_type_code: str,
    color_code: Optional[str] = None
) -> Decimal:
    """
    Get the cost per kg for a material
    
    If color is specified, returns the specific inventory cost.
    Otherwise returns the base material type cost.
    
    Args:
        db: Database session
        material_type_code: Material type code
        color_code: Optional color code
    
    Returns:
        Cost per kg as Decimal
    """
    material = get_material_type(db, material_type_code)
    
    if color_code:
        try:
            inventory = get_material_inventory(db, material_type_code, color_code)
            if inventory.cost_per_kg:
                return inventory.cost_per_kg
        except MaterialColorNotAvailableError:
            pass
    
    return material.base_price_per_kg


def get_material_density(db: Session, material_type_code: str) -> Decimal:
    """
    Get the density for a material type
    
    Args:
        db: Database session
        material_type_code: Material type code
    
    Returns:
        Density in g/cm³ as Decimal
    """
    material = get_material_type(db, material_type_code)
    return material.density


def get_material_price_multiplier(db: Session, material_type_code: str) -> Decimal:
    """
    Get the price multiplier for a material type (relative to PLA)
    
    Args:
        db: Database session
        material_type_code: Material type code
    
    Returns:
        Price multiplier as Decimal
    """
    material = get_material_type(db, material_type_code)
    return material.price_multiplier


def check_material_availability(
    db: Session,
    material_type_code: str,
    color_code: str,
    quantity_kg: Decimal
) -> Tuple[bool, str]:
    """
    Check if a material-color combination is available in sufficient quantity
    
    Args:
        db: Database session
        material_type_code: Material type code
        color_code: Color code
        quantity_kg: Required quantity in kg
    
    Returns:
        Tuple of (is_available: bool, message: str)
    """
    try:
        inventory = get_material_inventory(db, material_type_code, color_code)
    except MaterialColorNotAvailableError:
        return False, f"Material-color combination not available: {material_type_code} + {color_code}"
    
    if not inventory.in_stock:
        return False, f"Material is out of stock: {material_type_code} + {color_code}"
    
    if inventory.quantity_kg < quantity_kg:
        return False, (
            f"Insufficient stock: have {inventory.quantity_kg}kg, "
            f"need {quantity_kg}kg of {material_type_code} + {color_code}"
        )
    
    return True, "Available"


def get_portal_material_options(db: Session) -> List[dict]:
    """
    Get material options formatted for the portal frontend

    Returns a list of material types with their available colors.
    Includes ALL colors with in_stock status for lead time calculation.

    Returns:
        List of dicts: [
            {
                "code": "PLA_BASIC",
                "name": "PLA Basic",
                "description": "...",
                "price_multiplier": 1.0,
                "colors": [
                    {"code": "BLK", "name": "Black", "hex": "#000000", "in_stock": true},
                    {"code": "WHT", "name": "White", "hex": "#FFFFFF", "in_stock": false},
                    ...
                ]
            },
            ...
        ]
    """
    materials = get_available_material_types(db, customer_visible_only=True)

    result = []
    for material in materials:
        # Get ALL customer-visible colors (not just in-stock)
        colors = get_available_colors_for_material(
            db,
            material.code,
            in_stock_only=False,  # Show all colors
            customer_visible_only=True
        )

        if not colors:
            continue  # Skip materials with no colors available

        # Build color list with stock info
        color_list = []
        for c in colors:
            # Check inventory for this color
            inventory = db.query(MaterialInventory).filter(
                MaterialInventory.material_type_id == material.id,
                MaterialInventory.color_id == c.id,
                MaterialInventory.active == True
            ).first()

            # Get stock status and quantity
            is_in_stock = inventory.in_stock if inventory else False
            quantity_kg = float(inventory.quantity_kg) if inventory and inventory.quantity_kg else 0.0

            color_list.append({
                "code": c.code,
                "name": c.name,
                "hex": c.hex_code,
                "hex_secondary": c.hex_code_secondary,
                "in_stock": is_in_stock,
                "quantity_kg": quantity_kg,  # Available stock in kg
            })

        result.append({
            "code": material.code,
            "name": material.name,
            "description": material.description,
            "base_material": material.base_material,
            "price_multiplier": float(material.price_multiplier),
            "strength_rating": material.strength_rating,
            "requires_enclosure": material.requires_enclosure,
            "colors": color_list
        })

    return result
