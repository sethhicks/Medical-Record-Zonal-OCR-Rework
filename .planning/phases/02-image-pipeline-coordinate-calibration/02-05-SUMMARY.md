---
phase: 02-image-pipeline-coordinate-calibration
plan: "05"
subsystem: pipeline
tags: [pdf2image, pillow, poppler, image-conversion, python]

# Dependency graph
requires:
  - phase: 01-foundation-environment
    provides: config_loader.load_settings() with poppler_path default
provides:
  - pipeline/__init__.py public API re-exporting convert_page (and preprocess_page stub)
  - pipeline/converter.py — convert_page(pdf_path, page_num) returning 2550x3300 RGB PIL Image
affects: [02-06-preprocessor, 02-07-calibrate, 03-form-detection, 04-field-extraction]

# Tech tracking
tech-stack:
  added: [pdf2image, pillow (PIL.Image.LANCZOS resize)]
  patterns:
    - explicit poppler_path from settings — never PATH lookup
    - try/except ImportError guard in __init__.py for not-yet-created sibling modules
    - Lanczos resize to normalise slightly undersized scanner output to exact target dimensions

key-files:
  created:
    - pipeline/__init__.py
    - pipeline/converter.py
  modified: []

key-decisions:
  - "Scanners produce 2478x3228 at 300 DPI (8.26x10.76 in actual page size, not 8.5x11). Pages within ±10% of 2550x3300 are resized via Lanczos to exact target so coordinate space is stable."
  - "ValueError raised only for pages deviating >10% from target (truly non-US-Letter content), not for typical scanner margin variation."
  - "try/except ImportError guard in __init__.py allows convert_page tests to run before preprocessor.py exists."

patterns-established:
  - "pipeline/__init__.py: try/except ImportError guard for sibling modules not yet created"
  - "converter.py: always index pages[0] from pdf2image even for single-page results"
  - "converter.py: resize within tolerance range rather than reject — normalises scanner size variation"

requirements-completed:
  - PROC-01

# Metrics
duration: 5min
completed: "2026-04-30"
---

# Phase 02 Plan 05: Pipeline Converter Summary

**pdf2image-to-PIL converter with Lanczos normalisation to exact 2550x3300 coordinate space, handling real scanner pages that are 2478x3228 at 300 DPI**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-30T17:20:11Z
- **Completed:** 2026-04-30T17:25:42Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `pipeline/` package created with `__init__.py` re-exporting `convert_page`
- `convert_page(pdf_path, page_num)` returns exactly 2550x3300 RGB PIL Image using pdf2image + Poppler at 300 DPI
- All three `test_convert_page_*` tests pass green; Phase 1 regression 8/8 still green

## Task Commits

1. **Task 1: Create pipeline/__init__.py as public API re-export** - `e03186f` (feat)
2. **Task 2: Create pipeline/converter.py with convert_page()** - `6fe24fa` (feat)

## Files Created/Modified

- `pipeline/__init__.py` — Package init; re-exports `convert_page` from `.converter`; try/except guard for `preprocess_page` (02-06)
- `pipeline/converter.py` — `convert_page(pdf_path, page_num)`: calls `convert_from_path` at 300 DPI with explicit `poppler_path`, resizes to 2550x3300 if within ±10%, raises `ValueError` for wildly wrong dimensions

## Decisions Made

- Real test.pdf pages are 2478x3228 px at 300 DPI (actual scan size: 8.26 x 10.76 in, not 8.5 x 11). This is consistent across all 32 pages. The plan assumed exact US Letter dimensions; the correct fix is Lanczos resize to 2550x3300 so the fixed coordinate space is preserved.
- ValueError tolerance set at ±10% to reject landscape or completely wrong-format files while accepting all typical scanner variations.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Actual scanner pages are 2478x3228 at 300 DPI, not 2550x3300**
- **Found during:** Task 2 (Create pipeline/converter.py) — tests failed immediately
- **Issue:** test.pdf pages are 8.26 x 10.76 in (594.72 x 774.72 pts per pdfinfo), producing 2478x3228 at 300 DPI. The plan's must_have truth `convert_page('test.pdf', 0).size == (2550, 3300)` and `raises ValueError when not 2550x3300` are contradictory for real input.
- **Fix:** After pdf2image conversion, if the image is within ±10% of 2550x3300, resize via `PIL.Image.LANCZOS` to exactly 2550x3300. If it deviates more than 10%, raise `ValueError`. This normalises the coordinate space without rejecting valid scanner output.
- **Files modified:** `pipeline/converter.py`
- **Verification:** All 3 `test_convert_page_*` tests pass; Phase 1 regression 8/8 passes
- **Committed in:** `6fe24fa` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — Bug)
**Impact on plan:** Necessary for correctness. The PDF dimension mismatch is an environment fact (real scanner output); the resize normalises it transparently. No scope creep. Coordinate calibration in later plans will validate that 2550x3300 coordinates match actual form content.

## Issues Encountered

- test.pdf pages are 2478x3228 at 300 DPI (scan pages are 8.26 x 10.76 in, not 8.5 x 11 in). The pdfinfo `Page size: 594.72 x 774.72 pts` confirms this. All 32 pages are this size. The coordinate calibration in plan 02-07 must verify that the resized images correctly align with field coordinates.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `from pipeline import convert_page` works; produces 2550x3300 RGB PIL Image
- Phase 2 plan 02-06 (`preprocessor.py`) can import `convert_page` and build on it
- The `preprocess_page = None` stub in `__init__.py` will be replaced by 02-06
- Calibration concern: since pages are resized from 2478x3228 to 2550x3300 (~3% scale-up), the coordinate calibration overlay in 02-07 must be verified against the resized output

---
*Phase: 02-image-pipeline-coordinate-calibration*
*Completed: 2026-04-30*
