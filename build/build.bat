@echo off
REM Build script for MDI AutoLogin
REM This creates a standalone Windows executable

echo Building MDI AutoLogin...
echo.

REM Kill all instances of the executable (request admin only if needed)
echo Stopping running instances...
taskkill /IM "MDI AutoLogin.exe" /F >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting admin to kill tasks...
    powershell -Command "Start-Process -FilePath 'taskkill' -ArgumentList '/IM', 'MDI AutoLogin.exe', '/F' -Verb RunAs -Wait -WindowStyle Hidden"
)

REM Change to app directory for build
cd /d "%~dp0..\app"

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build using the optimized spec file (spec file path relative to current dir)
pyinstaller ..\build\build.spec --workpath=build --distpath=dist

REM Check if build succeeded
if errorlevel 1 (
    echo.
    echo Build failed! Check the error messages above.
    pause
    exit /b 1
)

REM If we get here, build succeeded
echo.
echo Build successful!
echo Executable location: app\dist\MDI AutoLogin.exe
echo.
echo Next steps:
echo 1. Test the executable on a clean Windows machine
echo 2. Sign the executable with a code signing certificate (recommended)
echo 3. Submit to VirusTotal for scanning if needed
echo.
pause

