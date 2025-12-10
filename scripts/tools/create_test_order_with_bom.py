"""
Create a test sales order with a product that has a BOM

This script:
1. Finds or creates a finished good product
2. Creates a BOM with material components
3. Creates a sales order for that product
4. Verifies the setup
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime

from app.db.session import SessionLocal
from app.models.product import Product
from app.models.bom import BOM, BOMLine
from app.models.sales_order import SalesOrder
from app.models.user import User
from app.models.material import MaterialType, Color

def create_test_order_with_bom():
    db: Session = SessionLocal()
    
    try:
        print("=" * 60)
        print("Creating Test Order with BOM")
        print("=" * 60)
        
        # 1. Get or create admin user
        admin_user = db.query(User).filter(User.account_type == "admin").first()
        if not admin_user:
            print("ERROR: No admin user found. Please create an admin user first.")
            return
        print(f"✓ Using admin user: {admin_user.email} (ID: {admin_user.id})")
        
        # 2. Find or create a finished good product
        test_product = db.query(Product).filter(
            Product.sku.like("TEST-%"),
            Product.item_type == "finished_good"
        ).first()
        
        if not test_product:
            print("\nCreating test product...")
            # Get next SKU number
            last_test = db.query(Product).filter(Product.sku.like("TEST-%")).order_by(Product.sku.desc()).first()
            next_num = 1
            if last_test:
                try:
                    next_num = int(last_test.sku.split("-")[1]) + 1
                except:
                    pass
            
            test_product = Product(
                sku=f"TEST-{next_num:03d}",
                name="Test Product with BOM",
                item_type="finished_good",
                procurement_type="make",
                unit="EA",
                standard_cost=Decimal("10.00"),
                selling_price=Decimal("25.00"),
                active=True,
            )
            db.add(test_product)
            db.flush()
            print(f"✓ Created product: {test_product.sku} - {test_product.name}")
        else:
            print(f"✓ Using existing product: {test_product.sku} - {test_product.name}")
        
        # 3. Check if BOM exists
        bom = db.query(BOM).filter(
            BOM.product_id == test_product.id,
            BOM.active == True
        ).first()
        
        if not bom:
            print("\nCreating BOM...")
            # Get next BOM code
            last_bom = db.query(BOM).order_by(BOM.code.desc()).first()
            bom_num = 1
            if last_bom:
                try:
                    bom_num = int(last_bom.code.split("-")[1]) + 1
                except:
                    pass
            
            bom = BOM(
                product_id=test_product.id,
                code=f"BOM-{bom_num:04d}",
                name=f"BOM for {test_product.sku}",
                active=True,
            )
            db.add(bom)
            db.flush()
            print(f"✓ Created BOM: {bom.code}")
            
            # 4. Add BOM lines with materials
            print("\nAdding BOM lines...")
            
            # Find a material product (any material type)
            material_product = db.query(Product).filter(
                Product.material_type_id.isnot(None),
                Product.active == True
            ).first()
            
            if not material_product:
                # Try finding by name
                material_product = db.query(Product).filter(
                    (Product.name.ilike("%PLA%")) | (Product.name.ilike("%PETG%")),
                    Product.active == True
                ).first()
            
            if material_product:
                # Add material line
                bom_line_material = BOMLine(
                    bom_id=bom.id,
                    component_id=material_product.id,
                    quantity=Decimal("0.125"),  # 125g per unit
                    unit="kg",
                    sequence=10,
                    scrap_factor=Decimal("5.0"),  # 5% scrap
                    is_cost_only=False,
                )
                db.add(bom_line_material)
                print(f"  ✓ Added material: {material_product.sku} - {material_product.name} (0.125 kg)")
            else:
                print("  ⚠ No material product found, skipping material line")
            
            # Find a component product (or create a simple one)
            component = db.query(Product).filter(
                Product.item_type == "component",
                Product.active == True
            ).first()
            
            if component:
                bom_line_component = BOMLine(
                    bom_id=bom.id,
                    component_id=component.id,
                    quantity=Decimal("4"),
                    unit="EA",
                    sequence=20,
                    scrap_factor=Decimal("0"),
                    is_cost_only=False,
                )
                db.add(bom_line_component)
                print(f"  ✓ Added component: {component.sku} - {component.name} (4 EA)")
            else:
                print("  ⚠ No component product found, skipping component line")
            
            db.flush()
        else:
            print(f"✓ Using existing BOM: {bom.code}")
            line_count = db.query(BOMLine).filter(BOMLine.bom_id == bom.id).count()
            print(f"  BOM has {line_count} lines")
        
        # 5. Create sales order
        print("\nCreating sales order...")
        
        # Get next order number
        year = datetime.now().year
        last_order = db.query(SalesOrder).filter(
            SalesOrder.order_number.like(f"SO-{year}-%")
        ).order_by(SalesOrder.order_number.desc()).first()
        
        order_num = 1
        if last_order:
            try:
                order_num = int(last_order.order_number.split("-")[2]) + 1
            except:
                pass
        
        order_number = f"SO-{year}-{order_num:03d}"
        
        # Create as line_item order (simpler - has product_id in lines)
        sales_order = SalesOrder(
            user_id=admin_user.id,
            order_number=order_number,
            order_type="line_item",  # Use line_item for simpler testing
            source="manual",
            product_name=test_product.name,  # Summary name
            quantity=10,  # Total quantity
            material_type="PLA",  # Default
            finish="standard",
            unit_price=test_product.selling_price,
            total_price=test_product.selling_price * 10,
            tax_amount=Decimal("0"),
            shipping_cost=Decimal("0"),
            grand_total=test_product.selling_price * 10,
            status="confirmed",
            payment_status="paid",
            rush_level="standard",
        )
        db.add(sales_order)
        db.flush()
        
        # Create order line with product
        from app.models.sales_order import SalesOrderLine
        order_line = SalesOrderLine(
            sales_order_id=sales_order.id,
            product_id=test_product.id,  # Link product here
            quantity=Decimal("10"),
            unit_price=test_product.selling_price,
            total=test_product.selling_price * 10,
            discount=Decimal("0"),
            tax_rate=Decimal("0"),
            notes="Test order line",
            created_by=admin_user.id,
        )
        db.add(order_line)
        
        print(f"✓ Created sales order: {order_number}")
        print(f"  Product: {test_product.sku} - {test_product.name}")
        print(f"  Quantity: 10")
        print(f"  Total: ${sales_order.grand_total}")
        
        # 6. Verify setup
        print("\n" + "=" * 60)
        print("Verification")
        print("=" * 60)
        
        # Check BOM lines
        bom_lines = db.query(BOMLine).filter(BOMLine.bom_id == bom.id).all()
        print(f"\nBOM Lines ({len(bom_lines)}):")
        for line in bom_lines:
            component = db.query(Product).filter(Product.id == line.component_id).first()
            print(f"  - {component.sku if component else 'N/A'}: {line.quantity} {line.unit}")
        
        # Check routing (optional)
        try:
            from app.models.manufacturing import Routing
            routing = db.query(Routing).filter(
                Routing.product_id == test_product.id,
                Routing.is_active == True
            ).first()
            
            if routing:
                print(f"\n✓ Routing found: {routing.code}")
                from app.models.manufacturing import RoutingOperation
                op_count = db.query(RoutingOperation).filter(RoutingOperation.routing_id == routing.id).count()
                print(f"  Operations: {op_count}")
            else:
                print("\n⚠ No routing found (optional)")
        except ImportError:
            print("\n⚠ Routing model not available (optional)")
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print(f"\nTest Order ID: {sales_order.id}")
        print(f"Order Number: {order_number}")
        print(f"Product ID: {test_product.id}")
        print(f"BOM ID: {bom.id}")
        print(f"\nView in UI: http://localhost:5173/admin/orders/{sales_order.id}")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_order_with_bom()

