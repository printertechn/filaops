"""
Material management models

Provides the lookup tables for:
- MaterialType: PLA Basic, PLA Matte, PLA Silk, PETG-HF, ABS, ASA, TPU, etc.
- Color: Black, White, Red, etc. with hex codes
- MaterialInventory: Links material type + color to actual product SKU
"""
from app.models.materials.material_type import MaterialType
from app.models.materials.color import Color
from app.models.materials.material_inventory import MaterialInventory

__all__ = ["MaterialType", "Color", "MaterialInventory"]
