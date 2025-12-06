-- ============================================================================
-- NUCLEAR OPTION: Drop all material tables and recreate from scratch
-- ============================================================================
-- This will delete all material data and recreate the tables properly
-- ============================================================================

USE BLB3D_ERP;
GO

PRINT '=== DROPPING ALL MATERIAL TABLES ===';
PRINT '';

-- Step 1: Drop material_inventory (has FK to both material_types and colors)
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[material_inventory]') AND type in (N'U'))
BEGIN
    DROP TABLE material_inventory;
    PRINT 'Dropped material_inventory';
END
GO

-- Step 2: Drop material_colors (has FK to both material_types and colors)
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[material_colors]') AND type in (N'U'))
BEGIN
    DROP TABLE material_colors;
    PRINT 'Dropped material_colors';
END
GO

-- Step 3: Drop colors (no dependencies now)
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[colors]') AND type in (N'U'))
BEGIN
    DROP TABLE colors;
    PRINT 'Dropped colors';
END
GO

-- Step 4: Drop material_types (no dependencies now)
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[material_types]') AND type in (N'U'))
BEGIN
    DROP TABLE material_types;
    PRINT 'Dropped material_types';
END
GO

PRINT '';
PRINT '=== RECREATING ALL MATERIAL TABLES ===';
PRINT '';

-- ============================================================================
-- MATERIAL TYPES
-- ============================================================================
CREATE TABLE material_types (
    id INT IDENTITY(1,1) PRIMARY KEY,

    -- Identification
    code NVARCHAR(50) NOT NULL,
    name NVARCHAR(100) NOT NULL,

    -- Base material category (for print settings)
    base_material NVARCHAR(20) NOT NULL,  -- PLA, PETG, ABS, ASA, TPU

    -- Process type (for future expansion)
    process_type NVARCHAR(20) NOT NULL DEFAULT 'FDM',  -- FDM, SLA, SLS

    -- Physical properties
    density DECIMAL(6,4) NOT NULL,  -- g/cm3

    -- Print settings
    volumetric_flow_limit DECIMAL(6,2) NULL,  -- mm3/s
    nozzle_temp_min INT NULL,
    nozzle_temp_max INT NULL,
    bed_temp_min INT NULL,
    bed_temp_max INT NULL,
    requires_enclosure BIT DEFAULT 0,

    -- Pricing
    base_price_per_kg DECIMAL(10,2) NOT NULL,
    price_multiplier DECIMAL(4,2) DEFAULT 1.0,

    -- Customer-facing
    description NVARCHAR(MAX) NULL,
    strength_rating INT NULL,  -- 1-10
    is_customer_visible BIT DEFAULT 1,
    display_order INT DEFAULT 100,

    -- Status
    active BIT DEFAULT 1,

    -- Timestamps
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE(),

    -- Constraints
    CONSTRAINT UQ_material_types_code UNIQUE (code)
);

CREATE INDEX IX_material_types_base_material ON material_types(base_material);
CREATE INDEX IX_material_types_active ON material_types(active, is_customer_visible);

PRINT 'Created material_types';
GO

-- ============================================================================
-- COLORS
-- ============================================================================
CREATE TABLE colors (
    id INT IDENTITY(1,1) PRIMARY KEY,

    -- Identification
    code NVARCHAR(30) NOT NULL,
    name NVARCHAR(100) NOT NULL,

    -- Display
    hex_code NVARCHAR(7) NULL,  -- #000000
    hex_code_secondary NVARCHAR(7) NULL,  -- For dual-color silks

    -- Customer-facing
    display_order INT DEFAULT 100,
    is_customer_visible BIT DEFAULT 1,

    -- Status
    active BIT DEFAULT 1,

    -- Timestamps
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE(),

    -- Constraints
    CONSTRAINT UQ_colors_code UNIQUE (code)
);

CREATE INDEX IX_colors_active ON colors(active, is_customer_visible);

PRINT 'Created colors';
GO

-- ============================================================================
-- MATERIAL_COLORS (Junction Table)
-- ============================================================================
CREATE TABLE material_colors (
    id INT IDENTITY(1,1) PRIMARY KEY,

    -- Foreign keys
    material_type_id INT NOT NULL,
    color_id INT NOT NULL,

    -- This specific combination
    is_customer_visible BIT DEFAULT 1,
    display_order INT DEFAULT 100,

    -- Status
    active BIT DEFAULT 1,

    -- Constraints
    CONSTRAINT FK_material_colors_material_type FOREIGN KEY (material_type_id)
        REFERENCES material_types(id) ON DELETE CASCADE,
    CONSTRAINT FK_material_colors_color FOREIGN KEY (color_id)
        REFERENCES colors(id) ON DELETE CASCADE,
    CONSTRAINT UQ_material_colors UNIQUE (material_type_id, color_id)
);

CREATE INDEX IX_material_colors_lookup ON material_colors(material_type_id, color_id);
CREATE INDEX IX_material_colors_active ON material_colors(active, is_customer_visible);

PRINT 'Created material_colors';
GO

-- ============================================================================
-- MATERIAL_INVENTORY
-- ============================================================================
CREATE TABLE material_inventory (
    id INT IDENTITY(1,1) PRIMARY KEY,

    -- Material specification
    material_type_id INT NOT NULL,
    color_id INT NOT NULL,

    -- Link to Product table (for BOM, inventory tracking)
    product_id INT NULL,

    -- Direct SKU reference
    sku NVARCHAR(50) NOT NULL,

    -- Inventory status
    in_stock BIT DEFAULT 1,
    quantity_kg DECIMAL(10,3) DEFAULT 0,
    reorder_point_kg DECIMAL(10,3) DEFAULT 1.0,

    -- Costing
    cost_per_kg DECIMAL(10,2) NULL,
    last_purchase_date DATETIME2 NULL,
    last_purchase_price DECIMAL(10,2) NULL,

    -- Supplier info
    preferred_vendor NVARCHAR(100) NULL,
    vendor_sku NVARCHAR(100) NULL,

    -- Status
    active BIT DEFAULT 1,

    -- Timestamps
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE(),

    -- Constraints
    CONSTRAINT FK_material_inventory_material_type FOREIGN KEY (material_type_id)
        REFERENCES material_types(id),
    CONSTRAINT FK_material_inventory_color FOREIGN KEY (color_id)
        REFERENCES colors(id),
    CONSTRAINT FK_material_inventory_product FOREIGN KEY (product_id)
        REFERENCES products(id),
    CONSTRAINT UQ_material_inventory_sku UNIQUE (sku),
    CONSTRAINT UQ_material_inventory_combo UNIQUE (material_type_id, color_id)
);

CREATE INDEX IX_material_inventory_lookup ON material_inventory(material_type_id, color_id);
CREATE INDEX IX_material_inventory_stock ON material_inventory(in_stock, active);
CREATE INDEX IX_material_inventory_product ON material_inventory(product_id);

PRINT 'Created material_inventory';
GO

PRINT '';
PRINT '============================================================================';
PRINT 'ALL MATERIAL TABLES RECREATED SUCCESSFULLY!';
PRINT '============================================================================';
PRINT '';
PRINT 'Tables created:';
PRINT '  - material_types (10 material types will be imported)';
PRINT '  - colors (73 colors will be imported)';
PRINT '  - material_colors (78 combinations will be imported)';
PRINT '  - material_inventory (78 SKUs will be imported)';
PRINT '';
PRINT 'Now run: python scripts/material_import.py MATERIAL_CATALOG.csv';
PRINT '';
GO
