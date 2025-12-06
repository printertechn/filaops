# BLB3D ERP Bug Fix & Enhancement Status

**Last Updated:** 2024-12-01 ~02:30 EST  
**Document Location:** `/docs/BUG_FIX_STATUS.md`

---

## Overview

This document tracks the implementation status of critical bug fixes and enhancements identified during the E2E code review on 2024-12-01.

Full analysis document: See `blb3d-erp-bugfixes.md` in project outputs.

---

## Critical Bugs (Must Fix)

### Bug #1: Double Consumption in pass_qc ✅ FIXED

**Problem:** Both `complete_print()` and `pass_qc()` contained identical material consumption logic. When called in sequence (the normal flow), inventory was decremented TWICE.

**Impact:** Negative inventory quantities, inaccurate stock levels, incorrect COGS.

**Fix Applied:** Removed material consumption from `pass_qc()`. Materials are now consumed ONLY in `complete_print()`, which is correct because that's when physical consumption happens.

**File Modified:** `backend/app/api/v1/endpoints/admin/fulfillment.py`

**Status:** ✅ COMPLETE

**Correct Flow Now:**
```
start_production()  → reserves materials (allocated_qty increases)
complete_print()    → consumes materials (on_hand + allocated decrease)  
pass_qc()           → status update ONLY (no inventory changes)
```

---

### Bug #2: No Inventory Record for Materials ✅ FIXED

**Problem:** When `material_service.get_material_product_for_bom()` creates or links a Product for a material, no corresponding `Inventory` record is created. BOM explosion queries the `Inventory` table and finds nothing.

**Impact:** Production shows "insufficient materials" even when `MaterialInventory` shows stock available.

**Fix Applied:** After getting/creating Product, check if Inventory record exists. If not, create one with `on_hand_quantity` synced from `MaterialInventory.quantity_kg`.

**File Modified:** `backend/app/services/material_service.py`

**Status:** ✅ COMPLETE

---

### Bug #3: MTO Finished Goods Not Created ✅ FIXED

**Problem:** In `complete_print()`, when adding good parts to finished goods inventory, the code tries to find existing Inventory record for the product. For MTO (make-to-order) custom products, this is always None because no inventory exists for custom one-off products.

**Impact:** Finished goods never tracked in inventory for MTO orders.

**Fix Applied:** If no Inventory record exists for the product, create one at location_id=1 (default FG location) before adding quantity.

**File Modified:** `backend/app/api/v1/endpoints/admin/fulfillment.py`

**Status:** ✅ COMPLETE

---

### Bug #4: MaterialInventory Never Decremented ✅ FIXED

**Problem:** When materials are consumed in production, only the `Inventory` table is updated. `MaterialInventory.quantity_kg` is never decremented.

**Impact:** Quote engine keeps showing "in stock" for materials that have been used up. Customers can order products that can't be made.

**Fix Applied:** After consuming from `Inventory`, check if component is raw material (`is_raw_material=True`). If so, find linked `MaterialInventory` record and:
1. Decrement `quantity_kg` by consumed amount
2. Update `in_stock` flag to False if quantity reaches 0

**File Modified:** `backend/app/api/v1/endpoints/admin/fulfillment.py`

**Status:** ✅ COMPLETE

---

### Bug #5: No Sync at Production Start ✅ FIXED

**Problem:** Even if Inventory records exist for materials, quantities may be out of sync with MaterialInventory (the source of truth for raw materials).

**Impact:** BOM explosion may reserve wrong quantities.

**Fix Applied:** At the start of `start_production()`, before BOM explosion:
1. Loop through all BOM components that are raw materials
2. Find their MaterialInventory record
3. Create or sync Inventory record from MaterialInventory.quantity_kg
4. Return `materials_synced` in response showing what was synced

**File Modified:** `backend/app/api/v1/endpoints/admin/fulfillment.py`

**Status:** ✅ COMPLETE

---

## Medium Priority Bugs

### Bug #6: Hardcoded location_id=1 ⬜ TODO

**File:** `backend/app/api/v1/endpoints/inventory.py` line ~130

### Bug #7: No Blocking on Zero Inventory ⬜ TODO

Currently production starts with warnings only when insufficient materials.

### Bug #8: Scrap Location Fallback ⬜ TODO

Scrap transactions default to location_id=1 instead of proper scrap location.

---

## Enhancements

| # | Enhancement | Priority | Status |
|---|-------------|----------|--------|
| 1 | MTS (Make-to-Stock) Support | Medium | ⬜ TODO |
| 2 | Partial QC with Quantities | Medium | ⬜ TODO |
| 3 | Reprint Tracking (parent_production_order_id) | Medium | ⬜ TODO |
| 4 | Scrap Reason Codes | Low | ⬜ TODO |
| 5 | Yield Reporting (FPY, Pareto) | Low | ⬜ TODO |
| 6 | Purchasing Module | Medium | ⬜ TODO |
| 7 | Accounting Journals | Low | ⬜ TODO |

---

## Implementation Order

### Phase 1: Stop the Bleeding (Critical) - ~1 hour
1. ✅ Bug #1: Double consumption - **DONE**
2. ✅ Bug #3: MTO finished goods creation - **DONE**
3. ✅ Bug #4: MaterialInventory decrement on consumption - **DONE**

### Phase 2: Fix the Foundation - ~1 hour
4. ✅ Bug #2: Create Inventory records for materials - **DONE**
5. ✅ Bug #5: Sync at production start - **DONE**

### Phase 3: Polish - ~30 min
6. ⬜ Bug #6-8: Hardcoded values

### Phase 4: Enhancements
7. ⬜ Enhancements #1-7 per priority

---

## E2E Testing Checklist

After all critical bugs are fixed, run this test:

```
□ Upload 3MF, select material/color → Quote shows correct lead time
□ Pay for quote → Product, BOM, SO, PO all created
□ Check Inventory table → Material Product has Inventory record
□ Start production → Reservations created, allocated increases
□ Complete print (5 good, 1 bad) → Materials consumed ONCE, FG added, scrap recorded
□ Pass QC → Status updates ONLY (no inventory changes)
□ Check MaterialInventory → quantity_kg decremented
□ Ship order → Complete
□ Create new quote for same material → Shows updated (lower) stock
```

## Playwright Test Suite

**Test Files Created:**
- `tests/e2e/admin-flow/inventory-workflow.spec.ts` - Full E2E flow tests verifying all bug fixes
- `tests/e2e/admin-flow/api-tests.spec.ts` - Isolated API unit tests
- `tests/e2e/fixtures/test-data.ts` - Shared test data and constants

**Run Tests:**
```bash
# Run all E2E tests
npx playwright test

# Run only inventory workflow tests
npx playwright test inventory-workflow

# Run only API tests (faster, no browser)
npx playwright test api-tests

# Run with UI for debugging
npx playwright test --ui

# Run specific test file
npx playwright test tests/e2e/admin-flow/inventory-workflow.spec.ts

# Show test report
npx playwright show-report tests/e2e/reports
```

**What Tests Verify:**
- Bug #1: `pass_qc` response has no `materials_consumed` field
- Bug #2: Material products have `Inventory` records after BOM link
- Bug #3: `complete_print` creates FG inventory for MTO products
- Bug #4: `complete_print` response includes `material_inventory_synced: true`
- Bug #5: `start_production` response includes `materials_synced` array
- No negative inventory quantities
- MaterialInventory `in_stock` flag matches quantity

---

## Change Log

| Date | Item | Status | Notes |
|------|------|--------|-------|
| 2024-12-01 02:30 | Bug #1: Double consumption | ✅ FIXED | Removed consumption logic from pass_qc() |
| 2024-12-01 02:45 | Bug #3: MTO finished goods | ✅ FIXED | Create Inventory record if not exists in complete_print() |
| 2024-12-01 03:00 | Bug #4: MaterialInventory sync | ✅ FIXED | Decrement MaterialInventory.quantity_kg on consumption |
| 2024-12-01 03:15 | Bug #2: Inventory record creation | ✅ FIXED | Create Inventory in get_material_product_for_bom() |
| 2024-12-01 03:20 | Bug #5: Sync at production start | ✅ FIXED | Sync MaterialInventory → Inventory before BOM explosion |
| 2024-12-01 03:45 | Playwright Test Suite | ✅ ADDED | Created inventory-workflow.spec.ts and api-tests.spec.ts |

