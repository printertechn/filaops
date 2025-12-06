# BLB3D ERP ↔ Bambu Print Suite Integration - Quick Start

## 🎯 Overview

This guide will help you get the ERP and Bambu Print Suite integration running in **5 minutes**.

## 📋 Prerequisites

- Python 3.10+ installed
- SQL Server Express with BLB3D_ERP database
- Both repositories cloned:
  - `c:\Users\brand\OneDrive\Documents\blb3d-erp`
  - `C:\Users\brand\OneDrive\Documents\bambu-print-suite`

## 🚀 Quick Start (5 Steps)

### Step 1: Install Dependencies

**ERP Backend:**
```bash
cd c:\Users\brand\OneDrive\Documents\blb3d-erp\backend
pip install -r requirements.txt
```

**Bambu Print Suite:**
```bash
cd C:\Users\brand\OneDrive\Documents\bambu-print-suite\ml-dashboard\backend
pip install -r requirements.txt
```

### Step 2: Configure Integration

Edit the configuration file:
```bash
notepad c:\Users\brand\OneDrive\Documents\blb3d-erp\config\integration.yaml
```

**Minimum required settings:**
```yaml
erp:
  api_url: "http://localhost:8000"

bambu_suite:
  api_url: "http://localhost:8001"

features:
  auto_create_print_jobs: true
  real_time_updates: true
```

### Step 3: Start the ERP Backend

**Terminal 1:**
```bash
cd c:\Users\brand\OneDrive\Documents\blb3d-erp\backend
python -m uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

Verify it's working: http://localhost:8000/docs

### Step 4: Start Bambu Print Suite

**Terminal 2:**
```bash
cd C:\Users\brand\OneDrive\Documents\bambu-print-suite\ml-dashboard\backend
python main.py
```

You should see:
```
[OK] MRP routers loaded (..., integration)
INFO:     Uvicorn running on http://127.0.0.1:8001
```

Verify it's working: http://localhost:8001/docs

### Step 5: Test the Integration

**Check Integration Status:**

Open your browser to: http://localhost:8000/api/v1/integration/sync-status

You should see:
```json
{
  "status": "connected",
  "bambu_suite_url": "http://localhost:8001",
  "timestamp": "2025-11-23T..."
}
```

**From Bambu Suite side:**

Open: http://localhost:8001/api/integration/sync-status

You should see:
```json
{
  "status": "connected",
  "erp_url": "http://localhost:8000",
  "timestamp": "2025-11-23T..."
}
```

## 🎉 Success! Integration is Running

## 🧪 Test the Integration Flow

### Test 1: Create a Print Job from ERP

```bash
curl -X POST "http://localhost:8000/api/v1/production-orders" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "PO-TEST-001",
    "product_id": 1,
    "product_sku": "FG-00001",
    "product_name": "Test Widget",
    "quantity": 1,
    "priority": "normal"
  }'
```

**Expected Result:**
- Production order created in ERP
- Print job automatically created in Bambu Print Suite
- Job assigned to optimal printer
- Response shows print_job_id

### Test 2: Check Printer Status from ERP

```bash
curl "http://localhost:8000/api/v1/integration/printer-status"
```

**Expected Result:**
```json
[
  {
    "id": "DONATELLO",
    "name": "Donatello (A1)",
    "model": "Bambu A1",
    "status": "idle",
    "current_job_id": null
  },
  {
    "id": "LEONARDO",
    "name": "Leonardo (P1S)",
    "model": "Bambu P1S",
    "status": "printing",
    "current_job_id": "PJ-001",
    "progress_percent": 45.5,
    "remaining_time": 120
  }
]
```

### Test 3: Check Material Availability

```bash
curl -X POST "http://localhost:8000/api/v1/integration/material-check" \
  -H "Content-Type: application/json" \
  -d '{
    "material_type": "PLA",
    "required_quantity": 0.5
  }'
```

**Expected Result:**
```json
{
  "available": true,
  "on_hand": 5.0,
  "allocated": 1.0,
  "locations": [
    {"location": "PRODUCTION_AREA", "quantity": 3.0},
    {"location": "WAREHOUSE_A", "quantity": 2.0}
  ]
}
```

## 📊 Integration Architecture

```
┌─────────────────────┐         ┌─────────────────────┐
│   BLB3D ERP         │         │   Bambu Print Suite │
│   :8000             │◄───────►│   :8001             │
│                     │         │                     │
│  Production Orders  │  HTTP   │  Print Jobs         │
│  Inventory          │  REST   │  Printer Status     │
│  Materials          │   API   │  ML Scheduling      │
└─────────────────────┘         └─────────────────────┘
```

## 🔗 Key Integration Points

### 1. Production Order → Print Job
**ERP** creates production order → **Bambu Suite** receives and creates print job

**API Call:**
```
POST http://localhost:8001/api/integration/print-jobs
```

### 2. Printer Status → Dashboard
**Bambu Suite** monitors printers → **ERP** displays live status

**API Call:**
```
GET http://localhost:8001/api/integration/printers/status
```

### 3. Material Check
**Bambu Suite** checks inventory → **ERP** returns availability

**API Call:**
```
POST http://localhost:8000/api/v1/inventory/check
```

### 4. Print Completion → Inventory Update
**Bambu Suite** completes print → **ERP** updates inventory and production status

**API Calls:**
```
POST http://localhost:8000/api/v1/print-jobs/{job_id}/complete
POST http://localhost:8000/api/v1/production-orders/{id}/complete
```

## 📱 API Documentation

Both services provide interactive API documentation:

- **ERP API Docs**: http://localhost:8000/docs
- **Bambu Suite API Docs**: http://localhost:8001/docs

## 🐛 Troubleshooting

### Issue: "Connection refused" when testing sync-status

**Solution:**
- Verify both services are running
- Check port numbers (8000 for ERP, 8001 for Bambu Suite)
- Check firewall settings

### Issue: Import errors when starting services

**Solution:**
```bash
# ERP Backend
cd c:\Users\brand\OneDrive\Documents\blb3d-erp\backend
pip install -r requirements.txt --upgrade

# Bambu Suite
cd C:\Users\brand\OneDrive\Documents\bambu-print-suite\ml-dashboard\backend
pip install -r requirements.txt --upgrade
```

### Issue: Database connection errors

**Solution:**
- Verify SQL Server Express is running
- Check database name in config: `BLB3D_ERP`
- Ensure Windows Authentication is enabled

### Issue: Material check returns empty results

**Solution:**
- This is expected if no materials are in inventory yet
- Add materials through ERP interface first
- The integration will sync automatically

## 📚 Next Steps

Now that the integration is running:

1. **Configure Real Printers**
   - Edit printer settings in Bambu Suite
   - Add your actual printer IPs and access codes
   - Test MQTT connection

2. **Import Production Data**
   - Create products in ERP
   - Set up BOMs with material requirements
   - Link GCODE files to products

3. **Test End-to-End Flow**
   - Create a real sales order
   - Generate production order
   - Watch it auto-create print job
   - Monitor in real-time

4. **Set Up ML Training**
   - Start collecting actual print data
   - ML model will learn and improve scheduling
   - Cost estimates become more accurate

## 🎯 Integration Checklist

- [x] ERP backend running on :8000
- [x] Bambu Suite running on :8001
- [x] Sync status shows "connected"
- [ ] Created test production order
- [ ] Print job appeared in Bambu Suite
- [ ] Printer status displays correctly
- [ ] Material check works
- [ ] Configured real printers
- [ ] Tested with actual print

## 💡 Pro Tips

1. **Development**: Keep both terminal windows open to see real-time logs
2. **API Testing**: Use the `/docs` endpoints for interactive testing
3. **Debugging**: Set `development.debug: true` in config for verbose logging
4. **Production**: Change `features.mock_apis: false` when ready for real data

## 📞 Getting Help

**Check logs:**
```bash
# ERP logs
tail -f c:\Users\brand\OneDrive\Documents\blb3d-erp\logs\integration.log

# Bambu Suite logs - check terminal output
```

**Common Issues:**
- See troubleshooting section above
- Check API documentation at `/docs` endpoints
- Verify configuration in `config/integration.yaml`

---

**🎉 You now have a fully integrated ERP and Print Farm management system!**

The integration enables:
- ✅ Automatic print job creation from orders
- ✅ Real-time printer monitoring in ERP
- ✅ Material inventory synchronization
- ✅ ML-optimized printer scheduling
- ✅ Actual cost tracking and optimization
