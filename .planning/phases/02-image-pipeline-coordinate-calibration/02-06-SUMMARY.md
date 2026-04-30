---
phase: 02-image-pipeline-coordinate-calibration
plan: "06"
subsystem: pipeline
tags: [opencv, preprocessing, deskew, adaptive-threshold, scale-correction]
dependency_graph:
  requires: [02-01, 02-02, 02-05]
  provides: [pipeline.preprocess_page]
  affects: [pipeline/__init__.py]
tech_stack:
  added: [opencv-python, numpy]
  patterns: [PIL-to-NumPy conversion, Hough-line deskew, Gaussian adaptive threshold, contour-based scale correction]
key_files:
  created: [pipeline/preprocessor.py]
  modified: [pipeline/__init__.py]
decisions:
  - "Step order locked D-08: scale correction → deskew → adaptive threshold"
  - "Deskew rejection at ±5° raises ValueError with 'exceeds' in message (D-10)"
  - "block_size auto-corrects even values to odd via block_size += 1 (T-2-03)"
  - "debug=True writes 4 PNGs to CWD so tests control location via monkeypatch.chdir"
  - "Adaptive threshold: ADAPTIVE_THRESH_GAUSSIAN_C, block_size=31, C=11"
metrics:
  duration: "5 minutes"
  completed: "2026-04-30"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 1
---

# Phase 2 Plan 06: OpenCV Preprocessing Pipeline Summary

**One-liner:** Three-step OpenCV pipeline (scale correction, Hough-line deskew, Gaussian adaptive threshold) with ValueError rejection for skew >5° and even block_size auto-correction.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create pipeline/preprocessor.py with three-step pipeline | 3aacaf7 | pipeline/preprocessor.py (created) |
| 2 | Update pipeline/__init__.py to use real preprocessor import | 79ee644 | pipeline/__init__.py (modified) |

## Implementation Details

### pipeline/preprocessor.py

`preprocess_page(image, settings, debug=False) -> PIL.Image` implements the three mandatory steps in D-08 order:

**Step 1 — Scale Correction (D-07)**
Finds the largest contour on an inverted binary threshold of the grayscale image, computes scale_x/scale_y relative to the 2550x3300 canvas, then resizes to exactly 2550x3300 via `cv2.INTER_LINEAR`. If no contours exist (blank page), treats scale as 1.0.

**Step 2 — Deskew (D-10)**
Runs Canny edge detection then `HoughLinesP` with threshold=100, minLineLength=100, maxLineGap=10. Collects angles of near-horizontal lines (|angle| < 45°). Takes the median angle. Raises `ValueError(f"Skew angle {skew_angle:.1f}° exceeds ±5° limit — manual review required")` if |skew| > 5.0°. Applies `warpAffine` with `BORDER_REPLICATE` to correct small tilts without clipping.

**Step 3 — Adaptive Threshold (D-09)**
Reads `settings.get("threshold_block_size", 31)`. Auto-corrects even values: `if block_size % 2 == 0: block_size += 1` (T-2-03 mitigation). Applies `cv2.adaptiveThreshold` with `ADAPTIVE_THRESH_GAUSSIAN_C`, `THRESH_BINARY`, C=11. Returns grayscale result converted to RGB PIL Image.

**Debug mode (D-11):** `debug=True` saves 4 PNGs to CWD: `debug_01_raw.png`, `debug_02_scaled.png`, `debug_03_deskewed.png`, `debug_04_threshold.png`.

### pipeline/__init__.py

Replaced the `try/except ImportError` guard from 02-05-PLAN with a clean direct import:
```python
from .converter import convert_page
from .preprocessor import preprocess_page
```

## Test Results

All 5 preprocessor tests pass:

| Test | Result |
|------|--------|
| test_preprocess_smoke | PASSED |
| test_preprocess_mode | PASSED |
| test_deskew_rejection | PASSED |
| test_scale_factors_near_one | PASSED |
| test_preprocess_debug_files | PASSED |

Phase 1 regression: 8/8 green.

## Deviations from Plan

None — plan executed exactly as written. The plan provided the complete implementation verbatim and it passed all tests on first run.

## Known Stubs

None. `preprocess_page` is fully implemented with real OpenCV logic and produces valid output on `test.pdf` page 0.

## Threat Surface Scan

No new network endpoints, auth paths, or trust boundary changes. The T-2-03 threat (even block_size causing cv2.error) is mitigated as specified. T-2-06-01 (oversized image) is accepted per the plan — input is always 2550x3300 from convert_page.

## Self-Check

Files:
- pipeline/preprocessor.py: FOUND
- pipeline/__init__.py: FOUND (modified)

Commits:
- 3aacaf7: FOUND (feat(02-06): create pipeline/preprocessor.py)
- 79ee644: FOUND (feat(02-06): update pipeline/__init__.py)

## Self-Check: PASSED
