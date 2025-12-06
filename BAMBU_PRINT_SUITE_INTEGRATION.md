# Bambu Print Suite ↔ BLB3D ERP Integration Guide

## 🎯 Overview

Your **Bambu Print Suite** and **BLB3D ERP** are perfectly complementary systems that should be integrated. The Print Suite handles printer-level operations, while the ERP manages business operations.

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTEGRATION ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────┐         ┌─────────────────────────┐
│   BAMBU PRINT SUITE     │◄───────►│     BLB3D ERP           │
│                         │         │                         │
│  • Real-time monitoring │         │  • Business management  │
│  • MQTT telemetry       │         │  • Order management     │
│  • Quote generation     │         │  • Inventory tracking   │
│  • ML predictions       │         │  • Customer relations   │
│  • Cost calculation     │         │  • Financial tracking   │
└─────────────────────────┘         └─────────────────────────┘
         │                                     │
         └──────────── SHARED DATA ────────────┘
                  • Printers
                  • Print Jobs
                  • Materials
                  • Costs
                  • Telemetry
```

---

## 📊 Data Model Mapping

### **Perfect Alignment!**

| Bambu Print Suite | BLB3D ERP | Relationship |
|-------------------|-----------|--------------|
| `Printer` | `printers` table | 1:1 mapping |
| `PrintJob` | `print_jobs` table | 1:1 mapping |
| `Material` | `products` (materials) | ERP is source of truth |
| `Quote` | `sales_orders` | Quote converts to order |
| `Telemetry` | Real-time updates | Live data stream |
| `Analytics` | Aggregated from ERP | ERP provides historical data |

---

## 🔗 Integration Points

### **1. Production Orders → Print Jobs**

**Flow:**
```
ERP Sales Order
  ↓
ERP Production Order (what to make)
  ↓
ERP BOM (check materials)
  ↓
CREATE Print Job in Bambu Suite ← Integration Point
  ↓
Assign to Printer
  ↓
Monitor via MQTT
  ↓
UPDATE ERP with status
  ↓
Complete Production Order
```

**Implementation:**

```python
# In BLB3D ERP - Create Production Order
def create_production_order(sales_order_id, product_id, quantity):
    """Create production order and auto-create print jobs"""

    # 1. Create ERP production order
    production_order = ProductionOrder.create(
        code=generate_code('PO'),
        product_id=product_id,
        quantity=quantity,
        status='draft'
    )

    # 2. Get product BOM
    bom = BOM.get_active_for_product(product_id)

    # 3. Check if product needs 3D printing
    if product.category == 'Finished Goods' and product.has_bom:

        # 4. CREATE PRINT JOB in Bambu Suite via API
        print_job_request = {
            'production_order_id': production_order.id,
            'production_order_code': production_order.code,
            'product_sku': product.sku,
            'product_name': product.name,
            'quantity': quantity,
            'gcode_file': product.gcode_file_path,
            'material_type': bom.primary_material,  # from BOM
            'priority': 'normal',
            'estimated_time': bom.assembly_time_minutes
        }

        # Call Bambu Suite API
        response = bambu_api.create_print_job(print_job_request)

        # 5. Link print job to ERP
        PrintJob.create(
            production_order_id=production_order.id,
            printer_id=response['printer_id'],
            bambu_job_id=response['job_id'],  # Track Bambu Suite ID
            status='queued',
            gcode_file=product.gcode_file_path
        )

    return production_order
```

---

### **2. Material Inventory Sync**

**ERP is the Source of Truth for Inventory**

```python
# Bambu Suite queries ERP for material availability
class MaterialInventoryClient:
    """Client to check ERP inventory"""

    def check_material_availability(self, material_type: str, required_grams: float) -> dict:
        """Check if material is available in ERP inventory"""

        # Query ERP API
        response = requests.get(
            f"{ERP_API_URL}/api/inventory/check",
            params={
                'material_type': material_type,
                'required_quantity': required_grams / 1000  # Convert to kg
            }
        )

        return {
            'available': response.json()['available'],
            'on_hand': response.json()['on_hand_quantity'],
            'allocated': response.json()['allocated_quantity'],
            'locations': response.json()['locations']
        }

    def consume_material(self, print_job_id: str, material_type: str, grams_used: float):
        """Notify ERP that material was consumed"""

        # Create inventory transaction in ERP
        requests.post(
            f"{ERP_API_URL}/api/inventory/transactions",
            json={
                'transaction_type': 'consumption',
                'reference_type': 'print_job',
                'reference_id': print_job_id,
                'product_sku': material_type,  # e.g., 'M-00044' for PLA
                'quantity': grams_used / 1000,  # Convert to kg
                'location': 'PRODUCTION_AREA',
                'notes': f'Consumed by print job {print_job_id}'
            }
        )
```

---

### **3. Real-Time Printer Status**

**Bambu Suite → ERP Updates**

```python
# In Bambu Suite MQTT handler
class PrinterTelemetryHandler:
    """Handle MQTT telemetry and update ERP"""

    def on_telemetry_received(self, printer_id: str, telemetry: dict):
        """Process telemetry and update ERP"""

        # Update local Bambu Suite state
        self.update_local_state(printer_id, telemetry)

        # Push critical updates to ERP
        if telemetry['print_job_id']:
            self.update_erp_print_job(
                print_job_id=telemetry['print_job_id'],
                status=telemetry['status'],
                progress=telemetry['progress_percent'],
                current_layer=telemetry['layer_num'],
                remaining_time=telemetry['remaining_time']
            )

    def update_erp_print_job(self, print_job_id: str, **updates):
        """Update print job in ERP"""
        requests.patch(
            f"{ERP_API_URL}/api/print-jobs/{print_job_id}",
            json=updates
        )

    def on_print_completed(self, print_job_id: str, actual_data: dict):
        """Notify ERP that print is complete"""

        # Update ERP with actual data
        requests.post(
            f"{ERP_API_URL}/api/print-jobs/{print_job_id}/complete",
            json={
                'actual_time_minutes': actual_data['time'],
                'actual_material_grams': actual_data['filament_used'],
                'variance_percent': actual_data['variance'],
                'completed_at': datetime.now().isoformat()
            }
        )

        # Trigger production order completion in ERP
        requests.post(
            f"{ERP_API_URL}/api/production-orders/{actual_data['production_order_id']}/complete",
            json={
                'print_job_id': print_job_id,
                'actual_time': actual_data['time'],
                'actual_cost': actual_data['cost']
            }
        )
```

---

### **4. Quote Engine Integration**

**Bambu Suite Quote → ERP Sales Order**

```python
# Customer requests quote via Bambu Suite
# Quote approved → Convert to ERP Sales Order

class QuoteToOrderConverter:
    """Convert Bambu Suite quote to ERP sales order"""

    def convert_quote_to_order(self, quote_id: str, customer_id: int) -> int:
        """Create sales order in ERP from approved quote"""

        # Get quote from Bambu Suite
        quote = bambu_api.get_quote(quote_id)

        # Create sales order in ERP
        sales_order = {
            'customer_id': customer_id,
            'code': generate_code('CO'),
            'status': 'confirmed',
            'order_date': datetime.now().date(),
            'due_date': calculate_due_date(quote['total_time']),
            'subtotal': quote['total_price'],
            'total': quote['total_price'],
            'notes': f"Generated from quote {quote_id}",
            'lines': [
                {
                    'product_id': get_product_by_sku(quote['filename']),  # Map STL to product
                    'quantity': quote['quantity'],
                    'unit_price': quote['unit_price'],
                    'total': quote['total_price']
                }
            ]
        }

        # Create in ERP
        response = requests.post(
            f"{ERP_API_URL}/api/sales-orders",
            json=sales_order
        )

        order_id = response.json()['id']

        # Auto-create production order
        production_order_id = create_production_order(
            sales_order_id=order_id,
            product_id=sales_order['lines'][0]['product_id'],
            quantity=quote['quantity']
        )

        return order_id
```

---

### **5. ML Cost Prediction**

**Bambu Suite ML → ERP Cost Updates**

```python
# Use ML predictions to improve ERP cost estimates

class MLCostIntegration:
    """Integrate ML predictions into ERP"""

    def update_bom_costs_from_ml(self, product_id: int):
        """Update BOM costs based on ML predictions"""

        # Get historical print data from Bambu Suite
        ml_data = bambu_api.get_ml_predictions(product_id)

        # Update ERP BOM with more accurate costs
        bom = BOM.get_active_for_product(product_id)

        bom.update(
            total_cost=ml_data['predicted_cost'],
            assembly_time_minutes=ml_data['predicted_time'],
            notes=f"Updated from ML (based on {ml_data['sample_size']} prints)"
        )

        # Update product cost
        product = Product.get(product_id)
        product.update(cost=ml_data['predicted_cost'])
```

---

## 🏗️ Architecture Design

### **Recommended Setup:**

```
┌────────────────────────────────────────────────────────────────┐
│                      MICROSERVICES ARCHITECTURE                 │
└────────────────────────────────────────────────────────────────┘

┌─────────────────┐      ┌─────────────────┐      ┌──────────────┐
│   React UI      │      │   React UI      │      │  React UI    │
│  (ERP Frontend) │      │ (Print Suite)   │      │  (Customer)  │
└────────┬────────┘      └────────┬────────┘      └──────┬───────┘
         │                        │                       │
         │                        │                       │
    ┌────▼────────────────────────▼───────────────────────▼──────┐
    │                    API GATEWAY                              │
    │              (FastAPI - nginx routing)                      │
    └────┬─────────────────────┬──────────────────────┬──────────┘
         │                     │                      │
         │                     │                      │
┌────────▼──────────┐  ┌───────▼─────────┐  ┌───────▼──────────┐
│   ERP Backend     │  │ Print Suite API │  │  Quote Engine    │
│   (FastAPI)       │  │   (FastAPI)     │  │   (FastAPI)      │
│                   │  │                 │  │                  │
│ - Orders          │  │ - Printers      │  │ - STL Upload     │
│ - Inventory       │  │ - Print Jobs    │  │ - Slicing        │
│ - Customers       │  │ - Telemetry     │  │ - Cost Calc      │
│ - Production      │  │ - ML Engine     │  │ - Quote Gen      │
└────────┬──────────┘  └───────┬─────────┘  └───────┬──────────┘
         │                     │                      │
         │                     │                      │
┌────────▼──────────┐  ┌───────▼─────────┐  ┌───────▼──────────┐
│  SQL Server       │  │  SQLite/        │  │  File Storage    │
│  (ERP Database)   │  │  PostgreSQL     │  │  (GCODE/STL)     │
│                   │  │  (Print Data)   │  │                  │
└───────────────────┘  └─────────────────┘  └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  MQTT Broker     │
                    │  (Printers)      │
                    └──────────────────┘
                            │
                    ┌───────┴────────┐
                    ▼                ▼
            ┌─────────────┐   ┌─────────────┐
            │  Bambu P1S  │   │  Bambu A1   │
            │ (Donatello) │   │ (Leonardo)  │
            └─────────────┘   └─────────────┘
```

---

## 🔌 API Endpoints for Integration

### **ERP API Endpoints** (to add to FastAPI)

```python
# app/api/v1/integration/bambu.py

@router.post("/api/integration/print-jobs")
async def create_print_job_from_erp(request: PrintJobRequest):
    """Create print job in Bambu Suite from ERP production order"""
    # Forward to Bambu Suite API
    pass

@router.get("/api/integration/printer-status")
async def get_printer_status():
    """Get real-time printer status from Bambu Suite"""
    pass

@router.post("/api/integration/material-check")
async def check_material_availability(material: str, quantity: float):
    """Check if material is available"""
    pass

@router.post("/api/integration/quotes/convert")
async def convert_quote_to_order(quote_id: str, customer_id: int):
    """Convert Bambu Suite quote to ERP sales order"""
    pass
```

### **Bambu Suite API Endpoints** (to add)

```python
# bambu-print-suite/api/routes/integration.py

@router.post("/api/print-jobs")
async def create_print_job(job: PrintJobCreate):
    """Create new print job from ERP"""
    pass

@router.get("/api/printers/status")
async def get_all_printer_status():
    """Get status of all printers"""
    pass

@router.get("/api/print-jobs/{job_id}")
async def get_print_job_status(job_id: str):
    """Get detailed print job status"""
    pass

@router.post("/api/print-jobs/{job_id}/complete")
async def complete_print_job(job_id: str, actual_data: ActualData):
    """Mark job as complete and send data to ERP"""
    pass

@router.get("/api/materials/inventory")
async def get_material_inventory():
    """Query material inventory from ERP"""
    pass
```

---

## 📋 Implementation Roadmap

### **Phase 1: Basic Integration (Week 1)**

**Goal:** Link printers and enable basic job creation

1. **Set up shared database or API layer**
   - Option A: Shared PostgreSQL database
   - Option B: REST API between systems (recommended)

2. **Sync printer data**
   ```sql
   -- Add to ERP printers table
   INSERT INTO printers (code, name, model, status, mqtt_topic, ip_address)
   SELECT
       'DONATELLO',
       'Donatello (A1)',
       'Bambu A1',
       'idle',
       'device/{serial}/report',
       '192.168.1.100'
   FROM bambu_suite.printers;
   ```

3. **Create print jobs from production orders**
   - Add API endpoint in ERP
   - Call Bambu Suite API to create job
   - Link job back to production order

### **Phase 2: Real-Time Updates (Week 2)**

**Goal:** Live printer status in ERP dashboard

1. **Set up WebSocket/Server-Sent Events**
   - Bambu Suite pushes updates to ERP
   - ERP dashboard shows live status

2. **Update production orders automatically**
   - Print starts → Update status to "in_progress"
   - Print completes → Update to "completed"
   - Print fails → Alert and update status

3. **Material consumption tracking**
   - On print start: Allocate materials
   - On print complete: Consume materials
   - Create inventory transaction

### **Phase 3: Quote Integration (Week 3)**

**Goal:** Seamless quote-to-order flow

1. **Quote generation in Bambu Suite**
   - Customer uploads STL
   - Bambu Suite generates quote
   - Stores quote with customer info

2. **Quote approval → ERP order**
   - Customer approves quote
   - Auto-create customer in ERP (if new)
   - Convert to sales order
   - Create production order
   - Create print job

3. **Quote history in ERP**
   - Link quotes to customers
   - Track conversion rates
   - Analyze pricing effectiveness

### **Phase 4: ML Cost Optimization (Week 4)**

**Goal:** Use historical data to improve accuracy

1. **Collect actual vs estimated data**
   - Every print job records:
     - Estimated time vs actual
     - Estimated material vs actual
     - Estimated cost vs actual

2. **Train ML model**
   - Use historical data
   - Improve predictions
   - Update BOM costs

3. **Cost analysis dashboard**
   - Show variance trends
   - Identify inefficiencies
   - Optimize pricing

---

## 🔧 Configuration

### **Shared Configuration** (`config/integration.yaml`)

```yaml
# Integration settings
integration:
  mode: api  # or 'database'

  # ERP Connection
  erp:
    api_url: "http://localhost:8000"
    api_key: "your-api-key"
    database:
      host: "localhost\\SQLEXPRESS"
      database: "BLB3D_ERP"
      trusted_connection: true

  # Bambu Suite Connection
  bambu_suite:
    api_url: "http://localhost:8001"
    api_key: "your-api-key"
    mqtt_broker: "localhost"
    mqtt_port: 1883

  # Integration Features
  features:
    auto_create_print_jobs: true
    real_time_updates: true
    material_sync: true
    quote_conversion: true
    ml_cost_updates: true

  # Sync Settings
  sync:
    interval_seconds: 30  # How often to sync status
    retry_attempts: 3
    timeout_seconds: 10
```

---

## 💡 Benefits of Integration

### **For Operations:**
1. **Unified Dashboard**
   - See orders, production, and printers in one place
   - No switching between systems

2. **Automated Workflow**
   - Order → Production → Print Job (automatic)
   - Material consumption (automatic)
   - Inventory updates (automatic)

3. **Real-Time Visibility**
   - Know printer status instantly
   - Track job progress live
   - Alert on failures

### **For Customers:**
1. **Instant Quotes**
   - Upload STL → Get price immediately
   - No manual quoting process

2. **Order Tracking**
   - See production status
   - Get notifications
   - Know exact delivery date

### **For Finance:**
1. **Accurate Costs**
   - ML-based predictions
   - Actual vs estimated tracking
   - Better pricing decisions

2. **Profitability Analysis**
   - Per-product margins
   - Per-printer efficiency
   - Cost optimization insights

---

## 🚀 Quick Start Integration

### **Minimal Viable Integration (30 minutes)**

```python
# Step 1: Add to ERP (app/api/v1/bambu.py)
from fastapi import APIRouter
import requests

router = APIRouter()

BAMBU_API = "http://localhost:8001"

@router.post("/api/production-orders/{id}/start-print")
async def start_print_job(id: int, printer_id: str):
    """Start print job from production order"""

    # Get production order from ERP
    prod_order = ProductionOrder.get(id)

    # Create print job in Bambu Suite
    response = requests.post(
        f"{BAMBU_API}/api/print-jobs",
        json={
            'production_order_id': id,
            'product_sku': prod_order.product.sku,
            'quantity': prod_order.quantity,
            'printer_id': printer_id
        }
    )

    # Link back to ERP
    PrintJob.create(
        production_order_id=id,
        printer_id=printer_id,
        bambu_job_id=response.json()['id'],
        status='queued'
    )

    return {"status": "success", "job_id": response.json()['id']}


# Step 2: Add to Bambu Suite (api/routes/integration.py)
from fastapi import APIRouter

router = APIRouter()

@router.post("/api/print-jobs")
async def create_print_job(job_request: dict):
    """Receive print job from ERP"""

    # Create job in Bambu Suite
    job = PrintJob.create(
        id=generate_id(),
        production_order_id=job_request['production_order_id'],
        product_sku=job_request['product_sku'],
        quantity=job_request['quantity'],
        status='queued'
    )

    # Assign to printer
    assign_to_printer(job.id, job_request['printer_id'])

    return {"id": job.id, "status": "queued"}
```

---

## 📚 Next Steps

1. **Review current Bambu Suite API**
   - Check what endpoints exist
   - Identify gaps

2. **Add ERP integration endpoints**
   - Create `/api/integration/bambu` routes
   - Add WebSocket support

3. **Test basic flow**
   - Create production order → Print job
   - Monitor status updates
   - Complete production

4. **Deploy both systems**
   - Same server or separate?
   - Docker containers recommended
   - Nginx for routing

5. **Configure MQTT bridge**
   - Bambu Suite receives MQTT
   - Forwards critical updates to ERP
   - ERP dashboard updates live

---

## 🔒 Security Considerations

1. **API Authentication**
   - Use API keys for service-to-service
   - JWT tokens for user requests
   - Rate limiting

2. **Data Access**
   - ERP can read Bambu Suite data
   - Bambu Suite can only write to print jobs
   - No direct database access

3. **Network Security**
   - Use HTTPS for API calls
   - VPN for MQTT (if printers on different network)
   - Firewall rules

---

## 📞 Support & Questions

**Integration Issues?**
- Check logs: `/var/log/bambu-erp-integration.log`
- Verify API connectivity
- Check configuration file

**Need Help?**
- Review this document
- Check API documentation
- Test endpoints with Postman/Thunder Client

---

**This integration will give you a world-class 3D printing operation management system!** 🚀


---

## ?? Quote Engine Details (Updated Nov 26, 2025)

### Material Processing Pipeline
`
File Upload (3MF/STL)
        �
        ?
+-------------------------------------------------------------+
�                    production_profiles.py                    �
�  � Select printer based on material (P1S for ABS/ASA)       �
�  � Get BambuStudio profile paths                            �
�  � Read volumetric speed from filament profile              �
�  � Follow inheritance chain for flow ratio                  �
+-------------------------------------------------------------+
        �
        ?
+-------------------------------------------------------------+
�                      bambu_slicer.py                         �
�  � Create temp profiles with speed limits                   �
�  � Apply volumetric flow constraints                        �
�  � Run BambuStudio CLI                                      �
�  � Generate G-code                                          �
+-------------------------------------------------------------+
        �
        ?
+-------------------------------------------------------------+
�                    gcode_analyzer.py                         �
�  � Parse G-code for print time                              �
�  � Extract filament volume (mm�)                            �
�  � Count layers, moves                                      �
+-------------------------------------------------------------+
        �
        ?
+-------------------------------------------------------------+
�                   quote_calculator.py                        �
�  � Apply material density ? weight                          �
�  � Apply cost multiplier ? material cost                    �
�  � Add machine time, overhead, profit                       �
�  � ML correction factor (88.9% accuracy)                    �
+-------------------------------------------------------------+
        �
        ?
    Final Quote
`

### Material Configuration Locations

| Setting | File | Dict/Variable |
|---------|------|---------------|
| Cost multipliers | quote_calculator.py | material_multipliers |
| Densities (g/cm�) | quote_calculator.py | material_densities |
| Speed multipliers | filament_profiles.py | FILAMENT_SPEED_MULTIPLIERS |
| Volumetric limits | BambuStudio profiles | ilament_max_volumetric_speed |
| Flow ratios | BambuStudio profiles | ilament_flow_ratio |
| Printer support | production_profiles.py | supported_materials per printer |

### Profile Inheritance (BambuStudio)

BambuStudio profiles use inheritance. Child profiles may not contain all settings:
`
Bambu PETG Basic @BBL X1C.json
  +- inherits: "Bambu PETG Basic @base"
       +- Contains: filament_flow_ratio, temperatures, etc.
`

**Our code follows this chain** in production_profiles.py:
`python
def _read_volumetric_speed(self, profile_path):
    # Read from profile, if not found, follow 'inherits' to parent
`

### Printer Selection Logic
`python
# production_profiles.py
if material.upper() in ['ABS', 'ASA', 'PC', 'PA', 'PA-CF', 'PAHT-CF']:
    # Requires enclosed printer
    return self.get_printer_by_name('Leonardo')  # P1S
else:
    # Round-robin A1 printers
    return self.get_next_available_a1()
`

### Test Results (Nov 26, 2025)

| Material | Vol Speed | Flow | Calc Speed | Time | Weight | Price |
|----------|-----------|------|------------|------|--------|-------|
| PLA | 21.0 | 0.98 | 163 mm/s | 82m | 77.50g | .06 |
| PETG | 15.0 | 0.95 | 113 mm/s | 103m | 79.37g | .33 |
| ABS | 16.0 | 0.95 | 120 mm/s | 99m | 65.00g | .54 |
| ASA | 18.0 | 0.95 | 135 mm/s | 92m | 66.87g | .68 |
| TPU | 3.6 | 1.0 | 28 mm/s | 301m | 75.62g | .14 |

---

## ?? Known Issues

### STL Slicing Hangs
BambuStudio CLI hangs indefinitely on STL files. Workaround: Use 3MF format.

### Dimension Scaling
3MF dimensions read ~1.25� too large (trimesh library issue). Doesn't affect pricing.

### Technical Debt
Material config scattered across 4 files. Future: Admin page with DB-backed config.
