@echo off
REM Quick verification script for MDI AutoLogin startup configuration

echo ========================================
echo MDI AutoLogin Startup Verification
echo ========================================
echo.

echo Checking Scheduled Task...
echo.
schtasks /Query /TN "MDI AutoLogin" /FO LIST /V 2>nul
if errorlevel 1 (
    echo [X] Scheduled Task "MDI AutoLogin" NOT FOUND
    echo.
) else (
    echo.
    echo [✓] Scheduled Task "MDI AutoLogin" EXISTS
    echo.
    echo Checking for highest privileges...
    schtasks /Query /TN "MDI AutoLogin" /FO LIST /V | findstr /i "Highest Privileges" >nul
    if errorlevel 1 (
        echo [X] NOT running with highest privileges
    ) else (
        echo [✓] Running with HIGHEST PRIVILEGES
    )
    echo.
    echo Checking triggers...
    schtasks /Query /TN "MDI AutoLogin" /FO LIST /V | findstr /i "At log on\|At startup" >nul
    if errorlevel 1 (
        echo [X] No logon trigger found
    ) else (
        echo [✓] Has logon trigger configured
    )
)

echo.
echo Checking Registry Run Key (fallback method)...
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "MDI AutoLogin" >nul 2>&1
if errorlevel 1 (
    echo [✓] Not in Run key (good - using Scheduled Task instead)
) else (
    echo [!] Found in Run key (fallback method - may not have highest privileges)
    reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "MDI AutoLogin"
)

echo.
echo ========================================
echo Verification complete!
echo ========================================
echo.
echo If Scheduled Task exists with highest privileges, you're all set!
echo.
pause

