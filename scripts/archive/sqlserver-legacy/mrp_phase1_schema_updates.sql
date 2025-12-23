-- MRP Refactor - Phase 1 Schema Updates

-- Phase 1.1: Add Fields to Products Table
-- These columns link a product directly to a material type and color,
-- which is key to unifying the item master.
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[products]') AND name = 'material_type_id')
BEGIN
    ALTER TABLE products ADD material_type_id INT NULL;
    PRINT 'Added material_type_id column to products table';
END
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[products]') AND name = 'color_id')
BEGIN
    ALTER TABLE products ADD color_id INT NULL;
    PRINT 'Added color_id column to products table';
END
GO

-- Add foreign key constraints if they don't exist
IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE object_id = OBJECT_ID(N'FK_products_material_type') AND parent_object_id = OBJECT_ID(N'[dbo].[products]'))
BEGIN
    ALTER TABLE products ADD CONSTRAINT FK_products_material_type
    FOREIGN KEY (material_type_id) REFERENCES material_types(id);
    PRINT 'Added FK constraint for material_type_id to products table';
END
GO

IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE object_id = OBJECT_ID(N'FK_products_color') AND parent_object_id = OBJECT_ID(N'[dbo].[products]'))
BEGIN
    ALTER TABLE products ADD CONSTRAINT FK_products_color
    FOREIGN KEY (color_id) REFERENCES colors(id);
    PRINT 'Added FK constraint for color_id to products table';
END
GO


-- Phase 1.2: Add Unit to BOM Lines
-- This makes BOM calculations explicit and removes ambiguity.
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[bom_lines]') AND name = 'unit')
BEGIN
    ALTER TABLE bom_lines ADD unit VARCHAR(10) DEFAULT 'EA';
    PRINT 'Added unit column to bom_lines table';
END
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[bom_lines]') AND name = 'is_cost_only')
BEGIN
    ALTER TABLE bom_lines ADD is_cost_only BIT DEFAULT 0;
    PRINT 'Added is_cost_only column to bom_lines table';
END
GO

PRINT 'MRP Refactor - Phase 1 schema updates complete.';
GO