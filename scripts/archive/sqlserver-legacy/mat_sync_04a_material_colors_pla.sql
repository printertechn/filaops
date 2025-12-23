-- ============================================================================
-- MATERIAL CATALOG SYNC - STEP 4: INSERT MATERIAL_COLORS
-- Run after Step 3
-- Links material types to their available colors
-- ============================================================================

-- PLA MATTE (25 colors)
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Charcoal';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Dark Red';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Ash Grey';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Ivory White';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Dark Blue';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Dark Brown';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Latte Brown';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Sakura Pink';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Lemon Yellow';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Dark Green';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Mandarin Orange';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Grass Green';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Desert Tan';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Ice Blue';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Lilac Purple';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Marine Blue';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Scarlet Red';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Bone White';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Caramel';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Terracotta';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Dark Chocolate';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Plum';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Apple Green';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Sky Blue';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_MATTE' AND c.name = 'Nardo Gray';

PRINT 'PLA_MATTE: 25 colors added';

-- PLA BASIC (30 colors)
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Jade White';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Magenta';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Gold';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Mistletoe Green';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Red';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Beige';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Pink';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Sunflower Yellow';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Bronze';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Light Gray';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Hot Pink';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Yellow';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Silver';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Orange';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Gray';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Pumpkin Orange';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Bright Green';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Cocoa Brown';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Turquoise';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Purple';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Indigo Purple';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Cyan';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Blue Grey';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Brown';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Blue';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Dark Gray';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Bambu Green';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Maroon Red';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Cobalt Blue';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_BASIC' AND c.name = 'Black';

PRINT 'PLA_BASIC: 30 colors added';

-- PLA SILK (13 colors)
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK' AND c.name = 'Gold';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK' AND c.name = 'Silver';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK' AND c.name = 'Titan Gray';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK' AND c.name = 'Blue';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK' AND c.name = 'Purple';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK' AND c.name = 'Candy Red';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK' AND c.name = 'Candy Green';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK' AND c.name = 'Rose Gold';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK' AND c.name = 'Baby Blue';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK' AND c.name = 'Pink';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK' AND c.name = 'Mint';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK' AND c.name = 'Champagne';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK' AND c.name = 'White';

PRINT 'PLA_SILK: 13 colors added';

-- PLA SILK MULTI (10 colors)
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK_MULTI' AND c.name = 'Mystic Magenta';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK_MULTI' AND c.name = 'Phantom Blue';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK_MULTI' AND c.name = 'Velvet Eclipse';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK_MULTI' AND c.name = 'Midnight Blaze';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK_MULTI' AND c.name = 'Gilded Rose';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK_MULTI' AND c.name = 'Blue Hawaii';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK_MULTI' AND c.name = 'Neon City';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK_MULTI' AND c.name = 'Aurora Purple';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK_MULTI' AND c.name = 'South Beach';
INSERT INTO material_colors (material_type_id, color_id) SELECT mt.id, c.id FROM material_types mt, colors c WHERE mt.name = 'PLA_SILK_MULTI' AND c.name = 'Dawn Radiance';

PRINT 'PLA_SILK_MULTI: 10 colors added';

-- Verify PLA counts
SELECT mt.name, COUNT(*) as ColorCount 
FROM material_colors mc
JOIN material_types mt ON mc.material_type_id = mt.id
WHERE mt.name LIKE 'PLA%'
GROUP BY mt.name;
