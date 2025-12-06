# Multi-Material 3D Print Quoting System

## Overview

This document describes the automated multi-material quoting logic for 3D printed parts. The system analyzes uploaded 3MF files, detects multi-color regions, and provides intelligent pricing with real-time lead time calculation based on material stock.

**Why This Matters**: Most 3D print quoting systems treat all files as single-material. Our system automatically detects multi-material prints and gives customers the choice between single-color (cheaper, faster) or multi-color (premium) options - with real-time availability feedback.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CUSTOMER UPLOAD                               │
│                                                                         │
│   3MF File ──────────────────────────────────────────────────────────►  │
│       │                                                                 │
│       ▼                                                                 │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │              3MF ANALYZER (threemf_analyzer.py)                │   │
│   │                                                                │   │
│   │  • Parse ZIP structure (3MF = ZIP with XML + meshes)          │   │
│   │  • Extract basematerials / colorgroup definitions              │   │
│   │  • Parse BambuStudio metadata (plate configs, AMS mapping)     │   │
│   │  • Detect painted regions (mmu_segmentation files)             │   │
│   │  • Return: material_count, slot colors, is_multi_material      │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                               │                                         │
│                               ▼                                         │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                    QUOTE GENERATION                            │   │
│   │                                                                │   │
│   │  If multi_material:                                            │   │
│   │    • Calculate MULTI price (per-color filament cost)          │   │
│   │    • Calculate SINGLE alternative (same part, one color)       │   │
│   │    • Return both prices to customer                            │   │
│   │                                                                │   │
│   │  Price factors:                                                │   │
│   │    • Material grams (from sliced G-code)                       │   │
│   │    • Print time (from sliced G-code)                           │   │
│   │    • Color changes (AMS purge waste)                           │   │
│   │    • Quality setting (layer height)                            │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                               │                                         │
│                               ▼                                         │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                   CUSTOMER DECISION                            │   │
│   │                                                                │   │
│   │  ┌─────────────────┐      ┌─────────────────┐                 │   │
│   │  │  SINGLE COLOR   │  OR  │  MULTI COLOR    │                 │   │
│   │  │                 │      │                 │                 │   │
│   │  │  • Lower price  │      │  • Higher price │                 │   │
│   │  │  • Pick 1 color │      │  • Pick N colors│                 │   │
│   │  │  • Faster lead  │      │  • Stock-based  │                 │   │
│   │  │    time         │      │    lead time    │                 │   │
│   │  └─────────────────┘      └─────────────────┘                 │   │
│   │                                                                │   │
│   │  If MULTI selected:                                            │   │
│   │    → Customer selects color for EACH material slot             │   │
│   │    → Lead time updates in real-time based on stock             │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                               │                                         │
│                               ▼                                         │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                 LEAD TIME CALCULATION                          │   │
│   │                                                                │   │
│   │  For each selected color:                                      │   │
│   │    required_kg = (grams_per_part × quantity) / 1000            │   │
│   │    available_kg = inventory.quantity_kg                        │   │
│   │                                                                │   │
│   │    if required_kg <= available_kg:                             │   │
│   │      → IN STOCK (2 business days)                              │   │
│   │    else:                                                       │   │
│   │      → NEEDS RESTOCK (5 business days)                         │   │
│   │                                                                │   │
│   │  Final lead time = MAX(all color lead times)                   │   │
│   └────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3MF File Analysis

### What is a 3MF File?

A 3MF file is a ZIP archive containing:
```
model.3mf/
├── 3D/
│   └── 3dmodel.model          # XML with mesh data + material definitions
├── Metadata/
│   ├── plate_1.json           # BambuStudio plate config (AMS mapping)
│   ├── model_settings.config  # Slicer settings including extruder assignments
│   └── slice_info.config      # Filament colors and types
└── [Content_Types].xml
```

### Material Detection Methods

The system uses multiple detection strategies (in priority order):

#### 1. BambuStudio Metadata (Most Reliable)

```python
# From plate_X.json - Contains AMS slot assignments
{
    "filament_ids": ["GFL99", "GFL01", "", ""],  # Non-empty = used slot
    "filament_colours": ["#FF0000", "#00FF00", "#00000000", "#00000000"],
    "ams_mapping": [0, 1, -1, -1]  # Slot assignments
}
```

#### 2. Model Settings Config

```python
# From Metadata/model_settings.config
# Extruder assignments per object/region
"extruder": "2"  # Object uses extruder 2
filament_colour = #FF0000;#00FF00;#0000FF;#FFFF00  # Color per slot
```

#### 3. Standard 3MF Materials (XML)

```xml
<!-- From 3D/3dmodel.model -->
<basematerials id="1">
    <base name="Red PLA" displaycolor="#FF0000"/>
    <base name="Blue PLA" displaycolor="#0000FF"/>
</basematerials>
```

#### 4. Paint/Segmentation Detection

```python
# Files containing 'paint' or 'mmu_segmentation' indicate multi-color painting
# Even if no explicit material definitions, painted models are multi-material
```

### Analysis Output

```python
@dataclass
class ThreeMFAnalysis:
    is_multi_material: bool      # True if >1 material detected
    material_count: int          # Number of distinct materials/colors
    material_slots: List[MaterialSlot]  # Details per slot
    model_name: str
    bounding_box: Optional[dict]

@dataclass
class MaterialSlot:
    slot_index: int        # 0-based slot number
    name: str              # "Filament 1", "Red PLA", etc.
    display_color: str     # Hex color code
    material_type: str     # PLA, PETG, etc. (if specified)
```

---

## Pricing Logic

### Single-Material Pricing

Standard formula:
```
unit_price = (material_cost + print_time_cost + overhead) × margin
           = (grams × $/gram) + (hours × $/hour) + fixed_overhead

material_cost = grams × material_rate[material_type]
print_time_cost = hours × machine_rate
```

### Multi-Material Pricing

Additional factors for multi-color prints:

```python
# AMS (Automatic Material System) adds complexity:
# 1. Purge waste - filament purged during color changes
# 2. Print time increase - color changes take time
# 3. Setup complexity - multiple spools must be loaded

multi_color_multiplier = 1.0 + (0.15 * (material_count - 1))
# Example: 2 colors = 1.15x, 3 colors = 1.30x, 4 colors = 1.45x

# Purge waste estimate (BambuStudio default ~60mm³ per change)
purge_waste_grams = color_changes × 0.2  # ~0.2g per purge

multi_price = base_price × multi_color_multiplier + purge_material_cost
```

### Single-Color Alternative

When a multi-material file is uploaded, we also calculate what it would cost if printed in a single color:

```python
# Customer uploaded multi-color model but might accept single color
single_color_price = base_price  # No multiplier, no purge waste

# UI presents both options:
# "Multi-Color: $24.99 (as designed)"
# "Single Color: $19.99 (one color only)"
```

---

## Customer Decision Flow

### Frontend Logic (QuoteResult.jsx)

```jsx
// After quote generation, if multi-material detected:
{quoteData.is_multi_material && (
  <ColorModeSelector
    multiPrice={quoteData.total_price}
    singlePrice={quoteData.single_color_alternative}
    materialSlots={quoteData.material_slots}
    onModeChange={handleColorModeChange}
  />
)}

// Customer chooses:
// Option A: "Print in original colors" → Show per-slot color pickers
// Option B: "Print in single color" → Show one color picker, use lower price
```

### Multi-Color Selection UI

When customer chooses multi-color, they select a color for each material slot:

```jsx
{printMode === 'multi' && materialSlots.map((slot, index) => (
  <ColorSelector
    key={slot.slot_index}
    slotName={`Color ${index + 1}`}
    defaultColor={slot.display_color}
    availableColors={availableColors}
    onColorChange={(color) => handleSlotColorChange(index, color)}
  />
))}
```

### Primary Color Designation

For multi-material prints, customer designates one color as "primary":
- Used for BOM material calculation (largest quantity)
- Determines base material type for pricing
- Other slots are "accent colors"

---

## Real-Time Lead Time Calculation

### The Innovation

Most quoting systems show a fixed lead time. Our system calculates lead time **per color selection** based on actual inventory levels.

### Algorithm

```javascript
// Called whenever customer changes a color selection
async function calculateLeadTime(colorSelections, quantity, gramsPerPart) {
  const requiredKgPerColor = {};
  let maxLeadDays = 2;  // Minimum (in-stock baseline)

  for (const selection of colorSelections) {
    const colorCode = selection.color_code;
    const requiredKg = (gramsPerPart * quantity) / 1000;

    // Query inventory for this specific color
    const inventory = await getColorInventory(colorCode);
    const availableKg = inventory?.quantity_kg || 0;

    if (requiredKg > availableKg) {
      // Need to order more filament
      maxLeadDays = Math.max(maxLeadDays, 5);  // 5 day lead for restock

      // Could also query supplier lead times for more accuracy
      // maxLeadDays = Math.max(maxLeadDays, supplier.lead_days);
    }
  }

  return maxLeadDays;
}
```

### UI Feedback

```jsx
// Lead time updates as customer selects colors
<div className="lead-time">
  {leadTimeDays === 2 ? (
    <span className="in-stock">
      ✓ All colors in stock - Ships in 2 business days
    </span>
  ) : (
    <span className="restock-needed">
      ⚠ Some colors need restocking - Ships in {leadTimeDays} business days
    </span>
  )}
</div>

// Per-color availability shown in selector
<ColorOption color={color}>
  {color.name}
  {color.quantity_kg > requiredKg ? (
    <span className="stock-badge">In Stock</span>
  ) : (
    <span className="stock-badge low">Low Stock</span>
  )}
</ColorOption>
```

---

## Data Storage

### Quote Record (ERP Database)

```sql
-- Quote table stores selected options
CREATE TABLE quotes (
    id INT PRIMARY KEY,
    quote_number VARCHAR(20),
    material_type VARCHAR(50),     -- Primary material (PLA, PETG)
    color VARCHAR(30),             -- Primary color code
    internal_notes TEXT,           -- JSON with multi-color details
    -- ... other fields
);

-- internal_notes JSON structure for multi-color:
{
    "print_mode": "multi",
    "primary_slot": 0,
    "slot_colors": [
        {
            "slot": 0,
            "color_code": "RED-001",
            "color_name": "Crimson Red",
            "color_hex": "#DC143C",
            "is_primary": true
        },
        {
            "slot": 1,
            "color_code": "WHT-001",
            "color_name": "Pure White",
            "color_hex": "#FFFFFF",
            "is_primary": false
        }
    ]
}
```

### BOM Creation

When quote is accepted, multi-color info flows to BOM:

```python
def create_multi_color_bom(quote, color_info):
    bom = BOM(product_id=product.id, code=f"BOM-{quote.quote_number}")

    # Material line for each color
    for slot in color_info['slot_colors']:
        # Find the inventory item for this color
        material = find_material_by_color(slot['color_code'])

        # Calculate grams for this slot (simplified - could use per-slot weights)
        slot_grams = quote.material_grams / len(color_info['slot_colors'])

        bom_line = BOMLine(
            bom_id=bom.id,
            component_id=material.id,
            quantity=slot_grams / 1000,  # Convert to kg
            unit_of_measure='kg',
            notes=f"Slot {slot['slot']}: {slot['color_name']}"
        )
        db.add(bom_line)

    return bom
```

---

## API Endpoints

### 1. Analyze 3MF (Pre-Quote)

```
POST /api/quotes/analyze-3mf
Content-Type: multipart/form-data

file: <3mf_file>

Response:
{
    "is_multi_material": true,
    "material_count": 3,
    "material_slots": [
        {"slot_index": 0, "name": "Filament 1", "display_color": "#FF0000"},
        {"slot_index": 1, "name": "Filament 2", "display_color": "#00FF00"},
        {"slot_index": 2, "name": "Filament 3", "display_color": "#0000FF"}
    ],
    "model_name": "multicolor_logo"
}
```

### 2. Generate Quote (With Multi-Color Pricing)

```
POST /api/quotes/generate
Content-Type: multipart/form-data

file: <3mf_file>
material: PLA
quality: standard
infill: 20
quantity: 1

Response:
{
    "price": 24.99,
    "single_color_alternative": 19.99,  // Only if multi-material
    "is_multi_material": true,
    "material_count": 3,
    "material_grams": 45.2,
    "print_time_minutes": 142,
    "dimensions": {"x": 120.5, "y": 80.3, "z": 25.0}
}
```

### 3. Accept Quote (With Color Selections)

```
POST /api/v1/quotes/portal/{quote_id}/accept

{
    "shipping_name": "John Doe",
    "shipping_address_line1": "123 Main St",
    // ... shipping fields ...

    "print_mode": "multi",  // or "single"
    "adjusted_unit_price": 24.99,  // Price for selected mode
    "multi_color_info": {
        "primary_slot": 0,
        "slot_colors": [
            {"slot": 0, "color_code": "RED-001", "color_name": "Red", "is_primary": true},
            {"slot": 1, "color_code": "WHT-001", "color_name": "White", "is_primary": false}
        ]
    }
}
```

---

## Competitive Advantage

### What Makes This Unique

1. **Automatic Detection**: No manual tagging - system reads the 3MF structure
2. **Customer Choice**: Single vs multi-color options with transparent pricing
3. **Real-Time Availability**: Lead times reflect actual inventory, not guesses
4. **BambuStudio Native**: Reads native BambuStudio/PrusaSlicer metadata
5. **Paint Support**: Detects MMU painting, not just separate objects

### Market Gap

Most competitors either:
- Don't support multi-material at all
- Require manual color specification
- Show fixed lead times regardless of stock
- Can't parse BambuStudio-specific metadata

Our system handles the complete workflow from file upload to production scheduling with full multi-material awareness.

---

## Future Enhancements

1. **Per-Slot Weight Calculation**: Currently splits grams evenly; could analyze G-code for actual per-color usage
2. **Supplier Integration**: Query supplier APIs for real restocking lead times
3. **Color Matching**: Suggest similar in-stock colors when selection is out of stock
4. **Price Optimization**: Show cheapest color combinations that match customer's design intent
5. **Material Compatibility**: Warn when multi-material print mixes incompatible materials (PLA + ABS)

---

## File References

| Component | File | Purpose |
|-----------|------|---------|
| 3MF Parser | `quote-engine/slicer/threemf_analyzer.py` | Extract material slots from 3MF |
| Quote API | `ml-dashboard/backend/main.py` | Generate prices with multi-color support |
| Upload UI | `quote-portal/src/pages/GetQuote.jsx` | File upload + color selection |
| Result UI | `quote-portal/src/pages/QuoteResult.jsx` | Single/multi decision + lead time |
| Quote Accept | `blb3d-erp/backend/app/api/v1/endpoints/quotes.py` | Store color selections |
| BOM Creation | `blb3d-erp/backend/app/services/bom_service.py` | Create multi-material BOMs |

---

*Document created: November 30, 2025*
*System Version: BLB3D ERP + Bambu Print Suite Integration*
