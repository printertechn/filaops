-- Add shipping selection columns to quotes table
-- Run against BLB3D_ERP database

USE BLB3D_ERP;
GO

-- Add shipping selection columns to quotes table if they don't exist
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('quotes') AND name = 'shipping_rate_id')
BEGIN
    ALTER TABLE quotes ADD shipping_rate_id NVARCHAR(100) NULL;
    PRINT 'Added shipping_rate_id column to quotes';
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('quotes') AND name = 'shipping_carrier')
BEGIN
    ALTER TABLE quotes ADD shipping_carrier NVARCHAR(50) NULL;
    PRINT 'Added shipping_carrier column to quotes';
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('quotes') AND name = 'shipping_service')
BEGIN
    ALTER TABLE quotes ADD shipping_service NVARCHAR(100) NULL;
    PRINT 'Added shipping_service column to quotes';
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('quotes') AND name = 'shipping_cost')
BEGIN
    ALTER TABLE quotes ADD shipping_cost DECIMAL(10,2) NULL;
    PRINT 'Added shipping_cost column to quotes';
END

PRINT 'Shipping columns added successfully!';
GO
