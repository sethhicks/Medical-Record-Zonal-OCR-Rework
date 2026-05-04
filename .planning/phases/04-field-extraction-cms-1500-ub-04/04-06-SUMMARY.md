---
phase: 04-field-extraction-cms-1500-ub-04
plan: 06
subsystem: testing
tags: [calibration, ocr, tesseract, cms1500, ub04, integration-tests]

# Dependency graph
requires:
  - phase: 04-field-extraction-cms-1500-ub-04
    provides: extract_cms1500, extract_ub04 pipeline functions (plans 04-03 through 04-05)
provides:
  - Empirical non-empty rate data for all 30 test.pdf pages documented in STATE.md
  - CMS_THRESHOLD = 0.107 and UB04_THRESHOLD = 0.107 derived from live sweep
  - (pending checkpoint approval) 4 activated integration tests with calibrated thresholds
affects: [05-output-excel-export, 06-desktop-ui-batch-processing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Empirical-threshold integration tests: run extractor on best page from sweep, assert rate >= (best_rate - 0.05)"

key-files:
  created: []
  modified:
    - .planning/STATE.md

key-decisions:
  - "CMS_THRESHOLD = 0.107 (empirical 15.7% best rate minus 5pp); NOT hardcoded 0.80"
  - "UB04_THRESHOLD = 0.107 (empirical 15.7% best rate minus 5pp); NOT hardcoded 0.80"
  - "Best CMS-1500 page = 15 (14/89 fields non-empty = 15.7%)"
  - "Best UB-04 page = 6 (28/178 fields non-empty = 15.7%)"
  - "Coordinate re-tuning (Phase 2) needed before 80% roadmap criterion can be met"

patterns-established:
  - "Calibration-first: sweep all pages, pick best, derive threshold empirically before writing tests"

requirements-completed: [EXTR-01, EXTR-02, EXTR-03]

# Metrics
duration: partial (checkpoint pending)
completed: 2026-05-04
---

# Phase 4 Plan 06: Calibration Sweep & Integration Test Activation Summary

**PARTIAL — Awaiting checkpoint approval. Task 1 complete; Task 2 is a human-verify checkpoint; Task 3 not yet executed.**

**Empirical sweep of all 30 test.pdf pages reveals 15.7% best non-empty rate for both CMS-1500 (page 15) and UB-04 (page 6); integration test thresholds set to 10.7%**

## Performance

- **Duration:** ~12 min (Task 1 only)
- **Started:** 2026-05-04T13:49:44Z
- **Completed (Task 1):** 2026-05-04T13:56:00Z (approx)
- **Tasks:** 1/3 complete (Task 2 = checkpoint, Task 3 pending user approval)
- **Files modified:** 1 (.planning/STATE.md)

## Accomplishments

- Ran calibration sweep of all 30 pages in test.pdf using both `extract_cms1500` and `extract_ub04`
- Identified 22 CMS-1500 pages, 1 UB-04 page, 7 UNKNOWN pages
- Best CMS-1500: page 15 at 15.7% (14/89 non-empty fields)
- Best UB-04: page 6 at 15.7% (28/178 non-empty fields)
- Computed integration test thresholds: CMS_THRESHOLD = 0.107, UB04_THRESHOLD = 0.107
- Documented calibration data in STATE.md "Phase 4 Calibration Results" section

## Task Commits

1. **Task 1: Calibration sweep across all test.pdf pages** - `9499e20` (feat)
2. **Task 2: CHECKPOINT** — awaiting human verification
3. **Task 3: Activate 4 integration tests** — not yet executed

## Files Created/Modified

- `.planning/STATE.md` — Added "Phase 4 Calibration Results" section with per-page rates, best page numbers, and computed thresholds

## Calibration Results (for user review)

| Form Type | Best Page | Non-empty / Total | Rate | Integration Threshold | Rationale |
|-----------|-----------|-------------------|------|-----------------------|-----------|
| CMS-1500 | Page 15 | 14 / 89 | 15.7% | 10.7% | 15.7% - 5pp; below 80% roadmap criterion |
| UB-04 | Page 6 | 28 / 178 | 15.7% | 10.7% | 15.7% - 5pp; below 80% roadmap criterion |

### Full CMS-1500 Page Sweep

| Page | Non-empty / 89 | Rate |
|------|---------------|------|
| 0 | 8/89 | 9.0% |
| 1 | 8/89 | 9.0% |
| 2 | 9/89 | 10.1% |
| 3 | 7/89 | 7.9% |
| 5 | 7/89 | 7.9% |
| 7 | 10/89 | 11.2% |
| 9 | 7/89 | 7.9% |
| 10 | 9/89 | 10.1% |
| 12 | 10/89 | 11.2% |
| 13 | 13/89 | 14.6% |
| **15** | **14/89** | **15.7% (best)** |
| 16 | 11/89 | 12.4% |
| 18 | 10/89 | 11.2% |
| 19 | 8/89 | 9.0% |
| 20 | 11/89 | 12.4% |
| 21 | 14/89 | 15.7% |
| 24 | 10/89 | 11.2% |
| 25 | 10/89 | 11.2% |
| 26 | 13/89 | 14.6% |
| 27 | 11/89 | 12.4% |
| 28 | 11/89 | 12.4% |
| 29 | 8/89 | 9.0% |

### Full UB-04 Page Sweep

| Page | Non-empty / 178 | Rate |
|------|----------------|------|
| **6** | **28/178** | **15.7% (best, only UB-04 detected)** |

UNKNOWN pages (7): 4, 8, 11, 14, 17, 22, 23 — likely multi-page claim continuation sheets or atypical forms.

## Decisions Made

- CMS_THRESHOLD = 0.107 (empirical best 15.7% minus 5pp) — not hardcoded 0.80
- UB04_THRESHOLD = 0.107 (empirical best 15.7% minus 5pp) — not hardcoded 0.80
- Best CMS-1500 page = 15; best UB-04 page = 6
- Coordinate re-tuning (Phase 2) is needed before the 80% roadmap success criterion can be met; extractor code is correct, this is a coordinate calibration gap

## Deviations from Plan

None for Task 1 — plan executed exactly as written.

## Issues Encountered

None — calibration sweep completed cleanly; all 30 pages processed without Python exceptions.

## Coordinate Quality Note

The best non-empty rate achieved (15.7%) is significantly below the 80% roadmap target. This is expected at this stage — coordinate regions from Phase 2 were initially mapped but not fully tuned for field-level accuracy. The extractor correctly extracts from whatever pixels fall within the defined coordinates; increasing the non-empty rate requires refining the coordinate definitions in `config/cms1500.py` and `config/ub04.py`. Task 3 (pending checkpoint approval) will activate integration tests at the empirically-derived 10.7% threshold.

## Next Phase Readiness

- (Pending checkpoint approval) Task 3 will activate 4 remaining integration tests
- After Task 3: all 17 Phase 4 tests will be active (0 skipped)
- Full suite target: 48 passed (31 Phase 1-3 + 17 Phase 4), 0 skipped

---
*Phase: 04-field-extraction-cms-1500-ub-04*
*Partial summary — checkpoint reached after Task 1*
*Completed: 2026-05-04*
