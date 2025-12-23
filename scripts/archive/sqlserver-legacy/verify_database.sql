-- ============================================================================
-- BLB3D ERP Database Verification Script
-- ============================================================================
-- Run this in SSMS to verify your database setup
-- ============================================================================

USE BLB3D_ERP;
GO

PRINT '============================================================================';
PRINT 'BLB3D ERP Database Verification';
PRINT '============================================================================';
PRINT '';

-- Check 1: Database exists and is accessible
PRINT 'Check 1: Database Status';
PRINT '-------------------------------------------';
SELECT
    name AS [Database Name],
    database_id AS [ID],
    create_date AS [Created On],
    compatibility_level AS [Compatibility Level]
FROM sys.databases
WHERE name = 'BLB3D_ERP';
PRINT '';

-- Check 2: Count all tables
PRINT 'Check 2: Table Count';
PRINT '-------------------------------------------';
SELECT COUNT(*) AS [Total Tables]
FROM sys.tables;
PRINT 'Expected: 20 tables';
PRINT '';

-- Check 3: List all tables
PRINT 'Check 3: All Tables';
PRINT '-------------------------------------------';
SELECT
    TABLE_SCHEMA AS [Schema],
    TABLE_NAME AS [Table Name],
    TABLE_TYPE AS [Type]
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;
PRINT '';

-- Check 4: Count rows in each table
PRINT 'Check 4: Row Counts (Default Data)';
PRINT '-------------------------------------------';
SELECT
    t.name AS [Table Name],
    p.rows AS [Row Count]
FROM sys.tables t
INNER JOIN sys.partitions p ON t.object_id = p.object_id
WHERE p.index_id IN (0,1)  -- Heap or clustered index
ORDER BY t.name;
PRINT '';

-- Check 5: Verify default inventory location
PRINT 'Check 5: Default Inventory Location';
PRINT '-------------------------------------------';
SELECT * FROM inventory_locations;
PRINT 'Expected: 1 row (MAIN - Main Warehouse)';
PRINT '';

-- Check 6: Verify default chart of accounts
PRINT 'Check 6: Default Chart of Accounts';
PRINT '-------------------------------------------';
SELECT code, name, type FROM accounts ORDER BY code;
PRINT 'Expected: 7 rows (basic accounts)';
PRINT '';

-- Check 7: Verify indexes
PRINT 'Check 7: Indexes Created';
PRINT '-------------------------------------------';
SELECT
    t.name AS [Table Name],
    i.name AS [Index Name],
    i.type_desc AS [Index Type]
FROM sys.indexes i
INNER JOIN sys.tables t ON i.object_id = t.object_id
WHERE i.name IS NOT NULL
ORDER BY t.name, i.name;
PRINT '';

-- Check 8: Database size
PRINT 'Check 8: Database Size';
PRINT '-------------------------------------------';
EXEC sp_spaceused;
PRINT '';

PRINT '============================================================================';
PRINT 'Verification Complete!';
PRINT '';
PRINT 'Expected Results:';
PRINT '  - 20 tables created';
PRINT '  - 1 default inventory location (MAIN)';
PRINT '  - 7 default accounts';
PRINT '  - Multiple indexes for performance';
PRINT '';
PRINT 'If everything looks good, you are ready to import data!';
PRINT '============================================================================';
GO
