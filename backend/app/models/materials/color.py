"""
Color model

Represents available filament colors with hex codes for display.
Colors are linked to specific material types via MaterialInventory.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class Color(Base):
    """
    Filament color for inventory and quoting
    
    Colors are shared across material types but availability is tracked
    in MaterialInventory (e.g., Black is available in PLA Basic AND PLA Matte,
    but Charcoal is only available in PLA Matte)
    """
    __tablename__ = "colors"

    id = Column(Integer, primary_key=True, index=True)
    
    # Identification
    code = Column(String(30), unique=True, nullable=False, index=True)  # BLK, WHT, CHARCOAL
    name = Column(String(100), nullable=False)  # "Black", "White", "Charcoal"
    display_name = Column(String(100), nullable=True)  # Customer-facing if different
    
    # Visual
    hex_code = Column(String(7), nullable=True)  # #000000
    hex_code_secondary = Column(String(7), nullable=True)  # For multi-color filaments
    
    # Grouping (for filtering large color lists)
    color_family = Column(String(50), nullable=True)  # "Black/Gray", "Red/Pink", "Blue", etc.
    
    # Flags
    is_multi_color = Column(Boolean, default=False)  # Silk Multi filaments
    active = Column(Boolean, default=True)
    
    # Sort order for dropdowns
    sort_order = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    inventory_items = relationship("MaterialInventory", back_populates="color")
    
    def __repr__(self):
        return f"<Color {self.code}: {self.name}>"
    
    @property
    def customer_name(self) -> str:
        """Name to show customers"""
        return self.display_name or self.name
    
    @property
    def swatch_style(self) -> dict:
        """CSS-compatible color info for UI swatches"""
        if self.is_multi_color and self.hex_code_secondary:
            return {
                "type": "gradient",
                "colors": [self.hex_code, self.hex_code_secondary]
            }
        return {
            "type": "solid",
            "color": self.hex_code or "#CCCCCC"
        }
