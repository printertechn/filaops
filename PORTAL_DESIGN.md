# BLB3D Customer Portal - Architecture Design

**Status:** Phase 2 Planning
**Priority:** High - Competitive Advantage
**Goal:** Real-time STL quoting and ordering system to replace traditional e-commerce

---

## Overview

The Customer Portal is a web application that allows customers to:
1. Upload STL files and receive instant quotes
2. Configure print options (material, color, quantity, finish)
3. Create accounts and manage orders
4. Make payments and track production
5. Download completed files and reorder

This becomes the **primary ordering channel** for BLB3D, with Squarespace handling marketing and product catalog.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Customer Portal (React)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ STL Uploader │  │ Quote Config │  │  Dashboard   │     │
│  │  + 3D Preview│  │  + Instant $ │  │  + Tracking  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API (JWT Auth)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Auth Service │  │ Quote Engine │  │ Order Service│     │
│  │   (PyJWT)    │  │  (STL Parse) │  │   (Stripe)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              SQL Server Express (BLB3D_ERP)                  │
│  • users (auth + profiles)                                   │
│  • quotes (STL files + pricing)                              │
│  • sales_orders (confirmed orders)                           │
│  • production_orders (manufacturing)                         │
│  • stl_files (uploaded models + metadata)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Features

### 1. Real-Time STL Quoting Engine (MVP Feature) 🎯

**Strategic Decision:** Use Bambu Print Suite's existing quoter for accuracy and speed!

**Why Use Bambu Suite Quoter:**
- ✅ Uses actual slicer (PrusaSlicer/BambuStudio) for accurate estimates
- ✅ Tied to real printer capabilities and speeds
- ✅ ML-powered predictions based on historical data
- ✅ Already handles STL parsing, validation, slicing
- ✅ Reduces development time from 6 weeks → 2 weeks
- ✅ Single source of truth for print estimates
- ✅ Maintains itself as Bambu Suite improves

**User Flow:**
1. Customer uploads STL file (drag-and-drop)
2. Portal → Forwards STL to Bambu Suite API (Port 8001)
3. Bambu Suite:
   - Parses and validates STL
   - Slices with actual slicer
   - Calculates accurate print time
   - Calculates material usage
   - Returns ML-enhanced estimates
4. Portal receives Bambu quote and applies:
   - Business markup (2.5x)
   - Quantity discounts
   - Finish upcharges
   - Rush order fees
5. Customer selects options:
   - Material type (PLA, PETG, ABS, TPU, Resin)
   - Color (if available)
   - Quantity (1-100+)
   - Finish (standard, sanded, painted)
   - Infill density (10-100%)
6. Portal shows final price with breakdown
7. Customer adds to cart

**Technical Implementation:**

**Bambu Suite API Client:**
```python
# app/services/bambu_quote_service.py

import httpx
from typing import Optional
from fastapi import UploadFile

class BambuQuoteService:
    """Service to get quotes from Bambu Print Suite"""

    def __init__(self):
        self.bambu_api_url = "http://localhost:8001"
        self.timeout = 30.0  # 30 second timeout for slicing

    async def upload_stl_and_get_quote(
        self,
        stl_file: UploadFile,
        material_type: str,
        quantity: int,
        infill: int = 20,
        color: Optional[str] = None
    ) -> dict:
        """
        Upload STL to Bambu Suite and get accurate quote

        Returns:
            {
                "quote_id": "BAMBU-QUOTE-123",
                "filename": "model.stl",
                "estimated_time_hours": 2.5,
                "estimated_material_grams": 45.3,
                "estimated_material_cost": 0.91,
                "volume_cm3": 27.0,
                "surface_area_cm2": 54.0,
                "is_watertight": True,
                "ml_confidence_score": 0.92,
                "slicer_preview_url": "/api/previews/..."
            }
        """

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Upload STL to Bambu Suite
                files = {
                    "file": (stl_file.filename, stl_file.file, "model/stl")
                }
                data = {
                    "material": material_type,
                    "quantity": quantity,
                    "infill_percent": infill,
                    "color": color or ""
                }

                response = await client.post(
                    f"{self.bambu_api_url}/api/quotes/upload",
                    files=files,
                    data=data
                )
                response.raise_for_status()

                bambu_quote = response.json()

                # Apply our business rules and pricing
                final_quote = self.apply_pricing_rules(bambu_quote, quantity)

                return final_quote

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Quote generation timed out. Please try a smaller file or contact support."
            )
        except httpx.HTTPError as e:
            logger.error(f"Bambu Suite API error: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail="Quote service temporarily unavailable. Please try again in a moment."
            )

    def apply_pricing_rules(self, bambu_quote: dict, quantity: int) -> dict:
        """Apply BLB3D pricing rules to Bambu Suite quote"""

        # Get base costs from Bambu Suite (more accurate!)
        material_cost = bambu_quote["estimated_material_cost"]
        print_time_hours = bambu_quote["estimated_time_hours"]

        # Apply our machine hourly rate
        machine_cost = print_time_hours * MACHINE_HOURLY_RATE  # e.g., $2.50/hour

        # Calculate unit cost
        unit_cost = material_cost + machine_cost

        # Apply markup
        unit_price = unit_cost * MARKUP_MULTIPLIER  # e.g., 2.5x

        # Calculate quantity discount
        discount = self.calculate_quantity_discount(quantity)
        unit_price_discounted = unit_price * (1 - discount)

        # Calculate delivery estimate
        delivery_days = self.estimate_delivery(print_time_hours, quantity)

        return {
            # Customer-facing pricing
            "unit_price": round(unit_price_discounted, 2),
            "total_price": round(unit_price_discounted * quantity, 2),
            "quantity": quantity,
            "discount_percent": discount * 100,
            "estimated_delivery_days": delivery_days,

            # Cost breakdown (for transparency)
            "breakdown": {
                "material_grams": bambu_quote["estimated_material_grams"],
                "print_time_hours": print_time_hours,
                "material_cost": round(material_cost, 2),
                "machine_cost": round(machine_cost, 2),
                "unit_cost": round(unit_cost, 2),
                "markup_applied": MARKUP_MULTIPLIER
            },

            # Pass through Bambu Suite data (for reference)
            "bambu_data": {
                "quote_id": bambu_quote["quote_id"],
                "volume_cm3": bambu_quote["volume_cm3"],
                "surface_area_cm2": bambu_quote["surface_area_cm2"],
                "is_watertight": bambu_quote["is_watertight"],
                "ml_confidence_score": bambu_quote.get("ml_confidence_score", 0.85),
                "slicer_preview_url": bambu_quote.get("slicer_preview_url")
            }
        }

    def calculate_quantity_discount(self, quantity: int) -> float:
        """Calculate discount based on quantity"""
        if quantity >= 100:
            return 0.25  # 25% off
        elif quantity >= 50:
            return 0.15  # 15% off
        elif quantity >= 10:
            return 0.10  # 10% off
        else:
            return 0.0  # No discount

    def estimate_delivery(self, print_time_hours: float, quantity: int) -> int:
        """
        Estimate delivery time based on print time and queue

        TODO: Query actual printer availability and queue
        """
        total_hours = print_time_hours * quantity

        # Rough estimate: 8 hours per day of printing
        days = math.ceil(total_hours / 8)

        # Add buffer for processing, QC, shipping
        days += 2

        return days
```

**Quote Endpoint:**
```python
# app/api/v1/endpoints/quotes.py

@router.post("/quotes", response_model=QuoteResponse)
async def create_quote(
    file: UploadFile = File(...),
    material: str = Form(...),
    quantity: int = Form(...),
    infill: int = Form(20),
    color: Optional[str] = Form(None),
    finish: str = Form("standard"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create quote by uploading STL to Bambu Suite

    Process:
    1. Validate file (STL only, max 100MB)
    2. Forward to Bambu Suite for slicing/analysis
    3. Apply BLB3D pricing rules
    4. Save quote to database
    5. Return quote to customer
    """

    # Validate file
    if not file.filename.endswith(".stl"):
        raise HTTPException(400, "Only STL files are supported")

    if file.size > 100 * 1024 * 1024:  # 100MB
        raise HTTPException(400, "File too large. Maximum size is 100MB")

    # Get quote from Bambu Suite
    bambu_service = BambuQuoteService()
    quote_data = await bambu_service.upload_stl_and_get_quote(
        stl_file=file,
        material_type=material,
        quantity=quantity,
        infill=infill,
        color=color
    )

    # Apply finish upcharge
    finish_cost = FINISH_COSTS.get(finish, 0)
    quote_data["total_price"] += finish_cost * quantity

    # Save STL file record
    stl_file = STLFile(
        user_id=current_user.id,
        filename=file.filename,
        file_path=f"uploads/stl/{current_user.id}/{file.filename}",
        file_size_bytes=file.size,
        volume_cm3=quote_data["bambu_data"]["volume_cm3"],
        surface_area_cm2=quote_data["bambu_data"]["surface_area_cm2"],
        is_watertight=quote_data["bambu_data"]["is_watertight"]
    )
    db.add(stl_file)
    db.flush()

    # Save quote to database
    quote = Quote(
        user_id=current_user.id,
        stl_file_id=stl_file.id,
        bambu_quote_id=quote_data["bambu_data"]["quote_id"],
        material_type=material,
        color=color,
        quantity=quantity,
        infill_percent=infill,
        finish=finish,
        unit_price=quote_data["unit_price"],
        total_price=quote_data["total_price"],
        discount_percent=quote_data["discount_percent"],
        estimated_material_grams=quote_data["breakdown"]["material_grams"],
        estimated_print_time_hours=quote_data["breakdown"]["print_time_hours"],
        estimated_delivery_days=quote_data["estimated_delivery_days"],
        ml_confidence_score=quote_data["bambu_data"]["ml_confidence_score"],
        status="draft"
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)

    return quote
```

---

### 2. Authentication System (PyJWT)

**Endpoints:**
- `POST /api/v1/auth/register` - Create account
- `POST /api/v1/auth/login` - Get JWT tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Invalidate tokens
- `POST /api/v1/auth/forgot-password` - Send reset email
- `POST /api/v1/auth/reset-password` - Reset with token

**Implementation:**
```python
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "your-secret-key-from-env"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

def create_access_token(user_id: int):
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: int):
    """Create JWT refresh token"""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain, hashed)
```

**Database Schema:**
```sql
CREATE TABLE users (
    id INT PRIMARY KEY IDENTITY(1,1),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    company VARCHAR(100),

    -- Status
    is_active BIT DEFAULT 1,
    is_verified BIT DEFAULT 0,
    email_verified_at DATETIME,

    -- Addresses
    billing_address_line1 VARCHAR(255),
    billing_address_line2 VARCHAR(255),
    billing_city VARCHAR(100),
    billing_state VARCHAR(50),
    billing_zip VARCHAR(20),
    billing_country VARCHAR(50),

    shipping_address_line1 VARCHAR(255),
    shipping_address_line2 VARCHAR(255),
    shipping_city VARCHAR(100),
    shipping_state VARCHAR(50),
    shipping_zip VARCHAR(20),
    shipping_country VARCHAR(50),

    -- Metadata
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    last_login_at DATETIME,

    INDEX idx_email (email),
    INDEX idx_created_at (created_at)
);

CREATE TABLE refresh_tokens (
    id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT FOREIGN KEY REFERENCES users(id),
    token_hash VARCHAR(255) NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    revoked_at DATETIME,

    INDEX idx_user_id (user_id),
    INDEX idx_token_hash (token_hash)
);
```

---

### 3. Order Management

**Endpoints:**
- `POST /api/v1/quotes` - Create quote from STL upload
- `GET /api/v1/quotes/{id}` - Get quote details
- `POST /api/v1/quotes/{id}/order` - Convert quote to order
- `GET /api/v1/orders` - List user's orders
- `GET /api/v1/orders/{id}` - Get order details
- `GET /api/v1/orders/{id}/status` - Get production status

**Database Schema:**
```sql
CREATE TABLE quotes (
    id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT FOREIGN KEY REFERENCES users(id),
    stl_file_id INT FOREIGN KEY REFERENCES stl_files(id),

    -- Configuration
    material_type VARCHAR(50) NOT NULL,
    color VARCHAR(50),
    quantity INT NOT NULL,
    infill_percent INT NOT NULL DEFAULT 20,
    finish VARCHAR(50) NOT NULL DEFAULT 'standard',

    -- Pricing
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    discount_percent DECIMAL(5,2) DEFAULT 0,

    -- Estimates
    estimated_material_grams DECIMAL(10,2),
    estimated_print_time_hours DECIMAL(10,2),
    estimated_delivery_days INT,

    -- Status
    status VARCHAR(20) DEFAULT 'draft',  -- draft, expired, ordered
    expires_at DATETIME,
    ordered_at DATETIME,

    -- Metadata
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),

    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

CREATE TABLE stl_files (
    id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT FOREIGN KEY REFERENCES users(id),

    -- File info
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size_bytes INT NOT NULL,
    file_hash VARCHAR(64) NOT NULL,  -- SHA256 for deduplication

    -- 3D model metrics
    volume_cm3 DECIMAL(10,3),
    surface_area_cm2 DECIMAL(10,2),
    bounding_box_x DECIMAL(10,2),
    bounding_box_y DECIMAL(10,2),
    bounding_box_z DECIMAL(10,2),
    is_watertight BIT,
    triangle_count INT,

    -- Thumbnail
    thumbnail_path VARCHAR(500),

    -- Metadata
    created_at DATETIME DEFAULT GETDATE(),

    INDEX idx_user_id (user_id),
    INDEX idx_file_hash (file_hash)
);
```

---

### 4. Payment Integration (Stripe)

**Flow:**
1. Customer clicks "Place Order" on quote
2. Frontend creates Stripe Payment Intent via backend
3. Customer enters card details (Stripe Elements on frontend)
4. Payment processed by Stripe
5. Backend receives webhook confirmation
6. Order confirmed, sales order created
7. Production orders auto-generated
8. Customer receives order confirmation email

**Implementation:**
```python
import stripe

stripe.api_key = "your-stripe-secret-key"

def create_payment_intent(quote_id: int, user_id: int):
    """Create Stripe payment intent"""
    quote = db.query(Quote).filter_by(id=quote_id, user_id=user_id).first()

    # Create payment intent
    intent = stripe.PaymentIntent.create(
        amount=int(quote.total_price * 100),  # Convert to cents
        currency="usd",
        metadata={
            "quote_id": quote.id,
            "user_id": user.id,
            "user_email": user.email
        }
    )

    return {
        "client_secret": intent.client_secret,
        "amount": quote.total_price
    }

@app.post("/api/v1/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400)

    # Handle payment success
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        quote_id = payment_intent["metadata"]["quote_id"]

        # Create sales order from quote
        create_order_from_quote(quote_id)

        # Send confirmation email
        send_order_confirmation_email(quote_id)

    return {"status": "success"}
```

**Requirements:**
```python
# Add to requirements.txt
stripe==7.8.0
```

---

### 5. Frontend Architecture (React + Vite)

**Tech Stack:**
- **Framework:** React 18 with TypeScript
- **Build Tool:** Vite
- **Styling:** TailwindCSS
- **3D Viewer:** React Three Fiber (Three.js wrapper)
- **State Management:** Zustand or Context API
- **HTTP Client:** Axios
- **Routing:** React Router v6
- **Forms:** React Hook Form
- **UI Components:** shadcn/ui or Headless UI
- **Icons:** Lucide React

**Key Components:**

```
frontend/
├── src/
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── RegisterForm.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   ├── upload/
│   │   │   ├── STLUploader.tsx         # Drag-and-drop
│   │   │   ├── STLViewer3D.tsx         # Three.js viewer
│   │   │   └── UploadProgress.tsx
│   │   ├── quote/
│   │   │   ├── QuoteConfigurator.tsx   # Material, quantity, etc.
│   │   │   ├── QuoteSummary.tsx        # Price breakdown
│   │   │   └── QuoteHistory.tsx
│   │   ├── order/
│   │   │   ├── OrderList.tsx
│   │   │   ├── OrderDetails.tsx
│   │   │   └── OrderTracking.tsx       # Production status
│   │   ├── payment/
│   │   │   └── StripeCheckout.tsx      # Stripe Elements
│   │   └── dashboard/
│   │       └── UserDashboard.tsx
│   ├── pages/
│   │   ├── Home.tsx
│   │   ├── GetQuote.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Orders.tsx
│   │   └── Account.tsx
│   ├── services/
│   │   ├── api.ts                      # Axios instance
│   │   ├── authService.ts
│   │   ├── quoteService.ts
│   │   └── orderService.ts
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   └── useSTLUpload.ts
│   └── App.tsx
```

**STL Uploader Component:**
```typescript
import { useDropzone } from 'react-dropzone';
import { useState } from 'react';

export function STLUploader({ onUploadComplete }) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const { getRootProps, getInputProps } = useDropzone({
    accept: { 'model/stl': ['.stl'] },
    maxFiles: 1,
    maxSize: 100 * 1024 * 1024, // 100MB
    onDrop: async (acceptedFiles) => {
      const file = acceptedFiles[0];
      setUploading(true);

      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await axios.post('/api/v1/stl/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (e) => {
            setProgress(Math.round((e.loaded * 100) / e.total));
          }
        });

        onUploadComplete(response.data);
      } catch (error) {
        console.error('Upload failed:', error);
      } finally {
        setUploading(false);
      }
    }
  });

  return (
    <div {...getRootProps()} className="border-2 border-dashed p-8 rounded-lg cursor-pointer">
      <input {...getInputProps()} />
      {uploading ? (
        <ProgressBar progress={progress} />
      ) : (
        <div>
          <p>Drag & drop STL file here, or click to select</p>
          <p className="text-sm text-gray-500">Max 100MB</p>
        </div>
      )}
    </div>
  );
}
```

---

## Database Schema Updates

Need to add to [scripts/setup_database.sql](scripts/setup_database.sql):

```sql
-- Users table
CREATE TABLE users (
    -- See "Authentication System" section above
);

-- Quotes table
CREATE TABLE quotes (
    -- See "Order Management" section above
);

-- STL files table
CREATE TABLE stl_files (
    -- See "Order Management" section above
);

-- Refresh tokens table
CREATE TABLE refresh_tokens (
    -- See "Authentication System" section above
);
```

---

## API Endpoints Summary

### Auth Endpoints
- `POST /api/v1/auth/register` - Create account
- `POST /api/v1/auth/login` - Get JWT tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Invalidate tokens
- `POST /api/v1/auth/forgot-password` - Send reset email
- `POST /api/v1/auth/reset-password` - Reset with token
- `GET /api/v1/auth/me` - Get current user

### STL & Quote Endpoints
- `POST /api/v1/stl/upload` - Upload STL file
- `GET /api/v1/stl/{id}` - Get STL metadata
- `GET /api/v1/stl/{id}/thumbnail` - Get thumbnail image
- `POST /api/v1/quotes` - Create quote from STL
- `GET /api/v1/quotes` - List user's quotes
- `GET /api/v1/quotes/{id}` - Get quote details
- `PATCH /api/v1/quotes/{id}` - Update quote configuration
- `DELETE /api/v1/quotes/{id}` - Delete quote

### Order Endpoints
- `POST /api/v1/orders` - Create order from quote (with payment)
- `GET /api/v1/orders` - List user's orders
- `GET /api/v1/orders/{id}` - Get order details
- `GET /api/v1/orders/{id}/status` - Get production status
- `GET /api/v1/orders/{id}/invoice` - Download invoice PDF

### Payment Endpoints
- `POST /api/v1/payment/intent` - Create Stripe payment intent
- `POST /api/v1/webhooks/stripe` - Stripe webhook handler

### User Endpoints
- `GET /api/v1/users/me` - Get user profile
- `PATCH /api/v1/users/me` - Update profile
- `GET /api/v1/users/me/addresses` - Get saved addresses
- `POST /api/v1/users/me/addresses` - Add address

---

## Implementation Phases (REVISED - 8-10 weeks)

**Key Change:** Using Bambu Suite quoter cuts 4-6 weeks of development!

### Phase 2A: Authentication & User Management (Week 1-2) ✅ Test-Driven
1. **Write tests first** (see [TESTING_STRATEGY.md](TESTING_STRATEGY.md))
2. Add PyJWT to requirements.txt
3. Create users table and User model
4. Implement auth endpoints (register, login, refresh)
5. Add JWT middleware for protected routes
6. Create user profile endpoints
7. **Verify 100% test coverage on auth**

**Testing:** Unit tests + Integration tests for all auth endpoints

### Phase 2B: Bambu Suite Integration (Week 3-4) ✅ Test-Driven
1. **Write mock Bambu Suite server for tests**
2. Create stl_files and quotes tables
3. Create STLFile and Quote models
4. Implement Bambu API client (BambuQuoteService)
5. Build quote upload endpoint → forwards to Bambu Suite
6. Apply pricing rules (markup, discounts, finish costs)
7. **Test with mock + manual testing with real Bambu Suite**

**Testing:** Mock Bambu API + Integration tests + Manual validation

### Phase 2C: Payment Integration (Week 5) ✅ Test-Driven
1. **Write Stripe mock for tests**
2. Add Stripe to requirements.txt
3. Create Stripe test account and get API keys
4. Implement payment intent endpoint
5. Set up Stripe webhook handler (payment success)
6. Create order from quote on payment
7. Link order → production order → print job
8. **Test payment flow end-to-end**

**Testing:** Stripe test mode + Webhook testing + E2E flow

### Phase 2D: Frontend Development (Week 6-8)
1. Set up React + Vite + TypeScript
2. Install TailwindCSS and shadcn/ui
3. Build authentication UI (login/register)
4. Build STL uploader with drag-and-drop
5. Build quote configurator UI
6. Integrate Stripe Elements for payment
7. Build user dashboard
8. Build order tracking page
9. Add responsive design

**Testing:** Playwright E2E tests for critical flows

### Phase 2E: Integration & Testing (Week 9-10)
1. **Run full test suite** (unit + integration + E2E)
2. **Security testing** (OWASP ZAP, penetration testing)
3. **Load testing** (100 concurrent users, large files)
4. **Quote accuracy validation** (compare estimates vs actuals)
5. Performance optimization (caching, query optimization)
6. Error handling and user-friendly messages
7. Production deployment
8. **Monitoring and alerting setup**

**Testing:** See complete checklist in [TESTING_STRATEGY.md](TESTING_STRATEGY.md)

---

## Security Considerations

1. **File Upload Security:**
   - Validate file type (only .stl allowed)
   - Scan for malware (ClamAV integration)
   - Limit file size (100MB max)
   - Store with unique filenames (UUID)
   - Never execute uploaded files

2. **Authentication Security:**
   - Use strong password requirements
   - Hash passwords with bcrypt (already installed)
   - Use short-lived access tokens (30 min)
   - Implement refresh token rotation
   - Rate limit login attempts (5 attempts per 15 min)
   - Add CAPTCHA for registration

3. **API Security:**
   - CORS configuration for frontend domain only
   - Rate limiting on all endpoints
   - Input validation with Pydantic
   - SQL injection prevention (SQLAlchemy parameterized queries)
   - XSS prevention (sanitize outputs)
   - HTTPS only in production

4. **Payment Security:**
   - Never store credit card details (Stripe handles this)
   - Verify webhook signatures
   - Use Stripe test mode for development
   - PCI compliance through Stripe

---

## Configuration

Add to [backend/app/core/config.py](backend/app/core/config.py):

```python
class Settings(BaseSettings):
    # Existing settings...

    # JWT Configuration
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # File Upload
    UPLOAD_DIR: str = "uploads/stl_files"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: list = [".stl"]

    # Stripe
    STRIPE_SECRET_KEY: str = "sk_test_..."
    STRIPE_PUBLISHABLE_KEY: str = "pk_test_..."
    STRIPE_WEBHOOK_SECRET: str = "whsec_..."

    # Pricing
    MACHINE_HOURLY_RATE: float = 2.50
    MARKUP_MULTIPLIER: float = 2.5

    # Email (for notifications)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "your-email@gmail.com"
    SMTP_PASSWORD: str = "your-app-password"
    FROM_EMAIL: str = "noreply@blb3d.com"
```

---

## Dependencies to Add

Update [backend/requirements.txt](backend/requirements.txt):

```python
# Add these for Phase 2
PyJWT==2.10.1              # JWT authentication (replaces python-jose)
stripe==7.8.0              # Payment processing
pillow==11.0.0             # Image processing for thumbnails (optional)
python-magic==0.4.27       # File type detection (optional)

# NOTE: trimesh/numpy NOT needed - using Bambu Suite quoter!
# httpx==0.25.1 already installed for API calls
```

---

## Success Metrics

Portal will be considered successful when:
- ✅ Customer can upload STL and receive quote in < 5 seconds
- ✅ Quote accuracy within 10% of actual production cost
- ✅ 95%+ of quotes can be generated without errors
- ✅ Payment processing success rate > 98%
- ✅ Average order completion time < 48 hours
- ✅ Customer satisfaction score > 4.5/5
- ✅ Portal handles 1000+ concurrent users

---

## Questions for User

Before starting Phase 2 implementation, need to clarify:

1. **Pricing Strategy:**
   - What's the target markup multiplier? (2x, 2.5x, 3x?)
   - Quantity discount tiers? (10+, 50+, 100+?)
   - Finish pricing (sanded, painted, etc.)?
   - Rush order pricing?

2. **Materials Available:**
   - What materials do you stock? (PLA, PETG, ABS, TPU, Resin?)
   - Color options per material?
   - Cost per gram for each material?

3. **Machine Capabilities:**
   - How many printers? (for delivery time estimation)
   - Build volumes for each printer?
   - Average hourly cost per printer?

4. **Business Rules:**
   - Minimum order value?
   - Maximum file size for uploads?
   - Auto-approve orders or manual review?
   - Refund policy?

5. **Integrations:**
   - Existing Stripe account or create new?
   - Email provider (Gmail, SendGrid, etc.)?
   - File storage preference (local, Azure Blob, AWS S3)?

---

## Next Steps

1. Review this architecture document
2. Answer the questions above
3. Set up Stripe test account
4. Begin Phase 2A: Authentication implementation
5. Create users table in database
6. Implement JWT auth endpoints

---

**Last Updated:** 2025-11-24
**Status:** Phase 2 Planning Complete, Awaiting User Approval
