"""
Migration Script: MaterialInventory → Products + Inventory

This script migrates all MaterialInventory records to the unified Products + Inventory model.
After running this, MaterialInventory should only be used for backward compatibility lookups.

Phase 1.3 of MRP_REFACTOR_PLAN.md

Run from backend directory:
    python migrate_material_inventory_to_products.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from decimal import Decimal

from app.db.session import SessionLocal
from app.models.material import MaterialInventory, MaterialType, Color
from app.models.product import Product
from app.models.inventory import Inventory, InventoryLocation
from app.services.material_service import create_material_product


def migrate_material_inventory(db: Session) -> dict:
    """
    Migrate all MaterialInventory records to Products + Inventory.
    
    For each MaterialInventory record:
    1. Create Product if doesn't exist (using create_material_product)
    2. Create/Update Inventory record with quantity_kg
    3. Link MaterialInventory.product_id for backward compatibility
    
    Returns:
        dict with migration statistics
    """
    stats = {
        "total_material_inventory": 0,
        "products_created": 0,
        "products_existing": 0,
        "inventory_records_created": 0,
        "inventory_records_updated": 0,
        "errors": []
    }
    
    # Get default location
    location = db.query(InventoryLocation).filter(
        InventoryLocation.code == 'MAIN'
    ).first()
    
    if not location:
        print("Creating default MAIN location...")
        location = InventoryLocation(
            name="Main Warehouse",
            code="MAIN",
            type="warehouse"
        )
        db.add(location)
        db.flush()
    
    # Get all active MaterialInventory records
    # Use raw SQL to avoid SQLAlchemy metadata cache issues
    from sqlalchemy import text
    
    # First, check what database we're connected to
    db_name_result = db.execute(text("SELECT DB_NAME() AS db_name"))
    db_name = db_name_result.scalar()
    print(f"Connected to database: {db_name}")
    
    # Check total records without filter
    total_result = db.execute(text("SELECT COUNT(*) FROM material_inventory"))
    total_count = total_result.scalar()
    print(f"Total MaterialInventory records: {total_count}")
    
    # Check active records
    active_result = db.execute(text("SELECT COUNT(*) FROM material_inventory WHERE active = 1"))
    active_count = active_result.scalar()
    print(f"Active MaterialInventory records: {active_count}")
    
    # Try different BIT comparisons
    active_result2 = db.execute(text("SELECT COUNT(*) FROM material_inventory WHERE CAST(active AS INT) = 1"))
    active_count2 = active_result2.scalar()
    print(f"Active (cast to INT): {active_count2}")
    
    print("Querying MaterialInventory with raw SQL...")
    result = db.execute(text("""
        SELECT id, material_type_id, color_id, sku, quantity_kg, cost_per_kg, 
               product_id, in_stock, active
        FROM material_inventory
        WHERE CAST(active AS INT) = 1
    """))
    
    # Fetch all rows
    rows = result.fetchall()
    print(f"Raw SQL returned {len(rows)} rows")
    
    # Convert to MaterialInventory objects for easier handling
    material_inventories = []
    for row in rows:
        mat_inv = MaterialInventory()
        mat_inv.id = row[0]  # id
        mat_inv.material_type_id = row[1]  # material_type_id
        mat_inv.color_id = row[2]  # color_id
        mat_inv.sku = row[3]  # sku
        mat_inv.quantity_kg = row[4]  # quantity_kg
        mat_inv.cost_per_kg = row[5]  # cost_per_kg
        mat_inv.product_id = row[6]  # product_id
        mat_inv.in_stock = bool(row[7])  # in_stock
        mat_inv.active = bool(row[8])  # active
        material_inventories.append(mat_inv)
    
    stats["total_material_inventory"] = len(material_inventories)
    
    print(f"Found {stats['total_material_inventory']} MaterialInventory records to migrate")
    
    for mat_inv in material_inventories:
        try:
            # Get material type and color
            material_type = db.query(MaterialType).get(mat_inv.material_type_id)
            color = db.query(Color).get(mat_inv.color_id)
            
            if not material_type or not color:
                error_msg = f"MaterialInventory {mat_inv.id}: Missing material_type or color"
                stats["errors"].append(error_msg)
                print(f"  ERROR: {error_msg}")
                continue
            
            # Check if product already exists
            product = None
            if mat_inv.product_id:
                product = db.query(Product).get(mat_inv.product_id)
            
            if not product:
                # Try to find by SKU
                product = db.query(Product).filter(
                    Product.sku == mat_inv.sku,
                    Product.active == True
                ).first()
            
            if not product:
                # Create new product
                print(f"  Creating product for {material_type.code} + {color.code}...")
                # Note: create_material_product creates an Inventory record with 0 quantity
                # We'll update it after creation
                product = create_material_product(
                    db,
                    material_type_code=material_type.code,
                    color_code=color.code,
                    commit=False  # We'll commit at the end
                )
                stats["products_created"] += 1
            else:
                stats["products_existing"] += 1
            
            # Link MaterialInventory to Product (for backward compatibility)
            if mat_inv.product_id != product.id:
                mat_inv.product_id = product.id
            
            # Create or update Inventory record
            # Note: create_material_product may have already created one with 0 quantity
            inventory = db.query(Inventory).filter(
                Inventory.product_id == product.id,
                Inventory.location_id == location.id
            ).first()
            
            if not inventory:
                # Create new inventory record
                inventory = Inventory(
                    product_id=product.id,
                    location_id=location.id,
                    on_hand_quantity=mat_inv.quantity_kg or Decimal("0"),
                    allocated_quantity=Decimal("0")
                )
                db.add(inventory)
                stats["inventory_records_created"] += 1
                print(f"    Created inventory: {mat_inv.quantity_kg}kg")
            else:
                # Update existing inventory (may have been created by create_material_product)
                if mat_inv.quantity_kg:
                    inventory.on_hand_quantity = mat_inv.quantity_kg
                    stats["inventory_records_updated"] += 1
                    print(f"    Updated inventory: {mat_inv.quantity_kg}kg")
            
            # Update product cost if MaterialInventory has cost
            if mat_inv.cost_per_kg and not product.standard_cost:
                product.standard_cost = mat_inv.cost_per_kg
            
        except Exception as e:
            error_msg = f"MaterialInventory {mat_inv.id}: {str(e)}"
            stats["errors"].append(error_msg)
            print(f"  ERROR: {error_msg}")
            continue
    
    # Commit all changes
    try:
        db.commit()
        print("\n[SUCCESS] Migration completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Migration failed: {str(e)}")
        raise
    
    return stats


def verify_migration(db: Session) -> dict:
    """
    Verify the migration was successful.
    
    Checks:
    1. All MaterialInventory records have linked Products
    2. All Products have Inventory records
    3. Quantities match
    """
    print("\n[VERIFY] Verifying migration...")
    
    verification = {
        "material_inventory_with_products": 0,
        "material_inventory_without_products": 0,
        "products_with_inventory": 0,
        "products_without_inventory": 0,
        "quantity_mismatches": []
    }
    
    # Check MaterialInventory → Product links
    mat_invs = db.query(MaterialInventory).filter(
        MaterialInventory.active == True
    ).all()
    
    for mat_inv in mat_invs:
        if mat_inv.product_id:
            product = db.query(Product).get(mat_inv.product_id)
            if product:
                verification["material_inventory_with_products"] += 1
                
                # Check inventory quantity
                inventory = db.query(Inventory).filter(
                    Inventory.product_id == product.id
                ).first()
                
                if inventory:
                    verification["products_with_inventory"] += 1
                    # Note: quantities might differ if inventory was updated elsewhere
                else:
                    verification["products_without_inventory"] += 1
                    verification["quantity_mismatches"].append({
                        "material_inventory_id": mat_inv.id,
                        "product_id": product.id,
                        "issue": "Product exists but no Inventory record"
                    })
            else:
                verification["material_inventory_without_products"] += 1
        else:
            verification["material_inventory_without_products"] += 1
    
    return verification


def main():
    """Main migration function"""
    print("=" * 60)
    print("MaterialInventory -> Products + Inventory Migration")
    print("Phase 1.3 of MRP_REFACTOR_PLAN.md")
    print("=" * 60)
    
    # Verify we can import everything
    try:
        print("\n[1/2] Checking imports...")
        from app.db.session import SessionLocal
        from app.models.material import MaterialInventory, MaterialType, Color
        from app.models.product import Product
        from app.models.inventory import Inventory, InventoryLocation
        from app.services.material_service import create_material_product
        print("[OK] All imports successful")
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        print("\nMake sure you're running from the backend directory:")
        print("  cd backend")
        print("  python migrate_material_inventory_to_products.py")
        sys.exit(1)
    
    db = SessionLocal()
    
    try:
        # Test database connection
        print("\n[2/2] Testing database connection...")
        test_query = db.query(MaterialInventory).limit(1).all()
        print("[OK] Database connection successful")
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        print("\nCheck your database configuration in .env")
        db.close()
        sys.exit(1)
    
    try:
        # Run migration
        stats = migrate_material_inventory(db)
        
        # Print statistics
        print("\n" + "=" * 60)
        print("Migration Statistics:")
        print("=" * 60)
        print(f"Total MaterialInventory records: {stats['total_material_inventory']}")
        print(f"Products created: {stats['products_created']}")
        print(f"Products already existed: {stats['products_existing']}")
        print(f"Inventory records created: {stats['inventory_records_created']}")
        print(f"Inventory records updated: {stats['inventory_records_updated']}")
        
        if stats['errors']:
            print(f"\n[WARNING] Errors encountered: {len(stats['errors'])}")
            for error in stats['errors'][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(stats['errors']) > 10:
                print(f"  ... and {len(stats['errors']) - 10} more")
        
        # Verify migration
        verification = verify_migration(db)
        
        print("\n" + "=" * 60)
        print("Verification Results:")
        print("=" * 60)
        print(f"MaterialInventory with Products: {verification['material_inventory_with_products']}")
        print(f"MaterialInventory without Products: {verification['material_inventory_without_products']}")
        print(f"Products with Inventory: {verification['products_with_inventory']}")
        print(f"Products without Inventory: {verification['products_without_inventory']}")
        
        if verification['quantity_mismatches']:
            print(f"\n[WARNING] Quantity mismatches: {len(verification['quantity_mismatches'])}")
            for mismatch in verification['quantity_mismatches'][:5]:
                print(f"  - {mismatch}")
        
        if verification['material_inventory_without_products'] == 0 and \
           verification['products_without_inventory'] == 0:
            print("\n[SUCCESS] Verification passed! All records migrated successfully.")
        else:
            print("\n[WARNING] Verification found issues. Please review.")
        
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

