"""
Test SQL Server database connection
Run this to verify the backend can connect to BLB3D_ERP database
"""
import pyodbc
import sys

def test_connection():
    """Test connection to SQL Server Express"""
    print("="*60)
    print("BLB3D ERP - Database Connection Test")
    print("="*60)
    print()

    # Connection string for SQL Server Express with Windows Authentication
    conn_str = (
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        r'SERVER=localhost\SQLEXPRESS;'
        r'DATABASE=BLB3D_ERP;'
        r'Trusted_Connection=yes;'
    )

    print("Connection String:")
    print(f"  {conn_str}")
    print()

    try:
        print("Attempting to connect...")
        conn = pyodbc.connect(conn_str)
        print("✅ Connected successfully!")
        print()

        # Get cursor
        cursor = conn.cursor()

        # Test query: Get database name and version
        print("Running test query...")
        cursor.execute("SELECT DB_NAME() AS [Database], @@VERSION AS [Version]")
        row = cursor.fetchone()

        print()
        print("Database Information:")
        print(f"  Database: {row[0]}")
        print(f"  SQL Server Version:")
        for line in row[1].split('\n'):
            if line.strip():
                print(f"    {line.strip()}")
        print()

        # Count tables
        cursor.execute("""
            SELECT COUNT(*) AS table_count
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
        """)
        table_count = cursor.fetchone()[0]
        print(f"Tables Found: {table_count}")

        if table_count == 20:
            print("✅ All 20 tables created successfully!")
        else:
            print(f"⚠️  Expected 20 tables, found {table_count}")
        print()

        # List all tables
        cursor.execute("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)

        print("Tables in database:")
        for row in cursor.fetchall():
            print(f"  ✓ {row[0]}")
        print()

        # Check for data in key tables
        cursor.execute("SELECT COUNT(*) FROM inventory_locations")
        loc_count = cursor.fetchone()[0]
        print(f"Inventory Locations: {loc_count}")

        cursor.execute("SELECT COUNT(*) FROM accounts")
        acc_count = cursor.fetchone()[0]
        print(f"Default Accounts: {acc_count}")

        cursor.execute("SELECT COUNT(*) FROM products")
        prod_count = cursor.fetchone()[0]
        print(f"Products: {prod_count}")
        print()

        # Close connection
        conn.close()

        print("="*60)
        print("✅ DATABASE VERIFICATION SUCCESSFUL!")
        print("="*60)
        print()
        print("Next steps:")
        print("  1. Import MRPeasy data: python data_migration/import_products.py")
        print("  2. Start backend server: uvicorn main:app --reload")
        print()

        return True

    except pyodbc.Error as e:
        print("❌ Connection failed!")
        print()
        print("Error details:")
        print(f"  {str(e)}")
        print()

        # Common fixes
        print("Troubleshooting:")
        print("  1. Check if SQL Server Express is running:")
        print("     - Open 'Services' (services.msc)")
        print("     - Look for 'SQL Server (SQLEXPRESS)'")
        print("     - Status should be 'Running'")
        print()
        print("  2. Check your SQL Server instance name:")
        print("     - Open SSMS and see what you connect to")
        print("     - Update conn_str if different from 'localhost\\SQLEXPRESS'")
        print()
        print("  3. Install ODBC Driver 17 if missing:")
        print("     - Download from: https://aka.ms/downloadmsodbcsql")
        print()
        print("  4. Verify database exists:")
        print("     - Open SSMS")
        print("     - Check if BLB3D_ERP database is listed")
        print()

        return False

    except Exception as e:
        print("❌ Unexpected error!")
        print(f"  {str(e)}")
        print()
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
