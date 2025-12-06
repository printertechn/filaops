-- ============================================================================
-- BLB3D ERP - Material Management Tables Migration
-- ============================================================================
-- This script creates the material type, color, and inventory tables
-- Run this in SQL Server Management Studio (SSMS)
-- ============================================================================

USE BLB3D_ERP;
GO

PRINT 'Creating material management tables...';
GO

-- ============================================================================
-- MATERIAL TYPES
-- ============================================================================
-- Material types like PLA Basic, PLA Matte, PLA Silk, PETG-HF, ABS, ASA, TPU
-- These are the first dropdown in the quote portal

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[material_types]') AND type in (N'U'))
BEGIN
    CREATE TABLE material_types (
        id INT IDENTITY(1,1) PRIMARY KEY,
        
        -- Identification
        code NVARCHAR(50) NOT NULL,
        name NVARCHAR(100) NOT NULL,
        
        -- Base material category (for print settings)
        base_material NVARCHAR(20) NOT NULL,  -- PLA, PETG, ABS, ASA, TPU
        
        -- Process type (for future expansion)
        process_type NVARCHAR(20) NOT NULL DEFAULT 'FDM',  -- FDM, RESIN, SLS
        
        -- Physical properties
        density DECIMAL(6,4) NOT NULL,  -- g/cm³
        
        -- Print settings
        volumetric_flow_limit DECIMAL(6,2) NULL,  -- mm³/s
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
    
    PRINT 'Table material_types created successfully';
END
ELSE
BEGIN
    PRINT 'Table material_types already exists';
END
GO

-- ============================================================================
-- COLORS
-- ============================================================================
-- Color definitions (Black, White, Charcoal, Mystic Magenta, etc.)
-- Shared across material types but not all colors available for all materials

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[colors]') AND type in (N'U'))
BEGIN
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
    
    PRINT 'Table colors created successfully';
END
ELSE
BEGIN
    PRINT 'Table colors already exists';
END
GO

-- ============================================================================
-- MATERIAL_COLORS (Junction Table)
-- ============================================================================
-- Defines which colors are available for which material types
-- Example: PLA Silk only has Gold, Mint, Champagne, White

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[material_colors]') AND type in (N'U'))
BEGIN
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
    
    PRINT 'Table material_colors created successfully';
END
ELSE
BEGIN
    PRINT 'Table material_colors already exists';
END
GO

-- ============================================================================
-- MATERIAL_INVENTORY
-- ============================================================================
-- Actual inventory: what material+color combinations you have in stock
-- Links to products table for BOM integration

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[material_inventory]') AND type in (N'U'))
BEGIN
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
    
    PRINT 'Table material_inventory created successfully';
END
ELSE
BEGIN
    PRINT 'Table material_inventory already exists';
END
GO

-- ============================================================================
-- ADD COLOR TO QUOTES TABLE
-- ============================================================================
-- Add color field to quotes table if not exists

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[quotes]') AND name = 'color')
BEGIN
    ALTER TABLE quotes ADD color NVARCHAR(30) NULL;
    PRINT 'Added color column to quotes table';
END
ELSE
BEGIN
    PRINT 'Column color already exists in quotes table';
END
GO

-- Add material_type_id for proper foreign key reference (optional, keeps material_type string for now)
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[quotes]') AND name = 'material_type_id')
BEGIN
    ALTER TABLE quotes ADD material_type_id INT NULL;
    PRINT 'Added material_type_id column to quotes table';
END
GO

-- Add gcode_file_path if not exists (for tracking sliced files)
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[quotes]') AND name = 'gcode_file_path')
BEGIN
    ALTER TABLE quotes ADD gcode_file_path NVARCHAR(500) NULL;
    PRINT 'Added gcode_file_path column to quotes table';
END
GO

-- ============================================================================
-- ADD gcode_file_path TO PRODUCTS IF NOT EXISTS
-- ============================================================================

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[products]') AND name = 'gcode_file_path')
BEGIN
    ALTER TABLE products ADD gcode_file_path NVARCHAR(500) NULL;
    PRINT 'Added gcode_file_path column to products table';
END
GO

PRINT '';
PRINT '============================================================================';
PRINT 'Material management tables created successfully!';
PRINT '============================================================================';
PRINT '';
PRINT 'Next steps:';
PRINT '1. Run the material_import.py script to load data from MATERIAL_CATALOG.csv';
PRINT '2. Verify data with: SELECT * FROM material_types; SELECT * FROM colors;';
PRINT '';
GO
