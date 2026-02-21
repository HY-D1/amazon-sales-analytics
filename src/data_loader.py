"""
Simple Data Loader for Amazon Sales Dataset
Uses SQLite instead of PostgreSQL for zero-setup portability
"""

import pandas as pd
import sqlite3
from pathlib import Path

def load_data(csv_path='data/Amazon.csv', db_path='data/amazon_sales.db'):
    """
    Load CSV data into SQLite database for SQL analysis
    Returns both DataFrame and database connection
    """
    # Ensure data directory exists
    Path(db_path).parent.mkdir(exist_ok=True)
    
    print("📊 Loading Amazon Sales Data...")
    
    # Read CSV
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.lower()
    print(f"✓ Loaded {len(df):,} rows with {len(df.columns)} columns")
    
    # Create SQLite database
    conn = sqlite3.connect(db_path)
    
    # Load data into SQL
    df.to_sql('sales', conn, if_exists='replace', index=False)
    
    # Create useful views
    conn.executescript('''
        DROP VIEW IF EXISTS revenue_by_category;
        DROP VIEW IF EXISTS monthly_sales;
        DROP VIEW IF EXISTS customer_summary;
        
        CREATE VIEW revenue_by_category AS
        SELECT 
            category,
            COUNT(*) as orders,
            SUM(quantity) as items_sold,
            ROUND(SUM(totalamount), 2) as revenue,
            ROUND(AVG(totalamount), 2) as avg_order_value
        FROM sales
        GROUP BY category
        ORDER BY revenue DESC;
        
        CREATE VIEW monthly_sales AS
        SELECT 
            SUBSTR(orderdate, 1, 7) as month,
            COUNT(*) as orders,
            ROUND(SUM(totalamount), 2) as revenue,
            ROUND(AVG(totalamount), 2) as avg_order
        FROM sales
        GROUP BY month
        ORDER BY month;
        
        CREATE VIEW customer_summary AS
        SELECT 
            customerid,
            customername,
            COUNT(*) as orders,
            ROUND(SUM(totalamount), 2) as lifetime_value,
            ROUND(AVG(totalamount), 2) as avg_order,
            MIN(orderdate) as first_order,
            MAX(orderdate) as last_order
        FROM sales
        GROUP BY customerid, customername
        ORDER BY lifetime_value DESC;
    ''')
    
    conn.commit()
    print(f"✓ SQLite database created: {db_path}")
    print(f"✓ SQL views created: revenue_by_category, monthly_sales, customer_summary")
    
    return df, conn

def query(sql, conn):
    """Execute SQL query and return DataFrame"""
    return pd.read_sql_query(sql, conn)

if __name__ == "__main__":
    df, conn = load_data()
    print("\n📈 Sample Queries:")
    print("\n1. Revenue by Category:")
    print(query("SELECT * FROM revenue_by_category", conn))
    print("\n2. Top 5 Customers:")
    print(query("SELECT * FROM customer_summary LIMIT 5", conn))
    conn.close()
