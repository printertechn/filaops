"""
Migration: Add Audit Columns to Key Tables

Adds created_by and updated_by columns to enable audit trails.
These columns track which user created/modified each record.

Run: python migrate_audit_columns.py

Tables affected:
- quotes: Add created_by, updated_by
- sales_orders: Add created_by, updated_by
- sales_order_lines: Add created_by
- production_orders: Add updated_by (created_by already exists)
- bom: Add created_by, updated_by
- bom_lines: Add created_by
- products: Add created_by, updated_by
- vendors: Add created_by, updated_by
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.db.session import SessionLocal


def add_audit_columns():
    """Add audit columns to tables that need them."""
    db = SessionLocal()

    # Define tables and their audit column needs
    # Format: (table_name, [(column_name, nullable, default)])
    tables_to_update = [
        # Quotes - core business records
        ("quotes", [
            ("created_by", True, None),
            ("updated_by", True, None),
        ]),
        # Sales Orders - core business records
        ("sales_orders", [
            ("created_by", True, None),
            ("updated_by", True, None),
        ]),
        # Sales Order Lines
        ("sales_order_lines", [
            ("created_by", True, None),
        ]),
        # Production Orders - updated_by only (created_by exists)
        ("production_orders", [
            ("updated_by", True, None),
        ]),
        # BOMs - core manufacturing records
        ("bom", [
            ("created_by", True, None),
            ("updated_by", True, None),
        ]),
        # BOM Lines
        ("bom_lines", [
            ("created_by", True, None),
        ]),
        # Products
        ("products", [
            ("created_by", True, None),
            ("updated_by", True, None),
        ]),
        # Vendors
        ("vendors", [
            ("created_by", True, None),
            ("updated_by", True, None),
        ]),
        # Work Centers
        ("work_centers", [
            ("created_by", True, None),
            ("updated_by", True, None),
        ]),
        # Resources
        ("manufacturing_resources", [
            ("created_by", True, None),
            ("updated_by", True, None),
        ]),
        # Routings
        ("routings", [
            ("created_by", True, None),
            ("updated_by", True, None),
        ]),
    ]

    try:
        for table_name, columns in tables_to_update:
            print(f"\nProcessing table: {table_name}")

            # Check if table exists
            check_table = text("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME = :table_name
            """)
            result = db.execute(check_table, {"table_name": table_name}).scalar()

            if result == 0:
                print(f"  - Table '{table_name}' does not exist, skipping")
                continue

            for col_name, nullable, default in columns:
                # Check if column already exists
                check_col = text("""
                    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = :table_name AND COLUMN_NAME = :col_name
                """)
                exists = db.execute(check_col, {"table_name": table_name, "col_name": col_name}).scalar()

                if exists:
                    print(f"  - Column '{col_name}' already exists, skipping")
                    continue

                # Build ALTER TABLE statement
                null_str = "NULL" if nullable else "NOT NULL"
                default_str = f"DEFAULT {default}" if default is not None else ""

                alter_sql = f"""
                    ALTER TABLE {table_name}
                    ADD {col_name} INT {null_str} {default_str}
                """

                print(f"  - Adding column '{col_name}'...")
                db.execute(text(alter_sql.strip()))
                print(f"    Added successfully")

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


def verify_audit_columns():
    """Verify audit columns were added correctly."""
    db = SessionLocal()

    tables_to_check = [
        "quotes", "sales_orders", "sales_order_lines", "production_orders",
        "bom", "bom_lines", "products", "vendors", "work_centers",
        "manufacturing_resources", "routings"
    ]

    print("\nVerifying audit columns:")
    print("-" * 50)

    try:
        for table_name in tables_to_check:
            # Check if table exists
            check_table = text("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME = :table_name
            """)
            if db.execute(check_table, {"table_name": table_name}).scalar() == 0:
                print(f"{table_name}: Table not found")
                continue

            # Get audit columns
            check_cols = text("""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = :table_name
                AND COLUMN_NAME IN ('created_by', 'updated_by')
                ORDER BY COLUMN_NAME
            """)
            cols = [row[0] for row in db.execute(check_cols, {"table_name": table_name}).fetchall()]

            if cols:
                print(f"{table_name}: {', '.join(cols)}")
            else:
                print(f"{table_name}: No audit columns")

    finally:
        db.close()


def show_sample_usage():
    """Show how to use audit columns in code."""
    print("""
Sample Usage in Endpoints:
--------------------------

from app.logging_config import audit_log

# When creating a quote
@router.post("/quotes")
async def create_quote(
    request: QuoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quote = Quote(
        **request.dict(),
        created_by=current_user.id,  # Track who created
    )
    db.add(quote)
    db.commit()

    # Also log to audit file
    audit_log(
        "QUOTE_CREATED",
        user_id=current_user.id,
        resource_type="quote",
        resource_id=quote.id,
        details={"quote_number": quote.quote_number}
    )

# When updating an order
@router.put("/sales-orders/{order_id}")
async def update_order(
    order_id: int,
    request: OrderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(SalesOrder).get(order_id)
    order.updated_by = current_user.id  # Track who modified
    # ... apply updates ...
    db.commit()

    audit_log(
        "ORDER_UPDATED",
        user_id=current_user.id,
        resource_type="sales_order",
        resource_id=order.id,
        details={"changes": request.dict(exclude_unset=True)}
    )
""")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Add audit columns to BLB3D ERP tables")
    parser.add_argument("--verify", action="store_true", help="Verify existing audit columns")
    parser.add_argument("--usage", action="store_true", help="Show sample usage code")
    args = parser.parse_args()

    if args.verify:
        verify_audit_columns()
    elif args.usage:
        show_sample_usage()
    else:
        add_audit_columns()
        print()
        verify_audit_columns()
