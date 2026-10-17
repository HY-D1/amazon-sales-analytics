-- Run against the schema-v2 database. Amounts remain integer USD cents.
-- Every result is a synthetic practice scenario, not evidence about Amazon.

-- 1. Calendar-complete monthly revenue and MoM. A date spine inserts zero-order
-- months so LAG compares adjacent calendar months rather than adjacent observed months.
WITH RECURSIVE
bounds AS (
    SELECT date(MIN(orderdate), 'start of month') AS first_month,
           date(MAX(orderdate), 'start of month') AS last_month FROM sales
),
months(month_start) AS (
    SELECT first_month FROM bounds WHERE first_month IS NOT NULL
    UNION ALL
    SELECT date(month_start, '+1 month') FROM months, bounds
    WHERE month_start < last_month
),
monthly AS (
    SELECT strftime('%Y-%m', month_start) AS month,
           COALESCE(delivered_revenue_cents, 0) AS delivered_revenue_cents,
           COALESCE(delivered_orders, 0) AS delivered_orders
    FROM months LEFT JOIN monthly_sales ON monthly_sales.month = strftime('%Y-%m', month_start)
),
comparison AS (
    SELECT *, LAG(delivered_revenue_cents) OVER (ORDER BY month) AS previous_month_cents
    FROM monthly
)
SELECT *, delivered_revenue_cents - previous_month_cents AS revenue_change_cents,
       1.0 * (delivered_revenue_cents - previous_month_cents)
           / NULLIF(previous_month_cents, 0) AS revenue_mom_rate
FROM comparison ORDER BY month;

-- 2. Category revenue rank/share plus a return diagnostic. Return share uses all
-- observed orders. It is a snapshot ratio, not a mature-cohort return probability.
WITH category_metrics AS (
    SELECT category, COUNT(*) AS orders,
           SUM(orderstatus = 'Returned') AS returned_orders,
           SUM(delivered_revenue_cents) AS delivered_revenue_cents
    FROM sales GROUP BY category
)
SELECT *, DENSE_RANK() OVER (ORDER BY delivered_revenue_cents DESC) AS revenue_rank,
       1.0 * delivered_revenue_cents / NULLIF(SUM(delivered_revenue_cents) OVER (), 0) AS revenue_share,
       1.0 * returned_orders / NULLIF(orders, 0) AS returned_share
FROM category_metrics ORDER BY revenue_rank, category;

-- 3. Exact reconciliation: category and monthly revenue must equal headline KPI.
SELECT (SELECT delivered_revenue_cents FROM kpi_summary) AS headline_cents,
       COALESCE((SELECT SUM(delivered_revenue_cents) FROM revenue_by_category), 0) AS category_cents,
       COALESCE((SELECT SUM(delivered_revenue_cents) FROM monthly_sales), 0) AS monthly_cents;
