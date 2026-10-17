# V2 change log

Date: 2026-10-16. Branch: `portfolio-v2`. Original `main` remains untouched.

## Root causes and fixes

| Root cause | Files / change | Contract effect |
|---|---|---|
| CSV loader, dashboard and notebook used separate paths/policies | `src/data_loader.py`, `dashboard.py`, notebook, startup scripts | One repository-root path resolution and read-only SQL query API |
| Every status counted as revenue; counts assumed row=order without checks | `sql/views.sql`, `docs/METRICS.md`, loader and dashboard | Delivered discounted merchandise revenue; all-status bookings separate; unique order grain enforced |
| Legacy source lacks provenance/license/currency and coherent identities | `docs/DATA_AUDIT.md`, `data/README.md`, `scripts/generate_demo_data.py` | Independent deterministic synthetic default; original CSV unchanged and unused in V2 |
| No meaningful automated gates and false-success health exit | `tests/`, `check.py`, CI workflow | Actual contract/AppTest/export/health tests; nonzero exit on failure |
| Fixed notebook conclusions/unsupported LTV/recovery/model claims | notebook, reporting code, English brief, README | Computed descriptive results only; no fabricated impact |
| No reviewable BI handoff | `src/reporting.py`, `bi/README.md`, `bi/measures.dax` | Checked fact/dimension CSVs and explicit unverified Desktop/DAX boundary |
| Parse/hash race and export input overwrite | loader/reporting + regression tests | Immutable source bytes; preflight protects CSV, DB and sidecar before any export write |
| Dependency drift and working-directory assumptions | requirements + lock, scripts | Verified PyArrow/NumPy combination; anchored launchers; Python 3.11 verified |

## Retained review trail

`docs/PROCESSING_TRACE.md` links each transformation to its source function, SQL, command, input/output and tests. `TASK_LIST.md` records task cards and acceptance. `docs/VERIFICATION.md` records actual results. Generated baseline brief/metrics and real browser screenshots are versioned. Generated CSV/DB/BI exports are reproducible and ignored locally; CI packages exports.

## Test changes

37 automated tests cover status-aware money/AOV/return definitions, duplicate and malformed input handling, dimension conflicts, atomic DB failure, immutable-source race, integer precision above float-safe range, parameterized filters, path resolution, calendar-spine SQL, deterministic generation/exports, star-schema join cardinality, input-overwrite protection, provenance labeling, health exits and real Streamlit app behavior.

## Risks and next steps

- No changes to live data, main branch, immigration/NOC eligibility or employment claims.
- Deliberately single-product orders, fixed customer geography, USD demonstration assumption; real multi-line/multi-currency/event-ledger ingestion requires a revised contract.
- Legacy dataset source and reuse permission remain unknown; obtain original terms before using it elsewhere.
- No repository-wide license selected or inferred.
- Windows launcher, Power BI import/DAX/interactions and PBIX remain pending; follow `bi/README.md` before claiming Power BI implementation.
- Dependencies emit 12 deprecation warnings; local dashboard and tests pass. Dependency modernization is a separate scoped change.
- Local demo has no authentication and binds to localhost. Public deployment has not been performed.

## Commit suggestion

`feat: deliver auditable retail analytics portfolio v2` — keep the coherent metric/data contract and its tests together. Follow with delivery-only documentation when remote CI/PR results are available. Website presentation belongs in its separate repository/branch/PR after this gate passes.
