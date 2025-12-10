# Create GitHub Release
# Requires: GitHub CLI (gh) installed
# Run: .\scripts\create-release.ps1

param(
    [string]$Version = "v1.0.0-docker",
    [string]$Title = "🐳 Docker Deployment - One-Command Setup for Print Farms",
    [switch]$Draft = $false
)

$releaseNotes = @"
# 🐳 Docker Deployment - One-Command Setup

## 🚀 GET STARTED IN 5 MINUTES - NO CODING REQUIRED

Print farm owners can now deploy FilaOps with a single command:
``````bash
docker-compose up -d
``````

Everything is pre-configured:
- ✅ SQL Server database (auto-initialized)
- ✅ Backend API (FastAPI)
- ✅ Frontend UI (React)
- ✅ All dependencies included

Perfect for non-technical users who want professional ERP functionality without the complexity.

## 📦 What's New

### Docker Deployment
- Complete docker-compose.yml setup
- Automatic database initialization
- Production-ready nginx configuration
- Zero-configuration startup

### Material & Orders Import
- CSV import for filament inventory with template download
- Orders import from Squarespace, Shopify, WooCommerce, Etsy, TikTok Shop
- Automatic column mapping for all major marketplaces
- Comprehensive import guides

### Bulk Operations
- Bulk item updates (categories, types, status)
- Multi-select interface
- Batch processing

### Enhanced Onboarding
- Guided setup wizard
- Seed data option for quick start
- Progress tracking

## 🔧 Improvements

- Fixed inventory location handling (removed hardcoded values)
- Better CSV import error messages
- Enhanced marketplace column mapping
- Improved material display (Filament vs Supply)
- Optional customer email/SKU in orders import
- Fixed bulk update category reversion bug

## 📚 Documentation

- Updated README with Docker quick start
- Comprehensive marketplace import guides
- Installation guide for non-technical users

## 🎯 Stats

- 26 stars in 3 days
- 183 clones
- 1,011 views

## 🚀 Get Started

``````bash
git clone https://github.com/Blb3D/filaops.git
cd filaops
docker-compose up -d
``````

Open http://localhost:5173 and start managing your print farm!

---

**Full Changelog:** See commit history for detailed changes.
"@

# Save release notes to temp file
$notesFile = "release-notes-temp.md"
Set-Content -Path $notesFile -Value $releaseNotes

Write-Host "Creating GitHub release..." -ForegroundColor Cyan
Write-Host "Version: $Version" -ForegroundColor Yellow
Write-Host "Title: $Title" -ForegroundColor Yellow
if ($Draft) {
    Write-Host "Mode: DRAFT" -ForegroundColor Yellow
}
Write-Host ""

# Check if gh CLI is installed
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ GitHub CLI (gh) not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install from: https://cli.github.com/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Release notes saved to: $notesFile" -ForegroundColor Cyan
    Write-Host "Create release manually at: https://github.com/Blb3D/filaops/releases/new" -ForegroundColor Cyan
    exit 1
}

# Check authentication
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ GitHub CLI not authenticated!" -ForegroundColor Red
    Write-Host "Run: gh auth login" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Release notes saved to: $notesFile" -ForegroundColor Cyan
    exit 1
}

# Build gh release command
$releaseCmd = "gh release create $Version --title `"$Title`" --notes-file $notesFile"
if ($Draft) {
    $releaseCmd += " --draft"
}

Write-Host "Executing: $releaseCmd" -ForegroundColor Gray
Write-Host ""

Invoke-Expression $releaseCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ GitHub release created successfully!" -ForegroundColor Green
    Remove-Item $notesFile -ErrorAction SilentlyContinue
    Write-Host ""
    Write-Host "View release: https://github.com/Blb3D/filaops/releases/tag/$Version" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "❌ Failed to create release." -ForegroundColor Red
    Write-Host "Release notes saved to: $notesFile" -ForegroundColor Cyan
    Write-Host "Create manually at: https://github.com/Blb3D/filaops/releases/new" -ForegroundColor Cyan
}

