-- Find all FKs referencing material_types and drop them
USE BLB3D_ERP;
GO

PRINT 'Finding all foreign keys referencing material_types...';

-- List all FKs
SELECT
    fk.name AS FK_Name,
    OBJECT_NAME(fk.parent_object_id) AS Table_Name,
    COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS Column_Name
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
WHERE OBJECT_NAME(fk.referenced_object_id) = 'material_types';
GO

-- Drop any FK from quotes table
IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name LIKE '%quotes%material_type%')
BEGIN
    DECLARE @sql NVARCHAR(MAX);
    SELECT @sql = 'ALTER TABLE ' + OBJECT_NAME(parent_object_id) + ' DROP CONSTRAINT ' + name
    FROM sys.foreign_keys
    WHERE OBJECT_NAME(referenced_object_id) = 'material_types';

    PRINT @sql;
    EXEC sp_executesql @sql;
END
GO

-- Now try to drop material_types
PRINT 'Attempting to drop material_types...';

IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[material_types]') AND type in (N'U'))
BEGIN
    DROP TABLE material_types;
    PRINT 'Dropped material_types successfully!';
END
GO

-- Recreate it
CREATE TABLE material_types (
    id INT IDENTITY(1,1) PRIMARY KEY,
    code NVARCHAR(50) NOT NULL,
    name NVARCHAR(100) NOT NULL,
    base_material NVARCHAR(20) NOT NULL,
    process_type NVARCHAR(20) NOT NULL DEFAULT 'FDM',
    density DECIMAL(6,4) NOT NULL,
    volumetric_flow_limit DECIMAL(6,2) NULL,
    nozzle_temp_min INT NULL,
    nozzle_temp_max INT NULL,
    bed_temp_min INT NULL,
    bed_temp_max INT NULL,
    requires_enclosure BIT DEFAULT 0,
    base_price_per_kg DECIMAL(10,2) NOT NULL,
    price_multiplier DECIMAL(4,2) DEFAULT 1.0,
    description NVARCHAR(MAX) NULL,
    strength_rating INT NULL,
    is_customer_visible BIT DEFAULT 1,
    display_order INT DEFAULT 100,
    active BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE(),
    CONSTRAINT UQ_material_types_code UNIQUE (code)
);

CREATE INDEX IX_material_types_base_material ON material_types(base_material);
CREATE INDEX IX_material_types_active ON material_types(active, is_customer_visible);

PRINT 'Created material_types with full schema!';
GO

-- Re-add FK from material_colors if it exists
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[material_colors]') AND type in (N'U'))
BEGIN
    IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_material_colors_material_type')
    BEGIN
        ALTER TABLE material_colors ADD CONSTRAINT FK_material_colors_material_type
            FOREIGN KEY (material_type_id) REFERENCES material_types(id) ON DELETE CASCADE;
        PRINT 'Added FK from material_colors';
    END
END
GO

-- Re-add FK from material_inventory if it exists
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[material_inventory]') AND type in (N'U'))
BEGIN
    IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_material_inventory_material_type')
    BEGIN
        ALTER TABLE material_inventory ADD CONSTRAINT FK_material_inventory_material_type
            FOREIGN KEY (material_type_id) REFERENCES material_types(id);
        PRINT 'Added FK from material_inventory';
    END
END
GO

PRINT '';
PRINT 'DONE! Now run the import script.';
GO
