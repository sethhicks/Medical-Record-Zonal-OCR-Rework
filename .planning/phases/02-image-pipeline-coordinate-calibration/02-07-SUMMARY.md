---
plan: 02-07
phase: 02-image-pipeline-coordinate-calibration
status: complete
wave: 2
completed: 2026-05-01
---

# Plan 02-07: Calibration Overlay CLI — Summary

## What Was Built

`pipeline/calibrate.py` — standalone CLI script that renders a PDF page with all configured field regions drawn as labelled rectangles and writes the result to `calibration_overlay_p{N}.png`. Implements the coordinate verification gate required before Phase 4 field extraction begins.

## Key Files

### Created
- `pipeline/calibrate.py` — CLI calibration overlay script with `_run()` entry point

## Behaviour

```
python pipeline/calibrate.py --page 0 --pdf test.pdf
python pipeline/calibrate.py --page 2 --pdf test.pdf --form ub04
```

- Loads the page via `convert_page()`, detects form type from anchor strings (or accepts `--form` override)
- Draws only the field set matching the detected form type (D-04)
- `FieldDef` rectangles: green; `TableFieldDef` row boxes: orange; labels: red, drawn above each rectangle (D-03)
- Writes `calibration_overlay_p{N}.png` to the current working directory (D-01)
- Prints form type, page number, field count, and output path to stdout
- sys.path bootstrap ensures importability regardless of invocation CWD

## Verification

```
pytest tests/test_phase2.py -q
# → 15 passed in ~17 s
```

- `test_calibrate_overlay_created` — PASSED (exit 0, file exists)
- `test_calibrate_overlay_nonempty` — PASSED (file > 1 KB)

Phase 1 regression: 8/8 green.

## Self-Check: PASSED

- [x] `python pipeline/calibrate.py --page 0 --pdf test.pdf` exits 0
- [x] `calibration_overlay_p0.png` written and > 1 KB
- [x] Overlay draws only the matching form type field set (D-04)
- [x] Labels are full `FieldDef.name` strings drawn outside rectangles (D-03)
- [x] All 15 Phase 2 tests pass (15/15)
- [x] SUMMARY.md committed in phase directory
