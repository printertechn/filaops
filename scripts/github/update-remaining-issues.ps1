# Update Remaining Completed Issues with Completion Status
# Updates issues #35, #36, #37 with completion details
# Requires: GitHub CLI (gh) installed and authenticated
# Run: .\scripts\update-remaining-issues.ps1

Write-Host "Updating remaining GitHub issues with completion status..." -ForegroundColor Cyan
Write-Host ""

# Check if gh CLI is installed
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ GitHub CLI (gh) not found!" -ForegroundColor Red
    Write-Host "Install from: https://cli.github.com/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Alternatively, update issues manually:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://github.com/Blb3D/filaops/issues" -ForegroundColor Cyan
    Write-Host "2. Update issues #35, #36, and #37 with completion comments" -ForegroundColor Cyan
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

# Update Issue #35: Structured Logging
Write-Host "Updating Issue #35: Structured Logging..." -ForegroundColor Yellow
$comment35 = @"
## ✅ Completed - December 2025

This issue has been completed! Here's what was implemented:

### Implementation Details
- ✅ Replaced all `print()` statements with structured logging using `get_logger()`
- ✅ Used appropriate log levels (info, error, warning, debug)
- ✅ Logging includes relevant context (IDs, operation names)
- ✅ No `print()` statements remain in production code paths

### Files Modified
- `backend/app/api/v1/endpoints/auth.py` - Login, registration, password reset logging
- `backend/app/api/v1/endpoints/admin/customers.py` - Customer CRUD operations logging
- `backend/app/api/v1/endpoints/admin/bom.py` - BOM operations logging
- `backend/app/api/v1/endpoints/sales_orders.py` - Production order creation logging
- `backend/app/services/quote_conversion_service.py` - Quote conversion logging
- `backend/app/core/pricing_config.py` - Pricing calculations logging

### Implementation Notes
- Replaced ~15+ print() statements across 6 files
- Used structured logging with proper log levels
- Maintained existing logging configuration system from `app.logging_config`
- All logging now includes timestamps, log levels, and structured context

This improves debuggability and makes logs suitable for production aggregation systems.
"@

$tempFile35 = "issue-35-comment.md"
Set-Content -Path $tempFile35 -Value $comment35
gh issue comment 35 --body-file $tempFile35
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Added completion comment" -ForegroundColor Green
} else {
    Write-Host "  ❌ Failed to add comment" -ForegroundColor Red
}
Remove-Item $tempFile35 -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 500

# Update Issue #36: Commented Code Cleanup
Write-Host "Updating Issue #36: Commented Code Cleanup..." -ForegroundColor Yellow
$comment36 = @"
## ✅ Completed - December 2025

This issue has been completed! Here's what was implemented:

### Implementation Details
- ✅ Removed large commented-out code blocks
- ✅ Active code remains unchanged
- ✅ No functional changes - code cleanup only

### Files Modified
- `backend/app/api/v1/endpoints/admin/fulfillment.py` - Removed large commented-out blocks

### Implementation Notes
- Removed commented-out code in fulfillment.py
- Preserved all active functionality
- Codebase is now cleaner and easier to maintain

This reduces clutter and makes the codebase more maintainable for contributors.
"@

$tempFile36 = "issue-36-comment.md"
Set-Content -Path $tempFile36 -Value $comment36
gh issue comment 36 --body-file $tempFile36
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Added completion comment" -ForegroundColor Green
} else {
    Write-Host "  ❌ Failed to add comment" -ForegroundColor Red
}
Remove-Item $tempFile36 -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 500

# Update Issue #37: Frontend Error Handling
Write-Host "Updating Issue #37: Frontend Error Handling..." -ForegroundColor Yellow
$comment37 = @"
## ✅ Completed - December 2025

This issue has been completed! Here's what was implemented:

### Implementation Details
- ✅ Replaced all `console.error()` with proper user-facing error handling
- ✅ User-facing errors show appropriate messages (alerts or error state)
- ✅ Non-critical failures documented with comments
- ✅ Debug `console.log()` statements removed
- ✅ No `console.error()` or `console.warn()` remain in production code

### Files Modified (~25 files)

#### Admin Pages (13 files)
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

#### Components (9 files)
- `frontend/src/components/BOMEditor.jsx` - BOM fetch, components, materials
- `frontend/src/components/RoutingEditor.jsx` - Routing fetch, work centers, templates
- `frontend/src/components/MaterialForm.jsx` - Material types, colors
- `frontend/src/components/ItemWizard.jsx` - Categories, components, work centers, templates, materials
- `frontend/src/components/SalesOrderWizard.jsx` - Customers, products, categories, components, work centers, templates, materials
- `frontend/src/components/ProductionScheduler.jsx` - Resource fetch warnings
- `frontend/src/components/ProductionSchedulingModal.jsx` - Work centers, resources
- `frontend/src/components/ExportImport.jsx` - Export failures
- `frontend/src/components/ItemForm.jsx` - Categories (non-critical)

#### Pages (2 files)
- `frontend/src/pages/Onboarding.jsx` - Removed debug console.log statements
- `frontend/src/pages/admin/AdminMaterialImport.jsx` - Removed debug console.log statements

#### Hooks (1 file)
- `frontend/src/hooks/useFeatureFlags.js` - Tier fetch failures

### Error Handling Strategy
1. **User-facing errors**: Show alerts or set error state for critical operations
2. **Non-critical failures**: Add comments explaining why they're handled silently (e.g., dropdown data fetch failures)
3. **Debug logs**: Removed unnecessary console.log statements from import operations

### Implementation Notes
- Replaced ~50+ console.error/warn/log statements
- Added user-facing error messages for critical operations
- Documented non-critical failures with comments
- Improved user experience with proper error feedback

This significantly improves user experience by making errors visible and actionable, rather than silently failing.
"@

$tempFile37 = "issue-37-comment.md"
Set-Content -Path $tempFile37 -Value $comment37
gh issue comment 37 --body-file $tempFile37
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Added completion comment" -ForegroundColor Green
} else {
    Write-Host "  ❌ Failed to add comment" -ForegroundColor Red
}
Remove-Item $tempFile37 -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "✅ Issue updates complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Updated issues:" -ForegroundColor Cyan
Write-Host "  - Issue #35: Structured Logging" -ForegroundColor White
Write-Host "  - Issue #36: Commented Code Cleanup" -ForegroundColor White
Write-Host "  - Issue #37: Frontend Error Handling" -ForegroundColor White
Write-Host ""
Write-Host "View issues: https://github.com/Blb3D/filaops/issues" -ForegroundColor Cyan

