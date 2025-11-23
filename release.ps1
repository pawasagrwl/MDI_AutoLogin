# Release script for MDI AutoLogin (PowerShell version)
# This creates a git tag and pushes it, triggering the GitHub Actions build

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MDI AutoLogin Release Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Host "ERROR: Not in a git repository!" -ForegroundColor Red
    Write-Host "Please run this script from the repository root." -ForegroundColor Red
    exit 1
}

# Check if there are uncommitted changes
$changes = git status --porcelain
if ($changes) {
    Write-Host "WARNING: You have uncommitted changes!" -ForegroundColor Yellow
    Write-Host ""
    git status --short
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Host "Release cancelled." -ForegroundColor Yellow
        exit 1
    }
}

# Get version number
$version = Read-Host "Enter version number (e.g., 1.0.0)"
if ([string]::IsNullOrWhiteSpace($version)) {
    Write-Host "ERROR: Version number is required!" -ForegroundColor Red
    exit 1
}

# Validate version format (basic check)
if ($version -notmatch '^\d+\.\d+\.\d+$') {
    Write-Host "WARNING: Version format might be invalid (expected: X.Y.Z)" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Host "Release cancelled." -ForegroundColor Yellow
        exit 1
    }
}

# Create tag name
$tag = "v$version"

# Check if tag already exists
$existingTag = git tag -l $tag
if ($existingTag) {
    Write-Host "ERROR: Tag $tag already exists!" -ForegroundColor Red
    Write-Host ""
    $overwrite = Read-Host "Delete and recreate? (y/N)"
    if ($overwrite -eq "y" -or $overwrite -eq "Y") {
        Write-Host "Deleting existing tag..." -ForegroundColor Yellow
        git tag -d $tag 2>$null
        git push origin ":refs/tags/$tag" 2>$null
    } else {
        Write-Host "Release cancelled." -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Creating release: $tag" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create the tag
Write-Host "Creating git tag..." -ForegroundColor Green
git tag -a $tag -m "Release $version"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create tag!" -ForegroundColor Red
    exit 1
}

# Push the tag
Write-Host "Pushing tag to remote..." -ForegroundColor Green
git push origin $tag
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to push tag!" -ForegroundColor Red
    Write-Host ""
    Write-Host "You may need to set up your remote or push manually:" -ForegroundColor Yellow
    Write-Host "  git push origin $tag" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Release created successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Tag $tag has been pushed to GitHub." -ForegroundColor Cyan
Write-Host "GitHub Actions will now:" -ForegroundColor Cyan
Write-Host "  1. Build the Windows EXE" -ForegroundColor White
Write-Host "  2. Create a GitHub Release" -ForegroundColor White
Write-Host "  3. Attach the EXE to the release" -ForegroundColor White
Write-Host ""
Write-Host "You can monitor the build progress at:" -ForegroundColor Cyan
Write-Host "  https://github.com/pawasagrwl/MDI_AutoLogin/actions" -ForegroundColor Yellow
Write-Host ""
Write-Host "Once the build completes, your release will be available at:" -ForegroundColor Cyan
Write-Host "  https://github.com/pawasagrwl/MDI_AutoLogin/releases" -ForegroundColor Yellow
Write-Host ""

