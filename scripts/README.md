# FilaOps Scripts

This directory contains utility scripts organized by purpose.

## 📁 Directory Structure

### `github/`
Scripts for GitHub issue and release management:
- `create-new-issues.ps1` - Create GitHub issues from templates
- `update-completed-issues.ps1` - Update issues with completion comments
- `check-duplicate-issues.ps1` - Check for duplicate issues
- `create-core-issues.ps1` - Create core release issues
- `create-release.ps1` - Create GitHub releases
- `add-github-topics.ps1` - Add topics to repository

**Usage:** Requires GitHub CLI (`gh`) to be installed and authenticated.

### `database/`
SQL scripts for database setup and migration:
- `init-db.sql` - Initial database setup
- `setup_database.sql` - Database initialization
- `create_*.sql` - Table creation scripts
- `*_sync_*.sql` - Data synchronization scripts
- Various migration and fix scripts

**Usage:** Run these scripts against your SQL Server database.

### `tools/`
Utility Python scripts and helpers:
- `material_import.py` - Material data import utilities
- `fresh_database_setup.py` - Fresh database setup script
- Various migration and analysis tools

**Usage:** Most can be run directly with Python:
```bash
python scripts/tools/script_name.py
```

## 🔧 PowerShell Scripts

### Prerequisites
- PowerShell 7+ (recommended)
- GitHub CLI (`gh`) for GitHub scripts
- Python 3.11+ for Python scripts

### Common Tasks

**Create GitHub Issues:**
```powershell
.\scripts\github\create-new-issues.ps1
```

**Update Completed Issues:**
```powershell
.\scripts\github\update-completed-issues.ps1
```

**Check for Duplicates:**
```powershell
.\scripts\github\check-duplicate-issues.ps1
```

## 📝 Notes

- All scripts include error handling and user-friendly output
- GitHub scripts require authentication: `gh auth login`
- Database scripts should be run with appropriate permissions
- Always review scripts before running in production

---

For more information, see the main [README.md](../README.md) or [CONTRIBUTING.md](../CONTRIBUTING.md).
