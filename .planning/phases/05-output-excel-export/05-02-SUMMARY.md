---
phase: 05-output-excel-export
plan: 02
subsystem: output
tags: [openpyxl, excel, writer, field-extraction, cms1500, ub04]

# Dependency graph
requires:
  - phase: 04-field-extraction-cms-1500-ub-04
    provides: FieldResult dataclass, extract_cms1500 (89 fields), extract_ub04 (178 fields)
  - phase: 05-01
    provides: tests/test_phase5.py with 12 @pytest.mark.skip stubs
provides:
  - pipeline/writer.py with write_workbook() implementing D-01 through D-10
  - 89-column CMS-1500 sheet and 178-column UB-04 sheet with labels, freeze_panes, yellow fill, text format
  - write_workbook exported from pipeline/__init__.py
  - 8 unit tests activated (8 passed, 4 integration stubs remain skipped for 05-03)
affects: [05-03-output-pipeline-export, 06-desktop-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "write_workbook(cms_pages, ub_pages, settings) -> str: stateless function following extractor pattern"
    - "Header labels via fd.label or fd.name fallback (D-01/D-04)"
    - "Text-format substring matching via _TEXT_FORMAT_SUBSTRINGS set (_needs_text_format)"
    - "Yellow fill via _YELLOW = PatternFill(fill_type='solid', fgColor='FFFF00')"
    - "Pathlib join for output path — hardcoded filename prevents path injection (T-05-02)"

key-files:
  created:
    - pipeline/writer.py
  modified:
    - pipeline/__init__.py
    - tests/test_phase5.py

key-decisions:
  - "Deviation (Rule 3): Added write_workbook to pipeline/__init__.py in this plan rather than 05-03 — required for the 8 unit tests to pass since all use 'from pipeline import write_workbook'"
  - "Test fixes (Rule 1): Fixed 3 bugs in test stubs from 05-01 — tfd.rows (should be len(tfd.row_boxes)), header lookup by label not field name, fgColor.rgb endswith('FFFF00') for ARGB format"
  - "openpyxl ARGB format: when loading back a saved workbook, fgColor.rgb returns '00FFFF00' (8-char ARGB) not 'FFFF00' (6-char RGB) — test uses endswith() to handle both"

patterns-established:
  - "Pattern 1: pathlib-output-path — use pathlib.Path(output_dir) / 'hardcoded_name.xlsx' to prevent path injection via settings dict"
  - "Pattern 2: label-fallback — headers always use fd.label or fd.name; no empty column headers allowed"
  - "Pattern 3: text-format-substrings — substring set checked against lowercased field_name to identify code/date/monetary columns requiring '@' number format"

requirements-completed: [OUT-01, OUT-02, OUT-03, OUT-04, OUT-05]

# Metrics
duration: 25min
completed: 2026-05-06
---

# Phase 5 Plan 02: Excel Workbook Writer Summary

**openpyxl writer with 89-column CMS-1500 and 178-column UB-04 sheets, yellow fill for low-confidence cells, text-format '@' for code/date/monetary columns, frozen header row, pathlib path construction**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-05-06T00:00:00Z
- **Completed:** 2026-05-06T00:25:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created pipeline/writer.py (213 lines) implementing write_workbook() with all D-01 through D-10 decisions
- CMS-1500 sheet: 89 columns (29 single fields + 10 table fields x 6 SL rows), header frozen at A2, width 15
- UB-04 sheet: 178 columns (24 single fields + 7 table fields x 22 RL rows), header frozen at A2, width 15
- Yellow PatternFill applied to cells with confidence < threshold or confidence == -1.0 sentinel
- Text format '@' applied via _TEXT_FORMAT_SUBSTRINGS substring matching for NPI, CPT, date, charge, ICD/diag, tax, ZIP, HCPCS, etc.
- Output path uses pathlib join with hardcoded 'extracted_results.xlsx' filename (T-05-02 path injection mitigated)
- Added write_workbook to pipeline/__init__.py exports (Rule 3 deviation — needed for tests)
- Activated 8 unit stubs in tests/test_phase5.py; all 8 pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Create pipeline/writer.py with write_workbook()** - `c938cfa` (feat)
2. **Task 2: Activate 8 unit stubs in tests/test_phase5.py** - `e0b16ea` (test)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `pipeline/writer.py` - Complete Excel output module with write_workbook(), 213 lines
- `pipeline/__init__.py` - Added write_workbook export to __all__ and imports
- `tests/test_phase5.py` - Activated 8 unit stubs; fixed 3 bugs in test logic

## Decisions Made
- Used `endswith("FFFF00")` for fill color assertion — openpyxl saves colors as ARGB (8-char) when read back from disk, so the rgb value is `00FFFF00` not `FFFF00`; endswith handles both forms
- Added pipeline/__init__.py export in this plan rather than deferring to 05-03-PLAN because the 8 unit tests all use `from pipeline import write_workbook` and cannot pass without it

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added write_workbook to pipeline/__init__.py**
- **Found during:** Task 1 (verifying 8 unit tests would pass)
- **Issue:** All 8 unit tests use `from pipeline import write_workbook` but pipeline/__init__.py did not export write_workbook. The plan listed only pipeline/writer.py in files_modified and planned 05-03-PLAN to wire the export. Without the export the 8 unit tests cannot import and pass.
- **Fix:** Added `from .writer import write_workbook` and `"write_workbook"` to __all__ in pipeline/__init__.py
- **Files modified:** pipeline/__init__.py
- **Verification:** `python -c "from pipeline import write_workbook; print('OK')"` exits 0
- **Committed in:** c938cfa (Task 1 commit)

**2. [Rule 1 - Bug] Fixed tfd.rows AttributeError in test_cms1500_column_count and test_ub04_column_count**
- **Found during:** Task 2 (activating stubs)
- **Issue:** Test stubs used `tfd.rows` but TableFieldDef has no `.rows` attribute — only `.row_boxes` (a list). Would raise AttributeError when test ran.
- **Fix:** Changed `range(1, tfd.rows + 1)` to `range(1, len(tfd.row_boxes) + 1)` in both column count tests
- **Files modified:** tests/test_phase5.py
- **Verification:** test_cms1500_column_count and test_ub04_column_count both pass
- **Committed in:** e0b16ea (Task 2 commit)

**3. [Rule 1 - Bug] Fixed header lookup in test_yellow_fill_below_threshold and test_no_fill_above_threshold**
- **Found during:** Task 2 (activating stubs)
- **Issue:** Tests used `header_row.index("box1_insurance_type")` to find column index, but writer uses `fd.label or fd.name` (D-01) — the header is "Box 1 — Insurance Type", not "box1_insurance_type". Would raise ValueError (not in list).
- **Fix:** Changed test to look up `label = next(fd.label or fd.name for fd in CMS1500_FIELDS if fd.name == "box1_insurance_type")` and use that label value for index lookup
- **Files modified:** tests/test_phase5.py
- **Verification:** Both yellow fill tests pass
- **Committed in:** e0b16ea (Task 2 commit)

**4. [Rule 1 - Bug] Fixed fgColor.rgb assertion in test_yellow_fill_below_threshold**
- **Found during:** Task 2 (first test run)
- **Issue:** Test asserted `cell.fill.fgColor.rgb == "FFFF00"` but openpyxl returns `"00FFFF00"` (ARGB format with alpha prefix) when reading back a saved workbook. Test failed with `AssertionError: assert '00FFFF00' == 'FFFF00'`.
- **Fix:** Changed assertion to `cell.fill.fgColor.rgb.endswith("FFFF00")` which handles both 6-char RGB and 8-char ARGB forms
- **Files modified:** tests/test_phase5.py
- **Verification:** test_yellow_fill_below_threshold passes
- **Committed in:** e0b16ea (Task 2 commit)

---

**Total deviations:** 4 auto-fixed (1 Rule 3 blocking, 3 Rule 1 bugs)
**Impact on plan:** All auto-fixes necessary for tests to pass. Rule 3 deviation anticipates 05-03-PLAN (no scope creep — 05-03 would have added the same export). Rule 1 fixes corrected bugs in test stubs created by 05-01-PLAN.

## Issues Encountered
- Pre-existing worktree environment failures: 9 tests in test_phase2.py and 2 errors in test_phase3.py fail because `test.pdf` is not present in the worktree and Poppler path differs. These are identical to failures noted in 05-01-SUMMARY.md and are out of scope.

## Known Stubs
None. pipeline/writer.py is fully implemented. The 4 remaining `@pytest.mark.skip` stubs in test_phase5.py are intentional — activated by 05-03-PLAN.

## Threat Flags
None. The path injection threat (T-05-02) is mitigated: output_path is constructed via `pathlib.Path(output_dir) / "extracted_results.xlsx"` with hardcoded filename. No new security surface introduced.

## Next Phase Readiness
- 05-03-PLAN can now wire the pipeline export verification (test_import_write_workbook_from_pipeline) and activate the text-format and one-row-per-page integration tests
- write_workbook is already exported from pipeline/__init__.py — 05-03 only needs to remove the 4 remaining skip markers and verify the integration stubs pass
- Phase 6 UI can call `write_workbook(cms_pages, ub_pages, settings)` and receive the full output path for the "Open output file" button

## Self-Check

- [x] pipeline/writer.py exists (confirmed by write + import test)
- [x] `python -c "from pipeline.writer import write_workbook; print('OK')"` exits 0
- [x] `python -c "from pipeline import write_workbook; print('OK')"` exits 0
- [x] 8 unit tests pass (pytest tests/test_phase5.py: 8 passed, 4 skipped)
- [x] Commit c938cfa exists (Task 1)
- [x] Commit e0b16ea exists (Task 2)
- [x] No accidental file deletions (git diff --diff-filter=D HEAD~2 HEAD: empty)

## Self-Check: PASSED

---
*Phase: 05-output-excel-export*
*Completed: 2026-05-06*
