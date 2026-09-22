@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if exist ".env" (
    for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do set "%%A=%%B"
)

if not exist ".venv\Scripts\python.exe" (
    echo [PxDCA] First run detected. Installing the local Python environment...
    call install.bat
    if errorlevel 1 exit /b 1
)

".venv\Scripts\python.exe" -c "import fastmcp, jsonschema, sys; assert (3,12) <= sys.version_info[:2] < (3,14); assert fastmcp.__version__ == '3.4.7'" >nul 2>nul
if errorlevel 1 (
    echo [PxDCA] Python dependencies are missing or incompatible. Repairing installation...
    call install.bat
    if errorlevel 1 exit /b 1
)

set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "PYTHONPATH=%CD%"
if not defined PXDCA_CONFIG set "PXDCA_CONFIG=%CD%\config\pxdca.toml"

echo [PxDCA] Starting local MCP service. Runtime settings: %PXDCA_CONFIG%
".venv\Scripts\python.exe" -m server.fastmcp_service
exit /b %errorlevel%
