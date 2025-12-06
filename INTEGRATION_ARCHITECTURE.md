# BLB3D ERP - Integration Architecture

**Created:** November 27, 2025
**Status:** Planning

---

## Overview

The ERP serves as the **single source of truth** for all business operations. All sales channels feed into the ERP, which then syncs to external services for payments, shipping, and accounting.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SALES CHANNELS                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │  Portal  │  │Squarespace│  │  TikTok  │  │   POS    │                │
│  │ (Custom) │  │  (Shop)  │  │(via Sqsp)│  │(Walk-in) │                │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘                │
└───────┼─────────────┼─────────────┼─────────────┼───────────────────────┘
        │             │             │             │
        │ Direct      │ Webhook     │ Via Sqsp    │ Manual
        │             │             │             │
        └─────────────┴──────┬──────┴─────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           BLB3D ERP                                     │
│                    (Single Source of Truth)                             │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     UNIFIED ORDER QUEUE                          │   │
│  │  order_type: quote_based | line_item                             │   │
│  │  source: portal | squarespace | tiktok | pos                     │   │
│  │  payment_status: paid | pending                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                             │                                           │
│           ┌─────────────────┼─────────────────┐                         │
│           ▼                 ▼                 ▼                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │  PRODUCTION  │  │  FINANCIAL   │  │  INVENTORY   │                  │
│  │              │  │              │  │              │                  │
│  │ • Print jobs │  │ • Revenue    │  │ • Materials  │                  │
│  │ • Scheduling │  │ • COGS       │  │ • Stock lvls │                  │
│  │ • Machine $  │  │ • Margins    │  │ • Reorder    │                  │
│  │ • Labor time │  │ • Fees       │  │ • Lot track  │                  │
│  └──────────────┘  └──────┬───────┘  └──────────────┘                  │
│                           │                                             │
└───────────────────────────┼─────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│    Stripe    │    │  QuickBooks  │    │   EasyPost   │
│  (Payments)  │    │ (Accounting) │    │  (Shipping)  │
│              │    │              │    │              │
│ Portal only  │    │ • Invoices   │    │ • Rates      │
│              │    │ • COGS       │    │ • Labels     │
│              │    │ • P&L        │    │ • Tracking   │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## Sales Channel Details

### 1. Quote Portal (Custom 3D Prints)
- **Payment**: Stripe (handled by ERP)
- **Shipping**: EasyPost rates shown in checkout
- **Flow**: Quote → Accept → Shipping → Stripe → ERP Order → Production

### 2. Squarespace (Product Catalog)
- **Payment**: Squarespace checkout (already paid when ERP receives)
- **Shipping**: Customer paid Squarespace rates
- **Flow**: Squarespace Order → Webhook → ERP Order → Production → EasyPost Label
- **Integration**: Squarespace Commerce API + Webhooks

### 3. TikTok Shop
- **Current Setup**: Orders flow through Squarespace
- **Payment**: TikTok handles
- **Shipping**: Must meet TikTok SLAs, tracking required
- **Flow**: TikTok → Squarespace → Webhook → ERP Order
- **Note**: Identified in ERP by source tag from Squarespace

### 4. POS (Point of Sale)
- **Payment**: Square Terminal / Cash
- **Shipping**: Usually pickup or local delivery
- **Flow**: Manual entry in ERP → Production (if needed)
- **Integration**: Square API (optional) or manual

---

## External Service Integrations

### Stripe (Payments)
- **Purpose**: Process payments for Quote Portal
- **Status**: ✅ IMPLEMENTED
- **Endpoints**:
  - `POST /payments/create-checkout` - Create checkout session
  - `POST /payments/verify` - Verify payment after redirect
  - `POST /payments/webhook` - Receive Stripe events

### EasyPost (Shipping)
- **Purpose**: Rate calculation + label generation for ALL channels
- **Status**: 🔲 PLANNED
- **Features Needed**:
  - Get shipping rates (show in portal checkout)
  - Generate labels (for all orders)
  - Track shipments
  - Push tracking to source platforms (Squarespace, TikTok)

### QuickBooks (Accounting)
- **Purpose**: Official books, tax prep, P&L
- **Status**: 🔲 PLANNED
- **Sync from ERP**:
  - Sales receipts (revenue)
  - Bills/expenses (COGS: materials, shipping)
  - Journal entries (complex transactions)
- **COGS Components**:
  - Material cost: grams used × $/kg
  - Machine time: print hours × $/hour
  - Labor: (optional) time × rate
  - Shipping cost: actual from EasyPost
  - Payment fees: Stripe %

### Squarespace (Sales Channel)
- **Purpose**: Receive orders from Squarespace + TikTok
- **Status**: 🔲 PLANNED
- **Integration**:
  - Webhook for new orders
  - API to push tracking numbers back
  - Inventory sync (optional)

---

## Data Flow Summary

### Order Creation
| Source | Payment | Enters ERP Via | Shipping Label |
|--------|---------|----------------|----------------|
| Portal | Stripe → ERP | Direct | EasyPost |
| Squarespace | Squarespace | Webhook | EasyPost |
| TikTok | TikTok (via Sqsp) | Webhook | EasyPost* |
| POS | Square/Cash | Manual | N/A or EasyPost |

*TikTok may require their own labels in some cases

### Financial Tracking
```
Order Revenue
  - Product price
  - Shipping charged
  - Tax collected

Order COGS
  - Material cost (from BOM)
  - Machine time cost
  - Shipping cost (actual)
  - Payment processing fee

Order Profit = Revenue - COGS
```

---

## Implementation Priority

| # | Integration | Complexity | Business Value |
|---|-------------|------------|----------------|
| 1 | ✅ Stripe | Done | Portal payments |
| 2 | EasyPost | Medium | All shipping labels |
| 3 | Squarespace Webhook | Low | 80% of orders? |
| 4 | QuickBooks | Medium | Proper accounting |
| 5 | Square POS | Low | Walk-in sales |

---

## Next Steps

1. **EasyPost Integration**
   - Sign up for test account
   - Implement rate calculation
   - Add label generation
   - Update portal checkout with shipping options

2. **Squarespace Webhook**
   - Set up webhook endpoint
   - Map Squarespace order → ERP order
   - Handle TikTok source identification

3. **QuickBooks Sync**
   - Connect QuickBooks API
   - Design sync schedule (real-time vs batch)
   - Map ERP transactions → QB entries

---

## Notes

- TikTok orders currently route through Squarespace - this simplifies integration
- QuickBooks becomes a downstream sync, not the source of truth
- All COGS tracking happens in ERP first, then syncs to QB
- EasyPost chosen over Pirate Ship API (easier integration, similar rates)
