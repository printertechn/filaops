-- ============================================================================
-- DIAGNOSTIC: Check current database state
-- Run this first to see what exists
-- ============================================================================

PRINT '=== MATERIAL TYPES ===';
SELECT id, code, name, base_material, price_multiplier, base_price_per_kg 
FROM material_types 
ORDER BY base_material, code;

PRINT '';
PRINT '=== COLORS ===';
SELECT id, code, name, hex_code
FROM colors 
ORDER BY code;

PRINT '';
PRINT '=== MATERIAL_COLORS (combinations) ===';
SELECT mc.id, mt.code as material_code, c.code as color_code, c.name as color_name
FROM material_colors mc
JOIN material_types mt ON mc.material_type_id = mt.id
JOIN colors c ON mc.color_id = c.id
ORDER BY mt.code, c.code;

PRINT '';
PRINT '=== MATERIAL_INVENTORY ===';
SELECT mi.id, mi.sku, mt.code as material_code, c.code as color_code, mi.quantity_kg, mi.in_stock
FROM material_inventory mi
JOIN material_types mt ON mi.material_type_id = mt.id
JOIN colors c ON mi.color_id = c.id
ORDER BY mi.sku;

PRINT '';
PRINT '=== COUNTS ===';
SELECT 'material_types' as TableName, COUNT(*) as RowCount FROM material_types
UNION ALL SELECT 'colors', COUNT(*) FROM colors
UNION ALL SELECT 'material_colors', COUNT(*) FROM material_colors
UNION ALL SELECT 'material_inventory', COUNT(*) FROM material_inventory;
