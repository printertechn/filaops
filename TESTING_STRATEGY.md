# BLB3D ERP - Testing Strategy

**Priority:** CRITICAL - Customer-facing portal must be bulletproof
**Approach:** Test-Driven Development (TDD) + Automated Testing + Manual QA

---

## 🎯 Testing Philosophy

### **Zero Tolerance for Production Bugs**
- No feature ships without tests
- Every bug found = new test added
- Automated tests run on every commit (GitHub Actions)
- Manual testing before every deployment

### **Test Coverage Goals**
- **Backend:** 90%+ code coverage
- **Critical Paths:** 100% coverage (auth, quotes, payments)
- **Integration:** All API endpoints tested
- **E2E:** Complete user flows tested

---

## 🧪 Testing Pyramid

```
                    ┌─────────────────┐
                    │  Manual QA      │  (Small - before release)
                    │  Exploratory    │
                    └─────────────────┘
                ┌───────────────────────┐
                │  End-to-End Tests     │  (Medium - critical flows)
                │  Playwright/Selenium  │
                └───────────────────────┘
            ┌───────────────────────────────┐
            │  Integration Tests            │  (Large - API endpoints)
            │  FastAPI TestClient           │
            └───────────────────────────────┘
        ┌───────────────────────────────────────┐
        │  Unit Tests                           │  (Largest - business logic)
        │  pytest                               │
        └───────────────────────────────────────┘
```

---

## 📋 Phase-by-Phase Testing Plan

### **Phase 2A: Authentication Testing**

#### Unit Tests
```python
# tests/test_auth.py

def test_hash_password():
    """Test password hashing works"""
    password = "SecurePass123!"
    hashed = hash_password(password)
    assert verify_password(password, hashed)
    assert not verify_password("WrongPass", hashed)

def test_create_access_token():
    """Test JWT token creation"""
    token = create_access_token(user_id=1)
    assert token is not None
    payload = verify_token(token)
    assert payload["sub"] == "1"
    assert payload["type"] == "access"

def test_token_expiration():
    """Test expired tokens are rejected"""
    # Create token that expires in 1 second
    token = create_access_token(user_id=1, expires_delta=timedelta(seconds=1))
    time.sleep(2)
    with pytest.raises(HTTPException) as exc:
        verify_token(token)
    assert exc.value.status_code == 401
```

#### Integration Tests
```python
# tests/integration/test_auth_api.py

def test_register_user(client: TestClient):
    """Test user registration endpoint"""
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "SecurePass123!",
        "first_name": "Test",
        "last_name": "User"
    })
    assert response.status_code == 201
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()

def test_register_duplicate_email(client: TestClient):
    """Test duplicate email is rejected"""
    # Register first user
    client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "Pass123!"
    })
    # Try to register again with same email
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "DifferentPass123!"
    })
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()

def test_login_success(client: TestClient, test_user):
    """Test successful login"""
    response = client.post("/api/v1/auth/login", json={
        "email": test_user["email"],
        "password": "TestPassword123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client: TestClient, test_user):
    """Test login with wrong password fails"""
    response = client.post("/api/v1/auth/login", json={
        "email": test_user["email"],
        "password": "WrongPassword!"
    })
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()

def test_refresh_token(client: TestClient, test_user):
    """Test refresh token endpoint"""
    # Login to get tokens
    login_response = client.post("/api/v1/auth/login", json={
        "email": test_user["email"],
        "password": "TestPassword123!"
    })
    refresh_token = login_response.json()["refresh_token"]

    # Use refresh token to get new access token
    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_protected_endpoint_without_token(client: TestClient):
    """Test protected endpoint rejects requests without token"""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

def test_protected_endpoint_with_token(client: TestClient, test_user, auth_headers):
    """Test protected endpoint accepts valid token"""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["email"]
```

---

### **Phase 2B: Bambu Suite Integration Testing**

#### Mock Bambu Suite API
```python
# tests/mocks/bambu_mock_server.py

from fastapi import FastAPI
from typing import Optional

app = FastAPI()

# Mock quote responses
MOCK_QUOTES = {
    "test_cube.stl": {
        "estimated_time_hours": 2.5,
        "estimated_material_grams": 45.3,
        "estimated_material_cost": 0.91,  # $0.91
        "volume_cm3": 27.0,
        "surface_area_cm2": 54.0,
        "is_watertight": True,
        "ml_confidence_score": 0.92
    },
    "complex_model.stl": {
        "estimated_time_hours": 8.2,
        "estimated_material_grams": 156.7,
        "estimated_material_cost": 3.13,
        "volume_cm3": 93.4,
        "surface_area_cm2": 187.8,
        "is_watertight": True,
        "ml_confidence_score": 0.88
    }
}

@app.post("/api/quotes/upload")
async def mock_upload_stl(file: UploadFile, material: str, quantity: int, infill_percent: int):
    """Mock Bambu Suite quote upload endpoint"""

    # Simulate processing delay
    await asyncio.sleep(0.5)

    # Return mock quote based on filename
    quote_data = MOCK_QUOTES.get(file.filename, MOCK_QUOTES["test_cube.stl"])

    return {
        "quote_id": f"QUOTE-{uuid.uuid4()}",
        "filename": file.filename,
        "material": material,
        "quantity": quantity,
        "infill_percent": infill_percent,
        **quote_data
    }

@app.get("/api/quotes/{quote_id}")
async def mock_get_quote(quote_id: str):
    """Mock get quote endpoint"""
    return {
        "quote_id": quote_id,
        "status": "completed",
        **MOCK_QUOTES["test_cube.stl"]
    }

# Run mock server during tests
# pytest-mock-server will start this on port 8001 during test runs
```

#### Integration Tests with Mock
```python
# tests/integration/test_bambu_integration.py

@pytest.fixture
def mock_bambu_server():
    """Start mock Bambu Suite server for tests"""
    # This starts the mock server defined above
    yield from start_mock_server(bambu_mock_server.app, port=8001)

def test_upload_stl_to_bambu(client: TestClient, mock_bambu_server):
    """Test STL upload forwards to Bambu Suite"""

    # Create test STL file
    stl_content = create_test_stl_cube()
    files = {"file": ("test_cube.stl", stl_content, "model/stl")}

    response = client.post(
        "/api/v1/stl/upload",
        files=files,
        data={"material": "PLA", "quantity": 1, "infill": 20}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify we got quote data back
    assert "estimated_time_hours" in data
    assert "estimated_material_grams" in data
    assert "estimated_material_cost" in data
    assert data["ml_confidence_score"] > 0.8

def test_quote_price_calculation(client: TestClient, mock_bambu_server):
    """Test that we correctly calculate final price from Bambu quote"""

    stl_content = create_test_stl_cube()
    files = {"file": ("test_cube.stl", stl_content, "model/stl")}

    response = client.post(
        "/api/v1/quotes",
        files=files,
        data={"material": "PLA", "quantity": 1, "infill": 20}
    )

    data = response.json()

    # Verify pricing calculation
    # Bambu quote: $0.91 material + (2.5 hours * $2.50/hr) = $7.16 cost
    # With 2.5x markup = $17.90
    expected_price = round((0.91 + (2.5 * 2.50)) * 2.5, 2)
    assert data["unit_price"] == expected_price

def test_quote_with_quantity_discount(client: TestClient, mock_bambu_server):
    """Test quantity discounts are applied correctly"""

    stl_content = create_test_stl_cube()
    files = {"file": ("test_cube.stl", stl_content, "model/stl")}

    # Order 50 units (15% discount)
    response = client.post(
        "/api/v1/quotes",
        files=files,
        data={"material": "PLA", "quantity": 50, "infill": 20}
    )

    data = response.json()

    # Verify discount applied
    assert data["discount_percent"] == 15.0
    base_price = round((0.91 + (2.5 * 2.50)) * 2.5, 2)  # $17.90
    discounted_price = round(base_price * 0.85, 2)  # 15% off = $15.22
    assert data["unit_price"] == discounted_price
    assert data["total_price"] == discounted_price * 50

def test_bambu_suite_unavailable(client: TestClient, monkeypatch):
    """Test graceful handling when Bambu Suite is down"""

    # Stop mock server (simulate Bambu Suite down)
    def mock_connection_error(*args, **kwargs):
        raise ConnectionError("Bambu Suite unavailable")

    monkeypatch.setattr("httpx.AsyncClient.post", mock_connection_error)

    stl_content = create_test_stl_cube()
    files = {"file": ("test_cube.stl", stl_content, "model/stl")}

    response = client.post(
        "/api/v1/quotes",
        files=files,
        data={"material": "PLA", "quantity": 1, "infill": 20}
    )

    # Should return 503 Service Unavailable
    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"].lower()
```

---

### **Phase 2C: Payment Testing (Stripe)**

#### Mock Stripe Client
```python
# tests/mocks/stripe_mock.py

class MockStripeClient:
    """Mock Stripe client for testing"""

    def create_payment_intent(self, amount: int, currency: str, metadata: dict):
        """Mock create payment intent"""
        return {
            "id": f"pi_test_{uuid.uuid4()}",
            "client_secret": f"pi_test_{uuid.uuid4()}_secret_test",
            "amount": amount,
            "currency": currency,
            "status": "requires_payment_method",
            "metadata": metadata
        }

    def confirm_payment_intent(self, payment_intent_id: str):
        """Mock confirm payment"""
        return {
            "id": payment_intent_id,
            "status": "succeeded",
            "amount_received": 1790  # $17.90
        }
```

#### Integration Tests
```python
# tests/integration/test_payment.py

def test_create_payment_intent(client: TestClient, test_quote, auth_headers):
    """Test creating payment intent for quote"""

    response = client.post(
        f"/api/v1/payment/intent",
        json={"quote_id": test_quote["id"]},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "client_secret" in data
    assert data["amount"] == test_quote["total_price"]

def test_webhook_payment_success(client: TestClient, test_quote):
    """Test Stripe webhook creates order on payment success"""

    # Simulate Stripe webhook
    webhook_payload = {
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test_123",
                "amount": int(test_quote["total_price"] * 100),
                "metadata": {
                    "quote_id": test_quote["id"],
                    "user_id": test_quote["user_id"]
                }
            }
        }
    }

    response = client.post(
        "/api/v1/webhooks/stripe",
        json=webhook_payload,
        headers={"stripe-signature": "test_signature"}
    )

    assert response.status_code == 200

    # Verify sales order was created
    order_response = client.get(
        f"/api/v1/orders?quote_id={test_quote['id']}",
        headers=auth_headers
    )
    orders = order_response.json()
    assert len(orders) == 1
    assert orders[0]["status"] == "confirmed"

def test_payment_creates_production_order(client: TestClient, test_quote, auth_headers):
    """Test successful payment auto-creates production order"""

    # Complete payment
    complete_payment_for_quote(test_quote["id"])

    # Verify production order created
    response = client.get(
        f"/api/v1/production-orders",
        headers=auth_headers
    )

    prod_orders = response.json()
    assert len(prod_orders) > 0

    # Find our production order
    our_order = next(po for po in prod_orders if po["product_id"] == test_quote["product_id"])
    assert our_order["quantity"] == test_quote["quantity"]
    assert our_order["status"] == "draft"
```

---

### **End-to-End Tests (Complete User Flows)**

```python
# tests/e2e/test_complete_order_flow.py

@pytest.mark.e2e
def test_complete_customer_journey(browser: PlaywrightPage):
    """Test complete flow: Register → Upload → Quote → Pay → Track"""

    # 1. Customer visits portal
    browser.goto("http://localhost:3000")

    # 2. Register new account
    browser.click("text=Sign Up")
    browser.fill("[name=email]", "customer@example.com")
    browser.fill("[name=password]", "SecurePass123!")
    browser.fill("[name=firstName]", "John")
    browser.fill("[name=lastName]", "Doe")
    browser.click("button[type=submit]")

    # Wait for redirect to dashboard
    browser.wait_for_url("**/dashboard")
    assert "Welcome, John" in browser.inner_text("body")

    # 3. Upload STL file
    browser.click("text=Get Quote")
    browser.set_input_files("[type=file]", "tests/fixtures/test_cube.stl")

    # Wait for file processing
    browser.wait_for_selector("text=File uploaded successfully")

    # 4. Configure quote
    browser.select_option("[name=material]", "PLA")
    browser.select_option("[name=color]", "Black")
    browser.fill("[name=quantity]", "10")
    browser.select_option("[name=infill]", "20")

    # Wait for quote calculation
    browser.wait_for_selector("[data-testid=quote-price]")

    # Verify quote displayed
    price_text = browser.inner_text("[data-testid=quote-price]")
    assert "$" in price_text

    # 5. Add to cart and checkout
    browser.click("text=Add to Cart")
    browser.click("text=Checkout")

    # 6. Enter payment (using Stripe test card)
    stripe_iframe = browser.frame_locator("iframe[name*=stripe]")
    stripe_iframe.locator("[name=cardnumber]").fill("4242424242424242")
    stripe_iframe.locator("[name=exp-date]").fill("12/25")
    stripe_iframe.locator("[name=cvc]").fill("123")
    stripe_iframe.locator("[name=postal]").fill("12345")

    browser.click("button:has-text('Place Order')")

    # 7. Verify order confirmation
    browser.wait_for_url("**/orders/*")
    assert "Order Confirmed" in browser.inner_text("h1")

    # Verify order details
    assert "10 units" in browser.inner_text("body")
    assert "PLA" in browser.inner_text("body")

    # 8. Check order status
    browser.click("text=View Orders")
    orders = browser.locator("[data-testid=order-card]")
    assert orders.count() >= 1

    # Verify production status
    first_order = orders.first
    status = first_order.locator("[data-testid=order-status]").inner_text()
    assert status in ["Confirmed", "In Production", "Queued"]

@pytest.mark.e2e
def test_quote_accuracy_validation(browser: PlaywrightPage, admin_auth):
    """Test quote estimates vs actual production data"""

    # This test runs after prints complete to verify accuracy
    # Compare estimated vs actual for last 100 orders

    response = requests.get(
        "http://localhost:8000/api/v1/analytics/quote-accuracy",
        headers=admin_auth
    )

    data = response.json()

    # Verify quote accuracy within 10%
    assert data["avg_time_variance_percent"] < 10
    assert data["avg_material_variance_percent"] < 10
    assert data["avg_cost_variance_percent"] < 10
```

---

## 🔄 Continuous Integration (GitHub Actions)

```yaml
# .github/workflows/tests.yml

name: Test Suite

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio

    - name: Run unit tests
      run: |
        cd backend
        pytest tests/unit/ -v --cov=app --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml

  integration-tests:
    runs-on: ubuntu-latest

    services:
      sqlserver:
        image: mcr.microsoft.com/mssql/server:2022-latest
        env:
          ACCEPT_EULA: Y
          SA_PASSWORD: Test1234!
        ports:
          - 1433:1433

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"

    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-asyncio

    - name: Set up test database
      run: |
        # Create test database schema
        sqlcmd -S localhost -U sa -P Test1234! -i scripts/setup_database.sql

    - name: Run integration tests
      run: |
        cd backend
        pytest tests/integration/ -v

  e2e-tests:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"

    - name: Set up Node
      uses: actions/setup-node@v4
      with:
        node-version: "20"

    - name: Install backend dependencies
      run: |
        cd backend
        pip install -r requirements.txt

    - name: Install frontend dependencies
      run: |
        cd frontend
        npm install

    - name: Start backend server
      run: |
        cd backend
        python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &

    - name: Start frontend dev server
      run: |
        cd frontend
        npm run dev &

    - name: Wait for servers
      run: |
        npx wait-on http://localhost:8000/health http://localhost:3000

    - name: Install Playwright
      run: npx playwright install --with-deps

    - name: Run E2E tests
      run: |
        cd frontend
        npx playwright test

    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: playwright-results
        path: frontend/test-results/
```

---

## 📊 Test Coverage Requirements

### **Critical Paths (100% Coverage Required)**
- ✅ Authentication (register, login, token refresh)
- ✅ Quote calculation (pricing, discounts)
- ✅ Payment processing (Stripe integration)
- ✅ Order creation (quote → sales order → production order)
- ✅ STL upload and validation

### **Important Paths (90%+ Coverage Required)**
- User profile management
- Order history and tracking
- Bambu Suite API integration
- Inventory checks
- Email notifications

### **Nice-to-Have (70%+ Coverage Required)**
- Admin dashboards
- Analytics endpoints
- Reporting functions

---

## 🐛 Bug Tracking & Regression Tests

### **Every Bug Gets a Test**

When a bug is found:
1. Write a failing test that reproduces the bug
2. Fix the bug
3. Verify test passes
4. Commit both test and fix together

Example:
```python
# Test added after bug discovery: ISSUE-123

def test_quote_with_zero_quantity_rejected():
    """
    Bug: User could create quote with 0 quantity
    Issue: ISSUE-123
    Fixed: 2025-11-24
    """
    response = client.post("/api/v1/quotes", json={
        "stl_file_id": 1,
        "material": "PLA",
        "quantity": 0,  # Invalid!
        "infill": 20
    })

    assert response.status_code == 422
    assert "quantity must be at least 1" in response.json()["detail"]
```

---

## 🚀 Pre-Launch Testing Checklist

### **Before Going Live:**

**Security Testing:**
- [ ] SQL injection tests (automated with sqlmap)
- [ ] XSS tests (automated with OWASP ZAP)
- [ ] CSRF protection verified
- [ ] Rate limiting tested
- [ ] File upload security (malicious files rejected)
- [ ] Authentication bypass attempts tested

**Load Testing:**
- [ ] 100 concurrent users (Apache Bench)
- [ ] 1000 quotes generated in 1 hour
- [ ] Large STL files (100MB) upload without timeout
- [ ] Database connection pool stress tested
- [ ] Payment processing under load

**Accuracy Testing:**
- [ ] 50 test quotes compared to actual prints
- [ ] Quote accuracy within 10% variance
- [ ] Material cost calculations verified
- [ ] Print time estimates validated

**Integration Testing:**
- [ ] Bambu Suite API integration (all endpoints)
- [ ] Stripe webhooks (test mode)
- [ ] Email delivery (test emails sent)
- [ ] Database transactions (rollback on errors)

**Browser Testing:**
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Mobile Safari (iOS)
- [ ] Mobile Chrome (Android)

**Manual QA:**
- [ ] Complete user flow (10 test orders)
- [ ] Edge cases (large orders, unusual materials)
- [ ] Error messages are user-friendly
- [ ] Loading states displayed correctly
- [ ] Forms validate properly

---

## 📞 Monitoring & Alerting (Post-Launch)

### **Production Monitoring:**

```python
# app/middleware/monitoring.py

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    """Monitor all requests and alert on errors"""

    start_time = time.time()

    try:
        response = await call_next(request)

        # Log slow requests
        duration = time.time() - start_time
        if duration > 3.0:  # 3 seconds
            logger.warning(f"Slow request: {request.url.path} took {duration:.2f}s")

        # Alert on 5xx errors
        if response.status_code >= 500:
            send_alert(f"500 error on {request.url.path}", severity="high")

        return response

    except Exception as e:
        # Alert on uncaught exceptions
        send_alert(f"Uncaught exception: {str(e)}", severity="critical")
        raise
```

### **Key Metrics to Track:**
- Quote generation success rate (target: >95%)
- Payment success rate (target: >98%)
- Average quote time (target: <5 seconds)
- API error rate (target: <1%)
- Customer conversion rate (quotes → orders)

---

## 🎓 Testing Best Practices

1. **Write tests first** (TDD approach)
2. **Test one thing per test** (easy to debug)
3. **Use descriptive test names** (explains what's being tested)
4. **Test error cases** (not just happy paths)
5. **Mock external services** (Bambu Suite, Stripe)
6. **Use fixtures** (reusable test data)
7. **Run tests locally** (before pushing)
8. **Review test coverage** (aim for 90%+)

---

**Testing is not optional. It's what separates a hobby project from production software.** 🎯

**Next Step:** Set up pytest and write first auth tests!
