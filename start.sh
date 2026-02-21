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
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed.${NC}"
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

# Check if data exists
if [ ! -f "data/Amazon.csv" ]; then
    echo -e "${RED}❌ Error: data/Amazon.csv not found!${NC}"
    exit 1
fi

# Parse argument
MODE=${1:-menu}

run_notebook() {
    echo -e "${GREEN}🚀 Starting Jupyter Lab...${NC}"
    echo -e "${YELLOW}   URL: http://localhost:8888${NC}"
    echo -e "${YELLOW}   Press Ctrl+C to stop${NC}"
    echo ""
    jupyter lab notebooks/amazon_sales_analysis.ipynb --no-browser || {
        echo -e "${RED}❌ Failed to start Jupyter. Try: pip install jupyterlab${NC}"
        exit 1
    }
}

run_dashboard() {
    echo -e "${GREEN}🚀 Starting Streamlit Dashboard...${NC}"
    
    # Find available port (cross-platform)
    PORT=8501
    MAX_PORT=8510
    while [ $PORT -le $MAX_PORT ]; do
        # Check if port is in use (cross-platform method)
        if ! (echo "" > /dev/tcp/localhost/$PORT) 2>/dev/null; then
            break
        fi
        echo -e "${YELLOW}⚠️  Port $PORT is busy, trying $((PORT+1))...${NC}"
        PORT=$((PORT+1))
    done
    
    if [ $PORT -gt $MAX_PORT ]; then
        echo -e "${RED}❌ Could not find available port between 8501-8510${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}   URL: http://localhost:$PORT${NC}"
    echo -e "${YELLOW}   Press Ctrl+C to stop${NC}"
    echo ""
    
    # Run Streamlit with error handling
    if ! streamlit run dashboard.py --server.port=$PORT --server.headless=true 2>&1; then
        echo ""
        echo -e "${RED}❌ Streamlit failed to start${NC}"
        echo -e "${YELLOW}   Common fixes:${NC}"
        echo -e "   1. Install: pip install streamlit plotly${NC}"
        echo -e "   2. Check Python: python3 --version${NC}"
        echo -e "   3. Run check: python3 check.py${NC}"
        exit 1
    fi
}

if [ "$MODE" == "notebook" ] || [ "$MODE" == "n" ]; then
    run_notebook
    
elif [ "$MODE" == "dashboard" ] || [ "$MODE" == "d" ]; then
    run_dashboard
    
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
            run_notebook
            ;;
        2)
            run_dashboard
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
