@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if exist ".env" (
    for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do set "%%A=%%B"
)

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
if not defined MCP_HOST set "MCP_HOST=127.0.0.1"
if not defined MCP_PORT set "MCP_PORT=8000"
if not defined MCP_PATH set "MCP_PATH=/mcp"
if not defined MCP_TRANSPORT set "MCP_TRANSPORT=http"
if not defined MCP_OUTPUT_ROOT set "MCP_OUTPUT_ROOT=%CD%\output"

echo [FastMCP] Starting local MCP service at http://%MCP_HOST%:%MCP_PORT%%MCP_PATH%
".venv\Scripts\python.exe" -m server.fastmcp_service
exit /b %errorlevel%
