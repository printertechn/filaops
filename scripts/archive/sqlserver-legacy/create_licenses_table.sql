-- Create licenses table for Pro/Enterprise tier management
-- Run this in SQL Server

USE FilaOps;
GO

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[licenses]') AND type in (N'U'))
BEGIN
    CREATE TABLE licenses (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NOT NULL,
        license_key_hash NVARCHAR(255) NOT NULL,
        tier NVARCHAR(20) NOT NULL,  -- 'pro' or 'enterprise'
        status NVARCHAR(20) NOT NULL DEFAULT 'active',  -- active, expired, revoked
        activated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
        expires_at DATETIME2 NULL,
        revoked_at DATETIME2 NULL,
        created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
        updated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
        
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        INDEX idx_licenses_user_id (user_id),
        INDEX idx_licenses_status (status),
        INDEX idx_licenses_key_hash (license_key_hash)
    );
    
    PRINT 'Table licenses created';
END
GO

