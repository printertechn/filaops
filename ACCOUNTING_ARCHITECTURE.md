# Accounting Architecture Plan

## Overview

This document outlines the accounting and inventory flow architecture for BLB3D ERP, with the goal of integrating with QuickBooks Online for proper financial tracking.

## Goals

1. **Double-Entry Accounting** - All inventory and cost movements tracked via journal entries
2. **QuickBooks Online Integration** - Sync transactions to QBO for official books
3. **Inventory Flow** - Material reservation and consumption through production lifecycle
4. **Tax Compliance** - Proper COGS, WIP, and expense tracking for writeoffs

## Account Structure (Chart of Accounts)

### Assets
- **1100 - Cash** (synced from QBO)
- **1200 - Accounts Receivable** (customer invoices)
- **1300 - Inventory - Raw Materials** (filament, components, packaging)
- **1310 - Inventory - Work in Progress (WIP)** (materials in production)
- **1320 - Inventory - Finished Goods** (completed products ready to ship)

### Liabilities
- **2100 - Accounts Payable** (supplier invoices)
- **2200 - Sales Tax Payable**

### Revenue
- **4100 - Product Sales**
- **4200 - Shipping Revenue** (charged to customer)

### Cost of Goods Sold (COGS)
- **5100 - Material Cost**
- **5200 - Direct Labor** (if tracked)
- **5300 - Manufacturing Overhead**

### Expenses
- **6100 - Shipping Expense** (actual shipping cost)
- **6200 - Equipment & Supplies**
- **6300 - Utilities**

## Transaction Types

### 1. Purchase Receipt (Inventory In)
When raw materials arrive:
```
DR: 1300 Inventory - Raw Materials    $XXX
CR: 2100 Accounts Payable             $XXX
```

### 2. Production Start (Reserve Materials)
When production order starts:
```
DR: 1310 Inventory - WIP              $XXX (material cost from BOM)
CR: 1300 Inventory - Raw Materials    $XXX
```

### 3. Production Complete (QC Pass)
When production passes QC:
```
DR: 1320 Inventory - Finished Goods   $XXX (total production cost)
CR: 1310 Inventory - WIP              $XXX
```

### 4. Sale/Shipment
When order ships:
```
DR: 1200 Accounts Receivable          $XXX (invoice total)
CR: 4100 Product Sales                $XXX
CR: 4200 Shipping Revenue             $XXX
CR: 2200 Sales Tax Payable            $XXX

DR: 5100 Material Cost (COGS)         $XXX
CR: 1320 Inventory - Finished Goods   $XXX
```

### 5. Production Scrap/Waste
When production fails QC:
```
DR: 5100 Material Cost (COGS - Waste) $XXX
CR: 1310 Inventory - WIP              $XXX
```

## Inventory Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           INVENTORY LIFECYCLE                                 │
└──────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌──────────┐
  │   RECEIVE   │──────│   RESERVE   │──────│   CONSUME   │──────│   SHIP   │
  │  Materials  │      │  (Allocate) │      │ (Complete)  │      │  (COGS)  │
  └─────────────┘      └─────────────┘      └─────────────┘      └──────────┘
        │                    │                    │                    │
        ▼                    ▼                    ▼                    ▼
  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌──────────┐
  │ Raw Material│      │     WIP     │      │  Finished   │      │   SOLD   │
  │  Inventory  │      │  Inventory  │      │    Goods    │      │  (COGS)  │
  │   (1300)    │      │   (1310)    │      │   (1320)    │      │  (5100)  │
  └─────────────┘      └─────────────┘      └─────────────┘      └──────────┘
```

## Implementation Phases

### Phase 1: Internal Journal System (Current Priority)
- Create `JournalEntry` and `JournalLine` models in ERP
- Implement transaction service for common operations
- Hook into existing production workflow endpoints
- Track inventory movements without external sync

### Phase 2: Inventory Reservation
- Update `start_production()` to reserve materials from BOM
- Deduct from raw materials, add to WIP
- Block production if insufficient inventory
- Show material availability in fulfillment queue

### Phase 3: Inventory Consumption
- Update `pass_qc()` to consume WIP and create finished goods
- Update `fail_qc()` to write off WIP as scrap
- Track actual vs estimated material usage

### Phase 4: QuickBooks Online Integration
- Set up QBO OAuth2 connection
- Map ERP accounts to QBO Chart of Accounts
- Sync journal entries on configurable schedule (real-time or daily)
- Reconciliation reports

### Phase 5: Advanced Features (Future)
- Lot tracking for materials
- Serial numbers for finished goods
- Quality orders and inspection records
- Batch costing and variance analysis

## Data Models

### JournalEntry
```python
class JournalEntry:
    id: int
    entry_number: str  # JE-2025-001
    entry_date: datetime
    description: str
    source_type: str  # 'production_order', 'sales_order', 'purchase', 'adjustment'
    source_id: int    # Related record ID
    status: str       # 'draft', 'posted', 'void'
    posted_at: datetime
    qbo_sync_status: str  # 'pending', 'synced', 'error'
    qbo_journal_id: str   # QuickBooks journal entry ID
```

### JournalLine
```python
class JournalLine:
    id: int
    journal_entry_id: int
    account_code: str  # '1300', '5100', etc.
    account_name: str
    debit: Decimal
    credit: Decimal
    memo: str
    inventory_item_id: int  # If related to inventory
    quantity: Decimal       # Units affected
```

### InventoryReservation
```python
class InventoryReservation:
    id: int
    production_order_id: int
    inventory_item_id: int
    quantity_reserved: Decimal
    quantity_consumed: Decimal
    status: str  # 'reserved', 'consumed', 'released'
    reserved_at: datetime
    consumed_at: datetime
```

## QuickBooks Online API Integration

### Authentication
- OAuth2 with refresh token storage
- Scopes: `com.intuit.quickbooks.accounting`

### Key Endpoints
- `POST /v3/company/{realmId}/journalentry` - Create journal entry
- `GET /v3/company/{realmId}/query?query=select * from Account` - Get accounts
- `POST /v3/company/{realmId}/invoice` - Create invoice (optional)

### Sync Strategy
1. **Batch Sync (Recommended)**: Collect journal entries throughout day, sync at night
2. **Real-time Sync**: Post to QBO immediately after ERP commit
3. **Manual Sync**: Admin triggers sync from dashboard

### Error Handling
- Store failed syncs with error message
- Retry queue with exponential backoff
- Admin notification for sync failures
- Manual reconciliation tools

## API Endpoints Needed

### Journal Entries
- `POST /api/v1/accounting/journal-entries` - Create journal entry
- `GET /api/v1/accounting/journal-entries` - List journal entries
- `POST /api/v1/accounting/journal-entries/{id}/post` - Post entry

### Inventory Movements
- `POST /api/v1/inventory/{item_id}/reserve` - Reserve for production
- `POST /api/v1/inventory/{item_id}/consume` - Consume from WIP
- `POST /api/v1/inventory/{item_id}/release` - Release reservation

### QuickBooks Integration
- `GET /api/v1/accounting/qbo/auth-url` - Get OAuth URL
- `POST /api/v1/accounting/qbo/callback` - Handle OAuth callback
- `POST /api/v1/accounting/qbo/sync` - Trigger manual sync
- `GET /api/v1/accounting/qbo/status` - Sync status

## Configuration

```python
# .env settings for QuickBooks
QBO_CLIENT_ID=your_client_id
QBO_CLIENT_SECRET=your_client_secret
QBO_REDIRECT_URI=http://localhost:8000/api/v1/accounting/qbo/callback
QBO_ENVIRONMENT=sandbox  # or 'production'

# Sync settings
ACCOUNTING_SYNC_MODE=batch  # 'batch' or 'realtime'
ACCOUNTING_BATCH_HOUR=23    # Run batch sync at 11 PM
```

## Next Steps

1. Create database migrations for JournalEntry, JournalLine, InventoryReservation
2. Implement internal journal service
3. Hook journal creation into production workflow
4. Add inventory reservation to start_production
5. Add inventory consumption to pass_qc
6. Set up QuickBooks developer account and OAuth
7. Implement QBO sync service
8. Create admin UI for accounting/sync management

## References

- [QuickBooks Online API Documentation](https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/journalentry)
- [OAuth 2.0 for QuickBooks](https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization/oauth-2.0)
