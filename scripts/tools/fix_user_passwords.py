"""
Fix malformed password hashes in the users table

This script resets passwords for users in the FilaOps database.
Useful after database copy/sanitization when password hashes may be corrupted.
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password

def fix_user_passwords():
    """Reset passwords for all users to a default password"""
    db = SessionLocal()
    
    try:
        # Default password for all users (change this!)
        DEFAULT_PASSWORD = "Admin123!"  # Must meet password requirements
        
        print("=" * 60)
        print("Fixing User Passwords")
        print("=" * 60)
        print(f"Database: {db.bind.url.database}")
        print()
        
        # Get all users
        users = db.query(User).all()
        print(f"Found {len(users)} users")
        print()
        
        if len(users) == 0:
            print("No users found. Exiting.")
            return
        
        # Show current state
        print("Current users:")
        for user in users:
            hash_preview = user.password_hash[:30] if user.password_hash else "NULL"
            print(f"  - {user.email} (ID: {user.id}, Status: {user.status}, Type: {user.account_type})")
            print(f"    Hash preview: {hash_preview}... (length: {len(user.password_hash) if user.password_hash else 0})")
        print()
        
        # Ask for confirmation
        response = input(f"Reset all passwords to '{DEFAULT_PASSWORD}'? (yes/no): ")
        if response.lower() != "yes":
            print("Cancelled.")
            return
        
        # Reset passwords
        print()
        print("Resetting passwords...")
        for user in users:
            user.password_hash = hash_password(DEFAULT_PASSWORD)
            print(f"  - Reset password for {user.email}")
        
        db.commit()
        print()
        print("=" * 60)
        print("SUCCESS: All passwords have been reset!")
        print("=" * 60)
        print()
        print(f"Default password for all users: {DEFAULT_PASSWORD}")
        print()
        print("Users and their account types:")
        for user in users:
            print(f"  - {user.email} ({user.account_type})")
        print()
        
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    fix_user_passwords()

