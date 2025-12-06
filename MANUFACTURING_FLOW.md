# BLB3D Manufacturing Flow & System Components

## High-Level Process Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CUSTOMER JOURNEY                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  [Quote Request] ──► [Quote Generated] ──► [Customer Accepts] ──► [Payment]     │
│        │                    │                     │                    │         │
│        ▼                    ▼                     ▼                    ▼         │
│   Upload 3MF          ML Pricing             Shipping Rates      Stripe Checkout │
│                       + BOM Preview          from EasyPost                       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              ORDER MANAGEMENT                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  [Sales Order Created] ──► [BOM Review] ──► [Release to Production]             │
│        │                       │                    │                            │
│        ▼                       ▼                    ▼                            │
│   Auto-create:            Admin verifies      Creates Production Order           │
│   - Product               - Materials         - Allocates inventory              │
│   - BOM                   - Quantities        - Schedules machines               │
│   - G-code link           - Costs                                                │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              MANUFACTURING                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  [Start Production] ──► [Print Job Running] ──► [Print Complete] ──► [QC]       │
│        │                       │                      │                │         │
│        ▼                       ▼                      ▼                ▼         │
│   TRANSACTIONS:           TRACKING:              TRANSACTIONS:    Pass/Fail      │
│   - Consume raw           - Machine ID           - WIP → FG          │          │
│     material              - Start time           - Labor cost        │          │
│   - Create WIP            - Progress %           - Machine cost      │          │
│                           - Est. complete                            │          │
│                                                                      ▼          │
│                                                              [Ready to Ship]     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FULFILLMENT                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  [Pack Order] ──► [Create Label] ──► [Ship] ──► [Complete]                      │
│       │                 │               │            │                           │
│       ▼                 ▼               ▼            ▼                           │
│  TRANSACTIONS:      EasyPost API    Update SO    FINANCIAL:                      │
│  - Consume            - Buy label   - Tracking   - Record revenue                │
│    packaging          - Get track#  - Status     - Record COGS                   │
│                                       "shipped"  - Sync to QuickBooks            │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Transactional Flow

### Phase 1: Order Entry (✅ BUILT)

| Step | Action | System Component | Transactions |
|------|--------|------------------|--------------|
| 1.1 | Customer uploads 3MF | Quote Portal | Create `Quote` record |
| 1.2 | System generates quote | Bambu Suite API | Price calculation, BOM preview |
| 1.3 | Customer enters shipping | Quote Portal | Save address to `Quote` |
| 1.4 | Get shipping rates | EasyPost API | Fetch rates (no DB change) |
| 1.5 | Customer pays | Stripe Checkout | Payment captured |
| 1.6 | Order created | Payment Webhook | Create `SalesOrder`, `Product`, `BOM` |

**Inventory Impact:** None yet (no allocation)

---

### Phase 2: Order Review & Release (⚠️ PARTIAL)

| Step | Action | System Component | Transactions |
|------|--------|------------------|--------------|
| 2.1 | Admin reviews BOM | Admin Dashboard | Update `BOM` if needed |
| 2.2 | Check inventory | Inventory Service | Query available stock |
| 2.3 | Release to production | Production Module | Create `ProductionOrder` |
| 2.4 | Allocate inventory | Inventory Service | `inventory.allocated_qty += X` |

**Inventory Impact:**
```
Raw Material (e.g., PLA Black):
  - available_qty: 1000g → 950g
  - allocated_qty: 0g → 50g
  - on_hand_qty: 1000g (unchanged)
```

**What's Needed:**
- [ ] BOM approval workflow
- [ ] Inventory allocation on PO creation
- [ ] Inventory availability check before release

---

### Phase 3: Manufacturing Execution (❌ NOT BUILT)

| Step | Action | System Component | Transactions |
|------|--------|------------------|--------------|
| 3.1 | Start print job | Print Job Module | Create `PrintJob`, link to machine |
| 3.2 | Consume materials | Inventory Service | Hard deduct from inventory |
| 3.3 | Track WIP | WIP Tracking | Create WIP record with costs |
| 3.4 | Job completes | Bambu Suite Webhook | Update `PrintJob.status` |
| 3.5 | Record output | Production Module | WIP → Finished Goods |

**Inventory Impact (on Start - Step 3.2):**
```
Raw Material (PLA Black):
  - on_hand_qty: 1000g → 950g
  - allocated_qty: 50g → 0g
  - available_qty: 950g (unchanged)

WIP:
  - Create WIP record for this production order
  - WIP value = material cost + (labor rate × est. time)
```

**Inventory Impact (on Complete - Step 3.5):**
```
WIP:
  - Close WIP record
  - Final cost = material + labor + machine depreciation

Finished Goods (ALWAYS goes to inventory):
  - on_hand_qty: 0 → 1
  - status: "pending_qc"
  - linked_sales_order_id: SO-2025-001 (for make-to-order)
  - location: "QC Station"
  - unit_cost: calculated from WIP

This allows:
  - Unified inventory view
  - Batch QC processing
  - Partial shipments
  - Returns handling
  - Clear audit trail
```

**What's Needed:**
- [ ] `PrintJob` ↔ `ProductionOrder` relationship
- [ ] Material consumption transaction
- [ ] WIP cost accumulation
- [ ] Machine time tracking
- [ ] Production completion workflow

---

### Phase 4: Quality Control (❌ NOT BUILT)

| Step | Action | System Component | Transactions |
|------|--------|------------------|--------------|
| 4.1 | Inspect part | QC Module | Create `QCInspection` record |
| 4.2a | Pass | QC Module | Status → "ready_to_ship" |
| 4.2b | Fail | QC Module | Scrap or rework decision |
| 4.3 | Scrap (if fail) | Inventory Service | Write off WIP, adjust costs |

**Inventory Impact (Pass):**
```
Finished Goods:
  - status: "pending_qc" → "ready_to_ship"

Sales Order:
  - qc_status: "passed"
  - ready_to_ship: true
```

**Inventory Impact (Fail - Scrap):**
```
WIP:
  - Write off to scrap expense
  - Record scrap reason

Production Order:
  - May need to re-run
```

**What's Needed:**
- [ ] QC inspection form/checklist
- [ ] Pass/fail workflow
- [ ] Scrap tracking
- [ ] Rework handling

---

### Phase 5: Shipping & Fulfillment (⚠️ PARTIAL)

| Step | Action | System Component | Transactions |
|------|--------|------------------|--------------|
| 5.1 | Pack order | Fulfillment | Consume packaging materials |
| 5.2 | Create label | EasyPost API | Buy label, get tracking # |
| 5.3 | Update order | Sales Order | tracking_number, carrier, status |
| 5.4 | Ship notification | Email Service | Send tracking to customer |

**Inventory Impact:**
```
Packaging (box, tape, etc.):
  - on_hand_qty: 100 → 99

Sales Order:
  - status: "confirmed" → "shipped"
  - shipped_at: timestamp
  - tracking_number: "1Z999..."
```

**What's Needed:**
- [ ] Packaging BOM or flat consumption
- [ ] Create label button in admin
- [ ] Auto-email with tracking
- [ ] Batch label printing

---

### Phase 6: Financial Close (❌ NOT BUILT)

| Step | Action | System Component | Transactions |
|------|--------|------------------|--------------|
| 6.1 | Record revenue | Journal Service | Debit: A/R, Credit: Revenue |
| 6.2 | Record COGS | Journal Service | Debit: COGS, Credit: Inventory |
| 6.3 | Record shipping | Journal Service | Expense if cost > collected |
| 6.4 | Sync to QB | QuickBooks API | Push journal entries |

**Journal Entries:**

```
On Payment (already captured in Stripe):
  DR  Cash/Stripe Clearing     $25.00
    CR  Deferred Revenue              $18.00
    CR  Shipping Collected             $7.00

On Ship (recognize revenue):
  DR  Deferred Revenue         $18.00
    CR  Sales Revenue                 $18.00

  DR  Cost of Goods Sold       $8.50
    CR  Inventory - Raw Material       $5.00
    CR  Inventory - Packaging          $0.50
    CR  WIP Labor                      $2.00
    CR  WIP Machine Depreciation       $1.00

  DR  Shipping Expense         $6.31  (actual label cost)
    CR  Cash/EasyPost                  $6.31
```

**What's Needed:**
- [ ] Journal entry model
- [ ] Automated journal creation on events
- [ ] QuickBooks OAuth integration
- [ ] Journal sync endpoint

---

## Data Model Additions Needed

### New Tables

```sql
-- WIP Tracking
CREATE TABLE work_in_progress (
    id INT PRIMARY KEY,
    production_order_id INT FK,
    print_job_id INT FK,
    material_cost DECIMAL(10,2),
    labor_cost DECIMAL(10,2),
    machine_cost DECIMAL(10,2),
    status VARCHAR(20),  -- 'active', 'completed', 'scrapped'
    started_at DATETIME,
    completed_at DATETIME
);

-- QC Inspections
CREATE TABLE qc_inspections (
    id INT PRIMARY KEY,
    production_order_id INT FK,
    inspector_id INT FK,
    result VARCHAR(20),  -- 'pass', 'fail', 'rework'
    notes TEXT,
    inspected_at DATETIME
);

-- Journal Entries
CREATE TABLE journal_entries (
    id INT PRIMARY KEY,
    entry_date DATE,
    reference_type VARCHAR(50),  -- 'sales_order', 'production_order'
    reference_id INT,
    description VARCHAR(255),
    posted_to_qb BOOLEAN,
    qb_sync_id VARCHAR(100)
);

CREATE TABLE journal_lines (
    id INT PRIMARY KEY,
    journal_entry_id INT FK,
    account_code VARCHAR(20),
    account_name VARCHAR(100),
    debit DECIMAL(10,2),
    credit DECIMAL(10,2)
);

-- Machine Utilization
CREATE TABLE machine_usage (
    id INT PRIMARY KEY,
    machine_id INT FK,
    print_job_id INT FK,
    started_at DATETIME,
    ended_at DATETIME,
    runtime_minutes INT,
    idle_minutes INT
);
```

---

## Machine Utilization Tracking

```
┌─────────────────────────────────────────────────────────────────┐
│                    MACHINE: P1S-001                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Timeline (24 hours):                                            │
│  ├──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┤      │
│  │ IDLE │ JOB1 │ JOB1 │ IDLE │ JOB2 │ JOB2 │ JOB2 │ IDLE │      │
│  ├──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┤      │
│  0h     3h     6h     9h    12h    15h    18h    21h   24h      │
│                                                                  │
│  Utilization: 15h / 24h = 62.5%                                 │
│  Jobs Completed: 2                                               │
│  Total Print Time: 15 hours                                      │
│  Idle Time: 9 hours                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Tracked via:**
- Bambu Suite webhooks (job start/end)
- `machine_usage` table aggregation
- Dashboard showing real-time utilization

---

## Implementation Priority

### Must Have (Phase 1)
1. Production Order → Print Job link
2. Material consumption on job start
3. Job completion workflow
4. Create shipping label button
5. Order status progression

### Should Have (Phase 2)
1. WIP cost tracking
2. Machine utilization dashboard
3. QC pass/fail workflow
4. Email notifications

### Nice to Have (Phase 3)
1. Journal entries
2. QuickBooks sync
3. Batch operations
4. Advanced reporting

---

## Summary: What Each Transaction Does

| Event | Inventory | Financial | Status |
|-------|-----------|-----------|--------|
| Quote Accepted | - | - | Quote → Accepted |
| Payment Received | - | Cash ↑ | SO Created, Paid |
| Released to Prod | Allocate materials | - | PO Created |
| Print Started | Consume materials | WIP ↑ | Job Running |
| Print Complete | - | WIP finalized | Job Complete |
| QC Passed | FG available | - | Ready to Ship |
| Shipped | Consume packaging | Revenue, COGS | SO Shipped |
| QB Synced | - | Books closed | Complete |
