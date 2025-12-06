# BLB3D ERP - Project Status

**Last Updated:** December 4, 2025
**Status:** Phase 3 - Manufacturing Execution & Fulfillment (Complete)

---

## Current State

### What's Working NOW

| Component | Status | Notes |
|-----------|--------|-------|
| **Customer Portal** | ✅ Complete | Quote flow, 3D viewer, material/color selection |
| **Quote Engine** | ✅ Complete | Material-aware pricing, density-based weights |
| **Infill/Strength Selection** | ✅ Complete | Light/Standard/Strong/Solid with correct pricing |
| **Stripe Payment** | ✅ Complete | End-to-end checkout tested successfully |
| **EasyPost Shipping** | ✅ Complete | Rate fetching, carrier selection |
| **Quote Review Workflow** | ✅ Complete | Email capture, pending_review status |
| **Admin Dashboard** | ✅ Complete | Quote management with filters |
| **BambuStudio Integration** | ✅ Complete | CLI slicing with profile inheritance |
| **Material System** | ✅ Complete | 146 SKUs - PLA, PETG, ABS, ASA, TPU with colors |
| **Sales Order System** | ✅ Complete | Multi-source order management |
| **Product Catalog** | ✅ Complete | 633 products migrated |
| **ML Time Estimation** | ✅ Complete | 88.9% accuracy with correction model |
| **Printer Fleet** | ✅ Connected | 4 printers (3x A1, 1x P1S) via MQTT |
| **Fulfillment Queue** | ✅ Complete | Production order queue in ML Dashboard |
| **Printer Assignment** | ✅ Complete | Select printer when starting production |
| **BOM Explosion** | ✅ Complete | Material reservation on production start |
| **Good/Bad Tracking** | ✅ Complete | Qty good → inventory, qty bad → scrap |
| **Machine Time Tracking** | ✅ Complete | Captures printer hours as transactions |
| **Transaction Audit** | ✅ Complete | Timeline, gaps, health score |
| **E2E Tests** | ✅ Complete | Order-to-ship Playwright suite |

### Recent Wins (Dec 4, 2025)

1. **Live Multi-Color 3D Preview** - Real-time color preview in Three.js viewer
   - Auto-matches original 3MF colors to available inventory colors
   - Correct weight-to-color mapping (heaviest region = Region 1)
   - Fixed mesh index reversal issue for proper color assignment
   - Unique feature - not found in other 3D printing quote systems
2. **API Call Optimization** - Fixed excessive `/materials/options` calls
   - Was calling API on every 3D viewer interaction (OrbitControls)
   - Added `useMemo` to prevent re-parsing sessionStorage on every render
   - Now calls API once on page load instead of 20+ times
3. **OrcaSlicer Integration** - Fixed output directory bug for non-3MF files
4. **Multi-Color UI Enhancement** - Filters unused AMS slots, shows only active colors

### Known Performance Issues (Dec 4, 2025)

**Memory Usage**: Complex multi-color jobs (5+ colors, detailed models) can spike RAM to 90%+
- Root cause likely in Three.js mesh handling or slicing process
- Needs investigation: mesh count limits, LOD for preview, worker threads
- Potential guardrails: file size limits, mesh decimation, lazy loading

### Previous Wins (Dec 2, 2025)

1. **Machine Time Tracking** - Captures printer usage as transactions for metrics & costing
   - `machine_time` transaction type records actual hours used
   - Tracks estimated vs actual with variance calculation
   - Includes hourly rate and total cost for job costing
   - Links to printer when assigned for utilization metrics
2. **PO → SO Linkage Fix** - Production orders now correctly linked to sales orders
   - Enables full transaction timeline queries
   - Supports audit trail from order → production → inventory
3. **Transaction Audit System** - Complete transaction verification for accounting
   - Timeline API shows all transactions for an order
   - Gap detection for missing reservations/consumptions
   - Health score calculation for order integrity
4. **E2E Test Suite** - Playwright tests for complete order-to-ship workflow
   - Tests quote → accept → convert → production → complete flow
   - Verifies all transaction types: reservation, consumption, machine_time, receipt

### Previous Wins (Nov 30, 2025 - Evening Session)

1. **Fulfillment Queue Backend** - Complete `/api/v1/admin/fulfillment/` endpoints
2. **BOM Explosion & Material Reservation** - When starting production, automatically reserves BOM components from inventory
3. **Material Consumption Tracking** - Converts reservations to actual consumption on production completion
4. **Good/Bad Quantity Tracking** - `complete-print` endpoint accepts qty_good and qty_bad
   - Good parts → added to finished goods inventory
   - Bad parts → recorded as scrap transactions with scrap rate
   - Shortfall detection → flags if reprint needed
5. **Printer Selection UI** - FulfillmentQueue.jsx now has printer dropdown when starting jobs
6. **Inventory Model Fix** - Fixed FK pointing to wrong table (warehouse_locations → inventory_locations)
7. **InventoryTransaction Model Fix** - Aligned model columns with actual DB schema

### Earlier Wins (Nov 30, 2025 - Morning)

1. **Lead Time Display** - Replaced print time with customer-friendly lead times (2 days if material in stock, 5 days if needs ordering or manual review)
2. **Stripe Tax Integration** - Automatic sales tax calculation via Stripe Tax with customer shipping address
3. **Multi-Color 3D Preview** - Live color updates in Three.js viewer when selecting primary color
4. **Primary Color Designation** - Click-to-set primary color for multi-material prints

### Previous Wins (Nov 29, 2025)

1. **Stripe Payment Integration** - Full checkout flow working end-to-end
2. **EasyPost Shipping Rates** - Real-time carrier rates with selection
3. **3D Model Viewer** - Three.js viewer restored on quote result page
4. **Dark Mode UI** - Full dark theme across portal
5. **Infill Pricing Bug Fix** - Solid (100%) now correctly priced (capped at 99% for BambuStudio compatibility)
6. **Quote Review Workflow** - Quotes with special instructions route to manual review
7. **Payment Validation** - Pay button disabled until shipping address and rate selected
8. **ML Dashboard ERP Integration** - Orders tab now reads from ERP internal API
9. **Inventory API Endpoints** - `/api/v1/internal/inventory/items`, `/summary`, `/transactions`
10. **Data Architecture** - ERP established as single source of truth for business data
11. **Material Catalog Expansion** - 146 SKUs across 12 material types (added PETG_CF, ABS_GF)
12. **Quote Conversion Service** - Unified service auto-creates Product + BOM + Sales Order + Production Order
13. **Inventory Schema Fix** - Added missing columns (last_counted, created_at, updated_at)

### Infill/Strength Pricing (Validated Nov 29)

| Strength | Infill | Material Usage | Price (test part) |
|----------|--------|----------------|-------------------|
| Light | 15% | 15.4g | $9.12 |
| Standard | 20% | 16.1g | $9.15 |
| Strong | 40% | 18.7g | $9.27 |
| Solid | 100%→99% | 26.2g | $9.68 |

*Note: 100% infill capped at 99% due to BambuStudio CLI limitation with sparse infill patterns*

---

## 🏗️ Repository Structure

### BLB3D-ERP (This Repo)
```
blb3d-erp/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # REST API endpoints
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic
│   ├── scripts/                 # SQL setup scripts
│   ├── tests/                   # Unit & integration tests
├── config/                      # Integration config
├── data_migration/              # Migration scripts & data
├── docs (root level .md files)  # Architecture, roadmap, etc.
```

### Quote-Portal (Customer Facing)
```
quote-portal/
├── src/
│   ├── pages/
│   │   ├── QuoteForm.jsx       # File upload, options
│   │   ├── QuoteResult.jsx     # Results, shipping, payment
│   │   ├── QuoteSubmitted.jsx  # Review confirmation
│   │   ├── PaymentSuccess.jsx  # Post-payment confirmation
│   ├── api/
│   │   ├── client.js           # API client functions
```

### Bambu-Print-Suite (Companion Repo)
```
bambu-print-suite/
├── ml-dashboard/
│   ├── backend/                 # FastAPI server (port 8001)
│   │   ├── routers/             # API routes
│   │   ├── managers/            # BOM, inventory, etc.
│   ├── frontend/                # React dashboard
├── quote-engine/
│   ├── slicer/
│       ├── quote_calculator.py  # Pricing logic
│       ├── gcode_analyzer.py    # G-code parsing
│       ├── bambu_slicer.py      # BambuStudio CLI wrapper
│       ├── production_profiles.py # Material/printer profiles
├── ml-engine/                   # ML training & models
├── Printer_Gcode_Files/         # Per-printer data (TMNT names)
```

---

## 🔌 Integration Architecture
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Quote Portal   │────▶│   ERP Backend   │────▶│  ML Dashboard   │
│   (port 5173)   │◀────│   (port 8000)   │◀────│   (port 8001)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                        │
         ┌─────────────────────┼────────────────────────┤
         ▼                     ▼                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Stripe      │     │   SQL Server    │     │  BambuStudio    │
│   (payments)    │     │    Express      │     │      CLI        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
┌─────────────────┐                                     ▼
│    EasyPost     │                            ┌─────────────────┐
│   (shipping)    │                            │  Printer Fleet  │
└─────────────────┘                            │ (MQTT Protocol) │
                                               └─────────────────┘
```

---

## 📋 Phase Status

### ✅ Phase 1: Foundation (COMPLETE)
- Database schema (20+ tables)
- FastAPI backend structure
- Authentication system
- Basic CRUD operations

### ✅ Phase 2A: Product Migration (COMPLETE)
- 633 products imported from Squarespace
- SKU standardization
- Category mapping

### ✅ Phase 2B: Quote System (COMPLETE)
- File upload (3MF/STL)
- BambuStudio CLI slicing
- G-code analysis
- Pricing calculation

### ✅ Phase 2C: Material System (COMPLETE)
- Material-specific cost multipliers
- Speed/volumetric flow limits
- Density-based weight calculation
- Profile inheritance resolution
- 146 material SKUs with colors (12 material types, 90 colors)

### ✅ Phase 2D: Customer Portal (COMPLETE)
- Customer login/registration with auto-generated numbers
- Quote flow with customer association
- Shipping address capture on quote acceptance
- Admin dashboard with filtering and customer info
- Sticky header for better UX

### ✅ Phase 2E: Payment Integration (COMPLETE)
- Stripe checkout integration
- EasyPost shipping rates
- Payment success/cancel flows
- Quote review workflow for manual approval
- Dark mode UI
- 3D model viewer (Three.js)
- Infill/strength selection with pricing
- Lead time calculation with stock warnings

### ✅ Phase 2F: ML Dashboard ERP Integration (COMPLETE)
- [x] Internal API endpoints for sales orders, customers, BOMs
- [x] ML Dashboard OrderManagement.jsx fetches from ERP
- [x] Inventory API endpoints (items, summary, transactions)
- [x] Raw SQL pattern for schema mismatches
- [x] Category mapping between ERP and frontend
- [x] Material catalog expanded to 146 SKUs (added PETG_CF, ABS_GF)
- [x] Material inventory cleanup (removed duplicates, verified 146 records)
- [ ] Material inventory stock verification (in_stock flags need actual values)

### ✅ Phase 3: Manufacturing Execution (COMPLETE)

- [x] Auto-create custom products from accepted quotes (quote_conversion_service.py)
- [x] Auto-create BOMs with material requirements from quotes
- [x] Auto-create Production Orders from paid quotes
- [x] Production order queue visualization (ML Dashboard FulfillmentQueue.jsx)
- [x] Printer assignment (dropdown on Start Production)
- [x] BOM explosion with material reservation on production start
- [x] Material consumption tracking on production complete
- [x] Good/bad quantity tracking with scrap transactions
- [x] Shortfall detection for reprints
- [x] **Machine time tracking** - Captures printer hours as transactions for metrics & costing
- [x] **Transaction audit system** - Timeline, gap detection, health score
- [x] **E2E test suite** - Playwright tests for complete order-to-ship workflow
- [x] Production order → Sales order linkage (enables full transaction queries)

### 📋 Phase 3.5: Manufacturing Insights (PLANNED)

- [ ] **Scheduling tab refinement** - Convert to MES (Manufacturing Execution System) focus
- [ ] Production variance reporting (scrap rate analysis)
- [ ] Printer utilization dashboards (based on machine_time transactions)
- [ ] Job costing reports (material + machine time costs)

### 📋 Phase 4: MRP & Procurement (PLANNED)

- [ ] Lead time field on MaterialInventory
- [ ] Quote adjusts delivery date when material OOS
- [ ] Automatic reorder trigger below reorder_point_kg
- [ ] Purchase order generation
- [ ] Low stock alerts/notifications
- [ ] Lot tracking

---

## ⚠️ Known Issues

### Active
- **STL Slicing** - BambuStudio CLI hangs on STL files (3MF works fine)
- **Dimension Scaling** - 3MF dimensions read 1.25× too large (trimesh issue)

### Technical Debt
- Material config scattered across multiple files (density, cost, speed)
- Machine rate hardcoded at $0/hr (should be $20-25)
- Need admin UI for pricing/material configuration

---

## 📝 TODO / Action Items

### Immediate (Before MVP Launch)
- [x] **Email Setup** - ✅ Configured (Google Workspace)
  - support@blb3dprinting.com
  - orders@blb3dprinting.com
  - customer_service@blb3dprinting.com
- [ ] Run database migration: `scripts/add_quote_customer_fields.sql`
- [ ] Test quote review workflow end-to-end
- [ ] Add email notification when quote submitted for review
- [ ] Add admin ability to send payment links to customers
- [ ] **Inventory Data Cleanup** (CSV review in progress)
  - Fix ~25 miscategorized items (boxes in Finished Goods)
  - Remove 4 duplicate SKUs (CW-CWDS-Black vs BK)
  - Fix 3 bad SKU formats (A00015, C-00)
  - Add names to 47 "Product M-00044-XX" items
  - Delete 2 test entries
- [ ] **Material Inventory** - Set actual in_stock flags (all show in_stock=1 with qty=0)

### Short-term
- [ ] Admin page for quote review with price adjustment
- [ ] Email templates for quote confirmation and payment links
- [ ] Webhook for Stripe payment confirmation
- [ ] Auto-create products from accepted portal quotes

### Medium-term
- [ ] Production order creation from paid quotes
- [ ] Printer assignment and scheduling
- [ ] Material inventory tracking
- [ ] Squarespace webhook integration

---

## 🚀 Quick Start
```bash
# Start ERP Backend (port 8000)
cd blb3d-erp/backend
python -m uvicorn app.main:app --reload --port 8000

# Start ML Dashboard (port 8001)  
cd bambu-print-suite/ml-dashboard/backend
python main.py

# Start Quote Portal (port 5173)
cd quote-portal
npm run dev

# Test URLs
Portal: http://localhost:5173/quote
ERP API: http://localhost:8000/docs
ML Dashboard: http://localhost:8001/docs
```

---

## 📚 Key Documentation

| Document | Purpose |
|----------|---------|
| ARCHITECTURE.md | System design & data flow |
| ROADMAP.md | Development phases |
| ISSUES.md | Bug tracking & fixes |
| AI_CONTEXT.md | Context for AI assistants |
| CLAUDE.md | Claude-specific instructions |
| BAMBU_PRINT_SUITE_INTEGRATION.md | Integration details |

---

**Maintained by:** Brandan @ BLB3D
**AI Assistance:** Claude (Anthropic)
