---
phase: 05-output-excel-export
plan: 03
subsystem: output
tags: [openpyxl, excel, writer, pipeline-api, integration-tests]

# Dependency graph
requires:
  - phase: 05-02
    provides: pipeline/writer.py with write_workbook(), write_workbook already in pipeline/__init__.py
  - phase: 04-field-extraction-cms-1500-ub-04
    provides: FieldResult dataclass, CMS1500_FIELDS/TABLE_FIELDS, UB04_FIELDS/TABLE_FIELDS
provides:
  - All 12 Phase 5 tests passing (0 skipped)
  - write_workbook confirmed in pipeline public API (__all__ and importable)
  - Integration tests for text-format NPI/date columns and one-row-per-page verified
affects: [06-desktop-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Header lookup in tests uses fd.label or fd.name (not field_name) — matches D-01 writer convention"
    - "Table column header format: '{tfd.label or tfd.name} SL{N}' — matches D-02 writer convention"

key-files:
  created: []
  modified:
    - tests/test_phase5.py

key-decisions:
  - "Task 1 already complete: pipeline/__init__.py had write_workbook added by 05-02-PLAN (Rule 3 deviation) — verified and confirmed, no changes needed"
  - "Rule 1 fix: test_text_format_npi_column header lookup changed from field_name 'box17b_referring_npi' to label 'Box 17b — Referring NPI' to match writer's D-01 header convention"
  - "Rule 1 fix: test_text_format_date_column header lookup changed from field_name 'box24_date_from_sl1' to constructed label 'Box 24 — Date From SL1' to match writer's D-02 table header convention"

requirements-completed: [OUT-01, OUT-02, OUT-03, OUT-04, OUT-05]

# Metrics
duration: 15min
completed: 2026-05-06
---

# Phase 5 Plan 03: Pipeline Export Wiring and Integration Test Activation Summary

**All 12 Phase 5 stubs activated; write_workbook confirmed in pipeline public API; header lookup bugs fixed in text-format integration tests**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-05-06T19:55:00Z
- **Completed:** 2026-05-06T20:09:47Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Verified write_workbook is already exported from pipeline.__init__.py (Task 1 complete from 05-02 deviation)
- Activated all 4 remaining integration stubs in tests/test_phase5.py:
  - test_import_write_workbook_from_pipeline — simple callable check
  - test_text_format_npi_column — confirms '@' format on NPI column
  - test_text_format_date_column — confirms '@' format on date column
  - test_cms1500_one_row_per_page — confirms 2 pages -> max_row == 3
- Fixed header lookup bugs in NPI and date tests (see Deviations)
- All 12 Phase 5 tests pass with 0 skipped
- Phase 6 can call `write_workbook(cms_pages, ub_pages, settings)` without further wiring

## Task Commits

Each task committed atomically:

1. **Task 1: Add write_workbook to pipeline/__init__.py** — Already complete (05-02 Rule 3 deviation). No commit needed; verified with `python -c "from pipeline import write_workbook; assert callable(write_workbook)"`.

2. **Task 2: Activate 4 remaining integration stubs** — `c0de389` (test)

## Files Created/Modified

- `tests/test_phase5.py` — Removed 4 @pytest.mark.skip decorators; fixed header lookups in NPI/date tests; updated docstring to show all 12 stubs activated

## Decisions Made

- Task 1 required no code changes — write_workbook was already in pipeline/__init__.py from 05-02's Rule 3 deviation. Verification only.
- Header lookups in integration tests must use `fd.label or fd.name` (not `fd.name`) because the writer follows D-01 which uses labels as column headers.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed header lookup in test_text_format_npi_column**
- **Found during:** Task 2 (analyzing stub body before removing skip marker)
- **Issue:** Stub used `header_row.index("box17b_referring_npi")` to locate the NPI column, but the writer uses `fd.label or fd.name` for headers (D-01). The actual column header is `"Box 17b — Referring NPI"`, not the raw field name. Running the test without the fix would raise `ValueError: 'box17b_referring_npi' is not in list`.
- **Fix:** Added lookup `npi_label = next(fd.label or fd.name for fd in CMS1500_FIELDS if fd.name == "box17b_referring_npi")` and changed `header_row.index("box17b_referring_npi")` to `header_row.index(npi_label)`.
- **Files modified:** tests/test_phase5.py
- **Verification:** test_text_format_npi_column PASSED
- **Committed in:** c0de389

**2. [Rule 1 - Bug] Fixed header lookup in test_text_format_date_column**
- **Found during:** Task 2 (analyzing stub body before removing skip marker)
- **Issue:** Stub used `header_row.index("box24_date_from_sl1")` to locate the date column, but the writer generates table column headers as `f"{tfd.label or tfd.name} SL{i+1}"` (D-02/D-04). The actual column header is `"Box 24 — Date From SL1"`, not the raw field name. Running the test without the fix would raise `ValueError: 'box24_date_from_sl1' is not in list`.
- **Fix:** Added lookup `date_tfd = next(tfd for tfd in CMS1500_TABLE_FIELDS if tfd.name == "box24_date_from")` and `date_sl1_header = f"{date_tfd.label or date_tfd.name} SL1"`, then changed `header_row.index("box24_date_from_sl1")` to `header_row.index(date_sl1_header)`.
- **Files modified:** tests/test_phase5.py
- **Verification:** test_text_format_date_column PASSED
- **Committed in:** c0de389

---

**Total deviations:** 2 auto-fixed (Rule 1 bugs) + 1 non-deviation (Task 1 already done)
**Impact on plan:** Bug fixes were necessary for the integration tests to pass. Task 1 being pre-done by 05-02 is a harmless acceleration.

## Issues Encountered

Pre-existing worktree environment failures (out of scope, identical to 05-01 and 05-02 reports):
- 9 tests in test_phase2.py fail (Poppler unable to open worktree test.pdf)
- 2 errors in test_phase3.py (test.pdf fixture not found in worktree)
- 4 tests in test_phase4.py still skipped (Phase 4 integration stubs, unrelated to this plan)

These failures are environmental and identical to those documented in 05-01-SUMMARY.md and 05-02-SUMMARY.md. They do not affect the Phase 5 deliverables.

## Known Stubs

None. All 12 Phase 5 tests are active and passing. No stubs remain in tests/test_phase5.py.

## Threat Flags

None. No new network endpoints, auth paths, file access patterns, or schema changes introduced. Tests run in isolated tmp_path per pytest invocation (accepted per T-05-07).

## Self-Check

- [x] pipeline/__init__.py contains `from .writer import write_workbook` (verified: `python -c "from pipeline import write_workbook; assert callable(write_workbook)"` exits 0)
- [x] pipeline.__all__ contains `"write_workbook"` (verified: `python -c "import pipeline; assert 'write_workbook' in pipeline.__all__"` exits 0)
- [x] All 5 prior exports still present (verified)
- [x] tests/test_phase5.py contains zero @pytest.mark.skip decorators (grep -c returns 0)
- [x] All 12 Phase 5 tests PASSED (pytest tests/test_phase5.py -v: 12 passed, 0 skipped)
- [x] Commit c0de389 exists (Task 2)
- [x] No accidental file deletions (git diff --diff-filter=D HEAD~1 HEAD: empty)

## Self-Check: PASSED

---
*Phase: 05-output-excel-export*
*Completed: 2026-05-06*
