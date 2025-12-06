"""
Items API Endpoints - Unified item management for products, components, supplies, and services
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
import logging
import csv
import io

from decimal import Decimal
from app.db.session import get_db
from app.models import Product, ItemCategory, Inventory, BOM, BOMLine
from app.models.manufacturing import Routing
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.schemas.item import (
    ItemType,
    ItemCategoryCreate,
    ItemCategoryUpdate,
    ItemCategoryResponse,
    ItemCategoryTreeNode,
    ItemCreate,
    ItemUpdate,
    ItemListResponse,
    ItemResponse,
    ItemCSVImportRequest,
    ItemCSVImportResult,
    ItemBulkUpdateRequest,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Default pricing markup (from quoter: PLA/PETG=3.5x, ABS/ASA=4.0x, TPU=4.5x)
# Using 3.5x as default since PLA is most common
DEFAULT_PRICE_MARKUP = 3.5


# ============================================================================
# Item Categories
# ============================================================================

@router.get("/categories", response_model=List[ItemCategoryResponse])
async def list_categories(
    include_inactive: bool = False,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    List all item categories

    - **include_inactive**: Include inactive categories
    - **parent_id**: Filter to children of a specific parent (null for root categories)
    """
    query = db.query(ItemCategory)

    if not include_inactive:
        query = query.filter(ItemCategory.is_active == True)

    if parent_id is not None:
        query = query.filter(ItemCategory.parent_id == parent_id)

    categories = query.order_by(ItemCategory.sort_order, ItemCategory.name).all()

    result = []
    for cat in categories:
        resp = ItemCategoryResponse(
            id=cat.id,
            code=cat.code,
            name=cat.name,
            parent_id=cat.parent_id,
            description=cat.description,
            sort_order=cat.sort_order,
            is_active=cat.is_active,
            parent_name=cat.parent.name if cat.parent else None,
            full_path=cat.full_path,
            created_at=cat.created_at,
            updated_at=cat.updated_at,
        )
        result.append(resp)

    return result


@router.get("/categories/tree", response_model=List[ItemCategoryTreeNode])
async def get_category_tree(
    db: Session = Depends(get_db),
):
    """Get categories as a nested tree structure"""
    # Get all active categories
    categories = db.query(ItemCategory).filter(
        ItemCategory.is_active == True
    ).order_by(ItemCategory.sort_order, ItemCategory.name).all()

    # Build tree
    def build_tree(parent_id: Optional[int] = None) -> List[ItemCategoryTreeNode]:
        nodes = []
        for cat in categories:
            if cat.parent_id == parent_id:
                node = ItemCategoryTreeNode(
                    id=cat.id,
                    code=cat.code,
                    name=cat.name,
                    description=cat.description,
                    is_active=cat.is_active,
                    children=build_tree(cat.id),
                )
                nodes.append(node)
        return nodes

    return build_tree(None)


@router.post("/categories", response_model=ItemCategoryResponse, status_code=201)
async def create_category(
    request: ItemCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new item category"""
    # Check for duplicate code
    existing = db.query(ItemCategory).filter(ItemCategory.code == request.code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Category code '{request.code}' already exists")

    # Validate parent exists
    if request.parent_id:
        parent = db.query(ItemCategory).filter(ItemCategory.id == request.parent_id).first()
        if not parent:
            raise HTTPException(status_code=400, detail=f"Parent category {request.parent_id} not found")

    category = ItemCategory(
        code=request.code.upper(),
        name=request.name,
        parent_id=request.parent_id,
        description=request.description,
        sort_order=request.sort_order or 0,
        is_active=request.is_active if request.is_active is not None else True,
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    logger.info(f"Created category: {category.code}")

    return ItemCategoryResponse(
        id=category.id,
        code=category.code,
        name=category.name,
        parent_id=category.parent_id,
        description=category.description,
        sort_order=category.sort_order,
        is_active=category.is_active,
        parent_name=category.parent.name if category.parent else None,
        full_path=category.full_path,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.get("/categories/{category_id}", response_model=ItemCategoryResponse)
async def get_category(
    category_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific category by ID"""
    category = db.query(ItemCategory).filter(ItemCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail=f"Category {category_id} not found")

    return ItemCategoryResponse(
        id=category.id,
        code=category.code,
        name=category.name,
        parent_id=category.parent_id,
        description=category.description,
        sort_order=category.sort_order,
        is_active=category.is_active,
        parent_name=category.parent.name if category.parent else None,
        full_path=category.full_path,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.patch("/categories/{category_id}", response_model=ItemCategoryResponse)
async def update_category(
    category_id: int,
    request: ItemCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing category"""
    category = db.query(ItemCategory).filter(ItemCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail=f"Category {category_id} not found")

    # Check for code conflict if changing code
    if request.code and request.code.upper() != category.code:
        existing = db.query(ItemCategory).filter(ItemCategory.code == request.code.upper()).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Category code '{request.code}' already exists")

    # Validate parent if changing
    if request.parent_id is not None and request.parent_id != category.parent_id:
        if request.parent_id == category_id:
            raise HTTPException(status_code=400, detail="Category cannot be its own parent")
        if request.parent_id:
            parent = db.query(ItemCategory).filter(ItemCategory.id == request.parent_id).first()
            if not parent:
                raise HTTPException(status_code=400, detail=f"Parent category {request.parent_id} not found")

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "code" and value:
            value = value.upper()
        setattr(category, field, value)

    category.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(category)

    logger.info(f"Updated category: {category.code}")

    return ItemCategoryResponse(
        id=category.id,
        code=category.code,
        name=category.name,
        parent_id=category.parent_id,
        description=category.description,
        sort_order=category.sort_order,
        is_active=category.is_active,
        parent_name=category.parent.name if category.parent else None,
        full_path=category.full_path,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft delete a category (set is_active=False)

    Will fail if category has active items or child categories.
    """
    category = db.query(ItemCategory).filter(ItemCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail=f"Category {category_id} not found")

    # Check for child categories
    children = db.query(ItemCategory).filter(
        ItemCategory.parent_id == category_id,
        ItemCategory.is_active == True
    ).count()
    if children > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete category with {children} active child categories"
        )

    # Check for items in this category
    items = db.query(Product).filter(
        Product.category_id == category_id,
        Product.active == True
    ).count()
    if items > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete category with {items} active items"
        )

    category.is_active = False
    category.updated_at = datetime.utcnow()
    db.commit()

    logger.info(f"Deleted (deactivated) category: {category.code}")

    return {"message": f"Category {category.code} deleted"}


# ============================================================================
# Items (Products with extended fields)
# ============================================================================

@router.get("", response_model=dict)
async def list_items(
    item_type: Optional[str] = Query(None, description="Filter by item type"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search SKU or name"),
    active_only: bool = Query(True, description="Only show active items"),
    needs_reorder: bool = Query(False, description="Only show items below reorder point"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    List items with filtering and pagination

    Returns items with inventory summary and reorder status.
    """
    query = db.query(Product)

    # Filters
    if active_only:
        query = query.filter(Product.active == True)

    if item_type:
        query = query.filter(Product.item_type == item_type)

    if category_id:
        # Get all descendant category IDs (including the selected one)
        category_ids = _get_category_and_descendants(db, category_id)
        query = query.filter(Product.category_id.in_(category_ids))

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Product.sku.ilike(search_pattern),
                Product.name.ilike(search_pattern),
                Product.upc.ilike(search_pattern),
            )
        )

    # Get total count before pagination
    total = query.count()

    # Load with category relationship
    query = query.options(joinedload(Product.item_category))

    # Order and paginate
    items = query.order_by(Product.sku).offset(offset).limit(limit).all()

    # Build response with inventory info
    result = []
    for item in items:
        # Get inventory totals
        inv = db.query(
            func.coalesce(func.sum(Inventory.on_hand_quantity), 0).label("on_hand"),
            func.coalesce(func.sum(Inventory.allocated_quantity), 0).label("allocated"),
        ).filter(Inventory.product_id == item.id).first()

        on_hand = float(inv.on_hand) if inv else 0
        allocated = float(inv.allocated) if inv else 0
        available = on_hand - allocated
        reorder_point = float(item.reorder_point) if item.reorder_point else None
        item_needs_reorder = reorder_point is not None and on_hand <= reorder_point

        # Skip if needs_reorder filter is on and item doesn't need reorder
        if needs_reorder and not item_needs_reorder:
            continue

        # Calculate suggested price from standard cost with markup
        suggested_price = None
        if item.standard_cost:
            suggested_price = float(item.standard_cost) * DEFAULT_PRICE_MARKUP

        result.append(ItemListResponse(
            id=item.id,
            sku=item.sku,
            name=item.name,
            item_type=item.item_type or "finished_good",
            category_id=item.category_id,
            category_name=item.item_category.name if item.item_category else None,
            unit=item.unit,
            standard_cost=item.standard_cost,
            average_cost=item.average_cost,
            selling_price=item.selling_price,
            suggested_price=suggested_price,
            active=item.active,
            on_hand_qty=on_hand,
            available_qty=available,
            reorder_point=reorder_point,
            needs_reorder=item_needs_reorder,
        ))

    return {
        "total": total,
        "items": result,
    }


@router.post("", response_model=ItemResponse, status_code=201)
async def create_item(
    request: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new item"""
    # Check for duplicate SKU
    existing = db.query(Product).filter(Product.sku == request.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"SKU '{request.sku}' already exists")

    # Validate category if provided
    if request.category_id:
        category = db.query(ItemCategory).filter(ItemCategory.id == request.category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail=f"Category {request.category_id} not found")

    item = Product(
        sku=request.sku.upper(),
        name=request.name,
        description=request.description,
        unit=request.unit or "EA",
        item_type=request.item_type.value if request.item_type else "finished_good",
        category_id=request.category_id,
        cost_method=request.cost_method.value if request.cost_method else "average",
        standard_cost=request.standard_cost,
        selling_price=request.selling_price,
        weight_oz=request.weight_oz,
        length_in=request.length_in,
        width_in=request.width_in,
        height_in=request.height_in,
        lead_time_days=request.lead_time_days,
        min_order_qty=request.min_order_qty,
        reorder_point=request.reorder_point,
        upc=request.upc,
        legacy_sku=request.legacy_sku,
        is_raw_material=request.is_raw_material or False,
        track_lots=request.track_lots or False,
        track_serials=request.track_serials or False,
        active=True,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    logger.info(f"Created item: {item.sku}")

    return _build_item_response(item, db)


# ============================================================================
# Low Stock / Reorder Alerts
# ============================================================================

@router.get("/low-stock")
async def get_low_stock_items(
    include_zero_reorder: bool = False,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Get items that are below their reorder point.

    Returns items where available_quantity <= reorder_point, sorted by shortfall.

    - **include_zero_reorder**: Include items with reorder_point = 0 or NULL (default: False)
    - **limit**: Maximum number of items to return
    """
    from decimal import Decimal

    # Query products with inventory, filter to those below reorder point
    query = db.query(Product, Inventory).outerjoin(
        Inventory, Product.id == Inventory.product_id
    ).filter(
        Product.active == True,
        Product.reorder_point.isnot(None),
    )

    if not include_zero_reorder:
        query = query.filter(Product.reorder_point > 0)

    # Filter to items below reorder point
    # available_quantity <= reorder_point
    query = query.filter(
        or_(
            Inventory.available_quantity <= Product.reorder_point,
            Inventory.id.is_(None)  # No inventory record = 0 stock
        )
    )

    results = query.limit(limit).all()

    items = []
    for product, inventory in results:
        available = float(inventory.available_quantity) if inventory else 0
        on_hand = float(inventory.on_hand_quantity) if inventory else 0
        reorder_point = float(product.reorder_point) if product.reorder_point else 0
        shortfall = reorder_point - available

        items.append({
            "id": product.id,
            "sku": product.sku,
            "name": product.name,
            "item_type": product.item_type,
            "unit": product.unit,
            "category_name": product.item_category.name if product.item_category else None,
            "on_hand_qty": on_hand,
            "available_qty": available,
            "reorder_point": reorder_point,
            "shortfall": shortfall,
            "cost": float(product.standard_cost or product.average_cost or 0),
            "preferred_vendor_id": product.preferred_vendor_id,
        })

    # Sort by shortfall (most critical first)
    items.sort(key=lambda x: x["shortfall"], reverse=True)

    return {
        "items": items,
        "count": len(items),
        "summary": {
            "total_items_low": len(items),
            "total_shortfall_value": sum(i["shortfall"] * i["cost"] for i in items),
        }
    }


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific item by ID"""
    item = db.query(Product).options(
        joinedload(Product.item_category)
    ).filter(Product.id == item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")

    return _build_item_response(item, db)


@router.get("/sku/{sku}", response_model=ItemResponse)
async def get_item_by_sku(
    sku: str,
    db: Session = Depends(get_db),
):
    """Get a specific item by SKU"""
    item = db.query(Product).options(
        joinedload(Product.item_category)
    ).filter(Product.sku == sku.upper()).first()

    if not item:
        raise HTTPException(status_code=404, detail=f"Item with SKU '{sku}' not found")

    return _build_item_response(item, db)


@router.patch("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    request: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing item"""
    item = db.query(Product).filter(Product.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")

    # Check for SKU conflict if changing
    if request.sku and request.sku.upper() != item.sku:
        existing = db.query(Product).filter(Product.sku == request.sku.upper()).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"SKU '{request.sku}' already exists")

    # Validate category if changing
    if request.category_id is not None and request.category_id != item.category_id:
        if request.category_id:
            category = db.query(ItemCategory).filter(ItemCategory.id == request.category_id).first()
            if not category:
                raise HTTPException(status_code=400, detail=f"Category {request.category_id} not found")

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "sku" and value:
            value = value.upper()
        if field == "item_type" and value:
            value = value.value if hasattr(value, "value") else value
        if field == "cost_method" and value:
            value = value.value if hasattr(value, "value") else value
        if field == "is_active":
            field = "active"
        setattr(item, field, value)

    item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)

    logger.info(f"Updated item: {item.sku}")

    return _build_item_response(item, db)


@router.delete("/{item_id}")
async def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft delete an item (set active=False)

    Will fail if item has inventory on hand or is used in active BOMs.
    """
    item = db.query(Product).filter(Product.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")

    # Check for inventory
    inv = db.query(func.sum(Inventory.on_hand_quantity)).filter(
        Inventory.product_id == item_id
    ).scalar()
    if inv and float(inv) > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete item with {inv} units on hand"
        )

    # Check for active BOMs using this item
    bom_count = db.query(BOM).filter(
        BOM.product_id == item_id,
        BOM.active == True
    ).count()
    if bom_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete item used in {bom_count} active BOMs"
        )

    item.active = False
    item.updated_at = datetime.utcnow()
    db.commit()

    logger.info(f"Deleted (deactivated) item: {item.sku}")

    return {"message": f"Item {item.sku} deleted"}


# ============================================================================
# Bulk Operations
# ============================================================================

@router.post("/import", response_model=ItemCSVImportResult)
async def import_items_csv(
    file: UploadFile = File(...),
    update_existing: bool = Query(False, description="Update items if SKU exists"),
    default_item_type: str = Query("finished_good", description="Default item type"),
    default_category_id: Optional[int] = Query(None, description="Default category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Import items from CSV file

    Expected columns: sku, name, description, unit, item_type, category_id,
    standard_cost, selling_price, reorder_point, upc
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    content = await file.read()
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    result = ItemCSVImportResult(
        total_rows=0,
        created=0,
        updated=0,
        skipped=0,
        errors=[],
    )

    for row_num, row in enumerate(reader, start=2):
        result.total_rows += 1

        try:
            sku = row.get("sku", "").strip().upper()
            if not sku:
                result.errors.append({"row": row_num, "error": "SKU is required"})
                result.skipped += 1
                continue

            name = row.get("name", "").strip()
            if not name:
                result.errors.append({"row": row_num, "error": "Name is required", "sku": sku})
                result.skipped += 1
                continue

            # Check if exists
            existing = db.query(Product).filter(Product.sku == sku).first()

            if existing:
                if not update_existing:
                    result.skipped += 1
                    continue

                # Update existing
                existing.name = name
                existing.description = row.get("description", "").strip() or existing.description
                existing.unit = row.get("unit", "").strip() or existing.unit
                existing.item_type = row.get("item_type", "").strip() or existing.item_type
                if row.get("category_id"):
                    existing.category_id = int(row["category_id"])
                if row.get("standard_cost"):
                    existing.standard_cost = float(row["standard_cost"])
                if row.get("selling_price"):
                    existing.selling_price = float(row["selling_price"])
                if row.get("reorder_point"):
                    existing.reorder_point = float(row["reorder_point"])
                existing.upc = row.get("upc", "").strip() or existing.upc
                existing.updated_at = datetime.utcnow()
                result.updated += 1
            else:
                # Create new
                item = Product(
                    sku=sku,
                    name=name,
                    description=row.get("description", "").strip() or None,
                    unit=row.get("unit", "").strip() or "EA",
                    item_type=row.get("item_type", "").strip() or default_item_type,
                    category_id=int(row["category_id"]) if row.get("category_id") else default_category_id,
                    standard_cost=float(row["standard_cost"]) if row.get("standard_cost") else None,
                    selling_price=float(row["selling_price"]) if row.get("selling_price") else None,
                    reorder_point=float(row["reorder_point"]) if row.get("reorder_point") else None,
                    upc=row.get("upc", "").strip() or None,
                    active=True,
                )
                db.add(item)
                result.created += 1

        except Exception as e:
            result.errors.append({"row": row_num, "error": str(e), "sku": row.get("sku", "")})
            result.skipped += 1

    db.commit()

    logger.info(f"CSV import complete: {result.created} created, {result.updated} updated, {result.skipped} skipped")

    return result


@router.post("/bulk-update")
async def bulk_update_items(
    request: ItemBulkUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bulk update multiple items at once"""
    if not request.item_ids:
        raise HTTPException(status_code=400, detail="No items specified")

    # Validate category if provided
    if request.category_id:
        category = db.query(ItemCategory).filter(ItemCategory.id == request.category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail=f"Category {request.category_id} not found")

    updated = 0
    for item_id in request.item_ids:
        item = db.query(Product).filter(Product.id == item_id).first()
        if item:
            if request.category_id is not None:
                item.category_id = request.category_id
            if request.item_type is not None:
                item.item_type = request.item_type.value
            if request.is_active is not None:
                item.active = request.is_active
            item.updated_at = datetime.utcnow()
            updated += 1

    db.commit()

    logger.info(f"Bulk update: {updated} items updated")

    return {"message": f"{updated} items updated"}


# ============================================================================
# Recost Operations
# ============================================================================

def _recalculate_bom_cost(bom: BOM, db: Session) -> Decimal:
    """
    Recalculate BOM total cost from component standard_costs.

    For each BOM line:
      line_cost = component.standard_cost * quantity * (1 + scrap_factor/100)

    Updates bom.total_cost and returns the new value.
    """
    total = Decimal("0")

    # Get all BOM lines (BOMLine doesn't have active flag - only BOM does)
    lines = db.query(BOMLine).filter(
        BOMLine.bom_id == bom.id
    ).all()

    for line in lines:
        component = db.query(Product).filter(Product.id == line.component_id).first()
        if component:
            # Use standard_cost, fall back to average_cost, then last_cost
            component_cost = component.standard_cost or component.average_cost or component.last_cost
            if component_cost:
                qty = line.quantity or Decimal("0")
                scrap = line.scrap_factor or Decimal("0")
                effective_qty = qty * (1 + scrap / 100)
                total += Decimal(str(component_cost)) * effective_qty

    # Update the BOM total_cost
    bom.total_cost = total
    bom.updated_at = datetime.utcnow()

    return total


def _calculate_item_cost(item: Product, db: Session) -> dict:
    """
    Calculate standard cost for an item.

    For manufactured items (with BOM):
      1. Recalculate BOM cost from component standard_costs
      2. Add Routing process cost
    For purchased items (no BOM):
      Use average_cost or last_cost from purchases

    Returns a dict with breakdown.
    """
    bom_cost = 0.0
    routing_cost = 0.0
    purchase_cost = 0.0
    bom_id = None
    routing_id = None
    cost_source = None

    # Check for active BOM (indicates manufactured item)
    bom = db.query(BOM).filter(
        BOM.product_id == item.id,
        BOM.active == True
    ).first()

    if bom:
        # Manufactured item: recalculate BOM + add Routing
        cost_source = "manufactured"
        bom_id = bom.id

        # Recalculate BOM cost from component standard_costs
        bom_cost = float(_recalculate_bom_cost(bom, db))

        # Get active Routing cost
        routing = db.query(Routing).filter(
            Routing.product_id == item.id,
            Routing.is_active == True
        ).first()
        if routing and routing.total_cost:
            routing_cost = float(routing.total_cost)
            routing_id = routing.id

        total_cost = bom_cost + routing_cost
    else:
        # Purchased item: use average_cost, fall back to last_cost
        cost_source = "purchased"
        if item.average_cost:
            purchase_cost = float(item.average_cost)
        elif item.last_cost:
            purchase_cost = float(item.last_cost)

        total_cost = purchase_cost

    return {
        "bom_id": bom_id,
        "bom_cost": bom_cost,
        "routing_id": routing_id,
        "routing_cost": routing_cost,
        "purchase_cost": purchase_cost,
        "total_cost": total_cost,
        "cost_source": cost_source,
    }


@router.post("/recost-all")
async def recost_all_items(
    item_type: Optional[str] = Query(None, description="Filter by item type"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    cost_source: Optional[str] = Query(None, description="Filter: 'manufactured' or 'purchased'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recost all items matching filters.

    - Manufactured items (with BOM): BOM cost + Routing cost
    - Purchased items (no BOM): Uses average_cost or last_cost from purchases

    - **item_type**: Filter by item type (e.g., 'finished_good', 'raw_material')
    - **category_id**: Filter by category (includes descendants)
    - **cost_source**: Filter by 'manufactured' (has BOM) or 'purchased' (no BOM)
    """
    query = db.query(Product).filter(Product.active == True)

    if item_type:
        query = query.filter(Product.item_type == item_type)

    if category_id:
        category_ids = _get_category_and_descendants(db, category_id)
        query = query.filter(Product.category_id.in_(category_ids))

    items = query.all()

    updated = 0
    skipped = 0
    results = []

    for item in items:
        cost_data = _calculate_item_cost(item, db)

        # Filter by cost source if specified
        if cost_source and cost_data["cost_source"] != cost_source:
            continue

        # Skip if no cost to set
        if cost_data["total_cost"] == 0:
            skipped += 1
            continue

        # Update standard cost
        old_cost = float(item.standard_cost) if item.standard_cost else 0
        item.standard_cost = cost_data["total_cost"]
        item.updated_at = datetime.utcnow()
        updated += 1

        results.append({
            "id": item.id,
            "sku": item.sku,
            "old_cost": old_cost,
            "new_cost": cost_data["total_cost"],
            "cost_source": cost_data["cost_source"],
            "bom_cost": cost_data["bom_cost"],
            "routing_cost": cost_data["routing_cost"],
            "purchase_cost": cost_data["purchase_cost"],
        })

    db.commit()

    logger.info(f"Recost all: {updated} items updated, {skipped} skipped")

    return {
        "updated": updated,
        "skipped": skipped,
        "items": results,
    }


@router.post("/{item_id}/recost")
async def recost_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recost a single item.

    - Manufactured items (with BOM): BOM cost + Routing cost
    - Purchased items (no BOM): Uses average_cost or last_cost
    """
    item = db.query(Product).filter(Product.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")

    cost_data = _calculate_item_cost(item, db)

    old_cost = float(item.standard_cost) if item.standard_cost else 0
    item.standard_cost = cost_data["total_cost"]
    item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)

    logger.info(f"Recost item {item.sku}: ${old_cost:.4f} -> ${cost_data['total_cost']:.4f}")

    return {
        "id": item.id,
        "sku": item.sku,
        "name": item.name,
        "old_cost": old_cost,
        "new_cost": cost_data["total_cost"],
        "cost_source": cost_data["cost_source"],
        "bom_id": cost_data["bom_id"],
        "bom_cost": cost_data["bom_cost"],
        "routing_id": cost_data["routing_id"],
        "routing_cost": cost_data["routing_cost"],
        "purchase_cost": cost_data["purchase_cost"],
        "message": f"Standard cost updated: ${old_cost:.4f} -> ${cost_data['total_cost']:.4f}",
    }


# ============================================================================
# Helper Functions
# ============================================================================

def _get_category_and_descendants(db: Session, category_id: int) -> list[int]:
    """
    Get a category ID and all its descendant category IDs.
    Used for filtering items by category hierarchy.
    """
    result = [category_id]

    # Get direct children
    children = db.query(ItemCategory.id).filter(
        ItemCategory.parent_id == category_id
    ).all()

    # Recursively get descendants
    for (child_id,) in children:
        result.extend(_get_category_and_descendants(db, child_id))

    return result


def _build_item_response(item: Product, db: Session) -> ItemResponse:
    """Build full item response with inventory and BOM info"""
    # Get inventory totals
    inv = db.query(
        func.coalesce(func.sum(Inventory.on_hand_quantity), 0).label("on_hand"),
        func.coalesce(func.sum(Inventory.allocated_quantity), 0).label("allocated"),
    ).filter(Inventory.product_id == item.id).first()

    on_hand = float(inv.on_hand) if inv else 0
    allocated = float(inv.allocated) if inv else 0

    # Get BOM count
    bom_count = db.query(BOM).filter(BOM.product_id == item.id, BOM.active == True).count()

    return ItemResponse(
        id=item.id,
        sku=item.sku,
        name=item.name,
        description=item.description,
        unit=item.unit,
        item_type=ItemType(item.item_type) if item.item_type else ItemType.FINISHED_GOOD,
        category_id=item.category_id,
        cost_method=item.cost_method or "average",
        standard_cost=item.standard_cost,
        average_cost=item.average_cost,
        last_cost=item.last_cost,
        selling_price=item.selling_price,
        weight_oz=item.weight_oz,
        length_in=item.length_in,
        width_in=item.width_in,
        height_in=item.height_in,
        lead_time_days=item.lead_time_days,
        min_order_qty=item.min_order_qty,
        reorder_point=item.reorder_point,
        upc=item.upc,
        legacy_sku=item.legacy_sku,
        active=item.active,
        is_raw_material=item.is_raw_material,
        track_lots=item.track_lots,
        track_serials=item.track_serials,
        category_name=item.item_category.name if item.item_category else None,
        category_path=item.item_category.full_path if item.item_category else None,
        on_hand_qty=on_hand,
        available_qty=on_hand - allocated,
        allocated_qty=allocated,
        has_bom=item.has_bom or bom_count > 0,
        bom_count=bom_count,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )
