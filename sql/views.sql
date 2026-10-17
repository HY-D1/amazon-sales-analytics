-- Schema version 2. All currency amounts below are integer USD cents.
-- Grain: one unique orderid, one product per order; there is no order-line ID.
-- Delivered merchandise revenue is a descriptive snapshot, not accounting revenue:
-- discounted merchandise only; Returned/Cancelled/Pending/Shipped and tax/freight excluded.
CREATE VIEW kpi_summary AS
SELECT COUNT(*) AS total_orders,
       COALESCE(SUM(orderstatus = 'Delivered'), 0) AS delivered_orders,
       COALESCE(SUM(orderstatus = 'Returned'), 0) AS returned_orders,
       COUNT(DISTINCT customerid) AS unique_customers,
       COALESCE(SUM(delivered_revenue_cents), 0) AS delivered_revenue_cents,
       COALESCE(SUM(totalamount_cents), 0) AS booked_total_cents,
       1.0 * SUM(delivered_revenue_cents) / NULLIF(SUM(orderstatus = 'Delivered'), 0) AS delivered_aov_cents,
       1.0 * SUM(orderstatus = 'Returned') / NULLIF(COUNT(*), 0) AS returned_share,
       1.0 * SUM(orderstatus = 'Returned') / NULLIF(SUM(orderstatus IN ('Returned', 'Delivered')), 0) AS completed_return_rate,
       1.0 * SUM(orderstatus = 'Delivered') / NULLIF(COUNT(*), 0) AS delivered_share
FROM sales;

CREATE VIEW revenue_by_category AS
SELECT category, COUNT(*) AS orders,
       SUM(orderstatus = 'Delivered') AS delivered_orders,
       SUM(CASE WHEN orderstatus = 'Delivered' THEN quantity ELSE 0 END) AS items_sold,
       SUM(delivered_revenue_cents) AS delivered_revenue_cents,
       SUM(totalamount_cents) AS booked_total_cents,
       1.0 * SUM(delivered_revenue_cents) / NULLIF(SUM(orderstatus = 'Delivered'), 0) AS delivered_aov_cents
FROM sales GROUP BY category;

CREATE VIEW monthly_sales AS
SELECT SUBSTR(orderdate, 1, 7) AS month, COUNT(*) AS orders,
       SUM(orderstatus = 'Delivered') AS delivered_orders,
       SUM(CASE WHEN orderstatus = 'Delivered' THEN quantity ELSE 0 END) AS items_sold,
       SUM(delivered_revenue_cents) AS delivered_revenue_cents,
       SUM(totalamount_cents) AS booked_total_cents,
       1.0 * SUM(delivered_revenue_cents) / NULLIF(SUM(orderstatus = 'Delivered'), 0) AS delivered_aov_cents
FROM sales GROUP BY month;

CREATE VIEW customer_summary AS
SELECT customerid, customername, COUNT(*) AS orders,
       SUM(orderstatus = 'Delivered') AS delivered_orders,
       SUM(delivered_revenue_cents) AS observed_spend_cents,
       MIN(orderdate) AS first_order, MAX(orderdate) AS last_order
FROM sales GROUP BY customerid, customername;
