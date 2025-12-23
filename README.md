# FilaOps - 3D Print Farm ERP

> The ERP that understands additive manufacturing—built by a print farm, for print farms.

[![License: BSL 1.1](https://img.shields.io/badge/License-BSL%201.1-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Discord](https://img.shields.io/badge/Discord-Join%20Server-5865F2.svg?logo=discord&logoColor=white)](https://discord.gg/FAhxySnRwa)

---

## Why FilaOps?

Most ERP systems are built for traditional manufacturing. They don't understand filament spools, print times, multi-material jobs, or why you need to track which roll went into which print.

FilaOps was built by someone who runs a print farm and got tired of spreadsheets and generic software that didn't fit.

**What makes it different:**
- **3D printing native** - BOMs that understand filament, print times, and material costs
- **Actually usable** - Simple PostgreSQL setup, dark theme UI, no enterprise sales calls required
- **Self-hosted & open** - Your data stays yours. No cloud dependency, no vendor lock-in
- **Production-grade** - Serial/lot traceability ready for medical device and aerospace compliance

---

## Quick Start

Choose your platform for step-by-step setup instructions:

- **[Windows Setup Guide](FilaOps_Zero-to-Running_Windows.md)** - Complete Windows installation guide
- **[macOS/Linux Setup Guide](FilaOps_Zero-to-Running_macOS_Linux_SSH.md)** - Complete macOS, Linux, and SSH setup guide

**Prerequisites:** Python 3.11+, PostgreSQL 16+, Node.js 18+

After setup, open http://localhost:5173 — the **Setup Wizard** will guide you through creating your admin account.

📖 **[Getting Started Guide](GETTING_STARTED.md)** for detailed instructions and troubleshooting.

---

## What's Included

### Core ERP (Free, Self-Hosted)

| Module | What It Does |
|--------|--------------|
| **Products & Items** | Unified catalog for finished goods, components, filament, hardware |
| **Bill of Materials** | Multi-level BOMs with material costs and unit tracking |
| **Inventory** | Stock levels, FIFO tracking, low stock alerts |
| **Sales Orders** | Order management with status tracking |
| **Production Orders** | Manufacturing workflow from order to ship |
| **Scrap & Remake** | Track print failures with configurable reasons, partial scrap, auto-remake orders |
| **MRP** | Material requirements planning with shortage detection |
| **Traceability** | Serial numbers, lot tracking, forward/backward recall queries |
| **Multi-User** | Team access with user accounts |
| **REST API** | Full API for integrations and automation |

### Admin Dashboard
- Dark theme (your eyes will thank you at 2am)
- Real-time KPIs: overdue orders, low stock, revenue
- Order Command Center with MRP explosion

---

## Feature Comparison

The core ERP is fully functional and free to self-host. Pro and Enterprise tiers add integrations and advanced features for larger operations.

| | Community | Pro | Enterprise |
|---|:---:|:---:|:---:|
| **Core ERP** | ✅ | ✅ | ✅ |
| Products, BOMs, Inventory | ✅ | ✅ | ✅ |
| Sales & Production Orders | ✅ | ✅ | ✅ |
| MRP & Shortage Detection | ✅ | ✅ | ✅ |
| Serial/Lot Traceability | ✅ | ✅ | ✅ |
| Multi-User | ✅ | ✅ | ✅ |
| REST API | ✅ | ✅ | ✅ |
| | | | |
| **Integrations** | | | |
| Customer Quote Portal | — | ✅ | ✅ |
| Multi-Material/AMS Quoting | — | ✅ | ✅ |
| Squarespace Sync | — | ✅ | ✅ |
| QuickBooks Integration | — | ✅ | ✅ |
| | | | |
| **Advanced** | | | |
| Advanced Role Permissions | — | ✅ | ✅ |
| User Activity Audit Logs | — | ✅ | ✅ |
| ML Print Time Estimation | — | — | ✅ |
| Printer Fleet Management | — | — | ✅ |
| SSO / LDAP | — | ✅ | ✅ |
| Priority Support | — | — | ✅ |

**Pro & Enterprise launching 2026** — [Join the waitlist](mailto:info@blb3dprinting.com)

---

## ⚙️ Build Configuration (Community Edition)

The community version uses **development mode builds** for the frontend to maximize debuggability and contributor experience:

- ✅ **Unminified code** - Easy to debug and understand
- ✅ **Source maps included** - Full stack traces with real line numbers
- ✅ **Readable variable names** - Contributing PRs is easier
- ✅ **Instant hot reload** - Changes appear immediately (no Docker rebuilds)
- ⚠️ **Larger bundle size** (~2MB vs ~1MB minified)

**This is intentional for self-hosted deployments** where source code is already visible and performance impact is negligible on local networks.

> 📝 **For SaaS/Production hosting:** Production builds require refactoring ~30 components to fix React hook timing issues. See `frontend/PRODUCTION_BUILD_BLOCKED.md` for details. This only affects public-facing deployments; self-hosted users are unaffected.

## 🆕 Recent Improvements

### PostgreSQL-Only Architecture
- **Simplified setup** - No Docker required, direct PostgreSQL connection
- **Faster performance** - Native database drivers, no container overhead
- **Easier debugging** - Direct access to database tools
- **Better reliability** - Fewer moving parts

### Enhanced Production Scheduling
- **Gantt chart interface** - Visual timeline for production orders
- **Drag & drop scheduling** - Easily reschedule orders
- **Resource management** - Assign orders to specific machines
- **Auto-arrange** - Optimize schedule layout automatically

### Frontend Enhancements
- **Better error handling** - More informative error messages
- **Centralized API client** - Automatic retry and error recovery
- **Improved components** - Enhanced scheduling, scrap, and update modals
- **Instant hot reload** - See changes immediately during development

See **[ANNOUNCEMENT_POSTGRES_MIGRATION.md](ANNOUNCEMENT_POSTGRES_MIGRATION.md)** for complete details.

---

## Documentation

| | |
|---|---|
| **[HOW_IT_WORKS.md](HOW_IT_WORKS.md)** | System overview and workflows |
| **[docs/EMAIL_CONFIGURATION.md](docs/EMAIL_CONFIGURATION.md)** | Email/SMTP setup guide |
| **[KNOWN_ISSUES.md](KNOWN_ISSUES.md)** | Known issues and workarounds |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Common issues and fixes |
| **[FAQ.md](FAQ.md)** | Frequently asked questions |
| **[CONTRIBUTING.md](CONTRIBUTING.md)** | For contributors |
| **[docs/](docs/)** | Full documentation (architecture, API, planning) |

---

## For Developers

### Local Development Setup

**Prerequisites:** Python 3.11+, Node.js 18+, PostgreSQL 16+

```bash
# Backend
cd backend
pip install -r requirements.txt
# Create .env file with PostgreSQL connection details
python -m uvicorn app.main:app --reload --port 8001

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

- API docs: http://localhost:8001/docs
- Admin UI: http://localhost:5173

See **[FilaOps_Zero-to-Running_Windows.md](FilaOps_Zero-to-Running_Windows.md)** or **[FilaOps_Zero-to-Running_macOS_Linux_SSH.md](FilaOps_Zero-to-Running_macOS_Linux_SSH.md)** for complete setup instructions.

### Project Structure

```
filaops/
├── backend/           # FastAPI API
│   ├── app/
│   │   ├── api/       # REST endpoints
│   │   ├── models/    # SQLAlchemy ORM
│   │   ├── services/  # Business logic (MRP, etc)
│   │   └── core/      # Config, security
│   └── tests/
├── frontend/          # React admin UI
└── docs/              # Documentation
```

### Contributing

We welcome contributions. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Good first issues:**
- Bug fixes
- Documentation improvements  
- UI/UX polish
- Test coverage

---

## License

**Business Source License 1.1** — see [LICENSE](LICENSE)

- ✅ Free for internal business use
- ✅ Free for personal and educational use  
- ❌ Cannot offer FilaOps as a hosted service to others
- 🔓 Converts to Apache 2.0 after 4 years

---

## Support

- **[Discord](https://discord.gg/FAhxySnRwa)** — Chat with the community
- **[GitHub Issues](https://github.com/Blb3D/filaops/issues)** — Bug reports
- **[GitHub Discussions](https://github.com/Blb3D/filaops/discussions)** — Questions and ideas
- **Email:** info@blb3dprinting.com

---

Built by [BLB3D](https://blb3dprinting.com) — a print farm that needed real manufacturing software.
