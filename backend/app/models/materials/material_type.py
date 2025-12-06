"""
MaterialType model

Represents filament material categories like PLA Basic, PLA Matte, PLA Silk, PETG-HF, etc.
Each type has specific properties (density, print settings) and available colors.
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class MaterialType(Base):
    """
    Material type/category for quoting and inventory
    
    Examples: PLA Basic, PLA Matte, PLA Silk, PETG-HF, ABS, ASA, TPU 68D, TPU 95A
    """
    __tablename__ = "material_types"

    id = Column(Integer, primary_key=True, index=True)
    
    # Identification
    code = Column(String(50), unique=True, nullable=False, index=True)  # PLA_BASIC, PLA_MATTE, PETG_HF
    name = Column(String(100), nullable=False)  # "PLA Basic", "PLA Matte"
    display_name = Column(String(100), nullable=True)  # Customer-facing name if different
    
    # Base material (for grouping in quote engine)
    base_material = Column(String(20), nullable=False, index=True)  # PLA, PETG, ABS, ASA, TPU
    
    # Physical properties (from Bambu specs)
    density = Column(Numeric(6, 3), nullable=False)  # g/cm³ - e.g., 1.24 for PLA
    
    # Print settings reference (maps to BambuStudio profile)
    bambu_profile_name = Column(String(100), nullable=True)  # "Bambu Lab PLA Basic"
    
    # Pricing
    base_price_per_kg = Column(Numeric(10, 2), nullable=False)  # Base cost from supplier
    price_multiplier = Column(Numeric(4, 2), default=1.0)  # For quote calculation vs PLA baseline
    
    # Volumetric flow limit (affects print speed/time calculation)
    max_volumetric_speed = Column(Numeric(6, 2), nullable=True)  # mm³/s
    
    # Characteristics (for customer display)
    description = Column(Text, nullable=True)
    finish_type = Column(String(50), nullable=True)  # matte, glossy, silk, standard
    strength_rating = Column(String(20), nullable=True)  # standard, high, flexible
    
    # Flags
    requires_enclosure = Column(Boolean, default=False)  # ABS, ASA need enclosure
    requires_hardened_nozzle = Column(Boolean, default=False)  # CF materials
    is_flexible = Column(Boolean, default=False)  # TPU
    active = Column(Boolean, default=True)
    available_for_quoting = Column(Boolean, default=True)  # Show in customer dropdown
    
    # Sort order for dropdowns
    sort_order = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    inventory_items = relationship("MaterialInventory", back_populates="material_type")
    
    def __repr__(self):
        return f"<MaterialType {self.code}: {self.name}>"
    
    @property
    def customer_name(self) -> str:
        """Name to show customers"""
        return self.display_name or self.name
