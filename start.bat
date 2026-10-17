@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=dashboard"
if "%MODE%"=="setup" (
    if not exist .venv\Scripts\python.exe py -3.11 -m venv .venv
    if errorlevel 1 exit /b 1
    .venv\Scripts\python.exe -m pip install -r requirements-dev.txt
    exit /b
)
if not exist .venv\Scripts\python.exe (
    echo Run start.bat setup first with Python 3.11 installed.
    exit /b 1
)
if "%MODE%"=="build" (
    if not defined DATA_PATH .venv\Scripts\python.exe scripts\generate_demo_data.py
    if errorlevel 1 exit /b 1
    .venv\Scripts\python.exe -m src.data_loader
    if errorlevel 1 exit /b 1
    .venv\Scripts\python.exe -m src.reporting
    exit /b
)
if "%MODE%"=="test" (
    .venv\Scripts\python.exe -m pytest -q
    exit /b
)
if "%MODE%"=="check" (
    .venv\Scripts\python.exe check.py
    exit /b
)
if "%MODE%"=="report" (
    .venv\Scripts\python.exe -m src.reporting
    exit /b
)
if "%MODE%"=="notebook" (
    .venv\Scripts\python.exe -m jupyter lab notebooks\amazon_sales_analysis.ipynb --no-browser
    exit /b
)
if "%MODE%"=="dashboard" (
    if not defined DASHBOARD_PORT set "DASHBOARD_PORT=8501"
    .venv\Scripts\python.exe -m streamlit run dashboard.py --server.address=127.0.0.1 --server.port=!DASHBOARD_PORT! --server.headless=true
    exit /b
)
echo Usage: start.bat [setup^|build^|test^|check^|report^|dashboard^|notebook]
exit /b 2
