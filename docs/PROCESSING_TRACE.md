# Processing trace — review the work, step by step

This file maps every displayed number back to retained Python/SQL source. No opaque one-off cleaning, manual spreadsheet edits, hidden API calls or undocumented data transformations feed the V2 demo.

## Review order

| Step | Source to review | Command | Input → output | What changes / what is checked |
|---|---|---|---|---|
| 0. Audit legacy data | `docs/DATA_AUDIT.md` (includes executable reproduction block) | run the documented read-only audit | immutable baseline Git blob of `data/Amazon.csv` → counts, hash, conflict evidence | No legacy records modified; provenance/currency/permission remain unverified |
| 1. Create independent demo | `scripts/generate_demo_data.py` → `generate` | `python scripts/generate_demo_data.py` | seed 42 + explicit constants → `data/demo_sales.csv` + `.metadata.json` | 2,400 orders, invented IDs/labels, dates 2024–2025, assumed USD; standard-library RNG + Decimal HALF_UP |
| 2. Normalize and validate | `src/data_loader.py` → `_validate` | part of `python -m src.data_loader` | demo CSV → canonical DataFrame | Trim header/values, lowercase headers, require exact 20-field schema, remove exact duplicates and count them, reject conflicting order IDs/dimensions, validate dates/status/numerics/total formula |
| 3. Preserve money semantics | `src/data_loader.py` → `_decimal`, `_cents`, `_validate` | same command | decimal source fields → integer cents and delivered revenue column | Merchandise is rounded per order; only Delivered contributes delivered revenue; tax/shipping retained separately; invalid/nonfinite/negative/overflow values fail |
| 4. Publish canonical store | `src/data_loader.py` → `load_data`, `_source_metadata`, `_create_views`; `sql/views.sql` | `python -m src.data_loader` | canonical rows → temporary DB → atomic `data/amazon_sales.db` | Build/index/integrity check before replacement; last-good DB survives failed validation/SQL build; metadata includes source SHA, grain, schema and quality counts |
| 5. Calculate metrics | `sql/views.sql`; `src/data_loader.py` → `get_dashboard_data` | loader CLI prints full baseline | SQLite sales → KPI/category/month/status/payment/customer queries | One metric policy; integer sums; zero denominator is null; inclusive dates and parameterized category/country filters |
| 6. Explore deeper SQL | `sql/analyst_queries.sql` | run SELECT statements against built DB | canonical SQLite → monthly LAG, category DENSE_RANK/share, reconciliation | Calendar spine inserts missing months; guards division by zero; no forecast/causal claims |
| 7. Render dashboard | `dashboard.py` → `main`, `render_overview`, `render_explorer`, `render_definitions` | `python -m streamlit run dashboard.py` | read-only SQL API → English charts/KPI/selected CSV | Every visible output uses same selected cohort; definitions, source metadata and rebuild instructions are exposed |
| 8. Export BI model | `src/reporting.py` → `build_star`, `export` | `python -m src.reporting` | SQL canonical rows → `bi/exports/FactOrders.csv` + 4 Dim tables + manifest | Unique dimensions, matching foreign keys, many-to-one joins, one row/order; exported fact reconciles to SQL counts and cents; file hashes retained |
| 9. Write analytical brief | `src/reporting.py` → `write_report` | same export command | SQL query results → `reports/business_insights.md`, `reports/metrics.json` | All descriptive values generated; source type preserved; no invented recovery, profit, model accuracy or LTV |
| 10. Review notebook | `notebooks/amazon_sales_analysis.ipynb` | `python -m jupyter nbconvert --to notebook --execute notebooks/amazon_sales_analysis.ipynb --output /tmp/portfolio-executed.ipynb` | same built DB → executed analysis | No second CSV loader or fixed executive summary; assertions reconcile selected rows to SQL |
| 11. Validate Windows BI | `bi/README.md`, `bi/measures.dax` | import into supported Power BI Desktop | validated CSV model → future real PBIX | **Not executed on this Mac**. Draft DAX/relationships/layout are reviewable; no PBIX or Power BI screenshot claimed |

## Exact V2 transformation policy

- No imputation of missing fields, silent row dropping, currency conversion or reassignment of inconsistent IDs.
- Exact duplicate rows after whitespace normalization are removed with an explicit count. Conflicting order IDs reject the whole input; there is no line identifier to disambiguate multiple products or repeated header totals.
- Rejected inputs do not create a partial dataset or replace the last-good database. Error messages identify the rule and logical row number. This is fail-closed ingestion, not a repair of questionable source values.
- Source dates are ISO strings. They describe the order cohort only. A Returned status is not a return timestamp.
- Monetary source precision is limited to two decimal places. Discounted merchandise uses Decimal HALF_UP once per order; integer cents are used for totals. The source total check tolerates one cent of rounding difference and preserves the supplied booked total.
- The deliberately fixed customer dimension rejects differing customer name/geography for the same ID. Real address changes require a revised production model; no such history is guessed.
- `customer_summary.observed_spend_cents` means delivered spend in the observed window, not lifetime value.

## Re-run everything locally

```bash
./start.sh setup
./start.sh build
./start.sh test
./start.sh check
./start.sh dashboard
```

Use Python 3.11 (the verified version). `requirements.txt` pins direct dependencies; `requirements-lock.txt` records the exact verified environment including transitive dependencies. Install the lock for a matching environment with `python -m pip install -r requirements-lock.txt`.

All relative data paths resolve from repository root. Explicit CLI `--csv`/`--db` override `DATA_PATH`/`DB_PATH`; defaults are `data/demo_sales.csv` and `data/amazon_sales.db`. The dashboard reads an imported snapshot and does not change it. After changing a CSV, rerun ingestion. `check.py` rejects a source hash that differs from the imported snapshot.

## What is versioned and what is generated

- Versioned: every processing `.py`, executable `.sql`, notebook source, tests, metrics contract, processing trace, audit reproduction, generated baseline brief/metrics, actual screenshots, CI configuration and verification notes.
- Regenerable and ignored: demo CSV/manifest, local SQLite database, BI export CSVs/manifest, environment and test cache. CI uploads the validated reports and BI exports as an artifact. No raw legacy personal-looking names are shown in screenshots or reports.
- Original `data/Amazon.csv` and `archive/` remain untouched. Their inherited availability does not establish permission to reuse the legacy dataset. Old notebook predictions/recommendations are historical, unverified and excluded from current portfolio claims.

## Tests and evidence

- `tests/test_data_pipeline.py`: independent small ledger; all five statuses; duplicate prevention; malformed and conflicting inputs; atomic failure protection; read-only DB; integer precision; paths; filtered SQL/view reconciliation; generator reproducibility; calendar-spine SQL.
- `tests/test_reporting.py`: separate expected ledger and Decimal arithmetic; export totals/AOV/return denominators; dimension keys and join cardinality; deterministic bytes/hash; empty/no-delivery cases; source labeling and no published machine paths.
- `tests/test_dashboard.py`: real Streamlit AppTest startup, filters, no-data/incomplete dates, chart specs, exports, missing/stale DB and provenance notice.
- `docs/VERIFICATION.md`: commands actually run, observed outcomes and limitations. `docs/CHANGELOG.md`: root causes, changed contracts/files, revisions and remaining work.

The generated manifest ties each BI CSV to its SHA-256 and expected SQL KPIs. The database metadata ties canonical rows to the input hash. Regenerating a file changes no checked-in business claim automatically: review the new report/metrics diff and update screenshots when deliberately changing the demo seed or generator.
