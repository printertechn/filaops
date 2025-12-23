-- ============================================================================
-- MATERIAL CATALOG SYNC - STEP 4B: INSERT MATERIAL_COLORS (PETG/ABS/ASA/TPU)
-- Run after Step 4A
-- ============================================================================

-- PETG-HF (14 colors)
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_HF' AND c.name = 'Yellow';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_HF' AND c.name = 'Orange';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_HF' AND c.name = 'Green';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_HF' AND c.name = 'Red';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_HF' AND c.name = 'Blue';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_HF' AND c.name = 'Black';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_HF' AND c.name = 'White';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_HF' AND c.name = 'Cream';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_HF' AND c.name = 'Lime Green';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_HF' AND c.name = 'Forest Green';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_HF' AND c.name = 'Lake Blue';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_HF' AND c.name = 'Peanut Brown';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_HF' AND c.name = 'Gray';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_HF' AND c.name = 'Dark Gray';

PRINT 'PETG_HF: 14 colors added';

-- PETG TRANSLUCENT (8 colors)
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_TRANS' AND c.name = 'Translucent Gray';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_TRANS' AND c.name = 'Translucent Light Blue';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_TRANS' AND c.name = 'Translucent Olive';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_TRANS' AND c.name = 'Translucent Brown';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_TRANS' AND c.name = 'Translucent Teal';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_TRANS' AND c.name = 'Translucent Orange';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_TRANS' AND c.name = 'Translucent Purple';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_TRANS' AND c.name = 'Translucent Pink';

PRINT 'PETG_TRANS: 8 colors added';

-- PETG-CF Carbon Fiber (6 colors)
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_CF' AND c.name = 'Brick Red';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_CF' AND c.name = 'Violet Purple';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_CF' AND c.name = 'Indigo Blue';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_CF' AND c.name = 'Malachita Green';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_CF' AND c.name = 'Black';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PETG_CF' AND c.name = 'Titan Gray';

PRINT 'PETG_CF: 6 colors added';

-- ABS (12 colors)
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ABS' AND c.name = 'Olive';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ABS' AND c.name = 'Tangerine Yellow';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ABS' AND c.name = 'Azure';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ABS' AND c.name = 'Navy Blue';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ABS' AND c.name = 'White';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ABS' AND c.name = 'Silver';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ABS' AND c.name = 'Red';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ABS' AND c.name = 'Orange';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ABS' AND c.name = 'Bambu Green';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ABS' AND c.name = 'Blue';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ABS' AND c.name = 'Purple';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ABS' AND c.name = 'Black';

PRINT 'ABS: 12 colors added';

-- ABS-GF Glass Fiber (8 colors)
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ABS_GF' AND c.name = 'White';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ABS_GF' AND c.name = 'Gray';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ABS_GF' AND c.name = 'Yellow';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ABS_GF' AND c.name = 'Orange';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ABS_GF' AND c.name = 'Red';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ABS_GF' AND c.name = 'Green';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ABS_GF' AND c.name = 'Blue';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ABS_GF' AND c.name = 'Black';

PRINT 'ABS_GF: 8 colors added';

-- ASA (7 colors)
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ASA' AND c.name = 'White';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ASA' AND c.name = 'Gray';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ASA' AND c.name = 'Red';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ASA' AND c.name = 'Green';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ASA' AND c.name = 'Blue';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ASA' AND c.name = 'Black';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'ASA' AND c.name = 'Yellow';

PRINT 'ASA: 7 colors added';

-- TPU 68D (7 colors)
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'TPU_68D' AND c.name = 'Red';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'TPU_68D' AND c.name = 'Yellow';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'TPU_68D' AND c.name = 'Blue';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'TPU_68D' AND c.name = 'Neon Green';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'TPU_68D' AND c.name = 'White';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'TPU_68D' AND c.name = 'Gray';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'TPU_68D' AND c.name = 'Black';

PRINT 'TPU_68D: 7 colors added';

-- TPU 95A (6 colors)
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'TPU_95A' AND c.name = 'White';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'TPU_95A' AND c.name = 'Yellow';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'TPU_95A' AND c.name = 'Blue';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'TPU_95A' AND c.name = 'Red';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'TPU_95A' AND c.name = 'Gray';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'TPU_95A' AND c.name = 'Black';

PRINT 'TPU_95A: 6 colors added';

-- Verify all counts
SELECT mt.name as MaterialType, COUNT(*) as ColorCount 
FROM material_colors mc
JOIN material_types mt ON mc.material_type_id = mt.id
GROUP BY mt.name
ORDER BY mt.name;

SELECT 'Total material_colors' as Summary, COUNT(*) as Total FROM material_colors;
