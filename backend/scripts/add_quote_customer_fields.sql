-- Migration: Add customer contact fields to quotes table
-- Date: 2024-11-29
-- Purpose: Support portal quotes where customer email is captured separately from user account

-- Add customer contact fields for portal quotes
ALTER TABLE quotes ADD customer_email NVARCHAR(255) NULL;
ALTER TABLE quotes ADD customer_name NVARCHAR(200) NULL;
ALTER TABLE quotes ADD internal_notes NVARCHAR(1000) NULL;

-- Add index on customer_email for lookup when sending payment links
CREATE INDEX IX_quotes_customer_email ON quotes(customer_email) WHERE customer_email IS NOT NULL;

-- Verify columns were added
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'quotes' 
AND COLUMN_NAME IN ('customer_email', 'customer_name', 'internal_notes');
