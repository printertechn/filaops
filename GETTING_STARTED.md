# Getting Started with BLB3D ERP

## Quick Start Guide

### Step 1: Initialize Git (Manual)

**Note:** OneDrive can sometimes interfere with `git init`. If you had issues, run this manually:

```bash
cd "C:\Users\brand\OneDrive\Documents\blb3d-erp"
git init
git add .
git commit -m "Initial commit"
```

Or, move the project outside OneDrive for better Git performance:
```bash
# Copy to local drive
xcopy /E /I "C:\Users\brand\OneDrive\Documents\blb3d-erp" "C:\Dev\blb3d-erp"
cd C:\Dev\blb3d-erp
git init
```

### Step 2: Set Up SQL Server Database

1. Open **SQL Server Management Studio (SSMS)**
2. Connect to your SQL Server Express instance
3. Run the schema creation script:
   ```sql
   -- See scripts/setup_database.sql
   ```

### Step 3: Set Up Python Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Step 4: Configure Environment

Create `backend/.env`:
```env
DATABASE_URL=mssql+pyodbc://localhost/BLB3D_ERP?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes
SECRET_KEY=your-secret-key-here
WOOCOMMERCE_URL=https://yourstore.com
WOOCOMMERCE_KEY=ck_xxxxx
WOOCOMMERCE_SECRET=cs_xxxxx
```

### Step 5: Run Database Migrations

```bash
cd backend
python -m alembic upgrade head
```

### Step 6: Import MRPeasy Data

```bash
cd data_migration
python import_all.py
```

### Step 7: Start Backend Server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000
API docs at: http://localhost:8000/docs

### Step 8: Set Up React Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at: http://localhost:5173

## Next Steps

1. Review the imported data
2. Set up WooCommerce (see docs/WOOCOMMERCE_SETUP.md)
3. Configure print farm integration
4. Start processing orders!

## Need Help?

Check the docs folder for detailed guides on each module.
