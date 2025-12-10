"""
Material Catalog Import Script v2

Imports material data from MATERIAL_CATALOG_v2.csv into the material tables:
- material_types
- colors  
- material_colors (junction)
- material_inventory

Updated for new CSV format with Material Type column and new material types.
"""
import csv
import os
import sys
from decimal import Decimal
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "mssql+pyodbc://localhost\\SQLEXPRESS/BLB3D_ERP?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"


# ============================================================================
# MATERIAL TYPE DEFINITIONS (Updated with PETG_CF and ABS_GF)
# ============================================================================
MATERIAL_TYPES = {
    "PLA_BASIC": {
        "name": "PLA Basic",
        "base_material": "PLA",
        "density": 1.24,
        "base_price_per_kg": 19.99,
        "price_multiplier": 1.0,
        "volumetric_flow_limit": 21.0,
        "nozzle_temp_min": 190,
        "nozzle_temp_max": 230,
        "bed_temp_min": 45,
        "bed_temp_max": 60,
        "requires_enclosure": False,
        "description": "Standard PLA filament. Good all-around material with easy printability.",
        "strength_rating": 5,
        "display_order": 10,
    },
    "PLA_MATTE": {
        "name": "PLA Matte",
        "base_material": "PLA",
        "density": 1.24,
        "base_price_per_kg": 19.99,
        "price_multiplier": 1.0,
        "volumetric_flow_limit": 21.0,
        "nozzle_temp_min": 190,
        "nozzle_temp_max": 230,
        "bed_temp_min": 45,
        "bed_temp_max": 60,
        "requires_enclosure": False,
        "description": "Matte finish PLA. Same strength as standard PLA with a non-reflective surface.",
        "strength_rating": 5,
        "display_order": 20,
    },
    "PLA_SILK": {
        "name": "PLA Silk",
        "base_material": "PLA",
        "density": 1.24,
        "base_price_per_kg": 22.99,
        "price_multiplier": 1.15,
        "volumetric_flow_limit": 21.0,
        "nozzle_temp_min": 200,
        "nozzle_temp_max": 230,
        "bed_temp_min": 45,
        "bed_temp_max": 60,
        "requires_enclosure": False,
        "description": "Silk finish PLA. Shiny, lustrous appearance.",
        "strength_rating": 4,
        "display_order": 30,
    },
    "PLA_SILK_MULTI": {
        "name": "PLA Silk Multi",
        "base_material": "PLA",
        "density": 1.24,
        "base_price_per_kg": 22.49,
        "price_multiplier": 1.15,
        "volumetric_flow_limit": 21.0,
        "nozzle_temp_min": 200,
        "nozzle_temp_max": 230,
        "bed_temp_min": 45,
        "bed_temp_max": 60,
        "requires_enclosure": False,
        "description": "Multi-color silk PLA. Color-changing effect.",
        "strength_rating": 4,
        "display_order": 40,
    },
    "PETG_HF": {
        "name": "PETG-HF",
        "base_material": "PETG",
        "density": 1.27,
        "base_price_per_kg": 19.99,
        "price_multiplier": 1.2,
        "volumetric_flow_limit": 15.0,
        "nozzle_temp_min": 230,
        "nozzle_temp_max": 260,
        "bed_temp_min": 70,
        "bed_temp_max": 85,
        "requires_enclosure": False,
        "description": "High-flow PETG. More durable than PLA, good chemical resistance.",
        "strength_rating": 7,
        "display_order": 50,
    },
    "PETG_TRANS": {
        "name": "PETG Translucent",
        "base_material": "PETG",
        "density": 1.27,
        "base_price_per_kg": 19.99,
        "price_multiplier": 1.2,
        "volumetric_flow_limit": 15.0,
        "nozzle_temp_min": 230,
        "nozzle_temp_max": 260,
        "bed_temp_min": 70,
        "bed_temp_max": 85,
        "requires_enclosure": False,
        "description": "Translucent PETG. Light transmission for decorative use.",
        "strength_rating": 7,
        "display_order": 55,
    },
    "PETG_CF": {
        "name": "PETG Carbon Fiber",
        "base_material": "PETG",
        "density": 1.27,
        "base_price_per_kg": 28.79,
        "price_multiplier": 1.44,
        "volumetric_flow_limit": 12.0,
        "nozzle_temp_min": 250,
        "nozzle_temp_max": 270,
        "bed_temp_min": 70,
        "bed_temp_max": 80,
        "requires_enclosure": False,
        "description": "Carbon fiber reinforced PETG. High strength and stiffness.",
        "strength_rating": 9,
        "display_order": 56,
    },
    "ABS": {
        "name": "ABS",
        "base_material": "ABS",
        "density": 1.04,
        "base_price_per_kg": 19.99,
        "price_multiplier": 1.1,
        "volumetric_flow_limit": 16.0,
        "nozzle_temp_min": 240,
        "nozzle_temp_max": 270,
        "bed_temp_min": 90,
        "bed_temp_max": 110,
        "requires_enclosure": True,
        "description": "ABS plastic. High impact resistance, heat resistant. Requires enclosure.",
        "strength_rating": 8,
        "display_order": 60,
    },
    "ABS_GF": {
        "name": "ABS Glass Fiber",
        "base_material": "ABS",
        "density": 1.15,
        "base_price_per_kg": 23.99,
        "price_multiplier": 1.2,
        "volumetric_flow_limit": 14.0,
        "nozzle_temp_min": 240,
        "nozzle_temp_max": 260,
        "bed_temp_min": 90,
        "bed_temp_max": 100,
        "requires_enclosure": True,
        "description": "Glass fiber reinforced ABS. Improved stiffness and heat resistance.",
        "strength_rating": 9,
        "display_order": 65,
    },
    "ASA": {
        "name": "ASA",
        "base_material": "ASA",
        "density": 1.07,
        "base_price_per_kg": 23.99,
        "price_multiplier": 1.3,
        "volumetric_flow_limit": 18.0,
        "nozzle_temp_min": 240,
        "nozzle_temp_max": 270,
        "bed_temp_min": 90,
        "bed_temp_max": 110,
        "requires_enclosure": True,
        "description": "ASA - UV resistant ABS alternative. Great for outdoor use.",
        "strength_rating": 8,
        "display_order": 70,
    },
    "TPU_68D": {
        "name": "TPU 68D",
        "base_material": "TPU",
        "density": 1.21,
        "base_price_per_kg": 27.99,
        "price_multiplier": 1.8,
        "volumetric_flow_limit": 3.6,
        "nozzle_temp_min": 210,
        "nozzle_temp_max": 230,
        "bed_temp_min": 45,
        "bed_temp_max": 60,
        "requires_enclosure": False,
        "description": "Flexible TPU 68D (harder). AMS compatible.",
        "strength_rating": 6,
        "display_order": 80,
    },
    "TPU_95A": {
        "name": "TPU 95A",
        "base_material": "TPU",
        "density": 1.21,
        "base_price_per_kg": 33.59,
        "price_multiplier": 1.9,
        "volumetric_flow_limit": 3.0,
        "nozzle_temp_min": 210,
        "nozzle_temp_max": 230,
        "bed_temp_min": 45,
        "bed_temp_max": 60,
        "requires_enclosure": False,
        "description": "Flexible TPU 95A (softer). High flexibility.",
        "strength_rating": 5,
        "display_order": 90,
    },
}


def parse_csv_v2(filepath: str) -> list:
    """
    Parse MATERIAL_CATALOG_v2.csv format
    
    Columns: Category, SKU, Name, Material Type, Material Color Name, HEX Code, Unit, Status, Price/kg, On Hand (g)
    """
    materials = []
    
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Get fields
            category = row.get('Category', '').strip()
            sku = row.get('SKU', '').strip()
            material_type_code = row.get('Material Type', '').strip()
            color_name = row.get('Material Color Name', '').strip()
            hex_code = row.get('HEX Code', '').strip()
            status = row.get('Status', '').strip()
            price_str = row.get('Price/kg', '').strip()
            
            # Skip inactive
            if status != 'Active':
                continue
            
            # Skip if no material type
            if not material_type_code:
                continue
            
            # Extract color code from SKU (last part after the last dash)
            parts = sku.split('-')
            color_code = parts[-1] if len(parts) > 3 else None
            
            if not color_code:
                continue
            
            # Parse price
            price = None
            if price_str:
                try:
                    price = Decimal(price_str)
                except:
                    pass
            
            materials.append({
                'sku': sku,
                'material_type_code': material_type_code,
                'color_code': color_code,
                'color_name': color_name,
                'hex_code': hex_code if hex_code.startswith('#') else None,
                'price_per_kg': price,
            })
    
    return materials


def import_materials_v2(csv_path: str, dry_run: bool = False):
    """
    Import materials from CSV v2 format into database
    """
    print(f"Parsing CSV: {csv_path}")
    materials = parse_csv_v2(csv_path)
    print(f"Found {len(materials)} active materials to import")
    
    if dry_run:
        print("\n=== DRY RUN - No changes will be made ===\n")
    
    # Connect to database
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # ====================================================================
        # Step 1: Insert/Update Material Types
        # ====================================================================
        print("\n--- Checking/Inserting Material Types ---")
        material_type_ids = {}
        
        for code, props in MATERIAL_TYPES.items():
            # Check if exists
            result = session.execute(
                text("SELECT id FROM material_types WHERE code = :code"),
                {"code": code}
            ).fetchone()
            
            if result:
                material_type_ids[code] = result[0]
                print(f"  [EXISTS] {code} (id={result[0]})")
            else:
                if not dry_run:
                    session.execute(
                        text("""
                            INSERT INTO material_types (
                                code, name, base_material, process_type, density,
                                volumetric_flow_limit, nozzle_temp_min, nozzle_temp_max,
                                bed_temp_min, bed_temp_max, requires_enclosure,
                                base_price_per_kg, price_multiplier, description,
                                strength_rating, display_order, is_customer_visible, active
                            ) VALUES (
                                :code, :name, :base_material, 'FDM', :density,
                                :volumetric_flow_limit, :nozzle_temp_min, :nozzle_temp_max,
                                :bed_temp_min, :bed_temp_max, :requires_enclosure,
                                :base_price_per_kg, :price_multiplier, :description,
                                :strength_rating, :display_order, 1, 1
                            )
                        """),
                        {
                            "code": code,
                            "name": props["name"],
                            "base_material": props["base_material"],
                            "density": props["density"],
                            "volumetric_flow_limit": props["volumetric_flow_limit"],
                            "nozzle_temp_min": props["nozzle_temp_min"],
                            "nozzle_temp_max": props["nozzle_temp_max"],
                            "bed_temp_min": props["bed_temp_min"],
                            "bed_temp_max": props["bed_temp_max"],
                            "requires_enclosure": 1 if props["requires_enclosure"] else 0,
                            "base_price_per_kg": props["base_price_per_kg"],
                            "price_multiplier": props["price_multiplier"],
                            "description": props["description"],
                            "strength_rating": props["strength_rating"],
                            "display_order": props["display_order"],
                        }
                    )
                    session.commit()
                    
                    result = session.execute(
                        text("SELECT id FROM material_types WHERE code = :code"),
                        {"code": code}
                    ).fetchone()
                    material_type_ids[code] = result[0]
                    
                print(f"  [INSERT] {code}")
        
        # ====================================================================
        # Step 2: Insert Colors (unique by code)
        # ====================================================================
        print("\n--- Inserting Colors ---")
        color_ids = {}
        seen_colors = {}
        
        for mat in materials:
            color_code = mat['color_code']
            if color_code in seen_colors:
                continue
            seen_colors[color_code] = mat
            
            # Check if exists
            result = session.execute(
                text("SELECT id FROM colors WHERE code = :code"),
                {"code": color_code}
            ).fetchone()
            
            if result:
                color_ids[color_code] = result[0]
                # Don't print - too many
            else:
                if not dry_run:
                    session.execute(
                        text("""
                            INSERT INTO colors (
                                code, name, hex_code,
                                display_order, is_customer_visible, active
                            ) VALUES (
                                :code, :name, :hex_code,
                                100, 1, 1
                            )
                        """),
                        {
                            "code": color_code,
                            "name": mat['color_name'],
                            "hex_code": mat['hex_code'],
                        }
                    )
                    session.commit()
                    
                    result = session.execute(
                        text("SELECT id FROM colors WHERE code = :code"),
                        {"code": color_code}
                    ).fetchone()
                    color_ids[color_code] = result[0]
                    
                print(f"  [INSERT] {color_code} - {mat['color_name']}")
        
        print(f"  Total colors: {len(color_ids)}")
        
        # ====================================================================
        # Step 3: Insert Material-Color Combinations
        # ====================================================================
        print("\n--- Inserting Material-Color Combinations ---")
        combo_count = 0
        
        for mat in materials:
            material_type_code = mat['material_type_code']
            color_code = mat['color_code']
            
            if dry_run:
                combo_count += 1
                continue
            
            material_type_id = material_type_ids.get(material_type_code)
            color_id = color_ids.get(color_code)
            
            if not material_type_id or not color_id:
                print(f"  [SKIP] Missing ID for {material_type_code} + {color_code}")
                continue
            
            # Check if exists
            result = session.execute(
                text("""
                    SELECT id FROM material_colors 
                    WHERE material_type_id = :mt_id AND color_id = :c_id
                """),
                {"mt_id": material_type_id, "c_id": color_id}
            ).fetchone()
            
            if not result:
                session.execute(
                    text("""
                        INSERT INTO material_colors (
                            material_type_id, color_id, is_customer_visible, active
                        ) VALUES (
                            :mt_id, :c_id, 1, 1
                        )
                    """),
                    {"mt_id": material_type_id, "c_id": color_id}
                )
                session.commit()
                combo_count += 1
        
        print(f"  Inserted {combo_count} combinations")
        
        # ====================================================================
        # Step 4: Insert Material Inventory
        # ====================================================================
        print("\n--- Inserting Material Inventory ---")
        inv_count = 0
        
        for mat in materials:
            sku = mat['sku']
            material_type_code = mat['material_type_code']
            color_code = mat['color_code']
            
            if dry_run:
                inv_count += 1
                continue
            
            material_type_id = material_type_ids.get(material_type_code)
            color_id = color_ids.get(color_code)
            
            if not material_type_id or not color_id:
                continue
            
            # Check if exists
            result = session.execute(
                text("""
                    SELECT id FROM material_inventory 
                    WHERE sku = :sku
                """),
                {"sku": sku}
            ).fetchone()
            
            if not result:
                price = mat['price_per_kg'] or MATERIAL_TYPES.get(material_type_code, {}).get('base_price_per_kg', 19.99)
                
                session.execute(
                    text("""
                        INSERT INTO material_inventory (
                            material_type_id, color_id, sku,
                            in_stock, quantity_kg, cost_per_kg, active
                        ) VALUES (
                            :mt_id, :c_id, :sku,
                            1, 1.0, :cost, 1
                        )
                    """),
                    {
                        "mt_id": material_type_id,
                        "c_id": color_id,
                        "sku": sku,
                        "cost": price,
                    }
                )
                session.commit()
                inv_count += 1
        
        print(f"  Inserted {inv_count} inventory items")
        
        print("\n=== Import Complete ===")
        
        # Summary
        print("\n--- Summary ---")
        result = session.execute(text("SELECT COUNT(*) FROM material_types")).fetchone()
        print(f"Material Types: {result[0]}")
        result = session.execute(text("SELECT COUNT(*) FROM colors")).fetchone()
        print(f"Colors: {result[0]}")
        result = session.execute(text("SELECT COUNT(*) FROM material_colors")).fetchone()
        print(f"Material-Color Combinations: {result[0]}")
        result = session.execute(text("SELECT COUNT(*) FROM material_inventory")).fetchone()
        print(f"Inventory Items: {result[0]}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Import materials from CSV v2")
    parser.add_argument("csv_path", nargs='?', 
                       default=r"C:\Users\brand\OneDrive\Documents\blb3d-erp\MATERIAL_CATALOG_v2.csv",
                       help="Path to MATERIAL_CATALOG_v2.csv")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    
    args = parser.parse_args()
    
    import_materials_v2(args.csv_path, dry_run=args.dry_run)
