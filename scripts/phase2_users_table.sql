/*
 * Phase 2A: Customer Portal Authentication
 * Users Table Migration Script
 *
 * Creates users table for customer authentication and profile management
 * Run this script in SQL Server Express (BLB3D_ERP database)
 *
 * Date: 2025-11-24
 */

USE BLB3D_ERP;
GO

-- Drop table if exists (for development only - remove for production)
IF OBJECT_ID('dbo.users', 'U') IS NOT NULL
    DROP TABLE dbo.users;
GO

-- Create users table
CREATE TABLE users (
    id INT PRIMARY KEY IDENTITY(1,1),

    -- Authentication
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email_verified BIT NOT NULL DEFAULT 0,

    -- Profile Information
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company_name VARCHAR(200),
    phone VARCHAR(20),

    -- Billing Address
    billing_address_line1 VARCHAR(255),
    billing_address_line2 VARCHAR(255),
    billing_city VARCHAR(100),
    billing_state VARCHAR(50),
    billing_zip VARCHAR(20),
    billing_country VARCHAR(100) DEFAULT 'USA',

    -- Shipping Address
    shipping_address_line1 VARCHAR(255),
    shipping_address_line2 VARCHAR(255),
    shipping_city VARCHAR(100),
    shipping_state VARCHAR(50),
    shipping_zip VARCHAR(20),
    shipping_country VARCHAR(100) DEFAULT 'USA',

    -- Account Status
    status VARCHAR(20) NOT NULL DEFAULT 'active',  -- active, inactive, suspended
    account_type VARCHAR(20) NOT NULL DEFAULT 'customer',  -- customer, admin, operator

    -- Timestamps
    created_at DATETIME NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME NOT NULL DEFAULT GETDATE(),
    last_login_at DATETIME,

    -- Audit
    created_by INT,  -- NULL for self-registration
    updated_by INT,

    -- Indexes
    INDEX idx_users_email (email),
    INDEX idx_users_status (status),
    INDEX idx_users_created_at (created_at)
);
GO

-- Create trigger to update updated_at timestamp
CREATE TRIGGER trg_users_updated_at
ON users
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE users
    SET updated_at = GETDATE()
    FROM users u
    INNER JOIN inserted i ON u.id = i.id;
END;
GO

-- Create refresh_tokens table for JWT refresh token storage
IF OBJECT_ID('dbo.refresh_tokens', 'U') IS NOT NULL
    DROP TABLE dbo.refresh_tokens;
GO

CREATE TABLE refresh_tokens (
    id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL FOREIGN KEY REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,  -- Store hash, not raw token
    expires_at DATETIME NOT NULL,
    revoked BIT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT GETDATE(),
    revoked_at DATETIME,

    INDEX idx_refresh_tokens_user_id (user_id),
    INDEX idx_refresh_tokens_token_hash (token_hash),
    INDEX idx_refresh_tokens_expires_at (expires_at)
);
GO

-- Insert default admin user (password: 'ChangeMe123!' - must be changed on first login)
-- Password hash for 'ChangeMe123!' using bcrypt
INSERT INTO users (
    email,
    password_hash,
    first_name,
    last_name,
    account_type,
    email_verified,
    status
) VALUES (
    'bbaker@blb3dprinting.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ND2cKlHm5uWi',  -- ChangeMe123!
    'Brandon',
    'Baker',
    'admin',
    1,
    'active'
);
GO

PRINT 'Phase 2A users table migration completed successfully!';
PRINT 'Default admin user created: bbaker@blb3dprinting.com (password: ChangeMe123!)';
PRINT 'IMPORTANT: Change the admin password immediately after first login!';
GO
