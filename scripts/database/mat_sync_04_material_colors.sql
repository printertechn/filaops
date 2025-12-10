-- ============================================================================
-- MATERIAL CATALOG SYNC - STEP 4: INSERT MATERIAL_COLORS (All materials)
-- Run after Step 3
-- Links material types to their available colors via code lookups
-- ============================================================================

-- First, let's see what material types and colors we have
SELECT id, code, name FROM material_types ORDER BY code;
SELECT id, code, name FROM colors ORDER BY code;

-- PLA MATTE (25 colors)
-- Using code-based lookups
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'CHAR';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'DKRED';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'ASHGRY';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'IVWHT';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'DKBLU';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'DKBRN';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'LATBRN';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'SAKPNK';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'LEMYEL';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'DKGRN';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'MNDORG';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'GRSGRN';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'DESTAN';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'ICEBLU';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'LILPUR';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'MARBLU';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'SCARED';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'BNWHT';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'CARM';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'TERRA';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'DKCHOC';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'PLUM';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'APPGRN';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'SKYBLU';
INSERT INTO material_colors (material_type_id, color_id, active)
SELECT mt.id, c.id, 1 FROM material_types mt, colors c WHERE mt.code = 'PLA_MATTE' AND c.code = 'NRDGRY';

PRINT 'PLA_MATTE: 25 color links created';

-- Check what was inserted (should show combinations)
SELECT 'PLA_MATTE colors inserted:' as Info, COUNT(*) as Total 
FROM material_colors mc 
JOIN material_types mt ON mc.material_type_id = mt.id 
WHERE mt.code = 'PLA_MATTE';
