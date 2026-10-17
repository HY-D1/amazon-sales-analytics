# Data provenance and quality contract

## Default demo: independently generated, single-currency practice data

`python scripts/generate_demo_data.py` creates `demo_sales.csv` and a SHA-256
manifest, using only Python's standard library and seed 42. It imports no external
records. Customers, sellers, products, cities, regions, and markets are invented
labels; no real customer names or contact details are used. The default is 2,400
orders dated 2024-01-01 through 2025-12-31, with **USD explicitly assumed** for all
amounts. Dates/statuses/discounts are generated for practice; apparent patterns
are consequences of this simulation and cannot establish actual market behavior.

The generator and generated CSV are original additions for this demonstration;
they do not redistribute third-party Amazon data. No repository license file was
present during this audit; public availability does not establish a general license.
The project name does not imply affiliation with, or access to, Amazon.

## Legacy `Amazon.csv`: quarantined from the published demonstration

The original repository contains `Amazon.csv` (100,000 source rows). No verified
original publisher URL, dataset version, currency definition, or redistribution
license has been supplied. Its source and license remain **unverified**. It is
retained untouched for audit history and is **not** the default input, exported
BI data, dashboard screenshot source, or evidence of real business performance.
Do not represent its personal-looking names as verified fictional individuals.
A README assertion that a dataset is synthetic does not resolve provenance or
redistribution permission. Obtain the original source and terms before use.

## Grain, validation, and metrics

- One unique `OrderID` represents one order containing one product. This fixture
  is deliberately simpler than a real order-line ledger. There is no line ID.
- All 20 source columns are required and nonempty. Dates must be ISO calendar
  dates. Quantity is a positive integer. Numeric inputs must be finite and
  nonnegative, discount must be in [0, 1], and input money has at most two decimal
  places. Status is Delivered, Returned, Cancelled, Pending, or Shipped.
- Exact duplicate records (after trimming surrounding whitespace) are removed
  and counted. Conflicting repeated order IDs cause the import to fail; they
  are never assumed to be order lines and never silently summed.
- A product ID must have consistent name, category, and brand. In this deliberately
  fixed-dimension demo a customer ID must have consistent name and geography.
  Conflicts fail the import. Real customers can move or have multiple addresses;
  a production ledger would need address keys or a time-varying dimension.
- Discounted merchandise = quantity × unit price × (1 − discount), rounded once
  to cents using decimal **ROUND_HALF_UP**. Source total must equal rounded
  merchandise + tax + shipping within one cent. All metric money is stored
  and summed as integer cents, with USD as a demo assumption.
- **Delivered merchandise revenue** sums discounted merchandise for Delivered
  orders only; it excludes tax, shipping and all other statuses. This descriptive
  status-snapshot metric is not GAAP/IFRS recognized revenue or realized cash.
- **Booked order total** sums source `TotalAmount` across every status, including
  Returned/Cancelled/Pending/Shipped; it is not revenue or cash collected.
- **Delivered AOV** = delivered merchandise revenue ÷ Delivered order count.
- **Returned share** = Returned orders ÷ all unique orders.
- **Completed-order return ratio** = Returned ÷ (Returned + Delivered). With no
  order/return event history or cohort maturity, this is not a return probability.
- Counts and monetary sums for an empty selection are zero. AOV/rates with a
  zero denominator are null (shown as not available), not a misleading 0%.

## Reproducibility and paths

`DATA_PATH` and `DB_PATH` override the default `data/demo_sales.csv` and
`data/amazon_sales.db`. Relative paths always resolve from the repository root,
regardless of the working directory. CLI `--csv`/`--db` override environment
variables. A successful import builds a temporary SQLite file and atomically
replaces the target; any failed validation or SQL build preserves the last good
file. Dashboard connections use SQLite read-only mode and never import CSV data.
Metadata records the source path, SHA-256, schema version, quality counts, date
range, currency assumption and verified matching generator-manifest status.
The CSV is read once into an immutable byte snapshot; parsing and SHA-256 use
those same bytes. A concurrent source/manifest change cannot label old imported
rows with the replacement file's hash or provenance.
