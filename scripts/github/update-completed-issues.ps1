# Update GitHub Issues with Completion Status
# Requires: GitHub CLI (gh) installed and authenticated
# Run: .\scripts\update-completed-issues.ps1

Write-Host "Updating GitHub issues with completion status..." -ForegroundColor Cyan
Write-Host ""

# Check if gh CLI is installed
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ GitHub CLI (gh) not found!" -ForegroundColor Red
    Write-Host "Install from: https://cli.github.com/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Alternatively, update issues manually:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://github.com/Blb3D/filaops/issues" -ForegroundColor Cyan
    Write-Host "2. Update issues #33 and #34 with completion comments" -ForegroundColor Cyan
    Write-Host "3. Create new issues #6, #7, and #8 from GITHUB_ISSUES_TO_CREATE.md" -ForegroundColor Cyan
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

# Update Issue #33: Rate Limiting
Write-Host "Updating Issue #33: Rate Limiting..." -ForegroundColor Yellow
$comment33 = @"
## ✅ Completed - December 2025

This issue has been completed! Here's what was implemented:

### Implementation Details
- ✅ Installed `slowapi==0.1.9` and added to `requirements.txt`
- ✅ Rate limit `/api/v1/auth/login` to 5 requests/minute per IP
- ✅ Rate limit `/api/v1/auth/register` to 3 requests/minute per IP  
- ✅ Rate limit `/api/v1/auth/password-reset/request` to 3 requests/minute per IP
- ✅ Rate limit `/api/v1/auth/portal/login` to 5 requests/minute per IP
- ✅ Rate limit `/api/v1/auth/portal/register` to 3 requests/minute per IP
- ✅ Returns appropriate 429 response with retry-after header

### Files Modified
- `backend/requirements.txt` - Added slowapi dependency
- `backend/app/main.py` - Configured limiter middleware
- `backend/app/api/v1/endpoints/auth.py` - Added rate limiting decorators

### Testing
Rate limiting is active and will return 429 status when limits are exceeded.

**Note:** Tests for rate limiting behavior can be added as a future enhancement.
"@

$tempFile33 = "issue-33-comment.md"
Set-Content -Path $tempFile33 -Value $comment33
gh issue comment 33 --body-file $tempFile33
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Added completion comment" -ForegroundColor Green
} else {
    Write-Host "  ❌ Failed to add comment" -ForegroundColor Red
}
Remove-Item $tempFile33 -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 500

# Update Issue #34: Personal Address
Write-Host "Updating Issue #34: Personal Address..." -ForegroundColor Yellow
$comment34 = @"
## ✅ Completed - December 2025

This issue has been completed! Here's what was implemented:

### Implementation Details
- ✅ All default address values replaced with placeholders
- ✅ Updated `SHIP_FROM_NAME`, `SHIP_FROM_STREET1`, `SHIP_FROM_CITY`, `SHIP_FROM_STATE`, `SHIP_FROM_ZIP`, `SHIP_FROM_COUNTRY`, `SHIP_FROM_PHONE`
- ✅ Updated `SMTP_FROM_EMAIL` and `SMTP_FROM_NAME` to generic placeholders
- ✅ Updated `ADMIN_APPROVAL_EMAIL` to generic placeholder
- ✅ Added comments noting these must be configured via environment variables

### Files Modified
- `backend/app/core/settings.py` - Replaced all personal/business data with generic placeholders

### Example Changes
- `SHIP_FROM_NAME`: "BLB3D Printing" → "Your Company Name"
- `SHIP_FROM_STREET1`: "[REAL ADDRESS]" → "123 Main Street"
- `SHIP_FROM_CITY`: "[REAL CITY]" → "Your City"
- `SMTP_FROM_EMAIL`: Real email → "noreply@example.com"

**Note:** Updating `.env.example` with required variables can be done as a future enhancement.
"@

$tempFile34 = "issue-34-comment.md"
Set-Content -Path $tempFile34 -Value $comment34
gh issue comment 34 --body-file $tempFile34
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Added completion comment" -ForegroundColor Green
} else {
    Write-Host "  ❌ Failed to add comment" -ForegroundColor Red
}
Remove-Item $tempFile34 -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 500

Write-Host ""
Write-Host "✅ Issue updates complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Review the comments added to issues #33 and #34" -ForegroundColor White
Write-Host "2. Close the issues if you're satisfied with the completion" -ForegroundColor White
Write-Host "3. Create new issues #6, #7, and #8 from GITHUB_ISSUES_TO_CREATE.md" -ForegroundColor White
Write-Host ""
Write-Host "View issues: https://github.com/Blb3D/filaops/issues" -ForegroundColor Cyan

