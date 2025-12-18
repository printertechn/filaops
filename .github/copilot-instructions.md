# FilaOps - AI Coding Agent Instructions

## Project Overview

FilaOps is a **3D printing ERP system** built for print farm operations. Core stack:

- **Backend**: FastAPI + SQLAlchemy (SQL Server/SQL Server Express)
- **Frontend**: React + Vite + Tailwind CSS (⚠️ **DEVELOPMENT MODE ONLY** - production builds disabled)
- **Deployment**: Docker Compose (dev and production environments run simultaneously)

## ⚠️ CRITICAL: Frontend Production Builds DISABLED

**DO NOT enable production builds.** The frontend uses `vite build --mode development` (unminified) due to widespread temporal dead zone errors. See `.ai-instructions/NO_PRODUCTION_BUILDS.md` for details.

- ✅ Use: `npm run build` (development mode)
- ❌ Never: `npm run build:prod` (blocked)
- ❌ Never: `vite build` directly

## Critical Architecture Patterns

### Database: SQL Server Quirks

**Always use `== True` for boolean filters** (not `.is_(True)`):

```python
# CORRECT - SQL Server requires this
.filter(Model.active == True)  # noqa: E712

# WRONG - generates invalid SQL on SQL Server
.filter(Model.active.is_(True))
```

**Database sessions**: Use dependency injection via `get_db()` from `app.db.session`:

```python
from app.db.session import get_db

@router.get("/items")
def get_items(db: Session = Depends(get_db)):
    return db.query(Item).all()
```

### Multi-Environment Setup

Development and production **coexist** via separate Docker networks:

|                | **Development**          | **Production**       |
| -------------- | ------------------------ | -------------------- |
| Docker compose | `docker-compose.dev.yml` | `docker-compose.yml` |
| Frontend       | localhost:5174           | localhost:5173       |
| Backend        | localhost:8001           | localhost:8000       |
| Database port  | 1434                     | 1433                 |
| Volumes        | `filaops-dev-*`          | `filaops-*`          |

**Always use** `-f docker-compose.dev.yml` when working in this repo:

```bash
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml logs -f backend
```

### API Structure

**Backend routing** (`app/api/v1/__init__.py`):

- All routes registered in `/api/v1/`
- Business logic lives in `app/services/` (e.g., `MRPService`, `ShippingService`)
- Models in `app/models/` extend SQLAlchemy `Base`
- Schemas in `app/schemas/` (Pydantic for validation)

**Frontend API calls** (`frontend/src/config/api.js`):

```javascript
import { API_URL } from "../config/api";
const response = await fetch(`${API_URL}/api/v1/products`);
```

Use `127.0.0.1` not `localhost` to avoid IPv6/IPv4 issues.

## Development Workflow

### Before Pushing Code

1. **Run tests**: `cd backend && pytest tests/ -v`
2. **Lint**: `cd backend && ruff check .`
3. **Commit format**:

   ```
   feat: Add multi-material quoting

   Implements AMS detection for quote generation.

   Fixes #123
   ```

### Testing

- **Unit tests**: `backend/tests/unit/` (business logic, e.g., MRP explosion)
- **Integration tests**: `backend/tests/integration/` (API endpoints)
- **E2E tests**: `frontend/e2e/` (Playwright)
- Tests use **in-memory SQLite** (no SQL Server required for CI)

Run specific test suites:

```bash
pytest tests/unit/test_mrp_service.py -v
npx playwright test --grep orders
```

## ERP Domain Knowledge

### Core Data Flow

```
Sales Order → Production Order → MRP Explosion → Material Requirements
     ↓              ↓                  ↓                    ↓
Customer      Work Centers         BOM Tree           Purchase Orders
```

**Key entities** (see `backend/app/models/`):

- `Product` - Everything is a product (finished goods, filament, components)
- `BOM` - Multi-level bills of materials (supports nested assemblies)
- `ProductionOrder` - Manufacturing jobs with operations/routings
- `SalesOrder` - Customer orders
- `InventoryTransaction` - Source of truth for stock movements

### MRP (Material Requirements Planning)

**MRP Service** (`app/services/mrp.py`):

1. Explodes BOMs recursively
2. Calculates net requirements (demand - inventory)
3. Generates planned orders (purchase or production)
4. Respects lead times, minimum order quantities

**Watch for**:

- Circular BOM references (detected and prevented)
- Multi-level aggregation (components used in multiple products)
- FIFO inventory consumption

### Order Status Workflow (Two-Tier Model)

**CRITICAL**: Sales Orders and Production Orders have separate status lifecycles.

**Sales Order statuses** (customer-facing):

- `draft` → `pending_payment` → `confirmed` → `in_production` → `ready_to_ship` → `shipped` → `delivered` → `completed`
- `fulfillment_status` field tracks shipping logistics: `pending` → `ready` → `picking` → `packing` → `shipped`
- Don't mark SO as "shipped" until all items physically ship

**Production Order statuses** (manufacturing):

- `draft` → `released` → `scheduled` → `in_progress` → `completed` → `closed`
- QC workflow: `completed` → `qc_hold` → (`scrapped` | rework to `in_progress` | `closed`)
- Scrap triggers auto-remake via `order_status_service.scrap_wo_and_create_remake()`

**Always use OrderStatusService for status changes**:

```python
from app.services.order_status import order_status_service

# Validates transitions (throws ValueError if invalid)
order_status_service.update_so_status(db, so, "confirmed")
order_status_service.update_wo_status(db, wo, "in_progress")

# Auto-updates SO when WOs complete
order_status_service.auto_update_so_from_wos(db, so)
```

See [docs/ORDER_STATUS_WORKFLOW.md](docs/ORDER_STATUS_WORKFLOW.md) for complete workflow guide.

### 3D Printing-Specific Logic

**Filament tracking**:

- Measured in grams (not typical inventory units)
- Multi-material support via `QuoteMaterial` table
- AMS (Automatic Material System) detection in quote generation

**Print jobs** link to Bambu Lab printer fleet (optional Pro feature).

## UI Patterns

### Styling (Tailwind)

**Dark theme consistently**:

```jsx
<div className="bg-gray-900 text-white border border-gray-700">
  <button className="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded">
```

**Tables**:

```jsx
<table className="w-full border-collapse">
  <thead className="bg-gray-800">
    <tr className="border-b border-gray-700">
```

### Component Organization

- **Pages**: `frontend/src/pages/admin/` (e.g., `AdminOrders.jsx`, `AdminBOM.jsx`)
- **Reusable components**: `frontend/src/components/`
- **State**: React hooks (no Redux/Zustand - keep it simple)

## Key Files Reference

| File                          | Purpose                                               |
| ----------------------------- | ----------------------------------------------------- |
| `backend/app/main.py`         | FastAPI app entry, middleware, startup hooks          |
| `backend/app/services/mrp.py` | BOM explosion, shortage calculation                   |
| `backend/database.py`         | Legacy DB setup (use `app/db/session.py` instead)     |
| `frontend/src/App.jsx`        | React Router configuration                            |
| `docker-compose.dev.yml`      | **Development environment** (ALWAYS use this)         |
| `HOW_IT_WORKS.md`             | ERP concepts explained (BOMs, routings, traceability) |

## Common Pitfalls

1. **Don't use bare `docker-compose`** in dev - always `-f docker-compose.dev.yml`
2. **SQL Server booleans**: `== True` not `.is_(True)`
3. **API URL changes**: Requires frontend rebuild (`docker-compose build --no-cache frontend`)
4. **Type hints**: Required on all functions (enforced by mypy)
5. **First-run setup**: App auto-detects no users and shows `/setup` wizard (don't hardcode admin creation)

## Security Notes

- JWT authentication (30min access tokens, 7-day refresh)
- Password validation: min 8 chars, uppercase, lowercase, number, special char
- Rate limiting via SlowAPI
- CORS configured per environment (see `app/main.py`)
- **Never commit** `.env` files (use `.env.example` as template)
