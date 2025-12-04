-- Amazon Sales Database Initialization Script
-- This script runs automatically when PostgreSQL container starts for the first time

-- Create the sales transactions table
-- This mirrors the structure of your CSV file
CREATE TABLE IF NOT EXISTS sales_transactions (
    order_id VARCHAR(50) PRIMARY KEY,
    order_date DATE NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    customer_name VARCHAR(200),
    product_id VARCHAR(50) NOT NULL,
    product_name VARCHAR(500),
    category VARCHAR(100),
    brand VARCHAR(100),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0),
    discount DECIMAL(10, 2) DEFAULT 0 CHECK (discount >= 0),
    tax DECIMAL(10, 2) DEFAULT 0 CHECK (tax >= 0),
    shipping_cost DECIMAL(10, 2) DEFAULT 0 CHECK (shipping_cost >= 0),
    total_amount DECIMAL(10, 2) NOT NULL CHECK (total_amount >= 0),
    payment_method VARCHAR(50),
    order_status VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    seller_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common query patterns
-- These will speed up your SQL queries significantly

-- Index for date-based queries (time series analysis)
CREATE INDEX idx_order_date ON sales_transactions(order_date);

-- Index for customer analysis
CREATE INDEX idx_customer_id ON sales_transactions(customer_id);

-- Index for product analysis
CREATE INDEX idx_product_id ON sales_transactions(product_id);
CREATE INDEX idx_category ON sales_transactions(category);
CREATE INDEX idx_brand ON sales_transactions(brand);

-- Index for geographic analysis
CREATE INDEX idx_location ON sales_transactions(city, state, country);

-- Index for order status tracking
CREATE INDEX idx_order_status ON sales_transactions(order_status);

-- Composite index for product category and date analysis
CREATE INDEX idx_category_date ON sales_transactions(category, order_date);

-- Create a view for quick revenue analysis
-- Views are like saved queries that you can reference easily
CREATE OR REPLACE VIEW revenue_summary AS
SELECT 
    DATE_TRUNC('month', order_date) as month,
    category,
    COUNT(*) as total_orders,
    SUM(quantity) as total_items_sold,
    SUM(total_amount) as total_revenue,
    AVG(total_amount) as avg_order_value,
    SUM(discount) as total_discounts_given
FROM sales_transactions
WHERE order_status = 'Completed'
GROUP BY DATE_TRUNC('month', order_date), category
ORDER BY month DESC, total_revenue DESC;

-- Create a view for customer insights
CREATE OR REPLACE VIEW customer_insights AS
SELECT 
    customer_id,
    customer_name,
    COUNT(DISTINCT order_id) as total_orders,
    SUM(total_amount) as lifetime_value,
    AVG(total_amount) as avg_order_value,
    MIN(order_date) as first_order_date,
    MAX(order_date) as last_order_date,
    COUNT(DISTINCT category) as categories_purchased
FROM sales_transactions
GROUP BY customer_id, customer_name;

-- Create a view for product performance
CREATE OR REPLACE VIEW product_performance AS
SELECT 
    product_id,
    product_name,
    category,
    brand,
    COUNT(*) as times_ordered,
    SUM(quantity) as total_quantity_sold,
    SUM(total_amount) as total_revenue,
    AVG(unit_price) as avg_unit_price,
    AVG(discount) as avg_discount_rate
FROM sales_transactions
GROUP BY product_id, product_name, category, brand
HAVING COUNT(*) > 1  -- Only include products sold more than once
ORDER BY total_revenue DESC;

-- Grant necessary permissions
-- This ensures your Python scripts can read and write to the database
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO analyst;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO analyst;

-- Display confirmation message
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully!';
    RAISE NOTICE 'Tables created: sales_transactions';
    RAISE NOTICE 'Views created: revenue_summary, customer_insights, product_performance';
    RAISE NOTICE 'Indexes created for optimized query performance';
END $$;