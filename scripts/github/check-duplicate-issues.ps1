# Check for Duplicate GitHub Issues
# Compares planned issues with existing GitHub issues to prevent duplicates
# Requires: GitHub CLI (gh) installed and authenticated
# Run: .\scripts\check-duplicate-issues.ps1

Write-Host "Checking for duplicate GitHub issues..." -ForegroundColor Cyan
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

# Fetch all open issues
Write-Host "Fetching existing GitHub issues..." -ForegroundColor Yellow
$existingIssues = gh issue list --state all --json number,title,body --limit 100 | ConvertFrom-Json

Write-Host "Found $($existingIssues.Count) existing issues" -ForegroundColor Cyan
Write-Host ""

# Define planned issues to check
$plannedIssues = @(
    @{
        Number = 1
        Title = "[Infra] Set up Alembic database migrations"
        Keywords = @("alembic", "database migrations", "migrations")
    },
    @{
        Number = 2
        Title = "[Infra] Set up GitHub Actions CI/CD pipeline"
        Keywords = @("ci/cd", "github actions", "pipeline", "workflow")
    },
    @{
        Number = 3
        Title = "[Chore] Fix hardcoded localhost:8000 API URLs in frontend"
        Keywords = @("api_url", "hardcoded", "localhost:8000", "frontend")
    },
    @{
        Number = 33
        Title = "[Security] Add rate limiting to authentication endpoints"
        Keywords = @("rate limiting", "authentication", "slowapi", "security")
    },
    @{
        Number = 34
        Title = "[Security] Remove personal address from default settings"
        Keywords = @("personal address", "settings", "ship_from", "security")
    },
    @{
        Number = 6
        Title = "[Chore] Replace print() statements with structured logging in backend"
        Keywords = @("print()", "logging", "structured logging", "backend")
    },
    @{
        Number = 7
        Title = "[Chore] Remove commented-out code blocks"
        Keywords = @("commented-out", "code cleanup", "remove comments")
    },
    @{
        Number = 8
        Title = "[Chore] Convert console.error to proper error handling in frontend"
        Keywords = @("console.error", "error handling", "frontend", "react")
    }
)

Write-Host "Checking for duplicates..." -ForegroundColor Yellow
Write-Host ""

$duplicatesFound = @()
$safeToCreate = @()

foreach ($planned in $plannedIssues) {
    $found = $false
    $matches = @()
    
    foreach ($existing in $existingIssues) {
        $titleMatch = $existing.title -like "*$($planned.Title.Replace('[', '').Replace(']', '').Split(' ')[-1])*"
        $keywordMatches = 0
        
        foreach ($keyword in $planned.Keywords) {
            if ($existing.title -match $keyword -or $existing.body -match $keyword) {
                $keywordMatches++
            }
        }
        
        # If title matches or 2+ keywords match, consider it a duplicate
        if ($titleMatch -or $keywordMatches -ge 2) {
            $found = $true
            $matches += @{
                Number = $existing.number
                Title = $existing.title
                Matches = $keywordMatches
            }
        }
    }
    
    if ($found) {
        $duplicatesFound += @{
            Planned = $planned
            Existing = $matches
        }
        Write-Host "⚠️  DUPLICATE FOUND: '$($planned.Title)'" -ForegroundColor Yellow
        foreach ($match in $matches) {
            $matchType = if ($match.IsTitleMatch) { "Title match" } else { "Keyword match ($($match.MatchedKeywords))" }
            Write-Host "   → Matches existing issue #$($match.Number): $($match.Title)" -ForegroundColor Red
            Write-Host "     Match type: $matchType" -ForegroundColor Gray
        }
        Write-Host ""
    } else {
        $safeToCreate += $planned
        Write-Host "✅ Safe to create: '$($planned.Title)'" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

if ($duplicatesFound.Count -gt 0) {
    Write-Host "⚠️  Found $($duplicatesFound.Count) potential duplicate(s):" -ForegroundColor Yellow
    Write-Host ""
    foreach ($dup in $duplicatesFound) {
        Write-Host "Planned Issue:" -ForegroundColor White
        Write-Host "  Title: $($dup.Planned.Title)" -ForegroundColor Gray
        Write-Host "  Expected Number: #$($dup.Planned.Number)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  Matches Existing Issue(s):" -ForegroundColor White
        foreach ($match in $dup.Existing) {
            $matchType = if ($match.IsTitleMatch) { " (Title match)" } else { " (Keyword match: $($match.MatchedKeywords))" }
            Write-Host "    - Issue #$($match.Number): $($match.Title)$matchType" -ForegroundColor Red
        }
        Write-Host ""
    }
} else {
    Write-Host "✅ No duplicates found! All issues are safe to create." -ForegroundColor Green
    Write-Host ""
}

Write-Host "Issues safe to create: $($safeToCreate.Count)" -ForegroundColor Cyan
if ($safeToCreate.Count -gt 0) {
    Write-Host ""
    Write-Host "Safe issues:" -ForegroundColor White
    foreach ($safe in $safeToCreate) {
        Write-Host "  - #$($safe.Number): $($safe.Title)" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "View all issues: https://github.com/Blb3D/filaops/issues" -ForegroundColor Cyan

