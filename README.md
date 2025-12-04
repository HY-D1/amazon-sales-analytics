# Amazon Sales Analytics Project

A comprehensive data analytics portfolio project demonstrating end-to-end analysis of Amazon sales data, featuring descriptive statistics, predictive modeling, SQL querying, and interactive visualizations.

## Project Overview

This project analyzes 100,000 Amazon sales transactions to uncover business insights and build predictive models. The analysis demonstrates proficiency in Python data science libraries, SQL, statistical analysis, and machine learning fundamentals.

## Dataset Description

The Amazon sales dataset contains 20 features across 100,000 transactions including order details, customer information, product data, pricing, and geographic information. Key features include OrderDate, ProductName, Category, Brand, UnitPrice, Discount, TotalAmount, PaymentMethod, and OrderStatus.

## Technical Stack

**Data Analysis:** Python (Pandas, NumPy), SQL (PostgreSQL)  
**Visualization:** Matplotlib, Seaborn, Plotly  
**Machine Learning:** Scikit-learn  
**Statistical Analysis:** SciPy, Statsmodels  
**Development Environment:** Docker, Jupyter Lab  
**Version Control:** Git

## Getting Started

### Prerequisites

Docker Desktop installed

### Setup Instructions


```bash
# Build containers
docker-compose build

# Start environment
docker-compose up

# Access Jupyter Lab at: http://localhost:8888
# Token: amazon_analytics_2024
```

### Database Connection

```bash
postgresql://analyst:analytics2024@postgres:5432/amazon_sales
```

### Stopping and Restarting
```bash
# Ctrl+C, then:
docker-compose down
```

## Project Structure

```
amazon-sales-analytics/
├── Dockerfile                  # Python environment configuration
├── docker-compose.yml          # Multi-container orchestration
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── .gitignore                  # Files to exclude from git
├── data/
│   └── Amazon.csv             # Raw dataset
├── sql_scripts/
│   └── init_db.sql            # Database initialization
├── notebooks/
│   ├── 01_exploratory_analysis.ipynb
│   ├── 02_descriptive_statistics.ipynb
│   └── 03_predictive_modeling.ipynb
├── src/
│   ├── data_loader.py         # Data loading utilities
│   ├── preprocessing.py       # Data cleaning functions
│   └── models.py              # ML model implementations
└── visualizations/
    └── (Generated charts and dashboards)
```

## Analysis Components

The project includes comprehensive exploratory data analysis examining sales patterns. I perform descriptive statistical analysis calculating key metrics like average order value, discount patterns, revenue by category, and seasonal trends. The predictive modeling component builds machine learning models to forecast sales volumes, predict order values, and classify high-value customers. Finally, SQL querying demonstrates database operations including complex joins, aggregations, window functions, and subqueries to extract business insights.