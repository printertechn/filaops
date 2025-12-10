# Add GitHub topics to repository
# Requires: GitHub CLI (gh) installed
# Run: .\scripts\add-github-topics.ps1

$topics = @(
    "3d-printing",
    "erp",
    "docker",
    "manufacturing",
    "inventory-management",
    "print-farm",
    "mrp",
    "bom",
    "fastapi",
    "react",
    "open-source",
    "self-hosted",
    "manufacturing-software",
    "production-planning",
    "material-requirements-planning"
)

$topicsString = $topics -join ","

Write-Host "Adding GitHub topics..." -ForegroundColor Cyan
Write-Host "Topics: $topicsString" -ForegroundColor Yellow
Write-Host ""

# Check if gh CLI is installed
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ GitHub CLI (gh) not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install from: https://cli.github.com/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Or add topics manually:" -ForegroundColor Cyan
    Write-Host "1. Go to: https://github.com/Blb3D/filaops/settings" -ForegroundColor White
    Write-Host "2. Scroll to 'Topics'" -ForegroundColor White
    Write-Host "3. Add each topic:" -ForegroundColor White
    foreach ($topic in $topics) {
        Write-Host "   - $topic" -ForegroundColor Gray
    }
    exit 1
}

# Check authentication
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ GitHub CLI not authenticated!" -ForegroundColor Red
    Write-Host "Run: gh auth login" -ForegroundColor Yellow
    exit 1
}

# Add topics
Write-Host "Adding topics to repository..." -ForegroundColor Cyan
gh repo edit Blb3D/filaops --add-topic $topicsString

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ GitHub topics added successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to add topics." -ForegroundColor Red
    Write-Host "Check: gh repo view Blb3D/filaops" -ForegroundColor Yellow
}

