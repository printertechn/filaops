"""
Migration script to categorize component and packaging items.

Creates ASSEMBLY category structure and categorizes:
- COMP-* items (components)
- PKG-* items (packaging)
- MP-* items (machine parts)
- CON-* items (consumables)

Run from backend directory:
    python migrate_categorize_components.py
"""

from datetime import datetime
from app.db.session import SessionLocal
from app.models.product import Product
from app.models.item_category import ItemCategory

def run_migration():
    db = SessionLocal()

    try:
        # =====================================================================
        # STEP 1: Create ASSEMBLY root category
        # =====================================================================
        print("=== Creating ASSEMBLY Category Structure ===")

        assembly_cat = db.query(ItemCategory).filter(ItemCategory.code == "ASSEMBLY").first()
        if not assembly_cat:
            assembly_cat = ItemCategory(
                code="ASSEMBLY",
                name="Assembly Components",
                parent_id=None,
                description="Non-sellable components used in assemblies",
                sort_order=6,  # After existing root categories
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(assembly_cat)
            db.flush()
            print(f"  CREATED: ASSEMBLY (ID {assembly_cat.id})")
        else:
            print(f"  EXISTS: ASSEMBLY (ID {assembly_cat.id})")

        # =====================================================================
        # STEP 2: Create ASSEMBLY subcategories
        # =====================================================================
        assembly_subs = [
            ("LIGHTING", "Lighting", "LEDs, lamps, tealights", 1),
            ("ELECTRONICS", "Electronics", "Screens, controllers, sensors", 2),
            ("PRINTED_PARTS", "Printed Parts", "3D printed components (non-sellable)", 3),
            ("MISC_COMPONENTS", "Misc Components", "Keychains, drawer slides, etc.", 4),
        ]

        assembly_subcats = {}
        for code, name, desc, sort in assembly_subs:
            existing = db.query(ItemCategory).filter(ItemCategory.code == code).first()
            if existing:
                print(f"  EXISTS: {code} (ID {existing.id})")
                assembly_subcats[code] = existing
            else:
                new_cat = ItemCategory(
                    code=code,
                    name=name,
                    parent_id=assembly_cat.id,
                    description=desc,
                    sort_order=sort,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(new_cat)
                db.flush()
                print(f"  CREATED: {code} (ID {new_cat.id}) under ASSEMBLY")
                assembly_subcats[code] = new_cat

        # =====================================================================
        # STEP 3: Move HARDWARE under ASSEMBLY
        # =====================================================================
        print("\n=== Moving HARDWARE under ASSEMBLY ===")
        hardware_cat = db.query(ItemCategory).filter(ItemCategory.code == "HARDWARE").first()
        if hardware_cat:
            if hardware_cat.parent_id != assembly_cat.id:
                hardware_cat.parent_id = assembly_cat.id
                hardware_cat.sort_order = 5  # After other assembly subcats
                hardware_cat.updated_at = datetime.utcnow()
                print(f"  MOVED: HARDWARE (ID {hardware_cat.id}) under ASSEMBLY")
            else:
                print(f"  ALREADY under ASSEMBLY")

        # =====================================================================
        # STEP 4: Create MACHINE_PARTS category
        # =====================================================================
        print("\n=== Creating MACHINE_PARTS Category ===")
        mp_cat = db.query(ItemCategory).filter(ItemCategory.code == "MACHINE_PARTS").first()
        if not mp_cat:
            mp_cat = ItemCategory(
                code="MACHINE_PARTS",
                name="Machine Parts",
                parent_id=None,
                description="Printer spare parts and consumables",
                sort_order=7,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(mp_cat)
            db.flush()
            print(f"  CREATED: MACHINE_PARTS (ID {mp_cat.id})")
        else:
            print(f"  EXISTS: MACHINE_PARTS (ID {mp_cat.id})")

        # Subcategories for machine parts
        mp_subs = [
            ("MP_A1", "A1 Series Parts", 1),
            ("MP_P1S", "P1S Series Parts", 2),
            ("MP_OTHER", "Other Printer Parts", 3),
        ]
        mp_subcats = {}
        for code, name, sort in mp_subs:
            existing = db.query(ItemCategory).filter(ItemCategory.code == code).first()
            if existing:
                print(f"  EXISTS: {code}")
                mp_subcats[code] = existing
            else:
                new_cat = ItemCategory(
                    code=code,
                    name=name,
                    parent_id=mp_cat.id,
                    sort_order=sort,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(new_cat)
                db.flush()
                print(f"  CREATED: {code} (ID {new_cat.id})")
                mp_subcats[code] = new_cat

        # =====================================================================
        # STEP 5: Get packaging subcategories
        # =====================================================================
        boxes_cat = db.query(ItemCategory).filter(ItemCategory.code == "BOXES").first()
        bags_cat = db.query(ItemCategory).filter(ItemCategory.code == "BAGS").first()
        filler_cat = db.query(ItemCategory).filter(ItemCategory.code == "FILLER").first()

        # =====================================================================
        # STEP 6: Categorize items
        # =====================================================================
        print("\n=== Categorizing Items ===")

        updated = {"component": 0, "supply": 0}

        # COMP-* items
        comp_items = db.query(Product).filter(Product.sku.like("COMP-%")).all()
        for item in comp_items:
            sku = item.sku
            item.item_type = "component"

            # Assign to specific subcategory based on name/SKU
            if "LED" in sku or "LIGHT" in item.name.upper() or "TEALIGHT" in sku:
                item.category_id = assembly_subcats["LIGHTING"].id
            elif "SCREEN" in sku or "SENSOR" in sku:
                item.category_id = assembly_subcats["ELECTRONICS"].id
            elif "M3" in sku or "SCREW" in sku or "INSERT" in sku:
                # These should go to Hardware > Fasteners/Inserts
                if "INSERT" in sku:
                    inserts = db.query(ItemCategory).filter(ItemCategory.code == "INSERTS").first()
                    if inserts:
                        item.category_id = inserts.id
                else:
                    fasteners = db.query(ItemCategory).filter(ItemCategory.code == "FASTENERS").first()
                    if fasteners:
                        item.category_id = fasteners.id
            else:
                item.category_id = assembly_subcats["MISC_COMPONENTS"].id

            item.updated_at = datetime.utcnow()
            updated["component"] += 1
            print(f"  {sku}: component -> {item.category_id}")

        # PKG-* items
        pkg_items = db.query(Product).filter(Product.sku.like("PKG-%")).all()
        for item in pkg_items:
            sku = item.sku
            item.item_type = "supply"

            if "BOX" in sku:
                if boxes_cat:
                    item.category_id = boxes_cat.id
            elif "MESH" in sku or "BAG" in sku:
                if bags_cat:
                    item.category_id = bags_cat.id
            else:
                # Tape, pads, honeycomb -> filler
                if filler_cat:
                    item.category_id = filler_cat.id

            item.updated_at = datetime.utcnow()
            updated["supply"] += 1
            print(f"  {sku}: supply -> {item.category_id}")

        # MP-* items (Machine Parts)
        mp_items = db.query(Product).filter(Product.sku.like("MP-%")).all()
        for item in mp_items:
            sku = item.sku
            item.item_type = "supply"

            if "A1" in sku:
                item.category_id = mp_subcats["MP_A1"].id
            elif "P1S" in sku:
                item.category_id = mp_subcats["MP_P1S"].id
            else:
                item.category_id = mp_subcats["MP_OTHER"].id

            item.updated_at = datetime.utcnow()
            updated["supply"] += 1
            print(f"  {sku}: supply -> {item.category_id}")

        # CON-* items (Consumables) -> Supplies, categorize PVA under Specialty filament
        con_items = db.query(Product).filter(Product.sku.like("CON-%")).all()
        specialty = db.query(ItemCategory).filter(ItemCategory.code == "SPECIALTY").first()
        for item in con_items:
            item.item_type = "supply"
            if "PVA" in item.sku and specialty:
                item.category_id = specialty.id
            # Lube/maintenance items stay uncategorized for now
            item.updated_at = datetime.utcnow()
            updated["supply"] += 1
            print(f"  {item.sku}: supply -> {item.category_id}")

        # MFG-* items -> Service
        mfg_items = db.query(Product).filter(Product.sku.like("MFG-%")).all()
        machine_time = db.query(ItemCategory).filter(ItemCategory.code == "MACHINE_TIME").first()
        for item in mfg_items:
            item.item_type = "service"
            if machine_time:
                item.category_id = machine_time.id
            item.updated_at = datetime.utcnow()
            print(f"  {item.sku}: service -> {item.category_id}")

        # =====================================================================
        # Summary and Commit
        # =====================================================================
        print(f"\n=== Summary ===")
        print(f"Components updated: {updated['component']}")
        print(f"Supplies updated: {updated['supply']}")

        db.commit()
        print("\nMigration completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"\nMigration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
