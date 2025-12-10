"""
Migration script to create MRP (Material Requirements Planning) tables.

Creates:
- planned_orders table (MRP-generated planned purchase/production orders)
- mrp_runs table (audit trail of MRP calculations)
- Adds safety_stock column to products table

Run from backend directory:
    python migrate_mrp_tables.py
"""

from app.db.session import engine
from sqlalchemy import text


def run_migration():
    print("=== Creating MRP Tables ===\n")

    with engine.connect() as conn:
        # =====================================================================
        # Add safety_stock column to products table
        # =====================================================================
        print("Adding safety_stock column to products table...")
        conn.execute(text("""
            IF NOT EXISTS (
                SELECT * FROM sys.columns
                WHERE object_id = OBJECT_ID('products') AND name = 'safety_stock'
            )
            BEGIN
                ALTER TABLE products ADD safety_stock DECIMAL(18,4) DEFAULT 0;
                PRINT 'Added safety_stock column to products';
            END
            ELSE
                PRINT 'safety_stock column already exists';
        """))
        conn.commit()
        print("  safety_stock column ready")

        # =====================================================================
        # Create mrp_runs table (audit trail)
        # =====================================================================
        print("Creating mrp_runs table...")
        conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'mrp_runs')
            BEGIN
                CREATE TABLE mrp_runs (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    run_date DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                    planning_horizon_days INT NOT NULL DEFAULT 30,

                    -- Scope of what was processed
                    orders_processed INT DEFAULT 0,
                    components_analyzed INT DEFAULT 0,

                    -- Results
                    shortages_found INT DEFAULT 0,
                    planned_orders_created INT DEFAULT 0,

                    -- Status tracking
                    status NVARCHAR(20) NOT NULL DEFAULT 'running',
                    error_message NVARCHAR(MAX) NULL,

                    -- Audit
                    created_by INT NULL,
                    completed_at DATETIME2 NULL,

                    CONSTRAINT CK_mrp_runs_status CHECK (
                        status IN ('running', 'completed', 'failed', 'cancelled')
                    )
                );
                CREATE INDEX IX_mrp_runs_run_date ON mrp_runs(run_date DESC);
                CREATE INDEX IX_mrp_runs_status ON mrp_runs(status);
                PRINT 'Created mrp_runs table';
            END
            ELSE
                PRINT 'mrp_runs table already exists';
        """))
        conn.commit()
        print("  mrp_runs table ready")

        # =====================================================================
        # Create planned_orders table
        # =====================================================================
        print("Creating planned_orders table...")
        conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'planned_orders')
            BEGIN
                CREATE TABLE planned_orders (
                    id INT IDENTITY(1,1) PRIMARY KEY,

                    -- Order type: purchase or production
                    order_type NVARCHAR(20) NOT NULL,

                    -- What needs to be ordered
                    product_id INT NOT NULL,
                    quantity DECIMAL(18,4) NOT NULL,

                    -- Timing (lead-time offset from demand)
                    due_date DATE NOT NULL,
                    start_date DATE NOT NULL,

                    -- Pegging: what demand triggered this order
                    source_demand_type NVARCHAR(50) NULL,
                    source_demand_id INT NULL,
                    mrp_run_id INT NULL,

                    -- Order lifecycle
                    status NVARCHAR(20) NOT NULL DEFAULT 'planned',

                    -- Conversion tracking
                    converted_to_po_id INT NULL,
                    converted_to_mo_id INT NULL,

                    -- Notes and audit
                    notes NVARCHAR(MAX) NULL,
                    created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                    created_by INT NULL,
                    updated_at DATETIME2 NULL,
                    firmed_at DATETIME2 NULL,
                    released_at DATETIME2 NULL,

                    -- Constraints
                    CONSTRAINT FK_planned_orders_product FOREIGN KEY (product_id)
                        REFERENCES products(id),
                    CONSTRAINT FK_planned_orders_mrp_run FOREIGN KEY (mrp_run_id)
                        REFERENCES mrp_runs(id),
                    CONSTRAINT FK_planned_orders_po FOREIGN KEY (converted_to_po_id)
                        REFERENCES purchase_orders(id),
                    CONSTRAINT FK_planned_orders_mo FOREIGN KEY (converted_to_mo_id)
                        REFERENCES production_orders(id),
                    CONSTRAINT CK_planned_orders_type CHECK (
                        order_type IN ('purchase', 'production')
                    ),
                    CONSTRAINT CK_planned_orders_status CHECK (
                        status IN ('planned', 'firmed', 'released', 'cancelled')
                    )
                );

                -- Indexes for common queries
                CREATE INDEX IX_planned_orders_status ON planned_orders(status);
                CREATE INDEX IX_planned_orders_product_id ON planned_orders(product_id);
                CREATE INDEX IX_planned_orders_due_date ON planned_orders(due_date);
                CREATE INDEX IX_planned_orders_order_type ON planned_orders(order_type);
                CREATE INDEX IX_planned_orders_mrp_run_id ON planned_orders(mrp_run_id);

                PRINT 'Created planned_orders table';
            END
            ELSE
                PRINT 'planned_orders table already exists';
        """))
        conn.commit()
        print("  planned_orders table ready")

        # =====================================================================
        # Summary
        # =====================================================================
        print("\n=== Verifying Tables ===")
        result = conn.execute(text("""
            SELECT name FROM sys.tables
            WHERE name IN ('mrp_runs', 'planned_orders')
            ORDER BY name
        """))
        tables = [row[0] for row in result]
        print(f"MRP tables created: {', '.join(tables)}")

        # Check safety_stock column
        result = conn.execute(text("""
            SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS
            WHERE table_name = 'products' AND column_name = 'safety_stock'
        """))
        cols = [row[0] for row in result]
        if cols:
            print("safety_stock column added to products table")

        print("\nMRP Migration completed successfully!")


if __name__ == "__main__":
    run_migration()