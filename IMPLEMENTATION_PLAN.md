# BLB3D ERP - Implementation Plan

**Created:** November 27, 2025  
**Goal:** Rock-solid quote-to-order flow that works like real life

---

## The Problem

We have working pieces that aren't connected:
- Quote engine slices 3MF files and calculates prices ✅
- Material catalog exists in CSV ✅
- Database models exist ✅
- BUT: Quote acceptance fails because BOM service can't find materials
- BUT: No color field on quotes
- BUT: Production orders never get created

---

## The Solution (In Order)

### Phase 1: Data Foundation
**Status: Scripts Created, Need to Run**

Get materials into the database so BOM service can find them.

#### What Already Exists:
- `scripts/material_tables.sql` - Creates 4 new tables
- `scripts/material_import.py` - Imports your CSV
- `backend/app/models/material.py` - SQLAlchemy models
- `MATERIAL_CATALOG.csv` - Your material data (147 items)

#### Tables Being Created:
| Table | Purpose |
|-------|---------|
| `material_types` | PLA Basic, PLA Matte, PETG-HF, ABS, ASA, TPU, etc. |
| `colors` | Black, White, Charcoal, Gold, etc. with hex codes |
| `material_colors` | Junction: which colors available for which materials |
| `material_inventory` | Links material+color to Product SKU for BOM |

#### New SKU Format:
```
MAT-FDM-PLA_BASIC-BLK    (was MAT-00059)
MAT-FDM-PLA_MATTE-CHARCOAL   (was MAT-00018)
```

#### Steps to Complete Phase 1:

**Step 1: Clean up duplicate folder**
```powershell
Remove-Item -Recurse -Force "C:\Users\brand\OneDrive\Documents\blb3d-erp\backend\app\models\materials"
```

**Step 2: Run SQL migration**
Open SSMS, connect to `localhost\SQLEXPRESS`, database `BLB3D_ERP`, then run:
```
C:\Users\brand\OneDrive\Documents\blb3d-erp\scripts\material_tables.sql
```

**Step 3: Import materials from CSV**
```powershell
cd C:\Users\brand\OneDrive\Documents\blb3d-erp

# Preview first (no changes):
python scripts/material_import.py "PATH_TO_YOUR_CSV\MATERIAL_CATALOG.csv" --dry-run

# Then run for real:
python scripts/material_import.py "PATH_TO_YOUR_CSV\MATERIAL_CATALOG.csv"
```

**Step 4: Verify**
```sql
SELECT COUNT(*) FROM material_types;      -- Should be ~10
SELECT COUNT(*) FROM colors;              -- Should be ~50+
SELECT COUNT(*) FROM material_colors;     -- Should be ~80+
SELECT COUNT(*) FROM material_inventory;  -- Should be ~80+
```

---

### Phase 2: Fix Quote Flow
**Status: Not Started**

Make quote acceptance actually work.

#### What Needs to Change:

1. **Add `color` field to Quote model** (SQL already in material_tables.sql)
   - Quote now stores: `material_type` (e.g., "PLA_MATTE") + `color` (e.g., "CHARCOAL")

2. **Update BOM Service** (`backend/app/services/bom_service.py`)
   - Current: Searches `Product.name.like('%PLA%')` - BROKEN
   - New: Query `MaterialInventory` by material_type + color → get SKU

3. **Update Portal Quote Endpoint** (`backend/app/api/v1/endpoints/quotes.py`)
   - Accept color from frontend
   - Store gcode_file_path from quote engine

4. **Fix Quote Acceptance Endpoint**
   - Create Product with gcode_file_path
   - Create BOM with correct material from MaterialInventory
   - Create ProductionOrder (currently missing!)

---

### Phase 3: Portal Integration
**Status: Not Started**

Make the customer portal use real inventory.

#### What Needs to Change:

1. **New API Endpoint: GET /api/v1/materials/available**
   - Returns material types that are `available_for_quoting=true`
   - Each material type includes its available colors (from `material_colors` junction)
   - Only shows colors where `in_stock=true` in `material_inventory`

2. **Update Quote Portal Frontend** (`quote-portal/src/pages/GetQuote.jsx`)
   - First dropdown: Material Type (PLA Basic, PLA Matte, PETG-HF, etc.)
   - Second dropdown: Colors (filtered by material type selection)
   - Color swatches with hex codes

3. **Quote Engine Integration**
   - Pass material_type_code to quote engine (not just "PLA")
   - Use correct price_multiplier from material_type table

---

### Phase 4: File Format Support
**Status: Not Started**

Allow STL and STEP files (not just 3MF).

- STL: Need to slice with BambuStudio CLI (add default settings)
- STEP: Need to convert to STL first, then slice

---

### Phase 5: Integrations (Later)
**Status: Future**

- Stripe: Payment processing
- Squarespace: Sync orders from website
- QuickBooks: Accounting integration
- WooCommerce: Alternative storefront

---

## File Locations Reference

### Backend (ERP)
```
C:\Users\brand\OneDrive\Documents\blb3d-erp\
├── backend\app\
│   ├── api\v1\endpoints\
│   │   ├── quotes.py          # Quote endpoints
│   │   └── sales_orders.py    # Order endpoints
│   ├── models\
│   │   ├── material.py        # Material models ✅
│   │   ├── quote.py           # Quote model
│   │   ├── product.py         # Product model
│   │   └── bom.py             # BOM model
│   └── services\
│       └── bom_service.py     # BOM creation (NEEDS UPDATE)
├── scripts\
│   ├── material_tables.sql    # SQL migration ✅
│   └── material_import.py     # CSV import ✅
```

### Quote Engine (Bambu Print Suite)
```
C:\Users\brand\OneDrive\Documents\bambu-print-suite\
├── ml-dashboard\backend\
│   └── main.py                # /api/quotes/generate endpoint
└── quote-engine\slicer\
    ├── quote_calculator.py    # Pricing logic
    └── production_profiles.py # Material profiles
```

### Portal Frontend
```
C:\Users\brand\OneDrive\Documents\quote-portal\
└── src\pages\
    ├── GetQuote.jsx           # Upload + material selection
    └── QuoteResult.jsx        # Quote display + accept
```

---

## Data Flow (When Complete)

```
Customer uploads 3MF
        ↓
Selects: Material Type (PLA Matte) + Color (Charcoal)
        ↓
Quote Engine slices → calculates price using material's price_multiplier
        ↓
Quote saved with: material_type="PLA_MATTE", color="CHARCOAL", gcode_path="..."
        ↓
Customer accepts quote
        ↓
System looks up: MaterialInventory WHERE material_type=PLA_MATTE AND color=CHARCOAL
        ↓
Finds: SKU="MAT-FDM-PLA_MATTE-CHARCOAL", product_id=123
        ↓
Creates: Custom Product + BOM (with material product_id=123) + Production Order
        ↓
Customer converts to Sales Order
        ↓
Admin sees order → Schedules print → Ships → Done
```

---

## Quick Start Tomorrow

1. Run Phase 1 steps (SQL + import)
2. Tell Claude: "Phase 1 complete, let's update the BOM service for Phase 2"

---

## Questions to Answer Later

- What colors do you want to show customers? (Limit to ~10 per material type?)
- Do you want customers to see all material types or just common ones?
- What's your actual CSV file path?
