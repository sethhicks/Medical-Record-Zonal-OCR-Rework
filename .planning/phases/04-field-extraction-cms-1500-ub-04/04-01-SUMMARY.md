---
phase: 04-field-extraction-cms-1500-ub-04
plan: 01
subsystem: testing
tags: [pytest, pytesseract, cms1500, ub04, field-extraction]

# Dependency graph
requires:
  - phase: 03-form-detection
    provides: conftest.py fixtures (test_pdf_path, sample_settings) and test stub pattern

provides:
  - tests/test_phase4.py with 17 @pytest.mark.skip stubs covering EXTR-01, EXTR-02, EXTR-03
  - Nyquist contract for Phase 4 field extraction before any implementation begins

affects: [04-02-PLAN, 04-03-PLAN, 04-04-PLAN, 04-05-PLAN, 04-06-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Import-inside-function pattern: all pipeline imports deferred inside test bodies to avoid ImportError before modules exist"
    - "Wave-tagged skip reasons: stub reason strings include wave number (Wave 1 / Wave 2) to track which plan activates each stub"

key-files:
  created:
    - tests/test_phase4.py
  modified: []

key-decisions:
  - "13 unit stubs marked Wave 1 (monkeypatch signatures preserved for activation); 4 integration stubs marked Wave 2 (test_pdf_path + sample_settings fixtures)"
  - "All imports deferred inside function bodies so test_phase4.py can be collected before pipeline/extractor_cms1500.py and pipeline/extractor_ub04.py exist"

patterns-established:
  - "Stub pattern: @pytest.mark.skip(reason='stub — implemented by Wave N') + pass body"
  - "Section grouping: stubs grouped by EXTR-01 (CMS-1500), EXTR-02 (UB-04), EXTR-03 (integration) with separator comments"

requirements-completed: [EXTR-01, EXTR-02, EXTR-03]

# Metrics
duration: 5min
completed: 2026-05-03
---

# Phase 4 Plan 01: Field Extraction Test Scaffold Summary

**17 @pytest.mark.skip stubs in tests/test_phase4.py establishing the Nyquist contract for CMS-1500 and UB-04 field extraction before any extractor code is written**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-05-03T00:00:00Z
- **Completed:** 2026-05-03T00:05:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Created tests/test_phase4.py with exactly 17 test stubs covering EXTR-01 (6 CMS-1500 unit tests), EXTR-02 (5 UB-04 unit tests), pipeline imports (2 stubs), and integration tests (4 stubs)
- Wave 1 stubs (13) use `reason="stub — implemented by Wave 1"` with monkeypatch fixture signatures preserved for activation
- Wave 2 integration stubs (4) use `reason="stub — implemented by Wave 2"` with test_pdf_path + sample_settings fixture signatures
- Full pytest suite passes at 31 passed, 17 skipped, 0 errors — existing regression intact

## Task Commits

Each task was committed atomically:

1. **Task 1: Create tests/test_phase4.py with 17 skipped stubs** - `8868bc1` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `tests/test_phase4.py` - 17 @pytest.mark.skip stubs for Phase 4 field extraction tests; Wave 1 stubs have monkeypatch signatures; Wave 2 stubs have test_pdf_path + sample_settings fixture parameters

## Decisions Made

None - followed plan as specified. Stub structure and skip reasons match plan specification exactly.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- test_phase4.py is in place; Wave 1 plans (04-02 through 04-05) can now remove skip markers as extractors are built
- 04-02 activates whitelist config updates in config/cms1500.py (box21 ICD-10 alpha + CPT hyphen)
- 04-03 activates 6 CMS-1500 unit stubs after implementing pipeline/extractor_cms1500.py
- 04-04 activates 5 UB-04 unit stubs after implementing pipeline/extractor_ub04.py
- 04-05 activates 2 pipeline import stubs after updating pipeline/__init__.py re-exports
- 04-06 activates 4 integration stubs after empirical calibration sweep

## Self-Check

- [x] tests/test_phase4.py exists at C:/Users/shset/Documents/GitHub/OCR-Rework/tests/test_phase4.py
- [x] grep -c "def test_" returns 17
- [x] grep -c "pytest.mark.skip" returns 17
- [x] pytest exits 0 with "31 passed, 17 skipped"
- [x] Commit 8868bc1 exists

## Self-Check: PASSED

---
*Phase: 04-field-extraction-cms-1500-ub-04*
*Completed: 2026-05-03*
