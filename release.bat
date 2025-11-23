@echo off
REM Release script for MDI AutoLogin
REM This creates a git tag and pushes it, triggering the GitHub Actions build

echo ========================================
echo MDI AutoLogin Release Script
echo ========================================
echo.

REM Check if we're in a git repository
git rev-parse --git-dir >nul 2>&1
if errorlevel 1 (
    echo ERROR: Not in a git repository!
    echo Please run this script from the repository root.
    pause
    exit /b 1
)

REM Check if there are uncommitted changes
git diff --quiet
if errorlevel 1 (
    echo WARNING: You have uncommitted changes!
    echo.
    git status --short
    echo.
    set /p continue="Continue anyway? (y/N): "
    if /i not "%continue%"=="y" (
        echo Release cancelled.
        pause
        exit /b 1
    )
)

REM Get version number
set /p version="Enter version number (e.g., 1.0.0): "
if "%version%"=="" (
    echo ERROR: Version number is required!
    pause
    exit /b 1
)

REM Validate version format (basic check)
echo %version% | findstr /r "^[0-9]\+\.[0-9]\+\.[0-9]\+$" >nul
if errorlevel 1 (
    echo WARNING: Version format might be invalid (expected: X.Y.Z)
    set /p continue="Continue anyway? (y/N): "
    if /i not "%continue%"=="y" (
        echo Release cancelled.
        pause
        exit /b 1
    )
)

REM Create tag name
set tag=v%version%

REM Check if tag already exists
git rev-parse %tag% >nul 2>&1
if not errorlevel 1 (
    echo ERROR: Tag %tag% already exists!
    echo.
    set /p overwrite="Delete and recreate? (y/N): "
    if /i "%overwrite%"=="y" (
        echo Deleting existing tag...
        git tag -d %tag% >nul 2>&1
        git push origin :refs/tags/%tag% >nul 2>&1
    ) else (
        echo Release cancelled.
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo Creating release: %tag%
echo ========================================
echo.

REM Create the tag
echo Creating git tag...
git tag -a %tag% -m "Release %version%"
if errorlevel 1 (
    echo ERROR: Failed to create tag!
    pause
    exit /b 1
)

REM Push the tag
echo Pushing tag to remote...
git push origin %tag%
if errorlevel 1 (
    echo ERROR: Failed to push tag!
    echo.
    echo You may need to set up your remote or push manually:
    echo   git push origin %tag%
    pause
    exit /b 1
)

echo.
echo ========================================
echo Release created successfully!
echo ========================================
echo.
echo Tag %tag% has been pushed to GitHub.
echo GitHub Actions will now:
echo   1. Build the Windows EXE
echo   2. Create a GitHub Release
echo   3. Attach the EXE to the release
echo.
echo You can monitor the build progress at:
echo   https://github.com/pawasagrwl/MDI_AutoLogin/actions
echo.
echo Once the build completes, your release will be available at:
echo   https://github.com/pawasagrwl/MDI_AutoLogin/releases
echo.
pause

