@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [LogicMCP] First run detected. Installing the local Python environment...
    call install.bat
    if errorlevel 1 exit /b 1
)

".venv\Scripts\python.exe" -c "from fastmcp import FastMCP; import jsonschema" >nul 2>nul
if errorlevel 1 (
    echo [LogicMCP] Python dependencies are missing or incompatible. Repairing installation...
    call install.bat
    if errorlevel 1 exit /b 1
)

set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "PYTHONPATH=%CD%"
set "MCP_HOST=127.0.0.1"
set "MCP_PORT=8000"
set "MCP_PATH=/mcp"
set "MCP_TRANSPORT=http"
set "MCP_OUTPUT_ROOT=%CD%\output"

echo [FastMCP] Starting local MCP service at http://127.0.0.1:8000/mcp
".venv\Scripts\python.exe" -m server.fastmcp_service
exit /b %errorlevel%
