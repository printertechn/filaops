# BLB3D ERP Numbering Standards

## Overview

This document defines all item numbers (SKUs) and document numbers used throughout the BLB3D ERP system. Consistent numbering enables:
- Automated routing and categorization
- Cross-system integration (Squarespace, QuickBooks, etc.)
- Clear identification at a glance
- Scalability for SaaS product

---

## PART 1: ITEM NUMBERS (SKUs)

### 1.1 Raw Materials

**Format:** `MAT-{PROCESS}-{TYPE}-{COLOR}`

| Segment | Description | Examples |
|---------|-------------|----------|
| MAT | Material prefix | Always "MAT" |
| PROCESS | Manufacturing process | FDM, SLA, MJF |
| TYPE | Material type code | PLA_BASIC, PETG_HF, TPU_95A |
| COLOR | Color abbreviation (3-6 chars) | BLK, WHT, GLD, MYSTMAG |

**Examples:**
```
MAT-FDM-PLA_BASIC-BLK       PLA Basic Black
MAT-FDM-PLA_SILK-GLD        PLA Silk Gold
MAT-FDM-PETG_HF-WHT         PETG High Flow White
MAT-FDM-TPU_95A-CLR         TPU 95A Clear
MAT-SLA-RESIN_STD-GRY       Standard Resin Gray (future)
```

**Material Type Codes:**
| Code | Full Name | Base Material |
|------|-----------|---------------|
| PLA_BASIC | PLA Basic | PLA |
| PLA_MATTE | PLA Matte | PLA |
| PLA_SILK | PLA Silk | PLA |
| PLA_SILK_MULTI | PLA Silk Multi-Color | PLA |
| PETG_HF | PETG High Flow | PETG |
| PETG_TRANS | PETG Translucent | PETG |
| ABS | ABS | ABS |
| ASA | ASA | ASA |
| TPU_68D | TPU 68D (rigid flex) | TPU |
| TPU_95A | TPU 95A (soft flex) | TPU |

**Color Abbreviation Rules:**
- Standard colors: 3 letters (BLK, WHT, RED, BLU, GRN, YEL, ORG, PNK, PUR, GRY)
- Compound colors: 4-6 letters (DKBLU, LTGRY, HTPNK)
- Special names: 4-7 letters (MYSTMAG, PHANBLU, CHAMP)
- Multi-color: Use primary color or effect name

---

### 1.2 Finished Goods (Printed Products)

**Format:** `FG-{COLLECTION}-{PRODUCT}-{VARIANT}`

| Segment | Description | Examples |
|---------|-------------|----------|
| FG | Finished Goods prefix | Always "FG" |
| COLLECTION | Product line/collection | OCEAN, DESK, XMAS, KEYCHAIN |
| PRODUCT | Product identifier | TURTLE, HOOK, TREE, RING |
| VARIANT | Size/style variant (optional) | SM, LG, V2, GLOW |

**Examples:**
```
FG-OCEAN-TURTLE             Sea Turtle (standard)
FG-OCEAN-TURTLE-LG          Sea Turtle Large
FG-DESK-HOOK-DBL            Desk Hook Double
FG-XMAS-TREE-GLOW           Christmas Tree Glow-in-dark
FG-KEYCHAIN-RING            Keychain Ring Base
FG-CUSTOM-Q1042             Custom Quote Product (auto-generated)
```

**Collection Codes:**
| Code | Description |
|------|-------------|
| OCEAN | Ocean/sea life collection |
| DESK | Desk organizers & accessories |
| XMAS | Christmas/holiday seasonal |
| KEYCHAIN | Keychain products |
| HOME | Home decor items |
| GAME | Gaming accessories |
| TECH | Tech accessories (phone stands, etc.) |
| CUSTOM | Custom/one-off products from quotes |

---

### 1.3 Machine Parts (Printer Spares)

**Format:** `MP-{PRINTER}-{PART}`

| Segment | Description | Examples |
|---------|-------------|----------|
| MP | Machine Parts prefix | Always "MP" |
| PRINTER | Printer model code | A1, X1C, P1S, ENDER3 |
| PART | Part identifier | HOTEND-04, EXTRUDER, FILSENSOR |

**Examples:**
```
MP-A1-HOTEND-02             A1 Hotend 0.2mm nozzle
MP-A1-HOTEND-04             A1 Hotend 0.4mm nozzle
MP-A1-HOTEND-06             A1 Hotend 0.6mm nozzle
MP-A1-EXTRUDER              A1 Extruder Unit
MP-A1-FILSENSOR             A1 Filament Runout Sensor
MP-A1-FILHUB                A1/AMS Lite Filament Hub
MP-A1-COOLPLATE             A1 Cool Plate
MP-X1C-HOTEND-04            X1 Carbon Hotend 0.4mm
MP-ENDER3-HOTEND            Ender 3 V3 Hotend
```

---

### 1.4 Packaging

**Format:** `PKG-{TYPE}-{SIZE}`

| Segment | Description | Examples |
|---------|-------------|----------|
| PKG | Packaging prefix | Always "PKG" |
| TYPE | Package type | BOX, PAD, TAPE, MESH, WRAP |
| SIZE | Dimensions or descriptor | 6x6x6, 8x8, 2ROLL |

**Examples:**
```
PKG-BOX-4x4x4               Shipping Box 4x4x4"
PKG-BOX-6x6x6               Shipping Box 6x6x6"
PKG-BOX-12x9x4              Shipping Box 12x9x4"
PKG-PAD-8x8                 Corrugated Pad 8x8"
PKG-TAPE-2ROLL              Packing Tape (2 roll pack)
PKG-MESH-3x4                Mesh Drawstring Bag 3x4"
PKG-WRAP-HONEYCOMB          Honeycomb Paper Wrap
```

---

### 1.5 Components (Assembly Parts)

**Format:** `COMP-{NAME}` or `COMP-{TYPE}-{SPEC}`

| Segment | Description | Examples |
|---------|-------------|----------|
| COMP | Component prefix | Always "COMP" |
| NAME/TYPE | Component type | M3, LED, KEYRING |
| SPEC | Specification (optional) | 12MM, INSERT, SCREEN |

**Examples:**
```
COMP-KEYRING                Keychain Split Ring
COMP-LED-SCREEN             LED Screen Module
COMP-LED-TEALIGHT           LED Tealight Insert
COMP-LED-KIT                LED Lamp Kit (complete)
COMP-M3-12MM                M3 Screw 12mm
COMP-M3-INSERT              M3 Threaded Insert
COMP-DRAWER-22              22" Drawer Slides (pair)
COMP-MAGNET-6x3             6x3mm Neodymium Magnet
```

---

### 1.6 Consumables

**Format:** `CON-{NAME}`

**Examples:**
```
CON-PVA                     PVA Support Material
CON-LUBE-A1                 Lubricant for A1 Printer
CON-GLUE-STICK              Bed Adhesion Glue Stick
CON-IPA                     Isopropyl Alcohol
CON-NOZZLE-CLEAN            Nozzle Cleaning Filament
```

---

## PART 2: DOCUMENT NUMBERS

### 2.1 Quotes

**Format:** `QT-{YYYY}-{SEQUENCE}`

| Segment | Description |
|---------|-------------|
| QT | Quote prefix |
| YYYY | Year |
| SEQUENCE | 4-digit sequential number, resets annually |

**Examples:**
```
QT-2025-0001                First quote of 2025
QT-2025-0142                142nd quote of 2025
```

**Status Codes:**
| Status | Description |
|--------|-------------|
| DRAFT | Initial creation, editable |
| SENT | Sent to customer |
| ACCEPTED | Customer accepted, pending payment |
| PAID | Payment received |
| CONVERTED | Converted to Sales Order |
| EXPIRED | Past validity date |
| REJECTED | Customer declined |

---

### 2.2 Sales Orders

**Format:** `SO-{YYYY}-{SEQUENCE}`

| Segment | Description |
|---------|-------------|
| SO | Sales Order prefix |
| YYYY | Year |
| SEQUENCE | 4-digit sequential number, resets annually |

**Examples:**
```
SO-2025-0001                First sales order of 2025
SO-2025-0089                89th sales order of 2025
```

**Source Tracking:**
| Source | Description |
|--------|-------------|
| PORTAL | Customer quote portal |
| SQUARESPACE | Squarespace webhook |
| TIKTOK | TikTok Shop (via Squarespace) |
| POS | Point of Sale (Stripe Terminal) |
| MANUAL | Manual entry |

**Status Codes:**
| Status | Description |
|--------|-------------|
| PENDING | Awaiting confirmation/payment |
| CONFIRMED | Payment received, ready for production |
| IN_PRODUCTION | Production orders created |
| SHIPPED | All items shipped |
| DELIVERED | Delivery confirmed |
| CANCELLED | Order cancelled |

---

### 2.3 Production Orders

**Format:** `PROD-{YYYY}-{SEQUENCE}`

| Segment | Description |
|---------|-------------|
| PROD | Production Order prefix |
| YYYY | Year |
| SEQUENCE | 4-digit sequential number |

**Examples:**
```
PROD-2025-0001              First production order of 2025
PROD-2025-0234              234th production order
```

**Status Codes:**
| Status | Description |
|--------|-------------|
| QUEUED | Waiting for scheduling |
| SCHEDULED | Assigned to printer/time slot |
| PRINTING | Currently on printer |
| COMPLETED | Print finished successfully |
| FAILED | Print failed, needs requeue |
| QC_PENDING | Awaiting quality check |
| QC_PASSED | Quality approved |
| QC_FAILED | Quality rejected |

---

### 2.4 Purchase Orders (Supplier Orders)

**Format:** `PUR-{YYYY}-{SEQUENCE}`

| Segment | Description |
|---------|-------------|
| PUR | Purchase Order prefix |
| YYYY | Year |
| SEQUENCE | 4-digit sequential number |

**Examples:**
```
PUR-2025-0001               First purchase order of 2025
PUR-2025-0012               12th purchase order
```

**Status Codes:**
| Status | Description |
|--------|-------------|
| DRAFT | Being prepared |
| SENT | Sent to supplier |
| ACKNOWLEDGED | Supplier confirmed |
| PARTIAL | Partially received |
| RECEIVED | Fully received |
| CLOSED | Completed and reconciled |
| CANCELLED | Cancelled |

---

### 2.5 Receiving Documents

**Format:** `RCV-{YYYY}-{SEQUENCE}`

**Examples:**
```
RCV-2025-0001               First receiving document
RCV-2025-0045               45th receiving
```

Links to: Purchase Order, Inventory adjustments

---

### 2.6 Shipments

**Format:** `SHP-{YYYY}-{SEQUENCE}`

**Examples:**
```
SHP-2025-0001               First shipment of 2025
SHP-2025-0156               156th shipment
```

**Status Codes:**
| Status | Description |
|--------|-------------|
| PENDING | Awaiting label creation |
| LABELED | Label created (EasyPost) |
| PICKED_UP | Carrier picked up |
| IN_TRANSIT | In transit |
| DELIVERED | Delivered |
| EXCEPTION | Delivery exception |

---

### 2.7 Invoices (for QuickBooks sync)

**Format:** `INV-{YYYY}-{SEQUENCE}`

**Examples:**
```
INV-2025-0001               First invoice of 2025
```

**Note:** May mirror Sales Order number for simplicity:
- SO-2025-0042 → INV-2025-0042

---

### 2.8 Quality Orders / Inspection Reports

**Format:** `QC-{YYYY}-{SEQUENCE}`

**Examples:**
```
QC-2025-0001                First QC inspection
```

**Status Codes:**
| Status | Description |
|--------|-------------|
| PENDING | Awaiting inspection |
| PASSED | Passed inspection |
| FAILED | Failed, action required |
| REWORK | Sent for rework |
| SCRAPPED | Item scrapped |

---

### 2.9 Return Merchandise Authorization (RMA)

**Format:** `RMA-{YYYY}-{SEQUENCE}`

**Examples:**
```
RMA-2025-0001               First return of 2025
```

**Status Codes:**
| Status | Description |
|--------|-------------|
| REQUESTED | Customer requested return |
| APPROVED | Return approved |
| RECEIVED | Item received back |
| INSPECTED | Item inspected |
| REFUNDED | Refund issued |
| REPLACED | Replacement sent |
| DENIED | Return denied |

---

### 2.10 Inventory Adjustments

**Format:** `ADJ-{YYYY}-{SEQUENCE}`

**Examples:**
```
ADJ-2025-0001               First adjustment
```

**Adjustment Types:**
| Type | Description |
|------|-------------|
| COUNT | Physical count correction |
| DAMAGE | Damaged goods write-off |
| SCRAP | Scrap/waste |
| TRANSFER | Location transfer |
| RECEIPT | Receiving (non-PO) |
| ISSUE | Manual issue |

---

## PART 3: CUSTOMER & VENDOR NUMBERS

### 3.1 Customers

**Format:** `CUST-{SEQUENCE}`

**Examples:**
```
CUST-000001                 First customer
CUST-001042                 Customer #1042
```

**Customer Types:**
| Type | Description |
|------|-------------|
| B2C | Individual consumer |
| B2B | Business customer |
| WHOLESALE | Wholesale/reseller |

---

### 3.2 Vendors/Suppliers

**Format:** `VEND-{SEQUENCE}`

**Examples:**
```
VEND-0001                   Bambu Lab (direct)
VEND-0002                   Amazon (supplies)
VEND-0003                   ULINE (packaging)
```

---

## PART 4: DATABASE SEQUENCE CONFIGURATION

### Current Identity Values (After Cleanup)

| Table | Sequence Column | Current Value | Format |
|-------|-----------------|---------------|--------|
| quotes | id | 0 | QT-YYYY-{id} |
| sales_orders | id | 0 | SO-YYYY-{id} |
| production_orders | id | 0 | PROD-YYYY-{id} |
| products | id | 33+ | (varies by category) |
| customers | id | ? | CUST-{id} |
| inventory | id | 33+ | (internal) |

### Recommended: Add order_number columns

Rather than relying on auto-increment IDs, add explicit order_number columns:

```sql
ALTER TABLE quotes ADD quote_number VARCHAR(20);
ALTER TABLE sales_orders ADD order_number VARCHAR(20);
ALTER TABLE production_orders ADD production_number VARCHAR(20);
```

Then generate on insert:
```sql
-- Example trigger/procedure
SET @year = YEAR(GETDATE());
SET @seq = (SELECT ISNULL(MAX(seq), 0) + 1 FROM quote_sequence WHERE year = @year);
SET @quote_number = CONCAT('QT-', @year, '-', RIGHT('0000' + CAST(@seq AS VARCHAR), 4));
```

---

## PART 5: QUICK REFERENCE CARD

### Item Prefixes
| Prefix | Category | Example |
|--------|----------|---------|
| MAT- | Raw Materials | MAT-FDM-PLA_BASIC-BLK |
| FG- | Finished Goods | FG-OCEAN-TURTLE |
| MP- | Machine Parts | MP-A1-HOTEND-04 |
| PKG- | Packaging | PKG-BOX-6x6x6 |
| COMP- | Components | COMP-M3-INSERT |
| CON- | Consumables | CON-PVA |

### Document Prefixes
| Prefix | Document | Example |
|--------|----------|---------|
| QT- | Quote | QT-2025-0001 |
| SO- | Sales Order | SO-2025-0001 |
| PROD- | Production Order | PROD-2025-0001 |
| PUR- | Purchase Order | PUR-2025-0001 |
| RCV- | Receiving | RCV-2025-0001 |
| SHP- | Shipment | SHP-2025-0001 |
| INV- | Invoice | INV-2025-0001 |
| QC- | Quality Check | QC-2025-0001 |
| RMA- | Return | RMA-2025-0001 |
| ADJ- | Adjustment | ADJ-2025-0001 |

### Entity Prefixes
| Prefix | Entity | Example |
|--------|--------|---------|
| CUST- | Customer | CUST-000001 |
| VEND- | Vendor | VEND-0001 |

---

## PART 6: QUOTE-TO-SHIP WORKFLOW CHECKLIST

### Complete Flow (Identify Gaps)

```
[ ] 1. QUOTE CREATION
    [ ] Customer uploads 3D model
    [ ] System calculates pricing (material, time, labor)
    [ ] Quote saved as QT-YYYY-NNNN (DRAFT)
    
[ ] 2. QUOTE REVIEW (if required)
    [ ] Admin reviews complex quotes
    [ ] Adjust pricing if needed
    [ ] Quote status → SENT
    
[ ] 3. CUSTOMER ACCEPTANCE
    [ ] Customer views quote
    [ ] Customer accepts & pays (Stripe)
    [ ] Quote status → PAID
    
[ ] 4. QUOTE CONVERSION
    [ ] Auto-create Product (FG-CUSTOM-QNNNN) ← GAP?
    [ ] Auto-create BOM (material requirements) ← GAP?
    [ ] Auto-create Sales Order (SO-YYYY-NNNN)
    [ ] Quote status → CONVERTED
    
[ ] 5. PRODUCTION PLANNING
    [ ] Check material inventory
    [ ] If insufficient → flag for PO or delay
    [ ] Create Production Order (PROD-YYYY-NNNN)
    
[ ] 6. PRODUCTION EXECUTION
    [ ] Send to ML Dashboard
    [ ] Print job execution
    [ ] Production status updates
    [ ] Mark COMPLETED
    
[ ] 7. QUALITY CHECK
    [ ] Inspect printed item
    [ ] QC-YYYY-NNNN (PASSED/FAILED)
    [ ] If failed → requeue or scrap
    
[ ] 8. PACKING
    [ ] Select appropriate packaging
    [ ] Deduct packaging from inventory
    [ ] Prepare for shipment
    
[ ] 9. SHIPPING
    [ ] Create shipment (SHP-YYYY-NNNN)
    [ ] Generate label (EasyPost)
    [ ] Update tracking on Sales Order
    [ ] Sales Order status → SHIPPED
    
[ ] 10. ACCOUNTING SYNC
    [ ] Push invoice to QuickBooks
    [ ] Revenue recognition
    
[ ] 11. DELIVERY CONFIRMATION
    [ ] Track delivery status
    [ ] Sales Order status → DELIVERED
```

### Known Gaps to Address:

1. ~~**Quote → Product/BOM conversion**~~ - **IMPLEMENTED** (quote_conversion_service.py)
2. **Material availability check** - Endpoint exists, needs frontend integration
3. **Document number generation** - Implemented (SO-YYYY-NNN, PO-YYYY-NNN, Q-YYYY-NNN)
4. **QC workflow** - Not yet built
5. **QuickBooks sync** - Future phase
6. **Packaging inventory deduction** - Need to integrate

---

*Document Version: 1.0*
*Last Updated: 2025-11-29*
*Author: BLB3D ERP Development*
