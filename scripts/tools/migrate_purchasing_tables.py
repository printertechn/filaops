"""
Migration script to create purchasing tables.

Creates:
- vendors table
- purchase_orders table
- purchase_order_lines table

Run from backend directory:
    python migrate_purchasing_tables.py
"""

from app.db.session import engine
from sqlalchemy import text

def run_migration():
    print("=== Creating Purchasing Tables ===\n")

    with engine.connect() as conn:
        # =====================================================================
        # Create vendors table
        # =====================================================================
        print("Creating vendors table...")
        conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'vendors')
            BEGIN
                CREATE TABLE vendors (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    code NVARCHAR(50) NOT NULL UNIQUE,
                    name NVARCHAR(200) NOT NULL,
                    contact_name NVARCHAR(100) NULL,
                    email NVARCHAR(200) NULL,
                    phone NVARCHAR(50) NULL,
                    website NVARCHAR(500) NULL,
                    address_line1 NVARCHAR(200) NULL,
                    address_line2 NVARCHAR(200) NULL,
                    city NVARCHAR(100) NULL,
                    state NVARCHAR(100) NULL,
                    postal_code NVARCHAR(20) NULL,
                    country NVARCHAR(100) DEFAULT 'USA',
                    payment_terms NVARCHAR(100) NULL,
                    account_number NVARCHAR(100) NULL,
                    tax_id NVARCHAR(50) NULL,
                    lead_time_days INT NULL,
                    rating DECIMAL(3,2) NULL,
                    notes NVARCHAR(MAX) NULL,
                    is_active BIT DEFAULT 1 NOT NULL,
                    created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                    updated_at DATETIME2 NOT NULL DEFAULT GETUTCDATE()
                );
                CREATE INDEX IX_vendors_code ON vendors(code);
                CREATE INDEX IX_vendors_name ON vendors(name);
                PRINT 'Created vendors table';
            END
            ELSE
                PRINT 'vendors table already exists';
        """))
        conn.commit()
        print("  vendors table ready")

        # =====================================================================
        # Create purchase_orders table
        # =====================================================================
        print("Creating purchase_orders table...")
        conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'purchase_orders')
            BEGIN
                CREATE TABLE purchase_orders (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    po_number NVARCHAR(50) NOT NULL UNIQUE,
                    vendor_id INT NOT NULL,
                    status NVARCHAR(50) DEFAULT 'draft' NOT NULL,
                    order_date DATE NULL,
                    expected_date DATE NULL,
                    shipped_date DATE NULL,
                    received_date DATE NULL,
                    tracking_number NVARCHAR(200) NULL,
                    carrier NVARCHAR(100) NULL,
                    subtotal DECIMAL(18,4) DEFAULT 0 NOT NULL,
                    tax_amount DECIMAL(18,4) DEFAULT 0 NOT NULL,
                    shipping_cost DECIMAL(18,4) DEFAULT 0 NOT NULL,
                    total_amount DECIMAL(18,4) DEFAULT 0 NOT NULL,
                    payment_method NVARCHAR(100) NULL,
                    payment_reference NVARCHAR(200) NULL,
                    document_url NVARCHAR(1000) NULL,
                    notes NVARCHAR(MAX) NULL,
                    created_by NVARCHAR(100) NULL,
                    created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                    updated_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                    CONSTRAINT FK_purchase_orders_vendor FOREIGN KEY (vendor_id)
                        REFERENCES vendors(id)
                );
                CREATE INDEX IX_purchase_orders_po_number ON purchase_orders(po_number);
                CREATE INDEX IX_purchase_orders_vendor_id ON purchase_orders(vendor_id);
                CREATE INDEX IX_purchase_orders_status ON purchase_orders(status);
                PRINT 'Created purchase_orders table';
            END
            ELSE
                PRINT 'purchase_orders table already exists';
        """))
        conn.commit()
        print("  purchase_orders table ready")

        # =====================================================================
        # Create purchase_order_lines table
        # =====================================================================
        print("Creating purchase_order_lines table...")
        conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'purchase_order_lines')
            BEGIN
                CREATE TABLE purchase_order_lines (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    purchase_order_id INT NOT NULL,
                    product_id INT NOT NULL,
                    line_number INT NOT NULL,
                    quantity_ordered DECIMAL(18,4) NOT NULL,
                    quantity_received DECIMAL(18,4) DEFAULT 0 NOT NULL,
                    unit_cost DECIMAL(18,4) NOT NULL,
                    line_total DECIMAL(18,4) NOT NULL,
                    notes NVARCHAR(MAX) NULL,
                    created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                    updated_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                    CONSTRAINT FK_po_lines_purchase_order FOREIGN KEY (purchase_order_id)
                        REFERENCES purchase_orders(id) ON DELETE CASCADE,
                    CONSTRAINT FK_po_lines_product FOREIGN KEY (product_id)
                        REFERENCES products(id)
                );
                CREATE INDEX IX_po_lines_purchase_order_id ON purchase_order_lines(purchase_order_id);
                CREATE INDEX IX_po_lines_product_id ON purchase_order_lines(product_id);
                PRINT 'Created purchase_order_lines table';
            END
            ELSE
                PRINT 'purchase_order_lines table already exists';
        """))
        conn.commit()
        print("  purchase_order_lines table ready")

        # =====================================================================
        # Summary
        # =====================================================================
        print("\n=== Verifying Tables ===")
        result = conn.execute(text("""
            SELECT name FROM sys.tables
            WHERE name IN ('vendors', 'purchase_orders', 'purchase_order_lines')
            ORDER BY name
        """))
        tables = [row[0] for row in result]
        print(f"Tables created: {', '.join(tables)}")

        print("\nMigration completed successfully!")

if __name__ == "__main__":
    run_migration()
