@echo off
setlocal EnableExtensions
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    py -3.13 -c "import sys" >nul 2>nul
    if not errorlevel 1 (
        py -3.13 scripts\bootstrap.py
        exit /b %errorlevel%
    )
    py -3.12 -c "import sys" >nul 2>nul
    if not errorlevel 1 (
        py -3.12 scripts\bootstrap.py
        exit /b %errorlevel%
    )
)

python -c "import sys; assert (3,12) <= sys.version_info[:2] < (3,14)" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] PxDCA requires Python 3.12 or 3.13.
    exit /b 1
)
python scripts\bootstrap.py
exit /b %errorlevel%
