"""
Simple Data Loader for Amazon Sales Dataset
"""

import pandas as pd
from sqlalchemy import create_engine, text
import os

def load_data():
    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        'postgresql://analyst:analytics2024@postgres:5432/amazon_sales'
    )
    
    CSV_PATH = '/app/data/Amazon.csv'
    
    try:
        print("Reading CSV...")
        df = pd.read_csv(CSV_PATH)
        
        # Convert column names to lowercase
        df.columns = df.columns.str.lower()
        
        print(f"Loaded {len(df):,} rows")
        
        # Connect and drop dependent views first
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("DROP VIEW IF EXISTS revenue_summary CASCADE"))
            conn.execute(text("DROP VIEW IF EXISTS customer_insights CASCADE"))
            conn.execute(text("DROP VIEW IF EXISTS product_performance CASCADE"))
            conn.commit()
        
        # Load data
        print("Loading into PostgreSQL...")
        df.to_sql(
            name='sales_transactions',
            con=engine,
            if_exists='replace',
            index=False,
            chunksize=5000
        )
        
        # Verify
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM sales_transactions"))
            count = result.fetchone()[0]
        
        print(f"✓ Success! Loaded {count:,} rows into database")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    load_data()