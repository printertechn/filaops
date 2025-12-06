# FilaOps SaaS Tiering Plan

> **Status**: PLANNED - Not yet implemented
> **Date**: December 5, 2025
> **Purpose**: Document the commercial open-source strategy for future implementation

## Overview

FilaOps follows an "open core" model where the base ERP is open source (free) and premium features are paid tiers.

## Product Tiers

| Tier | Price | Target Audience | Deployment |
|------|-------|-----------------|------------|
| **Open Source** | Free | DIY print farms, hobbyists, developers | Self-hosted |
| **Pro** | $X/month | Small/medium print farms (1-10 printers) | SaaS or Self-hosted |
| **Enterprise** | $XX/month | Large operations, medical/automotive compliance | SaaS |

## Feature Matrix

| Feature | Open Source | Pro | Enterprise |
|---------|:-----------:|:---:|:----------:|
| **Core ERP** |
| Products & BOMs | Yes | Yes | Yes |
| Inventory Management | Yes | Yes | Yes |
| Sales Orders | Yes | Yes | Yes |
| Production Orders | Yes | Yes | Yes |
| Basic MRP | Yes | Yes | Yes |
| Traceability (Serial/Lot) | Yes | Yes | Yes |
| **Customer Facing** |
| Quote Portal | - | Yes | Yes |
| B2B Partner Portal | - | Yes | Yes |
| Customer Self-Service | - | Yes | Yes |
| **Integrations** |
| Squarespace Sync | - | Yes | Yes |
| QuickBooks Sync | - | Yes | Yes |
| Stripe Payments | - | Yes | Yes |
| EasyPost Shipping | - | Yes | Yes |
| **ML & Advanced** |
| ML Time Estimation | - | - | Yes |
| Printer Fleet (MQTT) | - | - | Yes |
| Job Scheduling | - | - | Yes |
| Live Monitoring | - | - | Yes |
| Production Analytics | - | - | Yes |
| **Support** |
| Community (GitHub) | Yes | Yes | Yes |
| Email Support | - | Yes | Yes |
| Priority Support | - | - | Yes |
| Custom Development | - | - | Yes |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     OPEN SOURCE (GitHub)                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  filaops-core                                            │   │
│  │  - FastAPI Backend                                       │   │
│  │  - Products, BOMs, Inventory                             │   │
│  │  - Sales Orders, Production Orders                       │   │
│  │  - Basic MRP, Traceability                               │   │
│  │  - Admin API                                             │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│         PRO TIER         │  │     ENTERPRISE TIER      │
│  (Licensed Add-on)       │  │  (Licensed Add-on)       │
│                          │  │                          │
│  - Quote Portal          │  │  - ML Time Estimation    │
│  - B2B Portal            │  │  - Printer Fleet MQTT    │
│  - Squarespace Integration│ │  - Job Scheduling        │
│  - QuickBooks Integration │  │  - Live Monitoring       │
│  - Stripe/EasyPost       │  │  - Analytics Dashboard   │
└──────────────────────────┘  └──────────────────────────┘
```

## Implementation Plan

### Phase 1: Open Source Release (Current)
- [x] Clean up ERP codebase
- [x] Security audit
- [x] Update .gitignore
- [ ] Create LICENSE (BSL)
- [ ] Update README
- [ ] Push to GitHub

### Phase 2: Quote Proxy (Future)
- [ ] Add `/api/v1/quotes/generate` proxy endpoint in ERP
- [ ] Quote Portal calls ERP only (not ML directly)
- [ ] ERP proxies to ML backend if available
- [ ] Graceful degradation if ML unavailable

### Phase 3: Feature Flags (Future)
- [ ] Add `TIER` setting (open/pro/enterprise)
- [ ] Feature flag checks in endpoints
- [ ] License key validation
- [ ] Usage metering

### Phase 4: SaaS Infrastructure (Future)
- [ ] Multi-tenant database
- [ ] Subscription management
- [ ] Billing integration
- [ ] Customer dashboard

## Technical Implementation Notes

### Tier Detection
```python
# backend/app/core/settings.py
class Settings(BaseSettings):
    TIER: str = Field(default="open", description="open|pro|enterprise")
    LICENSE_KEY: Optional[str] = Field(default=None)

    @property
    def has_quote_portal(self) -> bool:
        return self.TIER in ("pro", "enterprise")

    @property
    def has_ml_features(self) -> bool:
        return self.TIER == "enterprise"
```

### Feature Gate Decorator
```python
# backend/app/core/features.py
from functools import wraps
from fastapi import HTTPException
from app.core.settings import settings

def require_tier(minimum_tier: str):
    tier_levels = {"open": 0, "pro": 1, "enterprise": 2}

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_level = tier_levels.get(settings.TIER, 0)
            required_level = tier_levels.get(minimum_tier, 0)

            if current_level < required_level:
                raise HTTPException(
                    status_code=402,
                    detail=f"This feature requires {minimum_tier} tier or higher"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage:
@router.post("/quotes/generate")
@require_tier("pro")
async def generate_quote(...):
    ...
```

## Proprietary Components (Never Open Source)

These remain in the private `bambu-print-suite` repository:

- `ml-engine/` - ML training code and data
- `data/models/*.pkl` - Trained models
- `Printer_Gcode_Files/` - Production print history
- Fleet management MQTT code
- Advanced analytics algorithms

## Revenue Model Considerations

| Revenue Stream | Notes |
|----------------|-------|
| SaaS Subscriptions | Primary revenue, predictable MRR |
| Self-hosted Licenses | One-time or annual for Pro tier |
| Support Contracts | Enterprise customers |
| Custom Development | Integration work |
| Training/Consulting | Implementation help |

## Competitive Positioning

- **vs MRPeasy**: More 3D print focused, ML capabilities
- **vs Odoo**: Lighter weight, print farm specific
- **vs Custom Solutions**: Faster to deploy, maintained

---

**Note**: This is a planning document. Implementation should wait until the core ERP is stable and has organic adoption.
