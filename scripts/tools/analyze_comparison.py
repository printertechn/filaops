"""
Quick comparison of Squarespace products vs database
"""
import csv
import pyodbc

def get_connection():
    """Connect to SQL Server Express"""
    conn_str = (
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        r'SERVER=localhost\SQLEXPRESS;'
        r'DATABASE=BLB3D_ERP;'
        r'Trusted_Connection=yes;'
    )
    return pyodbc.connect(conn_str)

def get_existing_skus():
    """Get all SKUs currently in database"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT sku FROM products")
    skus = set(row[0] for row in cursor.fetchall())
    conn.close()
    return skus

# Get existing SKUs from database
print("Fetching existing SKUs from database...")
existing_skus = get_existing_skus()
print(f"Found {len(existing_skus)} SKUs in database")
print()

# Read Squarespace export
csv_path = r'c:\Users\brand\OneDrive\Documents\blb3d-erp\Squarespace_Products_11222025.csv'
print(f"Reading Squarespace export: {csv_path}")
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    squarespace_products = list(reader)

print(f"Found {len(squarespace_products)} products in Squarespace")
print()

# Compare and categorize
new_products = []
existing_products = []
missing_sku = []

for product in squarespace_products:
    sku = product.get('SKU', '').strip()

    if not sku:
        missing_sku.append(product)
        continue

    if sku in existing_skus:
        existing_products.append(product)
    else:
        new_products.append(product)

# Display results
print("="*80)
print("COMPARISON RESULTS")
print("="*80)
print()

print(f"Products in Database:        {len(existing_skus)}")
print(f"Products in Squarespace:     {len(squarespace_products)}")
print(f"  - Already in database:     {len(existing_products)}")
print(f"  - NEW (not in database):   {len(new_products)}")
print(f"  - Missing SKU:             {len(missing_sku)}")
print()

if new_products:
    print("="*80)
    print("NEW PRODUCTS TO IMPORT:")
    print("="*80)
    print()

    for i, product in enumerate(new_products, 1):
        sku = product.get('SKU', '')
        name = product.get('Title', 'N/A')
        price = product.get('Price', 'N/A')
        visible = product.get('Visible', 'N/A')
        print(f"{i:3}. {sku:<20} ${price:<8} {visible:<5} {name}")

    print()
else:
    print("No new products found. Your database is up to date!")

print()

if existing_products:
    print("="*80)
    print("EXISTING PRODUCTS (sample):")
    print("="*80)
    print()

    for i, product in enumerate(existing_products[:10], 1):
        sku = product.get('SKU', '')
        name = product.get('Title', 'N/A')
        price = product.get('Price', 'N/A')
        print(f"{i:2}. {sku:<20} ${price:<8} {name}")

    if len(existing_products) > 10:
        print(f"    ... and {len(existing_products) - 10} more")
    print()

print("="*80)
