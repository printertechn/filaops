# BLB3D ERP - System Architecture

> **Purpose**: This document explains the complete system architecture for AI assistants and developers.
> Keep this file updated as the system evolves.

---

## System Overview

BLB3D ERP is a custom ERP system for a 3D print farm operation. It replaces MRPeasy and integrates with:
- **Bambu Print Suite** (ML-Dashboard) for print scheduling and execution
- **Squarespace** (current) / **WooCommerce** (future) for retail B2C sales
- **Customer Portal** for B2B and custom quote orders

### Core Principle

**All order sources must converge to a unified production system.**

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   SQUARESPACE   │     │ CUSTOMER PORTAL │     │   WOOCOMMERCE   │
│   (Retail B2C)  │     │  (B2B/Custom)   │     │    (Future)     │
│                 │     │                 │     │                 │
│ • Standard SKUs │     │ • Custom quotes │     │ • Standard SKUs │
│ • Multi-item    │     │ • 3MF uploads   │     │ • Multi-item    │
│ • Pre-paid      │     │ • Auto-pricing  │     │ • Pre-paid      │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BLB3D ERP                               │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │  Products   │───▶│    BOMs     │───▶│ Production Orders   │ │
│  │  (Catalog)  │    │ (Materials) │    │ (Unified Queue)     │ │
│  └─────────────┘    └─────────────┘    └──────────┬──────────┘ │
│                                                   │             │
│  ┌─────────────┐    ┌─────────────┐               │             │
│  │  Inventory  │◀───│     MRP     │◀──────────────┘             │
│  │ (Materials) │    │ (Planning)  │                             │
│  └─────────────┘    └─────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BAMBU PRINT SUITE                           │
│                                                                 │
│  • ML-optimized printer scheduling                              │
│  • Real-time printer status via MQTT                            │
│  • Print job execution and monitoring                           │
│  • Actual vs estimated tracking for ML training                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Order Flow Architecture

### The Problem We're Solving

Orders come from multiple sources with different data structures:

| Source | Order Type | Products | BOMs | Payment |
|--------|-----------|----------|------|---------|
| Squarespace | Multi-line items | Known SKUs | Pre-defined | Pre-paid |
| Portal | Single custom item | No SKU (custom) | None exists | Pay later |
| WooCommerce | Multi-line items | Known SKUs | Pre-defined | Pre-paid |
| Manual | Either | Either | Either | Either |

**The Challenge**: Portal orders don't have products or BOMs, so MRP can't calculate material needs.

### The Solution: Unified Production Orders

Every order, regardless of source, must result in Production Orders that have:
1. A `product_id` (standard OR auto-created custom product)
2. A BOM with material requirements
3. Material type and quantity for MRP
4. GCODE file path for printing

---

## Data Models

### Sales Order Types

```
SALES_ORDER
├── order_type: 'line_item' | 'quote_based'
├── source: 'squarespace' | 'portal' | 'woocommerce' | 'manual'
├── source_order_id: (external reference)
│
├── IF order_type = 'line_item':
│   └── SALES_ORDER_LINES[] (one per product)
│       ├── product_id → PRODUCTS
│       ├── quantity
│       └── unit_price
│
└── IF order_type = 'quote_based':
    ├── quote_id → QUOTES
    └── product_id → PRODUCTS (auto-created custom product)
```

### Quote to Custom Product Flow

```
QUOTE (Customer Portal)
│
├── quote_number: "Q-2025-042"
├── product_name: "Custom Bracket" (freeform)
├── material_type: "PETG"
├── quantity: 50
├── material_grams: 125.5 (estimated)
├── files[]: uploaded 3MF files
│
│   ON QUOTE ACCEPTANCE:
│   ▼
├── Auto-create PRODUCT
│   ├── sku: "CUSTOM-Q-2025-042"
│   ├── name: "Custom Bracket"
│   ├── category: "custom"
│   └── gcode_path: (from uploaded file)
│
├── Auto-create BOM
│   └── BOM_LINE
│       ├── component_id → Material product (PETG)
│       └── quantity: 0.1255 kg
│
└── Create SALES_ORDER
    ├── order_type: 'quote_based'
    ├── quote_id: (this quote)
    └── product_id: (auto-created product)
```

### Marketplace to Sales Order Flow

```
SQUARESPACE WEBHOOK (order.created)
│
├── order_id: "SQ-12345"
├── line_items[]:
│   ├── {sku: "FG-00015", name: "Sea Turtle Blue", qty: 2}
│   ├── {sku: "FG-00022", name: "Dragon Red", qty: 1}
│   └── {sku: "FG-00008", name: "Fidget Cube", qty: 5}
│
│   ON WEBHOOK RECEIVED:
│   ▼
├── Map SKUs to existing PRODUCTS (via marketplace_product_mappings)
│
├── Create SALES_ORDER
│   ├── order_type: 'line_item'
│   ├── source: 'squarespace'
│   ├── source_order_id: "SQ-12345"
│   └── status: 'confirmed' (already paid)
│
└── Create SALES_ORDER_LINES[]
    ├── {product_id: 15, quantity: 2}
    ├── {product_id: 22, quantity: 1}
    └── {product_id: 8, quantity: 5}
```

### Production Order Creation

Both flows converge to create Production Orders:

```
SALES_ORDER
│
├── IF order_type = 'line_item':
│   │
│   │   FOR EACH sales_order_line:
│   │   ▼
│   └── Create PRODUCTION_ORDER
│       ├── sales_order_id
│       ├── sales_order_line_id
│       ├── product_id (from line)
│       ├── quantity (from line)
│       └── → BOM lookup works (product exists)
│
└── IF order_type = 'quote_based':
    │
    │   Create single PRODUCTION_ORDER:
    │   ▼
    └── Create PRODUCTION_ORDER
        ├── sales_order_id
        ├── quote_id
        ├── product_id (auto-created custom product)
        ├── quantity
        └── → BOM lookup works (auto-created BOM)
```

---

## Database Schema

### Core Tables

```sql
-- Products (both standard catalog and auto-created custom)
products
├── id (PK)
├── sku (UNIQUE) -- "FG-00015" or "CUSTOM-Q-2025-042"
├── name
├── category -- 'finished_good', 'material', 'custom'
├── type -- 'standard', 'custom'
├── is_active
├── unit_cost
├── gcode_file_path -- for 3D printed products
└── notes

-- Bill of Materials
boms
├── id (PK)
├── product_id (FK → products) -- finished good
├── code (UNIQUE)
├── name
├── is_active
└── total_cost

bom_lines
├── id (PK)
├── bom_id (FK → boms)
├── component_id (FK → products) -- raw material
├── quantity
└── unit_of_measure

-- Sales Orders (hybrid: supports both types)
sales_orders
├── id (PK)
├── order_number (UNIQUE) -- "SO-2025-001"
├── order_type -- 'line_item' | 'quote_based'
├── source -- 'squarespace' | 'portal' | 'woocommerce' | 'manual'
├── source_order_id -- external reference
├── customer_id (FK → customers)
├── quote_id (FK → quotes, nullable) -- for quote_based
├── product_id (FK → products, nullable) -- for quote_based
├── status
├── payment_status
├── ... (shipping, totals, timestamps)

-- Sales Order Lines (for marketplace multi-item orders)
sales_order_lines
├── id (PK)
├── sales_order_id (FK → sales_orders)
├── product_id (FK → products)
├── quantity
├── unit_price
└── total

-- Quotes (customer portal)
quotes
├── id (PK)
├── user_id (FK → users)
├── quote_number (UNIQUE) -- "Q-2025-042"
├── product_name -- freeform text (before product created)
├── material_type
├── quantity
├── material_grams
├── total_price
├── status -- draft, pending, approved, accepted, rejected, cancelled
├── sales_order_id (FK, nullable) -- set after conversion
├── files[] → quote_files
└── expires_at

-- Production Orders (unified queue for all sources)
production_orders
├── id (PK)
├── code (UNIQUE) -- "PO-2025-001"
├── product_id (FK → products) -- ALWAYS populated
├── quantity
├── sales_order_id (FK → sales_orders, nullable)
├── sales_order_line_id (FK → sales_order_lines, nullable)
├── quote_id (FK → quotes, nullable)
├── source_type -- 'squarespace', 'portal', 'woocommerce', 'manual'
├── status
├── priority
└── ... (scheduling, timestamps)

-- Print Jobs (linked to Bambu Suite)
print_jobs
├── id (PK)
├── production_order_id (FK → production_orders)
├── printer_id
├── bambu_job_id -- external reference
├── status
├── gcode_file
├── estimated_time_minutes
├── actual_time_minutes
├── material_grams_used
└── ... (timestamps)

-- Marketplace Product Mapping
marketplace_product_mappings
├── id (PK)
├── marketplace -- 'squarespace', 'woocommerce'
├── marketplace_product_id
├── marketplace_sku
├── erp_product_id (FK → products)
└── UNIQUE(marketplace, marketplace_product_id)

-- Inventory
inventory
├── id (PK)
├── product_id (FK → products)
├── location_id (FK → inventory_locations)
├── on_hand_quantity
├── allocated_quantity
├── available_quantity (computed)
└── cost_per_unit
```

---

## API Endpoints

### Authentication
```
POST /api/v1/auth/register     - Create user account
POST /api/v1/auth/login        - Login, get JWT tokens
POST /api/v1/auth/refresh      - Refresh access token
GET  /api/v1/auth/me           - Get current user
PATCH /api/v1/auth/me          - Update profile
```

### Quotes (Customer Portal)
```
POST /api/v1/quotes                    - Create quote with file upload
GET  /api/v1/quotes                    - List user's quotes
GET  /api/v1/quotes/{id}               - Get quote details
PATCH /api/v1/quotes/{id}/accept       - Accept quote (triggers product creation)
PATCH /api/v1/quotes/{id}/reject       - Reject quote
POST /api/v1/quotes/{id}/cancel        - Cancel quote
```

### Sales Orders
```
POST /api/v1/sales-orders/convert/{quote_id}  - Convert quote to order
GET  /api/v1/sales-orders                      - List orders
GET  /api/v1/sales-orders/{id}                 - Get order details
PATCH /api/v1/sales-orders/{id}/status         - Update status
PATCH /api/v1/sales-orders/{id}/payment        - Update payment
PATCH /api/v1/sales-orders/{id}/shipping       - Update shipping
POST /api/v1/sales-orders/{id}/cancel          - Cancel order
```

### Marketplace Webhooks
```
POST /api/v1/webhooks/squarespace/order-created   - New Squarespace order
POST /api/v1/webhooks/squarespace/order-updated   - Order updated
POST /api/v1/webhooks/woocommerce/order-created   - New WooCommerce order (future)
```

### Production Orders
```
POST /api/v1/production-orders              - Create production order
GET  /api/v1/production-orders              - List production orders
GET  /api/v1/production-orders/{id}         - Get details
POST /api/v1/production-orders/{id}/start   - Start production
POST /api/v1/production-orders/{id}/complete - Complete production
```

### Integration (Bambu Suite)
```
GET  /api/v1/integration/sync-status       - Check connection
GET  /api/v1/integration/printer-status    - Get all printer status
POST /api/v1/integration/material-check    - Check material availability
```

### Products & Inventory
```
GET  /api/v1/products                      - List products
GET  /api/v1/products/{id}                 - Get product
POST /api/v1/inventory/check               - Check availability
POST /api/v1/inventory/transactions        - Record transaction
GET  /api/v1/inventory/materials           - List materials
```

---

## Status Flows

### Quote Status
```
draft → pending → approved → accepted → (converted to order)
                ↘ rejected
        ↘ cancelled
        ↘ (expired after 30 days)
```

### Sales Order Status
```
pending → confirmed → in_production → quality_check → shipped → delivered → completed
                   ↘ on_hold (can resume)
        ↘ cancelled
```

### Production Order Status
```
draft → confirmed → queued → printing → completed
                          ↘ failed (can retry)
      ↘ cancelled
```

### Payment Status
```
pending → paid
        ↘ partial → paid
        ↘ refunded
```

---

## MRP Material Planning

### How MRP Calculates Material Needs

```sql
-- Get total material requirements for pending/confirmed production orders
SELECT 
    m.sku AS material_sku,
    m.name AS material_name,
    SUM(bl.quantity * po.quantity) AS total_required_kg,
    COALESCE(inv.available_quantity, 0) AS available_kg,
    SUM(bl.quantity * po.quantity) - COALESCE(inv.available_quantity, 0) AS shortage_kg
FROM production_orders po
JOIN products p ON po.product_id = p.id
JOIN boms b ON p.id = b.product_id AND b.is_active = 1
JOIN bom_lines bl ON b.id = bl.bom_id
JOIN products m ON bl.component_id = m.id  -- material
LEFT JOIN (
    SELECT product_id, SUM(available_quantity) as available_quantity
    FROM inventory
    GROUP BY product_id
) inv ON m.id = inv.product_id
WHERE po.status IN ('pending', 'confirmed', 'queued')
GROUP BY m.sku, m.name, inv.available_quantity
HAVING SUM(bl.quantity * po.quantity) > COALESCE(inv.available_quantity, 0)
```

**Key Point**: This query works for BOTH standard products and custom products because:
- Standard products have pre-defined BOMs
- Custom products get auto-created BOMs when quotes are accepted

---

## Integration Points

### Bambu Print Suite

**ERP → Bambu Suite**:
- Create print job when production order starts
- Send: product SKU, quantity, material type, priority, GCODE path

**Bambu Suite → ERP**:
- Printer status updates (via polling or webhook)
- Job progress updates
- Job completion with actual metrics (time, material used)

### Squarespace

**Squarespace → ERP** (webhook):
- `order.created` - New order placed
- `order.updated` - Order modified
- `order.fulfilled` - Order shipped (update from their side)

**ERP → Squarespace** (API):
- Update fulfillment status
- Add tracking number

### Future: WooCommerce

Same pattern as Squarespace but different webhook format.

---

## File Storage

### Quote Files (Customer Uploads)
```
/uploads/quotes/{year}/{month}/{quote_id}/
├── original_filename.3mf
├── processed_model.gcode (if sliced)
└── thumbnail.png (if generated)
```

### GCODE Files (Standard Products)
```
/gcode/{product_sku}/
├── default.gcode
├── 0.2mm_standard.gcode
└── 0.1mm_detail.gcode
```

---

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=mssql+pyodbc://localhost\SQLEXPRESS/BLB3D_ERP?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes

# JWT Auth
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Bambu Suite Integration
BAMBU_SUITE_API_URL=http://localhost:8001
BAMBU_SUITE_API_KEY=your-api-key

# Squarespace Integration
SQUARESPACE_API_KEY=your-api-key
SQUARESPACE_WEBHOOK_SECRET=your-webhook-secret

# File Storage
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=100

# Google Cloud Storage (optional backup)
GCS_ENABLED=false
GCS_BUCKET_NAME=blb3d-quote-files
```

---

## Development Notes

### Running Locally
```bash
# ERP Backend (port 8000)
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Bambu Print Suite (port 8001)
cd ../bambu-print-suite/ml-dashboard/backend
python -m uvicorn main:app --reload --port 8001
```

### Testing the Flow
```bash
# 1. Create a quote (simulates portal customer)
curl -X POST "http://localhost:8000/api/v1/quotes" \
  -H "Authorization: Bearer {token}" \
  -F "files=@test.3mf" \
  -F "material_type=PLA" \
  -F "quantity=10"

# 2. Accept the quote (creates custom product + BOM)
curl -X PATCH "http://localhost:8000/api/v1/quotes/{id}/accept" \
  -H "Authorization: Bearer {token}"

# 3. Convert to sales order
curl -X POST "http://localhost:8000/api/v1/sales-orders/convert/{quote_id}" \
  -H "Authorization: Bearer {token}" \
  -d '{"shipping_address_line1": "123 Main St", ...}'

# 4. Check MRP can see material needs
curl "http://localhost:8000/api/v1/mrp/material-requirements"
```

---

## Known Gaps / TODOs

### Critical (Before Go-Live)
- [ ] Squarespace webhook integration
- [ ] Auto-create custom products from quotes (modify convert endpoint)
- [ ] Bring back SalesOrderLine model
- [ ] Admin endpoints for quote review
- [ ] SKU mapping table for marketplace products

### Important
- [ ] Email notifications (order confirmation, shipping)
- [ ] Background job for expired quote cleanup
- [ ] Rate limiting on auth endpoints
- [ ] File size validation on uploads
- [ ] Proper transaction handling (rollback on failures)

### Nice to Have
- [ ] WooCommerce integration
- [ ] Stripe payment integration
- [ ] Shipping carrier API integration
- [ ] Cost variance reporting
- [ ] Customer reorder from previous orders

---

## Glossary

| Term | Definition |
|------|------------|
| **Quote** | Customer request for pricing on a custom job (portal) |
| **Sales Order** | Confirmed customer order (from any source) |
| **Production Order** | Internal work order to manufacture product(s) |
| **Print Job** | Single print execution on a specific printer |
| **BOM** | Bill of Materials - list of components to make a product |
| **MRP** | Material Requirements Planning - calculates what materials are needed |
| **Custom Product** | Auto-created product record for portal quote orders |
| **Standard Product** | Pre-defined product in catalog with existing BOM |

---

*Last Updated: November 2025*
*Maintainer: BLB3D Team*
