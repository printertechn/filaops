-- ============================================================================
-- Phase 2B: Customer Quote System - Database Tables
-- ============================================================================
-- Creates tables for customer quote requests and uploaded 3D model files
-- Supports .3MF and .STL file formats with auto-approval logic

-- ============================================================================
-- Table: quotes
-- ============================================================================
-- Stores customer quote requests with pricing and approval workflow
CREATE TABLE quotes (
    id INT PRIMARY KEY IDENTITY(1,1),

    -- User & Reference
    user_id INT NOT NULL FOREIGN KEY REFERENCES users(id),
    quote_number VARCHAR(50) NOT NULL UNIQUE,  -- e.g., 'Q-2024-001'

    -- Product Details
    product_name VARCHAR(255),  -- Customer-provided name
    quantity INT NOT NULL DEFAULT 1,
    material_type VARCHAR(50) NOT NULL,  -- PLA, PETG, ABS, ASA, TPU
    finish VARCHAR(50) DEFAULT 'standard',  -- standard, smooth, painted

    -- Pricing (from Bambu Suite quoter)
    material_grams DECIMAL(10,2),
    print_time_hours DECIMAL(10,2),
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2) NOT NULL,
    margin_percent DECIMAL(5,2),

    -- File Metadata
    file_format VARCHAR(10) NOT NULL,  -- .3mf, .stl
    file_size_bytes BIGINT NOT NULL,
    dimensions_x DECIMAL(10,2),  -- mm
    dimensions_y DECIMAL(10,2),  -- mm
    dimensions_z DECIMAL(10,2),  -- mm

    -- Workflow Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, approved, rejected, expired, converted
    approval_method VARCHAR(50),  -- auto, manual, customer
    approved_by INT NULL FOREIGN KEY REFERENCES users(id),  -- Admin who approved (NULL if auto)
    approved_at DATETIME NULL,
    rejection_reason VARCHAR(500) NULL,

    -- Auto-Approval Flags
    auto_approved BIT NOT NULL DEFAULT 0,
    auto_approve_eligible BIT NOT NULL DEFAULT 0,  -- Met criteria for auto-approve
    requires_review_reason VARCHAR(255),  -- Why manual review needed

    -- Rush Order
    rush_level VARCHAR(20) DEFAULT 'standard',  -- standard, rush, super_rush, urgent
    requested_delivery_date DATE NULL,

    -- Customer Notes
    customer_notes VARCHAR(1000) NULL,
    admin_notes VARCHAR(1000) NULL,

    -- Conversion to Order
    sales_order_id INT NULL FOREIGN KEY REFERENCES sales_orders(id),
    converted_at DATETIME NULL,

    -- Timestamps
    created_at DATETIME NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME NOT NULL DEFAULT GETDATE(),
    expires_at DATETIME NOT NULL,  -- Quote valid for 7 days

    -- Indexes
    INDEX idx_quotes_user_id (user_id),
    INDEX idx_quotes_quote_number (quote_number),
    INDEX idx_quotes_status (status),
    INDEX idx_quotes_created_at (created_at)
);

-- ============================================================================
-- Table: quote_files
-- ============================================================================
-- Stores uploaded 3D model files associated with quotes
CREATE TABLE quote_files (
    id INT PRIMARY KEY IDENTITY(1,1),

    -- Quote Reference
    quote_id INT NOT NULL FOREIGN KEY REFERENCES quotes(id) ON DELETE CASCADE,

    -- File Information
    original_filename VARCHAR(255) NOT NULL,  -- User's filename
    stored_filename VARCHAR(255) NOT NULL UNIQUE,  -- UUID-based storage name
    file_path VARCHAR(500) NOT NULL,  -- Full storage path
    file_size_bytes BIGINT NOT NULL,
    file_format VARCHAR(10) NOT NULL,  -- .3mf, .stl
    mime_type VARCHAR(100) NOT NULL,

    -- File Validation
    is_valid BIT NOT NULL DEFAULT 1,
    validation_errors VARCHAR(1000) NULL,

    -- File Hash (for deduplication)
    file_hash VARCHAR(64) NOT NULL,  -- SHA256

    -- Metadata from file
    model_name VARCHAR(255) NULL,  -- Extracted from file if available
    vertex_count INT NULL,  -- For STL files
    triangle_count INT NULL,  -- For STL files

    -- Bambu Suite Processing
    bambu_file_id VARCHAR(100) NULL,  -- ID in Bambu Suite system
    processed BIT NOT NULL DEFAULT 0,
    processing_error VARCHAR(500) NULL,

    -- Timestamps
    uploaded_at DATETIME NOT NULL DEFAULT GETDATE(),
    processed_at DATETIME NULL,

    -- Indexes
    INDEX idx_quote_files_quote_id (quote_id),
    INDEX idx_quote_files_file_hash (file_hash),
    INDEX idx_quote_files_uploaded_at (uploaded_at)
);

-- ============================================================================
-- Table: quote_items (for multi-part quotes)
-- ============================================================================
-- Allows quotes with multiple different parts/files
CREATE TABLE quote_items (
    id INT PRIMARY KEY IDENTITY(1,1),

    -- Quote Reference
    quote_id INT NOT NULL FOREIGN KEY REFERENCES quotes(id) ON DELETE CASCADE,
    quote_file_id INT NOT NULL FOREIGN KEY REFERENCES quote_files(id),

    -- Item Details
    item_number INT NOT NULL,  -- Line item number (1, 2, 3...)
    description VARCHAR(255),
    quantity INT NOT NULL DEFAULT 1,

    -- Individual Item Pricing
    material_grams DECIMAL(10,2),
    print_time_hours DECIMAL(10,2),
    unit_price DECIMAL(10,2) NOT NULL,
    line_total DECIMAL(10,2) NOT NULL,

    -- Timestamps
    created_at DATETIME NOT NULL DEFAULT GETDATE(),

    -- Indexes
    INDEX idx_quote_items_quote_id (quote_id),
    UNIQUE INDEX idx_quote_items_quote_line (quote_id, item_number)
);

-- ============================================================================
-- Auto-Update Trigger for quotes.updated_at
-- ============================================================================
GO
CREATE TRIGGER trg_quotes_updated_at
ON quotes
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE quotes
    SET updated_at = GETDATE()
    FROM quotes q
    INNER JOIN inserted i ON q.id = i.id;
END;
GO

-- ============================================================================
-- Sample Quote Statuses
-- ============================================================================
-- pending      - Awaiting review/approval
-- approved     - Ready for customer to accept
-- rejected     - Not feasible or declined by admin
-- accepted     - Customer accepted the quote
-- expired      - Quote validity period ended
-- converted    - Converted to sales order
-- cancelled    - Customer cancelled request

-- ============================================================================
-- Business Rules for Auto-Approval
-- ============================================================================
-- Auto-approve if ALL conditions met:
-- 1. Total price < $50
-- 2. File size < 100MB
-- 3. If ABS/ASA: dimensions < 200x200x100mm
-- 4. Valid file format (.3mf or .stl)
-- 5. No custom requests in notes
