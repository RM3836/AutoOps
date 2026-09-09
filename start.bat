@echo off
chcp 65001 >nul 2>&1
setlocal EnableExtensions

title AutoOps

cd /d "%~dp0"

if not exist "run.py" (
    echo [ERROR] run.py not found.
    echo Please make sure this file is in the project root.
    pause
    exit /b 1
)

set "PYTHON_CMD="
python --version >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=python"

if not defined PYTHON_CMD (
    py --version >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py"
)

if not defined PYTHON_CMD (
    python3 --version >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python3"
)

if not defined PYTHON_CMD (
    echo [ERROR] Python 3.9+ not found.
    pause
    exit /b 1
)

echo [INFO] Using %PYTHON_CMD%
echo [INFO] Launching AutoOps...
echo.

"%PYTHON_CMD%" -u run.py

echo.
echo [INFO] AutoOps stopped.
pause

endlocal
