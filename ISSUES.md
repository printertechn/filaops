# Current Issues - Quote System

**Last Updated**: 2025-11-29
**Status**: Most issues RESOLVED - System functional for MVP testing
**Priority**: Medium (polish items remain)

---

## ✅ Recently Fixed (Nov 29, 2025)

### Issue #4: Infill Pricing Bug - RESOLVED

**Problem:** All infill percentages (15%, 20%, 40%, 100%) showed identical pricing

**Root Causes Found:**
1. BambuStudio CLI parameter was `--infill-density` but correct is `--sparse-infill-density`
2. 100% infill causes error: "sparse_infill_pattern: cubic doesn't work at 100% density"

**Fixes Applied:**
- File: `bambu-print-suite/quote-engine/slicer/bambu_slicer.py`
- Changed parameter: `--infill-density` → `--sparse-infill-density`
- Added 99% cap for solid infill:
```python
if infill_percentage is not None:
    effective_infill = min(infill_percentage, 99)
    cmd.extend(["--sparse-infill-density", str(effective_infill)])
```

**Validation Results:**
| Strength | Infill | Material | Price |
|----------|--------|----------|-------|
| Light | 15% | 15.4g | $9.12 |
| Standard | 20% | 16.1g | $9.15 |
| Strong | 40% | 18.7g | $9.27 |
| Solid | 99% | 26.2g | $9.68 |

### Issue #5: Payment Without Shipping - RESOLVED

**Problem:** Users could click Pay button without entering shipping address or selecting rate

**Fix Applied:**
- File: `quote-portal/src/pages/QuoteResult.jsx`
- Added validation state:
```javascript
const shippingComplete = shipping.shipping_address_line1 && 
  shipping.shipping_city && shipping.shipping_state && shipping.shipping_zip
const rateSelected = selectedRate !== null
const canSubmit = shippingComplete && rateSelected && emailValid
```
- Button now disabled until all requirements met
- Button text shows what's missing: "Fill shipping address" / "Select shipping rate"

---

## 🚨 Active Issues

### Issue #1: Dimensions Always Show Fallback Values (100×100×50mm)

**Status:** LOW PRIORITY - Doesn't affect pricing

**Description:**
Quotes show hardcoded fallback dimensions instead of actual model dimensions.

**Impact:** Cosmetic only - pricing uses actual G-code analysis

**Root Cause:** G-code may not contain bounding box comments in expected format

---

### Issue #3: STL File Slicing Failures

**Status:** WORKAROUND AVAILABLE - Use 3MF files

**Description:**
STL files fail to slice - BambuStudio CLI hangs indefinitely.

**Workaround:** Convert STL to 3MF before uploading (BambuStudio GUI or online converter)

**Impact:** Medium - customers must use 3MF format

---

## 📋 TODO Items (Not Bugs)

### Infrastructure
- [x] **Email Setup** - ✅ Configured (Google Workspace @ blb3dprinting.com)
  - support@blb3dprinting.com
  - orders@blb3dprinting.com
  - customer_service@blb3dprinting.com
- [ ] Run database migration: `scripts/add_quote_customer_fields.sql`

### Quote Review Workflow
- [ ] Email notification when quote submitted for review
- [ ] Admin UI for reviewing pending quotes
- [ ] Ability to adjust price and send payment link
- [ ] Email template for payment links

### Payment Flow
- [ ] Stripe webhook to confirm payment and create order
- [ ] Email receipt/confirmation to customer

---

## 📁 Key Files for Review

### Quote Generation Flow
1. **[main.py](C:\Users\brand\OneDrive\Documents\bambu-print-suite\ml-dashboard\backend\main.py)** (Lines 350-694)
   - API endpoint: `POST /api/quotes/generate`
   - Handles file upload, slicing, quote calculation
   - KEY LINES: 491 (material parameter), 642-680 (dimensions)

2. **[bambu_slicer.py](C:\Users\brand\OneDrive\Documents\bambu-print-suite\quote-engine\slicer\bambu_slicer.py)**
   - BambuStudio CLI wrapper
   - Slices STL/3MF files to G-code
   - KEY METHOD: `slice_stl()` (Lines 280-340)

3. **[gcode_analyzer.py](C:\Users\brand\OneDrive\Documents\bambu-print-suite\quote-engine\slicer\gcode_analyzer.py)**
   - Parses G-code for metrics
   - Extracts metadata (material, time, bounding box)
   - KEY LINES: 204-230 (bounding box extraction), 99-240 (metadata parsing)

4. **[quote_calculator.py](C:\Users\brand\OneDrive\Documents\bambu-print-suite\quote-engine\slicer\quote_calculator.py)**
   - Calculates pricing from G-code analysis
   - Applies material cost multipliers
   - KEY LINES: 63 (material param), 155-168 (multipliers), 229 (metadata)

5. **[production_profiles.py](C:\Users\brand\OneDrive\Documents\bambu-print-suite\quote-engine\slicer\production_profiles.py)**
   - Manages printer profiles and material routing
   - Selects quality/infill settings

### ERP Backend (Fallback)
6. **[bambu_client.py](c:\Users\brand\OneDrive\Documents\blb3d-erp\backend\app\services\bambu_client.py)**
   - ERP backend fallback pricing when ML Dashboard unavailable
   - Lines 35-44: Material costs
   - Lines 192-393: `generate_quote()` and `_calculate_quote_fallback()`

### Testing
7. **[test_ui.html](c:\Users\brand\OneDrive\Documents\blb3d-erp\backend\test_ui.html)**
   - Browser-based testing UI
   - Lines 284-292: Material dropdown (now includes TPU)
   - Lines 430: Material form data submission

---

## 🔍 Debugging Steps Taken

### Session Timeline
1. **Identified Issue**: Quotes showing fallback dimensions (100×100×50mm)
2. **First Attempt**: Updated main.py to extract dimensions from metadata
3. **Second Attempt**: Added bounding box extraction to gcode_analyzer.py
4. **Third Attempt**: Added material parameter to quote_calculator.py
5. **Fourth Attempt**: Updated main.py to pass material to calculator
6. **Fifth Attempt**: Added TPU to test UI dropdown
7. **Restarted Backend**: Killed shell 8121d4, started 4b7671

### Backend Restarts
- Initial: 978e46, 6c39c4, 8354ad, 09b91e (historical)
- Session: 6e67e8 → ba3e79 → 813ecf → 8121d4 → 4b7671 (current)
- Current: Shell 4b7671 running on port 8001

### Test Results Summary
| Quote # | Material | Weight | Dimensions | Price | Expected Price | Status |
|---------|----------|--------|------------|-------|----------------|--------|
| Q-2025-069 | PLA | 77.89g | 100×100×50 | $12.48 | ~$12.48 | ✅ Price OK |
| Q-2025-070 | ASA | 1170.88g | 100×100×50 | $250.57 | ~$25.81 | ❌ 10× too high |
| Q-2025-074 | PLA | 77.89g | 100×100×50 | $12.48 | $12.48 | ✅ Price OK |
| Q-2025-075 | PETG | 77.89g | 100×100×50 | $12.48 | ~$14.98 | ❌ Same as PLA |
| Q-2025-076 | ABS | 77.89g | 100×100×50 | $12.48 | ~$13.73 | ❌ Same as PLA |
| Q-2025-077 | PLA | 77.89g | 100×100×50 | $12.48 | $12.48 | ✅ Price OK |

**Pattern:**
- Dimensions ALWAYS fallback (100×100×50mm)
- Material costs NOT differentiated (all $12.48)
- Weight seems accurate for 3MF files
- Pricing was 10× too high for STL files (now failing to slice)

---

## 🛠️ Recommended Investigation

### High Priority
1. **Check G-code Output Format**
   - Manually slice a test file with BambuStudio CLI
   - Inspect G-code header for bounding box comments
   - Verify format matches parser expectations

2. **Add Extensive Debug Logging**
   ```python
   # In gcode_analyzer.py _extract_metadata()
   print(f"[DEBUG] Metadata extracted: {list(self.metadata.keys())}")
   print(f"[DEBUG] Bounding box in metadata: {'bounding_box_x' in self.metadata}")

   # In quote_calculator.py calculate_quote()
   print(f"[DEBUG] Material received: {material}")
   print(f"[DEBUG] Material cost per kg: ${material_cost_per_kg}")
   print(f"[DEBUG] Metadata keys: {list(metadata.keys())}")
   ```

3. **Test STL to 3MF Conversion**
   - As workaround, convert STL → 3MF before slicing
   - Check if 3MF format enables successful slicing

### Medium Priority
4. **Review Quote Calculation Chain**
   - Trace material parameter through entire flow
   - Check for any overrides in multi-plate logic
   - Verify no caching of old calculations

5. **Alternative Dimension Extraction**
   - If bounding box unavailable, parse G1 moves to find min/max XYZ
   - Calculate dimensions from actual toolpath

### Low Priority
6. **BambuStudio CLI Investigation**
   - Test CLI directly with problematic STL
   - Check version compatibility
   - Review CLI config settings

---

## 💡 Potential Root Causes

### Dimensions Issue
- ❓ G-code doesn't contain bounding box comments (BambuStudio CLI may omit them)
- ❓ Parser looking for wrong comment format
- ❓ Metadata not being passed through entire chain
- ❓ Fallback triggering too early

### Material Pricing Issue
- ❓ Quote calculation happening before material parameter applied
- ❓ Caching causing old quotes to be reused
- ❓ Multi-plate logic overriding material costs
- ❓ Material parameter getting lost in async/await chain

### STL Slicing Issue
- ❓ BambuStudio CLI profile incompatibility
- ❓ STL file format issues
- ❓ Resource exhaustion (memory/CPU)
- ❓ Profile settings causing infinite loop

---

## 📋 Checklist for Next Developer

- [ ] Read this entire document
- [ ] Review architecture diagram in ROADMAP.md
- [ ] Set up local environment (Python 3.11, SQL Server, BambuStudio CLI)
- [ ] Test quote generation with [test_ui.html](c:\Users\brand\OneDrive\Documents\blb3d-erp\backend\test_ui.html)
- [ ] Check backend logs for dimension extraction messages
- [ ] Manually slice STL file with BambuStudio CLI
- [ ] Inspect G-code output for bounding box comments
- [ ] Add debug logging to gcode_analyzer.py and quote_calculator.py
- [ ] Test material cost calculations with different materials
- [ ] Document findings and update this file

---

## 🎯 Success Criteria

**When these issues are fixed:**
1. ✅ Dimensions show actual model size (e.g., 99.34×99.34×80mm)
2. ✅ PETG costs 20% more than PLA for same part
3. ✅ STL files slice successfully (or auto-convert to 3MF)
4. ✅ Backend logs show `"[*] Extracted dimensions: X x Y x Z mm"`
5. ✅ Material cost multipliers visible in quote response

---

**Last Updated**: 2025-11-25
**Backend Status**: ML Dashboard running on port 8001 (shell 4b7671)
**Test UI**: [http://localhost:8000/test_ui.html](c:\Users\brand\OneDrive\Documents\blb3d-erp\backend\test_ui.html)

## 2025-11-25 - Quote System Fixes

FIXED:
- Material selection now flows through (Form params, .upper(), key name alignment)
- Dimensions extracted from mesh files (for 3MF)
- Different materials show different prices

REMAINING:
- Full material multipliers not applied in quote_calculator single-plate path
- STL slicing still hangs (BambuStudio CLI issue)
- 3MF dimensions read 1.25× too large (trimesh scaling issue)
## 2025-11-26 - Material Multiplier & Profile Inheritance Fixes

### FIXED:

**Issue #2: Material Costs Not Differentiating** - ? RESOLVED

Root Causes Found & Fixed:

1. **BambuStudio process profile inheritance** - Child profiles (e.g.,  .20mm Standard @BBL A1.json) use "inherits": "fdm_process_single_0.20" and don't contain speed settings directly. Our code checked if speed_key in profile_data which failed because speeds were inherited.
   - **Fix**: Always SET speed values in temp profile (overrides inheritance) instead of only modifying existing values
   - **File**: quote-engine/slicer/bambu_slicer.py lines 164-180

2. **Filament profile inheritance** - Volumetric speed and flow ratio values stored in base profiles (e.g., Bambu PETG Basic @base.json), not child profiles.
   - **Fix**: Follow inherits chain to read values from parent profiles
   - **File**: quote-engine/slicer/production_profiles.py _read_volumetric_speed() method

3. **ASA material missing** - ASA wasn't in materials dict, fell back to PLA.
   - **Fix**: Added 'ASA': 'Bambu ASA' to materials dict
   - **Fix**: Added ASA to P1S supported_materials (enclosed printer only)
   - **File**: quote-engine/slicer/production_profiles.py lines 64, 145

4. **P1S filament profile mismatch** - Leonardo (P1S) has ambustudio_name='Bambu Lab A1' as workaround, but condition 'A1' in printer.bambustudio_name matched first, causing A1 filament profiles instead of X1C.
   - **Fix**: Check printer.model == 'P1S' FIRST, use X1C filament profiles for proper ASA/ABS temps
   - **File**: quote-engine/slicer/production_profiles.py lines 243-252

### RESULTS - All Materials Now Working:

| Material | Volumetric | Flow | Max Speed | Print Time | Price |
|----------|------------|------|-----------|------------|-------|
| PLA | 21.0 mm�/s | 1.0 | 166 mm/s | 81.3 min | .02 |
| ABS | 16.0 mm�/s | 1.0 | 126 mm/s | 95.6 min | .79 |
| ASA | 18.0 mm�/s | 0.95 | 135 mm/s | 91.6 min | .04 |
| PETG | 13.0 mm�/s | 0.94 | 96 mm/s | 114.3 min | .72 |
| TPU | 3.6 mm�/s | 1.0 | 28 mm/s | 300.9 min | .23 |

### STILL REMAINING:

- **Issue #3: STL slicing hangs** - BambuStudio CLI issue with STL format
- **Dimension scaling** - 3MF dimensions read 1.25� too large (trimesh scaling issue)


---

## ?? Future Enhancements

### Enhancement #1: Centralized Material Configuration (Admin Page)

**Priority**: Medium
**Type**: Technical Debt / Feature

**Problem:**
Material data is currently scattered across multiple files:
- quote_calculator.py - densities (g/cm�), cost multipliers
- production_profiles.py - speed multipliers, volumetric limits
- ambu_client.py - fallback pricing
- Hardcoded machine rates (/hr placeholder - should be -25/hr)

**Proposed Solution:**
Single source of truth in database with admin UI:
`sql
CREATE TABLE Materials (
    material_id INT PRIMARY KEY,
    name VARCHAR(50),              -- 'PLA', 'ABS', etc.
    density DECIMAL(4,2),          -- g/cm�
    cost_multiplier DECIMAL(3,2),  -- vs PLA baseline
    speed_multiplier DECIMAL(3,2), -- vs PLA baseline
    base_cost_per_kg DECIMAL(8,2), -- actual purchase cost
    volumetric_limit DECIMAL(5,1), -- mm�/s
    flow_ratio DECIMAL(3,2),
    min_bed_temp INT,
    max_bed_temp INT,
    min_nozzle_temp INT,
    max_nozzle_temp INT,
    requires_enclosure BIT,
    supported_printers VARCHAR(255) -- CSV of printer models
);

CREATE TABLE SystemConfig (
    config_key VARCHAR(100) PRIMARY KEY,
    config_value VARCHAR(255),
    description VARCHAR(500)
);
-- machine_rate_per_hour, overhead_percent, profit_margin_percent, etc.
`

**Admin Page Features:**
- Material CRUD (add/edit/delete materials)
- Pricing config (machine rate, overhead %, profit margin %)
- Printer capabilities (which materials each printer supports)
- Labor rates (setup time, hourly rate)
- Real-time preview of how changes affect sample quote

**Benefits:**
- Change PLA price once ? all quotes update
- Add new material via UI, no code deploy
- Ties into inventory (actual purchase costs vs quoted costs)
- BOMs reference real material records
- Non-technical users can adjust pricing

**Target Phase**: Phase 3 (Material/Inventory Integration)

**Files to Refactor:**
- quote_calculator.py - pull from DB/config
- production_profiles.py - pull from DB/config  
- bambu_client.py - remove fallback hardcoding
- New: admin/config API endpoints
- New: admin UI page

---

### Enhancement #2: Material Weight by Density - IMPLEMENTED

**Date**: 2025-11-26
**Status**: ? COMPLETE

Added material-specific density lookup to quote_calculator.py:
`python
material_densities = {
    'PLA': 1.24, 'PETG': 1.27, 'ABS': 1.04, 'ASA': 1.07,
    'TPU': 1.21, 'PA-CF': 1.10, 'PC': 1.20, 'PAHT-CF': 1.10
}
`

Same 45,000 mm� part now shows correct weights:
- PLA: 55.8g
- ABS: 46.8g (16% lighter due to lower density)
- PETG: 57.2g (slightly heavier)

