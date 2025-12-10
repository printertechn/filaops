# Create GitHub Issues for Core Release Plan Items
# Requires: GitHub CLI (gh) installed and authenticated
# Run: .\scripts\create-core-issues.ps1

$issues = @(
    @{
        Title = "Audit and remove remaining hardcoded location_id values"
        Body  = @"
## Description
Complete audit of all backend endpoints to find and remove any remaining hardcoded `location_id=1` values. Some endpoints have been fixed, but a comprehensive audit is needed.

## Completed
- ✅ Fixed in inventory endpoints
- ✅ Fixed in fulfillment endpoints

## Remaining Work
- [ ] Audit all endpoints for hardcoded location_id
- [ ] Add default location configuration
- [ ] Update any remaining hardcoded values
- [ ] Add tests to prevent regression

## Priority
High - Affects multi-location functionality

## Labels
bug, technical-debt, core-release
"@
    },
    @{
        Title = "Implement tax calculation system"
        Body  = @"
## Description
Currently tax is hardcoded to 0. Need to implement a configurable tax system.

## Requirements
- [ ] Add tax configuration to settings
- [ ] Calculate tax on sales orders
- [ ] Display tax in order totals
- [ ] Support multiple tax rates (by location/product type)
- [ ] Tax exemption support

## Priority
High - Required for accurate order pricing

## Labels
enhancement, core-release, purchasing
"@
    },
    @{
        Title = "Email verification and password reset"
        Body  = @"
## Description
Email verification is currently disabled. Need to either implement it or document that it's disabled for open source.

## Options
1. Implement email verification flow
2. Document that it's disabled for open source (simpler)

## Requirements
- [ ] Decide on approach (implement vs document)
- [ ] If implementing: email service integration
- [ ] If implementing: email templates
- [ ] Password reset email functionality
- [ ] Update documentation

## Priority
Medium - Can document as disabled if needed

## Labels
enhancement, security, core-release
"@
    },
    @{
        Title = "Schedule conflict detection UI"
        Body  = @"
## Description
Add UI to detect and display scheduling conflicts when manually scheduling production orders.

## Requirements
- [ ] Visual indicators for conflicts in scheduler
- [ ] Conflict warnings when scheduling
- [ ] Show conflicting orders
- [ ] Suggest alternative time slots

## Priority
Medium - Improves scheduling UX

## Labels
enhancement, scheduling, core-release
"@
    },
    @{
        Title = "Reschedule existing production orders"
        Body  = @"
## Description
Allow users to reschedule existing production orders via drag-and-drop in the scheduler view.

## Requirements
- [ ] Drag scheduled orders to new time slots
- [ ] Drag scheduled orders to different machines
- [ ] Validate new schedule (no conflicts)
- [ ] Update production order times
- [ ] Notify if conflicts exist

## Priority
Medium - Important for schedule management

## Labels
enhancement, scheduling, core-release
"@
    },
    @{
        Title = "Purchase order creation workflow"
        Body  = @"
## Description
Complete purchase order creation workflow from low stock alerts to PO generation.

## Requirements
- [ ] Create purchase orders from low stock alerts
- [ ] Add line items to PO
- [ ] Select vendors
- [ ] Set expected delivery dates
- [ ] PO approval workflow (optional)
- [ ] PO status tracking

## Priority
High - Core purchasing functionality

## Labels
enhancement, purchasing, core-release
"@
    },
    @{
        Title = "Vendor management (CRUD)"
        Body  = @"
## Description
Complete vendor management system for creating, editing, and managing vendors.

## Requirements
- [ ] Create vendor
- [ ] Edit vendor details
- [ ] Delete vendor (with validation)
- [ ] Vendor contact information
- [ ] Vendor payment terms
- [ ] Vendor performance tracking (optional)

## Priority
High - Required for purchasing

## Labels
enhancement, purchasing, core-release
"@
    },
    @{
        Title = "Purchase order receiving"
        Body  = @"
## Description
Workflow for receiving goods from purchase orders and updating inventory.

## Requirements
- [ ] Receive PO line items
- [ ] Partial receiving support
- [ ] Update inventory on receipt
- [ ] Create inventory transactions
- [ ] Link receipts to PO
- [ ] Receiving discrepancies handling

## Priority
High - Core purchasing functionality

## Labels
enhancement, purchasing, core-release
"@
    },
    @{
        Title = "Multi-carrier shipping label printing"
        Body  = @"
## Description
Support for printing shipping labels from multiple carriers (USPS, FedEx, UPS, etc.).

## Requirements
- [ ] Integrate with shipping APIs (EasyPost, ShipStation, etc.)
- [ ] Label generation
- [ ] Label printing
- [ ] Carrier selection
- [ ] Rate comparison (optional)

## Priority
Medium - Shipping workflow enhancement

## Labels
enhancement, shipping, core-release
"@
    },
    @{
        Title = "Packing slip generation"
        Body  = @"
## Description
Generate and print packing slips for shipments.

## Requirements
- [ ] Packing slip template
- [ ] Generate PDF packing slips
- [ ] Print packing slips
- [ ] Include order details, items, quantities
- [ ] Customizable template (optional)

## Priority
Medium - Shipping workflow enhancement

## Labels
enhancement, shipping, core-release
"@
    },
    @{
        Title = "Shipping cost calculation"
        Body  = @"
## Description
Calculate shipping costs based on weight, dimensions, and carrier.

## Requirements
- [ ] Weight-based calculation
- [ ] Dimension-based calculation
- [ ] Carrier rate lookup
- [ ] Display shipping costs in orders
- [ ] Shipping cost tracking

## Priority
Medium - Shipping workflow enhancement

## Labels
enhancement, shipping, core-release
"@
    },
    @{
        Title = "Tracking number management"
        Body  = @"
## Description
System for managing and tracking shipping tracking numbers.

## Requirements
- [ ] Add tracking numbers to shipments
- [ ] Track shipment status
- [ ] Display tracking in orders
- [ ] Tracking number validation
- [ ] Auto-update from carrier (optional)

## Priority
Medium - Shipping workflow enhancement

## Labels
enhancement, shipping, core-release
"@
    },
    @{
        Title = "Inventory adjustments with reason codes"
        Body  = @"
## Description
Add reason codes to inventory adjustments for better audit trail.

## Requirements
- [ ] Reason code configuration
- [ ] Add reason to adjustments
- [ ] Reason code dropdown in UI
- [ ] Adjustment history with reasons
- [ ] Report on adjustments by reason

## Priority
Low - Nice-to-have for audit

## Labels
enhancement, inventory, core-release
"@
    },
    @{
        Title = "Cycle counting workflow"
        Body  = @"
## Description
Workflow for performing cycle counts and reconciling inventory.

## Requirements
- [ ] Create cycle count
- [ ] Count inventory items
- [ ] Compare counts to system
- [ ] Generate variance report
- [ ] Approve and post adjustments

## Priority
Low - Nice-to-have for inventory accuracy

## Labels
enhancement, inventory, core-release
"@
    },
    @{
        Title = "Security audit and fixes"
        Body  = @"
## Description
Comprehensive security audit of the application and fix any vulnerabilities.

## Requirements
- [ ] SQL injection prevention verified
- [ ] XSS prevention verified
- [ ] CSRF protection implemented
- [ ] Password requirements enforced
- [ ] JWT token security reviewed
- [ ] Rate limiting on API endpoints
- [ ] Dependency security audit
- [ ] Penetration testing (optional)

## Priority
High - Critical for release

## Labels
security, core-release, critical
"@
    },
    @{
        Title = "Code quality improvements"
        Body  = @"
## Description
Clean up codebase for production release.

## Requirements
- [ ] Remove debug code
- [ ] Remove commented-out code (or document why)
- [ ] Consistent code style (linting)
- [ ] Type checking (mypy/pyright)
- [ ] Fix type checker warnings
- [ ] Code review and cleanup

## Priority
Medium - Improves maintainability

## Labels
technical-debt, code-quality, core-release
"@
    },
    @{
        Title = "Complete E2E test coverage"
        Body  = @"
## Description
Expand E2E test coverage to include all critical workflows.

## Completed
- ✅ Order-to-ship workflow
- ✅ Scheduling tests

## Remaining
- [ ] Complete production workflow
- [ ] Inventory transaction tests
- [ ] BOM creation and editing
- [ ] CSV import/export tests
- [ ] Customer management tests
- [ ] Item management tests

## Priority
High - Ensures quality

## Labels
testing, core-release
"@
    },
    @{
        Title = "Backend unit tests"
        Body  = @"
## Description
Add unit tests for critical backend services and calculations.

## Requirements
- [ ] Backend service tests
- [ ] MRP calculation tests
- [ ] Inventory calculation tests
- [ ] BOM explosion tests
- [ ] Scheduling algorithm tests
- [ ] Material compatibility tests

## Priority
High - Ensures correctness

## Labels
testing, core-release
"@
    },
    @{
        Title = "Performance testing and optimization"
        Body  = @"
## Description
Test and optimize performance for production use.

## Requirements
- [ ] Large dataset handling (1000+ products)
- [ ] Concurrent user testing
- [ ] Database query optimization
- [ ] API response time benchmarks
- [ ] Identify and fix bottlenecks
- [ ] Load testing

## Priority
Medium - Important for scalability

## Labels
performance, core-release
"@
    }
)

Write-Host "Creating GitHub issues for Core Release Plan..." -ForegroundColor Cyan
Write-Host ""

# Check if gh CLI is installed
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "GitHub CLI not found. Creating issues without labels..." -ForegroundColor Yellow
    $useLabels = $false
}
else {
    # Try to create label if it doesn't exist
    Write-Host "Creating 'core-release' label if needed..." -ForegroundColor Yellow
    gh label create "core-release" --color "0E8A16" --description "Core release planning items" 2>&1 | Out-Null
    $useLabels = $true
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ GitHub CLI (gh) not found!" -ForegroundColor Red
    Write-Host "Install from: https://cli.github.com/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Alternatively, create issues manually:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://github.com/Blb3D/filaops/issues/new" -ForegroundColor Cyan
    Write-Host "2. Use the titles and descriptions below:" -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($issue in $issues) {
        Write-Host "---" -ForegroundColor Gray
        Write-Host "Title: $($issue.Title)" -ForegroundColor White
        Write-Host "Body:" -ForegroundColor White
        Write-Host $issue.Body -ForegroundColor Gray
        Write-Host ""
    }
    exit 1
}

# Create issues
$created = 0
$failed = 0

foreach ($issue in $issues) {
    Write-Host "Creating: $($issue.Title)..." -ForegroundColor Yellow
    
    # Save body to temp file
    $tempFile = "issue-body-temp.md"
    Set-Content -Path $tempFile -Value $issue.Body
    
    # Create issue
    if ($useLabels) {
        $result = gh issue create `
            --title "$($issue.Title)" `
            --body-file $tempFile `
            --label "core-release" `
            2>&1
    }
    else {
        $result = gh issue create `
            --title "$($issue.Title)" `
            --body-file $tempFile `
            2>&1
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Created" -ForegroundColor Green
        $created++
    }
    else {
        Write-Host "  ❌ Failed: $result" -ForegroundColor Red
        $failed++
    }
    
    # Clean up
    Remove-Item $tempFile -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500  # Rate limiting
}

Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Created: $created" -ForegroundColor Green
Write-Host "  Failed: $failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
Write-Host ""
Write-Host "View issues: https://github.com/Blb3D/filaops/issues" -ForegroundColor Cyan

