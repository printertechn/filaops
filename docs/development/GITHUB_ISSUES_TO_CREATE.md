# GitHub Issues to Create

Copy-paste these into GitHub Issues. Issues #1 and #2 can be created and immediately closed since the work is done.

---

## Issue 1: Database Migrations with Alembic ✅ DONE

**Title:** `[Infra] Set up Alembic database migrations`

**Labels:** `infrastructure`, `core-release`

**Body:**
```markdown
## Summary
Set up Alembic for database schema migrations to enable safe, versioned database changes.

## Why This Matters
- Currently using `Base.metadata.create_all()` which doesn't handle schema changes
- Need migration tracking for production deployments
- Contributors need a standard way to modify the database schema

## Acceptance Criteria
- [x] Alembic installed and configured
- [x] `migrations/` directory with env.py configured for FilaOps models
- [x] Baseline migration stamped for existing database
- [x] Documentation for creating new migrations

## Implementation Notes
Completed Dec 9, 2025:
- `backend/alembic.ini` - Configuration
- `backend/migrations/env.py` - Configured with settings.database_url and Base.metadata
- `backend/migrations/versions/baseline_001_stamp_existing.py` - Baseline stamp
- Added `alembic==1.17.2` to requirements.txt

### Usage
```bash
cd backend

# Create new migration after model changes
alembic revision --autogenerate -m "add_field_to_table"

# Apply migrations
alembic upgrade head

# Check current state
alembic current
```
```

---

## Issue 2: CI/CD Pipeline ✅ DONE

**Title:** `[Infra] Set up GitHub Actions CI/CD pipeline`

**Labels:** `infrastructure`, `core-release`

**Body:**
```markdown
## Summary
Create automated CI/CD pipeline for testing and quality checks on every push/PR.

## Why This Matters
- No automated testing before merge
- Manual verification is error-prone
- Contributors need immediate feedback on their changes

## Acceptance Criteria
- [x] Backend tests run on push/PR
- [x] Backend linting (ruff)
- [x] Frontend build verification
- [x] Docker build verification
- [x] Uses SQLite for CI (no SQL Server dependency)

## Implementation Notes
Completed Dec 9, 2025:
- `.github/workflows/ci.yml` created

### Jobs
1. **backend-tests** - pytest with coverage, SQLite in-memory
2. **backend-lint** - ruff check
3. **frontend-tests** - npm build verification
4. **docker-build** - Dockerfile build test

### Triggers
- Push to `main` or `develop`
- Pull requests to `main`
```

---

## Issue 3: Fix Hardcoded API_URL in Frontend ✅ COMPLETED

**Title:** `[Chore] Fix hardcoded localhost:8000 API URLs in frontend`

**Labels:** `good first issue`, `frontend`, `core-release`

**Body:**
```markdown
## Summary
Replace hardcoded `localhost:8000` API URLs with centralized configuration import across ~20 frontend files.

## Problem
Many frontend components define their own API_URL:
```javascript
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
```

This causes issues:
- IPv6/IPv4 resolution problems on some systems
- Inconsistent behavior across components
- Harder to configure for different environments

## Solution
Import from the existing centralized config:
```javascript
import { API_URL } from "../../config/api";
```

## Files to Update (~20 files)

### Components
- [ ] `frontend/src/components/bom/BOMEditor.jsx`
- [ ] `frontend/src/components/items/ItemForm.jsx`
- [ ] `frontend/src/components/items/ItemWizard.jsx`
- [ ] `frontend/src/components/materials/MaterialForm.jsx`
- [ ] `frontend/src/components/production/ProductionScheduler.jsx`
- [ ] `frontend/src/components/production/ProductionSchedulingModal.jsx`
- [ ] `frontend/src/components/routing/RoutingEditor.jsx`
- [ ] `frontend/src/components/sales/SalesOrderWizard.jsx`

### Pages
- [ ] `frontend/src/pages/admin/AdminBOM.jsx`
- [ ] `frontend/src/pages/admin/AdminCustomers.jsx`
- [ ] `frontend/src/pages/admin/AdminDashboard.jsx` ✅ (already fixed)
- [ ] `frontend/src/pages/admin/AdminItems.jsx`
- [ ] `frontend/src/pages/admin/AdminLogin.jsx`
- [ ] `frontend/src/pages/admin/AdminManufacturing.jsx`
- [ ] `frontend/src/pages/admin/AdminOrderImport.jsx`
- [ ] `frontend/src/pages/admin/AdminOrders.jsx`
- [ ] `frontend/src/pages/admin/AdminPasswordResetApproval.jsx`
- [ ] `frontend/src/pages/admin/AdminProduction.jsx`
- [ ] `frontend/src/pages/admin/AdminPurchasing.jsx`
- [ ] `frontend/src/pages/admin/AdminShipping.jsx`

## How to Fix Each File

1. Remove the local API_URL definition:
```diff
- const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
```

2. Add import at top of file:
```diff
+ import { API_URL } from "../../config/api";  // adjust path as needed
```

3. Verify the import path is correct relative to the file location

## Verification
```bash
# Find any remaining hardcoded URLs
grep -r "localhost:8000" frontend/src/ --include="*.jsx"
# Should return empty after fix
```

## Good First Issue
This is a straightforward find-and-replace task, perfect for new contributors!
```

---

## Issue 4: Add Rate Limiting to Auth Endpoints ✅ COMPLETED

**Title:** `[Security] Add rate limiting to authentication endpoints`

**Labels:** `security`, `core-release`

**Body:**
```markdown
## Summary
Add rate limiting to `/api/v1/auth/login` and related endpoints to prevent brute force attacks.

## Problem
Currently, there's no limit on authentication attempts. An attacker could:
- Brute force passwords
- Cause denial of service through repeated requests
- Enumerate valid usernames

## Solution
Use `slowapi` to add rate limiting:

```bash
pip install slowapi
```

```python
# backend/app/api/v1/endpoints/auth.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")  # 5 attempts per minute per IP
async def login(request: Request, ...):
    ...
```

## Acceptance Criteria
- [x] Install `slowapi` and add to requirements.txt
- [x] Rate limit `/api/v1/auth/login` to 5 requests/minute per IP
- [x] Rate limit `/api/v1/auth/register` to 3 requests/minute per IP
- [x] Rate limit `/api/v1/auth/forgot-password` to 3 requests/minute per IP
- [x] Return appropriate 429 response with retry-after header
- [ ] Add tests for rate limiting behavior (future enhancement)

## References
- [slowapi documentation](https://slowapi.readthedocs.io/)
- OWASP Authentication Cheat Sheet
```

---

## Issue 5: Remove Personal Address from Settings ✅ COMPLETED

**Title:** `[Security] Remove personal address from default settings`

**Labels:** `security`, `good first issue`, `core-release`

**Body:**
```markdown
## Summary
Replace personal/business address in `backend/app/core/settings.py` with generic placeholder values.

## Problem
The settings file contains a real business address as default values for ship-from configuration. This should be replaced with placeholder values for the open-source release.

## File
`backend/app/core/settings.py`

## Current (Remove)
```python
SHIP_FROM_NAME: str = Field(default="BLB3D Printing")
SHIP_FROM_STREET1: str = Field(default="[REAL ADDRESS]")
SHIP_FROM_CITY: str = Field(default="[REAL CITY]")
# etc.
```

## Replace With
```python
SHIP_FROM_NAME: str = Field(default="Your Company Name")
SHIP_FROM_STREET1: str = Field(default="123 Main Street")
SHIP_FROM_CITY: str = Field(default="Your City")
SHIP_FROM_STATE: str = Field(default="ST")
SHIP_FROM_ZIP: str = Field(default="12345")
SHIP_FROM_COUNTRY: str = Field(default="US")
SHIP_FROM_PHONE: str = Field(default="555-555-5555")
```

## Acceptance Criteria
- [x] All default address values replaced with placeholders
- [x] Add comment noting these must be configured via environment variables
- [ ] Update `.env.example` with the required variables (future enhancement)

## Good First Issue
Quick 5-minute fix, perfect for first-time contributors!
```

---

---

## Issue 6: Replace print() Statements with Structured Logging ✅ COMPLETED

**Title:** `[Chore] Replace print() statements with structured logging in backend`

**Labels:** `backend`, `code-quality`, `core-release`

**Body:**
```markdown
## Summary
Replace all `print()` statements in backend code with proper structured logging using the existing `logging_config.py` system.

## Problem
Backend code uses `print()` statements for logging, which:
- Cannot be filtered by log level
- Cannot be aggregated in production systems
- Don't include timestamps, log levels, or structured context
- Make debugging production issues difficult

## Solution
Use the existing `get_logger()` function from `app.logging_config`:
```python
from app.logging_config import get_logger

logger = get_logger(__name__)

# Replace print() with appropriate log level
logger.info("Customer created successfully")
logger.error("Failed to process order")
```

## Files Updated
- `backend/app/api/v1/endpoints/auth.py` - Login, registration, password reset
- `backend/app/api/v1/endpoints/admin/customers.py` - Customer CRUD operations
- `backend/app/api/v1/endpoints/admin/bom.py` - BOM operations
- `backend/app/api/v1/endpoints/sales_orders.py` - Production order creation
- `backend/app/services/quote_conversion_service.py` - Quote conversion
- `backend/app/core/pricing_config.py` - Pricing calculations

## Acceptance Criteria
- [x] All `print()` statements replaced with `logger.info()`, `logger.error()`, etc.
- [x] Appropriate log levels used (info, error, warning, debug)
- [x] Logging includes relevant context (IDs, operation names)
- [x] No `print()` statements remain in production code paths

## Implementation Notes
Completed December 2025:
- Replaced ~15+ print() statements across 6 files
- Used structured logging with proper log levels
- Maintained existing logging configuration system
```

---

## Issue 7: Clean Up Commented-Out Code Blocks ✅ COMPLETED

**Title:** `[Chore] Remove commented-out code blocks`

**Labels:** `code-quality`, `good first issue`, `core-release`

**Body:**
```markdown
## Summary
Remove large blocks of commented-out code that are no longer needed, especially in `backend/app/api/v1/endpoints/admin/fulfillment.py`.

## Problem
Codebase contains large sections of commented-out code that:
- Clutters the codebase
- Makes it harder to understand active code
- May contain outdated logic that confuses contributors
- Increases maintenance burden

## Files Cleaned
- `backend/app/api/v1/endpoints/admin/fulfillment.py` - Removed large commented-out blocks

## Acceptance Criteria
- [x] Commented-out code blocks removed
- [x] Active code remains unchanged
- [x] No functional changes

## Implementation Notes
Completed December 2025:
- Removed commented-out code in fulfillment.py
- Preserved all active functionality
```

---

## Issue 8: Convert console.error to Proper Error Handling ✅ COMPLETED

**Title:** `[Chore] Convert console.error to proper error handling in frontend`

**Labels:** `frontend`, `code-quality`, `core-release`

**Body:**
```markdown
## Summary
Replace all `console.error()` statements in frontend React components with proper user-facing error handling using error state or alerts.

## Problem
Frontend code uses `console.error()` for error handling, which:
- Errors are invisible to users
- No user feedback when operations fail
- Makes debugging user-reported issues difficult
- Poor user experience

## Solution
Replace with appropriate error handling:
1. **Components with error state**: Use `setError()` to display errors in UI
2. **Critical operations**: Show `alert()` for immediate user feedback
3. **Non-critical failures**: Add comments explaining why they're handled silently

## Files Updated (~25 files)

### Admin Pages
- `frontend/src/pages/admin/AdminBOM.jsx` - BOM operations, cost rollup, routing
- `frontend/src/pages/admin/AdminPurchasing.jsx` - Products, low stock, PO details
- `frontend/src/pages/admin/AdminShipping.jsx` - Production status, order updates
- `frontend/src/pages/admin/AdminManufacturing.jsx` - Products, resources
- `frontend/src/pages/admin/AdminProduction.jsx` - Products, status updates
- `frontend/src/pages/admin/AdminOrders.jsx` - Order status updates
- `frontend/src/pages/admin/AdminCustomers.jsx` - Orders, session storage
- `frontend/src/pages/admin/AdminItems.jsx` - Categories
- `frontend/src/pages/admin/OrderDetail.jsx` - Order fetch, BOM explosion
- `frontend/src/pages/admin/AdminAnalytics.jsx` - Analytics fetch
- `frontend/src/pages/admin/AdminLicense.jsx` - License info fetch
- `frontend/src/pages/admin/AdminInventoryTransactions.jsx` - Products, locations
- `frontend/src/pages/admin/AdminLogin.jsx` - Setup check

### Components
- `frontend/src/components/BOMEditor.jsx` - BOM fetch, components, materials
- `frontend/src/components/RoutingEditor.jsx` - Routing fetch, work centers, templates
- `frontend/src/components/MaterialForm.jsx` - Material types, colors
- `frontend/src/components/ItemWizard.jsx` - Categories, components, work centers, templates, materials
- `frontend/src/components/SalesOrderWizard.jsx` - Customers, products, categories, components, work centers, templates, materials
- `frontend/src/components/ProductionScheduler.jsx` - Resource fetch warnings
- `frontend/src/components/ProductionSchedulingModal.jsx` - Work centers, resources
- `frontend/src/components/ExportImport.jsx` - Export failures
- `frontend/src/components/ItemForm.jsx` - Categories (non-critical)

### Pages
- `frontend/src/pages/Onboarding.jsx` - Removed debug console.log statements
- `frontend/src/pages/admin/AdminMaterialImport.jsx` - Removed debug console.log statements

### Hooks
- `frontend/src/hooks/useFeatureFlags.js` - Tier fetch failures

## Error Handling Strategy
1. **User-facing errors**: Show alerts or set error state for critical operations
2. **Non-critical failures**: Add comments explaining why they're handled silently (e.g., dropdown data fetch failures)
3. **Debug logs**: Removed unnecessary console.log statements from import operations

## Acceptance Criteria
- [x] All `console.error()` replaced with proper error handling
- [x] User-facing errors show appropriate messages (alerts or error state)
- [x] Non-critical failures documented with comments
- [x] Debug `console.log()` statements removed
- [x] No `console.error()` or `console.warn()` remain in production code

## Implementation Notes
Completed December 2025:
- Replaced ~50+ console.error/warn/log statements
- Added user-facing error messages for critical operations
- Documented non-critical failures with comments
- Improved user experience with proper error feedback
```

---

## Summary

| Issue | Status | GitHub Issue # | Action |
|-------|--------|----------------|--------|
| Alembic migrations | ✅ Done | #31 (exists) | Already exists - update with completion comment & close |
| CI/CD pipeline | ✅ Done | Unknown | Run `scripts/check-duplicate-issues.ps1` first |
| API_URL hardcoding | ✅ Completed | Unknown | Run `scripts/check-duplicate-issues.ps1` first |
| Rate limiting | ✅ Completed | #33 (exists) | ✅ Already updated with completion comment |
| Personal address | ✅ Completed | #34 (exists) | ✅ Already updated with completion comment |
| Structured logging | ✅ Completed | #35 (exists) | Update with completion comment using `scripts/update-remaining-issues.ps1` |
| Commented code cleanup | ✅ Completed | #36 (exists) | Update with completion comment using `scripts/update-remaining-issues.ps1` |
| Frontend error handling | ✅ Completed | #37 (exists) | Update with completion comment using `scripts/update-remaining-issues.ps1` |

## Notes
- Issues #33 and #34 already exist and have been updated with completion comments
- Issue #31 exists for Alembic migrations - should add completion comment and close
- Always check for duplicates before creating new issues using `scripts/check-duplicate-issues.ps1`
