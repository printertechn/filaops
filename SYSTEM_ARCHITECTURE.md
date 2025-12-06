# BLB3D Print Farm - Complete System Architecture

## Executive Summary

BLB3D is a custom ERP system for a 3D print farm operation, designed to replace MRPeasy and unify multiple sales channels into a single production management system.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           BLB3D PRINT FARM ECOSYSTEM                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ Squarespace  │  │    Quote     │  │  WooCommerce │  │   Direct     │        │
│  │   (B2C)      │  │   Portal     │  │   (Future)   │  │   Sales      │        │
│  │  Retail      │  │   (B2B)      │  │              │  │              │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                 │                 │                 │                │
│         └────────────┬────┴────────────┬────┴─────────────────┘                │
│                      │                 │                                        │
│                      ▼                 ▼                                        │
│         ┌────────────────────────────────────────────┐                         │
│         │              UNIFIED ORDER INTAKE          │                         │
│         │         (Sales Orders & Quotes)            │                         │
│         └────────────────────┬───────────────────────┘                         │
│                              │                                                  │
│                              ▼                                                  │
│         ┌────────────────────────────────────────────┐                         │
│         │           PRODUCTION PLANNING              │                         │
│         │    (MRP, Scheduling, Material Planning)    │                         │
│         └────────────────────┬───────────────────────┘                         │
│                              │                                                  │
│                              ▼                                                  │
│         ┌────────────────────────────────────────────┐                         │
│         │            PRINTER FLEET                   │                         │
│         │   Donatello │ Leonardo │ Michelangelo │    │                         │
│         │     (A1)    │  (P1S)   │    (A1)      │    │ Raphael (A1)            │
│         └────────────────────┬───────────────────────┘                         │
│                              │                                                  │
│                              ▼                                                  │
│         ┌────────────────────────────────────────────┐                         │
│         │              FULFILLMENT                   │                         │
│         │      (Shipping, Tracking, Delivery)        │                         │
│         └────────────────────────────────────────────┘                         │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              TECHNOLOGY STACK                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  FRONTEND                        BACKEND                      INFRASTRUCTURE   │
│  ────────                        ───────                      ──────────────   │
│                                                                                 │
│  ┌─────────────┐                ┌─────────────┐              ┌─────────────┐   │
│  │   React     │                │   FastAPI   │              │ SQL Server  │   │
│  │   + Vite    │                │  (Python)   │              │   Express   │   │
│  │             │                │             │              │             │   │
│  │ • Quote     │                │ • ERP API   │              │ • Products  │   │
│  │   Portal    │                │   (8000)    │              │ • Orders    │   │
│  │ • Admin     │                │             │              │ • Quotes    │   │
│  │   Dashboard │                │ • ML Dash   │              │ • Inventory │   │
│  └─────────────┘                │   (8001)    │              │ • Materials │   │
│                                 └─────────────┘              └─────────────┘   │
│  ┌─────────────┐                                                               │
│  │  Three.js   │                ┌─────────────┐              ┌─────────────┐   │
│  │ 3D Viewer   │                │ BambuStudio │              │    MQTT     │   │
│  └─────────────┘                │     CLI     │              │  Protocol   │   │
│                                 │             │              │             │   │
│  ┌─────────────┐                │ • Slicing   │              │ • Printer   │   │
│  │ Tailwind    │                │ • G-code    │              │   Status    │   │
│  │    CSS      │                │ • Profiles  │              │ • Job Ctrl  │   │
│  └─────────────┘                └─────────────┘              └─────────────┘   │
│                                                                                 │
│  EXTERNAL SERVICES                                                              │
│  ─────────────────                                                              │
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │   Stripe    │  │  EasyPost   │  │ Squarespace │  │   GitHub    │           │
│  │  Payments   │  │  Shipping   │  │  Webhooks   │  │   Actions   │           │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            THREE REPOSITORIES                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  REPO 1: blb3d-erp (blb3d-print-farm)                                   │   │
│  │  ─────────────────────────────────────                                  │   │
│  │  Purpose: Core ERP backend & business logic                             │   │
│  │                                                                         │   │
│  │  backend/                                                               │   │
│  │  ├── app/                                                               │   │
│  │  │   ├── api/v1/endpoints/     # REST API endpoints                     │   │
│  │  │   │   ├── quotes.py         # Quote CRUD + review workflow           │   │
│  │  │   │   ├── sales_orders.py   # Order management                       │   │
│  │  │   │   ├── products.py       # Product catalog                        │   │
│  │  │   │   ├── shipping.py       # EasyPost integration                   │   │
│  │  │   │   └── stripe_webhook.py # Payment webhooks                       │   │
│  │  │   ├── models/               # SQLAlchemy ORM models                  │   │
│  │  │   ├── schemas/              # Pydantic validation schemas            │   │
│  │  │   └── services/             # Business logic services                │   │
│  │  │       └── bambu_client.py   # ML Dashboard API client                │   │
│  │  └── scripts/                  # SQL migrations                         │   │
│  │                                                                         │   │
│  │  Port: 8000                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  REPO 2: bambu-print-suite                                              │   │
│  │  ─────────────────────────────                                          │   │
│  │  Purpose: Print farm operations, slicing, ML, production                │   │
│  │                                                                         │   │
│  │  ml-dashboard/                                                          │   │
│  │  ├── backend/                  # FastAPI server (port 8001)             │   │
│  │  │   ├── main.py               # Quote generation API                   │   │
│  │  │   ├── routers/              # BOM, inventory, orders                 │   │
│  │  │   └── managers/             # Business logic                         │   │
│  │  └── frontend/                 # React admin dashboard                  │   │
│  │                                                                         │   │
│  │  quote-engine/                                                          │   │
│  │  └── slicer/                                                            │   │
│  │      ├── bambu_slicer.py       # BambuStudio CLI wrapper                │   │
│  │      ├── quote_calculator.py   # Pricing logic                          │   │
│  │      ├── gcode_analyzer.py     # G-code parsing                         │   │
│  │      └── production_profiles.py # Material/printer profiles             │   │
│  │                                                                         │   │
│  │  ml-engine/                    # ML training & time estimation          │   │
│  │                                                                         │   │
│  │  Port: 8001                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  REPO 3: quote-portal                                                   │   │
│  │  ────────────────────────                                               │   │
│  │  Purpose: Customer-facing quote & checkout experience                   │   │
│  │                                                                         │   │
│  │  src/                                                                   │   │
│  │  ├── pages/                                                             │   │
│  │  │   ├── GetQuote.jsx          # File upload, options selection         │   │
│  │  │   ├── QuoteResult.jsx       # Results, shipping, payment             │   │
│  │  │   ├── QuoteSubmitted.jsx    # Review confirmation                    │   │
│  │  │   └── PaymentSuccess.jsx    # Post-payment confirmation              │   │
│  │  ├── components/                                                        │   │
│  │  │   ├── ModelViewer.jsx       # Three.js 3D preview                    │   │
│  │  │   └── Layout.jsx            # App shell                              │   │
│  │  └── api/                                                               │   │
│  │      └── client.js             # API client functions                   │   │
│  │                                                                         │   │
│  │  Port: 5173 (dev)                                                       │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow - Quote to Delivery

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE ORDER LIFECYCLE FLOW                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  PHASE 1: QUOTE GENERATION                                                      │
│  ─────────────────────────────                                                  │
│                                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │ Customer │───▶│  Upload  │───▶│  Quote   │───▶│  Slice   │───▶│ Analyze  │ │
│  │ Portal   │    │   3MF    │    │  Portal  │    │ (Bambu)  │    │  G-code  │ │
│  │ (5173)   │    │  File    │    │  (8000)  │    │  (8001)  │    │          │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └────┬─────┘ │
│                                                                       │        │
│                                         ┌─────────────────────────────┘        │
│                                         ▼                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                                  │
│  │ Display  │◀───│ Calculate│◀───│  Parse   │                                  │
│  │  Quote   │    │  Price   │    │ Time/Mat │                                  │
│  │ + Options│    │          │    │          │                                  │
│  └──────────┘    └──────────┘    └──────────┘                                  │
│                                                                                 │
│  PHASE 2: CHECKOUT                                                              │
│  ─────────────────                                                              │
│                                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Select   │───▶│  Enter   │───▶│   Get    │───▶│  Select  │                  │
│  │ Material │    │ Shipping │    │  Rates   │    │  Rate    │                  │
│  │ + Options│    │ Address  │    │ EasyPost │    │          │                  │
│  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘                  │
│                                                       │                        │
│                       ┌───────────────────────────────┘                        │
│                       ▼                                                        │
│  AUTO-APPROVED?  ┌─────────┐                                                   │
│  (no notes,      │ Decision│                                                   │
│   price < $X)    └────┬────┘                                                   │
│                       │                                                        │
│         ┌─────────────┴─────────────┐                                          │
│         ▼                           ▼                                          │
│  ┌──────────────┐           ┌──────────────┐                                   │
│  │   YES: Pay   │           │  NO: Submit  │                                   │
│  │   via Stripe │           │  for Review  │                                   │
│  └──────┬───────┘           └──────┬───────┘                                   │
│         │                          │                                           │
│         ▼                          ▼                                           │
│  ┌──────────────┐           ┌──────────────┐                                   │
│  │   Stripe     │           │   Capture    │                                   │
│  │  Checkout    │           │    Email     │                                   │
│  └──────┬───────┘           └──────┬───────┘                                   │
│         │                          │                                           │
│         ▼                          ▼                                           │
│  ┌──────────────┐           ┌──────────────┐                                   │
│  │   Payment    │           │   Engineer   │                                   │
│  │   Success    │           │   Reviews    │                                   │
│  └──────┬───────┘           └──────┬───────┘                                   │
│         │                          │                                           │
│         │                          ▼                                           │
│         │                   ┌──────────────┐                                   │
│         │                   │ Send Payment │                                   │
│         │                   │    Link      │                                   │
│         │                   └──────┬───────┘                                   │
│         │                          │                                           │
│         └────────────┬─────────────┘                                           │
│                      ▼                                                         │
│                                                                                 │
│  PHASE 3: ORDER CREATION (Future)                                              │
│  ─────────────────────────────────                                              │
│                                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                      │
│  │   Create     │───▶│   Create     │───▶│   Create     │                      │
│  │ Sales Order  │    │   Product    │    │     BOM      │                      │
│  │              │    │  (if custom) │    │  (materials) │                      │
│  └──────────────┘    └──────────────┘    └──────────────┘                      │
│                                                                                 │
│  PHASE 4: PRODUCTION (Future)                                                   │
│  ─────────────────────────────                                                  │
│                                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Create     │───▶│   Assign     │───▶│    Print     │───▶│   Quality    │ │
│  │ Prod Order   │    │   Printer    │    │     Job      │    │    Check     │ │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘ │
│                                                                                 │
│  PHASE 5: FULFILLMENT (Future)                                                  │
│  ─────────────────────────────                                                  │
│                                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │    Pack      │───▶│   Create     │───▶│    Ship      │───▶│   Deliver    │ │
│  │   Order      │    │   Label      │    │   Package    │    │              │ │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘ │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## API Integration Map

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         API INTEGRATION ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│                          ┌─────────────────────┐                                │
│                          │   QUOTE PORTAL      │                                │
│                          │   (React - 5173)    │                                │
│                          └──────────┬──────────┘                                │
│                                     │                                           │
│                    ┌────────────────┼────────────────┐                          │
│                    │                │                │                          │
│                    ▼                ▼                ▼                          │
│  ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐       │
│  │  POST /api/quotes/  │ │  POST /api/quotes/  │ │  POST /api/shipping │       │
│  │     generate        │ │  {id}/accept        │ │      /rates         │       │
│  │                     │ │                     │ │                     │       │
│  │ • Upload 3MF        │ │ • Accept quote      │ │ • Get carrier rates │       │
│  │ • Select material   │ │ • Save shipping     │ │ • EasyPost API      │       │
│  │ • Select options    │ │ • Trigger payment   │ │                     │       │
│  └──────────┬──────────┘ └──────────┬──────────┘ └─────────────────────┘       │
│             │                       │                                           │
│             ▼                       ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐      │
│  │                       ERP BACKEND (FastAPI - 8000)                   │      │
│  ├──────────────────────────────────────────────────────────────────────┤      │
│  │                                                                      │      │
│  │  /api/v1/quotes/                    /api/v1/sales-orders/            │      │
│  │  ├── POST /generate                 ├── GET /                        │      │
│  │  ├── GET /{id}                      ├── POST /                       │      │
│  │  ├── POST /{id}/accept              └── GET /{id}                    │      │
│  │  └── POST /portal/{id}/submit-for-review                             │      │
│  │                                                                      │      │
│  │  /api/v1/shipping/                  /api/v1/stripe/                  │      │
│  │  └── POST /rates                    ├── POST /create-checkout        │      │
│  │                                     └── POST /webhook                │      │
│  │                                                                      │      │
│  │  /api/v1/materials/                 /api/v1/products/                │      │
│  │  ├── GET /                          ├── GET /                        │      │
│  │  └── GET /{id}/colors               └── GET /{id}                    │      │
│  │                                                                      │      │
│  └──────────────────────────────────────┬───────────────────────────────┘      │
│                                         │                                       │
│                                         ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐      │
│  │                    ML DASHBOARD (FastAPI - 8001)                     │      │
│  ├──────────────────────────────────────────────────────────────────────┤      │
│  │                                                                      │      │
│  │  /api/quotes/                                                        │      │
│  │  └── POST /generate                                                  │      │
│  │      • Receives 3MF file                                             │      │
│  │      • Calls BambuStudio CLI                                         │      │
│  │      • Analyzes G-code                                               │      │
│  │      • Calculates pricing                                            │      │
│  │      • Returns quote data                                            │      │
│  │                                                                      │      │
│  │  /api/printers/                     /api/jobs/                       │      │
│  │  ├── GET /status                    ├── GET /                        │      │
│  │  └── GET /{id}                      └── POST /                       │      │
│  │                                                                      │      │
│  └──────────────────────────────────────┬───────────────────────────────┘      │
│                                         │                                       │
│                    ┌────────────────────┴────────────────────┐                  │
│                    ▼                                         ▼                  │
│  ┌─────────────────────────────┐           ┌─────────────────────────────┐     │
│  │      BAMBUSTUDIO CLI        │           │       PRINTER FLEET         │     │
│  │                             │           │         (MQTT)              │     │
│  │  • Slice 3MF files          │           │                             │     │
│  │  • Generate G-code          │           │  Donatello (A1)             │     │
│  │  • Apply profiles           │           │  Leonardo (P1S)             │     │
│  │  • Calculate time/material  │           │  Michelangelo (A1)          │     │
│  └─────────────────────────────┘           │  Raphael (A1)               │     │
│                                            └─────────────────────────────┘     │
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐      │
│  │                      EXTERNAL SERVICES                               │      │
│  ├─────────────────┬─────────────────┬─────────────────┬────────────────┤      │
│  │     STRIPE      │    EASYPOST     │   SQUARESPACE   │     EMAIL      │      │
│  │                 │                 │    (Future)     │   (Future)     │      │
│  │ • Checkout      │ • Rate quotes   │                 │                │      │
│  │ • Webhooks      │ • Label create  │ • Order webhook │ • Confirmations│      │
│  │ • Refunds       │ • Tracking      │ • Inventory     │ • Payment links│      │
│  └─────────────────┴─────────────────┴─────────────────┴────────────────┘      │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          DATABASE SCHEMA (SQL Server)                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  CORE ENTITIES                                                                  │
│  ─────────────                                                                  │
│                                                                                 │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐         │
│  │    CUSTOMERS    │      │     QUOTES      │      │  SALES_ORDERS   │         │
│  ├─────────────────┤      ├─────────────────┤      ├─────────────────┤         │
│  │ id              │      │ id              │      │ id              │         │
│  │ customer_number │◀─────│ customer_id     │      │ customer_id     │─────▶   │
│  │ name            │      │ quote_number    │      │ order_number    │         │
│  │ email           │      │ status          │      │ status          │         │
│  │ phone           │      │ total_price     │      │ total_amount    │         │
│  │ company         │      │ material        │      │ quote_id        │─────▶   │
│  │ created_at      │      │ color           │      │ created_at      │         │
│  └─────────────────┘      │ quality         │      └─────────────────┘         │
│                           │ infill_percent  │                                   │
│                           │ customer_email* │   * New fields for               │
│                           │ customer_name*  │     review workflow              │
│                           │ internal_notes* │                                   │
│                           │ shipping_*      │                                   │
│                           │ expires_at      │                                   │
│                           └─────────────────┘                                   │
│                                                                                 │
│  PRODUCT & INVENTORY                                                            │
│  ───────────────────                                                            │
│                                                                                 │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐         │
│  │    PRODUCTS     │      │      BOMS       │      │   BOM_ITEMS     │         │
│  ├─────────────────┤      ├─────────────────┤      ├─────────────────┤         │
│  │ id              │◀─────│ product_id      │      │ bom_id          │─────▶   │
│  │ sku             │      │ id              │◀─────│ material_id     │─────▶   │
│  │ name            │      │ version         │      │ quantity        │         │
│  │ price           │      │ active          │      │ unit            │         │
│  │ category        │      │ created_at      │      └─────────────────┘         │
│  │ description     │      └─────────────────┘                                   │
│  │ active          │                                                            │
│  └─────────────────┘      ┌─────────────────┐      ┌─────────────────┐         │
│                           │MATERIAL_CATALOG │      │   INVENTORY     │         │
│                           ├─────────────────┤      ├─────────────────┤         │
│                           │ id              │◀─────│ material_id     │         │
│                           │ sku             │      │ quantity_on_hand│         │
│                           │ material_type   │      │ location        │         │
│                           │ brand           │      │ reorder_point   │         │
│                           │ color_name      │      │ last_updated    │         │
│                           │ color_hex       │      └─────────────────┘         │
│                           │ price_per_kg    │                                   │
│                           │ density         │                                   │
│                           │ in_stock        │                                   │
│                           └─────────────────┘                                   │
│                                                                                 │
│  PRODUCTION                                                                     │
│  ──────────                                                                     │
│                                                                                 │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐         │
│  │PRODUCTION_ORDERS│      │    PRINTERS     │      │   PRINT_JOBS    │         │
│  ├─────────────────┤      ├─────────────────┤      ├─────────────────┤         │
│  │ id              │      │ id              │◀─────│ printer_id      │         │
│  │ sales_order_id  │──▶   │ name            │      │ prod_order_id   │─────▶   │
│  │ product_id      │──▶   │ model           │      │ gcode_file      │         │
│  │ quantity        │      │ status          │      │ status          │         │
│  │ status          │      │ ip_address      │      │ started_at      │         │
│  │ priority        │      │ capabilities    │      │ completed_at    │         │
│  │ due_date        │      └─────────────────┘      └─────────────────┘         │
│  └─────────────────┘                                                            │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Quote Status Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           QUOTE STATUS LIFECYCLE                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│                              ┌─────────────┐                                    │
│                              │   DRAFT     │                                    │
│                              │  (created)  │                                    │
│                              └──────┬──────┘                                    │
│                                     │                                           │
│                                     ▼                                           │
│                    ┌────────────────────────────────┐                           │
│                    │      Quote Generated           │                           │
│                    │   (slicing complete, priced)   │                           │
│                    └────────────────┬───────────────┘                           │
│                                     │                                           │
│                     ┌───────────────┴───────────────┐                           │
│                     ▼                               ▼                           │
│          ┌─────────────────┐             ┌─────────────────┐                    │
│          │    APPROVED     │             │     PENDING     │                    │
│          │  (auto-approve) │             │ (needs review)  │                    │
│          │                 │             │                 │                    │
│          │ • No notes      │             │ • Has notes     │                    │
│          │ • Price < $X    │             │ • Price > $X    │                    │
│          │ • Standard opts │             │ • Special req   │                    │
│          └────────┬────────┘             └────────┬────────┘                    │
│                   │                               │                             │
│                   │                               ▼                             │
│                   │                    ┌─────────────────┐                      │
│                   │                    │ PENDING_REVIEW  │                      │
│                   │                    │  (submitted)    │                      │
│                   │                    │                 │                      │
│                   │                    │ • Email saved   │                      │
│                   │                    │ • Shipping saved│                      │
│                   │                    └────────┬────────┘                      │
│                   │                             │                               │
│                   │                    Engineer reviews                         │
│                   │                             │                               │
│                   │              ┌──────────────┴──────────────┐                │
│                   │              ▼                             ▼                │
│                   │   ┌─────────────────┐          ┌─────────────────┐          │
│                   │   │    APPROVED     │          │    REJECTED     │          │
│                   │   │ (after review)  │          │  (can't fulfill)│          │
│                   │   └────────┬────────┘          └─────────────────┘          │
│                   │            │                                                │
│                   │   Send payment link                                         │
│                   │            │                                                │
│                   └────────────┼────────────────────────────────┐               │
│                                ▼                                │               │
│                     ┌─────────────────┐                         │               │
│                     │    ACCEPTED     │                         │               │
│                     │ (customer pays) │                         │               │
│                     └────────┬────────┘                         │               │
│                              │                                  │               │
│            ┌─────────────────┼─────────────────┐                │               │
│            ▼                 ▼                 ▼                ▼               │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌────────────┐    │
│  │   CONVERTED     │ │    EXPIRED      │ │   CANCELLED     │ │  EXPIRED   │    │
│  │ (order created) │ │  (7 days)       │ │  (by customer)  │ │  (7 days)  │    │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ └────────────┘    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Material Pricing Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         MATERIAL PRICING CALCULATION                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  INPUT                                                                          │
│  ─────                                                                          │
│  ┌─────────────────┐                                                            │
│  │ 3MF File Upload │                                                            │
│  │ + Material      │                                                            │
│  │ + Infill %      │                                                            │
│  │ + Quality       │                                                            │
│  └────────┬────────┘                                                            │
│           │                                                                     │
│           ▼                                                                     │
│  SLICING (BambuStudio CLI)                                                      │
│  ─────────────────────────                                                      │
│  ┌─────────────────────────────────────────────────────────────┐               │
│  │                                                             │               │
│  │  bambu-studio.exe --slice input.3mf                         │               │
│  │    --printer "Bambu Lab A1 0.4 nozzle"                      │               │
│  │    --process "0.20mm Standard @BBL A1"                      │               │
│  │    --filament "Bambu PLA Basic @BBL A1"                     │               │
│  │    --sparse-infill-density 40        ◀── Infill %           │               │
│  │                                                             │               │
│  │  OUTPUT: plate_1.gcode                                      │               │
│  │                                                             │               │
│  └─────────────────────────────────────────────────────────────┘               │
│           │                                                                     │
│           ▼                                                                     │
│  G-CODE ANALYSIS                                                                │
│  ───────────────                                                                │
│  ┌─────────────────────────────────────────────────────────────┐               │
│  │                                                             │               │
│  │  Parse G-code for:                                          │               │
│  │  • Filament used (mm)  ──────▶  Volume (mm³)                │               │
│  │  • Print time (minutes)                                     │               │
│  │  • Layer count                                              │               │
│  │                                                             │               │
│  └─────────────────────────────────────────────────────────────┘               │
│           │                                                                     │
│           ▼                                                                     │
│  PRICING CALCULATION                                                            │
│  ───────────────────                                                            │
│  ┌─────────────────────────────────────────────────────────────┐               │
│  │                                                             │               │
│  │  ┌─────────────────────────────────────────────────────┐   │               │
│  │  │ Material Weight = Volume × Density                  │   │               │
│  │  │                                                     │   │               │
│  │  │ Densities:                                          │   │               │
│  │  │   PLA:  1.24 g/cm³                                  │   │               │
│  │  │   PETG: 1.27 g/cm³                                  │   │               │
│  │  │   ABS:  1.04 g/cm³                                  │   │               │
│  │  │   ASA:  1.07 g/cm³                                  │   │               │
│  │  │   TPU:  1.21 g/cm³                                  │   │               │
│  │  └─────────────────────────────────────────────────────┘   │               │
│  │                                                             │               │
│  │  ┌─────────────────────────────────────────────────────┐   │               │
│  │  │ Material Cost = Weight × (Base Cost × Multiplier)   │   │               │
│  │  │                                                     │   │               │
│  │  │ Multipliers:                                        │   │               │
│  │  │   PLA:  1.0× ($16.99/kg baseline)                   │   │               │
│  │  │   PETG: 1.2× ($20.39/kg)                            │   │               │
│  │  │   ABS:  1.1× ($18.69/kg)                            │   │               │
│  │  │   ASA:  1.3× ($22.09/kg)                            │   │               │
│  │  │   TPU:  1.8× ($30.58/kg)                            │   │               │
│  │  └─────────────────────────────────────────────────────┘   │               │
│  │                                                             │               │
│  │  ┌─────────────────────────────────────────────────────┐   │               │
│  │  │ Machine Cost = Print Time × Machine Rate            │   │               │
│  │  │              = minutes × ($20/hr ÷ 60)              │   │               │
│  │  └─────────────────────────────────────────────────────┘   │               │
│  │                                                             │               │
│  │  ┌─────────────────────────────────────────────────────┐   │               │
│  │  │ Total = Material Cost + Machine Cost + Overhead     │   │               │
│  │  │       + Profit Margin                               │   │               │
│  │  └─────────────────────────────────────────────────────┘   │               │
│  │                                                             │               │
│  └─────────────────────────────────────────────────────────────┘               │
│           │                                                                     │
│           ▼                                                                     │
│  OUTPUT                                                                         │
│  ──────                                                                         │
│  ┌─────────────────────────────────────────────────────────────┐               │
│  │                                                             │               │
│  │  {                                                          │               │
│  │    "quote_number": "Q-2025-123",                            │               │
│  │    "material": "PLA",                                       │               │
│  │    "material_grams": 26.2,                                  │               │
│  │    "print_time_minutes": 82,                                │               │
│  │    "unit_price": 9.68,                                      │               │
│  │    "total_price": 9.68,                                     │               │
│  │    "status": "approved"                                     │               │
│  │  }                                                          │               │
│  │                                                             │               │
│  └─────────────────────────────────────────────────────────────┘               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Current vs Target State

| Component | Current (Nov 2025) | Target (Q1 2026) |
|-----------|-------------------|------------------|
| **Quote System** | | |
| File upload (3MF) | ✅ | ✅ |
| Material selection | ✅ | ✅ |
| Color selection | ✅ | ✅ |
| Infill/strength | ✅ | ✅ |
| Real-time pricing | ✅ | ✅ |
| 3D model viewer | ✅ | ✅ |
| STL support | ⚠️ Broken | ✅ Fixed |
| **Payment** | | |
| Stripe checkout | ✅ | ✅ |
| Shipping rates | ✅ | ✅ |
| Review workflow | ✅ | ✅ |
| Payment webhooks | ❌ | ✅ |
| Email notifications | ❌ | ✅ |
| **Orders** | | |
| Auto-create from quote | ❌ | ✅ |
| Auto-create product | ❌ | ✅ |
| Auto-create BOM | ❌ | ✅ |
| Squarespace webhook | ❌ | ✅ |
| **Production** | | |
| Production queue | ❌ | ✅ |
| Printer assignment | ❌ | ✅ |
| Job scheduling | ❌ | ✅ |
| MRP material planning | ❌ | ✅ |
| **Fulfillment** | | |
| Packing workflow | ❌ | ✅ |
| Label generation | ❌ | ✅ |
| Tracking updates | ❌ | ✅ |
| **Inventory** | | |
| Stock tracking | ❌ | ✅ |
| Low stock alerts | ❌ | ✅ |
| Auto reorder | ❌ | ✅ |

---

## Summary

| Component | Technology | Port | Status |
|-----------|------------|------|--------|
| Quote Portal | React + Vite | 5173 | ✅ Live |
| ERP Backend | FastAPI + SQLAlchemy | 8000 | ✅ Live |
| ML Dashboard | FastAPI + React | 8001 | ✅ Live |
| Database | SQL Server Express | 1433 | ✅ Live |
| Payments | Stripe | - | ✅ Integrated |
| Shipping | EasyPost | - | ✅ Integrated |
| Slicing | BambuStudio CLI | - | ✅ Working |
| Printers | MQTT Protocol | - | ✅ Connected |

**Next Priorities:**
1. Email notifications (support@blb3d.com)
2. Stripe webhook for order creation
3. Auto-create products from portal quotes
4. Production queue and printer assignment
