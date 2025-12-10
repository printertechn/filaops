"""
Check MaterialInventory and Products status

This script checks:
1. How many MaterialInventory records exist (active and inactive)
2. How many Products exist with material_type_id/color_id
3. Whether migration is needed
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.material import MaterialInventory, MaterialType, Color
from app.models.product import Product
from app.models.inventory import Inventory


def check_status():
    """Check current status of materials"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("Material Inventory Status Check")
        print("=" * 60)
        
        # Check MaterialInventory table
        print("\n1. MaterialInventory Table:")
        total_mat_inv = db.query(MaterialInventory).count()
        active_mat_inv = db.query(MaterialInventory).filter(
            MaterialInventory.active == True
        ).count()
        inactive_mat_inv = total_mat_inv - active_mat_inv
        
        print(f"   Total records: {total_mat_inv}")
        print(f"   Active: {active_mat_inv}")
        print(f"   Inactive: {inactive_mat_inv}")
        
        if total_mat_inv > 0:
            print("\n   Sample MaterialInventory records:")
            samples = db.query(MaterialInventory).limit(5).all()
            for mat_inv in samples:
                material_type = db.query(MaterialType).get(mat_inv.material_type_id)
                color = db.query(Color).get(mat_inv.color_id)
                print(f"     - ID {mat_inv.id}: {material_type.code if material_type else 'N/A'} + {color.code if color else 'N/A'} "
                      f"(SKU: {mat_inv.sku}, Qty: {mat_inv.quantity_kg}kg, Active: {mat_inv.active})")
        
        # Check Products with material_type_id
        print("\n2. Products Table (with material_type_id):")
        try:
            products_with_material = db.query(Product).filter(
                Product.material_type_id.isnot(None)
            ).count()
            print(f"   Products with material_type_id: {products_with_material}")
        except Exception as e:
            print(f"   ⚠️  Could not query material_type_id (may need to restart Python): {e}")
            products_with_material = 0
        
        if products_with_material > 0:
            print("\n   Sample Products with material_type_id:")
            samples = db.query(Product).filter(
                Product.material_type_id.isnot(None)
            ).limit(5).all()
            for product in samples:
                material_type = db.query(MaterialType).get(product.material_type_id)
                color = db.query(Color).get(product.color_id) if product.color_id else None
                print(f"     - {product.sku}: {product.name} "
                      f"(Material: {material_type.code if material_type else 'N/A'}, "
                      f"Color: {color.code if color else 'N/A'})")
        
        # Check Products with "MAT-" SKU prefix (material products)
        print("\n3. Products with MAT- SKU prefix:")
        mat_products = db.query(Product).filter(
            Product.sku.like('MAT-%')
        ).count()
        print(f"   Products with MAT- prefix: {mat_products}")
        
        if mat_products > 0:
            print("\n   Sample MAT- products:")
            samples = db.query(Product).filter(
                Product.sku.like('MAT-%')
            ).limit(5).all()
            for product in samples:
                print(f"     - {product.sku}: {product.name} "
                      f"(Type: {product.item_type}, Active: {product.active})")
        
        # Check Inventory for material products
        print("\n4. Inventory Records for Material Products:")
        if products_with_material > 0:
            material_product_ids = [p.id for p in db.query(Product.id).filter(
                Product.material_type_id.isnot(None)
            ).all()]
            
            inventory_count = db.query(Inventory).filter(
                Inventory.product_id.in_(material_product_ids)
            ).count()
            print(f"   Inventory records for material products: {inventory_count}")
            
            if inventory_count > 0:
                total_qty = db.query(
                    Inventory.product_id,
                    Inventory.on_hand_quantity
                ).filter(
                    Inventory.product_id.in_(material_product_ids)
                ).all()
                total_kg = sum(float(qty) for _, qty in total_qty)
                print(f"   Total quantity across all locations: {total_kg}kg")
        
        # Summary
        print("\n" + "=" * 60)
        print("Summary:")
        print("=" * 60)
        
        if total_mat_inv == 0:
            print("✅ No MaterialInventory records found.")
            if products_with_material > 0:
                print("✅ Materials already exist as Products (migration may have already run)")
            else:
                print("⚠️  No materials found in either table. You may need to:")
                print("   1. Create materials via POST /api/v1/items/material")
                print("   2. Or import materials from your existing system")
        elif active_mat_inv > 0:
            print(f"⚠️  Found {active_mat_inv} active MaterialInventory records to migrate")
            print("   Run: python migrate_material_inventory_to_products.py")
        else:
            print(f"ℹ️  Found {total_mat_inv} MaterialInventory records (all inactive)")
            print("   Migration script only migrates active records")
            print("   If you want to migrate inactive records, modify the filter")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_status()

