-- ============================================================================
-- Fix material_types table - drop old incomplete version and recreate
-- ============================================================================

USE BLB3D_ERP;
GO

PRINT 'Fixing material_types table...';
GO

-- Drop the old incomplete table
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[material_types]') AND type in (N'U'))
BEGIN
    -- First check if there are foreign keys pointing to it
    IF EXISTS (SELECT * FROM sys.foreign_keys WHERE referenced_object_id = OBJECT_ID('material_types'))
    BEGIN
        PRINT 'Dropping foreign keys referencing material_types...';

        -- Drop FK from material_colors
        IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_material_colors_material_type')
        BEGIN
            ALTER TABLE material_colors DROP CONSTRAINT FK_material_colors_material_type;
        END

        -- Drop FK from material_inventory
        IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_material_inventory_material_type')
        BEGIN
            ALTER TABLE material_inventory DROP CONSTRAINT FK_material_inventory_material_type;
        END
    END

    DROP TABLE material_types;
    PRINT 'Dropped old material_types table';
END
GO

-- Recreate with full schema
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

PRINT 'Created material_types table with full schema';
GO

-- Re-add foreign keys
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[material_colors]') AND type in (N'U'))
BEGIN
    ALTER TABLE material_colors ADD CONSTRAINT FK_material_colors_material_type
        FOREIGN KEY (material_type_id) REFERENCES material_types(id) ON DELETE CASCADE;
    PRINT 'Re-added FK from material_colors';
END
GO

IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[material_inventory]') AND type in (N'U'))
BEGIN
    ALTER TABLE material_inventory ADD CONSTRAINT FK_material_inventory_material_type
        FOREIGN KEY (material_type_id) REFERENCES material_types(id);
    PRINT 'Re-added FK from material_inventory';
END
GO

PRINT '';
PRINT 'material_types table fixed! Now run the import script again.';
GO
