# Legacy data audit and portfolio data decision

Audit date: **2026-10-16** (America/Vancouver). Scope: the tracked dataset and
analysis at baseline commit **`78d173f`**, before the portfolio-v2 changes.
These measurements describe the legacy dataset, not any replacement demo data.

## Decision

Use a deterministic, locally generated fictional commerce dataset as the default
portfolio input. Preserve this audit as the reason for the change. Do not silently
repair the old CSV by inventing customer identities, currencies or product
categories. Do not present its records as real Amazon transactions or its totals
as verified Amazon business results.

The legacy file has no established provenance or redistribution permission in the
reviewed repository. Its customer and product attributes are inconsistent, and
its currency is absent. A new generator can make the assumptions explicit and
testable while retaining the project's SQL, Python and BI learning objectives.
This decision is about demonstrable data quality; it is not a legal determination
about the legacy file.

## Provenance and permission: unverified

| Evidence | Finding |
|---|---|
| `git log --all -- data/Amazon.csv` | The file first appears in commit `f8af9a0`, dated 2025-12-04. No subsequent change to the file was found in the reviewed history. |
| Baseline `README.md`, including its initial version | Describes an Amazon sales dataset. The latest version calls it synthetic/mock and claims no real PII, but provides no original source or generator that establishes either claim. |
| Reviewed tracked files | No dataset source URL, dataset license, source attribution document or generating script was found. |
| CSV header | No currency, line identifier, extraction timestamp, refund ledger, cost or accounting recognition field. |

**Unverified:** original publisher, authenticity, collection method, consent,
whether the names are fictional, and permission to redistribute or relicense the
CSV. A public GitHub copy and a README statement are not evidence of those facts.
Resolve this with the original dataset URL, its applicable license and version,
and the original data dictionary or generating code. No external dataset was
identified by guessing from the filename.

## File identity and observed grain

All counts below were calculated directly using Python's `csv`, `hashlib`,
`collections`, `datetime` and `decimal` modules. The CSV was not modified.

| Check | Observed result |
|---|---:|
| Path at baseline | `data/Amazon.csv` |
| File size | 17,377,579 bytes |
| SHA-256 | `f8483bfbd323102179afbe9d95ffa18be47cf54daa0b0740990f8defbaf734c6` |
| Data rows / columns | 100,000 / 20 |
| Distinct `OrderID` | 100,000 |
| Duplicate complete rows / duplicate `OrderID` values | 0 / 0 |
| Empty or whitespace-only cells | 0 |
| Distinct `CustomerID` / `CustomerName` | 43,233 / 200 |
| Distinct (`CustomerID`, `CustomerName`) pairs | 99,500 |
| Distinct `ProductID` / `ProductName` | 50 / 50 |
| Distinct seller IDs | 1,999 |
| Sum of `Quantity` | 300,140 |
| Dates | 2020-01-01 through 2024-12-29 |
| Invalid ISO dates / distinct calendar months | 0 / 60 |

The **observed** grain is one unique order record containing one product ID and a
quantity of 1–5. The source supplies no line key and no multi-product orders.
`COUNT(*)` equals distinct orders only for this exact validated file; that is not
a safe contract for later order-line data. The dates are dates, not timestamps.
The README's date ending in December 2024 does not establish complete coverage
of that month or a contemporaneous status snapshot.

## Data quality and dimension consistency

| Dependency or domain check | Measured result | Consequence |
|---|---:|---|
| `CustomerID → CustomerName` | 29,643 customer IDs have more than one name | A customer dimension cannot safely use the name without an explicit repair/source rule. Baseline `customer_summary` groups by both columns and produces 99,500 customer/name groups rather than 43,233 customers. |
| `CustomerID → City / State / Country` | 28,958 / 27,655 / 18,052 IDs have multiple values | These could be order-time attributes, but no history or address semantics are supplied. Do not claim a stable customer residence. |
| `ProductID → ProductName` | 0 conflicting IDs | The 50 IDs and 50 names map one-to-one in this file. |
| `ProductID → Category / Brand` | All 50 IDs have multiple categories and multiple brands | A product-category star schema would be ambiguous. Example: `P00014` occurs in all six categories. |
| `City → State` | 0 conflicting city values | A stable city/state pair is observed within the file. |
| `City → Country` | All 20 cities occur with all five countries | Geography is unsuitable for a real market-expansion claim. The file includes the same Washington/DC pair with India and other countries. |
| Numeric fields | No negative quantities, unit prices, discounts, taxes, shipping costs or totals | This domain check passes, but does not establish business authenticity. |
| Discount | 0.00–0.30 | The baseline README's stated upper bound of 0.15 is incorrect. |
| Money precision | All unit prices, taxes, shipping costs and totals have exact cent precision | A missing currency still prevents defensible cross-country monetary aggregation. |

There are six categories, ten brands, six payment methods, five countries and
five statuses. Realistic-looking labels do not verify a real business process.

## Amount reconciliation and KPI semantics

The candidate formula was checked with exact decimal arithmetic:

```text
candidate_total = quantity × unitprice × (1 − discount) + tax + shippingcost
```

All 100,000 stored totals differ from the **unrounded** candidate by at most
0.005. Rounding the final candidate to cents with `ROUND_HALF_UP` matches 96,747
rows; the other 3,253 stored totals are 0.01 lower. `ROUND_HALF_EVEN` matches
98,755 rows, leaving 1,245 mismatches. For example, CSV line 5 / `ORD0000004`
has stored total 159.66 versus a final half-up total of 159.67. The original
rounding procedure is **unverified**. These are cent-level rounding differences,
not evidence of large missing amounts. Do not silently replace source totals.

The following are sums of the source's **unlabelled monetary units**. They are
diagnostics, not USD/CAD revenue or accounting results.

| Order status | Orders | Sum of `TotalAmount` |
|---|---:|---:|
| Delivered | 74,628 | 68,372,677.10 |
| Shipped | 15,192 | 14,083,628.99 |
| Pending | 4,103 | 3,737,556.98 |
| Returned | 3,049 | 2,780,662.46 |
| Cancelled | 3,028 | 2,851,122.39 |
| **All statuses** | **100,000** | **91,825,647.92** |

The baseline loader's three views, dashboard and notebook sum all statuses and
call the result revenue. That includes cancelled, returned and incomplete
orders, tax and shipping. There is no refund ledger or settlement information
with which to calculate actual recognized revenue, net cash or profit.

Adopt an explicit demo contract for the replacement data:

- **Orders:** distinct `order_id`, never a count of order lines. State the
  denominator and filter behavior in every rate and average.
- **Merchandise sales:** quantity × unit price, less line discounts, with a
  documented per-line cent rounding rule. Exclude tax and shipping. Restrict a
  delivered-sales KPI to `Delivered`, and call it a demo sales measure rather
  than claiming accounting revenue.
- **Delivered AOV:** delivered merchandise sales divided by distinct delivered
  orders. Multi-line orders must not inflate its denominator.
- **Return rate:** distinct returned orders divided by all distinct orders in
  the selected cohort; label it a snapshot status rate. A rate among completed
  orders is a different metric and needs a different explicit denominator.
- **Cancelled / pending / shipped:** report separately. A status is not a
  timed transition, operational delay or proof of recoverable revenue.
- **Currency:** generated demo data should declare one currency explicitly;
  do not retrospectively assume the legacy file is USD.
- **Dimensions:** stable product and synthetic customer keys; explicit fact
  grain, unique line keys and consistent order-header attributes if multi-line
  data is used. Reject duplicate/conflicting rows rather than silently dropping
  them or multiplying amounts in joins.

This is a proposed semantic contract. The implemented v2 contract and tests are
the source of truth for the replacement data and should describe any deliberate
differences.

## Notebook findings and claims that must be retired

The baseline `notebooks/amazon_sales_analysis.ipynb` has 11 code cells, all with
null execution counts and no saved outputs. Its summary and recommendations are
fixed Markdown rather than values generated by the current pipeline.

| Baseline claim | Check against this CSV |
|---|---|
| 91.8M revenue, 918 AOV, 43,233 customers | All-status total is 91,825,647.92 and mean 918.2564792; customer-ID count is correct. The revenue and currency labels remain unsupported. |
| Date range 2020-01 to 2024-12 | Month labels agree, but exact end date is 2024-12-29. |
| Top 20% of customers provide 44% of revenue | Top `ceil(43,233 × 0.2) = 8,647` customer IDs represent 43.8033% of all-status amount. This is historical observed spend, not validated lifetime value. Cell 15 uses a different off-by-one indexing convention. |
| 25% cancelled / returned / pending | Incorrect: those statuses total 10,180 orders, or 10.18%. The 25.372% not marked Delivered also includes Shipped. |
| Recover roughly 23M / resolve half the issues | No intervention, conversion or refund evidence supports recovery or an uplift estimate. Cell 18's named statuses differ from the summary's 25% cohort. |
| Texas and California are around 45% of sales | Their source amount share is 44.7519%; geography and currency issues prevent a real regional-market conclusion. |

Archived notebooks contain saved outputs, but were **not rerun during this
audit**. Their results must not be promoted as validated model performance:

- `archive/03_predictive_modeling.ipynb`, cell 4, aggregates customer order count
  and average order value over the full dataset before the random train/test
  split in cell 6. These features expose the target row and held-out history.
- Its cell 12 predicts the same-period customer total using that period's order
  count and average value. Since `total = count × mean`, high scores demonstrate
  an algebraic dependency, not future customer value prediction.
- Its cell 10 stores delivery AUC values of **0.4996** and **0.5007**, with
  accuracy **0.7463** and **0.7462**. The delivered prevalence is 74.628%, so the
  accuracy is at the majority-class baseline and does not substantiate claims
  of useful delivery-risk prediction in cell 15.
- Its cell 8 samples hypothetical future orders and predicts their amounts.
  This is a simulation without time-based forecast validation or prediction
  intervals; it is not evidence of future actual sales.
- `archive/01_exploratory_analysis.ipynb` infers market maturity from a flat
  series and promotion ineffectiveness from correlation. The data and analysis
  do not identify those causes. The source also supplies no cost/margin data
  to substantiate profit recommendations.

## Reproduce core legacy checks

This uses the immutable Git object, so it still works if the legacy CSV is
excluded from the default v2 working data. Run from the repository root:

```bash
python3 - <<'PY'
import collections, csv, datetime, decimal, hashlib, io, subprocess

raw = subprocess.check_output(['git', 'show', '78d173f:data/Amazon.csv'])
rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
D = decimal.Decimal
print('sha256:', hashlib.sha256(raw).hexdigest())
print('rows:', len(rows), 'columns:', len(rows[0]))
for key in ('OrderID', 'CustomerID', 'ProductID'):
    print('distinct', key, len({r[key] for r in rows}))
print('duplicate rows:', len(rows) - len({tuple(r.values()) for r in rows}))
print('empty cells:', sum(not v.strip() for r in rows for v in r.values()))
dates = [datetime.date.fromisoformat(r['OrderDate']) for r in rows]
print('dates:', min(dates), max(dates))
for key, attribute in [('CustomerID', 'CustomerName'),
                       ('ProductID', 'Category'), ('ProductID', 'Brand'),
                       ('City', 'Country')]:
    groups = collections.defaultdict(set)
    for r in rows:
        groups[r[key]].add(r[attribute])
    print(key, '->', attribute, 'conflicts:',
          sum(len(v) > 1 for v in groups.values()))
totals = collections.defaultdict(lambda: D(0))
statuses = collections.Counter()
rounding_mismatch = collections.Counter()
for r in rows:
    actual = D(r['TotalAmount'])
    candidate = (D(r['Quantity']) * D(r['UnitPrice']) * (1-D(r['Discount']))
                 + D(r['Tax']) + D(r['ShippingCost']))
    assert abs(actual - candidate) <= D('.005')
    for mode in (decimal.ROUND_HALF_UP, decimal.ROUND_HALF_EVEN):
        rounding_mismatch[mode] += actual != candidate.quantize(D('.01'), rounding=mode)
    totals[r['OrderStatus']] += actual
    statuses[r['OrderStatus']] += 1
print('status counts:', dict(statuses))
print('status amounts:', {k: str(v) for k, v in totals.items()})
print('all-status amount:', sum(totals.values()))
print('rounding mismatches:', dict(rounding_mismatch))
PY
```

Audit verification result: the direct CSV profiling and independent rounding
checks executed successfully on the stated date. No data-generating process,
source license, notebook rerun or real-world business performance was verified.
