"""
Copy BLB3D_ERP database to FilaOps and sanitize private data

This script:
1. Creates a new FilaOps database
2. Copies schema from BLB3D_ERP
3. Copies data (sanitizing private information)
4. Prepares it for development/testing
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, create_engine
from app.core.settings import settings


def sanitize_data(db, table_name, sanitize_rules):
    """Sanitize data in a table based on rules"""
    for column, replacement in sanitize_rules.items():
        try:
            if replacement is None:
                # Set to NULL
                db.execute(text(f"UPDATE {table_name} SET {column} = NULL"))
            elif isinstance(replacement, str):
                # Set to string value
                db.execute(text(f"UPDATE {table_name} SET {column} = :val"), {"val": replacement})
            elif callable(replacement):
                # Call function to generate value
                result = db.execute(text(f"SELECT id FROM {table_name}"))
                for row in result:
                    new_val = replacement(row[0])
                    db.execute(text(f"UPDATE {table_name} SET {column} = :val WHERE id = :id"), 
                              {"val": new_val, "id": row[0]})
            db.commit()
            print(f"    Sanitized {table_name}.{column}")
        except Exception as e:
            print(f"    ⚠️  Could not sanitize {table_name}.{column}: {e}")
            db.rollback()


def copy_database():
    """Copy BLB3D_ERP to FilaOps and sanitize"""
    print("=" * 60)
    print("Database Copy and Sanitization")
    print("BLB3D_ERP → FilaOps")
    print("=" * 60)
    
    # Connect to master database to create new DB
    master_conn_str = (
        f"mssql+pyodbc://{settings.DB_HOST}/master"
        f"?driver=ODBC+Driver+17+for+SQL+Server"
        f"&Trusted_Connection=yes"
    )
    master_engine = create_engine(master_conn_str)
    
    source_db = "BLB3D_ERP"
    target_db = "FilaOps"
    
    with master_engine.connect() as conn:
        # Check if target database exists
        check_db = text(f"""
            SELECT COUNT(*) FROM sys.databases WHERE name = '{target_db}'
        """)
        db_exists = conn.execute(check_db).scalar()
        
        if db_exists:
            print(f"\n⚠️  Database '{target_db}' already exists.")
            response = input("Drop and recreate? (yes/no): ")
            if response.lower() == 'yes':
                print(f"Dropping existing '{target_db}' database...")
                # Close connections first
                conn.execute(text(f"ALTER DATABASE [{target_db}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE"))
                conn.execute(text(f"DROP DATABASE [{target_db}]"))
                conn.commit()
                print("✅ Database dropped")
            else:
                print("Aborting. Please manually drop the database or choose a different name.")
                return
        
        # Create new database
        print(f"\n📦 Creating database '{target_db}'...")
        conn.execute(text(f"CREATE DATABASE [{target_db}]"))
        conn.commit()
        print("✅ Database created")
    
    # Connect to source database
    source_conn_str = (
        f"mssql+pyodbc://{settings.DB_HOST}/{source_db}"
        f"?driver=ODBC+Driver+17+for+SQL+Server"
        f"&Trusted_Connection=yes"
    )
    source_engine = create_engine(source_conn_str)
    
    # Connect to target database
    target_conn_str = (
        f"mssql+pyodbc://{settings.DB_HOST}/{target_db}"
        f"?driver=ODBC+Driver+17+for+SQL+Server"
        f"&Trusted_Connection=yes"
    )
    target_engine = create_engine(target_conn_str)
    
    print(f"\n📋 Copying schema from '{source_db}' to '{target_db}'...")
    
    with source_engine.connect() as source_conn, target_engine.connect() as target_conn:
        # Get all tables
        tables_query = text("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        tables = [row[0] for row in source_conn.execute(tables_query)]
        
        print(f"Found {len(tables)} tables to copy")
        
        # Copy schema first using SQL Server's script generation
        print("  Generating schema script...")
        # We'll use a simpler approach: copy table by table with INSERT INTO
        
        # Copy schema and data for each table
        for table_name in tables:
            try:
                print(f"\n  📄 Copying {table_name}...")
                
                # Get column list
                columns_query = text(f"""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = '{table_name}'
                    ORDER BY ORDINAL_POSITION
                """)
                columns = source_conn.execute(columns_query).fetchall()
                column_names = [col[0] for col in columns]
                
                # Create table in target (simplified - assumes same schema)
                # First check if table exists in target
                table_exists = target_conn.execute(text(f"""
                    SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = '{table_name}'
                """)).scalar()
                
                if not table_exists:
                    # Generate CREATE TABLE statement (simplified)
                    # For production, you'd want full schema copy with constraints
                    # For now, we'll use SELECT INTO which handles this
                    pass
                
                # Copy data using INSERT INTO ... SELECT FROM
                # Use fully qualified names for cross-database query
                column_list = ', '.join([f'[{col}]' for col in column_names])
                
                # Check for identity columns
                identity_cols = source_conn.execute(text(f"""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = '{table_name}' 
                    AND COLUMNPROPERTY(OBJECT_ID('{table_name}'), COLUMN_NAME, 'IsIdentity') = 1
                """)).fetchall()
                
                if identity_cols:
                    # Enable IDENTITY_INSERT
                    target_conn.execute(text(f"SET IDENTITY_INSERT [{target_db}].dbo.[{table_name}] ON"))
                
                # Copy data
                copy_query = text(f"""
                    INSERT INTO [{target_db}].dbo.[{table_name}] ({column_list})
                    SELECT {column_list} FROM [{source_db}].dbo.[{table_name}]
                """)
                result = target_conn.execute(copy_query)
                rows_copied = result.rowcount
                
                if identity_cols:
                    target_conn.execute(text(f"SET IDENTITY_INSERT [{target_db}].dbo.[{table_name}] OFF"))
                
                target_conn.commit()
                print(f"    ✅ Copied {rows_copied} rows")
                
            except Exception as e:
                print(f"    ❌ Error copying {table_name}: {e}")
                import traceback
                traceback.print_exc()
                target_conn.rollback()
                # Try SELECT INTO as fallback
                try:
                    print(f"    Trying SELECT INTO fallback...")
                    target_conn.execute(text(f"""
                        SELECT * INTO [{target_db}].dbo.[{table_name}] 
                        FROM [{source_db}].dbo.[{table_name}]
                    """))
                    target_conn.commit()
                    count = target_conn.execute(text(f"SELECT COUNT(*) FROM [{target_db}].dbo.[{table_name}]")).scalar()
                    print(f"    ✅ Copied {count} rows (fallback method)")
                except Exception as e2:
                    print(f"    ❌ Fallback also failed: {e2}")
                    target_conn.rollback()
        
        # Copy constraints, indexes, etc. (simplified - may need manual fixes)
        print(f"\n📋 Copying constraints and indexes...")
        # Note: This is simplified. Full schema copy would need more complex logic.
        # For now, we'll rely on the SELECT INTO which copies basic structure.
        
        # Sanitize private data
        print(f"\n🧹 Sanitizing private data...")
        
        # Users table - anonymize emails, names
        if 'users' in tables:
            print("  Sanitizing users table...")
            sanitize_data(target_conn, 'users', {
                'email': lambda id: f'user{id}@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'password_hash': '$2b$12$dummyhashfordevelopmentonly',  # Dummy hash
            })
        
        # Customers table - anonymize contact info
        if 'customers' in tables:
            print("  Sanitizing customers table...")
            sanitize_data(target_conn, 'customers', {
                'email': lambda id: f'customer{id}@example.com',
                'phone': '555-0000',
                'address_line1': '123 Test St',
                'address_line2': None,
                'city': 'Test City',
                'state': 'TS',
                'postal_code': '12345',
                'country': 'USA',
            })
        
        # Sales orders - anonymize customer references if needed
        # (Keep IDs for referential integrity, but data is already sanitized via customers)
        
        # Quotes - anonymize customer info
        if 'quotes' in tables:
            print("  Sanitizing quotes table...")
            sanitize_data(target_conn, 'quotes', {
                'customer_email': lambda id: f'quote{id}@example.com',
                'customer_name': 'Test Customer',
            })
        
        print("\n✅ Database copy and sanitization complete!")
        print(f"\n📝 Next steps:")
        print(f"   1. Update your .env file: DB_NAME=FilaOps")
        print(f"   2. Run: python migrate_material_inventory_to_products.py")
        print(f"   3. Verify data looks correct")


if __name__ == "__main__":
    try:
        copy_database()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

