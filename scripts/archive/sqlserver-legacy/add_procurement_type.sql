-- Add procurement_type column to products table
-- Values: 'make' (manufactured with BOM), 'buy' (purchased), 'make_or_buy' (flexible)
-- Default: 'buy' for backward compatibility

USE FilaOps_Test;
GO

-- Check if column exists first
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'products' AND COLUMN_NAME = 'procurement_type'
)
BEGIN
    ALTER TABLE products
    ADD procurement_type VARCHAR(20) NOT NULL DEFAULT 'buy';

    PRINT 'Added procurement_type column to products table';
END
ELSE
BEGIN
    PRINT 'procurement_type column already exists';
END
GO

-- Update existing items based on item_type:
-- - finished_good items default to 'make' (they're manufactured)
-- - supply items stay as 'buy'
-- - component items stay as 'buy' (can be changed individually)
-- - service items stay as 'buy'

UPDATE products
SET procurement_type = 'make'
WHERE item_type = 'finished_good'
  AND procurement_type = 'buy';

PRINT 'Updated finished_good items to procurement_type = make';
GO

-- Show summary
SELECT
    procurement_type,
    item_type,
    COUNT(*) as count
FROM products
GROUP BY procurement_type, item_type
ORDER BY procurement_type, item_type;
GO
