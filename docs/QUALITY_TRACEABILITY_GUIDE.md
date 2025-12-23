# 🎯 Quality & Traceability System Guide

Welcome to FilaOps' comprehensive quality management and traceability system! This guide will show you how to use the new features.

## 📑 Table of Contents

1. [Overview](#overview)
2. [Material Traceability](#material-traceability)
3. [Forward Traceability](#forward-traceability)
4. [Backward Traceability](#backward-traceability)
5. [Device History Records (DHR)](#device-history-records-dhr)
6. [Recall Impact Analysis](#recall-impact-analysis)
7. [License Key System](#license-key-system)
8. [API Reference](#api-reference)

---

## Overview

The Quality & Traceability system provides:

- **Forward Traceability**: Track materials from spool → production → customer
- **Backward Traceability**: Track products back to source materials and vendors
- **DHR Generation**: Export complete lineage for compliance
- **Recall Impact**: Calculate scope of material recalls
- **Lot-Level Tracking**: Track every spool individually
- **Serial Number Tracking**: Trace individual units

### Why This Matters

For businesses that need:
- **Quality Management**: ISO 9001, AS9100, FDA compliance
- **Customer Support**: "Which customers got this bad material?"
- **Vendor Management**: "Which vendor supplied this defective material?"
- **Recall Preparedness**: "What's the scope if we recall this spool?"
- **RMA Processing**: "What materials were used in this returned unit?"

---

## Material Traceability

### Accessing Traceability

1. Log in to FilaOps admin panel
2. Navigate to **Quality** → **Material Traceability** in the sidebar
3. Choose **Forward Trace** or **Backward Trace**

### Quick Start

**Forward Trace** (Spool → Products):
1. Enter spool number (e.g., `PO-2025-010-L1-003`)
2. Click "Trace Forward"
3. See all products made with that material
4. Export DHR for compliance

**Backward Trace** (Product → Materials):
1. Select "Serial Number" or "Sales Order"
2. Enter serial number (e.g., `BLB-20250120-001`)
3. Click "Trace Backward"
4. See all source materials and vendors

---

## Forward Traceability

### What It Does

Answers the question: **"Where did this material go?"**

Traces a spool forward through:
1. **Spool** → Which production orders used it
2. **Production Orders** → Which products were made
3. **Sales Orders** → Which customers received them
4. **Serial Numbers** → Individual unit tracking

### Use Cases

#### Scenario 1: Defective Material Batch
```
Problem: Vendor reports bad batch of ABS Blue
Solution:
1. Find spool number from receiving record
2. Run forward trace
3. See exactly which customers got products made with that material
4. Contact affected customers proactively
```

#### Scenario 2: Vendor Audit
```
Question: "Which customers received products made from Vendor X's materials?"
Solution:
1. Filter spools by vendor
2. Run forward trace on each spool
3. Generate report of all affected customers
4. Provide proof of material lineage
```

#### Scenario 3: Quality Investigation
```
Problem: Customer reports issue with product strength
Solution:
1. Look up serial number from customer order
2. Run backward trace to find source material
3. Run forward trace on that spool
4. Check if other customers have same material
5. Proactive quality check
```

### Forward Trace Results

The results show:

**Spool Information:**
- Material type and name
- Initial and current weight
- Supplier lot number
- Received date and expiry
- Location

**Usage Details:**
- All production orders that used this spool
- Products made and quantities
- Material consumed per order
- Sales orders linked to production
- Customer names and ship dates
- Serial numbers produced

**Impact Summary:**
- Total production orders affected
- Total units produced
- Total material consumed
- Sales orders affected
- Customers affected

### Exporting Forward Trace DHR

Click "Export DHR" to download a JSON file containing:
- Complete material lineage
- All production records
- All customer shipments
- Timestamp and user information

---

## Backward Traceability

### What It Does

Answers the question: **"What went into this product?"**

Traces a product backward through:
1. **Serial Number** → Production order
2. **Production Order** → All spools used
3. **Spools** → Supplier lots and vendors
4. **Purchase Orders** → When/where purchased

### Use Cases

#### Scenario 1: Customer RMA
```
Problem: Customer returns defective product
Solution:
1. Enter serial number from product label
2. Run backward trace
3. See exact materials used
4. Check if material was expired or from bad lot
5. Determine root cause
```

#### Scenario 2: Regulatory Audit
```
Question: "Prove this product meets material requirements"
Solution:
1. Look up sales order
2. Run backward trace
3. Show complete material lineage
4. Provide vendor certifications
5. Export DHR for auditor
```

#### Scenario 3: Vendor Quality Issues
```
Problem: Multiple failures from same material
Solution:
1. Trace failed products back to materials
2. Identify common vendor/lot
3. Put vendor on quality hold
4. Contact other customers with same material
5. Prevent future issues
```

### Backward Trace Results

**By Serial Number:**
- Serial number details
- Product information
- Production order details
- Sales order and customer
- All spools used with weights
- Purchase orders and vendors
- Traceability completeness indicator

**By Sales Order:**
- Sales order details
- All products in order
- All materials used across all products
- Unique spools and total weights
- Production orders involved

### Exporting Backward Trace DHR

Click "Export DHR" to download a JSON file containing:
- Complete product history
- All source materials
- Vendor information
- Production timestamps
- Quality data

---

## Device History Records (DHR)

### What Is A DHR?

A Device History Record is a comprehensive document that traces the complete lineage of a product from raw materials to customer delivery.

Required for:
- **FDA Medical Devices** (21 CFR Part 820)
- **Aerospace** (AS9100)
- **Automotive** (IATF 16949)
- **ISO 9001** (Quality Management)

### DHR Contents

FilaOps DHR includes:

1. **Product Identification**
   - Serial number
   - Product SKU and name
   - Production date
   - Production order

2. **Material Lineage**
   - All spools used
   - Material types and weights
   - Supplier lot numbers
   - Vendor information
   - Purchase dates

3. **Production Records**
   - Work orders
   - Quantities produced
   - Completion dates
   - Operators (future)

4. **Customer Delivery**
   - Sales order number
   - Customer name
   - Ship date
   - Tracking number (future)

5. **Traceability Chain**
   - Forward and backward links
   - Completeness indicator
   - Audit trail

### Using DHR For Compliance

**During Audit:**
1. Auditor requests DHR for serial number
2. Run backward trace
3. Export DHR
4. Provide to auditor
5. Demonstrate complete traceability

**For Customer Complaints:**
1. Customer reports issue
2. Generate DHR for affected units
3. Investigate material sources
4. Determine root cause
5. Implement corrective action

**For Regulatory Submissions:**
1. Export DHRs for sample products
2. Demonstrate traceability capability
3. Show material verification process
4. Prove quality system effectiveness

---

## Recall Impact Analysis

### What It Does

Calculates the full scope of a material recall:
- Which production orders used the material
- Which sales orders are affected
- Which customers received products
- All serial numbers produced
- Impact severity assessment

### How To Use

**Via API:**
```bash
POST /api/v1/traceability/recall-impact
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN

[1, 2, 3]  # Array of spool IDs to recall
```

**Response:**
```json
{
  "spools": [...],
  "impact": {
    "production_orders_affected": 42,
    "sales_orders_affected": 18,
    "customers_affected": 12,
    "serial_numbers_affected": 156,
    "products_affected": 3
  },
  "sales_orders": [...],
  "customers": ["Acme Corp", "TechStart Inc", ...],
  "serial_numbers": [...],
  "severity": "HIGH"  // HIGH if > 10 customers, MEDIUM if > 0, LOW otherwise
}
```

### Severity Levels

- **HIGH**: > 10 customers affected
- **MEDIUM**: 1-10 customers affected
- **LOW**: 0 customers affected (in stock only)

### Recall Workflow

1. **Identify Problem Material**
   - Vendor notification
   - Internal quality finding
   - Customer complaint pattern

2. **Run Impact Analysis**
   - Get spool IDs for affected lots
   - POST to recall-impact endpoint
   - Review results

3. **Notify Affected Parties**
   - Export customer list
   - Send notifications
   - Provide return instructions

4. **Track Returns**
   - Use serial number tracking
   - Mark as quarantined
   - Process refunds/replacements

5. **Root Cause Analysis**
   - Analyze material sources
   - Review vendor quality
   - Implement preventive actions

---

## License Key System

### Overview

FilaOps uses a **dormant licensing system**:
- **Current State**: Everyone gets all features (FREE)
- **Future**: Optional paid tiers for advanced features
- **Contributor Keys**: Perpetual professional keys for contributors

### Enabling Licensing (For You)

When you're ready to monetize:

1. **Enable Licensing**
```python
# backend/app/core/features.py
LICENSING_ENABLED = True  # Change from False
```

2. **Change Feature Tiers**
```python
"recall_impact_calculator": {
    "tier": FeatureTier.PROFESSIONAL,  # Change from COMMUNITY
    ...
},
```

3. **Generate Keys**
```bash
# Interactive mode
python scripts/generate_license.py

# Batch mode for contributors
python scripts/generate_license.py --batch scripts/contributors.txt
```

### Generating License Keys

**For a Single Customer:**
```bash
$ python scripts/generate_license.py

Email address: alice@example.com
Organization name: Acme Corp
Tier: 2 (Professional)
Duration: 1 (1 year)
Max users: 10

✅ License Key Generated:
FILAOPS-PRO-a1b2c3d4-e5f6g7h8-i9j0k1l2
```

**For Multiple Contributors:**
```bash
# Edit contributors.txt
alice@example.com,professional,Alice Contributor,0
bob@example.com,professional,Bob Contributor,0
charlie@example.com,professional,Charlie Contributor,0

# Generate all at once
python scripts/generate_license.py --batch scripts/contributors.txt

# Output:
✅ Generated 3 keys
💾 Saved to licenses_batch_20250122_143022.txt
```

### Feature Tiers

**Community (FREE)**
- Forward traceability
- Backward traceability
- DHR export
- Material spool tracking
- Serial number tracking
- All core ERP features

**Professional ($99/mo)**
- Everything in Community
- Recall impact calculator
- Quality holds & quarantine
- Material usage alerts
- Advanced quality reports

**Enterprise (Custom)**
- Everything in Professional
- API webhooks for traceability
- Multi-site traceability
- Statistical Process Control
- Custom integrations
- Priority support

### Validating License Keys

**In Code:**
```python
from app.core.licensing import validate_license_key, is_license_valid
from app.core.features import has_feature

# Check if license is valid
if is_license_valid("FILAOPS-PRO-..."):
    print("Valid license!")

# Get license details
info = validate_license_key("FILAOPS-PRO-...")
print(f"Tier: {info['tier']}")
print(f"Expires: {info['expires_at']}")

# Check feature access
if has_feature("recall_impact_calculator", user_tier="professional"):
    print("Feature available!")
```

**Via UI (Future):**
1. Go to Admin → Settings → License
2. Enter license key
3. Click "Activate"
4. Features unlock immediately

---

## API Reference

### Forward Traceability

#### Trace Spool Forward

```http
GET /api/v1/traceability/forward/spool/{spool_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "spool": {
    "id": 1,
    "spool_number": "PO-2025-010-L1-003",
    "material_name": "ABS Blue",
    "initial_weight_g": 1000,
    "current_weight_g": 245.7,
    "consumed_g": 754.3,
    "status": "active"
  },
  "purchase_info": {
    "po_number": "PO-2025-010",
    "vendor_name": "Premium Filaments Inc",
    "received_date": "2025-01-15"
  },
  "usage": [
    {
      "production_order": {
        "code": "WO-2025-042",
        "product_name": "Custom Bracket",
        "quantity_produced": 12
      },
      "material_consumed_g": 245.3,
      "sales_order": {
        "order_number": "SO-2025-088",
        "customer_name": "Acme Corp",
        "ship_date": "2025-01-21"
      },
      "serial_numbers": [
        {"serial_number": "BLB-20250120-001"},
        {"serial_number": "BLB-20250120-002"}
      ]
    }
  ],
  "summary": {
    "total_production_orders": 3,
    "total_consumed_g": 754.3,
    "total_units_produced": 42,
    "affected_sales_orders": 2,
    "affected_customers": 2
  }
}
```

### Backward Traceability

#### Trace Serial Number Backward

```http
GET /api/v1/traceability/backward/serial/{serial_number}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "serial_number": {
    "serial_number": "BLB-20250120-001",
    "status": "delivered"
  },
  "product": {
    "sku": "PART-001",
    "name": "Custom Bracket"
  },
  "production_order": {
    "code": "WO-2025-042",
    "quantity_produced": 12,
    "completed_date": "2025-01-20"
  },
  "sales_order": {
    "order_number": "SO-2025-088",
    "customer_name": "Acme Corp",
    "ship_date": "2025-01-21"
  },
  "material_lineage": [
    {
      "spool": {
        "spool_number": "PO-2025-010-L1-003",
        "material_name": "ABS Blue",
        "supplier_lot_number": "ABC-2025-001"
      },
      "weight_consumed_g": 20.5,
      "purchase_order": {
        "po_number": "PO-2025-010",
        "vendor_name": "Premium Filaments Inc",
        "received_date": "2025-01-15"
      }
    }
  ],
  "traceability_chain": {
    "complete": true,
    "spools_used": 1,
    "vendors": 1
  }
}
```

#### Trace Sales Order Backward

```http
GET /api/v1/traceability/backward/sales-order/{so_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "sales_order": {
    "order_number": "SO-2025-088",
    "customer_name": "Acme Corp",
    "status": "shipped"
  },
  "production_orders": [
    {
      "code": "WO-2025-042",
      "product_name": "Custom Bracket",
      "quantity": 12
    }
  ],
  "materials_used": [
    {
      "spool_number": "PO-2025-010-L1-003",
      "material_name": "ABS Blue",
      "total_consumed_g": 245.3,
      "used_in_orders": [
        {
          "production_order_code": "WO-2025-042",
          "weight_consumed_g": 245.3
        }
      ]
    }
  ],
  "summary": {
    "unique_spools": 2,
    "total_material_g": 523.7,
    "total_production_orders": 3
  }
}
```

### Recall Impact Analysis

#### Calculate Recall Impact

```http
POST /api/v1/traceability/recall-impact
Content-Type: application/json
Authorization: Bearer {token}

[1, 2, 3]  // Array of spool IDs
```

**Response:**
```json
{
  "spools": [
    {
      "id": 1,
      "spool_number": "PO-2025-010-L1-003",
      "material_name": "ABS Blue",
      "supplier_lot_number": "ABC-2025-001"
    }
  ],
  "impact": {
    "production_orders_affected": 42,
    "sales_orders_affected": 18,
    "customers_affected": 12,
    "serial_numbers_affected": 156,
    "products_affected": 3
  },
  "sales_orders": [...],
  "customers": ["Acme Corp", "TechStart Inc"],
  "serial_numbers": [...],
  "products": ["Custom Bracket", "Widget Housing"],
  "severity": "HIGH"
}
```

---

## Best Practices

### 1. Spool Receiving

**Always create spools when receiving materials:**
1. Receive PO with "Create Spools" enabled
2. Enter individual spool weights
3. Record supplier lot numbers
4. Set expiry dates if applicable
5. Verify spool numbers are unique

### 2. Production

**Link production to sales orders:**
1. Create production order from sales order
2. System automatically links them
3. Traceability is maintained automatically
4. Serial numbers inherit linkage

### 3. Quality Checks

**Regular traceability audits:**
1. Pick random serial numbers
2. Run backward trace
3. Verify complete chain
4. Check for missing data
5. Train operators on importance

### 4. Vendor Management

**Track vendor quality:**
1. Use forward trace to find issues
2. Track which vendors cause problems
3. Quality hold bad lots
4. Require certifications
5. Audit vendor processes

### 5. Customer Service

**Respond to complaints:**
1. Get serial number from customer
2. Run backward trace immediately
3. Identify root cause
4. Run forward trace if material issue
5. Proactively contact other customers

---

## Troubleshooting

### "Spool not found"

**Cause**: Spool ID or number doesn't exist

**Solution**:
1. Check spool number spelling
2. Verify spool was created during PO receipt
3. Check Material Spools page
4. Ensure you're searching by spool_number, not ID

### "No traceability data"

**Cause**: Spool hasn't been used yet

**Solution**:
- This is normal for new spools
- Wait until production consumes material
- Forward trace will show usage when it happens

### "Incomplete traceability chain"

**Cause**: Missing linkages in data

**Solution**:
1. Check if production order has sales_order_id
2. Verify material spools were linked to production
3. Review ProductionOrderSpool table
4. Ensure proper workflow: SO → PO → Production

### "Serial number not found"

**Cause**: Serial wasn't generated or is misspelled

**Solution**:
1. Check SerialNumber table
2. Verify production order completed
3. Ensure serial generation is enabled
4. Check serial format

---

## Support & Feedback

### Need Help?

- **Documentation**: This file!
- **GitHub Issues**: Report bugs or request features
- **Community**: Join our Discord/Slack

### Feature Requests

We'd love to hear what quality features you need:
- Advanced SPC (Statistical Process Control)
- CAPA (Corrective Action/Preventive Action)
- Non-conformance tracking
- Supplier scorecards
- Certificate of Conformance generation

### Contributing

If you've built quality features you'd like to share:
1. Fork the repo
2. Add your features
3. Submit a pull request
4. Get a free professional license key!

---

## Changelog

### Version 1.0.0 (2025-01-22)

**Added:**
- Forward traceability (spool → products → customers)
- Backward traceability (product → materials → vendors)
- DHR export functionality
- Recall impact analysis
- Dormant licensing system
- License key generator
- Quality sidebar section
- Material Traceability page

**Coming Soon:**
- PDF DHR export
- Quality holds & quarantine
- Material usage alerts
- Statistical Process Control
- Multi-site traceability
- API webhooks

---

**You're all set!** 🚀 Start tracing materials and building a rock-solid quality system!

