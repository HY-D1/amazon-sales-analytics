#!/usr/bin/env bash
# Explicit, auditable build steps. All paths anchor to this script's directory.
set -euo pipefail
cd "$(dirname "$0")"
MODE=${1:-dashboard}
if [ "$MODE" = setup ]; then
    if command -v python3.11 >/dev/null 2>&1; then
        BOOTSTRAP_PYTHON=python3.11
    else
        BOOTSTRAP_PYTHON=python3
    fi
    "$BOOTSTRAP_PYTHON" -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11+ required; validated on 3.11"'
    [ -d .venv ] || "$BOOTSTRAP_PYTHON" -m venv .venv
    .venv/bin/python -m pip install -r requirements-dev.txt
    exit 0
fi
if [ ! -x .venv/bin/python ]; then
    echo "Run ./start.sh setup first (Python 3.11)." >&2
    exit 1
fi
case "$MODE" in
    build)
        if [ -z "${DATA_PATH:-}" ]; then
            .venv/bin/python scripts/generate_demo_data.py
        fi
        .venv/bin/python -m src.data_loader
        .venv/bin/python -m src.reporting
        ;;
    test) exec .venv/bin/python -m pytest -q ;;
    check) exec .venv/bin/python check.py ;;
    report) exec .venv/bin/python -m src.reporting ;;
    dashboard) exec .venv/bin/python -m streamlit run dashboard.py --server.address=127.0.0.1 --server.port="${DASHBOARD_PORT:-8501}" --server.headless=true ;;
    notebook) exec .venv/bin/python -m jupyter lab notebooks/amazon_sales_analysis.ipynb --no-browser ;;
    *) echo "Usage: ./start.sh [setup|build|test|check|report|dashboard|notebook]" >&2; exit 2 ;;
esac
