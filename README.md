# FilaOps - 3D Print Farm ERP

> Open source manufacturing resource planning for 3D print operations

[![License: BSL](https://img.shields.io/badge/License-BSL%201.1-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)

FilaOps is an open source ERP system built for 3D print farms. Manage products, inventory, BOMs, orders, and production - designed by someone who actually runs a print farm.

---

## What You Get

### Core ERP (Fully Functional)
- **Product Catalog** - SKUs, variants, material-aware costing
- **Bill of Materials** - Multi-level BOMs with filament and hardware components
- **Inventory Management** - Stock levels, low stock alerts, FIFO tracking
- **Sales Orders** - Order management with status tracking
- **Production Orders** - Manufacturing workflow with operation tracking
- **MRP** - Material requirements planning

### Manufacturing
- **Work Centers** - Machine pools and capacity planning
- **Routings** - Operation sequences with time standards
- **Traceability** - Serial numbers, lot tracking, recall queries (FDA/ISO ready)

### Admin Dashboard
- Full React-based admin UI included
- Manage products, BOMs, inventory, orders, production, shipping
- Works out of the box with the backend API

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- SQL Server Express (or SQL Server)
- ODBC Driver 17 for SQL Server

### Backend Setup
```bash
git clone https://github.com/Blb3D/filaops.git
cd filaops/backend

python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your database credentials

python -m uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend Setup
```bash
cd filaops/frontend

npm install
npm run dev
```

Admin UI: http://localhost:5173

### Database Setup

Run the schema script in SQL Server Management Studio:
```
scripts/setup_database.sql
```

---

## Configuration

Create `backend/.env`:
```env
# Database
DB_HOST=localhost\SQLEXPRESS
DB_NAME=FilaOps
DB_TRUSTED_CONNECTION=true

# Security
SECRET_KEY=your-secure-secret-key
```

---

## Project Structure
```
filaops/
+-- backend/
¦   +-- app/
¦   ¦   +-- api/v1/endpoints/   # REST API routes
¦   ¦   +-- models/             # SQLAlchemy ORM models
¦   ¦   +-- schemas/            # Pydantic schemas
¦   ¦   +-- services/           # Business logic
¦   ¦   +-- core/               # Config, security
¦   +-- requirements.txt
+-- frontend/                   # React admin UI
+-- mock-api/                   # Mock quote server (for contributors)
+-- scripts/                    # Database setup scripts
+-- docs/
```

---

## Mock API (For Contributors)

The `/mock-api` folder contains a mock quote server for UI development:
- Parses real 3MF files
- Returns fake quotes with realistic structure
- Lets contributors improve the quote portal UI without access to proprietary pricing

**This is for UI development only** - not for quoting real customers.
```bash
cd mock-api
npm install
node server.js
# Runs on http://localhost:3001
```

See [mock-api/README.md](mock-api/README.md) for details.

---

## API Overview

### Products & Inventory
```
GET    /api/v1/products           # List products
POST   /api/v1/products           # Create product
GET    /api/v1/inventory          # Current stock levels
POST   /api/v1/inventory/adjust   # Adjust inventory
```

### Orders
```
GET    /api/v1/sales-orders       # List sales orders
POST   /api/v1/sales-orders       # Create sales order
PATCH  /api/v1/sales-orders/{id}  # Update order status
```

### Production
```
GET    /api/v1/production-orders  # List production orders
POST   /api/v1/production-orders  # Create production order
POST   /api/v1/production-orders/{id}/start
POST   /api/v1/production-orders/{id}/complete
```

### Traceability
```
GET    /api/v1/admin/traceability/lots
GET    /api/v1/admin/traceability/serials
GET    /api/v1/admin/traceability/recall/forward/{lot}
GET    /api/v1/admin/traceability/recall/backward/{sn}
```

Full API docs at `/docs` when running.

---

## FilaOps Pro (Coming 2026)

| Feature | Open Source | Pro | Enterprise |
|---------|:-----------:|:---:|:----------:|
| Products, BOMs, Inventory | ? | ? | ? |
| Sales & Production Orders | ? | ? | ? |
| Work Centers & Routing | ? | ? | ? |
| Serial/Lot Traceability | ? | ? | ? |
| MRP | ? | ? | ? |
| Admin Dashboard UI | ? | ? | ? |
| REST API | ? | ? | ? |
| Mock Quote API | ? | - | - |
| Customer Quote Portal | - | ? | ? |
| Multi-Material Quoting | - | ? | ? |
| E-commerce Integrations | - | ? | ? |
| Payment Processing | - | ? | ? |
| Shipping Integrations | - | ? | ? |
| Accounting Integrations | - | ? | ? |
| Printer Fleet Management | - | - | ? |
| Live Production Monitoring | - | - | ? |
| ML Print Time Estimation | - | - | ? |

Questions? [Contact us](mailto:hello@blb3dprinting.com) or open a [Discussion](https://github.com/Blb3D/filaops/discussions).

---

## Contributing

Contributions welcome! This is the core ERP - help us make the foundation solid.

---

## License

Business Source License 1.1 - see [LICENSE](LICENSE).

Converts to Apache 2.0 after 4 years.

---

## Support

- [GitHub Issues](https://github.com/Blb3D/filaops/issues)
- [GitHub Discussions](https://github.com/Blb3D/filaops/discussions)

---

Built by [BLB3D](https://blb3dprinting.com) - a print farm that needed real manufacturing software.
