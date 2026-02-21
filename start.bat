@echo off
REM Amazon Sales Analytics - Windows Quick Start
REM Usage: start.bat [notebook|dashboard]

echo 📊 Amazon Sales Analytics
echo ==========================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is required but not installed.
    exit /b 1
)

REM Check if virtual environment exists
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install requirements if needed
if not exist ".venv\installed" (
    echo 📥 Installing dependencies...
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    type nul > .venv\installed
    echo ✅ Dependencies installed!
)

REM Check if data exists
if not exist "data\Amazon.csv" (
    echo ❌ Error: data\Amazon.csv not found!
    exit /b 1
)

REM Parse argument
if "%1"=="notebook" goto notebook
if "%1"=="n" goto notebook
if "%1"=="dashboard" goto dashboard
if "%1"=="d" goto dashboard

REM Interactive menu
echo.
echo Choose an option:
echo   1) 📓 Run Jupyter Notebook (analysis)
echo   2) 📊 Run Streamlit Dashboard (interactive)
echo   3) 🔧 Reinstall dependencies
echo   4) ❌ Exit
echo.
set /p choice="Enter choice [1-4]: "

if "%choice%"=="1" goto notebook
if "%choice%"=="2" goto dashboard
if "%choice%"=="3" goto reinstall
if "%choice%"=="4" goto end

echo ❌ Invalid choice.
goto end

:notebook
echo 🚀 Starting Jupyter Lab...
echo    URL: http://localhost:8888
echo    Press Ctrl+C to stop
echo.
jupyter lab notebooks/amazon_sales_analysis.ipynb --no-browser
if errorlevel 1 (
    echo ❌ Failed to start Jupyter.
    echo    Try: pip install jupyterlab
)
goto end

:dashboard
echo 🚀 Starting Streamlit Dashboard...
echo    URL: http://localhost:8501 (or next available)
echo    Press Ctrl+C to stop
echo.
streamlit run dashboard.py --server.headless=true
if errorlevel 1 (
    echo ❌ Failed to start Streamlit.
    echo    Try: pip install streamlit plotly
)
goto end

:reinstall
echo 🔄 Reinstalling dependencies...
del .venv\installed 2>nul
pip install -q -r requirements.txt
type nul > .venv\installed
echo ✅ Done! Run start.bat again.
goto end

:end
