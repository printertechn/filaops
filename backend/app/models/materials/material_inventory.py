"""
MaterialInventory model

Links MaterialType + Color to actual Product SKU in inventory.
This is the key table that enables:
1. Filtering colors by material type (only show colors you stock for that type)
2. Looking up the correct product SKU when creating BOMs
3. Tracking real inventory levels and costs
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class MaterialInventory(Base):
    """
    Inventory record for a specific material type + color combination
    
    This table answers: "Do we have Black PLA Matte in stock?"
    And provides: "The SKU is MAT-00018 and we have 2.5kg at $19.99/kg"
    """
    __tablename__ = "material_inventory"
    
    # Ensure each material_type + color combination is unique
    __table_args__ = (
        UniqueConstraint('material_type_id', 'color_id', name='uq_material_color'),
    )

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    material_type_id = Column(Integer, ForeignKey("material_types.id"), nullable=False, index=True)
    color_id = Column(Integer, ForeignKey("colors.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)  # Link to products table
    
    # SKU (denormalized for quick lookup, should match product.sku)
    sku = Column(String(50), nullable=False, index=True)
    
    # Inventory tracking
    quantity_kg = Column(Numeric(10, 3), default=0)  # Current stock in kg
    quantity_spools = Column(Integer, default=0)  # Approximate spool count
    reorder_point_kg = Column(Numeric(10, 3), default=1.0)  # Alert when below this
    
    # Costing
    cost_per_kg = Column(Numeric(10, 2), nullable=True)  # Actual purchase cost
    last_purchase_cost = Column(Numeric(10, 2), nullable=True)  # Most recent purchase
    last_purchase_date = Column(DateTime, nullable=True)
    
    # Supplier info
    primary_vendor = Column(String(100), nullable=True)
    vendor_sku = Column(String(100), nullable=True)  # Vendor's part number
    
    # Availability
    in_stock = Column(Boolean, default=True)  # Quick flag for "can we quote this?"
    available_for_quoting = Column(Boolean, default=True)  # Show in customer dropdown
    lead_time_days = Column(Integer, default=3)  # If out of stock, how long to get more
    
    # Location
    storage_location = Column(String(100), nullable=True)  # "Shelf A2", "Dry Box 1"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_inventory_count = Column(DateTime, nullable=True)
    
    # Relationships
    material_type = relationship("MaterialType", back_populates="inventory_items")
    color = relationship("Color", back_populates="inventory_items")
    product = relationship("Product")  # The actual product record
    
    def __repr__(self):
        return f"<MaterialInventory {self.sku}: {self.material_type.name if self.material_type else '?'} - {self.color.name if self.color else '?'}>"
    
    @property
    def is_low_stock(self) -> bool:
        """Check if below reorder point"""
        return self.quantity_kg < self.reorder_point_kg if self.quantity_kg else True
    
    @property
    def display_name(self) -> str:
        """Friendly name for display"""
        mat_name = self.material_type.name if self.material_type else "Unknown"
        color_name = self.color.name if self.color else "Unknown"
        return f"{mat_name} - {color_name}"
