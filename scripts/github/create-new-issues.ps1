# Create New GitHub Issues for Completed Work
# Requires: GitHub CLI (gh) installed and authenticated
# Run: .\scripts\create-new-issues.ps1

Write-Host "Creating new GitHub issues for completed work..." -ForegroundColor Cyan
Write-Host ""

# Check if gh CLI is installed
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ GitHub CLI (gh) not found!" -ForegroundColor Red
    Write-Host "Install from: https://cli.github.com/" -ForegroundColor Yellow
    exit 1
}

# Verify authentication
Write-Host "Checking GitHub authentication..." -ForegroundColor Yellow
$authCheck = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Not authenticated with GitHub CLI!" -ForegroundColor Red
    Write-Host "Run: gh auth login" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Authenticated" -ForegroundColor Green
Write-Host ""

# Check for existing issues to avoid duplicates
Write-Host "Checking for existing issues to avoid duplicates..." -ForegroundColor Yellow
$existingIssues = gh issue list --state all --json number, title --limit 100 | ConvertFrom-Json

# Known existing issues (don't create these)
$knownExisting = @{
    31 = "[Infra] Set up Alembic database migrations"
    33 = "[Security] Add rate limiting to authentication endpoints"
    34 = "[Security] Remove personal address from default settings"
}

foreach ($known in $knownExisting.GetEnumerator()) {
    $found = $existingIssues | Where-Object { $_.number -eq $known.Key }
    if ($found) {
        Write-Host "  ⚠️  Issue #$($known.Key) already exists: $($known.Value)" -ForegroundColor Yellow
        Write-Host "     Skipping creation - update existing issue instead" -ForegroundColor Gray
    }
}
Write-Host ""

# Check if issues already exist by title
$checkDuplicate = {
    param($title)
    $normalizedTitle = ($title -replace '\[.*?\]', '').Trim().ToLower()
    foreach ($issue in $existingIssues) {
        $issueTitleNormalized = ($issue.title -replace '\[.*?\]', '').Trim().ToLower()
        if ($issueTitleNormalized -eq $normalizedTitle -or 
            $issueTitleNormalized.Contains($normalizedTitle)) {
            return $issue
        }
    }
    return $null
}

# Issue 6: Structured Logging
$issue6Title = "[Chore] Replace print() statements with structured logging in backend"
$existing6 = & $checkDuplicate $issue6Title
if ($existing6) {
    Write-Host "⚠️  Issue already exists: #$($existing6.number) - $($existing6.title)" -ForegroundColor Yellow
    Write-Host "   Skipping creation. Update existing issue instead." -ForegroundColor Gray
    Write-Host ""
}
else {
    Write-Host "Creating Issue #6: Structured Logging..." -ForegroundColor Yellow
    $issue6 = @"
## Summary
Replace all `print()` statements in backend code with proper structured logging using the existing `logging_config.py` system.

## Problem
Backend code uses `print()` statements for logging, which:
- Cannot be filtered by log level
- Cannot be aggregated in production systems
- Don't include timestamps, log levels, or structured context
- Make debugging production issues difficult

## Solution
Use the existing `get_logger()` function from `app.logging_config`:
``````python
from app.logging_config import get_logger

logger = get_logger(__name__)

# Replace print() with appropriate log level
logger.info("Customer created successfully")
logger.error("Failed to process order")
``````

## Files Updated
- `backend/app/api/v1/endpoints/auth.py` - Login, registration, password reset
- `backend/app/api/v1/endpoints/admin/customers.py` - Customer CRUD operations
- `backend/app/api/v1/endpoints/admin/bom.py` - BOM operations
- `backend/app/api/v1/endpoints/sales_orders.py` - Production order creation
- `backend/app/services/quote_conversion_service.py` - Quote conversion
- `backend/app/core/pricing_config.py` - Pricing calculations

## Acceptance Criteria
- [x] All `print()` statements replaced with `logger.info()`, `logger.error()`, etc.
- [x] Appropriate log levels used (info, error, warning, debug)
- [x] Logging includes relevant context (IDs, operation names)
- [x] No `print()` statements remain in production code paths

## Implementation Notes
Completed December 2025:
- Replaced ~15+ print() statements across 6 files
- Used structured logging with proper log levels
- Maintained existing logging configuration system
"@

    $tempFile6 = "issue-6-body.md"
    Set-Content -Path $tempFile6 -Value $issue6
    $result6 = gh issue create --title "[Chore] Replace print() statements with structured logging in backend" --body-file $tempFile6 --label "backend" --label "code-quality" --label "core-release" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Created" -ForegroundColor Green
    }
    else {
        Write-Host "  ❌ Failed: $result6" -ForegroundColor Red
    }
    Remove-Item $tempFile6 -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
}

# Issue 7: Commented Code Cleanup
$issue7Title = "[Chore] Remove commented-out code blocks"
$existing7 = & $checkDuplicate $issue7Title
if ($existing7) {
    Write-Host "⚠️  Issue already exists: #$($existing7.number) - $($existing7.title)" -ForegroundColor Yellow
    Write-Host "   Skipping creation. Update existing issue instead." -ForegroundColor Gray
    Write-Host ""
}
else {
    Write-Host "Creating Issue #7: Commented Code Cleanup..." -ForegroundColor Yellow
    $issue7 = @"
## Summary
Remove large blocks of commented-out code that are no longer needed, especially in `backend/app/api/v1/endpoints/admin/fulfillment.py`.

## Problem
Codebase contains large sections of commented-out code that:
- Clutters the codebase
- Makes it harder to understand active code
- May contain outdated logic that confuses contributors
- Increases maintenance burden

## Files Cleaned
- `backend/app/api/v1/endpoints/admin/fulfillment.py` - Removed large commented-out blocks

## Acceptance Criteria
- [x] Commented-out code blocks removed
- [x] Active code remains unchanged
- [x] No functional changes

## Implementation Notes
Completed December 2025:
- Removed commented-out code in fulfillment.py
- Preserved all active functionality
"@

    $tempFile7 = "issue-7-body.md"
    Set-Content -Path $tempFile7 -Value $issue7
    $result7 = gh issue create --title "[Chore] Remove commented-out code blocks" --body-file $tempFile7 --label "code-quality" --label "good first issue" --label "core-release" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Created" -ForegroundColor Green
    }
    else {
        Write-Host "  ❌ Failed: $result7" -ForegroundColor Red
    }
    Remove-Item $tempFile7 -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
}

# Issue 8: Frontend Error Handling
$issue8Title = "[Chore] Convert console.error to proper error handling in frontend"
$existing8 = & $checkDuplicate $issue8Title
if ($existing8) {
    Write-Host "⚠️  Issue already exists: #$($existing8.number) - $($existing8.title)" -ForegroundColor Yellow
    Write-Host "   Skipping creation. Update existing issue instead." -ForegroundColor Gray
    Write-Host ""
}
else {
    Write-Host "Creating Issue #8: Frontend Error Handling..." -ForegroundColor Yellow
    $issue8 = @"
## Summary
Replace all `console.error()` statements in frontend React components with proper user-facing error handling using error state or alerts.

## Problem
Frontend code uses `console.error()` for error handling, which:
- Errors are invisible to users
- No user feedback when operations fail
- Makes debugging user-reported issues difficult
- Poor user experience

## Solution
Replace with appropriate error handling:
1. **Components with error state**: Use `setError()` to display errors in UI
2. **Critical operations**: Show `alert()` for immediate user feedback
3. **Non-critical failures**: Add comments explaining why they're handled silently

## Files Updated (~25 files)

### Admin Pages
- `frontend/src/pages/admin/AdminBOM.jsx` - BOM operations, cost rollup, routing
- `frontend/src/pages/admin/AdminPurchasing.jsx` - Products, low stock, PO details
- `frontend/src/pages/admin/AdminShipping.jsx` - Production status, order updates
- `frontend/src/pages/admin/AdminManufacturing.jsx` - Products, resources
- `frontend/src/pages/admin/AdminProduction.jsx` - Products, status updates
- `frontend/src/pages/admin/AdminOrders.jsx` - Order status updates
- `frontend/src/pages/admin/AdminCustomers.jsx` - Orders, session storage
- `frontend/src/pages/admin/AdminItems.jsx` - Categories
- `frontend/src/pages/admin/OrderDetail.jsx` - Order fetch, BOM explosion
- `frontend/src/pages/admin/AdminAnalytics.jsx` - Analytics fetch
- `frontend/src/pages/admin/AdminLicense.jsx` - License info fetch
- `frontend/src/pages/admin/AdminInventoryTransactions.jsx` - Products, locations
- `frontend/src/pages/admin/AdminLogin.jsx` - Setup check

### Components
- `frontend/src/components/BOMEditor.jsx` - BOM fetch, components, materials
- `frontend/src/components/RoutingEditor.jsx` - Routing fetch, work centers, templates
- `frontend/src/components/MaterialForm.jsx` - Material types, colors
- `frontend/src/components/ItemWizard.jsx` - Categories, components, work centers, templates, materials
- `frontend/src/components/SalesOrderWizard.jsx` - Customers, products, categories, components, work centers, templates, materials
- `frontend/src/components/ProductionScheduler.jsx` - Resource fetch warnings
- `frontend/src/components/ProductionSchedulingModal.jsx` - Work centers, resources
- `frontend/src/components/ExportImport.jsx` - Export failures
- `frontend/src/components/ItemForm.jsx` - Categories (non-critical)

### Pages
- `frontend/src/pages/Onboarding.jsx` - Removed debug console.log statements
- `frontend/src/pages/admin/AdminMaterialImport.jsx` - Removed debug console.log statements

### Hooks
- `frontend/src/hooks/useFeatureFlags.js` - Tier fetch failures

## Error Handling Strategy
1. **User-facing errors**: Show alerts or set error state for critical operations
2. **Non-critical failures**: Add comments explaining why they're handled silently (e.g., dropdown data fetch failures)
3. **Debug logs**: Removed unnecessary console.log statements from import operations

## Acceptance Criteria
- [x] All `console.error()` replaced with proper error handling
- [x] User-facing errors show appropriate messages (alerts or error state)
- [x] Non-critical failures documented with comments
- [x] Debug `console.log()` statements removed
- [x] No `console.error()` or `console.warn()` remain in production code

## Implementation Notes
Completed December 2025:
- Replaced ~50+ console.error/warn/log statements
- Added user-facing error messages for critical operations
- Documented non-critical failures with comments
- Improved user experience with proper error feedback
"@

    $tempFile8 = "issue-8-body.md"
    Set-Content -Path $tempFile8 -Value $issue8
    $result8 = gh issue create --title "[Chore] Convert console.error to proper error handling in frontend" --body-file $tempFile8 --label "frontend" --label "code-quality" --label "core-release" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Created" -ForegroundColor Green
    }
    else {
        Write-Host "  ❌ Failed: $result8" -ForegroundColor Red
    }
    Remove-Item $tempFile8 -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "✅ Issue creation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Note: Issues that already exist were skipped to avoid duplicates." -ForegroundColor Cyan
Write-Host "View issues: https://github.com/Blb3D/filaops/issues" -ForegroundColor Cyan

