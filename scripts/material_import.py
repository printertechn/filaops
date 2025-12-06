"""
Material Catalog Import Script

Imports material data from MATERIAL_CATALOG.csv into the new material tables:
- material_types
- colors  
- material_colors (junction)
- material_inventory

Run this after executing material_tables.sql
"""
import csv
import re
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
# MATERIAL TYPE DEFINITIONS
# ============================================================================
# These define the material types with their properties

MATERIAL_TYPES = {
    "PLA Basic": {
        "code": "PLA_BASIC",
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
    "PLA Matte": {
        "code": "PLA_MATTE",
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
    "PLA Silk": {
        "code": "PLA_SILK",
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
        "description": "Silk finish PLA. Shiny, lustrous appearance. Slightly less strong than standard PLA.",
        "strength_rating": 4,
        "display_order": 30,
    },
    "PLA Silk Multi": {
        "code": "PLA_SILK_MULTI",
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
        "description": "Multi-color silk PLA. Color-changing effect. Decorative use.",
        "strength_rating": 4,
        "display_order": 40,
    },
    "PETG-HF": {
        "code": "PETG_HF",
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
    "PETG Translucent": {
        "code": "PETG_TRANS",
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
        "description": "Translucent PETG. Light transmission for decorative or functional use.",
        "strength_rating": 7,
        "display_order": 55,
    },
    "ABS": {
        "code": "ABS",
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
    "ASA": {
        "code": "ASA",
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
        "description": "ASA - UV resistant ABS alternative. Great for outdoor use. Requires enclosure.",
        "strength_rating": 8,
        "display_order": 70,
    },
    "TPU 68D": {
        "code": "TPU_68D",
        "base_material": "TPU",
        "density": 1.21,
        "base_price_per_kg": 31.19,
        "price_multiplier": 1.8,
        "volumetric_flow_limit": 3.6,
        "nozzle_temp_min": 210,
        "nozzle_temp_max": 230,
        "bed_temp_min": 45,
        "bed_temp_max": 60,
        "requires_enclosure": False,
        "description": "Flexible TPU 68D (harder). AMS compatible. Good for functional flexible parts.",
        "strength_rating": 6,
        "display_order": 80,
    },
    "TPU 95A": {
        "code": "TPU_95A",
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
        "description": "Flexible TPU 95A (softer). High flexibility for gaskets, grips, etc.",
        "strength_rating": 5,
        "display_order": 90,
    },
}


def normalize_color_code(color_name: str) -> str:
    """
    Convert color name to a standardized code
    
    Examples:
        "Black" -> "BLK"
        "Jade White" -> "JADEWHT"
        "Mystic Magenta" -> "MYSTICMAG"
    """
    if not color_name or color_name == "N/A":
        return None
    
    # Common abbreviations
    abbreviations = {
        "black": "BLK",
        "white": "WHT",
        "gray": "GRY",
        "grey": "GRY",
        "red": "RED",
        "blue": "BLU",
        "green": "GRN",
        "yellow": "YLW",
        "orange": "ORG",
        "pink": "PNK",
        "purple": "PRP",
        "brown": "BRN",
        "gold": "GLD",
        "silver": "SLV",
        "cyan": "CYN",
        "magenta": "MAG",
        "beige": "BGE",
        "bronze": "BRZ",
        "turquoise": "TRQ",
    }
    
    # Clean up the name
    name_lower = color_name.lower().strip()
    
    # Try exact match first
    if name_lower in abbreviations:
        return abbreviations[name_lower].upper()
    
    # For compound names, create code from first letters or abbreviate each word
    words = name_lower.replace("-", " ").split()
    if len(words) == 1:
        # Single word - take first 3-4 letters
        return name_lower[:4].upper()
    else:
        # Multiple words - abbreviate each
        code_parts = []
        for word in words:
            if word in abbreviations:
                code_parts.append(abbreviations[word])
            else:
                code_parts.append(word[:3].upper())
        return "".join(code_parts)[:10]  # Max 10 chars


def normalize_category_to_material_type(category: str) -> str:
    """
    Map CSV category to material type code
    """
    category_map = {
        "PLA (Generic)": None,  # Discontinued
        "PLA Basic": "PLA_BASIC",
        "PLA Matte": "PLA_MATTE",
        "PLA Silk": "PLA_SILK",
        "PLA SIlk": "PLA_SILK",  # Handle typo in CSV
        "PLA Silk Multi": "PLA_SILK_MULTI",
        "PETG-HF": "PETG_HF",
        "PETG Translucent": "PETG_TRANS",
        "ABS": "ABS",
        "ASA": "ASA",
        "TPU 68D": "TPU_68D",
        "TPU 95A": "TPU_95A",
    }
    return category_map.get(category)


def generate_sku(material_code: str, color_code: str) -> str:
    """
    Generate new SKU in format: MAT-FDM-{MATERIAL}-{COLOR}
    """
    return f"MAT-FDM-{material_code}-{color_code}"


def parse_csv(filepath: str) -> list:
    """
    Parse the CSV file and return structured data
    """
    materials = []
    
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            category = row.get('Category', '').strip()
            status = row.get('Status', '').strip()
            color_name = row.get('Material Color Name', '').strip()
            hex_code = row.get('material color HEX code (if available)', '').strip()
            old_sku = row.get('SKU', '').strip()
            price = row.get('Price/kg', '').strip()
            
            # Skip discontinued or empty entries
            if status == 'Discontinued':
                continue
            if not color_name or color_name == 'N/A':
                continue
            
            # Map category to material type
            material_type_code = normalize_category_to_material_type(category)
            if not material_type_code:
                continue
            
            # Generate color code
            color_code = normalize_color_code(color_name)
            if not color_code:
                continue
            
            # Parse hex code(s)
            primary_hex = None
            secondary_hex = None
            if hex_code and hex_code != 'N/A':
                # Handle multi-color hex codes like "#720062, #3A913F"
                hex_parts = [h.strip() for h in hex_code.split(',')]
                if len(hex_parts) >= 1:
                    primary_hex = hex_parts[0] if hex_parts[0].startswith('#') else None
                if len(hex_parts) >= 2:
                    secondary_hex = hex_parts[1] if hex_parts[1].startswith('#') else None
            
            # Parse price
            price_value = None
            if price:
                try:
                    price_value = Decimal(price)
                except:
                    pass
            
            materials.append({
                'category': category,
                'material_type_code': material_type_code,
                'color_name': color_name,
                'color_code': color_code,
                'primary_hex': primary_hex,
                'secondary_hex': secondary_hex,
                'old_sku': old_sku,
                'price_per_kg': price_value,
            })
    
    return materials


def import_materials(csv_path: str, dry_run: bool = False):
    """
    Import materials from CSV into database
    """
    print(f"Parsing CSV: {csv_path}")
    materials = parse_csv(csv_path)
    print(f"Found {len(materials)} active materials to import")
    
    if dry_run:
        print("\n=== DRY RUN - No changes will be made ===\n")
    
    # Connect to database
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # ====================================================================
        # Step 1: Insert Material Types
        # ====================================================================
        print("\n--- Inserting Material Types ---")
        material_type_ids = {}
        
        for name, props in MATERIAL_TYPES.items():
            # Check if exists
            result = session.execute(
                text("SELECT id FROM material_types WHERE code = :code"),
                {"code": props["code"]}
            ).fetchone()
            
            if result:
                material_type_ids[props["code"]] = result[0]
                print(f"  [EXISTS] {props['code']} (id={result[0]})")
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
                            "code": props["code"],
                            "name": name,
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
                    
                    # Get the ID
                    result = session.execute(
                        text("SELECT id FROM material_types WHERE code = :code"),
                        {"code": props["code"]}
                    ).fetchone()
                    material_type_ids[props["code"]] = result[0]
                    
                print(f"  [INSERT] {props['code']}")
        
        # ====================================================================
        # Step 2: Insert Colors (unique)
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
                print(f"  [EXISTS] {color_code} - {mat['color_name']} (id={result[0]})")
            else:
                if not dry_run:
                    session.execute(
                        text("""
                            INSERT INTO colors (
                                code, name, hex_code, hex_code_secondary,
                                display_order, is_customer_visible, active
                            ) VALUES (
                                :code, :name, :hex_code, :hex_code_secondary,
                                100, 1, 1
                            )
                        """),
                        {
                            "code": color_code,
                            "name": mat['color_name'],
                            "hex_code": mat['primary_hex'],
                            "hex_code_secondary": mat['secondary_hex'],
                        }
                    )
                    session.commit()
                    
                    result = session.execute(
                        text("SELECT id FROM colors WHERE code = :code"),
                        {"code": color_code}
                    ).fetchone()
                    color_ids[color_code] = result[0]
                    
                print(f"  [INSERT] {color_code} - {mat['color_name']}")
        
        # ====================================================================
        # Step 3: Insert Material-Color Combinations
        # ====================================================================
        print("\n--- Inserting Material-Color Combinations ---")
        
        for mat in materials:
            material_type_code = mat['material_type_code']
            color_code = mat['color_code']
            
            if dry_run:
                print(f"  [WOULD INSERT] {material_type_code} + {color_code}")
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
            
            if result:
                print(f"  [EXISTS] {material_type_code} + {color_code}")
            else:
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
                print(f"  [INSERT] {material_type_code} + {color_code}")
        
        # ====================================================================
        # Step 4: Insert Material Inventory
        # ====================================================================
        print("\n--- Inserting Material Inventory ---")
        
        for mat in materials:
            material_type_code = mat['material_type_code']
            color_code = mat['color_code']
            new_sku = generate_sku(material_type_code, color_code)
            
            if dry_run:
                print(f"  [WOULD INSERT] {new_sku} ({mat['old_sku']})")
                continue
            
            material_type_id = material_type_ids.get(material_type_code)
            color_id = color_ids.get(color_code)
            
            if not material_type_id or not color_id:
                continue
            
            # Check if exists
            result = session.execute(
                text("""
                    SELECT id FROM material_inventory 
                    WHERE material_type_id = :mt_id AND color_id = :c_id
                """),
                {"mt_id": material_type_id, "c_id": color_id}
            ).fetchone()
            
            if result:
                print(f"  [EXISTS] {new_sku}")
            else:
                # Get price from material type if not specified
                price = mat['price_per_kg']
                if not price:
                    price = MATERIAL_TYPES.get(mat['category'], {}).get('base_price_per_kg', 19.99)
                
                session.execute(
                    text("""
                        INSERT INTO material_inventory (
                            material_type_id, color_id, sku,
                            in_stock, quantity_kg, cost_per_kg, active
                        ) VALUES (
                            :mt_id, :c_id, :sku,
                            1, 0, :cost, 1
                        )
                    """),
                    {
                        "mt_id": material_type_id,
                        "c_id": color_id,
                        "sku": new_sku,
                        "cost": price,
                    }
                )
                session.commit()
                print(f"  [INSERT] {new_sku} (was {mat['old_sku']})")
        
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
    
    parser = argparse.ArgumentParser(description="Import materials from CSV")
    parser.add_argument("csv_path", help="Path to MATERIAL_CATALOG.csv")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    
    args = parser.parse_args()
    
    import_materials(args.csv_path, dry_run=args.dry_run)
