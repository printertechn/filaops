-- ============================================================================
-- MATERIAL CATALOG SYNC - STEP 1: ADD NEW MATERIAL TYPES
-- Run this first to add PETG_CF and ABS_GF
-- Based on actual schema: material_types table
-- ============================================================================

-- Check existing types first
SELECT id, code, name, base_material, price_multiplier FROM material_types ORDER BY id;

-- Add PETG_CF (Carbon Fiber) if not exists
IF NOT EXISTS (SELECT 1 FROM material_types WHERE code = 'PETG_CF')
BEGIN
    INSERT INTO material_types (
        code, name, base_material, process_type, density,
        nozzle_temp_min, nozzle_temp_max, bed_temp_min, bed_temp_max,
        base_price_per_kg, price_multiplier, requires_enclosure,
        description, is_customer_visible, display_order, active
    )
    VALUES (
        'PETG_CF', 'PETG Carbon Fiber', 'PETG', 'FDM', 1.27,
        250, 270, 70, 80,
        28.79, 1.44, 0,
        'Carbon fiber reinforced PETG for high strength and stiffness', 1, 35, 1
    );
    PRINT 'Added PETG_CF material type';
END
ELSE
    PRINT 'PETG_CF already exists';

-- Add ABS_GF (Glass Fiber) if not exists
IF NOT EXISTS (SELECT 1 FROM material_types WHERE code = 'ABS_GF')
BEGIN
    INSERT INTO material_types (
        code, name, base_material, process_type, density,
        nozzle_temp_min, nozzle_temp_max, bed_temp_min, bed_temp_max,
        base_price_per_kg, price_multiplier, requires_enclosure,
        description, is_customer_visible, display_order, active
    )
    VALUES (
        'ABS_GF', 'ABS Glass Fiber', 'ABS', 'FDM', 1.15,
        240, 260, 90, 100,
        23.99, 1.20, 1,
        'Glass fiber reinforced ABS for improved stiffness and heat resistance', 1, 55, 1
    );
    PRINT 'Added ABS_GF material type';
END
ELSE
    PRINT 'ABS_GF already exists';

-- Verify material types
SELECT id, code, name, base_material, price_multiplier, base_price_per_kg 
FROM material_types 
ORDER BY code;
