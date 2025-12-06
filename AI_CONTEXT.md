# AI Assistant Context - BLB3D ERP

> **Read this first.** This file provides quick context for AI assistants working on this codebase.
> For full architecture details, see [ARCHITECTURE.md](./ARCHITECTURE.md)

## What Is This?

Custom ERP system for a 3D print farm. Replaces MRPeasy.

**Tech Stack:**
- Backend: FastAPI (Python 3.11) + SQL Server Express + SQLAlchemy
- Frontend: React quote portal (port 5173)
- Integration: Bambu Print Suite (port 8001) for print scheduling/quoting
- Payments: Stripe
- Shipping: EasyPost

## The Business Problem

Orders come from 3 sources that need to work together:

| Source | Type | Key Challenge |
|--------|------|---------------|
| **Squarespace** | Retail B2C, standard products | Multi-line orders, known SKUs |
| **Customer Portal** | B2B custom quotes | No SKU, no BOM, uploaded 3MF files |
| **WooCommerce** | Future retail channel | Same as Squarespace |

**The Gap**: Portal quotes don't have products/BOMs, so MRP can't calculate material needs.

**The Fix**: When a quote is accepted, auto-create a custom product + BOM so all orders flow through the same MRP system.

## Key Repositories

### blb3d-erp (This Repo)
- ERP backend (FastAPI, port 8000)
- Database models & migrations
- API endpoints for orders, products, inventory

### quote-portal
- Customer-facing React app (port 5173)
- File upload, material/color selection
- Stripe checkout integration
- Three.js 3D model viewer

### bambu-print-suite (Companion Repo)
- ML Dashboard backend (FastAPI, port 8001)
- Quote engine with BambuStudio CLI integration
- G-code analysis and pricing
- Printer fleet management via MQTT
- **NOTE**: ML Dashboard reads business data (orders, customers, BOMs) from ERP via internal API

## Architecture: ERP as Source of Truth

The ML Dashboard was updated (Nov 29, 2025) to read business data from ERP, eliminating duplicate data models:

```
┌─────────────────────────────────────────────────────────────────┐
│                        ERP Backend (8000)                        │
│                    "Source of Truth for Business"                │
│  • Sales Orders    • Customers    • Products/BOMs    • Inventory │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ /api/v1/internal/* (REST)
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                     ML Dashboard (8001)                          │
│                "Intelligence & Hardware Layer"                   │
│  • Printer Fleet (MQTT)    • Quote Engine (slicing)              │
│  • ML Predictions          • Production Scheduling               │
└─────────────────────────────────────────────────────────────────┘
```

**Internal API Endpoints** (no auth required, for service-to-service):

- `GET /api/v1/internal/sales-orders` - List all orders (ML Dashboard Orders tab)
- `GET /api/v1/internal/sales-orders/{id}` - Order details
- `GET /api/v1/internal/sales-orders/analytics/summary` - Dashboard summary cards
- `GET /api/v1/internal/customers` - List customers
- `GET /api/v1/internal/boms` - List BOMs for product selection
- `GET /api/v1/internal/boms/{id}` - BOM detail with cost calculation
- `GET /api/v1/internal/quotes` - List all quotes (ML Dashboard Quotes tab)
- `GET /api/v1/internal/quotes/{id}` - Quote detail with multi-material breakdown
- `GET /api/v1/internal/inventory/items` - Inventory grouped by category
- `GET /api/v1/internal/inventory/summary` - Aggregate stats (total items, low stock)
- `GET /api/v1/internal/inventory/transactions` - Transaction history with pagination
- `GET /api/v1/internal/production-orders` - Production order queue

**Future Plans**: See `FUTURE_ARCHITECTURE.md` for ML/Agent roadmap

## ACTIVE WORK: Phase 6 Code Quality (Dec 5, 2025)

> **If you're picking this up**: Phases 4A-4C, 5A-5B are COMPLETE. Phases 6A (Code Foundation) and 6B (Traceability) are COMPLETE.

### Phase 6A: Code Foundation - COMPLETE (Dec 5, 2025)

Enterprise-grade code patterns for maintainability and compliance.

**New Files Created:**
- `backend/app/core/settings.py` - pydantic-settings configuration with validation
- `backend/app/exceptions.py` - Custom exception hierarchy with error codes
- `backend/app/logging_config.py` - Structured JSON logging + audit log
- `backend/migrate_audit_columns.py` - Migration for audit trail columns

**Configuration Management:**
- All settings validated with pydantic-settings
- `.env.example` updated with 50+ documented settings
- Type coercion and validation (warns on default SECRET_KEY)
- Import: `from app.core.config import settings`

**Exception Hierarchy:**
```python
BLB3DException (base)
├── ValidationError (400)
├── InvalidStateError (400)
├── DuplicateError (400)
├── AuthenticationError (401)
├── PermissionDeniedError (403)
├── NotFoundError (404)
├── ConflictError (409)
├── BusinessRuleError (422)
│   ├── InsufficientInventoryError
│   ├── QuoteExpiredError
│   └── ProductionNotReadyError
├── IntegrationError (500)
│   ├── StripeError
│   ├── EasyPostError
│   └── BambuSuiteError
└── DatabaseError (500)
```

**Usage:**
```python
from app.exceptions import NotFoundError, ValidationError

if not product:
    raise NotFoundError("Product", product_id)
# Returns: {"error": "NOT_FOUND", "message": "Product with ID 123 not found"}
```

**Structured Logging:**
- JSON format for log aggregation (configurable: json or text)
- Separate audit log file (`logs/audit.log`) for compliance
- `get_logger(__name__)` for module loggers
- `audit_log()` for business events

**Audit Columns Added:**
- quotes: `created_by`, `updated_by`
- sales_orders: `created_by`, `updated_by`
- production_orders: `updated_by` (created_by existed)
- products, vendors, work_centers, routings: `created_by`, `updated_by`

**Bug Fixed During Testing:**
- `fulfillment.py`: Fixed priority sort (was comparing Integer to strings)
- `fulfillment.py`: Fixed status filter (`complete` not `completed`)

**E2E Test Results:** 55 passed, 4 failed (unrelated port config), 35 skipped

### Phase 6B: B2B Traceability - COMPLETE (Dec 5, 2025)

Tiered traceability system for B2B compliance. Configurable per customer - medical device customers get FULL traceability while B2C gets none.

**Traceability Levels:**
| Level | Description | Use Case |
|-------|-------------|----------|
| `none` | No tracking | B2C retail default |
| `lot` | Batch tracking only | Industrial customers |
| `serial` | Individual unit tracking | Warranty tracking |
| `full` | LOT + SERIAL + CoC | FDA/ISO/medical device |

**New Tables Created:**
- `serial_numbers` - Individual unit tracking (BLB-YYYYMMDD-XXXX format)
- `material_lots` - Batch tracking for raw materials (FIFO support)
- `production_lot_consumptions` - Links production to material lots (recall queries)
- `customer_traceability_profiles` - Per-customer traceability settings
- Added `traceability_level` column to `users` table

**New Files:**
- `backend/app/models/traceability.py` - SQLAlchemy models
- `backend/app/schemas/traceability.py` - Pydantic schemas
- `backend/app/api/v1/endpoints/admin/traceability.py` - Full CRUD + recall queries
- `backend/migrate_traceability.py` - Migration script

**API Endpoints** (`/api/v1/admin/traceability`):
| Endpoint | Description |
|----------|-------------|
| `GET /profiles` | List customer traceability profiles |
| `POST /profiles` | Create profile for customer |
| `PATCH /profiles/{user_id}` | Update customer's traceability level |
| `GET /lots` | List material lots (paginated, filterable) |
| `POST /lots` | Create material lot (receiving) |
| `POST /lots/generate-number` | Generate next lot number |
| `GET /serials` | List serial numbers |
| `POST /serials` | Generate serial numbers for production order |
| `GET /serials/lookup/{serial}` | Look up by serial string |
| `POST /consumptions` | Record lot consumption |
| `GET /recall/forward/{lot}` | "What did we make with lot X?" |
| `GET /recall/backward/{serial}` | "What went into serial Y?" |

**Auto-Serial Generation:**
When a production order completes, if the product has `track_serials=True`, serial numbers are automatically generated. Format: `BLB-YYYYMMDD-XXXX` (e.g., BLB-20251205-0001).

**Recall Query Examples:**
```sql
-- Forward: What did we make with a material lot?
SELECT sn.serial_number, p.name, so.order_number, u.email
FROM production_lot_consumptions plc
JOIN serial_numbers sn ON sn.production_order_id = plc.production_order_id
JOIN sales_orders so ON sn.sales_order_id = so.id
JOIN users u ON so.user_id = u.id
WHERE plc.material_lot_id = (SELECT id FROM material_lots WHERE lot_number = 'PLA-BLK-2025-0042');

-- Backward: What material lots went into a serial number?
SELECT ml.lot_number, ml.vendor_lot_number, p.name AS material
FROM production_lot_consumptions plc
JOIN material_lots ml ON plc.material_lot_id = ml.id
JOIN products p ON ml.product_id = p.id
WHERE plc.production_order_id = (SELECT production_order_id FROM serial_numbers WHERE serial_number = 'BLB-20251205-0001');
```

**Product Flags for Traceability:**
- `track_lots` - Enable lot tracking for this product (raw materials)
- `track_serials` - Enable serial tracking for this product (finished goods)

**Bug Fixed During Testing:**
- `order-to-ship.spec.ts`: Fixed port 8002 → 8000 for ERP URL

---

## Phase 4 ERP Foundation (COMPLETE)

> Phases 4A, 4B, and 4C are COMPLETE. Manufacturing Routes has backend + frontend integration in BOM modal.

### Phase 4 Overview

```
Phase A: Item Management     ✅ COMPLETE (Dec 4, 2025)
Phase B: Purchasing Module   ✅ COMPLETE (Dec 4, 2025) - Vendors, POs, Amazon CSV import
Phase C: Manufacturing Routes ✅ COMPLETE (Dec 5, 2025) - Work Centers, Routings, Process Path UI
Phase D: Squarespace Sync    ⏳ FUTURE
Phase E: QuickBooks Sync     ⏳ FUTURE
```

### Phase 4C: Manufacturing Routes - ✅ COMPLETE

Separates BOM (materials) from Routing (process). Enables capacity planning.

**New Tables:**
- `work_centers` - Machine pools, stations, labor pools with rates
- `resources` - Individual machines with Bambu integration fields
- `routings` - Versioned process definition per product (supports templates)
- `routing_operations` - Steps with setup/run/wait/move times

**Work Centers Configured:**
- FDM-POOL (200 hrs/day, $4/hr total: $3 machine + $0.50 labor + $0.50 overhead)
- QC (8 hrs/day, $25/hr labor)
- ASSEMBLY (8 hrs/day, $20/hr labor)
- SHIPPING (8 hrs/day, $18/hr labor)

**Routing Templates Seeded:**
- TPL-STANDARD: Print → QC → Pack → Ship (4 ops)
- TPL-ASSEMBLY: Print → QC → Assemble → Pack → Ship (5 ops)

**Cost Calculation:**
- Formula: `(setup_time + run_time) / 60 × hourly_rate`
- Setup time costed (7 min default for PRINT warmup)
- Example: PRINT 7m setup + 60m run = 67m × $4/hr = $4.47

**API Endpoints:**
- `GET/POST /api/v1/work-centers/` - List/create work centers
- `GET/PUT/DELETE /api/v1/work-centers/{id}` - CRUD
- `GET/POST /api/v1/work-centers/{id}/resources` - Manage machines
- `GET/POST /api/v1/routings/` - List/create routings
- `POST /api/v1/routings/seed-templates` - Create default templates
- `POST /api/v1/routings/apply-template` - Apply template to product with time overrides
- `GET /api/v1/routings?product_id={id}` - Get routing for product

**Frontend: Process Path UI in BOM Modal**
- Shows routing operations with editable run times
- Apply routing template to products
- Displays per-operation costs with setup time included
- Combined cost display: Material Cost + Process Cost = Total Unit Cost

**Key Files:**
- `backend/app/models/manufacturing.py` - SQLAlchemy models
- `backend/app/schemas/manufacturing.py` - Pydantic schemas
- `backend/app/api/v1/endpoints/work_centers.py` - Work center CRUD
- `backend/app/api/v1/endpoints/routings.py` - Routing CRUD + templates
- `quote-portal/src/pages/admin/AdminBOM.jsx` - Process Path UI
- `quote-portal/src/pages/admin/AdminManufacturing.jsx` - Work centers + routings management

### Phase 4A: Item & Product Management - ✅ COMPLETE

**Branch**: `phase4-erp-foundation`

**New Files Created**:
- `backend/app/models/item_category.py` - Hierarchical categories
- `backend/app/schemas/item.py` - Pydantic schemas for items/categories
- `backend/app/api/v1/endpoints/items.py` - Full CRUD API
- `backend/migrate_phase4a_items.py` - Migration script (run this!)

**New API Endpoints** (`/api/v1/items`):
| Endpoint | Description |
|----------|-------------|
| `GET /categories` | List categories |
| `GET /categories/tree` | Nested tree |
| `POST /categories` | Create category |
| `GET /items` | List items with filters |
| `POST /items` | Create item |
| `PATCH /items/{id}` | Update item |
| `POST /items/import` | CSV import |

**Product Model Extended** with:
- `item_type`: finished_good, component, supply, service
- `category_id`: FK to item_categories
- `cost_method`: fifo, average, standard
- `standard_cost`, `average_cost`, `last_cost`
- `lead_time_days`, `min_order_qty`, `reorder_point`
- `weight_oz`, `length_in`, `width_in`, `height_in`
- `upc` (barcode)

**Default Categories Seeded**:
- FILAMENT (PLA, PETG, ABS, TPU, Specialty)
- PACKAGING (Boxes, Bags, Filler)
- HARDWARE (Fasteners, Inserts)
- FINISHED_GOODS (Standard, Custom)
- SERVICES (Machine Time)

### Phase 4A: Admin UI - ✅ COMPLETE

**Files Created/Modified**:

- `quote-portal/src/pages/admin/AdminItems.jsx` - Full CRUD page with category tree sidebar
- `quote-portal/src/components/AdminLayout.jsx` - Added Items navigation link
- `quote-portal/src/App.jsx` - Added AdminItems route

**Bug Fixes Applied**:

- Removed auth from GET endpoints (items.py) - public read access
- Fixed Inventory column names: `quantity_on_hand` → `on_hand_quantity`, `quantity_allocated` → `allocated_quantity`

### To Run Migration

```bash
cd backend
python migrate_phase4a_items.py
```

---

## Current State (Updated Dec 4, 2025)

### ✅ Working NOW

| Component | Status | Location |
|-----------|--------|----------|
| **Quote Generation** | ✅ Complete | bambu-print-suite/quote-engine/ |
| **Material Pricing** | ✅ Complete | quote_calculator.py (cost multipliers) |
| **Infill/Strength Pricing** | ✅ Complete | Light/Standard/Strong/Solid options |
| **Material Speeds** | ✅ Complete | production_profiles.py (volumetric limits) |
| **Material Densities** | ✅ Complete | quote_calculator.py (weight calculation) |
| **Profile Inheritance** | ✅ Fixed | bambu_slicer.py, production_profiles.py |
| **Stripe Payments** | ✅ Complete | End-to-end checkout tested |
| **Stripe Tax** | ✅ Complete | Automatic tax via customer shipping address |
| **EasyPost Shipping** | ✅ Complete | Rate fetching and selection |
| **Quote Review Workflow** | ✅ Complete | Frontend + backend endpoint |
| **Lead Time Display** | ✅ Complete | 2 days (in stock) / 5 days (order/review) |
| **Multi-Color Preview** | ✅ Complete | Live 3D viewer color updates |
| **Sales Orders** | ✅ Complete | blb3d-erp/backend/app/ |
| **Product Catalog** | ✅ Complete | 633 products migrated |
| **Material Catalog** | ✅ Complete | 146 SKUs with colors (12 types, 90 colors) |
| **Internal API** | ✅ Complete | ERP serves ML Dashboard (orders, inventory, BOMs) |
| **Fulfillment Queue** | ✅ Complete | Production orders queue + printer assignment |
| **BOM Explosion** | ✅ Complete | Material reservation on production start |
| **Good/Bad Tracking** | ✅ Complete | Qty tracking, scrap transactions, shortfall detection |
| **BOM Costing** | ✅ Complete | Material + packaging + machine time ($1.50/hr) |
| **Quote Management UI** | ✅ Complete | ML Dashboard Quotes tab with detail view |
| **Multi-Material Support** | ✅ Complete | Per-slot weights + colors captured (Dec 1, 2025) |
| **Live 3D Color Preview** | ✅ Complete | Real-time color updates in Three.js viewer (Dec 4, 2025) |

### Quote Workflow

**Standard Quotes** (no special instructions, auto-approved):
1. Customer uploads 3MF → selects material/color/strength
2. System calculates price with real-time slicing
3. Customer enters shipping → gets rates from EasyPost
4. Customer pays via Stripe checkout
5. Payment success → order created

**Review Quotes** (has customer_notes, requires manual approval):
1. Customer uploads 3MF → adds special instructions
2. System shows "Requires Review" status
3. Customer enters email + shipping address
4. Customer clicks "Submit for Review"
5. Engineer reviews → sends payment link via email
6. Customer pays → order created

### Supported Materials

| Material | Cost Mult | Speed (mm³/s) | Density (g/cm³) | Notes |
|----------|-----------|---------------|-----------------|-------|
| PLA | 1.0× | 21.0 | 1.24 | Baseline |
| PETG | 1.2× | 15.0 | 1.27 | Slower, slightly heavier |
| ABS | 1.1× | 16.0 | 1.04 | 16% lighter than PLA |
| ASA | 1.3× | 18.0 | 1.07 | P1S only (needs enclosure) |
| TPU | 1.8× | 3.6 | 1.21 | Very slow, flexible |

### Infill/Strength Options

| Label | Infill % | Use Case |
|-------|----------|----------|
| Light | 15% | Display models, prototypes |
| Standard | 20% | General purpose (default) |
| Strong | 40% | Functional parts |
| Solid | 99%* | Maximum strength |

*Capped at 99% due to BambuStudio CLI limitation with sparse_infill_pattern at 100%

### BOM Cost Structure

When a quote is accepted, a 3-line BOM is auto-created:

| Line | Component | Source | Example |
|------|-----------|--------|---------|
| 1 | Material (filament) | `quote.material_grams` → kg | PETG-HF Black @ $23.99/kg |
| 2 | Packaging (box) | Dimensions → best-fit box | 8x8x14 Box @ $0.85 |
| 3 | Machine Time | `quote.print_time_hours` | 2.2hr @ $1.50/hr = $3.30 |

**Machine Time Product**: `SVC-MACHINE-TIME` (SKU), $1.50/hr fully-burdened rate (depreciation + electricity + maintenance)

**Material Costs**: Set per kg in products table. Defaults applied Dec 1, 2025:
- PLA Basic: $19.99/kg
- PLA Silk/Sparkle: $24.99/kg
- PETG: $21.99-23.99/kg
- ASA/ABS: $23.99-24.99/kg
- TPU: $34.99-39.99/kg
- Carbon fiber reinforced: $39.99-79.99/kg

### Multi-Material Quotes (QuoteMaterial) ✅ WORKING

For multi-color 3MF prints (using AMS), the `quote_materials` table stores per-slot breakdown:

```
quote_materials:
  - slot_number: 1, material_type: "TPU_95A", color_code: "RED", material_grams: 48.03
  - slot_number: 2, material_type: "TPU_95A", color_code: "WHT", material_grams: 101.02
```

**How It Works (Fixed Dec 1, 2025):**

1. **G-code Analysis**: `gcode_analyzer.py` extracts `filament_lengths_mm` per slot from G-code
2. **Weight Calculation**: `quote_calculator.py` converts lengths to weights using formula:
   - `Weight = Length × π × (d/2)² × density / 1000`
   - For 1.75mm filament: cross-section = π × 0.875² = 2.405 mm²
3. **QuoteMaterial Creation**: ERP creates records at quote time with weights (colors TBD)
4. **Color Selection**: Customer picks colors per slot in quote portal at accept time
5. **Color Update**: ERP updates QuoteMaterial records with selected colors at accept
6. **BOM Creation**: `bom_service.py` creates BOM lines for each material slot

**Files Modified:**

- `bambu-print-suite/quote-engine/slicer/quote_calculator.py` - Weight calculation from lengths
- `blb3d-erp/backend/app/api/v1/endpoints/quotes.py` - QuoteMaterial color updates at accept
- `blb3d-erp/backend/app/services/bom_service.py` - Multi-material BOM line creation

### Live 3D Color Preview (Dec 4, 2025) - UNIQUE FEATURE

Real-time color preview in Three.js viewer for multi-color 3MF files. This feature auto-matches original Bambu Studio colors to available inventory colors.

**How It Works:**

1. **3MF Analysis**: `threemf_analyzer.py` extracts `filament_colour` from `project_settings.config`
2. **G-code Analysis**: `gcode_analyzer.py` extracts `filament_weights_grams` per slot
3. **Color Filtering**: Frontend filters to only show USED slots (where weight > 0)
4. **Auto-Matching**: `findClosestColor()` matches original hex colors to inventory using Euclidean RGB distance
5. **3D Rendering**: ModelViewer.jsx assigns colors to meshes by index (reversed to match weight order)

**Key Files:**

- `quote-portal/src/pages/QuoteResult.jsx` - Color selection UI + useMemo optimization
- `quote-portal/src/components/ModelViewer.jsx` - Three.js viewer with multi-color support
- `quote-portal/src/pages/GetQuote.jsx` - Filters originalColors to match weights

**Technical Challenge Solved:**

Three.js's ThreeMFLoader doesn't preserve Bambu Studio's color metadata - all meshes appear as the same color. The solution assigns colors by mesh INDEX, but mesh indices are in reverse order from weight indices. The fix reverses the `selectedColors` array passed to ModelViewer.

**Performance Note:**

Complex models (5+ colors, high mesh count) can spike RAM to 90%+. Potential mitigations:
- File size limits on upload
- Mesh decimation for preview
- LOD (Level of Detail) switching
- Web Worker for parsing

### ❌ Not Done Yet

- ~~Auto-create custom products from accepted quotes~~ → **DONE** (quote_conversion_service.py)
- ~~BOM costing display~~ → **DONE** (ML Dashboard BOM tab)
- ~~Quote management UI~~ → **DONE** (ML Dashboard Quotes tab)
- ~~Multi-material capture from Bambu Suite slicer output~~ → **DONE** (Dec 1, 2025)
- Email notifications (confirmation, payment links)
- Admin UI for quote review and price adjustment
- SalesOrderLine model for multi-item orders
- Squarespace webhook integration
- Inventory checking before quote acceptance (endpoint exists, needs frontend integration)

## Key Files to Know

### Quote Portal (quote-portal)
```
src/pages/
├── QuoteForm.jsx        # File upload, material/color/strength selection
├── QuoteResult.jsx      # Results, shipping, payment/review buttons
├── QuoteSubmitted.jsx   # Review confirmation page
├── PaymentSuccess.jsx   # Post-payment confirmation
src/api/
├── client.js            # API client (submitQuoteForReview, etc.)
```

### Quote System (bambu-print-suite)
```
quote-engine/slicer/
├── quote_calculator.py     # Pricing logic, material costs, densities
├── gcode_analyzer.py       # Parse G-code for time/material
├── bambu_slicer.py         # BambuStudio CLI wrapper, speed limiting
├── production_profiles.py  # Material profiles, printer selection
├── filament_profiles.py    # Speed multipliers per material
```

### ERP Backend (blb3d-erp)

```
backend/app/
├── api/v1/endpoints/
│   ├── quotes.py           # Quote CRUD + /submit-for-review
│   ├── internal.py         # Internal API for ML Dashboard (orders, BOMs, quotes)
│   ├── sales_orders.py     # Order management
│   ├── products.py         # Product catalog
│   ├── production_orders.py # Production queue
│   ├── stripe_webhook.py   # Payment webhooks
│   ├── shipping.py         # EasyPost integration
├── models/
│   ├── quote.py            # Quote + QuoteMaterial (multi-material)
│   ├── bom.py              # BOM + BOMLine
├── schemas/                 # Pydantic schemas
├── services/
│   ├── bom_service.py      # Auto-create product/BOM from quote
│   ├── material_service.py # Material lookup for BOM lines
│   ├── bambu_client.py     # Calls ML Dashboard API
│   ├── quote_conversion_service.py  # Quote → Product/BOM/Order conversion
```

### ML Dashboard (bambu-print-suite/ml-dashboard)

```
frontend/src/components/
├── QuoteManagement.jsx     # Quotes tab - list + detail view
├── BOMManagement.jsx       # BOM tab - list + detail + cost breakdown
├── OrderManagement.jsx     # Orders tab
├── FulfillmentQueue.jsx    # MES tab - production queue
backend/
├── routers/erp_data.py     # Proxy routes to ERP internal API
├── clients/erp_client.py   # ERP API client methods
```

## Data Quality Issues Identified (Nov 29, 2025)

### Inventory (products table)
- **Wrong Categories**: ~25 items (boxes, printer parts in "Finished Goods")
- **Duplicate SKUs**: 4 entries (CW-CWDS-Black vs CW-CWDS-BK)
- **Bad SKU Formats**: 3 items (A00015, C-00, A-00086--PLASLK-SI)
- **Missing Product Names**: 47 items show as "Product M-00044-XX"
- **Test Entries**: 2 items to delete ("pla", "Shipping Fee")

### Material Inventory (material_inventory table)
- All 78 entries have `in_stock=1` but `quantity_kg=0` (lying!)
- PETG, ABS, ASA, TPU materials have no material_colors entries
- Portal shows all materials as "available" without actual stock check

**Fix Plan**: CSV exported for manual review → SQL UPDATE statements

## Recent Bug Fixes

### Stripe Tax Configuration (Nov 30, 2025)

**Note:** Stripe Tax requires Dashboard configuration before it works:

- Go to <https://dashboard.stripe.com/test/settings/tax>
- Add origin address (your business address)
- Set up tax registrations for states where you collect tax

The code is ready (`automatic_tax: {enabled: true}`), just needs Dashboard setup.

### Infill Pricing Bug (Nov 29, 2025)
**Problem:** All infill percentages showed same price
**Root Cause:** BambuStudio CLI parameter was `--infill-density` but correct is `--sparse-infill-density`
**Fix:** Updated bambu_slicer.py to use correct parameter + cap at 99% for solid

### Payment Without Shipping Bug (Nov 29, 2025)
**Problem:** Users could click Pay without entering shipping
**Fix:** Added validation in QuoteResult.jsx - button disabled until address + rate selected

## Database Migrations Pending

**File:** `scripts/add_quote_customer_fields.sql`
```sql
ALTER TABLE quotes ADD customer_email NVARCHAR(255) NULL;
ALTER TABLE quotes ADD customer_name NVARCHAR(200) NULL;
ALTER TABLE quotes ADD internal_notes NVARCHAR(1000) NULL;
CREATE INDEX IX_quotes_customer_email ON quotes(customer_email);
```
**Purpose:** Support quote review workflow with customer contact info

## Integration Roadmap (CRITICAL - DO NOT FORGET)

> **AI ASSISTANTS: Read this section every session. These are committed business requirements.**

### External Service Integrations

| Integration | Status | Priority | Purpose |
|-------------|--------|----------|---------|
| **Squarespace** | NOT STARTED | HIGH | Sync retail B2C orders → ERP sales orders |
| **QuickBooks** | NOT STARTED | HIGH | Sync invoices, payments, chart of accounts |
| **EasyPost** | PARTIAL (testing) | MEDIUM | Shipping rates + label purchase (use test API keys) |
| **Stripe** | PARTIAL (testing) | MEDIUM | Payment processing (use test mode) |

### B2B Standard Parts Portal (Retail Partners)

> **Business Need**: Retail partners (other businesses) need to order Make-To-Stock (MTS) parts at negotiated wholesale rates. Different from custom quote portal.

**Requirements:**

- Partner login with pre-negotiated pricing tiers
- Standard product catalog (not custom quotes)
- Volume discounts and net terms
- PO-based ordering (not credit card)
- Integration with ERP for inventory availability

**Implementation Notes:**

- Could be a separate route in quote-portal OR new repo
- Needs partner pricing table in database
- Needs partner authentication (separate from consumer auth)

### Integration API Keys Needed

```env
# Add to .env when ready for production
SQUARESPACE_API_KEY=        # Get from Squarespace > Settings > Advanced > API
SQUARESPACE_STORE_ID=       # From store settings
QUICKBOOKS_CLIENT_ID=       # From Intuit Developer Portal
QUICKBOOKS_CLIENT_SECRET=
QUICKBOOKS_REALM_ID=        # Company ID after OAuth
EASYPOST_API_KEY=           # Currently using test key
STRIPE_SECRET_KEY=          # Currently using test key
```

---

## TODO Items

### Immediate
- [x] **Create support@blb3dprinting.com email** - ✅ Configured
  - support@blb3dprinting.com (main support)
  - orders@blb3dprinting.com (order notifications)
  - customer_service@blb3dprinting.com (customer inquiries)
- [ ] Run database migration for customer fields
- [ ] Add email notifications for quote submission

### Short-term
- [ ] Admin page for quote review
- [ ] Send payment links to customers
- [ ] Auto-create products from accepted quotes

## Common Tasks

### Test Quote Generation
```bash
# Start all services
cd blb3d-erp/backend && python -m uvicorn app.main:app --reload --port 8000
cd bambu-print-suite/ml-dashboard/backend && python main.py
cd quote-portal && npm run dev

# Test URLs
http://localhost:5173/quote          # Customer portal
http://localhost:8000/docs           # ERP API docs
http://localhost:8001/docs           # ML Dashboard docs
```

### Debug Quote Issues
1. Check ML Dashboard console for [DEBUG] output
2. Look for volumetric speed limiting messages
3. Verify profile inheritance is being followed
4. Check material parameter flows through entire chain
5. For infill issues: verify --sparse-infill-density parameter

## Integration Points
```
Quote Portal (5173) ──HTTP──▶ ERP (8000) ──HTTP──▶ ML Dashboard (8001)
                                   │                      │
                                   ▼                      ▼
                              SQL Server           BambuStudio CLI
                                   │                      │
                     ┌─────────────┴─────────────┐       │
                     ▼                           ▼       ▼
                  Stripe                     EasyPost  Printers
```

## Database

SQL Server Express, connection in `backend/database.py`

Key tables: products, quotes, sales_orders, production_orders, boms, inventory, material_catalog

## Printer Fleet

| Name | Model | Use Case |
|------|-------|----------|
| Donatello | A1 | General production |
| Leonardo | P1S | ABS/ASA (enclosed) |
| Michelangelo | A1 | General production |
| Raphael | A1 | General production |

---

**See Also:**
- ARCHITECTURE.md - Full system design
- ISSUES.md - Bug tracking and recent fixes
- PROJECT_STATUS.md - Phase progress
- ROADMAP.md - Future plans
