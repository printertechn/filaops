# Phase 5B: MRP Engine Implementation Plan

## Overview

Implement Material Requirements Planning (MRP) engine to automatically calculate material needs, generate planned purchase orders, and track supply vs demand.

## Current State

**Already Implemented:**
- BOMs with multi-level components, scrap factors, quantities
- Inventory tracking: on_hand, allocated, available quantities
- Products with lead_time_days, reorder_point, min_order_qty
- Production orders with `source` field (supports 'mrp_planned')
- Purchase orders (manual creation only)
- Routing/work centers for capacity

**Gaps to Fill:**
- No demand explosion from BOMs
- No automatic PO generation
- No lead time offsetting
- No supply/demand netting

---

## Implementation Steps

### Step 1: Create MRP Service Module

**File:** `backend/app/services/mrp.py`

Core MRP calculation service with these functions:

```python
class MRPService:
    def explode_bom(product_id, quantity, db) -> List[ComponentRequirement]
        """Recursively explode BOM to get all component requirements"""

    def calculate_net_requirements(requirements, db) -> List[NetRequirement]
        """Compare gross requirements vs available inventory"""

    def generate_planned_orders(net_requirements, db) -> List[PlannedOrder]
        """Create planned POs based on shortages and lead times"""

    def run_mrp(production_orders, db) -> MRPResult
        """Full MRP run: explode -> net -> plan"""
```

### Step 2: Add MRP Database Tables

**New Model:** `planned_orders` table

```python
class PlannedOrder(Base):
    __tablename__ = "planned_orders"

    id: int (PK)
    order_type: str  # 'purchase' or 'production'
    product_id: int (FK)
    quantity: Decimal
    due_date: date
    start_date: date  # due_date - lead_time
    source_demand_type: str  # 'production_order', 'sales_order'
    source_demand_id: int
    status: str  # 'planned', 'firmed', 'released', 'cancelled'
    converted_to_po_id: int (FK, nullable)
    converted_to_mo_id: int (FK, nullable)
    created_at: datetime
    created_by: int
```

**New Model:** `mrp_runs` table (audit trail)

```python
class MRPRun(Base):
    __tablename__ = "mrp_runs"

    id: int (PK)
    run_date: datetime
    planning_horizon_days: int
    orders_processed: int
    planned_orders_created: int
    status: str  # 'running', 'completed', 'failed'
    error_message: str (nullable)
    created_by: int
```

### Step 3: MRP API Endpoints

**File:** `backend/app/api/v1/endpoints/mrp.py`

```
POST /api/v1/mrp/run
    - Trigger MRP calculation
    - Params: planning_horizon_days (default 30)
    - Returns: MRPRunResult with planned orders

GET /api/v1/mrp/planned-orders
    - List all planned orders
    - Filters: status, product_id, due_date_range

POST /api/v1/mrp/planned-orders/{id}/firm
    - Firm a planned order (lock it in)

POST /api/v1/mrp/planned-orders/{id}/release
    - Convert planned order to actual PO or MO

DELETE /api/v1/mrp/planned-orders/{id}
    - Cancel a planned order

GET /api/v1/mrp/requirements
    - Get material requirements summary
    - Shows: product, gross_req, on_hand, allocated, net_req

GET /api/v1/mrp/supply-demand
    - Timeline view of supply vs demand by product
```

### Step 4: MRP Calculation Logic

**BOM Explosion Algorithm:**
```
function explode_bom(product_id, quantity, level=0):
    bom = get_active_bom(product_id)
    if not bom:
        return []  # Raw material, no further explosion

    requirements = []
    for line in bom.lines:
        component_qty = quantity * line.quantity * (1 + line.scrap_factor)

        requirements.append({
            product_id: line.component_id,
            quantity: component_qty,
            level: level,
            parent_product_id: product_id,
            consume_stage: line.consume_stage
        })

        # Recursively explode sub-assemblies
        sub_reqs = explode_bom(line.component_id, component_qty, level + 1)
        requirements.extend(sub_reqs)

    return requirements
```

**Net Requirements Calculation:**
```
function calculate_net_requirements(gross_requirements):
    # Group requirements by product
    by_product = group_by(gross_requirements, 'product_id')

    net_requirements = []
    for product_id, reqs in by_product:
        total_gross = sum(r.quantity for r in reqs)

        inventory = get_inventory(product_id)
        available = inventory.on_hand - inventory.allocated

        # Include incoming supply (open POs)
        incoming = get_open_po_quantity(product_id)

        net_required = total_gross - available - incoming

        if net_required > 0:
            product = get_product(product_id)
            # Round up to min order quantity
            order_qty = max(net_required, product.min_order_qty or 0)

            net_requirements.append({
                product_id: product_id,
                gross_required: total_gross,
                available: available,
                incoming: incoming,
                net_required: net_required,
                suggested_order_qty: order_qty,
                lead_time_days: product.lead_time_days
            })

    return net_requirements
```

**Planned Order Generation:**
```
function generate_planned_orders(net_requirements, demand_due_date):
    planned_orders = []

    for req in net_requirements:
        product = get_product(req.product_id)

        # Calculate start date based on lead time
        lead_time = product.lead_time_days or 7
        start_date = demand_due_date - timedelta(days=lead_time)

        # Determine order type
        if product.has_bom:
            order_type = 'production'  # Make internally
        else:
            order_type = 'purchase'    # Buy from supplier

        planned_orders.append(PlannedOrder(
            order_type=order_type,
            product_id=req.product_id,
            quantity=req.suggested_order_qty,
            due_date=demand_due_date,
            start_date=start_date,
            status='planned'
        ))

    return planned_orders
```

### Step 5: Pydantic Schemas

**File:** `backend/app/schemas/mrp.py`

```python
class MRPRunRequest(BaseModel):
    planning_horizon_days: int = 30
    include_draft_orders: bool = False

class MRPRunResult(BaseModel):
    run_id: int
    orders_processed: int
    components_analyzed: int
    shortages_found: int
    planned_orders_created: int
    planned_orders: List[PlannedOrderResponse]

class PlannedOrderResponse(BaseModel):
    id: int
    order_type: str
    product_id: int
    product_sku: str
    product_name: str
    quantity: Decimal
    due_date: date
    start_date: date
    status: str
    source_demand_type: Optional[str]
    source_demand_id: Optional[int]

class MaterialRequirement(BaseModel):
    product_id: int
    product_sku: str
    product_name: str
    gross_required: Decimal
    on_hand: Decimal
    allocated: Decimal
    available: Decimal
    incoming_supply: Decimal
    net_required: Decimal
    suggested_order_qty: Decimal
    lead_time_days: int
    shortage: bool

class SupplyDemandTimeline(BaseModel):
    product_id: int
    product_sku: str
    timeline: List[SupplyDemandEntry]

class SupplyDemandEntry(BaseModel):
    date: date
    demand: Decimal
    supply: Decimal
    balance: Decimal
    source: str  # 'production_order', 'purchase_order', 'on_hand'
```

### Step 6: Integration Points

**When Production Order Released:**
- Option to auto-run MRP for that order's components
- Show warnings if materials unavailable

**When Purchase Order Received:**
- Update planned order status if linked
- Recalculate availability for dependent production orders

**Admin Dashboard Widget:**
- Material shortages count
- Planned orders pending release
- Items below reorder point

---

## Database Migration

```sql
-- Planned Orders table
CREATE TABLE planned_orders (
    id INT IDENTITY(1,1) PRIMARY KEY,
    order_type NVARCHAR(20) NOT NULL,  -- 'purchase' or 'production'
    product_id INT NOT NULL FOREIGN KEY REFERENCES products(id),
    quantity DECIMAL(18,4) NOT NULL,
    due_date DATE NOT NULL,
    start_date DATE NOT NULL,
    source_demand_type NVARCHAR(50),
    source_demand_id INT,
    status NVARCHAR(20) NOT NULL DEFAULT 'planned',
    converted_to_po_id INT FOREIGN KEY REFERENCES purchase_orders(id),
    converted_to_mo_id INT FOREIGN KEY REFERENCES production_orders(id),
    notes NVARCHAR(MAX),
    created_at DATETIME2 DEFAULT GETDATE(),
    created_by INT,
    updated_at DATETIME2
);

-- MRP Run audit table
CREATE TABLE mrp_runs (
    id INT IDENTITY(1,1) PRIMARY KEY,
    run_date DATETIME2 NOT NULL DEFAULT GETDATE(),
    planning_horizon_days INT NOT NULL,
    orders_processed INT,
    components_analyzed INT,
    shortages_found INT,
    planned_orders_created INT,
    status NVARCHAR(20) NOT NULL,
    error_message NVARCHAR(MAX),
    created_by INT,
    completed_at DATETIME2
);

-- Add safety_stock to products if missing
ALTER TABLE products ADD safety_stock DECIMAL(18,4) DEFAULT 0;
```

---

## Deliverables Summary

1. **MRP Service** (`app/services/mrp.py`)
   - BOM explosion
   - Net requirements calculation
   - Planned order generation

2. **Database Models** (`app/models/mrp.py`)
   - PlannedOrder
   - MRPRun

3. **API Endpoints** (`app/api/v1/endpoints/mrp.py`)
   - POST /mrp/run
   - GET /mrp/planned-orders
   - POST /mrp/planned-orders/{id}/firm
   - POST /mrp/planned-orders/{id}/release
   - GET /mrp/requirements
   - GET /mrp/supply-demand

4. **Schemas** (`app/schemas/mrp.py`)
   - Request/response models

5. **Database Migration**
   - planned_orders table
   - mrp_runs table
   - safety_stock field on products

---

## Future Enhancements (Phase 5C+)

- Finite capacity planning (work center load balancing)
- Multi-location inventory planning
- Forecast-based demand planning
- Vendor lead time optimization
- Safety stock calculations based on demand variability
