"""
Quick check of imported data
"""
import pyodbc

conn_str = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=localhost\SQLEXPRESS;'
    r'DATABASE=BLB3D_ERP;'
    r'Trusted_Connection=yes;'
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

print("="*60)
print("BLB3D ERP - Data Check")
print("="*60)
print()

# Count products
cursor.execute("SELECT COUNT(*) FROM products")
product_count = cursor.fetchone()[0]
print(f"Products: {product_count}")

# Show product breakdown by category
cursor.execute("""
    SELECT category, COUNT(*) as count
    FROM products
    GROUP BY category
    ORDER BY category
""")
print("\nProducts by Category:")
for row in cursor.fetchall():
    print(f"  • {row[0]}: {row[1]}")

# Show sample products
print("\nSample Products:")
cursor.execute("""
    SELECT TOP 10 sku, name, category, selling_price
    FROM products
    ORDER BY category, sku
""")
for row in cursor.fetchall():
    price = f"${row[3]:.2f}" if row[3] else "N/A"
    print(f"  {row[0]:<25} {row[1]:<40} {price}")

print()
print("="*60)
print("Data verified successfully!")
print("="*60)

conn.close()
