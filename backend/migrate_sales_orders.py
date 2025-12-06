"""
Migration script to recreate sales_orders table with new schema

This script:
1. Drops the existing sales_orders table (if it exists)
2. Recreates it with the new quote-centric schema
"""
import sys
from sqlalchemy import text

from app.db.session import engine
from app.db.base import Base
from app.models.sales_order import SalesOrder
from app.models.user import User
from app.models.quote import Quote

def migrate_sales_orders():
    """Drop and recreate sales_orders table"""
    print("Starting sales_orders table migration...")

    with engine.connect() as conn:
        # Step 1: Drop ALL FK constraints referencing sales_orders
        print("Step 1: Dropping FK constraints referencing sales_orders...")
        try:
            # Find all FK constraints referencing sales_orders
            result = conn.execute(text("""
                SELECT
                    OBJECT_NAME(parent_object_id) AS table_name,
                    name AS fk_name
                FROM sys.foreign_keys
                WHERE referenced_object_id = OBJECT_ID('sales_orders')
            """))
            fks = result.fetchall()

            if fks:
                for table_name, fk_name in fks:
                    print(f"  Dropping {table_name}.{fk_name}...")
                    conn.execute(text(f"ALTER TABLE {table_name} DROP CONSTRAINT {fk_name}"))
                    conn.commit()
                    print(f"  [OK] Dropped {fk_name}")
            else:
                print("  [OK] No FK constraints found")
        except Exception as e:
            print(f"Warning while dropping FKs: {e}")
            conn.rollback()

        # Step 2: Drop the old sales_orders table
        print("Step 2: Dropping old sales_orders table...")
        try:
            conn.execute(text("DROP TABLE IF EXISTS sales_orders"))
            conn.commit()
            print("[OK] Old sales_orders table dropped")
        except Exception as e:
            print(f"Error dropping table: {e}")
            conn.rollback()
            return False

    # Step 3: Create new table with updated schema
    print("Step 3: Creating new sales_orders table...")
    try:
        SalesOrder.__table__.create(engine, checkfirst=True)
        print("[OK] New sales_orders table created")
    except Exception as e:
        print(f"Error creating table: {e}")
        return False

    # Step 4: Re-add FK constraint from quotes to sales_orders
    print("Step 4: Re-adding FK constraint...")
    with engine.connect() as conn:
        try:
            conn.execute(text("""
                ALTER TABLE quotes
                ADD CONSTRAINT FK_quotes_sales_orders
                FOREIGN KEY (sales_order_id) REFERENCES sales_orders(id)
            """))
            conn.commit()
            print("[OK] FK constraint re-added")
        except Exception as e:
            print(f"Warning while adding FK: {e}")
            conn.rollback()

    print("\n[SUCCESS] Migration completed!")
    print("\nNew sales_orders schema:")
    print("- order_number (SO-YYYY-NNN format)")
    print("- Full customer quote integration (quote_id)")
    print("- Comprehensive payment tracking")
    print("- Shipping address and tracking")
    print("- Status lifecycle management")
    print("- Production and delivery timestamps")

    return True

if __name__ == "__main__":
    success = migrate_sales_orders()
    sys.exit(0 if success else 1)
