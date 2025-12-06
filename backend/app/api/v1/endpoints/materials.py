"""
Material API Endpoints

Provides material type and color options for the quote portal.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.services.material_service import (
    get_portal_material_options,
    get_available_material_types,
    get_available_colors_for_material,
    MaterialNotFoundError,
)


router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class ColorOption(BaseModel):
    """Color option for dropdown"""
    code: str
    name: str
    hex: str | None
    hex_secondary: str | None = None
    in_stock: bool = True  # Whether this color is marked in stock
    quantity_kg: float = 0.0  # Available quantity in kg for lead time calculation


class MaterialTypeOption(BaseModel):
    """Material type with available colors"""
    code: str
    name: str
    description: str | None
    base_material: str
    price_multiplier: float
    strength_rating: int | None
    requires_enclosure: bool
    colors: List[ColorOption]


class MaterialOptionsResponse(BaseModel):
    """Response containing all material options for portal"""
    materials: List[MaterialTypeOption]


class SimpleColorOption(BaseModel):
    """Simple color option"""
    code: str
    name: str
    hex: str | None


class ColorsResponse(BaseModel):
    """Response containing colors for a material type"""
    material_type: str
    colors: List[SimpleColorOption]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/options", response_model=MaterialOptionsResponse)
def get_material_options(
    in_stock_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get all material options for the quote portal.
    
    Returns a hierarchical structure:
    - Material types (first dropdown)
    - Colors available for each material type (second dropdown)
    
    Only returns materials that are:
    - Active
    - Customer visible
    - Have at least one color in stock (if in_stock_only=True)
    """
    try:
        materials = get_portal_material_options(db)
        
        # Filter based on in_stock_only
        if in_stock_only:
            # Already filtered by get_portal_material_options
            pass
        
        return MaterialOptionsResponse(
            materials=[
                MaterialTypeOption(
                    code=m["code"],
                    name=m["name"],
                    description=m.get("description"),
                    base_material=m["base_material"],
                    price_multiplier=m["price_multiplier"],
                    strength_rating=m.get("strength_rating"),
                    requires_enclosure=m.get("requires_enclosure", False),
                    colors=[
                        ColorOption(
                            code=c["code"],
                            name=c["name"],
                            hex=c.get("hex"),
                            hex_secondary=c.get("hex_secondary"),
                            in_stock=c.get("in_stock", True),
                            quantity_kg=c.get("quantity_kg", 0.0),
                        )
                        for c in m["colors"]
                    ]
                )
                for m in materials
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
def list_material_types(
    customer_visible_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get list of material types (for first dropdown).
    
    Returns just the material types without colors.
    """
    try:
        materials = get_available_material_types(db, customer_visible_only=customer_visible_only)
        
        return {
            "materials": [
                {
                    "code": m.code,
                    "name": m.name,
                    "base_material": m.base_material,
                    "description": m.description,
                    "price_multiplier": float(m.price_multiplier),
                    "strength_rating": m.strength_rating,
                    "requires_enclosure": m.requires_enclosure,
                }
                for m in materials
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types/{material_type_code}/colors", response_model=ColorsResponse)
def list_colors_for_material(
    material_type_code: str,
    in_stock_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get available colors for a specific material type (for second dropdown).
    
    Called when user selects a material type to populate the color dropdown.
    """
    try:
        colors = get_available_colors_for_material(
            db,
            material_type_code=material_type_code,
            in_stock_only=in_stock_only,
            customer_visible_only=True
        )
        
        return ColorsResponse(
            material_type=material_type_code,
            colors=[
                SimpleColorOption(
                    code=c.code,
                    name=c.name,
                    hex=c.hex_code,
                )
                for c in colors
            ]
        )
    except MaterialNotFoundError:
        raise HTTPException(
            status_code=404, 
            detail=f"Material type not found: {material_type_code}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pricing/{material_type_code}")
def get_material_pricing(
    material_type_code: str,
    db: Session = Depends(get_db)
):
    """
    Get pricing information for a material type.
    
    Used by the quote engine to calculate prices.
    """
    try:
        materials = get_available_material_types(db, customer_visible_only=False)
        material = next((m for m in materials if m.code == material_type_code), None)
        
        if not material:
            raise HTTPException(
                status_code=404,
                detail=f"Material type not found: {material_type_code}"
            )
        
        return {
            "code": material.code,
            "name": material.name,
            "base_material": material.base_material,
            "density": float(material.density),
            "base_price_per_kg": float(material.base_price_per_kg),
            "price_multiplier": float(material.price_multiplier),
            "volumetric_flow_limit": float(material.volumetric_flow_limit) if material.volumetric_flow_limit else None,
            "nozzle_temp_min": material.nozzle_temp_min,
            "nozzle_temp_max": material.nozzle_temp_max,
            "bed_temp_min": material.bed_temp_min,
            "bed_temp_max": material.bed_temp_max,
            "requires_enclosure": material.requires_enclosure,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
