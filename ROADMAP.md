# BLB3D ERP Development Roadmap

## Project Overview
Building a comprehensive ERP system to replace MRPeasy, with deep integration between WooCommerce orders and the Bambu Print Suite for automated 3D print farm operations.

## Architecture Overview

### High-Level System Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌──────────────────┐
│  WooCommerce    │────────▶│   BLB3D ERP     │◀────────│  Bambu Print     │
│  (Orders)       │         │   (Port 8000)   │         │  Suite ML-Dash   │
│                 │         │                 │         │  (Port 8001)     │
└─────────────────┘         └────────┬────────┘         └──────────────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  SQL Server     │
                            │  Express        │
                            │  (BLB3D_ERP DB) │
                            └─────────────────┘
```

### Detailed Quote System Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         CUSTOMER PORTAL (Phase 2B)                        │
│  Browser ──▶ test_ui.html ──▶ POST /api/v1/quotes (ERP Port 8000)       │
│                              │ File: .3mf or .stl                         │
│                              │ Material: PLA/PETG/ABS/ASA/TPU             │
└──────────────────────────────┼──────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    ERP BACKEND (Port 8000)                                │
│                                                                            │
│  1. Quote Endpoint: backend/app/api/v1/endpoints/quotes.py               │
│     ├─ Receives file upload + parameters                                 │
│     ├─ Saves to database (quotes table)                                  │
│     └─ Calls Bambu Suite API ──┐                                        │
│                                  │                                        │
│  2. Bambu Client: backend/app/services/bambu_client.py                   │
│     ├─ generate_quote() method                                           │
│     ├─ POST to ML Dashboard: http://localhost:8001/api/quotes/generate  │
│     │   • Uploads file                                                   │
│     │   • Sends material type, quantity, etc.                            │
│     └─ Fallback pricing if ML Dashboard unavailable                      │
│         (Uses file size estimation)                                       │
└────────────────────────────────────┼─────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────┐
│               BAMBU PRINT SUITE ML DASHBOARD (Port 8001)                  │
│           Location: bambu-print-suite/ml-dashboard/backend/               │
│                                                                            │
│  1. API Endpoint: main.py (Lines 350-694)                                │
│     POST /api/quotes/generate                                             │
│     ├─ Receives file (.3mf or .stl)                                      │
│     ├─ Receives material type (PLA/PETG/etc)                             │
│     └─ Determines if slicing needed ──┐                                  │
│                                         │                                  │
│  2. Production Profiles: production_profiles.py                           │
│     ├─ Selects printer (Leonardo P1S, Donatello A1, etc.)               │
│     ├─ Maps material → profiles                                          │
│     └─ Returns BambuStudio profile paths ──┐                            │
│                                              │                             │
│  3. BambuStudio CLI: bambu_slicer.py        │                            │
│     ├─ slice_stl() - Slices STL files       │                            │
│     │   ⚠️ ISSUE: Currently hangs indefinitely                           │
│     ├─ slice_multi_plate_project() - 3MF files ✅                        │
│     │   • Calls: "C:\Program Files\Bambu Studio\bambu-studio.exe"       │
│     │   • Args: --export-gcode, --load <profiles>, <file>               │
│     │   • Output: plate_1.gcode (temp directory)                         │
│     └─ Returns: gcode_path ──┐                                           │
│                                │                                           │
│  4. G-code Analyzer: gcode_analyzer.py (Lines 99-240)                    │
│     ├─ Parses G-code file                                                │
│     ├─ Extracts metadata:                                                │
│     │   • filament_used_mm3 → material volume                            │
│     │   • estimated_print_time → print time                              │
│     │   • bounding_box_min/max → dimensions ⚠️ NOT WORKING              │
│     ├─ Counts tool changes (multi-material)                              │
│     └─ Returns: analysis dict ──┐                                        │
│                                   │                                        │
│  5. Quote Calculator: quote_calculator.py (Lines 63-236)                 │
│     ├─ calculate_quote(gcode_path, material='PLA')                       │
│     ├─ Material Cost Multipliers:                                        │
│     │   • PLA: 1.0× ($16.99/kg baseline)                                │
│     │   • PETG: 1.2× ($20.39/kg) ⚠️ NOT DIFFERENTIATING                 │
│     │   • ABS: 1.1× ($18.69/kg)                                          │
│     │   • ASA: 1.3× ($22.09/kg)                                          │
│     │   • TPU: 1.8× ($30.58/kg)                                          │
│     ├─ Calculates: material + labor + overhead + profit                  │
│     └─ Returns: quote response ──┐                                       │
│                                    │                                       │
│  6. Response: main.py (Lines 647-690)                                    │
│     └─ Returns JSON:                                                      │
│         {                                                                  │
│           "success": true,                                                │
│           "material_grams": 77.89,                                        │
│           "print_time_hours": 1.12,                                       │
│           "unit_price": 12.48,                                            │
│           "total_price": 12.48,                                           │
│           "dimensions": {                                                 │
│             "x": 100.0,  ⚠️ ALWAYS FALLBACK VALUES                       │
│             "y": 100.0,                                                   │
│             "z": 50.0                                                     │
│           }                                                               │
│         }                                                                  │
└────────────────────────────────────┼─────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    ERP BACKEND (Receives Response)                        │
│                                                                            │
│  1. Bambu Client: bambu_client.py                                        │
│     ├─ Parses response from ML Dashboard                                 │
│     ├─ Extracts: dimensions, material_grams, etc.                        │
│     └─ Returns to Quote Endpoint ──┐                                     │
│                                      │                                     │
│  2. Quote Endpoint: quotes.py       │                                     │
│     ├─ Updates quote in database    │                                     │
│     ├─ Stores all quote details     │                                     │
│     └─ Returns to customer portal   │                                     │
└─────────────────────────────────────┼────────────────────────────────────┘
                                       │
                                       ▼
                            ┌─────────────────┐
                            │  Customer sees  │
                            │  Quote details  │
                            └─────────────────┘
```

### Key Integration Points

1. **ERP ↔ ML Dashboard Communication**
   - Protocol: HTTP REST API
   - Format: multipart/form-data (file upload) + JSON response
   - Authentication: None currently (localhost only)
   - Error Handling: ERP falls back to estimation if ML Dashboard unavailable

2. **ML Dashboard ↔ BambuStudio CLI**
   - Interface: subprocess.run() with command-line args
   - Profiles: JSON files in `C:\Users\brand\AppData\Roaming\BambuStudio\system\BBL\`
   - Output: G-code files in temp directory
   - ⚠️ Issue: STL files cause CLI to hang

3. **Data Flow**

   ```text
   Customer → test_ui.html → ERP API → Bambu Client → ML Dashboard API
                                                            ↓
   Customer ← ERP API ← Bambu Client ← Quote Response ← Quote Calculator
                                                            ↑
                                             G-code Analyzer ← BambuStudio CLI
   ```

### Critical Components

| Component | File | Purpose | Status |
|-----------|------|---------|--------|
| Quote API | `backend/app/api/v1/endpoints/quotes.py` | Customer quote creation | ✅ Working |
| Bambu Client | `backend/app/services/bambu_client.py` | ML Dashboard integration | ✅ Working |
| ML API | `ml-dashboard/backend/main.py` | Quote generation orchestrator | ✅ Working |
| BambuStudio Wrapper | `quote-engine/slicer/bambu_slicer.py` | CLI integration | ⚠️ STL failing |
| G-code Analyzer | `quote-engine/slicer/gcode_analyzer.py` | Extract print metrics | ⚠️ Missing dimensions |
| Quote Calculator | `quote-engine/slicer/quote_calculator.py` | Pricing logic | ⚠️ Material costs |
| Production Profiles | `quote-engine/slicer/production_profiles.py` | Printer/material routing | ✅ Working |

## Current Status: Phase 2D - Quote System Integration ⚠️ (85% Complete - BLOCKING ISSUES)

**⚠️ CRITICAL ISSUES - See [ISSUES.md](ISSUES.md) for detailed troubleshooting guide**

### 🚨 Blocking Issues

1. **Dimensions always show fallback values** (100×100×50mm) - Bounding box extraction not working
2. **Material costs not differentiating** - All materials showing same price despite multipliers
3. **STL files fail to slice** - BambuStudio CLI hangs indefinitely

### ✅ Working Features

- ✅ 3MF file upload and quoting
- ✅ Quote database storage
- ✅ Customer portal UI with auto-login
- ✅ Quote acceptance → Product + BOM creation
- ✅ Sales order creation from quotes
- ✅ TPU material support added

---

## Previous: Phase 2C - Sales Order System ✅ (100% Complete)

### ✅ Completed

1. **Database Schema**
   - Created all core tables in SQL Server Express
   - Tables: products, production_orders, print_jobs, inventory, sales_orders, BOMs, printers
   - Location: [scripts/setup_database.sql](scripts/setup_database.sql)

2. **SQLAlchemy ORM Models**
   - Product model - [backend/app/models/product.py](backend/app/models/product.py)
   - ProductionOrder model - [backend/app/models/production_order.py](backend/app/models/production_order.py)
   - PrintJob model - [backend/app/models/print_job.py](backend/app/models/print_job.py)
   - Inventory models - [backend/app/models/inventory.py](backend/app/models/inventory.py)
   - SalesOrder models - [backend/app/models/sales_order.py](backend/app/models/sales_order.py)
   - All models aligned with actual database schema

3. **Database Connection**
   - Session management - [backend/app/db/session.py](backend/app/db/session.py)
   - pyodbc + SQLAlchemy connection to SQL Server Express
   - Windows Authentication configured
   - Connection pooling enabled

4. **API Endpoints - Database Integration**

   **Products Endpoint** ✅
   - `GET /api/v1/products` - List products with filtering (633 products loaded)
   - `GET /api/v1/products/{id}` - Get product by ID
   - `GET /api/v1/products/sku/{sku}` - Get product by SKU
   - Location: [backend/app/api/v1/endpoints/products.py](backend/app/api/v1/endpoints/products.py)

   **Production Orders Endpoint** ✅
   - `POST /api/v1/production-orders` - Create production order (saves to DB)
   - `POST /api/v1/production-orders/{id}/start-print` - Start print job
   - `POST /api/v1/production-orders/{id}/complete` - Complete order
   - `GET /api/v1/production-orders/{id}` - Get order details
   - `GET /api/v1/production-orders` - List orders with filtering
   - Location: [backend/app/api/v1/endpoints/production_orders.py](backend/app/api/v1/endpoints/production_orders.py)

   **Print Jobs Endpoint** ✅
   - `PATCH /api/v1/print-jobs/{id}` - Update job status
   - `POST /api/v1/print-jobs/{id}/complete` - Complete job with metrics
   - `GET /api/v1/print-jobs/{id}` - Get job details
   - `GET /api/v1/print-jobs` - List jobs with filtering
   - Location: [backend/app/api/v1/endpoints/print_jobs.py](backend/app/api/v1/endpoints/print_jobs.py)

   **Inventory Endpoint** ✅
   - `POST /api/v1/inventory/check` - Check material availability
   - `POST /api/v1/inventory/transactions` - Create inventory transaction
   - `GET /api/v1/inventory/materials` - List raw materials
   - Location: [backend/app/api/v1/endpoints/inventory.py](backend/app/api/v1/endpoints/inventory.py)

5. **Data Migration**
   - 633 products imported from MRPeasy
   - Product SKUs compacted and deduplicated
   - All products loaded into SQL Server
   - Location: [data_migration/import_products_with_compact_skus.py](data_migration/import_products_with_compact_skus.py)

### ✅ All Issues Resolved

#### PrintJob Model Issue - FIXED

- Added missing `printer` relationship to PrintJob model
- SQLAlchemy mapper now correctly configured
- All relationships working properly
- Production orders retrieve successfully with print_jobs

### ✅ Phase 1 Complete

1. **✅ Database Layer**
   - All tables created in SQL Server
   - SQLAlchemy models working correctly
   - All relationships configured properly

2. **✅ API Endpoints Tested**
   - Products API: 633 products loaded and retrieving
   - Production Orders API: Create, list, retrieve working
   - Print Jobs API: Ready for Phase 3 integration
   - Inventory API: Material checks and transactions working

3. **✅ Code on GitHub**
   - Repository: [blb3d-print-farm](https://github.com/Blb3D/blb3d-print-farm) (Private)
   - Initial commit + PrintJob fix pushed
   - All sensitive data excluded via .gitignore

### ✅ Phase 2A - Authentication System (Complete)

1. **User Registration & Login** ✅
   - User model with bcrypt password hashing
   - Registration endpoint with email validation
   - Login endpoint with JWT token generation
   - Access tokens (30-min expiry) + Refresh tokens (7-day expiry)
   - Location: [backend/app/api/v1/endpoints/auth.py](backend/app/api/v1/endpoints/auth.py)

2. **Token Management** ✅
   - Refresh token database storage and rotation
   - Token refresh endpoint
   - Automatic token cleanup
   - JWT authentication dependency for protected routes

3. **User Profile Management** ✅
   - Get current user profile
   - Update user details (name, phone, addresses)
   - Protected endpoints using authentication

**Endpoints Added:**
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - Login and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get user profile
- `PATCH /api/v1/auth/me` - Update user profile

**Database Tables Added:**
- `users` - User accounts
- `refresh_tokens` - Token storage

### ✅ Phase 2B - Quote Management System (Complete)

1. **Quote Creation with File Uploads** ✅
   - Multi-file upload endpoint (3MF files)
   - Quote request with material, finish, quantity specs
   - File validation and storage
   - Location: [backend/app/api/v1/endpoints/quotes.py](backend/app/api/v1/endpoints/quotes.py)

2. **Automatic Pricing & Approval** ✅
   - Auto-approval for orders under $500
   - Admin review required for orders over $500
   - Configurable pricing logic
   - Rush order surcharges (20%, 40%, 60%)

3. **Quote Lifecycle Management** ✅
   - Quote status tracking (draft → pending → accepted/rejected)
   - 30-day expiration with is_expired property
   - Admin review workflow
   - Quote cancellation

4. **File Management** ✅
   - Multiple file uploads per quote
   - File type validation (3MF)
   - File storage with user/quote organization

**Endpoints Added:**
- `POST /api/v1/quotes` - Create quote with files
- `GET /api/v1/quotes` - List user's quotes
- `GET /api/v1/quotes/{id}` - Get quote details
- `PATCH /api/v1/quotes/{id}/accept` - Accept quote
- `PATCH /api/v1/quotes/{id}/reject` - Reject quote
- `POST /api/v1/quotes/{id}/cancel` - Cancel quote

**Database Tables Added:**
- `quotes` - Quote requests
- `quote_files` - Uploaded files

### ✅ Phase 2C - Sales Order System (Complete)

1. **Quote-to-Order Conversion** ✅
   - Convert accepted quotes to sales orders
   - Validation (quote must be accepted, not expired, not already converted)
   - Sequential order number generation (SO-YYYY-NNN)
   - Location: [backend/app/api/v1/endpoints/sales_orders.py](backend/app/api/v1/endpoints/sales_orders.py)

2. **Order Lifecycle Management** ✅
   - Status tracking: pending → confirmed → in_production → quality_check → shipped → delivered → completed
   - Automatic timestamp updates for status transitions
   - Business logic properties (is_cancellable, can_start_production)
   - Order cancellation with reason tracking

3. **Payment Tracking (Mock - Ready for Integration)** ✅
   - Payment status tracking (pending, partial, paid, refunded)
   - Payment method and transaction ID storage
   - Structured for Stripe integration
   - Payment timestamp tracking

4. **Shipping Tracking (Mock - Ready for Integration)** ✅
   - Shipping address storage
   - Tracking number and carrier info
   - Structured for carrier API integration
   - Shipping and delivery timestamp tracking

**Endpoints Added:**
- `POST /api/v1/sales-orders/convert/{quote_id}` - Convert quote to order
- `GET /api/v1/sales-orders` - List user's orders
- `GET /api/v1/sales-orders/{id}` - Get order details
- `PATCH /api/v1/sales-orders/{id}/status` - Update order status
- `PATCH /api/v1/sales-orders/{id}/payment` - Update payment info
- `PATCH /api/v1/sales-orders/{id}/shipping` - Update shipping info
- `POST /api/v1/sales-orders/{id}/cancel` - Cancel order

**Database Schema:**
- `sales_orders` table completely redesigned with quote-centric schema
- One-to-one relationship with quotes (no line items)
- Migration script: [backend/migrate_sales_orders.py](backend/migrate_sales_orders.py)

---

## Phase 2: Customer Portal (Backend API Complete ✅ - Frontend Next)

### Goal
Build custom web portal for real-time STL quoting and ordering, becoming the primary sales channel for BLB3D.

**Strategic Decision:** Build portal first with competitive advantage features (real-time quoting, instant pricing), then integrate Squarespace later. This allows BLB3D to control the customer experience and offer capabilities that Squarespace/WooCommerce cannot.

### Why Portal First?
- **Competitive Advantage**: Real-time STL quoting is a differentiator
- **Better Control**: Own the customer experience end-to-end
- **No Disruption**: Squarespace continues handling marketing/catalog
- **Flexibility**: Custom features not possible with Squarespace
- **Scalability**: Built for BLB3D's specific workflow

### Core Features

1. **Real-Time STL Quoting Engine** 🎯 MVP Feature
   - Upload STL files (drag-and-drop)
   - Parse 3D model (volume, surface area, dimensions)
   - Estimate print time using algorithms/ML
   - Calculate material usage (grams)
   - Instant price quote with breakdown
   - Configure: material, color, quantity, finish, infill
   - Quantity discounts (10+, 50+, 100+)

2. **Authentication & User Management**
   - Customer registration/login (PyJWT tokens)
   - Email verification
   - Password reset
   - User profiles with billing/shipping addresses
   - Account dashboard

3. **Order Management**
   - Convert quotes to orders
   - Shopping cart for multiple items
   - Order history and tracking
   - Real-time production status updates
   - Reorder from previous orders

4. **Payment Processing**
   - Stripe integration
   - Credit card payments
   - Order confirmation emails
   - Invoice generation

5. **3D Model Management**
   - Uploaded STL file storage
   - 3D preview viewer (Three.js)
   - File validation (watertight check)
   - Thumbnail generation

### Technology Stack

**Backend (FastAPI):**
- PyJWT 2.10.1 (authentication)
- trimesh 4.5.3 (STL parsing)
- numpy 2.2.1 (mesh calculations)
- stripe 7.8.0 (payments)
- pillow 11.0.0 (thumbnails)

**Frontend (React):**
- React 18 + TypeScript + Vite
- TailwindCSS (styling)
- React Three Fiber (3D viewer)
- Axios (API client)
- React Router v6 (routing)
- Stripe Elements (payment UI)

**Database:**
- New tables: users, quotes, stl_files, refresh_tokens
- Extends existing sales_orders and production_orders

### Implementation Phases

**Phase 2A: Authentication ✅ COMPLETE**
- ✅ User registration and login endpoints
- ✅ JWT token generation and validation
- ✅ Password hashing and verification
- ✅ User profile management
- ✅ Refresh token rotation

**Phase 2B: Quote Management ✅ COMPLETE**
- ✅ File upload endpoint with validation (3MF files)
- ✅ Quote creation with material/finish/quantity specs
- ✅ Automatic pricing and approval logic
- ✅ Quote lifecycle management (accept/reject/cancel)
- ✅ 30-day quote expiration
- ✅ Multi-file uploads per quote

**Phase 2C: Sales Order System ✅ COMPLETE**
- ✅ Quote-to-order conversion
- ✅ Sequential order numbering (SO-YYYY-NNN)
- ✅ Order lifecycle status management
- ✅ Payment tracking (ready for Stripe)
- ✅ Shipping tracking (ready for carrier API)
- ✅ Order cancellation workflow

**Phase 2D: Payment Integration (NEXT)**
- Stripe account setup
- Payment intent endpoint
- Webhook handler for payment confirmation
- Real payment processing (currently mock)
- Email notifications
- Receipt generation

**Phase 2E: Shipping Integration**
- EasyPost or ShipStation integration
- Rate calculation
- Label generation
- Tracking webhook handling
- Carrier selection logic

**Phase 2F: Frontend Development**
- React app setup with Vite
- Authentication UI (login/register)
- Quote request form with file upload
- 3D model viewer (React Three Fiber)
- Quote configurator UI
- Stripe Elements integration
- User dashboard and order tracking
- Responsive design

**Phase 2G: Integration & Testing**
- End-to-end testing
- Security testing
- Performance optimization
- Production deployment

### Database Schema

```sql
-- Users table
CREATE TABLE users (
    id INT PRIMARY KEY IDENTITY(1,1),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    -- addresses, status, etc.
    created_at DATETIME DEFAULT GETDATE()
);

-- Quotes table
CREATE TABLE quotes (
    id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT FOREIGN KEY REFERENCES users(id),
    stl_file_id INT FOREIGN KEY REFERENCES stl_files(id),
    material_type VARCHAR(50),
    quantity INT,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),
    status VARCHAR(20),
    created_at DATETIME DEFAULT GETDATE()
);

-- STL files table
CREATE TABLE stl_files (
    id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT FOREIGN KEY REFERENCES users(id),
    filename VARCHAR(255),
    file_path VARCHAR(500),
    volume_cm3 DECIMAL(10,3),
    surface_area_cm2 DECIMAL(10,2),
    -- other metrics
    created_at DATETIME DEFAULT GETDATE()
);
```

### API Endpoints

**Auth:**
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`

**STL & Quotes:**
- `POST /api/v1/stl/upload`
- `GET /api/v1/stl/{id}`
- `POST /api/v1/quotes`
- `GET /api/v1/quotes/{id}`
- `PATCH /api/v1/quotes/{id}`

**Orders:**
- `POST /api/v1/orders` (from quote)
- `GET /api/v1/orders`
- `GET /api/v1/orders/{id}`
- `GET /api/v1/orders/{id}/status`

**Payment:**
- `POST /api/v1/payment/intent`
- `POST /api/v1/webhooks/stripe`

### Success Metrics
- Quote generation in < 5 seconds
- Quote accuracy within 10% of actual cost
- 95%+ quote success rate
- Payment success rate > 98%
- Customer satisfaction > 4.5/5

### Questions to Answer Before Starting
1. Pricing: Markup multiplier? (2x, 2.5x, 3x?)
2. Materials: What's in stock? (PLA, PETG, ABS, etc.) Cost per gram?
3. Finish options: Sanded, painted pricing?
4. Quantity discounts: What tiers? (10+, 50+, 100+?)
5. Stripe: Existing account or create new?
6. File storage: Local, Azure Blob, or AWS S3?

**Full Design Document:** See [PORTAL_DESIGN.md](PORTAL_DESIGN.md) for complete technical specifications.

---

## Phase 3: Bambu Print Suite Integration

### Goal
Bidirectional communication between ERP and Bambu Print Suite for print job management.

### Tasks

1. **Print Job Creation in Bambu Suite**
   - Send print job to Bambu Suite ML-Dashboard API
   - Include: product SKU, quantity, material, priority
   - Receive: assigned printer, estimated time, job ID
   - Store external job ID for tracking

2. **Status Sync from Bambu Suite**
   - Receive webhooks/callbacks from Bambu Suite:
     - Job queued
     - Printing started
     - Print progress updates
     - Print completed
     - Print failed
   - Update production order status accordingly
   - Update print job metrics (actual time, material used)

3. **Material Consumption Tracking**
   - Record material usage when print completes
   - Create inventory consumption transactions
   - Calculate variance (estimated vs actual)
   - Feed data to ML cost prediction model

4. **Cost Calculation**
   - Material cost (grams used × cost per gram)
   - Machine time cost (minutes × cost per minute)
   - Labor overhead
   - Total production cost per item

### Bambu Suite API Integration Points

```python
# Create print job
POST /api/print-jobs
{
  "production_order_id": 123,
  "product_sku": "FG-00001",
  "quantity": 5,
  "material_type": "PLA",
  "priority": "normal"
}

# Receive status updates
POST /api/v1/print-jobs/{id}/status
{
  "status": "printing",
  "progress": 45.0,
  "remaining_time": 120
}

# Completion callback
POST /api/v1/print-jobs/{id}/complete
{
  "actual_time_minutes": 180,
  "actual_material_grams": 125.5,
  "variance_percent": 5.2
}
```

---

## Phase 4: Frontend Dashboard

### Goal
React-based UI for managing orders, production, and inventory.

### Components

1. **Dashboard Overview**
   - Active orders count
   - Production queue status
   - Printer utilization
   - Low stock alerts
   - Revenue/cost metrics

2. **Orders Management**
   - List sales orders
   - View order details
   - Manual order creation
   - Order status tracking

3. **Production Management**
   - Production queue
   - Assign jobs to printers
   - Monitor print progress
   - Complete/fail jobs

4. **Inventory Management**
   - Current stock levels
   - Material consumption history
   - Reorder alerts
   - Transaction history

5. **Products & BOMs**
   - Product catalog
   - BOM management
   - Cost calculations

---

## Phase 4: E-commerce Integration (Squarespace/WooCommerce)

### Goal
Integrate existing e-commerce platforms to create orders in the ERP system automatically.

**Note:** This phase is now deprioritized since the Customer Portal (Phase 2) will be the primary ordering channel. This integration allows customers who browse Squarespace to also place orders, but the Portal will offer superior features.

### Squarespace Integration

1. **Webhook Receiver**
   - Create endpoint: `POST /api/v1/integration/squarespace/webhook`
   - Parse order data from Squarespace
   - Extract product SKUs and quantities
   - Create sales orders in ERP

2. **Order Status Sync**
   - Update Squarespace when production starts
   - Sync tracking numbers when shipped
   - Handle order cancellations

### WooCommerce Integration (Optional)

If migrating from Squarespace to WooCommerce in the future:

1. **WooCommerce Webhook Receiver**
   - Create endpoint: `POST /api/v1/integration/woocommerce/webhook`
   - Verify webhook signature
   - Parse order data
   - Extract product SKUs and quantities

2. **Sales Order Creation**
   - Convert WooCommerce order to SalesOrder
   - Create SalesOrderLine items
   - Link to products by SKU
   - Store WooCommerce order ID for reference

3. **Production Order Auto-Generation**
   - Check if product has BOM (is_raw_material = false)
   - Create ProductionOrder for each line item
   - Set priority based on order date/shipping method

4. **Order Status Updates**
   - Update order status when production starts
   - Add production notes to order
   - Update when shipped
   - Sync tracking numbers

---

## Phase 5: Advanced Features

### Planned Features

1. **Purchase Order Management**
   - Create POs for raw materials
   - Vendor management
   - Receiving & QC

2. **Financial Integration (QuickBooks)**
   - QuickBooks Online sync
   - COGS tracking
   - Revenue recognition
   - P&L reporting
   - Invoice sync

3. **ML Cost Prediction**
   - Train models on historical print data
   - Predict print time and material usage
   - Optimize pricing
   - Improve quote accuracy

4. **Reporting & Analytics**
   - Production efficiency metrics
   - Inventory turnover
   - Customer analytics
   - Printer performance
   - Profitability analysis

5. **Multi-user & Permissions**
   - Internal user authentication (admin/operators)
   - Role-based access control
   - Audit logging
   - Activity tracking

6. **Database-Driven Pricing Updates** 🔄 Future Enhancement
   - Periodic review and update of material costs from database
   - Once inventory/purchase order data is populated with material costs
   - Automatic sync of average material costs to quote calculator
   - Schedule: Monthly or quarterly price adjustments based on actual purchase costs
   - Benefits: Maintain accurate margins as material costs fluctuate
   - Implementation:
     - Query average material costs from purchase_order_lines by material type
     - Update quote_calculator.py config values
     - Update bambu_client.py fallback pricing
     - Log price change history for audit trail
     - Optional: Admin UI to review/approve price changes before applying

---

## Development Guidelines

### Code Organization
```
backend/
├── app/
│   ├── api/v1/endpoints/     # API route handlers
│   ├── models/               # SQLAlchemy ORM models
│   ├── services/             # Business logic & integrations
│   ├── core/                 # Config, security, etc.
│   └── db/                   # Database connection & base
```

### Key Files to Know
- **Database Schema**: [scripts/setup_database.sql](scripts/setup_database.sql)
- **Main App**: [backend/app/main.py](backend/app/main.py)
- **Config**: [backend/app/core/config.py](backend/app/core/config.py)
- **DB Session**: [backend/app/db/session.py](backend/app/db/session.py)

### Running the Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### Database Connection
- **Server**: localhost\SQLEXPRESS
- **Database**: BLB3D_ERP
- **Auth**: Windows Authentication
- **Connection String**: In [backend/app/db/session.py](backend/app/db/session.py)

---

## Testing Strategy

### Unit Tests
- Model validation
- Business logic
- API endpoints

### Integration Tests
- Database operations
- WooCommerce webhook handling
- Bambu Suite API calls

### End-to-End Tests
- Complete order flow
- Production → printing → completion
- Inventory tracking

---

## Next Session: Start Here 🚀

### ✅ Current Status
- **Phase 1: Database Layer** - 100% Complete
- **Security Updates** - All critical vulnerabilities fixed
- **GitHub Actions** - Updated to latest versions
- **Phase 2 Planning** - Complete with full architecture design

### Immediate Next Steps: Begin Phase 2A (Authentication)

**Before Starting Implementation, Answer These Questions:**

1. **Pricing Strategy:**
   - Target markup multiplier? (Recommended: 2.5x)
   - Quantity discount tiers? (Suggested: 10+ = 10%, 50+ = 15%, 100+ = 25%)
   - Finish options and pricing? (Standard free, Sanded +$5, Painted +$15?)
   - Rush order surcharge? (24hr +50%, 48hr +25%?)

2. **Materials Available:**
   - What materials do you stock? (PLA, PETG, ABS, TPU, Resin?)
   - Color options per material?
   - Cost per gram for each material?
   - Which materials support which colors?

3. **Machine Capabilities:**
   - How many printers in the farm?
   - Build volumes for each printer type?
   - Average hourly operating cost per printer?
   - Typical utilization rate?

4. **Business Rules:**
   - Minimum order value? (e.g., $10 minimum)
   - Maximum STL file size? (Recommended: 100MB)
   - Auto-approve orders or manual review?
   - Refund/cancellation policy?

5. **Integrations:**
   - Create new Stripe account or use existing?
   - Email provider preference (Gmail SMTP, SendGrid, etc.)?
   - File storage (local filesystem, Azure Blob, AWS S3)?

### Once Questions Are Answered:

1. **Set Up Stripe Account**
   - Create Stripe account (or use existing)
   - Get test API keys (pk_test_... and sk_test_...)
   - Configure webhook endpoint (will set up in code)

2. **Install Phase 2 Dependencies**
   ```bash
   cd backend
   pip install PyJWT==2.10.1 trimesh==4.5.3 numpy==2.2.1 stripe==7.8.0 pillow==11.0.0
   ```

3. **Create Database Tables**
   ```bash
   # Run new schema updates for users, quotes, stl_files tables
   sqlcmd -S localhost\SQLEXPRESS -i scripts/phase2_schema.sql
   ```

4. **Begin Phase 2A Implementation**
   - Start with authentication system
   - Follow tasks in [PORTAL_DESIGN.md](PORTAL_DESIGN.md)
   - Implement user registration and login endpoints

### Reference Documents
- **Portal Architecture:** [PORTAL_DESIGN.md](PORTAL_DESIGN.md) - Complete technical specs
- **Project Roadmap:** [ROADMAP.md](ROADMAP.md) - Updated with Customer Portal as Phase 2
- **Current Status:** Phase 1 complete, ready to start Phase 2A

---

## Documentation
- **Setup Guide**: [docs/SETUP.md](docs/SETUP.md)
- **API Docs**: Auto-generated at http://localhost:8000/docs when server running
- **Database Schema**: [scripts/setup_database.sql](scripts/setup_database.sql)

## Support
- **Issues**: Track in GitHub or local issue tracker
- **Questions**: Document in `docs/FAQ.md` as they come up
