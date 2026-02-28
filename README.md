# Amazon Sales Analytics

A data analysis toolkit that uncovers revenue patterns and customer behavior from 100K Amazon transactions for data analysts and business stakeholders using Python, SQLite, and Streamlit.

## Demo

```bash
# Start the interactive menu
$ ./start.sh

📊 Amazon Sales Analytics
═══════════════════════════════════════

Choose an option:
  1) 📓 Open Jupyter Notebook
  2) 📊 Open Streamlit Dashboard

Enter your choice [1-2]:
```

## Features

### Implemented (v1.0)

- **Jupyter Notebook Analysis**: 5-section analysis with SQL queries, visualizations, and statistical insights
- **Interactive Streamlit Dashboard**: KPI cards, filterable charts, and data explorer
- **SQLite Data Layer**: Zero-setup database with pre-defined SQL views
- **Health Check Script**: Environment validation and diagnostics
- **Auto Environment Setup**: Virtual environment and dependency management via `start.sh`

### Planned (v2.0)

- Time series forecasting (Prophet/ARIMA)
- Customer segmentation (RFM analysis)
- A/B test analysis framework
- PDF/Excel report export
- Streamlit Cloud deployment support

## Architecture

Data flows from CSV → SQLite via `data_loader.py`, queried by either the Jupyter notebook (analysis) or Streamlit dashboard (interactive exploration). The notebook provides deep-dive SQL analysis and statistical modeling, while the dashboard offers real-time filtering and KPI tracking.

```mermaid
graph LR
    A[Amazon.csv] -->|load_data()| B[(SQLite DB)]
    B -->|SQL Queries| C[Jupyter Notebook]
    B -->|Pandas/Plotly| D[Streamlit Dashboard]
    C -->|Visualizations| E[Charts & Insights]
    D -->|Interactive| F[KPIs & Filters]
```

## Setup

### Prerequisites

- Python 3.9+
- 500MB disk space (includes virtual environment)

### Quick Start

```bash
# Interactive menu (recommended)
./start.sh

# Direct commands
./start.sh notebook     # Launch Jupyter Lab
./start.sh dashboard    # Launch Streamlit (port 8501-8510)
```

### Run Tests

```bash
# Environment and dependency validation
python3 check.py
```

### Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_PATH` | `data/Amazon.csv` | Path to transaction CSV |
| `DB_PATH` | `data/amazon.db` | SQLite database location |
| `DASHBOARD_PORT` | `8501` | Streamlit server port |

No configuration file required; modify `src/data_loader.py` or `dashboard.py` directly for custom paths.

## API Reference

N/A

## Data Model / Schema

**Table: `sales`** (100,000 rows)

| Column | Type | Description |
|--------|------|-------------|
| `orderid` | TEXT | Unique order identifier (ORD0000001) |
| `orderdate` | DATETIME | Order timestamp (2020-2024) |
| `customerid` | TEXT | Customer identifier (CUST######) |
| `customername` | TEXT | Full customer name |
| `productid` | TEXT | Product SKU (P#####) |
| `productname` | TEXT | Product description |
| `category` | TEXT | Electronics, Sports, Books, Clothing, Home & Kitchen, Toys |
| `brand` | TEXT | Product brand |
| `quantity` | INTEGER | Items ordered |
| `unitprice` | REAL | Price per unit ($) |
| `discount` | REAL | Discount rate (0.0-0.15) |
| `tax` | REAL | Tax amount ($) |
| `shippingcost` | REAL | Shipping cost ($) |
| `totalamount` | REAL | Final order total ($) |
| `paymentmethod` | TEXT | Credit Card, Debit Card, Amazon Pay, Gift Card, COD |
| `orderstatus` | TEXT | Delivered, Shipped, Pending, Returned, Cancelled |
| `city` | TEXT | Customer city |
| `state` | TEXT | Customer state |
| `country` | TEXT | Country (US, India, etc.) |
| `sellerid` | TEXT | Seller identifier |

**SQL Views:**
- `revenue_by_category` - Aggregated revenue per category
- `monthly_sales` - Time-series revenue data
- `customer_summary` - Per-customer metrics (orders, revenue, LTV)

## Trade-offs & Design Decisions

- **Chose:** SQLite over PostgreSQL
  - **Gave up:** Concurrent write support, enterprise scalability
  - **Why:** Zero-setup portability; users can run immediately without Docker or database configuration

- **Chose:** Manual/integration testing via `check.py` over unit tests
  - **Gave up:** Automated regression coverage, CI/CD integration
  - **Why:** Project is analysis-focused with visual outputs; health checks verify environment and data integrity more effectively than unit tests for notebooks

- **Chose:** Single-file Streamlit dashboard over modular components
  - **Gave up:** Code reusability, testability
  - **Why:** Simpler deployment to Streamlit Cloud; single entry point reduces complexity for data analysts who may not be software engineers

## Limitations

- Dataset contains synthetic/mock data (no real PII)
- SQLite is single-writer; concurrent dashboard sessions may experience locks
- No authentication on dashboard (local-only deployment)
- Windows support requires `start.bat` (maintained separately from `start.sh`)
- No automated tests for notebook cells; visual inspection required

## Next Steps

1. Implement time series forecasting for revenue prediction
2. Add customer segmentation using RFM (Recency, Frequency, Monetary) analysis
3. Create PDF report generator from notebook outputs
4. Deploy dashboard to Streamlit Cloud with public data source
5. Add unit tests for `data_loader.py` functions
