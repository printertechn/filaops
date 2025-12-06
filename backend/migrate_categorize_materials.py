"""
Migration script to categorize material items.

Creates subcategories for filament variants and assigns materials to them.
Also sets item_type = 'supply' for all MAT-FDM-* items.

Run from backend directory:
    python migrate_categorize_materials.py
"""

from datetime import datetime
from app.db.session import SessionLocal
from app.models.product import Product
from app.models.item_category import ItemCategory

def run_migration():
    db = SessionLocal()

    try:
        # Get parent category IDs
        pla_cat = db.query(ItemCategory).filter(ItemCategory.code == "PLA").first()
        petg_cat = db.query(ItemCategory).filter(ItemCategory.code == "PETG").first()
        abs_cat = db.query(ItemCategory).filter(ItemCategory.code == "ABS").first()
        tpu_cat = db.query(ItemCategory).filter(ItemCategory.code == "TPU").first()
        specialty_cat = db.query(ItemCategory).filter(ItemCategory.code == "SPECIALTY").first()

        print(f"Found parent categories:")
        print(f"  PLA: {pla_cat.id if pla_cat else 'NOT FOUND'}")
        print(f"  PETG: {petg_cat.id if petg_cat else 'NOT FOUND'}")
        print(f"  ABS: {abs_cat.id if abs_cat else 'NOT FOUND'}")
        print(f"  TPU: {tpu_cat.id if tpu_cat else 'NOT FOUND'}")
        print(f"  SPECIALTY: {specialty_cat.id if specialty_cat else 'NOT FOUND'}")

        # Define subcategories to create
        # Format: (code, name, parent_category, sort_order)
        subcategories = [
            # PLA variants
            ("PLA_BASIC", "PLA Basic", pla_cat, 1),
            ("PLA_MATTE", "PLA Matte", pla_cat, 2),
            ("PLA_SILK", "PLA Silk", pla_cat, 3),
            ("PLA_SILK_MULTI", "PLA Silk Multi-Color", pla_cat, 4),

            # PETG variants
            ("PETG_HF", "PETG High Flow", petg_cat, 1),
            ("PETG_CF", "PETG Carbon Fiber", petg_cat, 2),
            ("PETG_TRANS", "PETG Translucent", petg_cat, 3),

            # ABS variants
            ("ABS_STD", "ABS Standard", abs_cat, 1),  # For plain ABS SKUs
            ("ABS_GF", "ABS Glass Fiber", abs_cat, 2),

            # TPU variants
            ("TPU_95A", "TPU 95A (Standard)", tpu_cat, 1),
            ("TPU_68D", "TPU 68D (Firm)", tpu_cat, 2),

            # Specialty
            ("ASA", "ASA", specialty_cat, 1),
        ]

        # Create subcategories
        print("\n=== Creating Subcategories ===")
        category_map = {}  # code -> category object

        for code, name, parent, sort_order in subcategories:
            if parent is None:
                print(f"  SKIP {code}: Parent category not found")
                continue

            # Check if already exists
            existing = db.query(ItemCategory).filter(ItemCategory.code == code).first()
            if existing:
                print(f"  EXISTS: {code} (ID {existing.id})")
                category_map[code] = existing
            else:
                new_cat = ItemCategory(
                    code=code,
                    name=name,
                    parent_id=parent.id,
                    sort_order=sort_order,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(new_cat)
                db.flush()  # Get the ID
                print(f"  CREATED: {code} (ID {new_cat.id}) under {parent.code}")
                category_map[code] = new_cat

        # Map SKU material type to category code
        sku_to_category = {
            "PLA_BASIC": "PLA_BASIC",
            "PLA_MATTE": "PLA_MATTE",
            "PLA_SILK": "PLA_SILK",
            "PLA_SILK_MULTI": "PLA_SILK_MULTI",
            "PETG_HF": "PETG_HF",
            "PETG_CF": "PETG_CF",
            "PETG_TRANS": "PETG_TRANS",
            "ABS": "ABS_STD",  # Plain ABS goes to ABS_STD
            "ABS_GF": "ABS_GF",
            "TPU_95A": "TPU_95A",
            "TPU_68D": "TPU_68D",
            "ASA": "ASA",
        }

        # Update materials
        print("\n=== Updating Material Items ===")
        materials = db.query(Product).filter(Product.sku.like("MAT-FDM-%")).all()

        updated_count = 0
        by_category = {}

        for mat in materials:
            # Parse SKU: MAT-FDM-[TYPE]-[COLOR]
            parts = mat.sku.split("-")
            if len(parts) >= 3:
                mat_type = parts[2]  # e.g., PLA_BASIC, PETG_HF, ABS

                # Find the category
                cat_code = sku_to_category.get(mat_type)
                if cat_code and cat_code in category_map:
                    category = category_map[cat_code]
                    mat.category_id = category.id
                    mat.item_type = "supply"
                    mat.updated_at = datetime.utcnow()
                    updated_count += 1

                    # Track for summary
                    if cat_code not in by_category:
                        by_category[cat_code] = 0
                    by_category[cat_code] += 1
                else:
                    print(f"  WARNING: No category mapping for {mat_type} (SKU: {mat.sku})")

        # Summary
        print(f"\n=== Summary ===")
        print(f"Total materials updated: {updated_count}")
        for cat_code, count in sorted(by_category.items()):
            print(f"  {cat_code}: {count} items")

        # Commit
        db.commit()
        print("\n✓ Migration completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"\n✗ Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
