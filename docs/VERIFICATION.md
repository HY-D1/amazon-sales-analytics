# Verification record

Date: 2026-10-16 (America/Vancouver). Local platform: macOS arm64, Python 3.11. Environment packages recorded in `requirements-lock.txt`. Baseline commit: `78d173f`; working branch: `portfolio-v2`.

## Actual checks and outcomes

| Command / check | Observed result |
|---|---|
| Baseline `python3 check.py` | Reported missing packages but returned 0: incorrect failure signaling |
| Baseline `python3 -m unittest discover -v` | 0 tests; no regression coverage |
| Baseline targeted loader contracts | Failed before implementation (17 failures + 7 errors across 10 initial cases) |
| `./start.sh build` | PASS: generated 2,400 independent orders, loaded SQLite, exported 5 BI tables and analytical brief |
| `.venv/bin/python -m pytest -q` | PASS: 37 tests; 12 third-party matplotlib/pyparsing deprecation warnings; 8.21s in final recorded integration run |
| `.venv/bin/python -m pytest -q tests/test_reporting.py` | PASS: 13 tests, including five previously failing input-overwrite scenarios |
| `./start.sh check` | PASS: DB integrity, nonempty canonical orders and recorded-source hash matched |
| `.venv/bin/python -m pip check` | PASS: No broken requirements found after PyArrow compatibility pin |
| `.venv/bin/python -m jupyter nbconvert --to notebook --execute notebooks/amazon_sales_analysis.ipynb --output /tmp/amazon-portfolio-v2-executed.ipynb --ExecutePreprocessor.timeout=120` | PASS: 7 code cells executed, 0 error outputs; exported executed notebook to temporary path |
| `bash -n start.sh` | PASS |
| `git diff --check` | PASS |
| Streamlit startup via `./start.sh dashboard` | PASS: server bound to 127.0.0.1:8501 |
| Browser desktop view | PASS: five complete KPI values, actual charts and order explorer; captured `docs/screenshots/dashboard-overview.png` and `dashboard-explorer.png` |
| Browser narrow view (661px) | Initial truncation reproduced, responsive layout revised; PASS: full amount/label visible; captured `dashboard-narrow.png` |
| Browser console warning/error log | Empty list in final inspection |
| Streamlit AppTest | 8 passing cases included in full suite: startup/provenance, date/category/country filters, chart values, empty selection, incomplete dates, exported fields, missing/stale DB without writes |

The notebook run emitted a Jupyter local-kernel transport warning. It did not fail or create error outputs. This is not evidence of public notebook deployment; the dashboard remains local-only. Matplotlib's 12 deprecation warnings are dependency warnings, not silent test failures.

## Independently reconciled baseline

Source SHA-256: `deee0411148e466553a3b5e5412a12b0b93b2e2f66863baccfa9a57aed6cf4ef`.

- 2,400 unique orders; 1,701 Delivered; 228 Returned; 180 customer IDs.
- Delivered merchandise: **12,240,660 integer cents (USD 122,406.60)**.
- All-status bookings: **18,827,290 integer cents (USD 188,272.90)**.
- Delivered AOV: 12,240,660 / 1,701 cents, displayed USD 71.96.
- Returned share: 228 / 2,400 = 9.50%.
- BI FactOrders counts and revenue reconcile to SQL. Tests also use a separate hand-built ledger and independent Decimal calculations; they do not rely only on the demo constants.

## Root-cause revisions verified

1. Snapshot race: source mutation between parse and hash first failed a dedicated test. One immutable byte snapshot now feeds both validation and SHA. Last-good DB protection is retained.
2. Export overwrite: output paths could overwrite source/DB/sidecar (including symlinks). Five cases failed before path preflight and passed after it; no output is written when inputs would be overwritten.
3. Source labeling: custom CSV initially received a false independently-generated header. A failing provenance test prompted metadata-aware report/UI labels.
4. Dependency drift: automatically resolved PyArrow required a newer NumPy; the explicit PyArrow 17 pin restored import/runtime compatibility.
5. Health check source identity: the check now verifies the imported source recorded in metadata, including CLI custom input, and returns 1 when that source changes or disappears.

## Acceptance and remaining boundary

The SQL + Python + Streamlit + BI-ready data-model demonstration meets its local portfolio gate: successful run, validated metrics, passing tests, English interpretation, real screenshots, retained processing source and reproducible steps. It may be represented on the personal portfolio with those exact claims.

Power BI Desktop, Power Query import, draft DAX and visual cross-filtering are **Unverified** on Windows; no PBIX exists. The Windows launcher is also unverified. No live public Streamlit deployment is claimed. Source/license/currency of the legacy CSV remain unverified and are excluded from V2 results.

GitHub CI and pull-request URLs are recorded in delivery notes after remote checks complete. A CI configuration by itself is not a successful CI result.

## Remote clean-environment CI evidence

Implementation head: `2a29a94db5a1edd6755852eeaf79979685e62a0d`.

- [PR workflow run 39004482247](https://github.com/HY-D1/amazon-sales-analytics/actions/runs/39004482247): **SUCCESS**, completed 2026-10-16 21:58 PDT. Ubuntu/Python 3.11 installed from requirements, generated data, built SQLite/exports, checked dependencies/source hash, ran **37 passed, 12 warnings in 4.98s**, executed the notebook, and uploaded `validated-analysis` (artifact ID 12090436250).
- [Branch workflow run 39004461605](https://github.com/HY-D1/amazon-sales-analytics/actions/runs/39004461605): **SUCCESS** for the same implementation commit.
- Both runs were inspected with `gh run view`; the PR log confirmed five exported tables, fact/SQL reconciliation, 37 passing tests and the executed notebook artifact.
- Project PR: https://github.com/HY-D1/amazon-sales-analytics/pull/1. Open and mergeable; not merged. `origin/main` remains baseline `78d173fff0f87a4f891fc88d258e6ca523d62b85`.

The committed processing code and the complete local/remote checks satisfy the gate for a factual personal-website project entry. A website branch/PR does not itself constitute a live Pages deployment.

## Identity and screenshot corrections

The owner requested removal of the incorrect inherited Git author. Implementation commit `2a29a94` was replaced by `7b96a39` with the identical tree; GitHub confirms author and committer now associate with HY-D1. See `docs/GIT_IDENTITY_AUDIT.md`.

Screenshot-format verification found the capture API had returned JPEG bytes under `.png` filenames. Actual captures were re-encoded without visual edits using the retained `scripts/normalize_screenshots.sh` helper. File signatures now match PNG; final overview and analysis captures are 1280×720, explorer capture 1602×798, and narrow capture 661×865. Website tests verify the actual screenshot format and dimensions.
