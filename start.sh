#!/bin/bash

# Amazon Sales Analytics - Quick Start Script
# Usage: ./start.sh [notebook|dashboard]

set -e  # Exit on error

echo "📊 Amazon Sales Analytics"
echo "=========================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source .venv/bin/activate

# Install requirements if needed
if [ ! -f ".venv/installed" ] || [ "requirements.txt" -nt ".venv/installed" ]; then
    echo -e "${BLUE}📥 Installing dependencies...${NC}"
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    touch .venv/installed
    echo -e "${GREEN}✅ Dependencies installed!${NC}"
fi

# Parse argument
MODE=${1:-menu}

if [ "$MODE" == "notebook" ] || [ "$MODE" == "n" ]; then
    echo -e "${GREEN}🚀 Starting Jupyter Lab...${NC}"
    echo -e "${YELLOW}   URL: http://localhost:8888${NC}"
    jupyter lab notebooks/amazon_sales_analysis.ipynb --no-browser
    
elif [ "$MODE" == "dashboard" ] || [ "$MODE" == "d" ]; then
    echo -e "${GREEN}🚀 Starting Streamlit Dashboard...${NC}"
    echo -e "${YELLOW}   URL: http://localhost:8501${NC}"
    streamlit run dashboard.py
    
else
    # Interactive menu
    echo ""
    echo "Choose an option:"
    echo "  1) 📓 Run Jupyter Notebook (analysis)"
    echo "  2) 📊 Run Streamlit Dashboard (interactive)"
    echo "  3) 🔧 Reinstall dependencies"
    echo "  4) ❌ Exit"
    echo ""
    read -p "Enter choice [1-4]: " choice
    
    case $choice in
        1)
            echo -e "${GREEN}🚀 Starting Jupyter Lab...${NC}"
            echo -e "${YELLOW}   URL: http://localhost:8888${NC}"
            jupyter lab notebooks/amazon_sales_analysis.ipynb --no-browser
            ;;
        2)
            echo -e "${GREEN}🚀 Starting Streamlit Dashboard...${NC}"
            echo -e "${YELLOW}   URL: http://localhost:8501${NC}"
            streamlit run dashboard.py
            ;;
        3)
            echo -e "${BLUE}🔄 Reinstalling dependencies...${NC}"
            rm -f .venv/installed
            pip install -q -r requirements.txt
            touch .venv/installed
            echo -e "${GREEN}✅ Done! Run ./start.sh again.${NC}"
            ;;
        4)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid choice. Run ./start.sh again."
            exit 1
            ;;
    esac
fi
