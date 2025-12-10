"""
Migration: Create Traceability Tables for B2B Compliance

Creates tables for:
- serial_numbers: Individual unit tracking
- material_lots: Batch tracking for raw materials
- production_lot_consumptions: Links production to material lots (for recalls)
- customer_traceability_profiles: Per-customer traceability settings

Also adds traceability_level column to users table.

Run: python migrate_traceability.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.db.session import SessionLocal


def create_traceability_tables():
    """Create all traceability-related tables."""
    db = SessionLocal()

    try:
        # =====================================================================
        # 1. Customer Traceability Profiles
        # =====================================================================
        print("\n1. Creating customer_traceability_profiles table...")

        check_table = text("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = 'customer_traceability_profiles'
        """)
        if db.execute(check_table).scalar() == 0:
            db.execute(text("""
                CREATE TABLE customer_traceability_profiles (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    user_id INT NOT NULL UNIQUE,
                    traceability_level VARCHAR(20) NOT NULL DEFAULT 'none',
                    requires_coc BIT NOT NULL DEFAULT 0,
                    requires_coa BIT NOT NULL DEFAULT 0,
                    requires_first_article BIT NOT NULL DEFAULT 0,
                    record_retention_days INT DEFAULT 2555,
                    custom_serial_prefix VARCHAR(20) NULL,
                    compliance_standards VARCHAR(255) NULL,
                    notes NVARCHAR(MAX) NULL,
                    created_at DATETIME NOT NULL DEFAULT GETDATE(),
                    updated_at DATETIME NOT NULL DEFAULT GETDATE(),
                    CONSTRAINT FK_traceability_user FOREIGN KEY (user_id)
                        REFERENCES users(id) ON DELETE CASCADE
                )
            """))
            db.execute(text("""
                CREATE INDEX IX_traceability_user ON customer_traceability_profiles(user_id)
            """))
            print("   Created customer_traceability_profiles table")
        else:
            print("   Table already exists, skipping")

        # =====================================================================
        # 2. Material Lots
        # =====================================================================
        print("\n2. Creating material_lots table...")

        check_table = text("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = 'material_lots'
        """)
        if db.execute(check_table).scalar() == 0:
            db.execute(text("""
                CREATE TABLE material_lots (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    lot_number VARCHAR(100) NOT NULL UNIQUE,
                    product_id INT NOT NULL,
                    vendor_id INT NULL,
                    purchase_order_id INT NULL,
                    vendor_lot_number VARCHAR(100) NULL,
                    quantity_received DECIMAL(12,4) NOT NULL,
                    quantity_consumed DECIMAL(12,4) NOT NULL DEFAULT 0,
                    quantity_scrapped DECIMAL(12,4) NOT NULL DEFAULT 0,
                    quantity_adjusted DECIMAL(12,4) NOT NULL DEFAULT 0,
                    status VARCHAR(30) NOT NULL DEFAULT 'active',
                    certificate_of_analysis NVARCHAR(MAX) NULL,
                    coa_file_path VARCHAR(500) NULL,
                    inspection_status VARCHAR(30) DEFAULT 'pending',
                    manufactured_date DATE NULL,
                    expiration_date DATE NULL,
                    received_date DATE NOT NULL DEFAULT GETDATE(),
                    unit_cost DECIMAL(10,4) NULL,
                    location VARCHAR(100) NULL,
                    notes NVARCHAR(MAX) NULL,
                    created_at DATETIME NOT NULL DEFAULT GETDATE(),
                    updated_at DATETIME NOT NULL DEFAULT GETDATE(),
                    CONSTRAINT FK_lot_product FOREIGN KEY (product_id)
                        REFERENCES products(id),
                    CONSTRAINT FK_lot_vendor FOREIGN KEY (vendor_id)
                        REFERENCES vendors(id),
                    CONSTRAINT FK_lot_po FOREIGN KEY (purchase_order_id)
                        REFERENCES purchase_orders(id)
                )
            """))
            db.execute(text("""
                CREATE INDEX IX_lot_number ON material_lots(lot_number)
            """))
            db.execute(text("""
                CREATE INDEX IX_lot_product_status ON material_lots(product_id, status)
            """))
            db.execute(text("""
                CREATE INDEX IX_lot_received_date ON material_lots(received_date)
            """))
            db.execute(text("""
                CREATE INDEX IX_lot_expiration ON material_lots(expiration_date)
            """))
            print("   Created material_lots table")
        else:
            print("   Table already exists, skipping")

        # =====================================================================
        # 3. Serial Numbers
        # =====================================================================
        print("\n3. Creating serial_numbers table...")

        check_table = text("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = 'serial_numbers'
        """)
        if db.execute(check_table).scalar() == 0:
            db.execute(text("""
                CREATE TABLE serial_numbers (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    serial_number VARCHAR(50) NOT NULL UNIQUE,
                    product_id INT NOT NULL,
                    production_order_id INT NOT NULL,
                    status VARCHAR(30) NOT NULL DEFAULT 'manufactured',
                    qc_passed BIT NOT NULL DEFAULT 1,
                    qc_date DATETIME NULL,
                    qc_notes NVARCHAR(MAX) NULL,
                    sales_order_id INT NULL,
                    sales_order_line_id INT NULL,
                    sold_at DATETIME NULL,
                    shipped_at DATETIME NULL,
                    tracking_number VARCHAR(100) NULL,
                    returned_at DATETIME NULL,
                    return_reason NVARCHAR(MAX) NULL,
                    manufactured_at DATETIME NOT NULL DEFAULT GETDATE(),
                    created_at DATETIME NOT NULL DEFAULT GETDATE(),
                    CONSTRAINT FK_serial_product FOREIGN KEY (product_id)
                        REFERENCES products(id),
                    CONSTRAINT FK_serial_production FOREIGN KEY (production_order_id)
                        REFERENCES production_orders(id),
                    CONSTRAINT FK_serial_sales_order FOREIGN KEY (sales_order_id)
                        REFERENCES sales_orders(id),
                    CONSTRAINT FK_serial_sales_line FOREIGN KEY (sales_order_line_id)
                        REFERENCES sales_order_lines(id)
                )
            """))
            db.execute(text("""
                CREATE INDEX IX_serial_number ON serial_numbers(serial_number)
            """))
            db.execute(text("""
                CREATE INDEX IX_serial_product_status ON serial_numbers(product_id, status)
            """))
            db.execute(text("""
                CREATE INDEX IX_serial_manufactured_date ON serial_numbers(manufactured_at)
            """))
            db.execute(text("""
                CREATE INDEX IX_serial_production ON serial_numbers(production_order_id)
            """))
            db.execute(text("""
                CREATE INDEX IX_serial_sales ON serial_numbers(sales_order_id)
            """))
            print("   Created serial_numbers table")
        else:
            print("   Table already exists, skipping")

        # =====================================================================
        # 4. Production Lot Consumptions (links production to material lots)
        # =====================================================================
        print("\n4. Creating production_lot_consumptions table...")

        check_table = text("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = 'production_lot_consumptions'
        """)
        if db.execute(check_table).scalar() == 0:
            db.execute(text("""
                CREATE TABLE production_lot_consumptions (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    production_order_id INT NOT NULL,
                    material_lot_id INT NOT NULL,
                    serial_number_id INT NULL,
                    bom_line_id INT NULL,
                    quantity_consumed DECIMAL(12,4) NOT NULL,
                    consumed_at DATETIME NOT NULL DEFAULT GETDATE(),
                    CONSTRAINT FK_consumption_production FOREIGN KEY (production_order_id)
                        REFERENCES production_orders(id),
                    CONSTRAINT FK_consumption_lot FOREIGN KEY (material_lot_id)
                        REFERENCES material_lots(id),
                    CONSTRAINT FK_consumption_serial FOREIGN KEY (serial_number_id)
                        REFERENCES serial_numbers(id),
                    CONSTRAINT FK_consumption_bom_line FOREIGN KEY (bom_line_id)
                        REFERENCES bom_lines(id)
                )
            """))
            db.execute(text("""
                CREATE INDEX IX_consumption_production ON production_lot_consumptions(production_order_id)
            """))
            db.execute(text("""
                CREATE INDEX IX_consumption_lot ON production_lot_consumptions(material_lot_id)
            """))
            db.execute(text("""
                CREATE INDEX IX_consumption_lot_production ON production_lot_consumptions(material_lot_id, production_order_id)
            """))
            print("   Created production_lot_consumptions table")
        else:
            print("   Table already exists, skipping")

        # =====================================================================
        # 5. Add traceability_level to users table (for quick access)
        # =====================================================================
        print("\n5. Adding traceability_level column to users table...")

        check_col = text("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'traceability_level'
        """)
        if db.execute(check_col).scalar() == 0:
            db.execute(text("""
                ALTER TABLE users ADD traceability_level VARCHAR(20) NULL DEFAULT 'none'
            """))
            print("   Added traceability_level to users table")
        else:
            print("   Column already exists, skipping")

        db.commit()
        print("\n" + "=" * 50)
        print("Migration completed successfully!")
        print("=" * 50)

    except Exception as e:
        db.rollback()
        print(f"\nError during migration: {e}")
        raise
    finally:
        db.close()


def verify_tables():
    """Verify traceability tables were created correctly."""
    db = SessionLocal()

    tables_to_check = [
        "customer_traceability_profiles",
        "material_lots",
        "serial_numbers",
        "production_lot_consumptions"
    ]

    print("\nVerifying traceability tables:")
    print("-" * 50)

    try:
        for table_name in tables_to_check:
            check_table = text("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME = :table_name
            """)
            exists = db.execute(check_table, {"table_name": table_name}).scalar()

            if exists:
                # Get column count
                col_count = text("""
                    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = :table_name
                """)
                cols = db.execute(col_count, {"table_name": table_name}).scalar()
                print(f"  {table_name}: EXISTS ({cols} columns)")
            else:
                print(f"  {table_name}: NOT FOUND")

        # Check users.traceability_level
        check_col = text("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'traceability_level'
        """)
        if db.execute(check_col).scalar():
            print(f"  users.traceability_level: EXISTS")
        else:
            print(f"  users.traceability_level: NOT FOUND")

    finally:
        db.close()


def show_recall_queries():
    """Show example queries for recall scenarios."""
    print("""
RECALL QUERY EXAMPLES
=====================

1. Find all products that used a specific material lot:
   (Forward traceability - "What did we make with lot X?")

   SELECT DISTINCT
       sn.serial_number,
       p.name AS product_name,
       po.code AS production_order,
       sn.manufactured_at
   FROM production_lot_consumptions plc
   JOIN production_orders po ON plc.production_order_id = po.id
   JOIN serial_numbers sn ON sn.production_order_id = po.id
   JOIN products p ON sn.product_id = p.id
   WHERE plc.material_lot_id = (
       SELECT id FROM material_lots WHERE lot_number = 'PLA-BLK-2025-0042'
   )
   ORDER BY sn.manufactured_at;

2. Find all material lots used in a specific serial number:
   (Backward traceability - "What went into serial Y?")

   SELECT
       ml.lot_number,
       p.name AS material_name,
       plc.quantity_consumed,
       ml.vendor_lot_number,
       v.name AS vendor_name
   FROM production_lot_consumptions plc
   JOIN material_lots ml ON plc.material_lot_id = ml.id
   JOIN products p ON ml.product_id = p.id
   LEFT JOIN vendors v ON ml.vendor_id = v.id
   WHERE plc.production_order_id = (
       SELECT production_order_id FROM serial_numbers
       WHERE serial_number = 'BLB-20251205-0001'
   );

3. Find all customers who received products from a recalled lot:

   SELECT DISTINCT
       u.email,
       u.company_name,
       sn.serial_number,
       so.order_number,
       so.shipped_at
   FROM production_lot_consumptions plc
   JOIN production_orders po ON plc.production_order_id = po.id
   JOIN serial_numbers sn ON sn.production_order_id = po.id
   JOIN sales_orders so ON sn.sales_order_id = so.id
   JOIN users u ON so.user_id = u.id
   WHERE plc.material_lot_id = (
       SELECT id FROM material_lots WHERE lot_number = 'PLA-BLK-2025-0042'
   )
   AND sn.status = 'shipped';

4. Get material lot usage summary:

   SELECT
       ml.lot_number,
       ml.quantity_received,
       ml.quantity_consumed,
       ml.quantity_received - ml.quantity_consumed - ml.quantity_scrapped AS remaining,
       COUNT(DISTINCT plc.production_order_id) AS production_orders_count,
       COUNT(DISTINCT sn.id) AS units_produced
   FROM material_lots ml
   LEFT JOIN production_lot_consumptions plc ON ml.id = plc.material_lot_id
   LEFT JOIN serial_numbers sn ON sn.production_order_id = plc.production_order_id
   WHERE ml.product_id = 123  -- specific material
   GROUP BY ml.id, ml.lot_number, ml.quantity_received, ml.quantity_consumed, ml.quantity_scrapped;
""")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create traceability tables for BLB3D ERP")
    parser.add_argument("--verify", action="store_true", help="Verify existing tables")
    parser.add_argument("--queries", action="store_true", help="Show example recall queries")
    args = parser.parse_args()

    if args.verify:
        verify_tables()
    elif args.queries:
        show_recall_queries()
    else:
        create_traceability_tables()
        print()
        verify_tables()
