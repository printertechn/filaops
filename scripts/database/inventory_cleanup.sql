-- ============================================================================
-- BLB3D ERP - Inventory Cleanup & Fresh Start
-- Generated: November 29, 2025
-- 
-- IMPORTANT: Run these in order. Each section can be run separately.
-- ============================================================================

-- ============================================================================
-- STEP 1: BACKUP (Run this first!)
-- ============================================================================
-- Export current data before deleting (run in SSMS, right-click results > Save As CSV)

-- Backup products
SELECT * FROM products;

-- Backup inventory  
SELECT * FROM inventory;

-- Backup material_inventory
SELECT * FROM material_inventory;

-- ============================================================================
-- STEP 2: CLEAR OLD INVENTORY DATA
-- ============================================================================
-- This removes the messy data but keeps material system tables intact

-- Clear inventory table (depends on products)
DELETE FROM inventory;

-- Clear products table (but keep material-related products if any are linked)
-- First, unlink material_inventory from products
UPDATE material_inventory SET product_id = NULL;

-- Now safe to delete products
DELETE FROM products;

-- Reset identity seeds
DBCC CHECKIDENT ('inventory', RESEED, 0);
DBCC CHECKIDENT ('products', RESEED, 0);

PRINT 'Old inventory and products cleared.';

-- ============================================================================
-- STEP 3: UPDATE MATERIAL INVENTORY QUANTITIES
-- ============================================================================
-- Set all existing material_inventory entries to 1000g (1kg) and in_stock = 1

UPDATE material_inventory 
SET quantity_kg = 1.000,
    in_stock = 1,
    updated_at = GETDATE();

PRINT 'Material inventory updated to 1000g each.';

-- Verify material inventory
SELECT 
    mi.sku,
    mt.name as material_type,
    c.name as color,
    mi.quantity_kg,
    mi.in_stock
FROM material_inventory mi
JOIN material_types mt ON mt.id = mi.material_type_id
JOIN colors c ON c.id = mi.color_id
ORDER BY mt.display_order, c.name;

-- ============================================================================
-- STEP 4: INSERT MACHINE PARTS
-- ============================================================================

INSERT INTO products (sku, name, description, category, unit, active, created_at, updated_at)
VALUES
('MP-A1-HOTEND-02', 'A1 Hotend (0.2mm)', 'Bambu A1 series hotend - 0.2mm nozzle', 'Machine Parts', 'EA', 1, GETDATE(), GETDATE()),
('MP-A1-HOTEND-04', 'A1 Hotend (0.4mm)', 'Bambu A1 series hotend - 0.4mm nozzle', 'Machine Parts', 'EA', 1, GETDATE(), GETDATE()),
('MP-A1-HOTEND-06', 'A1 Hotend (0.6mm)', 'Bambu A1 series hotend - 0.6mm nozzle', 'Machine Parts', 'EA', 1, GETDATE(), GETDATE()),
('MP-A1-FILHUB', 'AMS lite Filament Hub', 'Filament hub for AMS lite', 'Machine Parts', 'EA', 1, GETDATE(), GETDATE()),
('MP-A1-COOLPLATE', 'Bambu Cool Plate SuperTack', 'Build plate for A1 series', 'Machine Parts', 'EA', 1, GETDATE(), GETDATE()),
('MP-A1-EXTRUDER', 'Extruder Unit - A1 Series', 'Complete extruder assembly', 'Machine Parts', 'EA', 1, GETDATE(), GETDATE()),
('MP-A1-FILSENSOR', 'Filament Sensor A1 Series', 'Filament runout sensor', 'Machine Parts', 'EA', 1, GETDATE(), GETDATE()),
('MP-A1-EXTRGEAR', 'Hardened Steel Extruder Gear Assembly - A1 Series', 'Upgraded extruder gears', 'Machine Parts', 'EA', 1, GETDATE(), GETDATE()),
('MP-A1-HOTENDASM', 'Hotend Heating Assembly - A1 Series', 'Heating block assembly', 'Machine Parts', 'EA', 1, GETDATE(), GETDATE()),
('MP-A1-SILSOCK', 'Hotend Silicone Sock for A1', 'Thermal insulation sock', 'Machine Parts', 'EA', 1, GETDATE(), GETDATE()),
('MP-A1-SCREWKIT', 'Screws Kit - A1 Series and AMS lite', 'Replacement screws kit', 'Machine Parts', 'EA', 1, GETDATE(), GETDATE()),
('MP-ENDER3-HOTEND', 'Creality Ender 3 V3 Hotend', 'Replacement hotend for Ender 3 V3', 'Machine Parts', 'EA', 1, GETDATE(), GETDATE());

PRINT 'Machine Parts products inserted.';

-- ============================================================================
-- STEP 5: INSERT PACKAGING
-- ============================================================================

INSERT INTO products (sku, name, description, category, unit, active, created_at, updated_at)
VALUES
('PKG-BOX-12x9x4', '12x9x4 Black Shipping Box', 'Black corrugated shipping box', 'Packaging', 'EA', 1, GETDATE(), GETDATE()),
('PKG-BOX-9x6x4', '9x6x4 Black Shipping Box', 'Black corrugated shipping box', 'Packaging', 'EA', 1, GETDATE(), GETDATE()),
('PKG-BOX-4x4x4', '4x4x4 Cube Box', 'Cube shipping box', 'Packaging', 'EA', 1, GETDATE(), GETDATE()),
('PKG-BOX-5x5x5', '5x5x5 Cube Box', 'Cube shipping box', 'Packaging', 'EA', 1, GETDATE(), GETDATE()),
('PKG-BOX-6x6x6', '6x6x6 Cube Box', 'Cube shipping box', 'Packaging', 'EA', 1, GETDATE(), GETDATE()),
('PKG-BOX-7x7x7', '7x7x7 Box', 'Shipping box', 'Packaging', 'EA', 1, GETDATE(), GETDATE()),
('PKG-BOX-8x8x14', '8x8x14 Box', 'Tall shipping box', 'Packaging', 'EA', 1, GETDATE(), GETDATE()),
('PKG-PADS-8x8', '8 x 8" 150 lb Corrugated Pads', 'Corrugated padding', 'Packaging', 'EA', 1, GETDATE(), GETDATE()),
('PKG-TAPE-2ROLL', '2-Roll Tape Starter Pack - 2" x 55 yds', 'Packing tape', 'Packaging', 'EA', 1, GETDATE(), GETDATE()),
('PKG-HONEYCOMB', 'Honeycomb Packaging Paper', 'Eco-friendly packing material', 'Packaging', 'EA', 1, GETDATE(), GETDATE()),
('PKG-MESH-3x4', 'Sheer Mesh Drawstring Bags 3 x 4 Inch', 'Small product bags', 'Packaging', 'EA', 1, GETDATE(), GETDATE()),
('PKG-MESH-6x9', 'Sheer Mesh Drawstring Bags 6 x 9 Inch', 'Large product bags', 'Packaging', 'EA', 1, GETDATE(), GETDATE());

PRINT 'Packaging products inserted.';

-- ============================================================================
-- STEP 6: INSERT COMPONENTS
-- ============================================================================

INSERT INTO products (sku, name, description, category, unit, active, created_at, updated_at)
VALUES
('COMP-KEYRING', 'Keychain with Ring', 'Metal keychain ring hardware', 'Components', 'EA', 1, GETDATE(), GETDATE()),
('COMP-LED-SCREEN', 'LED Screen', 'LED display screen', 'Components', 'EA', 1, GETDATE(), GETDATE()),
('COMP-TEALIGHT', 'AGPTEK Timer Flickering Tea Lights', 'Battery-powered tea lights', 'Components', 'EA', 1, GETDATE(), GETDATE()),
('COMP-LEDKIT-001', 'LED Lamp Kit 001', 'LED lighting kit for lamp products', 'Components', 'EA', 1, GETDATE(), GETDATE()),
('COMP-DRAWER-22', 'LONTAN Soft Close Drawer Slides 22 Inch', 'Drawer slide hardware', 'Components', 'EA', 1, GETDATE(), GETDATE()),
('COMP-M3-12MM', 'M3 x 12mm Hex Socket Head Cap Screw', 'M3 hardware screws', 'Components', 'EA', 1, GETDATE(), GETDATE()),
('COMP-M3-INSERT', 'M3 Threaded Insert', 'Heat-set threaded inserts', 'Components', 'EA', 1, GETDATE(), GETDATE());

PRINT 'Components products inserted.';

-- ============================================================================
-- STEP 7: INSERT CONSUMABLES
-- ============================================================================

INSERT INTO products (sku, name, description, category, unit, active, created_at, updated_at)
VALUES
('CON-PVA', 'PVA Support Material', 'Water-soluble support filament', 'Consumables', 'g', 1, GETDATE(), GETDATE()),
('CON-LUBE-A1', 'Lubricant Grease and Oil - A1 Series', 'Printer maintenance lubricant', 'Consumables', 'EA', 1, GETDATE(), GETDATE());

PRINT 'Consumables products inserted.';

-- ============================================================================
-- STEP 8: INSERT INVENTORY RECORDS
-- ============================================================================
-- Link products to inventory with on-hand quantities

-- Machine Parts inventory
INSERT INTO inventory (product_id, location_id, on_hand_quantity, allocated_quantity, available_quantity)
SELECT id, 1, 
    CASE sku
        WHEN 'MP-A1-HOTEND-02' THEN 4
        WHEN 'MP-A1-HOTEND-04' THEN 4
        WHEN 'MP-A1-HOTEND-06' THEN 5
        WHEN 'MP-A1-FILHUB' THEN 1
        WHEN 'MP-A1-COOLPLATE' THEN 5
        WHEN 'MP-A1-EXTRUDER' THEN 1
        WHEN 'MP-A1-FILSENSOR' THEN 1
        WHEN 'MP-A1-EXTRGEAR' THEN 1
        WHEN 'MP-A1-HOTENDASM' THEN 1
        WHEN 'MP-A1-SILSOCK' THEN 2
        WHEN 'MP-A1-SCREWKIT' THEN 1
        WHEN 'MP-ENDER3-HOTEND' THEN 1
        ELSE 0
    END,
    0,
    CASE sku
        WHEN 'MP-A1-HOTEND-02' THEN 4
        WHEN 'MP-A1-HOTEND-04' THEN 4
        WHEN 'MP-A1-HOTEND-06' THEN 5
        WHEN 'MP-A1-FILHUB' THEN 1
        WHEN 'MP-A1-COOLPLATE' THEN 5
        WHEN 'MP-A1-EXTRUDER' THEN 1
        WHEN 'MP-A1-FILSENSOR' THEN 1
        WHEN 'MP-A1-EXTRGEAR' THEN 1
        WHEN 'MP-A1-HOTENDASM' THEN 1
        WHEN 'MP-A1-SILSOCK' THEN 2
        WHEN 'MP-A1-SCREWKIT' THEN 1
        WHEN 'MP-ENDER3-HOTEND' THEN 1
        ELSE 0
    END
FROM products WHERE category = 'Machine Parts';

-- Packaging inventory
INSERT INTO inventory (product_id, location_id, on_hand_quantity, allocated_quantity, available_quantity)
SELECT id, 1,
    CASE sku
        WHEN 'PKG-BOX-12x9x4' THEN 20
        WHEN 'PKG-BOX-9x6x4' THEN 29
        WHEN 'PKG-BOX-4x4x4' THEN 46
        WHEN 'PKG-BOX-5x5x5' THEN 23
        WHEN 'PKG-BOX-6x6x6' THEN 13
        WHEN 'PKG-BOX-7x7x7' THEN 23
        WHEN 'PKG-BOX-8x8x14' THEN 24
        WHEN 'PKG-PADS-8x8' THEN 100
        WHEN 'PKG-TAPE-2ROLL' THEN 1
        WHEN 'PKG-HONEYCOMB' THEN 200
        WHEN 'PKG-MESH-3x4' THEN 100
        WHEN 'PKG-MESH-6x9' THEN 100
        ELSE 0
    END,
    0,
    CASE sku
        WHEN 'PKG-BOX-12x9x4' THEN 20
        WHEN 'PKG-BOX-9x6x4' THEN 29
        WHEN 'PKG-BOX-4x4x4' THEN 46
        WHEN 'PKG-BOX-5x5x5' THEN 23
        WHEN 'PKG-BOX-6x6x6' THEN 13
        WHEN 'PKG-BOX-7x7x7' THEN 23
        WHEN 'PKG-BOX-8x8x14' THEN 24
        WHEN 'PKG-PADS-8x8' THEN 100
        WHEN 'PKG-TAPE-2ROLL' THEN 1
        WHEN 'PKG-HONEYCOMB' THEN 200
        WHEN 'PKG-MESH-3x4' THEN 100
        WHEN 'PKG-MESH-6x9' THEN 100
        ELSE 0
    END
FROM products WHERE category = 'Packaging';

-- Components inventory
INSERT INTO inventory (product_id, location_id, on_hand_quantity, allocated_quantity, available_quantity)
SELECT id, 1,
    CASE sku
        WHEN 'COMP-KEYRING' THEN 9
        WHEN 'COMP-LED-SCREEN' THEN 2
        WHEN 'COMP-TEALIGHT' THEN 15
        WHEN 'COMP-LEDKIT-001' THEN 1
        WHEN 'COMP-DRAWER-22' THEN 2
        WHEN 'COMP-M3-12MM' THEN 100
        WHEN 'COMP-M3-INSERT' THEN 200
        ELSE 0
    END,
    0,
    CASE sku
        WHEN 'COMP-KEYRING' THEN 9
        WHEN 'COMP-LED-SCREEN' THEN 2
        WHEN 'COMP-TEALIGHT' THEN 15
        WHEN 'COMP-LEDKIT-001' THEN 1
        WHEN 'COMP-DRAWER-22' THEN 2
        WHEN 'COMP-M3-12MM' THEN 100
        WHEN 'COMP-M3-INSERT' THEN 200
        ELSE 0
    END
FROM products WHERE category = 'Components';

-- Consumables inventory
INSERT INTO inventory (product_id, location_id, on_hand_quantity, allocated_quantity, available_quantity)
SELECT id, 1,
    CASE sku
        WHEN 'CON-PVA' THEN 328
        WHEN 'CON-LUBE-A1' THEN 1
        ELSE 0
    END,
    0,
    CASE sku
        WHEN 'CON-PVA' THEN 328
        WHEN 'CON-LUBE-A1' THEN 1
        ELSE 0
    END
FROM products WHERE category = 'Consumables';

PRINT 'Inventory records inserted.';

-- ============================================================================
-- STEP 9: VERIFY RESULTS
-- ============================================================================

-- Count by category
SELECT 'Products by Category' as report;
SELECT category, COUNT(*) as count 
FROM products 
GROUP BY category 
ORDER BY category;

-- Total inventory value check
SELECT 'Inventory Summary' as report;
SELECT 
    p.category,
    COUNT(*) as items,
    SUM(i.on_hand_quantity) as total_on_hand
FROM inventory i
JOIN products p ON p.id = i.product_id
GROUP BY p.category
ORDER BY p.category;

-- Material inventory check
SELECT 'Material Inventory Summary' as report;
SELECT 
    mt.base_material,
    COUNT(*) as colors,
    SUM(mi.quantity_kg) as total_kg
FROM material_inventory mi
JOIN material_types mt ON mt.id = mi.material_type_id
GROUP BY mt.base_material
ORDER BY mt.base_material;

PRINT '=== CLEANUP COMPLETE ===';
PRINT 'Products: 33 items (Machine Parts, Packaging, Components, Consumables)';
PRINT 'Material Inventory: 78 items @ 1kg each';
PRINT 'Total: 111 clean inventory items';
