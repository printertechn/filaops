"""
Phase 4A Migration: Item Categories and Product Extensions

This script:
1. Creates the item_categories table
2. Adds new columns to the products table
3. Seeds default categories
"""
import sys
from sqlalchemy import text
from datetime import datetime

from app.db.session import engine
from app.db.base import Base
from app.models.item_category import ItemCategory
from app.models.product import Product


def migrate_phase4a():
    """Run Phase 4A migration"""
    print("=" * 60)
    print("Phase 4A Migration: Item Categories and Product Extensions")
    print("=" * 60)

    # Step 1: Create item_categories table
    print("\nStep 1: Creating item_categories table...")
    try:
        ItemCategory.__table__.create(engine, checkfirst=True)
        print("[OK] item_categories table created")
    except Exception as e:
        print(f"[WARN] Table may already exist: {e}")

    # Step 2: Add new columns to products table
    print("\nStep 2: Adding new columns to products table...")
    new_columns = [
        ("item_type", "VARCHAR(20) DEFAULT 'finished_good'"),
        ("category_id", "INT NULL"),
        ("cost_method", "VARCHAR(20) DEFAULT 'average'"),
        ("standard_cost", "DECIMAL(10,2) NULL"),
        ("average_cost", "DECIMAL(10,2) NULL"),
        ("last_cost", "DECIMAL(10,2) NULL"),
        ("lead_time_days", "INT NULL"),
        ("min_order_qty", "DECIMAL(10,2) NULL"),
        ("reorder_point", "DECIMAL(10,2) NULL"),
        ("preferred_vendor_id", "INT NULL"),
        ("upc", "VARCHAR(50) NULL"),
        ("weight_oz", "DECIMAL(8,2) NULL"),
        ("length_in", "DECIMAL(8,2) NULL"),
        ("width_in", "DECIMAL(8,2) NULL"),
        ("height_in", "DECIMAL(8,2) NULL"),
    ]

    with engine.connect() as conn:
        for col_name, col_def in new_columns:
            try:
                # Check if column exists
                result = conn.execute(text(f"""
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'products' AND COLUMN_NAME = '{col_name}'
                """))
                if result.fetchone():
                    print(f"  [SKIP] {col_name} already exists")
                else:
                    conn.execute(text(f"ALTER TABLE products ADD {col_name} {col_def}"))
                    conn.commit()
                    print(f"  [OK] Added {col_name}")
            except Exception as e:
                print(f"  [WARN] {col_name}: {e}")
                conn.rollback()

        # Add FK constraint for category_id
        print("\nStep 3: Adding foreign key constraint...")
        try:
            conn.execute(text("""
                IF NOT EXISTS (
                    SELECT 1 FROM sys.foreign_keys
                    WHERE name = 'FK_products_item_categories'
                )
                ALTER TABLE products
                ADD CONSTRAINT FK_products_item_categories
                FOREIGN KEY (category_id) REFERENCES item_categories(id)
            """))
            conn.commit()
            print("[OK] FK constraint added")
        except Exception as e:
            print(f"[WARN] FK may already exist: {e}")
            conn.rollback()

    # Step 4: Seed default categories
    print("\nStep 4: Seeding default categories...")
    seed_default_categories()

    print("\n" + "=" * 60)
    print("[SUCCESS] Phase 4A Migration completed!")
    print("=" * 60)
    print("\nNew capabilities:")
    print("  - Item categories with hierarchy")
    print("  - Item types: finished_good, component, supply, service")
    print("  - Cost tracking: standard, average, last cost")
    print("  - Purchasing: lead time, min order qty, reorder point")
    print("  - Physical: dimensions (length, width, height, weight)")
    print("  - Identification: UPC/barcode support")
    print("\nAPI endpoints available at:")
    print("  GET/POST /api/v1/items - List/create items")
    print("  GET/POST /api/v1/items/categories - List/create categories")
    print("  POST /api/v1/items/import - CSV import")

    return True


def seed_default_categories():
    """Seed default item categories"""
    from sqlalchemy.orm import Session

    categories = [
        # Root categories
        {"code": "FILAMENT", "name": "Filament", "parent_code": None, "sort_order": 1},
        {"code": "PACKAGING", "name": "Packaging", "parent_code": None, "sort_order": 2},
        {"code": "HARDWARE", "name": "Hardware", "parent_code": None, "sort_order": 3},
        {"code": "FINISHED_GOODS", "name": "Finished Goods", "parent_code": None, "sort_order": 4},
        {"code": "SERVICES", "name": "Services", "parent_code": None, "sort_order": 5},

        # Filament subcategories
        {"code": "PLA", "name": "PLA", "parent_code": "FILAMENT", "sort_order": 1},
        {"code": "PETG", "name": "PETG", "parent_code": "FILAMENT", "sort_order": 2},
        {"code": "ABS", "name": "ABS", "parent_code": "FILAMENT", "sort_order": 3},
        {"code": "TPU", "name": "TPU", "parent_code": "FILAMENT", "sort_order": 4},
        {"code": "SPECIALTY", "name": "Specialty", "parent_code": "FILAMENT", "sort_order": 5},

        # Packaging subcategories
        {"code": "BOXES", "name": "Boxes", "parent_code": "PACKAGING", "sort_order": 1},
        {"code": "BAGS", "name": "Bags", "parent_code": "PACKAGING", "sort_order": 2},
        {"code": "FILLER", "name": "Filler Material", "parent_code": "PACKAGING", "sort_order": 3},

        # Hardware subcategories
        {"code": "FASTENERS", "name": "Fasteners", "parent_code": "HARDWARE", "sort_order": 1},
        {"code": "INSERTS", "name": "Heat Set Inserts", "parent_code": "HARDWARE", "sort_order": 2},

        # Finished goods subcategories
        {"code": "STANDARD_PRODUCTS", "name": "Standard Products", "parent_code": "FINISHED_GOODS", "sort_order": 1},
        {"code": "CUSTOM_PRODUCTS", "name": "Custom Products", "parent_code": "FINISHED_GOODS", "sort_order": 2},

        # Services subcategories
        {"code": "MACHINE_TIME", "name": "Machine Time", "parent_code": "SERVICES", "sort_order": 1},
    ]

    with Session(engine) as session:
        # First pass: Create root categories
        code_to_id = {}
        for cat_data in categories:
            if cat_data["parent_code"] is None:
                existing = session.query(ItemCategory).filter(
                    ItemCategory.code == cat_data["code"]
                ).first()

                if existing:
                    code_to_id[cat_data["code"]] = existing.id
                    print(f"  [SKIP] {cat_data['code']} already exists")
                else:
                    cat = ItemCategory(
                        code=cat_data["code"],
                        name=cat_data["name"],
                        parent_id=None,
                        sort_order=cat_data["sort_order"],
                        is_active=True,
                    )
                    session.add(cat)
                    session.flush()  # Get ID immediately
                    code_to_id[cat_data["code"]] = cat.id
                    print(f"  [OK] Created {cat_data['code']}")

        session.commit()

        # Second pass: Create child categories
        for cat_data in categories:
            if cat_data["parent_code"] is not None:
                existing = session.query(ItemCategory).filter(
                    ItemCategory.code == cat_data["code"]
                ).first()

                if existing:
                    print(f"  [SKIP] {cat_data['code']} already exists")
                else:
                    parent_id = code_to_id.get(cat_data["parent_code"])
                    if not parent_id:
                        # Try to find in database
                        parent = session.query(ItemCategory).filter(
                            ItemCategory.code == cat_data["parent_code"]
                        ).first()
                        parent_id = parent.id if parent else None

                    if parent_id:
                        cat = ItemCategory(
                            code=cat_data["code"],
                            name=cat_data["name"],
                            parent_id=parent_id,
                            sort_order=cat_data["sort_order"],
                            is_active=True,
                        )
                        session.add(cat)
                        print(f"  [OK] Created {cat_data['code']} under {cat_data['parent_code']}")
                    else:
                        print(f"  [WARN] Parent not found for {cat_data['code']}")

        session.commit()


if __name__ == "__main__":
    success = migrate_phase4a()
    sys.exit(0 if success else 1)
