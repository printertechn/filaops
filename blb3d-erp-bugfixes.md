# BLB3D ERP System - Comprehensive Bug Fix Document

## Executive Summary

E2E code review identified **5 critical bugs** preventing inventory and BOM modules from functioning correctly. The root cause is an **architectural gap**: the system has two separate inventory tracking mechanisms that don't communicate.

| Severity | Count | Description |
|----------|-------|-------------|
| 🔴 Critical | 5 | Blocking production workflow |
| 🟡 Medium | 3 | Data integrity concerns |
| 🟢 Low | 3 | Enhancements |

---

## System Architecture (As Discovered)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           QUOTE ENGINE FLOW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  Customer Upload → 3MF Parse → Material Selection → Quote Created           │
│                                      ↓                                       │
│                        ┌─────────────────────────┐                          │
│                        │   MaterialInventory      │ ← Quote engine checks   │
│                        │   (material_inventory)   │    this table           │
│                        │   - quantity_kg          │                          │
│                        │   - in_stock flag        │                          │
│                        │   - product_id (FK)      │                          │
│                        └───────────┬─────────────┘                          │
│                                    │ Links to                               │
│                                    ↓                                         │
│                        ┌─────────────────────────┐                          │
│                        │       Product            │                          │
│                        │      (products)          │                          │
│                        │   - is_raw_material      │                          │
│                        │   - type (custom/std)    │                          │
│                        └───────────┬─────────────┘                          │
│                                    │                                         │
└────────────────────────────────────┼─────────────────────────────────────────┘
                                     │
         ╔═══════════════════════════╧═══════════════════════════╗
         ║              🚨 SYNC GAP - NOTHING CONNECTS THESE 🚨   ║
         ╚═══════════════════════════╤═══════════════════════════╝
                                     │
┌────────────────────────────────────┼─────────────────────────────────────────┐
│                           FULFILLMENT FLOW                                   │
├────────────────────────────────────┼─────────────────────────────────────────┤
│                                    ↓                                         │
│                        ┌─────────────────────────┐                          │
│                        │       Inventory          │ ← Fulfillment checks    │
│                        │      (inventory)         │    this table           │
│                        │   - product_id           │                          │
│                        │   - location_id          │                          │
│                        │   - on_hand_quantity     │                          │
│                        │   - allocated_quantity   │                          │
│                        └─────────────────────────┘                          │
│                                                                              │
│  BOM Explosion → Reserve Materials → Print → Consume → Ship                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

**The Problem**: Quote engine says "in stock" (MaterialInventory.quantity_kg > 0), but fulfillment says "no inventory" (no Inventory record exists for that Product).

---

## 🔴 CRITICAL BUG #1: Double Consumption

### Location
`backend/app/api/v1/endpoints/admin/fulfillment.py`

### Problem
Both `complete-print` (lines ~380-430) AND `pass-qc` (lines ~480-540) contain identical material consumption logic:

```python
# This code appears in BOTH functions:
reservation_txns = db.query(InventoryTransaction).filter(
    InventoryTransaction.reference_type == "production_order",
    InventoryTransaction.reference_id == po.id,
    InventoryTransaction.transaction_type == "reservation"
).all()

for res_txn in reservation_txns:
    reserved_qty = abs(float(res_txn.quantity))
    # ... consume from inventory ...
```

### Impact
- If both functions are called in sequence, inventory is decremented TWICE
- Material shows negative quantities
- Accounting is wrong

### Fix
Remove the consumption logic from `pass-qc`. It should ONLY:
1. Update production order status to "completed"
2. Update sales order status to "ready_to_ship"
3. Log QC notes

```python
@router.post("/queue/{production_order_id}/pass-qc")
async def pass_quality_check(
    production_order_id: int,
    qc_notes: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Mark order as passed QC and ready to ship."""
    po = db.query(ProductionOrder).filter(ProductionOrder.id == production_order_id).first()
    
    if not po:
        raise HTTPException(status_code=404, detail="Production order not found")
    
    if po.status != "printed":
        raise HTTPException(status_code=400, detail=f"Cannot pass QC for status '{po.status}'")
    
    # Update production order
    po.status = "completed"
    po.finish_date = datetime.utcnow()
    
    if qc_notes:
        po.notes = (po.notes + "\n" if po.notes else "") + f"[{datetime.utcnow().isoformat()}] QC Passed: {qc_notes}"
    
    # Update sales order - NO MATERIAL CONSUMPTION HERE (already done in complete-print)
    quote = db.query(Quote).filter(Quote.product_id == po.product_id).first() if po.product_id else None
    if quote:
        sales_order = db.query(SalesOrder).filter(SalesOrder.quote_id == quote.id).first()
        if sales_order:
            sales_order.status = "ready_to_ship"
    
    db.commit()
    
    return {
        "success": True,
        "production_order_id": po.id,
        "status": po.status,
        "sales_order_status": "ready_to_ship" if quote else None,
        "message": f"QC passed for {po.code}. Order ready to ship!",
    }
```

---

## 🔴 CRITICAL BUG #2: Inventory Record Not Created for Materials

### Location
`backend/app/services/material_service.py` - `get_material_product_for_bom()`

### Problem
When a material Product is created/linked, NO corresponding `Inventory` record is created:

```python
def get_material_product_for_bom(...):
    # ... gets or creates Product ...
    product = Product(
        sku=inventory.sku,
        name=f"{material.name} - {color.name}",
        is_raw_material=True,
        # ...
    )
    db.add(product)
    inventory.product_id = product.id  # Links MaterialInventory to Product
    # ❌ BUT NO Inventory RECORD CREATED!
```

When fulfillment does BOM explosion:
```python
inventory = db.query(Inventory).filter(
    Inventory.product_id == line.component_id
).first()
# Returns None! Production shows "insufficient materials"
```

### Fix
Add `Inventory` record creation when linking Product:

```python
def get_material_product_for_bom(
    db: Session,
    material_type_code: str,
    color_code: str,
    require_in_stock: bool = False
) -> Tuple[Product, MaterialInventory]:
    """Get the Product record for BOM creation based on material and color"""
    
    mat_inventory = get_material_inventory(db, material_type_code, color_code)
    
    if require_in_stock and not mat_inventory.in_stock:
        raise MaterialNotInStockError(f"Material not in stock: {material_type_code} + {color_code}")
    
    # Get or create the product
    product = None
    if mat_inventory.product_id:
        product = db.query(Product).get(mat_inventory.product_id)
    
    if not product:
        # Try to find by SKU
        product = db.query(Product).filter(
            Product.sku == mat_inventory.sku,
            Product.active == True
        ).first()
    
    if not product:
        # Create the product
        material = get_material_type(db, material_type_code)
        color = get_color(db, color_code)
        
        product = Product(
            sku=mat_inventory.sku,
            name=f"{material.name} - {color.name}",
            description=f"{material.name} filament in {color.name}",
            category="Raw Materials",
            unit="kg",
            cost=mat_inventory.cost_per_kg or material.base_price_per_kg,
            selling_price=material.base_price_per_kg,
            weight=Decimal("1.0"),
            is_raw_material=True,
            has_bom=False,
            active=True
        )
        db.add(product)
        db.flush()  # Get product.id
    
    # Link MaterialInventory to Product
    if mat_inventory.product_id != product.id:
        mat_inventory.product_id = product.id
    
    # ✅ NEW: Ensure Inventory record exists and is synced
    from app.models.inventory import Inventory, InventoryLocation
    
    # Get or create default location
    default_location = db.query(InventoryLocation).filter(
        InventoryLocation.code == "RAW"  # Or your raw materials location code
    ).first()
    
    if not default_location:
        default_location = db.query(InventoryLocation).first()  # Fallback to any location
    
    location_id = default_location.id if default_location else 1
    
    erp_inventory = db.query(Inventory).filter(
        Inventory.product_id == product.id,
        Inventory.location_id == location_id
    ).first()
    
    if not erp_inventory:
        # Create Inventory record synced from MaterialInventory
        erp_inventory = Inventory(
            product_id=product.id,
            location_id=location_id,
            on_hand_quantity=mat_inventory.quantity_kg or Decimal("0"),
            allocated_quantity=Decimal("0"),
            available_quantity=mat_inventory.quantity_kg or Decimal("0"),
        )
        db.add(erp_inventory)
    else:
        # Sync quantities (MaterialInventory is source of truth for raw materials)
        erp_inventory.on_hand_quantity = mat_inventory.quantity_kg or Decimal("0")
        erp_inventory.available_quantity = (
            (mat_inventory.quantity_kg or Decimal("0")) - erp_inventory.allocated_quantity
        )
    
    db.commit()
    return product, mat_inventory
```

---

## 🔴 CRITICAL BUG #3: MTO Finished Goods Inventory Not Created

### Location
`backend/app/api/v1/endpoints/admin/fulfillment.py` - `complete_print()`

### Problem
When production completes, the code tries to add finished goods to inventory:

```python
if qty_good > 0 and po.product_id:
    fg_inventory = db.query(Inventory).filter(
        Inventory.product_id == po.product_id
    ).first()
    
    if fg_inventory:  # ❌ For MTO custom products, this is ALWAYS None!
        fg_inventory.on_hand_quantity = ...
```

For MTO (Make-to-Order) custom products created from quotes, no `Inventory` record exists yet. The finished goods are never tracked.

### Fix
Create Inventory record if it doesn't exist:

```python
# FINISHED GOODS INVENTORY - Add good parts to stock
finished_goods_added = None
if qty_good > 0 and po.product_id:
    # Find or CREATE finished goods inventory
    fg_inventory = db.query(Inventory).filter(
        Inventory.product_id == po.product_id
    ).first()
    
    if not fg_inventory:
        # ✅ NEW: Create Inventory record for MTO finished goods
        # Get default finished goods location
        fg_location = db.query(InventoryLocation).filter(
            InventoryLocation.code == "FG"  # Finished Goods location
        ).first()
        
        if not fg_location:
            fg_location = db.query(InventoryLocation).first()  # Fallback
        
        fg_inventory = Inventory(
            product_id=po.product_id,
            location_id=fg_location.id if fg_location else 1,
            on_hand_quantity=Decimal("0"),
            allocated_quantity=Decimal("0"),
            available_quantity=Decimal("0"),
        )
        db.add(fg_inventory)
        db.flush()
    
    # Add good parts to inventory
    fg_inventory.on_hand_quantity = Decimal(str(
        float(fg_inventory.on_hand_quantity) + qty_good
    ))
    fg_inventory.available_quantity = Decimal(str(
        float(fg_inventory.on_hand_quantity) - float(fg_inventory.allocated_quantity)
    ))
    
    # Create receipt transaction
    receipt_txn = InventoryTransaction(
        product_id=po.product_id,
        location_id=fg_inventory.location_id,
        transaction_type="receipt",
        reference_type="production_order",
        reference_id=po.id,
        quantity=Decimal(str(qty_good)),
        notes=f"Produced from {po.code}: {qty_good} good parts",
        created_by="system",
    )
    db.add(receipt_txn)
    
    product = db.query(Product).filter(Product.id == po.product_id).first()
    finished_goods_added = {
        "product_sku": product.sku if product else "N/A",
        "quantity_added": qty_good,
        "new_on_hand": float(fg_inventory.on_hand_quantity),
    }
```

---

## 🔴 CRITICAL BUG #4: MaterialInventory Never Decremented

### Location
`backend/app/api/v1/endpoints/admin/fulfillment.py` - `complete_print()`

### Problem
When materials are consumed, only the `Inventory` table is updated. The `MaterialInventory.quantity_kg` is NEVER decremented.

Result: Quote engine keeps showing material "in stock" even after it's been consumed.

### Fix
After consuming from ERP Inventory, also decrement MaterialInventory:

```python
# In complete_print(), after consuming from Inventory:

for res_txn in reservation_txns:
    reserved_qty = abs(float(res_txn.quantity))
    
    # Find the inventory record
    inventory = db.query(Inventory).filter(
        Inventory.product_id == res_txn.product_id,
        Inventory.location_id == res_txn.location_id
    ).first()
    
    if inventory:
        # ... existing consumption logic ...
        
        # ✅ NEW: Also update MaterialInventory if this is a raw material
        component = db.query(Product).filter(Product.id == res_txn.product_id).first()
        
        if component and component.is_raw_material:
            # Find linked MaterialInventory
            mat_inv = db.query(MaterialInventory).filter(
                MaterialInventory.product_id == component.id
            ).first()
            
            if mat_inv:
                # Decrement MaterialInventory.quantity_kg
                new_qty = max(Decimal("0"), mat_inv.quantity_kg - Decimal(str(reserved_qty)))
                mat_inv.quantity_kg = new_qty
                
                # Update in_stock flag
                mat_inv.in_stock = new_qty > Decimal("0")
                
                consumed_materials[-1]["material_inventory_remaining_kg"] = float(new_qty)
```

---

## 🔴 CRITICAL BUG #5: Inventory Sync at Production Start

### Location
`backend/app/api/v1/endpoints/admin/fulfillment.py` - `start_production()`

### Problem
Even if we fix bug #2 (creating Inventory records), there's a timing issue. The BOM is created at payment time, but inventory may have changed between payment and production start.

Also, if the Inventory record was created but quantities are out of sync with MaterialInventory, reservations will fail.

### Fix
Add sync check at production start:

```python
@router.post("/queue/{production_order_id}/start")
async def start_production(...):
    # ... existing validation ...
    
    if bom and bom.lines:
        production_qty = float(po.quantity)
        
        for line in bom.lines:
            component = line.component
            
            # ✅ NEW: Sync MaterialInventory → Inventory for raw materials
            if component and component.is_raw_material:
                mat_inv = db.query(MaterialInventory).filter(
                    MaterialInventory.product_id == component.id
                ).first()
                
                if mat_inv:
                    # Get or create Inventory record
                    inventory = db.query(Inventory).filter(
                        Inventory.product_id == component.id
                    ).first()
                    
                    if not inventory:
                        # Create it
                        default_loc = db.query(InventoryLocation).first()
                        inventory = Inventory(
                            product_id=component.id,
                            location_id=default_loc.id if default_loc else 1,
                            on_hand_quantity=mat_inv.quantity_kg,
                            allocated_quantity=Decimal("0"),
                            available_quantity=mat_inv.quantity_kg,
                        )
                        db.add(inventory)
                        db.flush()
                    else:
                        # Sync from MaterialInventory (source of truth for raw materials)
                        inventory.on_hand_quantity = mat_inv.quantity_kg
                        inventory.available_quantity = mat_inv.quantity_kg - inventory.allocated_quantity
            
            # ... rest of existing reservation logic ...
```

---

## 🟡 MEDIUM BUG #6: Hardcoded location_id=1

### Location
`backend/app/api/v1/endpoints/inventory.py` - `create_transaction()`

### Problem
```python
# In create_transaction():
location_id = 1  # Hardcoded!
```

### Fix
Look up location by code or use the inventory record's location:

```python
# Find location by code
location = db.query(InventoryLocation).filter(
    InventoryLocation.code == request.location
).first()

if not location:
    # Fallback to default
    location = db.query(InventoryLocation).filter(InventoryLocation.code == "DEFAULT").first()
    if not location:
        location = db.query(InventoryLocation).first()

location_id = location.id if location else 1
```

---

## 🟡 MEDIUM BUG #7: No Blocking on Zero Inventory

### Location
`backend/app/api/v1/endpoints/admin/fulfillment.py` - `start_production()`

### Problem
Production starts even with zero inventory (just adds warning to `insufficient_materials`).

### Suggested Enhancement
Add optional blocking mode:

```python
class StartProductionRequest(BaseModel):
    printer_id: Optional[str] = None
    notes: Optional[str] = None
    allow_insufficient: bool = False  # NEW: Explicit override required

# In start_production:
if insufficient_materials and not request.allow_insufficient:
    raise HTTPException(
        status_code=400,
        detail={
            "error": "Insufficient materials",
            "materials": insufficient_materials,
            "message": "Set allow_insufficient=true to start anyway"
        }
    )
```

---

## 🟡 MEDIUM BUG #8: Scrap Location Fallback

### Location
`backend/app/api/v1/endpoints/admin/fulfillment.py` - `complete_print()` scrap tracking

### Problem
```python
scrap_txn = InventoryTransaction(
    product_id=po.product_id,
    location_id=fg_inventory.location_id if fg_inventory else 1,  # Hardcoded fallback
```

### Fix
Use proper location lookup:

```python
scrap_location_id = (
    fg_inventory.location_id if fg_inventory 
    else db.query(InventoryLocation).filter(InventoryLocation.code == "SCRAP").first()
    or db.query(InventoryLocation).first()
).id
```

---

## Implementation Order

### Phase 1: Stop the Bleeding (Do First)
1. **Bug #1** - Remove duplicate consumption from `pass_qc` (5 min)
2. **Bug #3** - Create Inventory for MTO finished goods (15 min)

### Phase 2: Fix the Sync Gap (Core Fix)
3. **Bug #2** - Create Inventory when linking material Product (30 min)
4. **Bug #4** - Decrement MaterialInventory on consumption (15 min)
5. **Bug #5** - Add sync check at production start (20 min)

### Phase 3: Polish
6. **Bug #6** - Remove hardcoded location_id (10 min)
7. **Bug #7** - Optional insufficient blocking (15 min)
8. **Bug #8** - Proper scrap location (5 min)

---

## Testing Checklist

After fixes, verify this E2E flow works:

- [ ] Upload 3MF, select material/color → Quote shows correct lead time
- [ ] Pay for quote → Product, BOM, SO, PO all created
- [ ] Check Inventory table → Material Product has Inventory record with correct qty
- [ ] Start production → Reservations created, Inventory.allocated increases
- [ ] Complete print (5 good, 1 bad) → Materials consumed, finished goods added, scrap recorded
- [ ] Pass QC → Status updates ONLY, no duplicate consumption
- [ ] Check MaterialInventory → quantity_kg decremented
- [ ] Ship order → Tracking updated, order complete
- [ ] Create new quote for same material → Shows updated (lower) stock

---

## Files Modified

| File | Changes |
|------|---------|
| `backend/app/api/v1/endpoints/admin/fulfillment.py` | Bugs #1, #3, #4, #5, #7, #8 |
| `backend/app/services/material_service.py` | Bug #2 |
| `backend/app/api/v1/endpoints/inventory.py` | Bug #6 |

---

---

---

## 🟢 ENHANCEMENT #1: MTS (Make-to-Stock) Support

### Current State
The system is 100% MTO (Make-to-Order). Every production order originates from a paid quote.

### Required for MTS

#### A. Create Production Order Without Sales Order

New endpoint: `POST /admin/fulfillment/create-production-order`

```python
class CreateProductionOrderRequest(BaseModel):
    product_id: int  # Existing MTS product
    quantity: int
    priority: str = "normal"
    notes: Optional[str] = None


@router.post("/create-production-order")
async def create_production_order_mts(
    request: CreateProductionOrderRequest,
    db: Session = Depends(get_db),
):
    """
    Create a production order for MTS (Make-to-Stock) products.
    
    No sales order required - builds to inventory.
    """
    # Verify product exists and has BOM
    product = db.query(Product).filter(Product.id == request.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if not product.has_bom:
        raise HTTPException(status_code=400, detail="Product has no BOM")
    
    # Get active BOM
    bom = db.query(BOM).filter(
        BOM.product_id == product.id,
        BOM.active == True
    ).first()
    
    if not bom:
        raise HTTPException(status_code=400, detail="No active BOM for product")
    
    # Generate PO code
    po_code = generate_production_order_code(db)
    
    # Create production order (no sales_order_id)
    po = ProductionOrder(
        code=po_code,
        product_id=product.id,
        bom_id=bom.id,
        sales_order_id=None,  # Key difference: MTS has no SO
        quantity=request.quantity,
        status="scheduled",
        priority=request.priority,
        notes=request.notes or f"MTS build for {product.sku}",
    )
    
    db.add(po)
    db.commit()
    
    return {
        "success": True,
        "production_order_id": po.id,
        "code": po.code,
        "product_sku": product.sku,
        "quantity": request.quantity,
        "message": f"MTS production order {po.code} created for {request.quantity}x {product.sku}",
    }
```

#### B. Sales Order Fulfillment from Stock

When creating a sales order for an MTS product, check finished goods inventory:

```python
# In sales order creation:
def create_sales_order_for_mts_product(product_id: int, quantity: int, db: Session):
    """Create SO and allocate from finished goods inventory."""
    
    # Check FG inventory
    fg_inventory = db.query(Inventory).filter(
        Inventory.product_id == product_id
    ).first()
    
    if not fg_inventory or fg_inventory.available_quantity < quantity:
        available = fg_inventory.available_quantity if fg_inventory else 0
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock: have {available}, need {quantity}"
        )
    
    # Create SO
    sales_order = SalesOrder(...)
    db.add(sales_order)
    db.flush()
    
    # Allocate finished goods
    fg_inventory.allocated_quantity += Decimal(str(quantity))
    fg_inventory.available_quantity = (
        fg_inventory.on_hand_quantity - fg_inventory.allocated_quantity
    )
    
    # Create allocation transaction
    alloc_txn = InventoryTransaction(
        product_id=product_id,
        location_id=fg_inventory.location_id,
        transaction_type="allocation",
        reference_type="sales_order",
        reference_id=sales_order.id,
        quantity=Decimal(str(-quantity)),  # Negative = allocated out
        notes=f"Allocated for {sales_order.order_number}",
        created_by="system",
    )
    db.add(alloc_txn)
    
    # Set status to ready_to_ship (no production needed)
    sales_order.status = "ready_to_ship"
    
    return sales_order
```

#### C. Ship from Stock (Skip Production)

For MTS orders, the fulfillment flow is simpler:

```
SO Created → Allocate from FG Inventory → Pack → Ship → Consume
```

No production order needed.

---

## 🟢 ENHANCEMENT #2: Partial QC Pass with Scrap Tracking

### Current State

| Scenario | Current Behavior | Correct Behavior |
|----------|-----------------|------------------|
| 10 printed, 10 good | `pass_qc` ✓ | ✓ |
| 10 printed, 0 good | `fail_qc` ✓ | ✓ |
| 10 printed, 8 good, 2 bad | ??? | Need partial pass |

### Solution: Modify `pass_qc` to Accept Quantities

```python
class PassQCRequest(BaseModel):
    """Request to pass QC with quantity tracking"""
    qty_passed: Optional[int] = None  # None = all passed
    qty_failed: Optional[int] = None  # Scrap count
    failure_reason: Optional[str] = None  # Reason for failures
    reprint_failures: bool = True  # Auto-create reprint for failed qty
    qc_notes: Optional[str] = None


@router.post("/queue/{production_order_id}/pass-qc")
async def pass_quality_check(
    production_order_id: int,
    request: PassQCRequest = PassQCRequest(),
    db: Session = Depends(get_db),
):
    """
    Mark order as passed QC with optional partial pass.
    
    If qty_passed < ordered quantity, records scrap and optionally creates reprint.
    """
    po = db.query(ProductionOrder).filter(ProductionOrder.id == production_order_id).first()
    
    if not po:
        raise HTTPException(status_code=404, detail="Production order not found")
    
    if po.status != "printed":
        raise HTTPException(status_code=400, detail=f"Cannot QC order with status '{po.status}'")
    
    ordered_qty = int(po.quantity)
    
    # Determine quantities
    if request.qty_passed is not None:
        qty_passed = request.qty_passed
        qty_failed = request.qty_failed or (ordered_qty - qty_passed)
    elif request.qty_failed is not None:
        qty_failed = request.qty_failed
        qty_passed = ordered_qty - qty_failed
    else:
        # Default: all passed
        qty_passed = ordered_qty
        qty_failed = 0
    
    # Validate
    if qty_passed + qty_failed > ordered_qty:
        raise HTTPException(
            status_code=400,
            detail=f"qty_passed ({qty_passed}) + qty_failed ({qty_failed}) exceeds ordered ({ordered_qty})"
        )
    
    # Update production order
    po.status = "completed"
    po.finish_date = datetime.utcnow()
    
    notes_entry = f"[{datetime.utcnow().isoformat()}] QC Complete: {qty_passed} passed"
    if qty_failed > 0:
        notes_entry += f", {qty_failed} failed"
        if request.failure_reason:
            notes_entry += f" ({request.failure_reason})"
    if request.qc_notes:
        notes_entry += f" - {request.qc_notes}"
    po.notes = (po.notes + "\n" if po.notes else "") + notes_entry
    
    # =========================================================================
    # SCRAP TRACKING - Record failed parts
    # =========================================================================
    scrap_recorded = None
    if qty_failed > 0:
        # Get finished goods inventory (should exist from complete_print)
        fg_inventory = db.query(Inventory).filter(
            Inventory.product_id == po.product_id
        ).first()
        
        if fg_inventory:
            # Decrement the failed parts from FG inventory
            # (They were added in complete_print but now we know they're scrap)
            fg_inventory.on_hand_quantity = Decimal(str(
                max(0, float(fg_inventory.on_hand_quantity) - qty_failed)
            ))
            fg_inventory.available_quantity = (
                fg_inventory.on_hand_quantity - fg_inventory.allocated_quantity
            )
        
        # Get scrap location
        scrap_location = db.query(InventoryLocation).filter(
            InventoryLocation.code == "SCRAP"
        ).first()
        scrap_location_id = scrap_location.id if scrap_location else (fg_inventory.location_id if fg_inventory else 1)
        
        # Create scrap transaction
        scrap_txn = InventoryTransaction(
            product_id=po.product_id,
            location_id=scrap_location_id,
            transaction_type="scrap",
            reference_type="production_order",
            reference_id=po.id,
            quantity=Decimal(str(-qty_failed)),
            notes=f"QC scrap from {po.code}: {qty_failed} parts failed ({request.failure_reason or 'unspecified'})",
            created_by="system",
        )
        db.add(scrap_txn)
        
        scrap_recorded = {
            "quantity_scrapped": qty_failed,
            "reason": request.failure_reason,
            "scrap_rate": round(qty_failed / ordered_qty * 100, 1),
        }
    
    # =========================================================================
    # REPRINT FOR SHORTFALL
    # =========================================================================
    reprint_order = None
    shortfall = ordered_qty - qty_passed
    
    if shortfall > 0 and request.reprint_failures:
        # Create reprint PO for just the failed quantity
        reprint_code = generate_production_order_code(db)
        
        reprint_po = ProductionOrder(
            code=reprint_code,
            product_id=po.product_id,
            bom_id=po.bom_id,
            sales_order_id=po.sales_order_id,  # Link to same SO
            quantity=shortfall,
            status="scheduled",
            priority="high",  # Reprints are high priority
            estimated_time_minutes=int((po.estimated_time_minutes or 0) * shortfall / ordered_qty),
            notes=f"REPRINT of {po.code}: {shortfall} parts failed QC ({request.failure_reason or 'unspecified'})",
        )
        db.add(reprint_po)
        db.flush()
        
        reprint_order = {
            "id": reprint_po.id,
            "code": reprint_po.code,
            "quantity": shortfall,
        }
    
    # =========================================================================
    # UPDATE SALES ORDER STATUS
    # =========================================================================
    sales_order_update = None
    
    # Find sales order (via quote or direct link)
    sales_order = None
    if po.sales_order_id:
        sales_order = db.query(SalesOrder).filter(SalesOrder.id == po.sales_order_id).first()
    else:
        quote = db.query(Quote).filter(Quote.product_id == po.product_id).first()
        if quote:
            sales_order = db.query(SalesOrder).filter(SalesOrder.quote_id == quote.id).first()
    
    if sales_order:
        if qty_passed >= ordered_qty:
            # Full pass - ready to ship
            sales_order.status = "ready_to_ship"
            sales_order_update = "ready_to_ship"
        elif qty_passed > 0 and reprint_order:
            # Partial pass with reprint pending
            sales_order.status = "partial_qc"  # New status
            sales_order_update = "partial_qc (reprint scheduled)"
        elif qty_passed > 0:
            # Partial pass, no reprint (ship what we have?)
            sales_order.status = "ready_to_ship"
            sales_order_update = "ready_to_ship (partial fulfillment)"
        else:
            # Complete failure
            sales_order.status = "qc_failed"
            sales_order_update = "qc_failed"
    
    db.commit()
    
    return {
        "success": True,
        "production_order_id": po.id,
        "status": po.status,
        "quantities": {
            "ordered": ordered_qty,
            "passed": qty_passed,
            "failed": qty_failed,
            "shortfall": shortfall,
        },
        "scrap_recorded": scrap_recorded,
        "reprint_order": reprint_order,
        "sales_order_status": sales_order_update,
        "message": (
            f"QC complete for {po.code}: {qty_passed}/{ordered_qty} passed" +
            (f". Reprint {reprint_order['code']} created for {shortfall}" if reprint_order else "")
        ),
    }
```

### QC Flow Decision Tree

```
                        ┌─────────────────────────┐
                        │    complete_print()     │
                        │  Records initial good/  │
                        │  bad from print run     │
                        └───────────┬─────────────┘
                                    │
                                    ▼
                        ┌─────────────────────────┐
                        │       QC Station        │
                        │  Visual/functional      │
                        │  inspection             │
                        └───────────┬─────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌───────────┐   ┌───────────┐   ┌───────────┐
            │ All Pass  │   │  Partial  │   │ All Fail  │
            │           │   │           │   │           │
            │ pass_qc() │   │ pass_qc() │   │ fail_qc() │
            │ qty=all   │   │ qty<all   │   │           │
            └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
                  │               │               │
                  ▼               ▼               ▼
            Ready to Ship   Scrap bad +      Scrap all +
                           Reprint short    Reprint all
```

### Important: Coordination with `complete_print`

The `complete_print` endpoint already tracks `qty_good` and `qty_bad` from the print run itself (adhesion failures, layer shifts, etc. caught immediately).

QC happens AFTER and catches things like:
- Surface defects
- Dimensional issues
- Color mismatch
- Functional failures

So the flow is:

```
Print Run: 12 attempted → 10 good, 2 immediate scrap (adhesion)
           ↓
           complete_print(qty_good=10, qty_bad=2)
           ↓
           10 go to QC
           ↓
QC:        8 pass, 2 fail (surface defects)
           ↓
           pass_qc(qty_passed=8, qty_failed=2)
           ↓
           8 ready to ship
           2 scrapped
           2 reprint ordered (if needed)
```

**Total scrap**: 2 (print) + 2 (QC) = 4 parts
**Total good**: 8 parts
**Reprint needed**: 2 parts (if order was for 10)

---

## Updated Testing Checklist

### MTS Flow
- [ ] Create production order without sales order
- [ ] Start production → materials reserved
- [ ] Complete print → finished goods added to inventory
- [ ] Pass QC → FG available for sale
- [ ] Create sales order for MTS product → allocates from FG inventory
- [ ] Ship order → consumes allocated FG inventory

### Partial QC Flow
- [ ] Print 10, all good from print
- [ ] QC: 8 pass, 2 fail
- [ ] Scrap transaction created for 2
- [ ] FG inventory decremented by 2
- [ ] Reprint PO created for 2
- [ ] Sales order shows "partial_qc" status
- [ ] Complete reprint, pass QC
- [ ] Sales order now "ready_to_ship"

---

## 🟢 ENHANCEMENT #3: Reprint Tracking & Traceability

### Problem
When a reprint is created, there's no link back to the original PO. You can't answer:
- How many reprints did this order require?
- What was the total material consumed including reprints?
- What's our reprint rate by product/material/printer?

### Solution: Add Parent PO Reference

#### Schema Change

```sql
ALTER TABLE production_orders ADD COLUMN parent_production_order_id INTEGER REFERENCES production_orders(id);
ALTER TABLE production_orders ADD COLUMN reprint_reason VARCHAR(100);
ALTER TABLE production_orders ADD COLUMN reprint_sequence INTEGER DEFAULT 0;  -- 0 = original, 1 = first reprint, etc.
```

#### Model Update

```python
# In app/models/production_order.py

class ProductionOrder(Base):
    # ... existing fields ...
    
    # Reprint tracking
    parent_production_order_id = Column(Integer, ForeignKey('production_orders.id'), nullable=True)
    reprint_reason = Column(String(100), nullable=True)
    reprint_sequence = Column(Integer, default=0)  # 0 = original
    
    # Relationships
    parent_order = relationship("ProductionOrder", remote_side=[id], backref="reprints")
```

#### Updated Reprint Creation

```python
# In pass_qc or fail_qc when creating reprint:

def create_reprint_order(
    original_po: ProductionOrder,
    quantity: int,
    reason: str,
    db: Session
) -> ProductionOrder:
    """Create a reprint PO linked to the original."""
    
    # Calculate reprint sequence
    existing_reprints = db.query(ProductionOrder).filter(
        or_(
            ProductionOrder.parent_production_order_id == original_po.id,
            ProductionOrder.parent_production_order_id == original_po.parent_production_order_id
        )
    ).count()
    
    # Find root PO (in case this is a reprint of a reprint)
    root_po_id = original_po.parent_production_order_id or original_po.id
    
    reprint_code = generate_production_order_code(db)
    
    reprint_po = ProductionOrder(
        code=reprint_code,
        product_id=original_po.product_id,
        bom_id=original_po.bom_id,
        sales_order_id=original_po.sales_order_id,
        quantity=quantity,
        status="scheduled",
        priority="high",
        # Reprint tracking
        parent_production_order_id=root_po_id,  # Always link to root, not intermediate
        reprint_reason=reason,
        reprint_sequence=existing_reprints + 1,
        # Time estimate proportional to quantity
        estimated_time_minutes=int(
            (original_po.estimated_time_minutes or 60) * quantity / float(original_po.quantity)
        ),
        notes=f"REPRINT #{existing_reprints + 1} of {original_po.code}: {quantity} units ({reason})",
    )
    
    db.add(reprint_po)
    return reprint_po
```

#### Reprint Chain Query

```python
@router.get("/queue/{production_order_id}/reprint-history")
async def get_reprint_history(
    production_order_id: int,
    db: Session = Depends(get_db),
):
    """Get full reprint chain for a production order."""
    
    po = db.query(ProductionOrder).filter(ProductionOrder.id == production_order_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Production order not found")
    
    # Find root PO
    root_id = po.parent_production_order_id or po.id
    root_po = db.query(ProductionOrder).filter(ProductionOrder.id == root_id).first()
    
    # Get all related POs
    all_pos = db.query(ProductionOrder).filter(
        or_(
            ProductionOrder.id == root_id,
            ProductionOrder.parent_production_order_id == root_id
        )
    ).order_by(ProductionOrder.reprint_sequence).all()
    
    # Calculate totals
    total_ordered = sum(float(p.quantity) for p in all_pos)
    total_completed = sum(
        float(p.quantity) for p in all_pos 
        if p.status == "completed"
    )
    
    # Get scrap transactions for all POs
    po_ids = [p.id for p in all_pos]
    scrap_txns = db.query(InventoryTransaction).filter(
        InventoryTransaction.reference_type == "production_order",
        InventoryTransaction.reference_id.in_(po_ids),
        InventoryTransaction.transaction_type == "scrap"
    ).all()
    total_scrapped = sum(abs(float(t.quantity)) for t in scrap_txns)
    
    return {
        "root_order": {
            "id": root_po.id,
            "code": root_po.code,
            "original_quantity": int(root_po.quantity),
        },
        "chain": [
            {
                "id": p.id,
                "code": p.code,
                "sequence": p.reprint_sequence,
                "quantity": int(p.quantity),
                "status": p.status,
                "reprint_reason": p.reprint_reason,
                "created_at": p.created_at.isoformat(),
            }
            for p in all_pos
        ],
        "totals": {
            "orders_in_chain": len(all_pos),
            "total_quantity_ordered": int(total_ordered),
            "total_completed": int(total_completed),
            "total_scrapped": int(total_scrapped),
            "effective_yield": round(total_completed / total_ordered * 100, 1) if total_ordered > 0 else 0,
        },
    }
```

---

## 🟢 ENHANCEMENT #4: Scrap Reason Codes

### Problem
Current scrap tracking uses free-text notes. Can't:
- Aggregate scrap by reason
- Identify systemic issues
- Track improvement over time

### Solution: Standardized Scrap Codes

#### Schema

```sql
CREATE TABLE scrap_reason_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,  -- 'print_failure', 'qc_failure', 'handling', 'other'
    description TEXT,
    corrective_action TEXT,  -- Suggested fix
    active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 100
);

-- Seed data for 3D printing
INSERT INTO scrap_reason_codes (code, name, category, description, corrective_action) VALUES
-- Print Failures (detected during print or immediately after)
('ADH', 'Adhesion Failure', 'print_failure', 'Part detached from bed during print', 'Clean bed, adjust Z-offset, check bed temp'),
('WAR', 'Warping', 'print_failure', 'Part lifted/curled at corners', 'Add brim, increase bed temp, use enclosure'),
('LAY', 'Layer Shift', 'print_failure', 'Layers misaligned mid-print', 'Check belt tension, reduce acceleration'),
('CLG', 'Clog/Underextrusion', 'print_failure', 'Missing material, gaps in layers', 'Clean nozzle, check filament path, reduce retraction'),
('STR', 'Stringing', 'print_failure', 'Excessive strings between parts', 'Tune retraction, reduce temp'),
('BLB', 'Blob/Zit', 'print_failure', 'Excess material deposits on surface', 'Tune pressure advance, reduce flow'),
('SPG', 'Spaghetti', 'print_failure', 'Print completely failed, tangled mess', 'Investigate root cause, check first layer'),

-- QC Failures (detected during inspection)
('DIM', 'Dimensional Out of Spec', 'qc_failure', 'Measurements outside tolerance', 'Calibrate printer, adjust flow rate'),
('SRF', 'Surface Defect', 'qc_failure', 'Scratches, marks, rough surface', 'Check nozzle condition, adjust print settings'),
('CLR', 'Color Mismatch', 'qc_failure', 'Color doesn''t match specification', 'Verify correct filament loaded'),
('INC', 'Incomplete Features', 'qc_failure', 'Missing holes, threads, or details', 'Check model orientation, support settings'),
('WEK', 'Weak/Brittle', 'qc_failure', 'Part breaks under expected load', 'Increase infill, check layer adhesion'),
('VIS', 'Visual Defect', 'qc_failure', 'General appearance not acceptable', 'Operator discretion'),

-- Handling Failures
('DRP', 'Dropped/Damaged', 'handling', 'Part damaged during handling', 'Improve handling procedures'),
('PCK', 'Packaging Damage', 'handling', 'Damaged during packing', 'Review packaging process'),

-- Other
('CUS', 'Customer Rejection', 'other', 'Customer returned/rejected part', 'Review with customer'),
('OTH', 'Other', 'other', 'See notes for details', 'Document in notes');
```

#### Model

```python
# app/models/scrap.py

class ScrapReasonCode(Base):
    __tablename__ = "scrap_reason_codes"
    
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # print_failure, qc_failure, handling, other
    description = Column(Text)
    corrective_action = Column(Text)
    active = Column(Boolean, default=True)
    display_order = Column(Integer, default=100)
```

#### Updated Inventory Transaction

```sql
ALTER TABLE inventory_transactions ADD COLUMN scrap_reason_code VARCHAR(20) REFERENCES scrap_reason_codes(code);
```

```python
# Updated InventoryTransaction model
class InventoryTransaction(Base):
    # ... existing fields ...
    scrap_reason_code = Column(String(20), ForeignKey('scrap_reason_codes.code'), nullable=True)
    
    scrap_reason = relationship("ScrapReasonCode")
```

#### Usage in QC

```python
class PassQCRequest(BaseModel):
    qty_passed: Optional[int] = None
    qty_failed: Optional[int] = None
    scrap_reason_code: Optional[str] = None  # Use code like 'SRF', 'DIM'
    failure_notes: Optional[str] = None  # Additional details
    reprint_failures: bool = True
    qc_notes: Optional[str] = None


# In pass_qc:
if qty_failed > 0:
    scrap_txn = InventoryTransaction(
        product_id=po.product_id,
        location_id=scrap_location_id,
        transaction_type="scrap",
        reference_type="production_order",
        reference_id=po.id,
        quantity=Decimal(str(-qty_failed)),
        scrap_reason_code=request.scrap_reason_code,  # Linked to code table
        notes=request.failure_notes or f"QC scrap: {request.scrap_reason_code}",
        created_by="system",
    )
```

#### Scrap Reason Endpoint

```python
@router.get("/scrap-reasons")
async def get_scrap_reasons(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get available scrap reason codes for dropdowns."""
    query = db.query(ScrapReasonCode).filter(ScrapReasonCode.active == True)
    
    if category:
        query = query.filter(ScrapReasonCode.category == category)
    
    reasons = query.order_by(ScrapReasonCode.display_order).all()
    
    return {
        "reasons": [
            {
                "code": r.code,
                "name": r.name,
                "category": r.category,
                "description": r.description,
                "corrective_action": r.corrective_action,
            }
            for r in reasons
        ]
    }
```

---

## 🟢 ENHANCEMENT #5: Yield Reporting & Analytics

### Key Metrics

| Metric | Formula | Purpose |
|--------|---------|---------|
| **First Pass Yield (FPY)** | Good on first try / Total started | Overall process capability |
| **Rolled Throughput Yield (RTY)** | FPY₁ × FPY₂ × ... | Multi-step yield |
| **Scrap Rate** | Scrapped / Total produced | Material waste |
| **Reprint Rate** | Orders with reprints / Total orders | Process reliability |
| **OEE** | Availability × Performance × Quality | Overall equipment effectiveness |

### Database Views

```sql
-- Production Order Summary View
CREATE OR REPLACE VIEW v_production_order_summary AS
SELECT 
    po.id,
    po.code,
    po.product_id,
    p.sku as product_sku,
    p.name as product_name,
    po.quantity as ordered_qty,
    po.status,
    po.priority,
    po.parent_production_order_id,
    po.reprint_sequence,
    po.reprint_reason,
    po.created_at,
    po.start_date,
    po.finish_date,
    po.estimated_time_minutes,
    po.actual_time_minutes,
    -- Calculate good/bad from transactions
    COALESCE((
        SELECT SUM(ABS(quantity)) 
        FROM inventory_transactions 
        WHERE reference_type = 'production_order' 
        AND reference_id = po.id 
        AND transaction_type = 'receipt'
    ), 0) as qty_good,
    COALESCE((
        SELECT SUM(ABS(quantity)) 
        FROM inventory_transactions 
        WHERE reference_type = 'production_order' 
        AND reference_id = po.id 
        AND transaction_type = 'scrap'
    ), 0) as qty_scrapped,
    -- Reprint count
    (SELECT COUNT(*) FROM production_orders WHERE parent_production_order_id = po.id) as reprint_count
FROM production_orders po
LEFT JOIN products p ON po.product_id = p.id;


-- Daily Yield Report View
CREATE OR REPLACE VIEW v_daily_yield AS
SELECT 
    DATE(finish_date) as production_date,
    COUNT(DISTINCT id) as orders_completed,
    SUM(ordered_qty) as total_ordered,
    SUM(qty_good) as total_good,
    SUM(qty_scrapped) as total_scrapped,
    ROUND(SUM(qty_good)::numeric / NULLIF(SUM(ordered_qty), 0) * 100, 2) as yield_pct,
    ROUND(SUM(qty_scrapped)::numeric / NULLIF(SUM(ordered_qty + qty_scrapped), 0) * 100, 2) as scrap_rate_pct,
    COUNT(DISTINCT CASE WHEN reprint_count > 0 THEN id END) as orders_with_reprints,
    ROUND(COUNT(DISTINCT CASE WHEN reprint_count > 0 THEN id END)::numeric / NULLIF(COUNT(DISTINCT id), 0) * 100, 2) as reprint_rate_pct
FROM v_production_order_summary
WHERE status = 'completed'
GROUP BY DATE(finish_date)
ORDER BY production_date DESC;


-- Scrap by Reason View
CREATE OR REPLACE VIEW v_scrap_by_reason AS
SELECT 
    DATE(it.created_at) as scrap_date,
    src.code as reason_code,
    src.name as reason_name,
    src.category,
    COUNT(*) as occurrence_count,
    SUM(ABS(it.quantity)) as total_qty_scrapped,
    src.corrective_action
FROM inventory_transactions it
JOIN scrap_reason_codes src ON it.scrap_reason_code = src.code
WHERE it.transaction_type = 'scrap'
GROUP BY DATE(it.created_at), src.code, src.name, src.category, src.corrective_action
ORDER BY scrap_date DESC, total_qty_scrapped DESC;


-- Yield by Material View
CREATE OR REPLACE VIEW v_yield_by_material AS
SELECT 
    q.material_type,
    q.color,
    COUNT(DISTINCT pos.id) as orders_completed,
    SUM(pos.ordered_qty) as total_ordered,
    SUM(pos.qty_good) as total_good,
    SUM(pos.qty_scrapped) as total_scrapped,
    ROUND(SUM(pos.qty_good)::numeric / NULLIF(SUM(pos.ordered_qty), 0) * 100, 2) as yield_pct
FROM v_production_order_summary pos
JOIN quotes q ON pos.product_id = q.product_id
WHERE pos.status = 'completed'
GROUP BY q.material_type, q.color
ORDER BY yield_pct ASC;  -- Worst performers first


-- Yield by Printer View (requires print_jobs linkage)
CREATE OR REPLACE VIEW v_yield_by_printer AS
SELECT 
    pr.code as printer_code,
    pr.name as printer_name,
    COUNT(DISTINCT pj.production_order_id) as orders_completed,
    SUM(pos.ordered_qty) as total_ordered,
    SUM(pos.qty_good) as total_good,
    SUM(pos.qty_scrapped) as total_scrapped,
    ROUND(SUM(pos.qty_good)::numeric / NULLIF(SUM(pos.ordered_qty), 0) * 100, 2) as yield_pct,
    ROUND(AVG(pos.actual_time_minutes), 0) as avg_time_minutes
FROM print_jobs pj
JOIN printers pr ON pj.printer_id = pr.id
JOIN v_production_order_summary pos ON pj.production_order_id = pos.id
WHERE pos.status = 'completed'
GROUP BY pr.code, pr.name
ORDER BY yield_pct ASC;
```

### API Endpoints

```python
@router.get("/reports/yield-summary")
async def get_yield_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Get yield summary for date range."""
    
    # Default to last 30 days
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Use the view
    result = db.execute(text("""
        SELECT 
            SUM(total_ordered) as total_ordered,
            SUM(total_good) as total_good,
            SUM(total_scrapped) as total_scrapped,
            SUM(orders_completed) as orders_completed,
            SUM(orders_with_reprints) as orders_with_reprints
        FROM v_daily_yield
        WHERE production_date BETWEEN :start AND :end
    """), {"start": start_date, "end": end_date}).fetchone()
    
    total_ordered = result.total_ordered or 0
    total_good = result.total_good or 0
    total_scrapped = result.total_scrapped or 0
    orders_completed = result.orders_completed or 0
    orders_with_reprints = result.orders_with_reprints or 0
    
    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "summary": {
            "orders_completed": orders_completed,
            "total_parts_ordered": total_ordered,
            "total_parts_good": total_good,
            "total_parts_scrapped": total_scrapped,
        },
        "metrics": {
            "first_pass_yield_pct": round(total_good / total_ordered * 100, 2) if total_ordered > 0 else 0,
            "scrap_rate_pct": round(total_scrapped / (total_ordered + total_scrapped) * 100, 2) if (total_ordered + total_scrapped) > 0 else 0,
            "reprint_rate_pct": round(orders_with_reprints / orders_completed * 100, 2) if orders_completed > 0 else 0,
        },
    }


@router.get("/reports/scrap-pareto")
async def get_scrap_pareto(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Get Pareto analysis of scrap reasons."""
    
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    result = db.execute(text("""
        SELECT 
            reason_code,
            reason_name,
            category,
            SUM(total_qty_scrapped) as qty,
            corrective_action
        FROM v_scrap_by_reason
        WHERE scrap_date BETWEEN :start AND :end
        GROUP BY reason_code, reason_name, category, corrective_action
        ORDER BY qty DESC
        LIMIT :limit
    """), {"start": start_date, "end": end_date, "limit": limit}).fetchall()
    
    total_scrap = sum(r.qty for r in result)
    
    pareto = []
    cumulative = 0
    for r in result:
        cumulative += r.qty
        pareto.append({
            "reason_code": r.reason_code,
            "reason_name": r.reason_name,
            "category": r.category,
            "quantity": int(r.qty),
            "percentage": round(r.qty / total_scrap * 100, 1) if total_scrap > 0 else 0,
            "cumulative_pct": round(cumulative / total_scrap * 100, 1) if total_scrap > 0 else 0,
            "corrective_action": r.corrective_action,
        })
    
    return {
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "total_scrap": int(total_scrap),
        "pareto": pareto,
    }
```

---

## 🟢 ENHANCEMENT #6: Purchasing Module

### Overview

The purchasing module handles:
1. **Purchase Orders** - Order materials from vendors
2. **Receiving** - Record incoming materials, update inventory
3. **Vendor Management** - Track suppliers, pricing, lead times
4. **Reorder Triggers** - Auto-create POs when stock is low

### Schema

```sql
-- Vendors
CREATE TABLE vendors (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    contact_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(50),
    address_line1 VARCHAR(200),
    address_line2 VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(20),
    country VARCHAR(50) DEFAULT 'USA',
    payment_terms VARCHAR(50),  -- NET30, NET60, etc.
    notes TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Vendor Items (what each vendor sells and at what price)
CREATE TABLE vendor_items (
    id SERIAL PRIMARY KEY,
    vendor_id INTEGER REFERENCES vendors(id) NOT NULL,
    product_id INTEGER REFERENCES products(id) NOT NULL,
    vendor_sku VARCHAR(100),  -- Vendor's part number
    unit_cost DECIMAL(18,4) NOT NULL,
    min_order_qty DECIMAL(10,2) DEFAULT 1,
    lead_time_days INTEGER,
    is_preferred BOOLEAN DEFAULT FALSE,  -- Preferred vendor for this item
    last_purchase_date DATE,
    last_purchase_price DECIMAL(18,4),
    notes TEXT,
    active BOOLEAN DEFAULT TRUE,
    UNIQUE(vendor_id, product_id)
);

-- Purchase Orders
CREATE TABLE purchase_orders (
    id SERIAL PRIMARY KEY,
    po_number VARCHAR(50) UNIQUE NOT NULL,  -- PUR-2025-001
    vendor_id INTEGER REFERENCES vendors(id) NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',  -- draft, submitted, confirmed, partial, received, cancelled
    order_date DATE,
    expected_date DATE,
    received_date DATE,
    subtotal DECIMAL(18,4),
    tax_amount DECIMAL(18,4),
    shipping_cost DECIMAL(18,4),
    total_amount DECIMAL(18,4),
    payment_status VARCHAR(50) DEFAULT 'unpaid',  -- unpaid, partial, paid
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100)
);

-- Purchase Order Lines
CREATE TABLE purchase_order_lines (
    id SERIAL PRIMARY KEY,
    purchase_order_id INTEGER REFERENCES purchase_orders(id) NOT NULL,
    product_id INTEGER REFERENCES products(id) NOT NULL,
    line_number INTEGER,
    quantity_ordered DECIMAL(18,4) NOT NULL,
    quantity_received DECIMAL(18,4) DEFAULT 0,
    unit_cost DECIMAL(18,4) NOT NULL,
    line_total DECIMAL(18,4),  -- qty * unit_cost
    notes TEXT
);

-- Receiving Records
CREATE TABLE receiving_records (
    id SERIAL PRIMARY KEY,
    purchase_order_id INTEGER REFERENCES purchase_orders(id) NOT NULL,
    receiving_number VARCHAR(50) UNIQUE NOT NULL,  -- RCV-2025-001
    received_date TIMESTAMP DEFAULT NOW(),
    received_by VARCHAR(100),
    notes TEXT
);

-- Receiving Lines
CREATE TABLE receiving_lines (
    id SERIAL PRIMARY KEY,
    receiving_record_id INTEGER REFERENCES receiving_records(id) NOT NULL,
    purchase_order_line_id INTEGER REFERENCES purchase_order_lines(id) NOT NULL,
    product_id INTEGER REFERENCES products(id) NOT NULL,
    quantity_received DECIMAL(18,4) NOT NULL,
    location_id INTEGER REFERENCES inventory_locations(id),
    lot_number VARCHAR(100),
    notes TEXT
);
```

### Models

```python
# app/models/purchasing.py

class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    contact_name = Column(String(100))
    email = Column(String(100))
    phone = Column(String(50))
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state = Column(String(50))
    zip = Column(String(20))
    country = Column(String(50), default="USA")
    payment_terms = Column(String(50))
    notes = Column(Text)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    items = relationship("VendorItem", back_populates="vendor")
    purchase_orders = relationship("PurchaseOrder", back_populates="vendor")


class VendorItem(Base):
    __tablename__ = "vendor_items"
    
    id = Column(Integer, primary_key=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    vendor_sku = Column(String(100))
    unit_cost = Column(Numeric(18, 4), nullable=False)
    min_order_qty = Column(Numeric(10, 2), default=1)
    lead_time_days = Column(Integer)
    is_preferred = Column(Boolean, default=False)
    last_purchase_date = Column(Date)
    last_purchase_price = Column(Numeric(18, 4))
    notes = Column(Text)
    active = Column(Boolean, default=True)
    
    vendor = relationship("Vendor", back_populates="items")
    product = relationship("Product")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    
    id = Column(Integer, primary_key=True)
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    status = Column(String(50), default="draft")
    order_date = Column(Date)
    expected_date = Column(Date)
    received_date = Column(Date)
    subtotal = Column(Numeric(18, 4))
    tax_amount = Column(Numeric(18, 4))
    shipping_cost = Column(Numeric(18, 4))
    total_amount = Column(Numeric(18, 4))
    payment_status = Column(String(50), default="unpaid")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    
    vendor = relationship("Vendor", back_populates="purchase_orders")
    lines = relationship("PurchaseOrderLine", back_populates="purchase_order", cascade="all, delete-orphan")


class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"
    
    id = Column(Integer, primary_key=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    line_number = Column(Integer)
    quantity_ordered = Column(Numeric(18, 4), nullable=False)
    quantity_received = Column(Numeric(18, 4), default=0)
    unit_cost = Column(Numeric(18, 4), nullable=False)
    line_total = Column(Numeric(18, 4))
    notes = Column(Text)
    
    purchase_order = relationship("PurchaseOrder", back_populates="lines")
    product = relationship("Product")
```

### Key Endpoints

```python
# app/api/v1/endpoints/admin/purchasing.py

@router.post("/purchase-orders")
async def create_purchase_order(request: CreatePORequest, db: Session = Depends(get_db)):
    """Create a new purchase order."""
    pass


@router.post("/purchase-orders/{po_id}/receive")
async def receive_purchase_order(
    po_id: int,
    request: ReceivePORequest,
    db: Session = Depends(get_db),
):
    """
    Receive items against a purchase order.
    
    This is the critical integration point:
    1. Updates PO line quantities received
    2. Creates Inventory records/updates quantities
    3. Syncs MaterialInventory for raw materials
    4. Creates accounting journal entries
    """
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    # Create receiving record
    rcv_number = generate_receiving_number(db)
    receiving = ReceivingRecord(
        purchase_order_id=po.id,
        receiving_number=rcv_number,
        received_by=request.received_by,
        notes=request.notes,
    )
    db.add(receiving)
    db.flush()
    
    received_lines = []
    
    for line_rcv in request.lines:
        po_line = db.query(PurchaseOrderLine).filter(
            PurchaseOrderLine.id == line_rcv.po_line_id
        ).first()
        
        if not po_line:
            continue
        
        # Update PO line received qty
        po_line.quantity_received = (po_line.quantity_received or 0) + line_rcv.quantity
        
        # Create receiving line
        rcv_line = ReceivingLine(
            receiving_record_id=receiving.id,
            purchase_order_line_id=po_line.id,
            product_id=po_line.product_id,
            quantity_received=line_rcv.quantity,
            location_id=line_rcv.location_id,
            lot_number=line_rcv.lot_number,
        )
        db.add(rcv_line)
        
        # =====================================================================
        # UPDATE INVENTORY
        # =====================================================================
        product = db.query(Product).filter(Product.id == po_line.product_id).first()
        
        # Get or create Inventory record
        inv = db.query(Inventory).filter(
            Inventory.product_id == po_line.product_id,
            Inventory.location_id == line_rcv.location_id
        ).first()
        
        if not inv:
            inv = Inventory(
                product_id=po_line.product_id,
                location_id=line_rcv.location_id,
                on_hand_quantity=Decimal("0"),
                allocated_quantity=Decimal("0"),
                available_quantity=Decimal("0"),
            )
            db.add(inv)
            db.flush()
        
        # Update quantities
        inv.on_hand_quantity += Decimal(str(line_rcv.quantity))
        inv.available_quantity = inv.on_hand_quantity - inv.allocated_quantity
        
        # Create receipt transaction
        txn = InventoryTransaction(
            product_id=po_line.product_id,
            location_id=line_rcv.location_id,
            transaction_type="receipt",
            reference_type="purchase_order",
            reference_id=po.id,
            quantity=Decimal(str(line_rcv.quantity)),
            cost_per_unit=po_line.unit_cost,
            lot_number=line_rcv.lot_number,
            notes=f"Received on {rcv_number} from PO {po.po_number}",
            created_by=request.received_by,
        )
        db.add(txn)
        
        # =====================================================================
        # SYNC MATERIAL INVENTORY (for raw materials)
        # =====================================================================
        if product and product.is_raw_material:
            mat_inv = db.query(MaterialInventory).filter(
                MaterialInventory.product_id == product.id
            ).first()
            
            if mat_inv:
                mat_inv.quantity_kg = inv.on_hand_quantity
                mat_inv.in_stock = inv.on_hand_quantity > 0
                mat_inv.last_purchase_date = date.today()
                mat_inv.last_purchase_price = po_line.unit_cost
        
        # =====================================================================
        # CREATE ACCOUNTING JOURNAL ENTRY
        # =====================================================================
        # Debit: Inventory Asset
        # Credit: Accounts Payable (or Cash if paid)
        journal_entry = create_journal_entry(
            entry_type="purchase_receipt",
            reference_type="purchase_order",
            reference_id=po.id,
            lines=[
                JournalLine(account="inventory_asset", debit=float(line_rcv.quantity * po_line.unit_cost)),
                JournalLine(account="accounts_payable", credit=float(line_rcv.quantity * po_line.unit_cost)),
            ],
            memo=f"Receipt of {product.sku} from PO {po.po_number}",
            db=db
        )
        
        received_lines.append({
            "product_sku": product.sku if product else "N/A",
            "quantity": float(line_rcv.quantity),
            "location": line_rcv.location_id,
            "new_on_hand": float(inv.on_hand_quantity),
        })
    
    # Update PO status
    all_lines = db.query(PurchaseOrderLine).filter(PurchaseOrderLine.purchase_order_id == po.id).all()
    all_received = all(l.quantity_received >= l.quantity_ordered for l in all_lines)
    any_received = any((l.quantity_received or 0) > 0 for l in all_lines)
    
    if all_received:
        po.status = "received"
        po.received_date = date.today()
    elif any_received:
        po.status = "partial"
    
    db.commit()
    
    return {
        "success": True,
        "receiving_number": rcv_number,
        "lines_received": received_lines,
        "po_status": po.status,
    }


@router.get("/reorder-suggestions")
async def get_reorder_suggestions(db: Session = Depends(get_db)):
    """
    Get list of items below reorder point.
    
    Combines MaterialInventory (for filaments) and Inventory (for other items).
    """
    suggestions = []
    
    # Check MaterialInventory for filaments
    low_materials = db.query(MaterialInventory).filter(
        MaterialInventory.active == True,
        MaterialInventory.quantity_kg <= MaterialInventory.reorder_point_kg
    ).all()
    
    for mat in low_materials:
        # Find preferred vendor
        vendor_item = db.query(VendorItem).filter(
            VendorItem.product_id == mat.product_id,
            VendorItem.is_preferred == True,
            VendorItem.active == True
        ).first()
        
        suggestions.append({
            "type": "material",
            "product_id": mat.product_id,
            "sku": mat.sku,
            "name": mat.display_name,
            "current_qty": float(mat.quantity_kg),
            "reorder_point": float(mat.reorder_point_kg),
            "suggested_qty": float(mat.reorder_point_kg) * 2,  # Order 2x reorder point
            "unit": "kg",
            "preferred_vendor": {
                "id": vendor_item.vendor.id,
                "name": vendor_item.vendor.name,
                "unit_cost": float(vendor_item.unit_cost),
                "lead_time_days": vendor_item.lead_time_days,
            } if vendor_item else None,
        })
    
    return {"suggestions": suggestions, "count": len(suggestions)}
```

---

## 🟢 ENHANCEMENT #7: Accounting Journal Entries

### Overview

Every inventory movement should create corresponding accounting entries. This enables:
- Accurate COGS calculation
- Inventory valuation
- Financial reporting
- Audit trail

### Standard Journal Entries for Manufacturing

| Event | Debit | Credit |
|-------|-------|--------|
| **Purchase materials** | Inventory Asset | Accounts Payable |
| **Pay vendor** | Accounts Payable | Cash |
| **Issue materials to production** | WIP (Work in Progress) | Inventory Asset |
| **Complete production** | Finished Goods | WIP |
| **Record scrap** | Scrap Expense | WIP |
| **Sell product** | COGS | Finished Goods |
| **Record revenue** | Accounts Receivable | Revenue |
| **Collect payment** | Cash | Accounts Receivable |

### Schema

```sql
-- Chart of Accounts
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- asset, liability, equity, revenue, expense
    subtype VARCHAR(50),  -- current_asset, fixed_asset, cogs, etc.
    parent_id INTEGER REFERENCES accounts(id),
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Default accounts for manufacturing
INSERT INTO accounts (code, name, type, subtype) VALUES
('1000', 'Cash', 'asset', 'current_asset'),
('1100', 'Accounts Receivable', 'asset', 'current_asset'),
('1200', 'Inventory - Raw Materials', 'asset', 'current_asset'),
('1210', 'Inventory - WIP', 'asset', 'current_asset'),
('1220', 'Inventory - Finished Goods', 'asset', 'current_asset'),
('2000', 'Accounts Payable', 'liability', 'current_liability'),
('4000', 'Sales Revenue', 'revenue', 'operating'),
('5000', 'Cost of Goods Sold', 'expense', 'cogs'),
('5100', 'Direct Materials', 'expense', 'cogs'),
('5200', 'Direct Labor', 'expense', 'cogs'),
('5300', 'Manufacturing Overhead', 'expense', 'cogs'),
('5400', 'Scrap Expense', 'expense', 'cogs'),
('6000', 'Shipping Expense', 'expense', 'operating');


-- Journal Entries
CREATE TABLE journal_entries (
    id SERIAL PRIMARY KEY,
    entry_number VARCHAR(50) UNIQUE NOT NULL,  -- JE-2025-00001
    entry_date DATE NOT NULL DEFAULT CURRENT_DATE,
    entry_type VARCHAR(50) NOT NULL,  -- purchase_receipt, material_issue, production_complete, sale, etc.
    reference_type VARCHAR(50),  -- purchase_order, production_order, sales_order
    reference_id INTEGER,
    memo TEXT,
    status VARCHAR(20) DEFAULT 'posted',  -- draft, posted, voided
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    posted_at TIMESTAMP,
    voided_at TIMESTAMP
);

-- Journal Entry Lines
CREATE TABLE journal_entry_lines (
    id SERIAL PRIMARY KEY,
    journal_entry_id INTEGER REFERENCES journal_entries(id) NOT NULL,
    account_id INTEGER REFERENCES accounts(id) NOT NULL,
    line_number INTEGER,
    description TEXT,
    debit DECIMAL(18,4) DEFAULT 0,
    credit DECIMAL(18,4) DEFAULT 0,
    -- Dimensional tracking
    product_id INTEGER REFERENCES products(id),
    location_id INTEGER REFERENCES inventory_locations(id),
    production_order_id INTEGER REFERENCES production_orders(id),
    sales_order_id INTEGER REFERENCES sales_orders(id),
    purchase_order_id INTEGER REFERENCES purchase_orders(id)
);

-- Ensure debits = credits
ALTER TABLE journal_entries ADD CONSTRAINT balanced_entry CHECK (
    (SELECT SUM(debit) FROM journal_entry_lines WHERE journal_entry_id = id) =
    (SELECT SUM(credit) FROM journal_entry_lines WHERE journal_entry_id = id)
);
```

### Journal Entry Service

```python
# app/services/accounting_service.py

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import date

from app.models.accounting import JournalEntry, JournalEntryLine, Account


@dataclass
class JournalLine:
    account_code: str  # e.g., "1200" for Raw Materials Inventory
    debit: float = 0
    credit: float = 0
    description: Optional[str] = None
    product_id: Optional[int] = None
    location_id: Optional[int] = None


def generate_entry_number(db: Session) -> str:
    """Generate next journal entry number."""
    year = date.today().year
    last = db.query(JournalEntry).filter(
        JournalEntry.entry_number.like(f"JE-{year}-%")
    ).order_by(JournalEntry.entry_number.desc()).first()
    
    if last:
        last_num = int(last.entry_number.split("-")[2])
        next_num = last_num + 1
    else:
        next_num = 1
    
    return f"JE-{year}-{next_num:05d}"


def create_journal_entry(
    entry_type: str,
    lines: List[JournalLine],
    db: Session,
    reference_type: Optional[str] = None,
    reference_id: Optional[int] = None,
    memo: Optional[str] = None,
    entry_date: Optional[date] = None,
    created_by: str = "system",
) -> JournalEntry:
    """
    Create a balanced journal entry.
    
    Validates that debits = credits before saving.
    """
    total_debits = sum(l.debit for l in lines)
    total_credits = sum(l.credit for l in lines)
    
    if abs(total_debits - total_credits) > 0.01:
        raise ValueError(f"Entry not balanced: debits={total_debits}, credits={total_credits}")
    
    entry = JournalEntry(
        entry_number=generate_entry_number(db),
        entry_date=entry_date or date.today(),
        entry_type=entry_type,
        reference_type=reference_type,
        reference_id=reference_id,
        memo=memo,
        status="posted",
        created_by=created_by,
        posted_at=datetime.utcnow(),
    )
    db.add(entry)
    db.flush()
    
    for i, line in enumerate(lines):
        account = db.query(Account).filter(Account.code == line.account_code).first()
        if not account:
            raise ValueError(f"Account not found: {line.account_code}")
        
        je_line = JournalEntryLine(
            journal_entry_id=entry.id,
            account_id=account.id,
            line_number=i + 1,
            description=line.description,
            debit=Decimal(str(line.debit)) if line.debit else Decimal("0"),
            credit=Decimal(str(line.credit)) if line.credit else Decimal("0"),
            product_id=line.product_id,
            location_id=line.location_id,
        )
        db.add(je_line)
    
    return entry


# ============================================================================
# STANDARD ENTRY TEMPLATES
# ============================================================================

def record_material_purchase(
    product_id: int,
    quantity: Decimal,
    unit_cost: Decimal,
    purchase_order_id: int,
    db: Session,
) -> JournalEntry:
    """Record receipt of purchased materials."""
    total = float(quantity * unit_cost)
    
    return create_journal_entry(
        entry_type="purchase_receipt",
        reference_type="purchase_order",
        reference_id=purchase_order_id,
        memo=f"Material receipt from PO #{purchase_order_id}",
        lines=[
            JournalLine(account_code="1200", debit=total, product_id=product_id),  # Dr Inventory
            JournalLine(account_code="2000", credit=total),  # Cr Accounts Payable
        ],
        db=db
    )


def record_material_issue(
    product_id: int,
    quantity: Decimal,
    unit_cost: Decimal,
    production_order_id: int,
    db: Session,
) -> JournalEntry:
    """Record issue of materials to production (BOM explosion)."""
    total = float(quantity * unit_cost)
    
    return create_journal_entry(
        entry_type="material_issue",
        reference_type="production_order",
        reference_id=production_order_id,
        memo=f"Material issued to PO #{production_order_id}",
        lines=[
            JournalLine(account_code="1210", debit=total),  # Dr WIP
            JournalLine(account_code="1200", credit=total, product_id=product_id),  # Cr Raw Materials
        ],
        db=db
    )


def record_production_complete(
    product_id: int,
    quantity: int,
    unit_cost: Decimal,
    production_order_id: int,
    db: Session,
) -> JournalEntry:
    """Record completion of production (finished goods to inventory)."""
    total = float(quantity * unit_cost)
    
    return create_journal_entry(
        entry_type="production_complete",
        reference_type="production_order",
        reference_id=production_order_id,
        memo=f"Production complete: {quantity} units from PO #{production_order_id}",
        lines=[
            JournalLine(account_code="1220", debit=total, product_id=product_id),  # Dr Finished Goods
            JournalLine(account_code="1210", credit=total),  # Cr WIP
        ],
        db=db
    )


def record_scrap(
    product_id: int,
    quantity: int,
    unit_cost: Decimal,
    production_order_id: int,
    scrap_reason: str,
    db: Session,
) -> JournalEntry:
    """Record production scrap."""
    total = float(quantity * unit_cost)
    
    return create_journal_entry(
        entry_type="scrap",
        reference_type="production_order",
        reference_id=production_order_id,
        memo=f"Scrap from PO #{production_order_id}: {scrap_reason}",
        lines=[
            JournalLine(account_code="5400", debit=total),  # Dr Scrap Expense
            JournalLine(account_code="1210", credit=total),  # Cr WIP
        ],
        db=db
    )


def record_sale(
    product_id: int,
    quantity: int,
    unit_cost: Decimal,
    sale_price: Decimal,
    sales_order_id: int,
    db: Session,
) -> JournalEntry:
    """Record sale and COGS."""
    cogs = float(quantity * unit_cost)
    revenue = float(quantity * sale_price)
    
    return create_journal_entry(
        entry_type="sale",
        reference_type="sales_order",
        reference_id=sales_order_id,
        memo=f"Sale from SO #{sales_order_id}",
        lines=[
            # Revenue side
            JournalLine(account_code="1100", debit=revenue),  # Dr Accounts Receivable
            JournalLine(account_code="4000", credit=revenue),  # Cr Sales Revenue
            # COGS side
            JournalLine(account_code="5000", debit=cogs),  # Dr COGS
            JournalLine(account_code="1220", credit=cogs, product_id=product_id),  # Cr Finished Goods
        ],
        db=db
    )


def record_payment_received(
    amount: Decimal,
    sales_order_id: int,
    payment_method: str,
    db: Session,
) -> JournalEntry:
    """Record customer payment."""
    
    return create_journal_entry(
        entry_type="payment_received",
        reference_type="sales_order",
        reference_id=sales_order_id,
        memo=f"Payment received for SO #{sales_order_id} via {payment_method}",
        lines=[
            JournalLine(account_code="1000", debit=float(amount)),  # Dr Cash
            JournalLine(account_code="1100", credit=float(amount)),  # Cr Accounts Receivable
        ],
        db=db
    )
```

### Integration Points

Add journal entry creation to existing flows:

```python
# In fulfillment.py - start_production (material issue)
for line in bom.lines:
    if reserved:
        record_material_issue(
            product_id=line.component_id,
            quantity=reserved_qty,
            unit_cost=component.cost or Decimal("0"),
            production_order_id=po.id,
            db=db
        )


# In fulfillment.py - complete_print (production complete + scrap)
if qty_good > 0:
    record_production_complete(
        product_id=po.product_id,
        quantity=qty_good,
        unit_cost=calculate_unit_cost(po, db),
        production_order_id=po.id,
        db=db
    )

if qty_bad > 0:
    record_scrap(
        product_id=po.product_id,
        quantity=qty_bad,
        unit_cost=calculate_unit_cost(po, db),
        production_order_id=po.id,
        scrap_reason=request.scrap_reason_code or "unspecified",
        db=db
    )


# In fulfillment.py - mark_shipped (sale)
record_sale(
    product_id=product.id,
    quantity=order.quantity,
    unit_cost=product.cost or Decimal("0"),
    sale_price=order.unit_price,
    sales_order_id=order.id,
    db=db
)


# In payments.py - verify_payment (payment received)
record_payment_received(
    amount=sales_order.grand_total,
    sales_order_id=sales_order.id,
    payment_method="stripe",
    db=db
)
```

### Reporting Endpoints

```python
@router.get("/reports/inventory-valuation")
async def get_inventory_valuation(db: Session = Depends(get_db)):
    """Get current inventory value by category."""
    
    result = db.execute(text("""
        SELECT 
            p.category,
            CASE 
                WHEN p.is_raw_material THEN 'Raw Materials'
                WHEN p.type = 'custom' THEN 'WIP/Custom'
                ELSE 'Finished Goods'
            END as inventory_type,
            COUNT(DISTINCT p.id) as item_count,
            SUM(i.on_hand_quantity) as total_quantity,
            SUM(i.on_hand_quantity * COALESCE(p.cost, 0)) as total_value
        FROM inventory i
        JOIN products p ON i.product_id = p.id
        WHERE i.on_hand_quantity > 0
        GROUP BY p.category, 
                 CASE 
                     WHEN p.is_raw_material THEN 'Raw Materials'
                     WHEN p.type = 'custom' THEN 'WIP/Custom'
                     ELSE 'Finished Goods'
                 END
        ORDER BY inventory_type, total_value DESC
    """)).fetchall()
    
    return {
        "valuation": [
            {
                "category": r.category,
                "inventory_type": r.inventory_type,
                "item_count": r.item_count,
                "total_quantity": float(r.total_quantity),
                "total_value": float(r.total_value),
            }
            for r in result
        ],
        "grand_total": sum(float(r.total_value) for r in result),
    }


@router.get("/reports/cogs-summary")
async def get_cogs_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Get COGS breakdown for period."""
    
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date.replace(day=1)  # First of month
    
    result = db.execute(text("""
        SELECT 
            a.code,
            a.name,
            SUM(jel.debit) as total_debit,
            SUM(jel.credit) as total_credit,
            SUM(jel.debit) - SUM(jel.credit) as net
        FROM journal_entry_lines jel
        JOIN journal_entries je ON jel.journal_entry_id = je.id
        JOIN accounts a ON jel.account_id = a.id
        WHERE a.type = 'expense'
        AND a.subtype = 'cogs'
        AND je.entry_date BETWEEN :start AND :end
        AND je.status = 'posted'
        GROUP BY a.code, a.name
        ORDER BY net DESC
    """), {"start": start_date, "end": end_date}).fetchall()
    
    return {
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "cogs_breakdown": [
            {
                "account_code": r.code,
                "account_name": r.name,
                "amount": float(r.net),
            }
            for r in result
        ],
        "total_cogs": sum(float(r.net) for r in result),
    }
```

---

## Summary: Implementation Phases

### Phase 1: Critical Bug Fixes (Week 1)
| Priority | Item | Effort |
|----------|------|--------|
| 🔴 | Bug #1: Double consumption | 30 min |
| 🔴 | Bug #2: Inventory record creation | 1 hr |
| 🔴 | Bug #3: MTO finished goods | 1 hr |
| 🔴 | Bug #4: MaterialInventory sync | 30 min |
| 🔴 | Bug #5: Production start sync | 30 min |

### Phase 2: Core Enhancements (Week 2-3)
| Priority | Item | Effort |
|----------|------|--------|
| 🟡 | Enhancement #2: Partial QC | 2 hr |
| 🟡 | Enhancement #3: Reprint tracking | 2 hr |
| 🟡 | Enhancement #4: Scrap codes | 2 hr |

### Phase 3: MTS & Purchasing (Week 4-5)
| Priority | Item | Effort |
|----------|------|--------|
| 🟢 | Enhancement #1: MTS support | 4 hr |
| 🟢 | Enhancement #6: Purchasing | 8 hr |

### Phase 4: Accounting (Week 6+)
| Priority | Item | Effort |
|----------|------|--------|
| 🟢 | Enhancement #5: Yield reporting | 4 hr |
| 🟢 | Enhancement #7: Accounting journals | 8 hr |

---

## QuickBooks Integration Considerations

Since you mentioned QuickBooks as a planned integration, here's how to structure for eventual sync:

### Option A: Journal Entry Export
- Export journal entries to QuickBooks via API
- Map BLB3D account codes to QB account codes
- Batch sync daily/weekly

### Option B: Transaction-Level Sync
- Push individual transactions (invoices, bills, payments)
- More real-time but more complex
- QB becomes source of truth for AR/AP

### Recommended Approach
1. Build internal accounting as documented above
2. Create export endpoint that generates QB-compatible format
3. Use QB API to push journal entries
4. Keep BLB3D as operational system, QB as financial reporting

```python
@router.get("/export/quickbooks")
async def export_to_quickbooks(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
):
    """Export journal entries in QuickBooks import format."""
    
    entries = db.query(JournalEntry).filter(
        JournalEntry.entry_date.between(start_date, end_date),
        JournalEntry.status == "posted",
        JournalEntry.exported_to_qb == False,  # Track what's been exported
    ).all()
    
    # Format for QB API or IIF import
    qb_format = format_for_quickbooks(entries)
    
    return qb_format
```

---

*Document generated from E2E code review - Updated with comprehensive ERP enhancements*
