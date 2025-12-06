-- ============================================================================
-- MATERIAL CATALOG SYNC - STEP 3: CLEAR EXISTING DATA
-- Run after Step 2
-- WARNING: This deletes all material_inventory and material_colors!
-- ============================================================================

-- Check current counts before deleting
SELECT 'BEFORE DELETE' as Status;
SELECT 'material_inventory' as TableName, COUNT(*) as RowCount FROM material_inventory
UNION ALL
SELECT 'material_colors', COUNT(*) FROM material_colors;

-- Clear tables (material_inventory first since it may reference material_colors)
DELETE FROM material_inventory;
DELETE FROM material_colors;

-- Verify deletion
SELECT 'AFTER DELETE' as Status;
SELECT 'material_inventory' as TableName, COUNT(*) as RowCount FROM material_inventory
UNION ALL
SELECT 'material_colors', COUNT(*) FROM material_colors;

PRINT 'Cleared material_colors and material_inventory tables';
