# Portfolio V2 task list

Audit/start date: 2026-10-16 (America/Vancouver). Base: `78d173f`; branch: `portfolio-v2`.
Confirmed local root: `/Users/HiMini/Desktop/HD/Extra/project/amazon-sales-analytics`.
Initial state: newly cloned into an empty confirmed directory; clean `main`; no local edits to preserve. Connected GitHub user HY-D1 has push/admin access.

## Goal and acceptance
Deliver an honest, reproducible SQL + Python + BI-ready retail analytics portfolio for Vancouver analyst roles. No employment, immigration, real Amazon performance, or Power BI Desktop implementation claims.

### TASK-1: Audit original data and analysis
- Goal: establish provenance, actual grain, duplicate/identity/amount issues.
- Input: existing CSV, code, notebooks, Git history.
- Output: `docs/DATA_AUDIT.md`.
- Acceptance: reproducible counts/hash and evidence; unknown permissions explicitly stated.
- Constraints: preserve legacy source; do not infer currency or data rights.
- Priority: P0. Dependencies: none. Complexity: M. Owner: SA-1.

### TASK-2: Canonical data and SQL metrics
- Goal: deterministic independent synthetic data; validated atomic ingestion; one SQLite metric source.
- Input: TASK-1 and existing loader.
- Output: generator, loader, SQL views, targeted tests.
- Acceptance: duplicate/conflict/malformed/empty/currency/status/path tests pass; last-good DB survives invalid inputs.
- Constraints: order grain enforced; integer cents; no implicit schema guesses.
- Priority: P0. Dependencies: TASK-1 findings. Complexity: L. Owner: SA-2.

### TASK-3: Interactive analyst dashboard
- Goal: English business dashboard with consistent filters and explicit demo limitations.
- Input: TASK-2 read-only query API.
- Output: `dashboard.py`, AppTest checks, actual screenshots.
- Acceptance: startup, filters, empty result and missing DB behavior verified.
- Constraints: SQLite only; no unsupported causal, LTV, currency or recovery claims.
- Priority: P1. Dependencies: TASK-2 contract. Complexity: M. Owner: SA-3.

### TASK-4: Reproducibility and portfolio package
- Goal: SQL + Python + documented Power BI import model; generated insights and evidence.
- Input: TASK-2/TASK-3.
- Output: report/export pipeline, notebook, BI documentation/DAX, CI, README and verification record.
- Acceptance: fresh setup, tests, report/export reconciliation, notebook execution, browser screenshots pass.
- Constraints: no fake PBIX; Windows/Desktop work explicitly unverified.
- Priority: P1. Dependencies: TASK-2/TASK-3. Complexity: L. Owner: BA.

### TASK-5: Delivery and conditional website update
- Goal: push reviewable branches/PRs; update portfolio only after project meets all gates.
- Input: TASK-4 acceptance.
- Output: project PR; website branch/PR using verified features/screenshots/links.
- Acceptance: no main overwrite; CI and website checks recorded; deployment status stated accurately.
- Constraints: protect existing local changes; no premature claims or automatic merge.
- Priority: P1. Dependencies: TASK-4 PASS. Complexity: M. Owner: BA.

## Baseline evidence
- `python3 check.py`: reported missing seaborn/plotly/streamlit but returned exit code 0 (defect).
- `python3 -m unittest discover -v`: zero tests discovered, not regression coverage.
- README says `data/amazon.db`, loader uses `data/amazon_sales.db`, dashboard bypasses both.
- Notebook embeds fixed $91.8M revenue and recovery claims without status-aware revenue policy.

## Status
TASK-1 ✅; TASK-2 ✅ (R1: immutable snapshot); TASK-3 ✅ (R1: narrow layout); TASK-4 ✅ (source labeling and export-path revisions verified). TASK-5 in progress after local acceptance gate PASS.

Integration check: all metric/source/export contracts match; 37 tests PASS; build/check/notebook/browser PASS. Power BI Desktop/DAX and Windows launcher explicitly Unverified and excluded from portfolio claims. Source trace, audit, metric contract, English results and real screenshots complete.
