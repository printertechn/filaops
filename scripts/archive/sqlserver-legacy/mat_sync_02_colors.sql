-- ============================================================================
-- MATERIAL CATALOG SYNC - STEP 2: ADD NEW COLORS
-- Run after Step 1
-- Colors table uses: code, name, hex_code, hex_code_secondary
-- ============================================================================

-- Add colors that may not exist yet (for PETG, ABS, ASA, TPU)
-- Using code as the unique identifier

-- PETG-HF specific colors
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'CREAM') INSERT INTO colors (code, name, hex_code, active) VALUES ('CREAM', 'Cream', '#F9DFB9', 1);
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'LIMGRN') INSERT INTO colors (code, name, hex_code, active) VALUES ('LIMGRN', 'Lime Green', '#6EE53C', 1);
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'FORGRN') INSERT INTO colors (code, name, hex_code, active) VALUES ('FORGRN', 'Forest Green', '#39541A', 1);
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'LAKBLU') INSERT INTO colors (code, name, hex_code, active) VALUES ('LAKBLU', 'Lake Blue', '#1F79E5', 1);
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'PNTBRN') INSERT INTO colors (code, name, hex_code, active) VALUES ('PNTBRN', 'Peanut Brown', '#875718', 1);

-- PETG Translucent colors
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'TRGRY') INSERT INTO colors (code, name, hex_code, active) VALUES ('TRGRY', 'Translucent Gray', '#8E8E8E', 1);
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'TRLTBLU') INSERT INTO colors (code, name, hex_code, active) VALUES ('TRLTBLU', 'Translucent Light Blue', '#61B0FF', 1);
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'TROLV') INSERT INTO colors (code, name, hex_code, active) VALUES ('TROLV', 'Translucent Olive', '#748C45', 1);
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'TRBRN') INSERT INTO colors (code, name, hex_code, active) VALUES ('TRBRN', 'Translucent Brown', '#C9A381', 1);
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'TRTEAL') INSERT INTO colors (code, name, hex_code, active) VALUES ('TRTEAL', 'Translucent Teal', '#77EDD7', 1);
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'TRORG') INSERT INTO colors (code, name, hex_code, active) VALUES ('TRORG', 'Translucent Orange', '#FF911A', 1);
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'TRPUR') INSERT INTO colors (code, name, hex_code, active) VALUES ('TRPUR', 'Translucent Purple', '#D6ABFF', 1);
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'TRPNK') INSERT INTO colors (code, name, hex_code, active) VALUES ('TRPNK', 'Translucent Pink', '#F9C1BD', 1);

-- PETG-CF colors
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'BRKRED') INSERT INTO colors (code, name, hex_code, active) VALUES ('BRKRED', 'Brick Red', '#9F332A', 1);
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'VIOPUR') INSERT INTO colors (code, name, hex_code, active) VALUES ('VIOPUR', 'Violet Purple', '#583061', 1);
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'INDBLU') INSERT INTO colors (code, name, hex_code, active) VALUES ('INDBLU', 'Indigo Blue', '#324585', 1);
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'MALGRN') INSERT INTO colors (code, name, hex_code, active) VALUES ('MALGRN', 'Malachita Green', '#16B08E', 1);

-- ABS colors
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'OLIVE') INSERT INTO colors (code, name, hex_code, active) VALUES ('OLIVE', 'Olive', '#789D4A', 1);
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'TANYEL') INSERT INTO colors (code, name, hex_code, active) VALUES ('TANYEL', 'Tangerine Yellow', '#FFC72C', 1);
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'AZURE') INSERT INTO colors (code, name, hex_code, active) VALUES ('AZURE', 'Azure', '#489FDF', 1);
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'NAVBLU') INSERT INTO colors (code, name, hex_code, active) VALUES ('NAVBLU', 'Navy Blue', '#0C2340', 1);

-- TPU colors
IF NOT EXISTS (SELECT 1 FROM colors WHERE code = 'NEOGRN') INSERT INTO colors (code, name, hex_code, active) VALUES ('NEOGRN', 'Neon Green', '#90FF1A', 1);

-- Verify colors added
SELECT COUNT(*) as TotalColors FROM colors;
SELECT code, name, hex_code FROM colors ORDER BY code;
