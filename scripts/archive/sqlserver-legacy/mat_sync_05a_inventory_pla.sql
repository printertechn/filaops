-- ============================================================================
-- MATERIAL CATALOG SYNC - STEP 5: INSERT MATERIAL_INVENTORY (PLA)
-- Run after Step 4B
-- Inserts inventory records with new SKU format
-- ============================================================================

-- PLA MATTE (25)
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-CHAR', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Charcoal';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-DKRED', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Dark Red';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-ASHGRY', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Ash Grey';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-IVWHT', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Ivory White';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-DKBLU', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Dark Blue';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-DKBRN', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Dark Brown';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-LATBRN', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Latte Brown';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-SAKPNK', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Sakura Pink';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-LEMYEL', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Lemon Yellow';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-DKGRN', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Dark Green';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-MNDORG', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Mandarin Orange';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-GRSGRN', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Grass Green';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-DESTAN', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Desert Tan';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-ICEBLU', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Ice Blue';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-LILPUR', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Lilac Purple';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-MARBLU', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Marine Blue';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-SCARED', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Scarlet Red';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-BNWHT', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Bone White';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-CARM', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Caramel';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-TERRA', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Terracotta';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-DKCHOC', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Dark Chocolate';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-PLUM', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Plum';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-APPGRN', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Apple Green';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-SKYBLU', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Sky Blue';

INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location)
SELECT mc.id, 'MAT-FDM-PLA_MATTE-NRDGRY', 1.0, 1, 'Main Warehouse'
FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id
WHERE mt.name = 'PLA_MATTE' AND c.name = 'Nardo Gray';

PRINT 'PLA_MATTE inventory: 25 items';

-- PLA BASIC (30)
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-JADWHT', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Jade White';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-MAG', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Magenta';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-GLD', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Gold';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-MSTGRN', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Mistletoe Green';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-RED', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Red';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-BEIGE', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Beige';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-PNK', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Pink';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-SUNYEL', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Sunflower Yellow';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-BRNZ', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Bronze';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-LTGRY', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Light Gray';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-HTPNK', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Hot Pink';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-YEL', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Yellow';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-SLV', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Silver';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-ORG', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Orange';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-GRY', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Gray';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-PMPORG', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Pumpkin Orange';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-BRTGRN', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Bright Green';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-COCBRN', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Cocoa Brown';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-TURQ', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Turquoise';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-PUR', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Purple';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-INDPUR', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Indigo Purple';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-CYN', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Cyan';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-BLUGRY', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Blue Grey';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-BRN', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Brown';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-BLU', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Blue';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-DKGRY', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Dark Gray';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-BAMGRN', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Bambu Green';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-MARRED', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Maroon Red';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-COBBLU', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Cobalt Blue';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_BASIC-BLK', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_BASIC' AND c.name = 'Black';

PRINT 'PLA_BASIC inventory: 30 items';

-- PLA SILK (13)
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK-GLD', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK' AND c.name = 'Gold';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK-SLV', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK' AND c.name = 'Silver';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK-TITGRY', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK' AND c.name = 'Titan Gray';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK-BLU', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK' AND c.name = 'Blue';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK-PUR', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK' AND c.name = 'Purple';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK-CNDRED', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK' AND c.name = 'Candy Red';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK-CNDGRN', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK' AND c.name = 'Candy Green';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK-RSGLD', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK' AND c.name = 'Rose Gold';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK-BBYBLU', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK' AND c.name = 'Baby Blue';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK-PNK', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK' AND c.name = 'Pink';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK-MINT', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK' AND c.name = 'Mint';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK-CHAMP', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK' AND c.name = 'Champagne';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK-WHT', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK' AND c.name = 'White';

PRINT 'PLA_SILK inventory: 13 items';

-- PLA SILK MULTI (10)
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK_MULTI-MYSTMAG', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK_MULTI' AND c.name = 'Mystic Magenta';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK_MULTI-PHANBLU', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK_MULTI' AND c.name = 'Phantom Blue';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK_MULTI-VELECL', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK_MULTI' AND c.name = 'Velvet Eclipse';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK_MULTI-MIDBLZ', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK_MULTI' AND c.name = 'Midnight Blaze';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK_MULTI-GLDROS', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK_MULTI' AND c.name = 'Gilded Rose';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK_MULTI-BLUHAW', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK_MULTI' AND c.name = 'Blue Hawaii';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK_MULTI-NEOCTY', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK_MULTI' AND c.name = 'Neon City';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK_MULTI-AURPUR', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK_MULTI' AND c.name = 'Aurora Purple';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK_MULTI-SOBCH', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK_MULTI' AND c.name = 'South Beach';
INSERT INTO material_inventory (material_color_id, sku, quantity_kg, in_stock, location) SELECT mc.id, 'MAT-FDM-PLA_SILK_MULTI-DWNRAD', 1.0, 1, 'Main Warehouse' FROM material_colors mc JOIN material_types mt ON mc.material_type_id = mt.id JOIN colors c ON mc.color_id = c.id WHERE mt.name = 'PLA_SILK_MULTI' AND c.name = 'Dawn Radiance';

PRINT 'PLA_SILK_MULTI inventory: 10 items';

-- Check PLA inventory counts
SELECT 'PLA Inventory Summary' as Report;
SELECT mt.name, COUNT(*) as Items FROM material_inventory mi
JOIN material_colors mc ON mi.material_color_id = mc.id
JOIN material_types mt ON mc.material_type_id = mt.id
WHERE mt.name LIKE 'PLA%'
GROUP BY mt.name;
