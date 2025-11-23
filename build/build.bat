@echo off
REM Build script for MDI AutoLogin
REM This creates a standalone Windows executable

echo Building MDI AutoLogin...
echo.



REM Change to app directory for build
cd /d "%~dp0..\app"

REM Clean previous builds thoroughly
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "MDI AutoLogin.spec" del /q "MDI AutoLogin.spec"

REM Build using the spec file (spec file path relative to current dir)
REM Use --clean to ensure fresh build
REM Note: onefile mode may show a harmless temp directory cleanup warning on exit
pyinstaller ..\build\build.spec --workpath=build --distpath=dist --clean

REM Alternative: Use onedir mode (no warning, but creates a folder):
REM pyinstaller ..\build\build-onedir.spec --workpath=build --distpath=dist --clean

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
pause

