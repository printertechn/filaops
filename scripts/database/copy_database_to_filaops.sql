-- Copy BLB3D_ERP database to FilaOps and sanitize private data
-- Run this script as Administrator or with appropriate permissions

USE master;
GO

-- Drop FilaOps if it exists
IF EXISTS (SELECT name FROM sys.databases WHERE name = 'FilaOps')
BEGIN
    ALTER DATABASE FilaOps SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE FilaOps;
    PRINT 'Dropped existing FilaOps database';
END
GO

-- Create new FilaOps database
CREATE DATABASE FilaOps;
GO

-- Copy all tables from BLB3D_ERP to FilaOps
-- Note: This copies schema and data. Constraints/indexes may need manual copying.

USE FilaOps;
GO

-- Get list of tables and copy them
-- We'll use SELECT INTO which automatically creates the table structure

DECLARE @table_name NVARCHAR(128);
DECLARE @sql NVARCHAR(MAX);

DECLARE table_cursor CURSOR FOR
SELECT TABLE_NAME 
FROM BLB3D_ERP.INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;

OPEN table_cursor;
FETCH NEXT FROM table_cursor INTO @table_name;

WHILE @@FETCH_STATUS = 0
BEGIN
    SET @sql = 'SELECT * INTO [' + @table_name + '] FROM BLB3D_ERP.dbo.[' + @table_name + ']';
    
    BEGIN TRY
        EXEC sp_executesql @sql;
        DECLARE @row_count INT;
        SET @sql = 'SELECT @count = COUNT(*) FROM [' + @table_name + ']';
        EXEC sp_executesql @sql, N'@count INT OUTPUT', @count = @row_count OUTPUT;
        PRINT 'Copied ' + @table_name + ': ' + CAST(@row_count AS NVARCHAR(10)) + ' rows';
    END TRY
    BEGIN CATCH
        PRINT 'Error copying ' + @table_name + ': ' + ERROR_MESSAGE();
    END CATCH
    
    FETCH NEXT FROM table_cursor INTO @table_name;
END

CLOSE table_cursor;
DEALLOCATE table_cursor;
GO

-- Sanitize private data
USE FilaOps;
GO

-- Users table
IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'users')
BEGIN
    UPDATE users 
    SET email = 'user' + CAST(id AS NVARCHAR(10)) + '@example.com',
        first_name = 'Test',
        last_name = 'User',
        password_hash = '$2b$12$dummyhashfordevelopmentonly';
    PRINT 'Sanitized users table';
END
GO

-- Customers table
IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'customers')
BEGIN
    UPDATE customers 
    SET email = 'customer' + CAST(id AS NVARCHAR(10)) + '@example.com',
        phone = '555-0000',
        address_line1 = '123 Test St',
        address_line2 = NULL,
        city = 'Test City',
        state = 'TS',
        postal_code = '12345',
        country = 'USA';
    PRINT 'Sanitized customers table';
END
GO

-- Quotes table
IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'quotes')
BEGIN
    UPDATE quotes 
    SET customer_email = 'quote' + CAST(id AS NVARCHAR(10)) + '@example.com',
        customer_name = 'Test Customer';
    PRINT 'Sanitized quotes table';
END
GO

PRINT 'Database copy and sanitization complete!';
PRINT 'Update your .env file: DB_NAME=FilaOps';
GO

