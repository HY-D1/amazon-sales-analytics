# 📊 Amazon Sales Analytics

A comprehensive data analysis of **100,000 Amazon transactions** uncovering revenue patterns, customer behavior, and business opportunities.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Pandas](https://img.shields.io/badge/Pandas-2.1.4-green)](https://pandas.pydata.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.29-FF4B4B)](https://streamlit.io)

---

## 🎯 Key Findings

| Metric | Value | Insight |
|--------|-------|---------|
| 💰 **Total Revenue** | $91.8M | Strong revenue base across 4 years |
| 📦 **Total Orders** | 100,000 | 3 items avg per order |
| 💵 **Avg Order Value** | $918 | Median $714 (right-skewed distribution) |
| 👥 **Unique Customers** | 43,233 | 2.3 orders per customer avg |
| ✅ **Delivery Rate** | 74.6% | 25% orders need attention |

### 📈 Strategic Insights

1. **🎯 Revenue Concentration**: Top 20% of customers generate **44% of total revenue**
   - *Recommendation*: Implement VIP customer retention program

2. **⚠️ Order Fulfillment Gap**: 25% orders cancelled/returned/pending
   - *Potential Recovery*: ~$23M if 50% issues resolved

3. **📦 Category Leaders**: Electronics & Sports dominate (~17K orders each)
   - *Recommendation*: Prioritize inventory for top categories

4. **💳 Payment Trends**: Credit cards 35%, Cash on Delivery only 5%
   - *Trend*: Strong digital payment adoption

5. **🗺️ Geographic Concentration**: 70% sales from US (Texas & California lead)
   - *Opportunity*: Expand in underperforming states

---

## 🚀 Quick Start (One Command)

```bash
./start.sh
```

That's it! The script will:
- ✅ Create virtual environment (if needed)
- ✅ Install dependencies (if needed)
- ✅ Show interactive menu to choose:
  - 📓 **Jupyter Notebook** - Complete analysis with code
  - 📊 **Streamlit Dashboard** - Interactive web dashboard

### Alternative Commands
```bash
./start.sh notebook     # Jump straight to notebook
./start.sh dashboard    # Jump straight to dashboard
```

---

## 📊 What You'll See

### Option 1: Jupyter Notebook
Complete analysis with 5 sections:
1. Data Overview & SQL Queries
2. Visual Analysis (Categories, Status, Payments)
3. Customer Insights & Pareto Analysis
4. Statistical Summary
5. Business Recommendations

### Option 2: Streamlit Dashboard
Interactive web interface with:
- **5 KPI Cards** (Revenue, Orders, AOV, Customers, Delivery Rate)
- **Interactive Charts** (filter, zoom, hover)
- **Geographic Analysis** (maps and breakdowns)
- **Data Explorer** (filter & export CSV)

---

## 📁 Project Structure

```
amazon-sales-analytics/
├── 🚀 start.sh                  # ← RUN THIS
├── 📊 dashboard.py              # Interactive Streamlit dashboard
├── 📓 notebooks/
│   └── amazon_sales_analysis.ipynb  # Complete analysis
├── 📁 data/
│   └── Amazon.csv              # 100K transactions
├── 🔧 src/
│   └── data_loader.py          # SQLite utilities
├── 📋 requirements.txt          # Python dependencies
└── 📖 README.md
```

---

## 🛠️ Manual Setup (if you prefer)

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run notebook
jupyter lab notebooks/amazon_sales_analysis.ipynb

# Or run dashboard
streamlit run dashboard.py
```

## 🔧 Troubleshooting

### Dashboard won't start / "Connection refused"

**Check:**
```bash
python3 check.py          # Diagnose issues
```

**Common fixes:**
1. **Missing packages:**
   ```bash
   pip install streamlit plotly seaborn
   ```

2. **Port 8501 busy:** The start.sh will auto-find another port (8502, 8503...)

3. **Virtual environment issues:**
   ```bash
   rm -rf .venv              # Remove old venv
   ./start.sh                # Recreate
   ```

### Windows Users
Use `start.bat` instead of `./start.sh`:
```cmd
start.bat
```

### Check Python version
```bash
python3 --version    # Needs 3.9+
```

---

## 💻 Code Example

```python
import pandas as pd
from src.data_loader import load_data

# Load data (auto-creates SQLite DB)
df, conn = load_data()

# Query with SQL
revenue = pd.read_sql("""
    SELECT category, SUM(totalamount) as revenue
    FROM sales
    GROUP BY category
    ORDER BY revenue DESC
""", conn)

print(revenue)
```

---

## 📦 Tech Stack

| Category | Tools |
|----------|-------|
| **Data Processing** | Pandas, NumPy |
| **Database** | SQLite |
| **Visualization** | Matplotlib, Seaborn, Plotly |
| **Dashboard** | Streamlit |
| **Statistics** | SciPy |

---

## 📝 Dataset

- **Size**: 100,000 transactions
- **Date Range**: 2020-2024
- **Features**: 20 columns (orders, customers, products, payments, geography)
- **Categories**: Electronics, Sports, Books, Clothing, Home & Kitchen, Toys

---

## 🤝 Contributing

Feel free to extend with:
- Time series forecasting
- Customer segmentation models
- A/B test analysis
- Additional visualizations

---

**Created with**: Python · Pandas · SQLite · Plotly · Streamlit

*Last updated: 2024*
