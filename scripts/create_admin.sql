-- Create initial admin user for FilaOps
-- Run this after database setup if you need to manually create an admin
--
-- Default credentials:
--   Email: admin@localhost
--   Password: admin123
--
-- CHANGE THIS PASSWORD IMMEDIATELY after first login!
--
-- Usage:
--   sqlcmd -S localhost\SQLEXPRESS -d FilaOps -i scripts/create_admin.sql

USE FilaOps;  -- Change to your database name if different
GO

-- This hash is for password "admin123" - generated with bcrypt
DECLARE @password_hash NVARCHAR(255) = '$2b$12$M8s8lTWl5oUfiynsZMe5euGtyWH2ENo1FKa0J9tl2Ing8hf6JGNV.';

-- Check if admin exists
IF EXISTS (SELECT 1 FROM users WHERE email = 'admin@localhost')
BEGIN
    -- Update existing admin
    UPDATE users
    SET password_hash = @password_hash,
        account_type = 'admin',
        status = 'active',
        updated_at = GETDATE()
    WHERE email = 'admin@localhost';
    PRINT 'Admin user updated';
END
ELSE
BEGIN
    -- Create new admin user
    INSERT INTO users (
        email,
        password_hash,
        first_name,
        last_name,
        account_type,
        status,
        email_verified,
        created_at,
        updated_at
    ) VALUES (
        'admin@localhost',
        @password_hash,
        'Admin',
        'User',
        'admin',
        'active',
        1,
        GETDATE(),
        GETDATE()
    );
    PRINT 'Admin user created';
END
GO

-- Verify admin
SELECT id, email, account_type, status FROM users WHERE email = 'admin@localhost';
GO

-- ========================================
-- Create Walk-in Customer
-- ========================================
-- This is a special customer record for in-store/pickup orders
-- Use this when a customer doesn't have an account

IF EXISTS (SELECT 1 FROM users WHERE email = 'walkin@internal')
BEGIN
    PRINT 'Walk-in Customer already exists';
END
ELSE
BEGIN
    -- Get next customer number
    DECLARE @next_cust_num INT;
    SELECT @next_cust_num = ISNULL(MAX(CAST(REPLACE(customer_number, 'CUST-', '') AS INT)), 0) + 1
    FROM users WHERE customer_number LIKE 'CUST-%';

    -- Use CUST-000 for walk-in (special reserved number)
    INSERT INTO users (
        customer_number,
        email,
        password_hash,
        first_name,
        last_name,
        company_name,
        account_type,
        status,
        email_verified,
        shipping_address_line1,
        shipping_city,
        shipping_state,
        shipping_zip,
        created_at,
        updated_at
    ) VALUES (
        'CUST-000',
        'walkin@internal',
        '$2b$12$INVALID_HASH_CANNOT_LOGIN_WALK_IN_CUSTOMER',  -- Cannot login
        'Walk-in',
        'Customer',
        'In-Store / Pickup',
        'customer',
        'active',
        1,
        '1613 Etna Ave',  -- Your business address for pickup
        'Huntington',
        'IN',
        '46750',
        GETDATE(),
        GETDATE()
    );
    PRINT 'Walk-in Customer created (CUST-000)';
END
GO

-- Verify walk-in customer
SELECT id, customer_number, email, company_name FROM users WHERE email = 'walkin@internal';
GO

PRINT '';
PRINT '========================================';
PRINT 'Admin login credentials:';
PRINT '  Email: admin@localhost';
PRINT '  Password: admin123';
PRINT '';
PRINT 'CHANGE THIS PASSWORD IMMEDIATELY!';
PRINT '';
PRINT 'Walk-in Customer: CUST-000';
PRINT '  Use for in-store/pickup orders';
PRINT '========================================';
GO
