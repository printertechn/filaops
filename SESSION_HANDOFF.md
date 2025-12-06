# Session Handoff - BLB3D ERP

> **AI ASSISTANTS: READ THIS FILE AT THE START OF EVERY SESSION.**
> This file captures critical context that must not be lost between sessions.
> Update this file at the END of every session with what was done and what's next.

## Last Updated

**Date:** December 5, 2025 (Session 3)
**Session Summary:** FilaOps rebrand commit, LICENSE file preparation

---

## CRITICAL BUSINESS CONTEXT

### Three Repositories Work Together

```
C:\Users\brand\OneDrive\Documents\blb3d-erp       → ERP Backend (port 8000)
C:\Users\brand\OneDrive\Documents\quote-portal    → Customer + Admin UI (port 5173)
C:\Users\brand\OneDrive\Documents\bambu-print-suite → ML Dashboard (port 8001)
```

**IMPORTANT:**

- Admin UI is at `localhost:5173/admin` (quote-portal), NOT the ML Dashboard
- ML Dashboard reads from ERP via `/api/v1/internal/*` endpoints
- All three repos need to stay in sync

### Revenue-Critical Integrations NOT YET BUILT

| Integration | Why It Matters | Status |
|-------------|----------------|--------|
| **Squarespace** | 80%+ of revenue comes from here. Orders must sync to ERP. | NOT STARTED |
| **QuickBooks** | Accounting compliance. Invoices/payments must sync. | NOT STARTED |
| **B2B Parts Portal** | Retail partners need wholesale ordering | NOT STARTED |

### Current Payment/Shipping Status

- **Stripe**: Works but in TEST MODE only
- **EasyPost**: Works but in TEST MODE only
- Need production API keys before go-live

---

## WHAT WAS COMPLETED THIS SESSION

### FilaOps Rebrand (Dec 5, 2025 - Session 3)

**Committed (a2ea41e):**
- README.md updated with professional FilaOps branding
- docs/SAAS_TIERING_PLAN.md created (tiering strategy)
- .gitignore updated (test screenshots, security patterns)
- CLAUDE.md updated with cross-repo docs

**LICENSE File:**
- User creating BSL 1.1 license separately
- Licensor: Brandan Baker DBA BLB3D Printing
- Change Date: December 5, 2029 → Apache 2.0

**Trademark Check:**
- "FilaOps" - No conflicts found (web search + USPTO)

### Previous Sessions

- Session 2: Security audit, .gitignore updates, proprietary content analysis
- Session 1: Phase 6B traceability, production order modal

---

## WHAT NEEDS TO BE DONE NEXT

### Public Repo (Before Going Live)

1. [x] **Choose repo name** - FilaOps
2. [ ] **Create LICENSE file** - BSL 1.1, user creating separately
3. [x] **Update README.md** - Done (a2ea41e)
4. [x] **Commit .gitignore updates** - Done (a2ea41e)
5. [ ] **Push to GitHub** - After LICENSE added

### Immediate (This Week)

1. [ ] **Test create production order** - Verify modal works end-to-end in quote-portal admin
2. [ ] **Add traceability UI** - Admin pages to manage lots, serials, run recall queries
3. [ ] **Squarespace integration** - Start with order webhook receiver

### Short Term

1. [ ] QuickBooks integration (OAuth2 flow, invoice sync)
2. [ ] B2B Partner Portal (pricing tiers, PO-based ordering)
3. [ ] Switch Stripe/EasyPost to production keys

### Known Issues

- 35 e2e tests skipped (conditional, need specific data states)
- Some tests reference wrong ports (fixed in latest commit)

---

## HOW TO PREVENT CONTEXT LOSS

### For the Human

1. **At session start**: Tell the AI to read `SESSION_HANDOFF.md` and `AI_CONTEXT.md`
2. **During session**: If discussing something important, ask AI to update these docs
3. **At session end**: Ask AI to update this file with what was done

### For the AI

1. **Always read** `AI_CONTEXT.md` → Integration Roadmap section
2. **Always read** this file (`SESSION_HANDOFF.md`)
3. **Update this file** at the end of every session
4. **Commit changes** before session ends to preserve work

---

## Key Files Reference

| Purpose | File Path |
|---------|-----------|
| Quick AI context | `AI_CONTEXT.md` |
| This handoff doc | `SESSION_HANDOFF.md` |
| Full architecture | `ARCHITECTURE.md` |
| Project roadmap | `ROADMAP.md` |
| ERP main entry | `backend/app/main.py` |
| Admin UI | `quote-portal/src/pages/admin/` |
| Production orders API | `backend/app/api/v1/endpoints/production_orders.py` |
| Traceability API | `backend/app/api/v1/endpoints/admin/traceability.py` |

---

## Environment Setup

```bash
# Start all services
cd blb3d-erp/backend && python -m uvicorn app.main:app --reload --port 8000
cd quote-portal && npm run dev
cd bambu-print-suite/ml-dashboard/backend && python main.py

# URLs
http://localhost:5173/admin    # Admin dashboard
http://localhost:8000/docs     # ERP API docs
http://localhost:8001/docs     # ML Dashboard docs
```
