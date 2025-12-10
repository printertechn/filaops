# FilaOps Quote Portal API Reference

> **For Contributors:** This document describes the API endpoints used by the quote portal frontend.
> The actual implementation is proprietary, but you can test against the mock API server.

---

## Quick Start

```bash
# Start the mock API server
cd mock-api
npm install
npm start

# Mock API will be available at:
# - http://localhost:8000 (analyze endpoint)
# - http://localhost:8001 (quote/materials endpoints)
```

---

## Endpoints

### 1. Analyze 3MF File

**Endpoint:** `POST http://localhost:8000/api/v1/analyze-3mf`

**Purpose:** Upload a 3MF file to extract geometry, materials, and metadata.

**Request:**
```http
POST /api/v1/analyze-3mf
Content-Type: multipart/form-data

file: <3mf file>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "file_id": "uuid-here",
    "materials": [
      {
        "slot": 1,
        "color": "#FF5733",
        "name": "PLA Red",
        "type": "PLA"
      }
    ],
    "thumbnail": "data:image/png;base64,iVBORw0KG...",
    "metadata": {
      "object_name": "Duck.3mf",
      "total_objects": 1,
      "has_instances": true,
      "instance_count": 25
    }
  }
}
```

**Key Fields:**
- `file_id` - Unique identifier for this analysis (use in generate-quote)
- `materials` - Array of detected materials/colors
- `thumbnail` - Base64-encoded preview image
- `metadata.has_instances` - Whether file contains multiple instances
- `metadata.instance_count` - Number of instances if applicable

---

### 2. Generate Quote

**Endpoint:** `POST http://localhost:8001/api/v1/generate-quote`

**Purpose:** Get a price quote based on material selections.

**Request:**
```json
{
  "file_id": "uuid-from-analyze",
  "material_selections": {
    "1": "PLA-RED-001",
    "2": "PLA-BLUE-001"
  },
  "quantity": 1,
  "shipping": {
    "zip_code": "46825",
    "country": "US"
  }
}
```

**Response:**
```json
{
  "success": true,
  "quote": {
    "quote_id": "Q-20251206-001",
    "subtotal": 15.43,
    "shipping_options": [
      {
        "carrier": "USPS",
        "service": "Ground",
        "rate": 8.50,
        "delivery_days": "3-5"
      }
    ],
    "materials_cost": 12.18,
    "print_time_estimate": "4h 23m",
    "breakdown": {
      "PLA-RED-001": {
        "grams": 145.2,
        "cost": 7.26
      },
      "PLA-BLUE-001": {
        "grams": 98.4,
        "cost": 4.92
      }
    }
  }
}
```

**Key Fields:**
- `quote_id` - Unique quote reference
- `subtotal` - Materials + printing cost (before shipping)
- `shipping_options` - Array of available carriers/services
- `materials_cost` - Total cost of materials only
- `print_time_estimate` - Estimated manufacturing time
- `breakdown` - Per-material weight and cost

---

### 3. Get Material Options

**Endpoint:** `GET http://localhost:8001/api/v1/materials/options`

**Purpose:** Retrieve available materials for color selection.

**Response:**
```json
{
  "success": true,
  "materials": {
    "PLA": [
      {
        "sku": "PLA-RED-001",
        "name": "PLA Red",
        "color": "#FF5733",
        "in_stock": true,
        "cost_per_gram": 0.05
      }
    ],
    "PETG": [
      {
        "sku": "PETG-BLUE-001",
        "name": "PETG Blue",
        "color": "#3357FF",
        "in_stock": true,
        "cost_per_gram": 0.06
      }
    ]
  }
}
```

**Key Fields:**
- Materials grouped by type (PLA, PETG, ABS, etc.)
- `sku` - Unique material identifier (use in material_selections)
- `color` - Hex color code for UI preview
- `in_stock` - Whether material is currently available
- `cost_per_gram` - Base material cost

---

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": {
    "code": "INVALID_FILE",
    "message": "File must be a valid 3MF",
    "details": "..."
  }
}
```

**Common Error Codes:**
- `INVALID_FILE` - Uploaded file is not a valid 3MF
- `FILE_TOO_LARGE` - File exceeds size limit
- `MATERIAL_NOT_AVAILABLE` - Selected material is out of stock
- `INVALID_SHIPPING` - Shipping address is invalid

---

## Mock API vs Production

The mock API provides realistic responses for development:

| Feature | Mock API | Production API |
|---------|----------|----------------|
| 3MF Parsing | ✅ Real (JSZip) | ✅ Real |
| Material Detection | ✅ Real | ✅ Real |
| Thumbnail Extraction | ✅ Real | ✅ Real |
| Weight Calculation | ❌ Estimated | ✅ Precise (via slicing) |
| Print Time | ❌ Estimated | ✅ Precise (via slicing) |
| Pricing | ❌ Fake rates | ✅ Real pricing engine |

**What this means for contributors:**
- The mock API lets you build and test the full UI workflow
- Material detection and file parsing work identically
- Weights and times are "close enough" for UI development
- Pricing is intentionally fake to protect business logic

---

## Testing Checklist

When working with the quote portal, test:

- [ ] Upload various 3MF files (single color, multi-color, instances)
- [ ] Material selection UI updates quote in real-time
- [ ] Shipping options display correctly
- [ ] Quote breakdown shows per-material costs
- [ ] Error states display user-friendly messages
- [ ] Mobile responsiveness
- [ ] Accessibility (keyboard navigation, screen readers)

---

## Notes for Frontend Development

### Material Color Mapping

When a 3MF has multiple materials, the analyze endpoint returns detected colors. Your UI should:

1. Display detected colors visually
2. Let users map each slot to an available material
3. Show real-time cost updates as selections change
4. Validate all slots are filled before generating quote

### Instance Rendering

If `metadata.has_instances` is true:
- The 3MF contains multiple copies of an object
- Your 3D viewer should render all instances
- Currently, there's a known issue with BambuStudio instance rendering

See: [Issue #1 - 3D Viewer Instance Rendering Bug](https://github.com/Blb3D/filaops/issues/1)

---

## Questions?

- **Frontend Issues:** Open an issue on GitHub
- **API Bugs:** File a bug report with request/response
- **Feature Requests:** Use GitHub Discussions

**Remember:** The mock API is for development only. Production uses a different backend.
