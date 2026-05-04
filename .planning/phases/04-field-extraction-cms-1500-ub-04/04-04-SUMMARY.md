---
phase: 04-field-extraction-cms-1500-ub-04
plan: "04"
subsystem: pipeline
tags: [extractor, ub04, ocr, field-extraction]
dependency_graph:
  requires:
    - 04-01-PLAN.md  # test scaffold
    - 04-03-PLAN.md  # CMS-1500 extractor (structural template)
  provides:
    - pipeline/extractor_ub04.py (extract_ub04 public function)
    - 5 activated UB-04 unit tests
  affects:
    - tests/test_phase4.py
tech_stack:
  added: []
  patterns:
    - Fixed-region crop + pytesseract.image_to_data per field (duplicated from CMS-1500 per D-08)
    - Revenue-line naming: {tfd.name}_rl{i+1} (D-07)
    - Blank sentinel: value='', confidence=-1.0 (D-11)
    - Min-confidence aggregation across words (D-10)
key_files:
  created:
    - pipeline/extractor_ub04.py
  modified:
    - tests/test_phase4.py
decisions:
  - "D-07 revenue-line suffix _rl{i+1} used (not _sl) to distinguish UB-04 from CMS-1500 service lines"
  - "D-08 _ocr_region duplicated verbatim from extractor_cms1500.py — both modules self-contained"
  - "D-11 blank/exception path returns ('', -1.0) sentinel so downstream callers always get float confidence"
  - "Tests import from pipeline.extractor_ub04 directly (not pipeline) until 04-05 adds __init__ export"
metrics:
  duration_seconds: 1461
  completed_date: "2026-05-04"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 1
requirements:
  - EXTR-02
  - EXTR-03
---

# Phase 04 Plan 04: UB-04 Extractor Summary

UB-04 field extractor created — extract_ub04 returns 178 FieldResults (24 single + 154 revenue-line cells across 7 x 22-row table) with _rl{i+1} naming and -1.0 blank sentinels; 5 unit tests activated and passing, full suite 42 passed 6 skipped.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create pipeline/extractor_ub04.py | 1e47ea8 | pipeline/extractor_ub04.py (created, 89 lines) |
| 2 | Activate 5 UB-04 unit tests | 52dacca | tests/test_phase4.py (modified) |

## What Was Built

### pipeline/extractor_ub04.py

New file implementing the UB-04 field extractor, mirroring the CMS-1500 extractor pattern (D-08):

- `_ocr_region(crop, psm, whitelist) -> (str, float)`: private helper, duplicated from extractor_cms1500.py. Runs `pytesseract.image_to_data`, collects words with conf > 0, returns min-confidence (D-10). Returns `("", -1.0)` for blank or exception (D-11, T-4-09 mitigation).
- `extract_ub04(image, settings) -> list[FieldResult]`: public function. Sets `pytesseract.tesseract_cmd` from settings (Windows requirement). Iterates 24 `UB04_FIELDS` entries for single-value fields, then 7 `UB04_TABLE_FIELDS` entries × 22 rows each for revenue lines. Revenue-line names use `{tfd.name}_rl{i+1}` suffix (D-07). Always returns exactly 178 entries.

### tests/test_phase4.py

Removed `@pytest.mark.skip` from 5 UB-04 test stubs and replaced stub bodies with real implementations:

1. `test_extract_ub04_returns_list` — verifies `isinstance(result, list)`
2. `test_extract_ub04_result_count` — verifies `len(result) == 178` (EXTR-02)
3. `test_extract_ub04_revenue_line_naming` — verifies `ub04_rl_rev_code_rl1` through `ub04_rl_rev_code_rl22` in result names (D-07)
4. `test_extract_ub04_blank_rl_sentinel` — verifies all value='' and confidence=-1.0 on all-white image (D-11)
5. `test_ub04_all_results_have_confidence` — verifies all confidence values are `float` instances (EXTR-03)

All tests use `monkeypatch` to mock `pytesseract.image_to_data` with empty data (no Tesseract I/O needed in unit tests). Imports are from `pipeline.extractor_ub04` directly (not `pipeline`) until 04-05-PLAN adds the `__init__.py` export (D-09).

## Verification Results

```
python -m pytest tests/test_phase4.py -x -q
# 11 passed, 6 skipped in 0.58s

python -m pytest tests/ -q
# 42 passed, 6 skipped in 19.60s

grep -c "pytest.mark.skip" tests/test_phase4.py
# 6
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None in the files created/modified by this plan. The 6 remaining `@pytest.mark.skip` tests in `test_phase4.py` are intentional stubs for later plans (04-05, 04-06), not stubs introduced by this plan.

## Threat Flags

No new threat surface introduced. `_ocr_region` exception handling mitigates T-4-09 (DoS via bad OCR region) as specified in the threat register.

## Self-Check: PASSED

- pipeline/extractor_ub04.py exists: FOUND
- tests/test_phase4.py modified with 5 activated tests: FOUND
- Commit 1e47ea8 (Task 1): FOUND
- Commit 52dacca (Task 2): FOUND
- Full suite: 42 passed, 6 skipped, 0 errors: VERIFIED
