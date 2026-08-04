@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [LogicMCP] Creating Python virtual environment...
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3.11 -m venv .venv 2>nul
        if errorlevel 1 py -3 -m venv .venv
    ) else (
        python -m venv .venv
    )
    if errorlevel 1 (
        echo [ERROR] Python 3.11 or newer is required.
        exit /b 1
    )
)

echo [LogicMCP] Installing Python dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo [LogicMCP] FastMCP service installation complete.
exit /b 0
