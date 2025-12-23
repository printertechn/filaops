-- ============================================================================
-- BLB3D ERP Database Setup Script for SQL Server Express
-- ============================================================================
-- This script creates the complete database schema for the BLB3D ERP system
-- Run this in SQL Server Management Studio (SSMS)
-- ============================================================================

-- Create database
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'BLB3D_ERP')
BEGIN
    CREATE DATABASE BLB3D_ERP;
    PRINT 'Database BLB3D_ERP created successfully';
END
ELSE
BEGIN
    PRINT 'Database BLB3D_ERP already exists';
END
GO

USE BLB3D_ERP;
GO

PRINT 'Creating tables...';
GO

-- ============================================================================
-- PRODUCTS & INVENTORY
-- ============================================================================

-- Products table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[products]') AND type in (N'U'))
BEGIN
    CREATE TABLE products (
        id INT IDENTITY(1,1) PRIMARY KEY,
        sku NVARCHAR(50) UNIQUE NOT NULL,
        name NVARCHAR(255) NOT NULL,
        description NVARCHAR(MAX),
        category NVARCHAR(100),
        unit NVARCHAR(20) DEFAULT 'EA',
        selling_price DECIMAL(18,4),
        cost DECIMAL(18,4),
        weight DECIMAL(18,4),
        is_raw_material BIT DEFAULT 0,
        has_bom BIT DEFAULT 0,
        track_lots BIT DEFAULT 0,
        track_serials BIT DEFAULT 0,
        active BIT DEFAULT 1,
        woocommerce_product_id BIGINT NULL,  -- External ID from WooCommerce
        created_at DATETIME2 DEFAULT GETDATE(),
        updated_at DATETIME2 DEFAULT GETDATE()
    );
    PRINT 'Table products created';
END
GO

-- Inventory locations table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[inventory_locations]') AND type in (N'U'))
BEGIN
    CREATE TABLE inventory_locations (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(100) NOT NULL,
        code NVARCHAR(50) UNIQUE NOT NULL,
        type NVARCHAR(50),  -- warehouse, shelf, bin
        parent_id INT,
        active BIT DEFAULT 1,
        FOREIGN KEY (parent_id) REFERENCES inventory_locations(id)
    );
    PRINT 'Table inventory_locations created';
END
GO

-- Inventory table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[inventory]') AND type in (N'U'))
BEGIN
    CREATE TABLE inventory (
        id INT IDENTITY(1,1) PRIMARY KEY,
        product_id INT NOT NULL,
        location_id INT NOT NULL,
        on_hand_quantity DECIMAL(18,4) DEFAULT 0,
        allocated_quantity DECIMAL(18,4) DEFAULT 0,
        available_quantity AS (on_hand_quantity - allocated_quantity) PERSISTED,
        lot_number NVARCHAR(100),
        serial_number NVARCHAR(100),
        cost_per_unit DECIMAL(18,4),
        last_updated DATETIME2 DEFAULT GETDATE(),
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (location_id) REFERENCES inventory_locations(id)
    );
    PRINT 'Table inventory created';
END
GO

-- Inventory transactions table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[inventory_transactions]') AND type in (N'U'))
BEGIN
    CREATE TABLE inventory_transactions (
        id INT IDENTITY(1,1) PRIMARY KEY,
        product_id INT NOT NULL,
        location_id INT NOT NULL,
        transaction_type NVARCHAR(50) NOT NULL,  -- receipt, adjustment, consumption, transfer, scrap
        quantity DECIMAL(18,4) NOT NULL,
        lot_number NVARCHAR(100),
        serial_number NVARCHAR(100),
        cost_per_unit DECIMAL(18,4),
        total_cost AS (quantity * cost_per_unit) PERSISTED,
        reference_type NVARCHAR(50),  -- sales_order, purchase_order, production_order
        reference_id INT,
        notes NVARCHAR(MAX),
        created_at DATETIME2 DEFAULT GETDATE(),
        created_by NVARCHAR(100),
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (location_id) REFERENCES inventory_locations(id)
    );
    PRINT 'Table inventory_transactions created';
END
GO

-- ============================================================================
-- MANUFACTURING
-- ============================================================================

-- BOMs table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[boms]') AND type in (N'U'))
BEGIN
    CREATE TABLE boms (
        id INT IDENTITY(1,1) PRIMARY KEY,
        product_id INT NOT NULL,
        code NVARCHAR(50) UNIQUE NOT NULL,
        name NVARCHAR(255) NOT NULL,
        version INT DEFAULT 1,
        revision NVARCHAR(10),
        total_cost DECIMAL(18,4),
        assembly_time_minutes INT,
        active BIT DEFAULT 1,
        effective_date DATE,
        notes NVARCHAR(MAX),
        created_at DATETIME2 DEFAULT GETDATE(),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );
    PRINT 'Table boms created';
END
GO

-- BOM lines table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[bom_lines]') AND type in (N'U'))
BEGIN
    CREATE TABLE bom_lines (
        id INT IDENTITY(1,1) PRIMARY KEY,
        bom_id INT NOT NULL,
        component_id INT NOT NULL,  -- references products(id)
        quantity DECIMAL(18,4) NOT NULL,
        sequence INT,
        scrap_factor DECIMAL(5,2) DEFAULT 0,
        notes NVARCHAR(MAX),
        FOREIGN KEY (bom_id) REFERENCES boms(id),
        FOREIGN KEY (component_id) REFERENCES products(id)
    );
    PRINT 'Table bom_lines created';
END
GO

-- Production orders table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[production_orders]') AND type in (N'U'))
BEGIN
    CREATE TABLE production_orders (
        id INT IDENTITY(1,1) PRIMARY KEY,
        code NVARCHAR(50) UNIQUE NOT NULL,
        product_id INT NOT NULL,
        bom_id INT,
        quantity DECIMAL(18,4) NOT NULL,
        status NVARCHAR(50) DEFAULT 'draft',  -- draft, scheduled, in_progress, completed, cancelled
        priority NVARCHAR(20) DEFAULT 'normal',  -- low, normal, high, urgent
        due_date DATE,
        start_date DATETIME2,
        finish_date DATETIME2,
        estimated_time_minutes INT,
        actual_time_minutes INT,
        estimated_cost DECIMAL(18,4),
        actual_cost DECIMAL(18,4),
        assigned_to NVARCHAR(100),
        notes NVARCHAR(MAX),
        created_at DATETIME2 DEFAULT GETDATE(),
        created_by NVARCHAR(100),
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (bom_id) REFERENCES boms(id)
    );
    PRINT 'Table production_orders created';
END
GO

-- ============================================================================
-- SALES
-- ============================================================================

-- Customers table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[customers]') AND type in (N'U'))
BEGIN
    CREATE TABLE customers (
        id INT IDENTITY(1,1) PRIMARY KEY,
        code NVARCHAR(50) UNIQUE NOT NULL,
        name NVARCHAR(255) NOT NULL,
        contact_name NVARCHAR(255),
        email NVARCHAR(255),
        phone NVARCHAR(50),
        website NVARCHAR(255),
        billing_address NVARCHAR(MAX),
        shipping_address NVARCHAR(MAX),
        payment_terms NVARCHAR(50),
        credit_limit DECIMAL(18,4),
        tax_rate DECIMAL(5,2),
        notes NVARCHAR(MAX),
        active BIT DEFAULT 1,
        woocommerce_customer_id BIGINT NULL,  -- External ID from WooCommerce
        created_at DATETIME2 DEFAULT GETDATE()
    );
    PRINT 'Table customers created';
END
GO

-- Sales orders table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sales_orders]') AND type in (N'U'))
BEGIN
    CREATE TABLE sales_orders (
        id INT IDENTITY(1,1) PRIMARY KEY,
        code NVARCHAR(50) UNIQUE NOT NULL,
        customer_id INT NOT NULL,
        status NVARCHAR(50) DEFAULT 'draft',  -- draft, confirmed, in_production, shipped, completed, cancelled
        order_date DATE DEFAULT CAST(GETDATE() AS DATE),
        due_date DATE,
        ship_date DATE,
        payment_status NVARCHAR(50) DEFAULT 'unpaid',  -- unpaid, partial, paid
        payment_method NVARCHAR(50),
        subtotal DECIMAL(18,4),
        tax DECIMAL(18,4),
        shipping DECIMAL(18,4),
        discount DECIMAL(18,4),
        total DECIMAL(18,4),
        woocommerce_order_id BIGINT NULL,  -- External ID from WooCommerce
        website_order_id NVARCHAR(100),
        notes NVARCHAR(MAX),
        created_at DATETIME2 DEFAULT GETDATE(),
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    );
    PRINT 'Table sales_orders created';
END
GO

-- Sales order lines table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sales_order_lines]') AND type in (N'U'))
BEGIN
    CREATE TABLE sales_order_lines (
        id INT IDENTITY(1,1) PRIMARY KEY,
        sales_order_id INT NOT NULL,
        product_id INT NOT NULL,
        quantity DECIMAL(18,4) NOT NULL,
        unit_price DECIMAL(18,4) NOT NULL,
        discount DECIMAL(18,4) DEFAULT 0,
        tax_rate DECIMAL(5,2),
        total DECIMAL(18,4),
        allocated_quantity DECIMAL(18,4) DEFAULT 0,
        shipped_quantity DECIMAL(18,4) DEFAULT 0,
        notes NVARCHAR(MAX),
        FOREIGN KEY (sales_order_id) REFERENCES sales_orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );
    PRINT 'Table sales_order_lines created';
END
GO

-- ============================================================================
-- PURCHASING
-- ============================================================================

-- Vendors table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[vendors]') AND type in (N'U'))
BEGIN
    CREATE TABLE vendors (
        id INT IDENTITY(1,1) PRIMARY KEY,
        code NVARCHAR(50) UNIQUE NOT NULL,
        name NVARCHAR(255) NOT NULL,
        contact_name NVARCHAR(255),
        email NVARCHAR(255),
        phone NVARCHAR(50),
        website NVARCHAR(255),
        address NVARCHAR(MAX),
        payment_terms NVARCHAR(50),
        notes NVARCHAR(MAX),
        active BIT DEFAULT 1,
        created_at DATETIME2 DEFAULT GETDATE()
    );
    PRINT 'Table vendors created';
END
GO

-- Purchase orders table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[purchase_orders]') AND type in (N'U'))
BEGIN
    CREATE TABLE purchase_orders (
        id INT IDENTITY(1,1) PRIMARY KEY,
        code NVARCHAR(50) UNIQUE NOT NULL,
        vendor_id INT NOT NULL,
        status NVARCHAR(50) DEFAULT 'draft',  -- draft, sent, confirmed, received, cancelled
        order_date DATE DEFAULT CAST(GETDATE() AS DATE),
        due_date DATE,
        received_date DATE,
        subtotal DECIMAL(18,4),
        tax DECIMAL(18,4),
        shipping DECIMAL(18,4),
        total DECIMAL(18,4),
        notes NVARCHAR(MAX),
        created_at DATETIME2 DEFAULT GETDATE(),
        created_by NVARCHAR(100),
        FOREIGN KEY (vendor_id) REFERENCES vendors(id)
    );
    PRINT 'Table purchase_orders created';
END
GO

-- Purchase order lines table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[purchase_order_lines]') AND type in (N'U'))
BEGIN
    CREATE TABLE purchase_order_lines (
        id INT IDENTITY(1,1) PRIMARY KEY,
        purchase_order_id INT NOT NULL,
        product_id INT NOT NULL,
        quantity DECIMAL(18,4) NOT NULL,
        unit_cost DECIMAL(18,4) NOT NULL,
        tax_rate DECIMAL(5,2),
        total DECIMAL(18,4),
        received_quantity DECIMAL(18,4) DEFAULT 0,
        notes NVARCHAR(MAX),
        FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );
    PRINT 'Table purchase_order_lines created';
END
GO

-- ============================================================================
-- FINANCIAL
-- ============================================================================

-- Accounts table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[accounts]') AND type in (N'U'))
BEGIN
    CREATE TABLE accounts (
        id INT IDENTITY(1,1) PRIMARY KEY,
        code NVARCHAR(50) UNIQUE NOT NULL,
        name NVARCHAR(255) NOT NULL,
        type NVARCHAR(50) NOT NULL,  -- asset, liability, equity, revenue, expense
        parent_id INT,
        balance DECIMAL(18,4) DEFAULT 0,
        quickbooks_id NVARCHAR(100),
        active BIT DEFAULT 1,
        FOREIGN KEY (parent_id) REFERENCES accounts(id)
    );
    PRINT 'Table accounts created';
END
GO

-- Journal entries table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[journal_entries]') AND type in (N'U'))
BEGIN
    CREATE TABLE journal_entries (
        id INT IDENTITY(1,1) PRIMARY KEY,
        code NVARCHAR(50) UNIQUE NOT NULL,
        entry_date DATE DEFAULT CAST(GETDATE() AS DATE),
        status NVARCHAR(50) DEFAULT 'draft',  -- draft, posted, void
        reference_type NVARCHAR(50),  -- sales_order, purchase_order, etc.
        reference_id INT,
        description NVARCHAR(MAX),
        created_at DATETIME2 DEFAULT GETDATE(),
        created_by NVARCHAR(100),
        posted_at DATETIME2,
        posted_by NVARCHAR(100)
    );
    PRINT 'Table journal_entries created';
END
GO

-- Journal lines table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[journal_lines]') AND type in (N'U'))
BEGIN
    CREATE TABLE journal_lines (
        id INT IDENTITY(1,1) PRIMARY KEY,
        journal_entry_id INT NOT NULL,
        account_id INT NOT NULL,
        debit DECIMAL(18,4) DEFAULT 0,
        credit DECIMAL(18,4) DEFAULT 0,
        description NVARCHAR(MAX),
        FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id),
        FOREIGN KEY (account_id) REFERENCES accounts(id)
    );
    PRINT 'Table journal_lines created';
END
GO

-- ============================================================================
-- PRINT FARM INTEGRATION
-- ============================================================================

-- Printers table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[printers]') AND type in (N'U'))
BEGIN
    CREATE TABLE printers (
        id INT IDENTITY(1,1) PRIMARY KEY,
        code NVARCHAR(50) UNIQUE NOT NULL,
        name NVARCHAR(255) NOT NULL,
        model NVARCHAR(100),
        serial_number NVARCHAR(100),
        location NVARCHAR(255),
        status NVARCHAR(50) DEFAULT 'offline',  -- offline, idle, printing, error
        mqtt_topic NVARCHAR(255),
        ip_address NVARCHAR(50),
        active BIT DEFAULT 1
    );
    PRINT 'Table printers created';
END
GO

-- Print jobs table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[print_jobs]') AND type in (N'U'))
BEGIN
    CREATE TABLE print_jobs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        production_order_id INT,
        printer_id INT,
        gcode_file NVARCHAR(500),
        status NVARCHAR(50) DEFAULT 'queued',  -- queued, assigned, printing, completed, failed
        priority NVARCHAR(20) DEFAULT 'normal',
        estimated_time_minutes INT,
        actual_time_minutes INT,
        estimated_material_grams DECIMAL(18,4),
        actual_material_grams DECIMAL(18,4),
        variance_percent DECIMAL(5,2),
        queued_at DATETIME2 DEFAULT GETDATE(),
        started_at DATETIME2,
        finished_at DATETIME2,
        notes NVARCHAR(MAX),
        FOREIGN KEY (production_order_id) REFERENCES production_orders(id),
        FOREIGN KEY (printer_id) REFERENCES printers(id)
    );
    PRINT 'Table print_jobs created';
END
GO

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

PRINT 'Creating indexes...';
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_products_sku')
    CREATE INDEX IX_products_sku ON products(sku);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_products_active')
    CREATE INDEX IX_products_active ON products(active);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_inventory_product_location')
    CREATE INDEX IX_inventory_product_location ON inventory(product_id, location_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_inventory_transactions_product')
    CREATE INDEX IX_inventory_transactions_product ON inventory_transactions(product_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_inventory_transactions_created')
    CREATE INDEX IX_inventory_transactions_created ON inventory_transactions(created_at);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_sales_orders_customer')
    CREATE INDEX IX_sales_orders_customer ON sales_orders(customer_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_sales_orders_status')
    CREATE INDEX IX_sales_orders_status ON sales_orders(status);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_production_orders_status')
    CREATE INDEX IX_production_orders_status ON production_orders(status);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_purchase_orders_vendor')
    CREATE INDEX IX_purchase_orders_vendor ON purchase_orders(vendor_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_purchase_orders_status')
    CREATE INDEX IX_purchase_orders_status ON purchase_orders(status);

PRINT 'Indexes created successfully';
GO

-- ============================================================================
-- INSERT DEFAULT DATA
-- ============================================================================

PRINT 'Inserting default data...';
GO

-- Default inventory location
IF NOT EXISTS (SELECT * FROM inventory_locations WHERE code = 'MAIN')
BEGIN
    INSERT INTO inventory_locations (name, code, type, active)
    VALUES ('Main Warehouse', 'MAIN', 'warehouse', 1);
    PRINT 'Default inventory location created';
END

-- Default accounts for basic financial tracking
IF NOT EXISTS (SELECT * FROM accounts WHERE code = '1000')
BEGIN
    INSERT INTO accounts (code, name, type, active)
    VALUES
        ('1000', 'Assets', 'asset', 1),
        ('1100', 'Inventory', 'asset', 1),
        ('2000', 'Liabilities', 'liability', 1),
        ('3000', 'Equity', 'equity', 1),
        ('4000', 'Revenue', 'revenue', 1),
        ('5000', 'Cost of Goods Sold', 'expense', 1),
        ('6000', 'Operating Expenses', 'expense', 1);
    PRINT 'Default chart of accounts created';
END
GO

PRINT '============================================================================';
PRINT 'Database setup complete!';
PRINT 'Database: BLB3D_ERP';
PRINT 'Tables created: 20';
PRINT 'Next steps:';
PRINT '1. Configure backend/.env file with database connection';
PRINT '2. Run data migration scripts to import MRPeasy data';
PRINT '3. Start the FastAPI backend server';
PRINT '============================================================================';
GO
