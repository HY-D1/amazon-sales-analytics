# Metric contract — V2

Version: 2.0; introduced 2026-10-16. Applies to the independently generated USD demonstration, not the unverified legacy CSV. A status is a snapshot, not an event history.

| Metric | Numerator / expression | Denominator / scope |
|---|---|---|
| Orders | distinct `orderid` | all selected order-date cohort records |
| Delivered orders | distinct orders with status Delivered | same cohort |
| Delivered merchandise revenue | sum of `delivered_revenue_cents` / 100 | Delivered only; quantity × unit price × (1 − discount), rounded once per order HALF_UP |
| All-status booked order value | sum `totalamount_cents` / 100 | all statuses; includes tax/shipping; never label revenue |
| Delivered merchandise AOV | delivered merchandise revenue | delivered distinct orders; N/A when zero |
| Returned share | returned distinct orders | all distinct orders; N/A when zero |
| Completed-outcome return share | returned distinct orders | returned + delivered distinct orders; N/A when zero; excludes pending/shipped/cancelled |
| Customers | distinct customerid | all selected orders; not a person count validated against external identity |
| Observed customer spend | delivered merchandise revenue by customer | observed dataset window; not lifetime value |

## Grain, identity and money

One row represents one order containing one product. `orderid` is the unique key. Exact duplicate records are removed with a reported count; conflicting duplicates are rejected. A real multi-product order must supply explicit line IDs and documented allocation of header tax/shipping/discount before changing the grain. Do not sum repeated order totals.

Required fields, finite/nonnegative money, positive integral quantity, discount range, dates, known status and consistent customer/product identity must validate before replacing the database. Monetary calculations and storage use integer cents with decimal HALF_UP rounding; compare recorded total against merchandise + tax + shipping with at most one cent tolerance for documented source rounding. No exchange-rate conversion is inferred. Defaults and relative environment paths resolve from repository root.

Date, category and country filters select the same cohort for every dashboard chart, KPI and downloadable row. Empty category/country selections mean zero matching orders. Orders crossing categories are not supported by this contract. Category order counts therefore reconcile to total orders. Non-delivered value is neither lost revenue nor recoverable profit.

## Accounting and analytical limits

Delivered merchandise revenue is an explicit portfolio convention. Real accounting requires Finance-approved recognition and refund policies. The snapshot contains no return dates, refund amounts, costs, margins, causal experiments, churn observations or customer lifetime horizon. No forecast, recovery estimate, causal inference or real-world recommendation can be established from this synthetic dataset.
