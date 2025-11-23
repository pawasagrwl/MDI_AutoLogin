@echo off
REM Test runner for MDI AutoLogin
echo ========================================
echo MDI AutoLogin Test Suite
echo ========================================
echo.

REM Change to app directory
cd /d "%~dp0.."

REM Run pytest
echo Running tests...
pytest tests/ -v --tb=short

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo All tests passed!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Some tests failed!
    echo ========================================
    exit /b 1
)

echo.
pause

