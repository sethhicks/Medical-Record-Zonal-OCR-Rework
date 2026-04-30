---
plan: 02-01
phase: 02-image-pipeline-coordinate-calibration
status: complete
wave: 0
completed: 2026-04-30
---

# Plan 02-01: Test Scaffold — Summary

## What Was Built

Created the complete Phase 2 test scaffold before any implementation exists. Establishes the RED baseline that all Wave 1 plans must satisfy.

## Key Files

### Created
- `tests/test_phase2.py` — 15 test functions covering PROC-01 (converter), PROC-02 (preprocessor), and EXTR-04 (calibration + coordinate configs). All fail/error on collection since implementations don't exist yet (no `@pytest.mark.skip` decorators).
- `tests/conftest.py` — Two session-scoped fixtures: `test_pdf_path` (resolves project-root `test.pdf`) and `sample_settings` (calls `load_settings()` with no settings.json to get defaults).

## Test Coverage

| Section | Tests | Covers |
|---------|-------|--------|
| PROC-01 convert_page | 3 | dimensions (2550×3300), mode (RGB), invalid-path exception |
| PROC-02 preprocess_page | 5 | smoke (size), mode, debug PNGs, deskew rejection (ValueError "exceeds"), scale factors near 1.0 |
| EXTR-04 calibrate CLI | 2 | overlay file created, overlay > 1 KB |
| Settings | 1 | threshold_block_size default = 31 |
| CMS-1500 coords | 2 | CMS1500_FIELDS non-empty FieldDef list, CMS1500_TABLE_FIELDS rows == 6 |
| UB-04 coords | 2 | UB04_FIELDS non-empty FieldDef list, UB04_TABLE_FIELDS rows == 22 |

## Verification

```
pytest tests/test_phase2.py --collect-only -q
# → 15 tests collected (0 errors, 0 skips)
```

Phase 1 regression: `pytest tests/test_phase1.py -q` — 8/8 passing (no regression).

## Self-Check: PASSED

- [x] 15 test functions present (`grep -c "^def test_" tests/test_phase2.py` = 15)
- [x] 0 skip markers (`grep -c "skip" tests/test_phase2.py` = 0)
- [x] pytest collects all 15 without import error
- [x] conftest.py has `test_pdf_path` and `sample_settings` fixtures (session-scoped)
- [x] SUMMARY.md committed in phase directory
- [x] STATE.md and ROADMAP.md not modified
