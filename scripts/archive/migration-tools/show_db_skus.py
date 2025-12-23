"""
Show all SKUs in database
"""
import pyodbc

conn = pyodbc.connect(
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=localhost\SQLEXPRESS;'
    r'DATABASE=BLB3D_ERP;'
    r'Trusted_Connection=yes;'
)
cursor = conn.cursor()

cursor.execute('SELECT sku, name, category FROM products ORDER BY sku')
print('ALL SKUs IN DATABASE:')
print('='*80)
for row in cursor.fetchall():
    print(f'{row[0]:<20} {row[1]:<45} {row[2]}')

conn.close()
