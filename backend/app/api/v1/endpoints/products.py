"""
Products API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.db.session import get_db
from app.models.product import Product

router = APIRouter()
logger = logging.getLogger(__name__)

class ProductResponse(BaseModel):
    """Product response"""
    id: int
    sku: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    unit: str
    cost: Optional[float] = None
    selling_price: Optional[float] = None
    weight: Optional[float] = None
    is_raw_material: bool
    has_bom: bool
    active: bool
    woocommerce_product_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ProductListResponse(BaseModel):
    """Product list response"""
    total: int
    items: List[ProductResponse]

@router.get("", response_model=ProductListResponse)
async def list_products(
    category: Optional[str] = None,
    active_only: bool = True,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List products with optional filtering

    - **category**: Filter by category (e.g., 'Finished Goods', 'Raw Materials')
    - **active_only**: Only show active products (default: True)
    - **search**: Search by SKU or name
    - **limit**: Max results (default: 50)
    - **offset**: Pagination offset (default: 0)
    """
    try:
        # Build query
        query = db.query(Product)

        # Apply filters
        if active_only:
            query = query.filter(Product.active == True)

        if category:
            query = query.filter(Product.category == category)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Product.sku.like(search_pattern)) |
                (Product.name.like(search_pattern))
            )

        # Get total count
        total = query.count()

        # Get paginated results
        products = query.order_by(Product.id).offset(offset).limit(limit).all()

        return ProductListResponse(
            total=total,
            items=[ProductResponse.from_orm(p) for p in products]
        )

    except Exception as e:
        logger.error(f"Failed to list products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id}", response_model=ProductResponse)
async def get_product(
    id: int,
    db: Session = Depends(get_db)
):
    """Get a specific product by ID"""
    try:
        product = db.query(Product).filter(Product.id == id).first()

        if not product:
            raise HTTPException(status_code=404, detail=f"Product {id} not found")

        return ProductResponse.from_orm(product)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get product: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sku/{sku}", response_model=ProductResponse)
async def get_product_by_sku(
    sku: str,
    db: Session = Depends(get_db)
):
    """Get a specific product by SKU"""
    try:
        product = db.query(Product).filter(Product.sku == sku).first()

        if not product:
            raise HTTPException(status_code=404, detail=f"Product with SKU {sku} not found")

        return ProductResponse.from_orm(product)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get product: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
