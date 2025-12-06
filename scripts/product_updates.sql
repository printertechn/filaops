-- ============================================================================
-- BLB3D ERP - Product Table Updates
-- ============================================================================
-- Adds new fields for SKU mapping, visibility, and sales channels
-- Run this in SQL Server Management Studio (SSMS)
-- ============================================================================

USE BLB3D_ERP;
GO

PRINT 'Updating products table...';
GO

-- ============================================================================
-- ADD legacy_sku (for Squarespace SKU mapping)
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[products]') AND name = 'legacy_sku')
BEGIN
    ALTER TABLE products ADD legacy_sku NVARCHAR(50) NULL;
    PRINT 'Added legacy_sku column';
END
ELSE
BEGIN
    PRINT 'Column legacy_sku already exists';
END
GO

-- Create index on legacy_sku for fast lookups
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_products_legacy_sku' AND object_id = OBJECT_ID('products'))
BEGIN
    CREATE INDEX IX_products_legacy_sku ON products(legacy_sku);
    PRINT 'Created index on legacy_sku';
END
GO

-- ============================================================================
-- ADD is_public (visibility flag)
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[products]') AND name = 'is_public')
BEGIN
    ALTER TABLE products ADD is_public BIT DEFAULT 1;
    PRINT 'Added is_public column';
END
ELSE
BEGIN
    PRINT 'Column is_public already exists';
END
GO

-- ============================================================================
-- ADD sales_channel (public / b2b / internal)
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[products]') AND name = 'sales_channel')
BEGIN
    ALTER TABLE products ADD sales_channel NVARCHAR(20) DEFAULT 'public';
    PRINT 'Added sales_channel column';
END
ELSE
BEGIN
    PRINT 'Column sales_channel already exists';
END
GO

-- ============================================================================
-- ADD customer_id (for B2B customer-specific products)
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[products]') AND name = 'customer_id')
BEGIN
    ALTER TABLE products ADD customer_id INT NULL;
    PRINT 'Added customer_id column';
END
ELSE
BEGIN
    PRINT 'Column customer_id already exists';
END
GO

-- ============================================================================
-- ADD squarespace_product_id
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[products]') AND name = 'squarespace_product_id')
BEGIN
    ALTER TABLE products ADD squarespace_product_id NVARCHAR(50) NULL;
    PRINT 'Added squarespace_product_id column';
END
ELSE
BEGIN
    PRINT 'Column squarespace_product_id already exists';
END
GO

-- ============================================================================
-- MIGRATE: Copy current SKU to legacy_sku for existing products
-- ============================================================================
-- This preserves the old SKU format (FG-00015) while allowing new SKUs

PRINT '';
PRINT 'Migrating existing SKUs to legacy_sku...';

UPDATE products
SET legacy_sku = sku
WHERE legacy_sku IS NULL
  AND sku IS NOT NULL;

DECLARE @migrated INT = @@ROWCOUNT;
PRINT CONCAT('Migrated ', @migrated, ' SKUs to legacy_sku');
GO

-- ============================================================================
-- SUMMARY
-- ============================================================================
PRINT '';
PRINT '============================================================================';
PRINT 'Product table updates complete!';
PRINT '============================================================================';
PRINT '';
PRINT 'New columns added:';
PRINT '  - legacy_sku: Maps old SKUs (FG-00015) to new format';
PRINT '  - is_public: Controls visibility on public storefront';
PRINT '  - sales_channel: public / b2b / internal';
PRINT '  - customer_id: Restrict product to specific B2B customer';
PRINT '  - squarespace_product_id: Squarespace product reference';
PRINT '';
PRINT 'Existing SKUs have been copied to legacy_sku for mapping.';
PRINT '';
GO
