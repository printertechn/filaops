"""
FilaOps - Fresh Database Setup Script

Creates a new database with all tables from SQLAlchemy models.
Use this for a clean installation or testing.

Usage:
    cd backend
    python ../scripts/fresh_database_setup.py --database FilaOps_Test

Options:
    --database NAME    Database name (default: FilaOps_Test)
    --host HOST        SQL Server host (default: localhost\\SQLEXPRESS)
    --seed             Include sample data (products, BOM, orders) for testing
    --no-seed          Skip default data seeding (admin user, work centers, etc.)
    --use-existing     Use existing database without prompting (for automation)

Examples:
    # Fresh install with default data only
    python ../scripts/fresh_database_setup.py --database FilaOps

    # Fresh install with sample products and orders
    python ../scripts/fresh_database_setup.py --database FilaOps --seed

    # Add sample data to existing database (CI/automation)
    python ../scripts/fresh_database_setup.py --database FilaOps_Test --seed --use-existing
"""

import argparse
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


def create_database(host: str, database: str, use_existing: bool = False):
    """Create the database if it doesn't exist."""
    import pyodbc

    # Connect to master to create database
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={host};"
        f"DATABASE=master;"
        f"Trusted_Connection=yes;"
    )

    try:
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute(
            "SELECT name FROM sys.databases WHERE name = ?",
            (database,)
        )

        if cursor.fetchone():
            print(f"Database '{database}' already exists.")
            if use_existing:
                print("Using existing database (--use-existing flag).")
                cursor.close()
                conn.close()
                return True
            response = input("Drop and recreate? (y/N): ").strip().lower()
            if response == 'y':
                # Close any existing connections
                cursor.execute(f"""
                    ALTER DATABASE [{database}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
                    DROP DATABASE [{database}];
                """)
                print(f"Dropped database '{database}'")
            else:
                print("Using existing database.")
                cursor.close()
                conn.close()
                return True

        # Create database
        cursor.execute(f"CREATE DATABASE [{database}]")
        print(f"Created database '{database}'")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"Error creating database: {e}")
        return False


def create_tables(host: str, database: str):
    """Create all tables from SQLAlchemy models."""
    import os
    os.environ["DB_HOST"] = host
    os.environ["DB_NAME"] = database
    os.environ["DB_TRUSTED_CONNECTION"] = "true"

    # Import after setting env vars
    from app.db.base import Base
    from app.db.session import engine

    # Import all models to register them with Base
    from app.models import (
        user, product, quote, sales_order, production_order,
        bom, inventory, material, manufacturing, mrp,
        print_job, printer, purchase_order, vendor,
        item_category, traceability
    )

    print("\nCreating tables...")
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully!")

    return engine


def seed_default_data(engine):
    """Insert default data for a new installation."""
    from sqlalchemy.orm import Session
    from datetime import datetime

    with Session(engine) as session:
        # Check if data exists
        from app.models.inventory import InventoryLocation
        existing = session.query(InventoryLocation).first()
        if existing:
            print("\nDefault data already exists, skipping seed.")
            return

        print("\nSeeding default data...")

        # 1. Default inventory location
        from app.models.inventory import InventoryLocation
        main_location = InventoryLocation(
            code="MAIN",
            name="Main Warehouse",
            type="warehouse",
            active=True
        )
        session.add(main_location)

        # 2. Default work centers for a print farm
        from app.models.manufacturing import WorkCenter
        work_centers = [
            WorkCenter(
                code="FDM-POOL",
                name="FDM Printer Pool",
                description="All FDM printers",
                center_type="machine",
                capacity_hours_per_day=200,  # Multiple printers
                machine_rate_per_hour=3.00,
                labor_rate_per_hour=0.50,
                overhead_rate_per_hour=0.50,
                is_active=True
            ),
            WorkCenter(
                code="QC",
                name="Quality Control",
                description="Inspection station",
                center_type="station",
                capacity_hours_per_day=8,
                labor_rate_per_hour=25.00,
                is_active=True
            ),
            WorkCenter(
                code="PACKING",
                name="Packing Station",
                description="Packaging and shipping prep",
                center_type="station",
                capacity_hours_per_day=8,
                labor_rate_per_hour=18.00,
                is_active=True
            ),
        ]
        session.add_all(work_centers)

        # 3. Default item categories
        from app.models.item_category import ItemCategory
        categories = [
            ItemCategory(code="FILAMENT", name="Filament", description="3D printing filaments"),
            ItemCategory(code="FINISHED", name="Finished Goods", description="Completed products"),
            ItemCategory(code="PACKAGING", name="Packaging", description="Boxes, bags, and packing materials"),
            ItemCategory(code="HARDWARE", name="Hardware", description="Screws, inserts, and fasteners"),
        ]
        session.add_all(categories)

        # 4. Create admin user
        from app.models.user import User
        from app.core.security import hash_password

        # Hash password using bcrypt (same as auth endpoints)
        admin_password = "admin123"
        password_hashed = hash_password(admin_password)

        admin_user = User(
            email="admin@localhost",
            password_hash=password_hashed,
            first_name="Admin",
            last_name="User",
            account_type="admin",
            status="active",
            email_verified=True
        )
        session.add(admin_user)

        # 5. Routing templates
        from app.models.manufacturing import Routing, RoutingOperation

        # Get work center IDs
        session.flush()  # Get IDs assigned
        fdm_pool = session.query(WorkCenter).filter_by(code="FDM-POOL").first()
        qc_station = session.query(WorkCenter).filter_by(code="QC").first()
        packing_station = session.query(WorkCenter).filter_by(code="PACKING").first()

        standard_routing = Routing(
            code="TPL-STANDARD",
            name="Standard Print (Template)",
            is_template=True,
            version=1,
            is_active=True
        )
        session.add(standard_routing)
        session.flush()

        # Standard routing operations
        operations = [
            RoutingOperation(
                routing_id=standard_routing.id,
                work_center_id=fdm_pool.id,
                sequence=10,
                operation_code="PRINT",
                operation_name="3D Print",
                setup_time_minutes=7,  # Warmup
                run_time_minutes=60,   # Placeholder - override per product
                runtime_source="manual"
            ),
            RoutingOperation(
                routing_id=standard_routing.id,
                work_center_id=qc_station.id,
                sequence=20,
                operation_code="QC",
                operation_name="Quality Inspection",
                setup_time_minutes=0,
                run_time_minutes=5,
                runtime_source="manual"
            ),
            RoutingOperation(
                routing_id=standard_routing.id,
                work_center_id=packing_station.id,
                sequence=30,
                operation_code="PACK",
                operation_name="Pack for Shipping",
                setup_time_minutes=0,
                run_time_minutes=3,
                runtime_source="manual"
            ),
        ]
        session.add_all(operations)

        session.commit()
        print("Default data seeded successfully!")
        print("\n  Default admin login:")
        print("    Email: admin@localhost")
        print("    Password: admin123")
        print("\n  (Change this password immediately in production!)")


def seed_sample_data(engine):
    """
    Insert sample data to help new users understand the workflow.
    Creates filaments, a finished product, BOM, and a sample order.
    """
    from sqlalchemy.orm import Session
    from datetime import datetime, timedelta
    from decimal import Decimal

    with Session(engine) as session:
        # Check if sample data already exists
        from app.models.product import Product
        existing = session.query(Product).filter(Product.sku == "FIL-PLA-BLK-1KG").first()
        if existing:
            print("\nSample data already exists, skipping.")
            return

        print("\nLoading sample data...")

        # ===== 1. Create Filaments (Raw Materials) =====
        filament_pla_black = Product(
            sku="FIL-PLA-BLK-1KG",
            name="PLA Filament - Black (1kg)",
            description="Standard PLA filament, 1.75mm, 1kg spool",
            category="Filament",
            item_type="supply",
            unit="KG",
            is_raw_material=True,
            standard_cost=Decimal("18.00"),
            selling_price=Decimal("25.00"),
            reorder_point=Decimal("5"),
            safety_stock=Decimal("2"),
            active=True
        )

        filament_petg_white = Product(
            sku="FIL-PETG-WHT-1KG",
            name="PETG Filament - White (1kg)",
            description="PETG filament, 1.75mm, 1kg spool - great for functional parts",
            category="Filament",
            item_type="supply",
            unit="KG",
            is_raw_material=True,
            standard_cost=Decimal("22.00"),
            selling_price=Decimal("30.00"),
            reorder_point=Decimal("3"),
            safety_stock=Decimal("1"),
            active=True
        )

        # ===== 2. Create Hardware (Component) =====
        heat_insert = Product(
            sku="HW-INSERT-M3",
            name="M3 Heat Set Insert",
            description="Brass heat-set insert for M3 screws",
            category="Hardware",
            item_type="component",
            unit="EA",
            standard_cost=Decimal("0.15"),
            selling_price=Decimal("0.50"),
            reorder_point=Decimal("100"),
            active=True
        )

        # ===== 3. Create Packaging (Supply) =====
        box_small = Product(
            sku="PKG-BOX-SM",
            name="Small Shipping Box",
            description="6x4x3 inch corrugated box",
            category="Packaging",
            item_type="supply",
            unit="EA",
            standard_cost=Decimal("0.75"),
            reorder_point=Decimal("50"),
            active=True
        )

        # ===== 4. Create Finished Product =====
        phone_stand = Product(
            sku="PRD-PHONE-STAND",
            name="Adjustable Phone Stand",
            description="3D printed adjustable phone/tablet stand with cable management",
            category="Finished Goods",
            item_type="finished_good",
            unit="EA",
            has_bom=True,
            standard_cost=Decimal("3.50"),
            selling_price=Decimal("15.00"),
            weight_oz=Decimal("2.5"),
            active=True
        )

        session.add_all([filament_pla_black, filament_petg_white, heat_insert, box_small, phone_stand])
        session.flush()  # Get IDs

        # ===== 5. Create BOM for Phone Stand =====
        from app.models.bom import BOM, BOMLine

        phone_stand_bom = BOM(
            product_id=phone_stand.id,
            code="BOM-PHONE-STAND",
            name="Phone Stand Assembly",
            version=1,
            active=True,
            notes="Standard phone stand - uses ~45g PLA + 2 inserts"
        )
        session.add(phone_stand_bom)
        session.flush()

        # BOM Lines
        bom_lines = [
            BOMLine(
                bom_id=phone_stand_bom.id,
                component_id=filament_pla_black.id,
                sequence=10,
                quantity=Decimal("0.045"),  # 45 grams = 0.045 kg
                consume_stage="production",
                notes="Main body material"
            ),
            BOMLine(
                bom_id=phone_stand_bom.id,
                component_id=heat_insert.id,
                sequence=20,
                quantity=Decimal("2"),
                consume_stage="production",
                notes="For adjustable hinge"
            ),
            BOMLine(
                bom_id=phone_stand_bom.id,
                component_id=box_small.id,
                sequence=30,
                quantity=Decimal("1"),
                consume_stage="shipping",
                notes="Packaging"
            ),
        ]
        session.add_all(bom_lines)

        # ===== 6. Create Inventory Records =====
        from app.models.inventory import Inventory, InventoryLocation

        # Get main warehouse location (created in default data)
        main_location = session.query(InventoryLocation).filter_by(code="MAIN").first()
        if main_location:
            inventory_records = [
                Inventory(
                    product_id=filament_pla_black.id,
                    location_id=main_location.id,
                    on_hand_quantity=Decimal("10")  # 10 kg
                ),
                Inventory(
                    product_id=filament_petg_white.id,
                    location_id=main_location.id,
                    on_hand_quantity=Decimal("5")
                ),
                Inventory(
                    product_id=heat_insert.id,
                    location_id=main_location.id,
                    on_hand_quantity=Decimal("200")
                ),
                Inventory(
                    product_id=box_small.id,
                    location_id=main_location.id,
                    on_hand_quantity=Decimal("100")
                ),
            ]
            session.add_all(inventory_records)

        # ===== 7. Create Sample Sales Order =====
        from app.models.sales_order import SalesOrder, SalesOrderLine
        from app.models.user import User

        admin_user = session.query(User).filter_by(email="admin@localhost").first()
        if admin_user:
            sample_order = SalesOrder(
                user_id=admin_user.id,
                order_number="SO-2025-001",
                order_type="line_item",
                source="manual",
                product_name="Sample Order",
                quantity=2,
                material_type="PLA",
                finish="standard",
                unit_price=Decimal("15.00"),
                total_price=Decimal("30.00"),
                tax_amount=Decimal("0"),
                shipping_cost=Decimal("5.99"),
                grand_total=Decimal("35.99"),
                status="pending",
                payment_status="pending",
                shipping_address_line1="123 Example Street",
                shipping_city="Sample City",
                shipping_state="CA",
                shipping_zip="90210",
                shipping_country="USA",
                customer_notes="This is a sample order to demonstrate the workflow",
                internal_notes="Created by sample data loader"
            )
            session.add(sample_order)
            session.flush()

            # Order line
            order_line = SalesOrderLine(
                sales_order_id=sample_order.id,
                product_id=phone_stand.id,
                line_number=1,
                quantity=2,
                unit_price=Decimal("15.00"),
                total_price=Decimal("30.00"),
                product_sku=phone_stand.sku,
                product_name=phone_stand.name
            )
            session.add(order_line)

        session.commit()
        print("Sample data loaded successfully!")
        print("\n  Created:")
        print("    - 2 Filaments (PLA Black, PETG White)")
        print("    - 1 Hardware item (M3 Heat Insert)")
        print("    - 1 Packaging item (Small Box)")
        print("    - 1 Finished Product (Phone Stand)")
        print("    - 1 BOM linking them together")
        print("    - Inventory for all items")
        print("    - 1 Sample Sales Order")


def print_summary(database: str):
    """Print setup summary."""
    print("\n" + "=" * 60)
    print("DATABASE SETUP COMPLETE")
    print("=" * 60)
    print(f"\n  Database: {database}")
    print("\n  Next steps:")
    print("    1. Update backend/.env with:")
    print(f"       DB_NAME={database}")
    print("    2. Start the backend:")
    print("       cd backend")
    print("       python -m uvicorn app.main:app --reload --port 8000")
    print("    3. Start the frontend:")
    print("       cd frontend")
    print("       npm run dev")
    print("    4. Open http://localhost:5173")
    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Create a fresh FilaOps database"
    )
    parser.add_argument(
        "--database",
        default="FilaOps_Test",
        help="Database name (default: FilaOps_Test)"
    )
    parser.add_argument(
        "--host",
        default="localhost\\SQLEXPRESS",
        help="SQL Server host (default: localhost\\SQLEXPRESS)"
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Include sample data for testing"
    )
    parser.add_argument(
        "--no-seed",
        action="store_true",
        help="Skip default data seeding"
    )
    parser.add_argument(
        "--use-existing",
        action="store_true",
        help="Use existing database without prompting (for CI/automation)"
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("FILAOPS FRESH DATABASE SETUP")
    print("=" * 60)
    print(f"\n  Host: {args.host}")
    print(f"  Database: {args.database}")

    # Step 1: Create database
    if not create_database(args.host, args.database, args.use_existing):
        sys.exit(1)

    # Step 2: Create tables
    engine = create_tables(args.host, args.database)

    # Step 3: Seed default data (unless --no-seed)
    if not args.no_seed:
        seed_default_data(engine)

    # Step 4: Seed sample data (if --seed)
    if args.seed:
        seed_sample_data(engine)

    # Print summary
    print_summary(args.database)


if __name__ == "__main__":
    main()
