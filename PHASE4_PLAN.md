# Phase 4: Core ERP Foundation

**Created:** December 4, 2025
**Status:** Planning
**Goal:** Build rock-solid ERP foundation before external integrations

---

## Strategy

Build internal ERP capabilities first, then integrate with external systems:

```
Phase A: Item Management     →  Foundation for everything
Phase B: Purchase Orders     →  Track what you buy
Phase C: Accounting Module   →  Track all financials
Phase D: Squarespace Sync    →  Connect retail orders
Phase E: QuickBooks Sync     →  Connect accounting
```

---

## Phase A: Item & Product Management

### Objective
Create a complete item catalog that supports finished goods, components, and supplies.

### Database Changes

#### New: `item_categories` table
```sql
CREATE TABLE item_categories (
    id INT IDENTITY PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,      -- 'FILAMENT', 'PACKAGING', 'HARDWARE'
    name VARCHAR(100) NOT NULL,
    parent_id INT NULL REFERENCES item_categories(id),
    description TEXT,
    sort_order INT DEFAULT 0,
    is_active BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETDATE()
);
```

#### Modify: `products` table
Add fields:
```sql
ALTER TABLE products ADD
    item_type VARCHAR(20) DEFAULT 'finished_good',  -- finished_good, component, supply, service
    category_id INT REFERENCES item_categories(id),
    cost_method VARCHAR(20) DEFAULT 'average',      -- fifo, average, standard
    standard_cost DECIMAL(10,2),
    average_cost DECIMAL(10,2),
    last_cost DECIMAL(10,2),
    lead_time_days INT,
    min_order_qty DECIMAL(10,2),
    reorder_point DECIMAL(10,2),
    preferred_vendor_id INT,  -- Future: references vendors
    upc VARCHAR(50),
    weight_oz DECIMAL(8,2),
    length_in DECIMAL(8,2),
    width_in DECIMAL(8,2),
    height_in DECIMAL(8,2);
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/items` | List all items with filters |
| POST | `/items` | Create item (any type) |
| GET | `/items/{id}` | Get item details |
| PATCH | `/items/{id}` | Update item |
| DELETE | `/items/{id}` | Soft delete item |
| GET | `/items/categories` | List categories |
| POST | `/items/categories` | Create category |
| POST | `/items/import` | Bulk CSV import |
| GET | `/items/export` | Export to CSV |

### Default Categories
```
FILAMENT
  ├── PLA
  ├── PETG
  ├── ABS
  ├── TPU
  └── Specialty

PACKAGING
  ├── Boxes
  ├── Bags
  └── Filler

HARDWARE
  ├── Fasteners
  └── Inserts

FINISHED_GOODS
  ├── Standard Products
  └── Custom Products

SERVICES
  └── Machine Time
```

### Deliverables
- [ ] ItemCategory model and migrations
- [ ] Product model updates
- [ ] CRUD API endpoints
- [ ] CSV import endpoint
- [ ] Seed default categories

---

## Phase B: Purchase Order System

### Objective
Track all purchases, receive inventory, match to invoices.

### Database Changes

#### New: `vendors` table
```sql
CREATE TABLE vendors (
    id INT IDENTITY PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,     -- 'BAMBU', 'AMAZON', 'ULINE'
    name VARCHAR(200) NOT NULL,
    contact_name VARCHAR(100),
    email VARCHAR(200),
    phone VARCHAR(50),
    website VARCHAR(200),
    address_line1 VARCHAR(200),
    address_line2 VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'US',
    payment_terms VARCHAR(50),            -- 'NET30', 'COD', 'PREPAID'
    tax_id VARCHAR(50),
    notes TEXT,
    is_active BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETDATE()
);
```

#### New: `purchase_orders` table
```sql
CREATE TABLE purchase_orders (
    id INT IDENTITY PRIMARY KEY,
    po_number VARCHAR(50) UNIQUE NOT NULL,  -- 'PO-2025-001'
    vendor_id INT NOT NULL REFERENCES vendors(id),
    status VARCHAR(20) DEFAULT 'draft',     -- draft, ordered, partial, received, cancelled
    order_date DATE,
    expected_date DATE,
    received_date DATE,
    subtotal DECIMAL(12,2),
    tax_amount DECIMAL(12,2),
    shipping_amount DECIMAL(12,2),
    total_amount DECIMAL(12,2),
    notes TEXT,
    created_by INT REFERENCES users(id),
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2
);
```

#### New: `purchase_order_lines` table
```sql
CREATE TABLE purchase_order_lines (
    id INT IDENTITY PRIMARY KEY,
    purchase_order_id INT NOT NULL REFERENCES purchase_orders(id),
    line_number INT NOT NULL,
    product_id INT NOT NULL REFERENCES products(id),
    description VARCHAR(500),
    qty_ordered DECIMAL(10,2) NOT NULL,
    qty_received DECIMAL(10,2) DEFAULT 0,
    unit_cost DECIMAL(10,4) NOT NULL,
    extended_cost DECIMAL(12,2),
    received_at DATETIME2
);
```

#### New: `vendor_invoices` table
```sql
CREATE TABLE vendor_invoices (
    id INT IDENTITY PRIMARY KEY,
    invoice_number VARCHAR(100) NOT NULL,
    vendor_id INT NOT NULL REFERENCES vendors(id),
    purchase_order_id INT REFERENCES purchase_orders(id),
    invoice_date DATE NOT NULL,
    due_date DATE,
    subtotal DECIMAL(12,2),
    tax_amount DECIMAL(12,2),
    total_amount DECIMAL(12,2),
    status VARCHAR(20) DEFAULT 'pending',  -- pending, paid, partial, void
    paid_date DATE,
    paid_amount DECIMAL(12,2),
    notes TEXT,
    created_at DATETIME2 DEFAULT GETDATE()
);
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/vendors` | List vendors |
| POST | `/vendors` | Create vendor |
| GET | `/purchase-orders` | List POs |
| POST | `/purchase-orders` | Create PO |
| PATCH | `/purchase-orders/{id}` | Update PO |
| POST | `/purchase-orders/{id}/receive` | Receive items |
| GET | `/vendor-invoices` | List invoices |
| POST | `/vendor-invoices` | Record invoice |
| PATCH | `/vendor-invoices/{id}/pay` | Mark paid |

### Deliverables
- [ ] Vendor model and CRUD
- [ ] PurchaseOrder model with lines
- [ ] VendorInvoice model
- [ ] Receiving workflow (creates inventory transactions)
- [ ] PO-to-Invoice matching

---

## Phase C: Accounting Module

### Objective
Track all financial activity internally before QB integration.

### Database Changes

#### New: `gl_accounts` table (Chart of Accounts)
```sql
CREATE TABLE gl_accounts (
    id INT IDENTITY PRIMARY KEY,
    account_number VARCHAR(20) UNIQUE NOT NULL,  -- '1000', '4000', '5000'
    name VARCHAR(200) NOT NULL,
    account_type VARCHAR(20) NOT NULL,  -- asset, liability, equity, revenue, expense
    parent_id INT REFERENCES gl_accounts(id),
    is_active BIT DEFAULT 1,
    description TEXT,
    normal_balance VARCHAR(10) DEFAULT 'debit'  -- debit or credit
);
```

#### New: `journal_entries` table
```sql
CREATE TABLE journal_entries (
    id INT IDENTITY PRIMARY KEY,
    entry_number VARCHAR(50) UNIQUE NOT NULL,  -- 'JE-2025-00001'
    entry_date DATE NOT NULL,
    description VARCHAR(500),
    source_type VARCHAR(50),       -- 'sale', 'purchase', 'receipt', 'payment', 'adjustment'
    source_id INT,                 -- Reference to source document
    is_posted BIT DEFAULT 0,
    posted_at DATETIME2,
    created_by INT REFERENCES users(id),
    created_at DATETIME2 DEFAULT GETDATE()
);
```

#### New: `journal_lines` table
```sql
CREATE TABLE journal_lines (
    id INT IDENTITY PRIMARY KEY,
    journal_entry_id INT NOT NULL REFERENCES journal_entries(id),
    line_number INT NOT NULL,
    gl_account_id INT NOT NULL REFERENCES gl_accounts(id),
    debit_amount DECIMAL(12,2) DEFAULT 0,
    credit_amount DECIMAL(12,2) DEFAULT 0,
    description VARCHAR(500)
);
```

#### New: `tax_rates` table
```sql
CREATE TABLE tax_rates (
    id INT IDENTITY PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    rate DECIMAL(6,4) NOT NULL,      -- 0.0625 for 6.25%
    jurisdiction VARCHAR(100),
    is_active BIT DEFAULT 1
);
```

### Standard Chart of Accounts
```
1000 - Cash (Asset)
1100 - Accounts Receivable (Asset)
1200 - Inventory - Raw Materials (Asset)
1210 - Inventory - Finished Goods (Asset)
1220 - Inventory - Packaging (Asset)
2000 - Accounts Payable (Liability)
2100 - Sales Tax Payable (Liability)
3000 - Owner's Equity (Equity)
3100 - Retained Earnings (Equity)
4000 - Sales Revenue (Revenue)
4100 - Shipping Revenue (Revenue)
5000 - Cost of Goods Sold (Expense)
5100 - Material Cost (Expense)
5200 - Labor Cost (Expense)
5300 - Packaging Cost (Expense)
6000 - Operating Expenses (Expense)
6100 - Shipping Expense (Expense)
```

### Auto-Generated Journal Entries

| Event | Debit | Credit |
|-------|-------|--------|
| Sale completed | AR + COGS | Revenue + Inventory |
| Payment received | Cash | AR |
| Purchase received | Inventory | AP |
| Vendor paid | AP | Cash |
| Scrap/waste | COGS | Inventory |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/accounting/chart-of-accounts` | List GL accounts |
| POST | `/accounting/chart-of-accounts` | Create account |
| GET | `/accounting/journal-entries` | List journal entries |
| POST | `/accounting/journal-entries` | Manual entry |
| GET | `/accounting/reports/trial-balance` | Trial balance |
| GET | `/accounting/reports/income-statement` | P&L |
| GET | `/accounting/reports/balance-sheet` | Balance sheet |
| GET | `/accounting/reports/tax-summary` | Tax collected/owed |

### Deliverables
- [ ] GLAccount model with COA seed
- [ ] JournalEntry and JournalLine models
- [ ] Auto-posting on sales/purchases/inventory
- [ ] Trial Balance report
- [ ] Income Statement report
- [ ] Balance Sheet report
- [ ] Sales Tax Summary report

---

## Phase D: Squarespace Integration (Future)

### Objective
Import retail orders from Squarespace into ERP.

### Approach
- Webhook or polling-based order import
- SKU mapping: Squarespace SKU → ERP Product
- Inventory sync back to Squarespace

### Deliverables
- [ ] Order import endpoint/webhook
- [ ] SKU mapping table
- [ ] Inventory sync (optional)

---

## Phase E: QuickBooks Integration (Future)

### Objective
Sync ERP accounting to QuickBooks Online.

### Approach
- Use QB Online API
- Sync: Customers, Invoices, Bills, Payments
- Read-only from QB: Bank transactions

### Deliverables
- [ ] QB OAuth connection
- [ ] Customer sync
- [ ] Invoice sync
- [ ] Bill sync
- [ ] Payment sync

---

## Implementation Order

### Week 1: Phase A - Items
1. Create ItemCategory model and seed data
2. Update Product model with new fields
3. Build CRUD endpoints for items/categories
4. Build CSV import endpoint

### Week 2: Phase B - Purchasing
1. Create Vendor model and CRUD
2. Create PurchaseOrder model with lines
3. Build receiving workflow
4. Create VendorInvoice model

### Week 3: Phase C - Accounting
1. Create GLAccount and seed COA
2. Create JournalEntry/Line models
3. Wire auto-posting to existing workflows
4. Build financial reports

### Week 4: Testing & Polish
1. End-to-end testing
2. Fix edge cases
3. Documentation
4. Ready for Squarespace/QB integration

---

## Files to Create/Modify

### New Models
- `app/models/item_category.py`
- `app/models/vendor.py`
- `app/models/purchase_order.py`
- `app/models/vendor_invoice.py`
- `app/models/gl_account.py`
- `app/models/journal_entry.py`
- `app/models/tax_rate.py`

### New Endpoints
- `app/api/v1/endpoints/items.py`
- `app/api/v1/endpoints/vendors.py`
- `app/api/v1/endpoints/purchase_orders.py`
- `app/api/v1/endpoints/accounting.py`

### New Services
- `app/services/purchasing_service.py`
- `app/services/accounting_service.py`

### New Schemas
- `app/schemas/item.py`
- `app/schemas/vendor.py`
- `app/schemas/purchase_order.py`
- `app/schemas/accounting.py`

---

## Success Criteria

### Phase A Complete When:
- [ ] Can create items with categories
- [ ] Can distinguish finished goods vs components vs supplies
- [ ] Can import items from CSV
- [ ] All items have cost tracking fields

### Phase B Complete When:
- [ ] Can create and manage vendors
- [ ] Can create POs and receive inventory
- [ ] Receiving creates inventory transactions
- [ ] Can record and pay vendor invoices

### Phase C Complete When:
- [ ] Chart of accounts is seeded
- [ ] All transactions auto-post journal entries
- [ ] Can generate P&L report
- [ ] Can generate Balance Sheet
- [ ] Can generate Sales Tax summary

---

## Notes

- **No Squarespace until Phase A-C are solid**
- **No QuickBooks until accounting module works**
- **Keep existing functionality working** - don't break quotes/production
- **Use existing patterns** - follow codebase conventions
