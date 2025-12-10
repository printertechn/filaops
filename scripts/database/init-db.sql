-- FilaOps Database Initialization Script
-- Creates database if not exists
-- Note: Tables are created by SQLAlchemy migrations on first backend startup

-- Create database if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'FilaOps')
BEGIN
    CREATE DATABASE FilaOps;
    PRINT 'Created FilaOps database';
END
ELSE
BEGIN
    PRINT 'FilaOps database already exists';
END
GO

USE FilaOps;
GO

-- The backend will handle table creation via SQLAlchemy
-- This script just ensures the database exists
PRINT 'Database initialization complete. Tables will be created by the backend on first startup.';
GO
