# BLB3D - Future Architecture & ML/Agent Roadmap

> **Purpose**: Document the planned evolution of the system architecture, particularly the separation of concerns between ERP (business logic) and ML/Print Services (intelligence layer).
> This file preserves architectural decisions and future enhancement plans.

---

## Current State (November 2025)

### The Problem We Had

The ML Dashboard (port 8001) grew organically and accumulated **duplicate domain models**:

```
ERP Backend (8000)                    ML Dashboard (8001)
─────────────────                     ─────────────────────
✓ Sales Orders (from payments)        ✗ Orders (duplicate, empty)
✓ Quotes                              ✗ Customers (duplicate)
✓ Products/BOMs                       ✗ BOMs (duplicate)
✓ Inventory                           
✓ Customers                           ✓ Print Job Telemetry (unique)
                                      ✓ ML Training Data (unique)
                                      ✓ Printer MQTT Connection (unique)
                                      ✓ Quote Engine/Slicing (unique)
                                      ✓ Production Scheduling (unique)
                                      ✓ Thermal Optimizer (unique)
```

**Result**: Paid orders existed in ERP, but ML Dashboard showed empty order lists.

### The Solution: ERP as Source of Truth

We updated the ML Dashboard to **read business data from ERP** while keeping its unique ML/print capabilities:

```
┌─────────────────────────────────────────────────────────────────┐
│                        ERP Backend (8000)                        │
│                    "Source of Truth for Business"                │
│                                                                  │
│  Domain Models:                                                  │
│  • Customers        • Products/BOMs      • Inventory             │
│  • Quotes           • Sales Orders       • Production Orders     │
│                                                                  │
│  Integrations:                                                   │
│  • Stripe (payments)                                             │
│  • EasyPost (shipping)                                           │
│  • Squarespace/WooCommerce webhooks (future)                     │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ REST API (read business data)
                              │ 
┌─────────────────────────────┴───────────────────────────────────┐
│                     ML/Print Services (8001)                     │
│                "Intelligence & Hardware Layer"                   │
│                                                                  │
│  Unique Capabilities (KEEP):                                     │
│  • Printer Fleet Management (MQTT)                               │
│  • Quote Engine (BambuStudio CLI slicing)                        │
│  • ML Time/Quality Predictions                                   │
│  • Production Scheduling & Queue                                 │
│  • Thermal Optimization                                          │
│  • Real-time Telemetry Collection                                │
│  • Training Data Management                                      │
│                                                                  │
│  Removed (now reads from ERP):                                   │
│  • Orders → calls ERP /api/v1/sales-orders                       │
│  • Customers → calls ERP /api/v1/customers                       │
│  • BOMs → uses ERP products/boms                                 │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ MQTT Protocol
                              ▼
                    ┌─────────────────┐
                    │  Printer Fleet   │
                    │  (4x Bambu Lab)  │
                    └─────────────────┘
```

---

## Migration Details (What We Changed)

### ML Dashboard OrderManagement.jsx

**Before**: Fetched from `http://localhost:8001/api/orders/` (local duplicate)
**After**: Fetches from `http://localhost:8000/api/v1/sales-orders/` (ERP source of truth)

Key changes:
1. Updated `API_BASE` references for orders to point to ERP
2. Mapped ERP sales order schema to dashboard display
3. Kept production scheduling logic (calls back to 8001 for printer operations)

### Data Flow After Migration

```
Customer Payment (Portal)
         │
         ▼
    Stripe Webhook
         │
         ▼
┌────────────────────┐
│  ERP Backend       │
│  - Creates Sales   │
│    Order           │
│  - Creates Product │
│  - Creates BOM     │
└────────┬───────────┘
         │
         │ (ML Dashboard reads via API)
         ▼
┌────────────────────┐
│  ML Dashboard      │
│  - Displays Order  │
│  - Allocates       │
│    Materials       │
│  - Schedules Print │
└────────┬───────────┘
         │
         │ (Production scheduling)
         ▼
┌────────────────────┐
│  Printer Fleet     │
│  - Executes Job    │
│  - Reports Status  │
└────────────────────┘
```

---

## Future Architecture Phases

### Phase 1: Current (November 2025) ✅
- ERP is source of truth for business data
- ML Dashboard consumes ERP data via REST
- Single unified view of orders across systems

### Phase 2: Service Extraction (Q1 2026)
Extract ML Dashboard into discrete microservices:

```
┌─────────────────────────────────────────────────────────────────┐
│                        ERP Backend (8000)                        │
│                    "Business Operations"                         │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Quote Service  │  │  Print Service  │  │   ML Service    │
│                 │  │                 │  │                 │
│ • BambuStudio   │  │ • MQTT Fleet    │  │ • Predictions   │
│   CLI slicing   │  │ • Job Queue     │  │ • Training      │
│ • G-code        │  │ • Status        │  │ • Optimization  │
│   analysis      │  │ • Scheduling    │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

**Benefits**:
- Independent scaling
- Cleaner testing
- Service-specific deployments

### Phase 3: Agent Layer (Q2-Q3 2026)
Add AI agent capabilities on top of services:

```
┌─────────────────────────────────────────────────────────────────┐
│                       Agent Orchestrator                         │
│                                                                  │
│  Capabilities:                                                   │
│  • Natural language order management                             │
│  • Automated production decisions                                │
│  • Proactive inventory alerts                                    │
│  • Customer communication automation                             │
│  • Anomaly detection and response                                │
└─────────────────────────────────────────────────────────────────┘
         │
         │ Tool Calls
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Tool Registry                             │
│                                                                  │
│  Business Tools (ERP):           Print Tools (ML Services):      │
│  • create_sales_order            • schedule_print_job            │
│  • update_order_status           • check_printer_status          │
│  • check_inventory               • estimate_print_time           │
│  • allocate_materials            • optimize_queue                │
│  • send_customer_email           • analyze_print_quality         │
│                                                                  │
│  Intelligence Tools:             External Tools:                 │
│  • predict_completion_time       • send_sms_notification         │
│  • recommend_material            • create_shipping_label         │
│  • detect_quality_issues         • process_payment               │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 4: Autonomous Operations (2027+)
Full autonomous print farm with human oversight:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Autonomous Print Farm                         │
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │   Intake    │───▶│  Planning   │───▶│  Execution  │          │
│  │   Agent     │    │   Agent     │    │   Agent     │          │
│  └─────────────┘    └─────────────┘    └─────────────┘          │
│        │                  │                  │                   │
│        ▼                  ▼                  ▼                   │
│  • Quote review     • Material       • Printer                  │
│  • Feasibility        planning         assignment               │
│  • Pricing          • Schedule       • Quality                  │
│    decisions          optimization     monitoring               │
│                     • Conflict       • Failure                  │
│                       resolution       recovery                 │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Human Oversight Dashboard                   │    │
│  │  • Exception handling    • Policy configuration          │    │
│  │  • Quality approval      • Cost thresholds               │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## ML Service Capabilities (Preserve & Expand)

### Current ML Features (port 8001)

| Feature | Status | Description |
|---------|--------|-------------|
| Print Time Prediction | ✅ Active | Predicts actual print time from G-code analysis |
| Material Usage Prediction | ✅ Active | Estimates filament consumption |
| Thermal Optimization | ✅ Active | Optimizes bed/nozzle temps for quality |
| Printer Assignment | 🔄 Basic | Assigns jobs to available printers |
| Training Data Collection | ✅ Active | Records predicted vs actual for model improvement |

### Planned ML Features

| Feature | Priority | Description |
|---------|----------|-------------|
| Quality Prediction | High | Predict print quality issues before they happen |
| Failure Detection | High | Real-time detection of print failures via telemetry |
| Dynamic Scheduling | Medium | Optimize queue based on material changes, deadlines |
| Cost Optimization | Medium | Recommend print settings to minimize cost |
| Demand Forecasting | Low | Predict busy periods for capacity planning |
| Anomaly Detection | Low | Alert on unusual patterns in printer behavior |

### Training Data Schema

```sql
-- Current training data structure (preserve this)
training_data
├── id (PK)
├── gcode_file_hash
├── printer_id
├── material_type
├── predicted_time_minutes
├── actual_time_minutes
├── predicted_material_grams
├── actual_material_grams
├── layer_height_mm
├── infill_percentage
├── print_speed_mm_s
├── quality_score (1-5)
├── had_failure (bool)
├── failure_type (nullable)
├── ambient_temp_c
├── humidity_percent
├── created_at
└── metadata (JSON)
```

---

## Agent Tool Definitions (Future)

### Order Management Tools

```python
@tool
def create_order_from_quote(quote_id: int) -> dict:
    """Convert an approved quote to a sales order.
    
    Args:
        quote_id: The ID of the approved quote
        
    Returns:
        dict with order_id, order_number, and status
    """
    pass

@tool  
def check_order_status(order_id: int) -> dict:
    """Get current status of a sales order.
    
    Args:
        order_id: The sales order ID
        
    Returns:
        dict with status, payment_status, production_status, shipping_status
    """
    pass

@tool
def update_order_priority(order_id: int, priority: str, reason: str) -> dict:
    """Change order priority (requires justification).
    
    Args:
        order_id: The sales order ID
        priority: 'low', 'normal', 'high', 'urgent'
        reason: Why priority is being changed
        
    Returns:
        dict with success status and new priority
    """
    pass
```

### Production Tools

```python
@tool
def schedule_print_job(
    production_order_id: int,
    printer_id: Optional[int] = None,
    priority: str = "normal"
) -> dict:
    """Schedule a production order for printing.
    
    Args:
        production_order_id: The production order to schedule
        printer_id: Specific printer (auto-assigns if None)
        priority: Queue priority
        
    Returns:
        dict with job_id, assigned_printer, estimated_start, estimated_complete
    """
    pass

@tool
def check_printer_availability() -> list[dict]:
    """Get status of all printers in the fleet.
    
    Returns:
        List of printer status dicts with id, name, status, current_job, queue_depth
    """
    pass

@tool
def estimate_completion_time(production_order_id: int) -> dict:
    """Predict when a production order will complete.
    
    Uses ML model to estimate based on current queue, printer status, and job complexity.
    
    Returns:
        dict with estimated_start, estimated_complete, confidence_percent
    """
    pass
```

### Inventory Tools

```python
@tool
def check_material_availability(material_sku: str, quantity_kg: float) -> dict:
    """Check if sufficient material is available.
    
    Args:
        material_sku: Material SKU (e.g., 'PLA-BASIC-BLACK')
        quantity_kg: Required quantity in kg
        
    Returns:
        dict with available, on_hand, allocated, can_fulfill, shortage_kg
    """
    pass

@tool
def allocate_materials(production_order_id: int) -> dict:
    """Reserve materials for a production order.
    
    Marks inventory as allocated (not yet consumed).
    
    Returns:
        dict with success, allocated_items, any_shortages
    """
    pass

@tool
def consume_materials(print_job_id: int, actual_grams: float) -> dict:
    """Record actual material consumption after print completes.
    
    Args:
        print_job_id: The completed print job
        actual_grams: Actual material used (from printer telemetry)
        
    Returns:
        dict with success, variance_from_estimate
    """
    pass
```

### Communication Tools

```python
@tool
def send_order_update(
    order_id: int,
    update_type: str,
    custom_message: Optional[str] = None
) -> dict:
    """Send customer notification about order status.
    
    Args:
        order_id: The sales order
        update_type: 'confirmation', 'production_started', 'shipped', 'delivered'
        custom_message: Optional additional message
        
    Returns:
        dict with success, notification_id
    """
    pass

@tool
def escalate_to_human(
    context: str,
    urgency: str,
    recommended_action: str
) -> dict:
    """Escalate a situation requiring human decision.
    
    Args:
        context: Description of the situation
        urgency: 'low', 'medium', 'high', 'critical'
        recommended_action: Agent's suggested resolution
        
    Returns:
        dict with escalation_id, assigned_to
    """
    pass
```

---

## API Versioning Strategy

As we add agent capabilities, maintain backwards compatibility:

```
/api/v1/...          # Current stable API
/api/v2/...          # Future agent-optimized API
/api/internal/...    # Service-to-service communication
/api/agent/...       # Agent-specific endpoints (tools)
```

---

## Security Considerations for Agents

### Guardrails

1. **Cost Limits**: Agents cannot approve orders above threshold without human approval
2. **Inventory Protection**: Cannot over-allocate materials
3. **Customer Communication**: Templates only, no freeform customer emails
4. **Scheduling Limits**: Cannot bump urgent orders without justification logging
5. **Audit Trail**: All agent actions logged with reasoning

### Authentication

```python
# Agent authentication uses service accounts
AGENT_SERVICE_ACCOUNTS = {
    "intake-agent": ["read:quotes", "write:orders", "read:customers"],
    "planning-agent": ["read:orders", "write:production", "read:inventory"],
    "execution-agent": ["read:production", "write:print_jobs", "read:printers"],
}
```

---

## Metrics to Track

### Business Metrics
- Orders per day (by source)
- Quote-to-order conversion rate
- Average order value
- Time from order to ship

### Production Metrics
- Printer utilization rate
- Print success rate
- Material waste percentage
- Actual vs estimated time accuracy

### ML Metrics
- Prediction accuracy (time, material)
- Model drift detection
- Training data quality score
- Feature importance changes

### Agent Metrics (Future)
- Decisions per hour
- Human escalation rate
- Decision accuracy (post-hoc review)
- Time saved vs manual processing

---

## References

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Current system architecture
- [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md) - Detailed technical architecture with diagrams
- [PROJECT_STATUS.md](./PROJECT_STATUS.md) - Current development status
- [AI_CONTEXT.md](./AI_CONTEXT.md) - Quick reference for AI assistants

---

*Document Created: November 29, 2025*
*Last Updated: November 29, 2025*
*Purpose: Preserve architectural decisions and future ML/Agent roadmap*
