-- ============================================================================
-- MATERIAL CATALOG SYNC SCRIPT
-- Generated: 2025-11-29
-- Total Materials: 146 SKUs
-- ============================================================================

-- ============================================================================
-- STEP 1: ADD NEW MATERIAL TYPES
-- ============================================================================
-- Check existing types first
SELECT id, name, base_material, cost_multiplier FROM material_types ORDER BY id;

-- Add PETG_CF (Carbon Fiber) if not exists
IF NOT EXISTS (SELECT 1 FROM material_types WHERE name = 'PETG_CF')
BEGIN
    INSERT INTO material_types (name, base_material, density_g_cm3, cost_multiplier, print_temp_min, print_temp_max, bed_temp_min, bed_temp_max)
    VALUES ('PETG_CF', 'PETG', 1.27, 1.44, 250, 270, 70, 80);
    PRINT 'Added PETG_CF material type';
END

-- Add ABS_GF (Glass Fiber) if not exists
IF NOT EXISTS (SELECT 1 FROM material_types WHERE name = 'ABS_GF')
BEGIN
    INSERT INTO material_types (name, base_material, density_g_cm3, cost_multiplier, print_temp_min, print_temp_max, bed_temp_min, bed_temp_max)
    VALUES ('ABS_GF', 'ABS', 1.15, 1.20, 240, 260, 90, 100);
    PRINT 'Added ABS_GF material type';
END

-- Verify material types
SELECT id, name, base_material, cost_multiplier FROM material_types ORDER BY name;
