# Final summary — retail analytics portfolio V2

Date: 2026-10-16 (America/Vancouver).

## Request and delivery

Develop the existing Amazon Sales Analytics project into an honest SQL + Python + BI-ready job portfolio, retain all processing source for owner review, verify metrics/runtime/tests, and update the personal-site showcase only after acceptance.

| Task | Status | Revisions / evidence |
|---|---|---|
| TASK-1: Source/grain audit | PASS | Original CSV unchanged; provenance/currency/license unverified; dimension conflicts demonstrated |
| TASK-2: Data + SQL pipeline | PASS | Immutable source snapshot; duplicate/conflict validation; atomic DB publish; 15 targeted tests |
| TASK-3: Streamlit dashboard | PASS | Shared SQL filters; 8 AppTests; desktop/narrow real-browser checks; responsive revision |
| TASK-4: Reviewable portfolio package | PASS | Generator, SQL, notebook, report/export code, metric contract, source trace, 13 export tests + health test; 37 total PASS locally and CI |
| TASK-5: Branch/PR + conditional website entry | PASS for reviewable delivery | Analytics PR #1 and website PR #6; website 17 checks PASS; neither main branch merged or deployed |
| Git identity audit/correction | PASS | Hanyu Dai author/committer linked to HY-D1; wrong global/local default removed; single implementation commit reauthored with identical tree and exact-head lease |

## Deliverables

- [Analytics PR #1](https://github.com/HY-D1/amazon-sales-analytics/pull/1).
- [Website PR #6](https://github.com/HY-D1/HY-D1.github.io/pull/6).
- `docs/PROCESSING_TRACE.md`: every retained Python/SQL step, inputs, outputs, commands and validation policy.
- `docs/DATA_AUDIT.md`: reproducible source evidence; `data/README.md`: source/grain contract.
- `src/data_loader.py`, `sql/`, `scripts/generate_demo_data.py`: canonical data and metrics.
- `dashboard.py`, notebook, actual screenshots and generated English brief/metrics.
- `src/reporting.py`, `bi/README.md`, `bi/measures.dax`: checked five-table BI export and explicit Windows validation boundary.
- `tests/`, `docs/VERIFICATION.md`, `docs/CHANGELOG.md`, `docs/GIT_IDENTITY_AUDIT.md` and CI: evidence and recovery trail.

## Key decisions

1. Use independently generated synthetic data by default because the inherited data's source/license/currency and stable identities could not be established.
2. Enforce one order/one product per row and reject conflicting order IDs because no line ID/allocation contract exists.
3. Count only Delivered discounted merchandise as the named descriptive revenue metric; keep tax/shipping/all-status bookings separate.
4. Provide verified BI-ready CSVs, relationships and draft DAX instead of a fabricated PBIX. Power BI Desktop is not available in this macOS workflow.
5. Keep all processing code in Git; generated bulk CSV/DB/exports are reproducible and available locally/through CI artifacts.
6. Present only verified capabilities on an isolated website branch. Public main/deployment remain unchanged for review.

## Actual verification

- Local: 37 tests PASS (12 dependency deprecation warnings); setup/build/check/pip-check/shell syntax/whitespace PASS.
- Notebook: 7 executed code cells, zero error outputs.
- Clean GitHub Ubuntu/Python 3.11 CI: 37 tests PASS, pipeline/export/health/notebook PASS, validated-analysis artifact uploaded. Exact run links in `docs/VERIFICATION.md`.
- Website: 17 tests PASS, syntax/whitespace PASS; browser showed 8 projects, loaded actual screenshot and no overflow at checked 1280px width.
- Default synthetic figures: 2,400 orders; delivered merchandise USD 122,406.60; bookings USD 188,272.90; delivered AOV USD 71.96; returned share 9.50%. These are demonstration arithmetic, not real Amazon performance.

## Remaining limits

- Power BI Desktop import, DAX execution, visual interactions, PBIX and Windows launcher remain unverified. Complete `bi/README.md` on supported Windows before claiming implemented Power BI reporting.
- Legacy dataset provenance/license/currency remain unverified and excluded from V2 output. No general repository license selected.
- No public Streamlit deployment or Pages update performed. Review/merge the two PRs through normal workflow; confirm Pages after merge.
- Full mobile/assistive-technology audit of the new website entry and dependency modernization remain separate work.
