"""
Fix the routing constraint to allow multiple templates with NULL product_id.

SQL Server treats NULL = NULL as equal in unique constraints, so we need
a filtered unique index that only applies when product_id IS NOT NULL.
"""
from app.db.session import engine
from sqlalchemy import text

def main():
    with engine.connect() as conn:
        # Check current constraints
        result = conn.execute(text("""
            SELECT name, type_desc
            FROM sys.objects
            WHERE parent_object_id = OBJECT_ID('routings')
            AND (name LIKE '%UQ%' OR name LIKE '%product_version%')
        """))
        print("Current constraints/indexes on routings:")
        rows = list(result)
        for row in rows:
            print(f"  {row[0]} ({row[1]})")

        if not rows:
            print("  (none found)")

        # Try to drop the constraint if it exists
        try:
            print("\nDropping UQ_routing_product_version constraint...")
            conn.execute(text("ALTER TABLE routings DROP CONSTRAINT UQ_routing_product_version"))
            conn.commit()
            print("  Dropped!")
        except Exception as e:
            print(f"  Could not drop constraint (may not exist as constraint): {e}")
            conn.rollback()

        # Try to drop as index
        try:
            print("\nDropping UQ_routing_product_version as index...")
            conn.execute(text("DROP INDEX UQ_routing_product_version ON routings"))
            conn.commit()
            print("  Dropped!")
        except Exception as e:
            print(f"  Could not drop index (may not exist): {e}")
            conn.rollback()

        # Create filtered unique index
        print("\nCreating filtered unique index...")
        try:
            conn.execute(text("""
                CREATE UNIQUE INDEX UQ_routing_product_version
                ON routings (product_id, version)
                WHERE product_id IS NOT NULL
            """))
            conn.commit()
            print("  Created filtered unique index!")
        except Exception as e:
            print(f"  Error creating index: {e}")
            conn.rollback()

        # Verify
        print("\nVerifying constraints after fix:")
        result = conn.execute(text("""
            SELECT name, type_desc, filter_definition
            FROM sys.indexes
            WHERE object_id = OBJECT_ID('routings')
            AND name LIKE '%UQ%'
        """))
        for row in result:
            print(f"  {row[0]} ({row[1]}) - Filter: {row[2]}")

if __name__ == "__main__":
    main()
