# Phase 2: Image Pipeline & Coordinate Calibration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-29
**Phase:** 02-image-pipeline-coordinate-calibration
**Areas discussed:** Calibration script output, Coordinate entry strategy, Preprocessing defaults, Pipeline module structure

---

## Calibration Script Output

| Option | Description | Selected |
|--------|-------------|----------|
| Save PNG + auto-open | Writes PNG and opens in default viewer | |
| Save PNG only | Writes PNG to disk; user opens manually | ✓ |
| cv2.imshow() interactive | OpenCV window; requires display | |

**User's choice:** Save PNG only

| Option | Description | Selected |
|--------|-------------|----------|
| CLI arg — any page on demand | `--page N` flag selects any page | ✓ |
| Hardcoded: page 0 + first UB-04 | Always renders two fixed pages | |
| All pages as a batch | Renders all 30 pages | |

**User's choice:** CLI arg (`python calibrate.py --page N --pdf PATH`)

| Option | Description | Selected |
|--------|-------------|----------|
| Project root | Writes alongside source files | ✓ |
| calibration/ subdirectory | Separate directory | |
| Same directory as input PDF | Beside test.pdf | |

**User's choice:** Project root — `calibration_overlay_p{N}.png`

| Option | Description | Selected |
|--------|-------------|----------|
| Short name inside the box | FieldDef.label as white text inside rectangle | |
| Numbered index only | Index + stdout legend | |
| Full field name outside the box | FieldDef.name drawn above/below rectangle | ✓ |

**User's choice:** Full field name (FieldDef.name) drawn outside the rectangle

---

## Coordinate Entry Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Pre-populate estimates, then calibrate | Claude writes estimated coords; user verifies visually | ✓ |
| Leave blank until I measure manually | Start empty; user fills all coordinates | |
| Interactive coordinate picker | Click-to-capture helper script | |

**User's choice:** Pre-populate estimates, then calibrate via overlay PNG

| Option | Description | Selected |
|--------|-------------|----------|
| Edit config/cms1500.py directly | Source files are the source of truth | ✓ |
| JSON/YAML side-file, then code-gen | Separate coords file with generator | |

**User's choice:** Edit config/cms1500.py and config/ub04.py directly

| Option | Description | Selected |
|--------|-------------|----------|
| Only the matching form type | CMS-1500 overlay on CMS-1500 pages only | ✓ |
| Both form types always | Draw all fields regardless of page type | |

**User's choice:** Only the matching form type

| Option | Description | Selected |
|--------|-------------|----------|
| Implement it — scans can vary slightly | Scale correction mandatory (aligns with ROADMAP SC-4) | ✓ |
| Skip scale correction | Trust all scans are 2550×3300 | |

**User's choice:** Implement scale correction

---

## Preprocessing Defaults

| Option | Description | Selected |
|--------|-------------|----------|
| Scale → Deskew → Threshold | Normalize geometry first, then threshold | ✓ |
| Deskew → Scale → Threshold | Straighten before scale-correct | |
| Threshold → Deskew → Scale | Binarize first for contour detection | |

**User's choice:** Scale → Deskew → Threshold

| Option | Description | Selected |
|--------|-------------|----------|
| 31 (standard for 300 DPI scanned forms) | Block size 31 as starting default | ✓ |
| 51 (more aggressive smoothing) | Larger block | |
| You decide | Leave to Claude | |

**User's choice:** 31 (stored in settings.json as `threshold_block_size`)

| Option | Description | Selected |
|--------|-------------|----------|
| Reject page — return error | Skew > ±5° → raise error, treated as failed page | ✓ |
| Clamp to ±5° and correct anyway | Cap correction silently | |
| Warn but continue | Log warning, proceed | |

**User's choice:** Reject page and return error if skew > ±5°

| Option | Description | Selected |
|--------|-------------|----------|
| Final image only; debug=True flag saves intermediates | Clean API, opt-in debug | ✓ |
| Return all intermediates | Always return all pipeline stages | |
| You decide | Leave to Claude | |

**User's choice:** Final image only; `debug=True` flag saves intermediate PNGs

---

## Pipeline Module Structure

| Option | Description | Selected |
|--------|-------------|----------|
| pipeline/ package with sub-modules | converter.py, preprocessor.py, calibrate.py, __init__.py | ✓ |
| Single pipeline.py module | One flat file with all functions | |

**User's choice:** `pipeline/` package with sub-modules

| Option | Description | Selected |
|--------|-------------|----------|
| Two functions: convert_page + preprocess_page | Separate convert and preprocess calls | ✓ |
| One function: process_page | Combined convert + preprocess in one call | |

**User's choice:** Two separate functions (`convert_page` + `preprocess_page`)

| Option | Description | Selected |
|--------|-------------|----------|
| Validate inside converter.py | ValueError if image ≠ 2550×3300 | ✓ |
| Caller validates | Converter returns whatever pdf2image gives | |

**User's choice:** Validate inside converter.py

| Option | Description | Selected |
|--------|-------------|----------|
| tests/test_phase2.py | Consistent with Phase 1 naming convention | ✓ |
| tests/test_pipeline.py | Named after the module | |

**User's choice:** `tests/test_phase2.py`

---

## Claude's Discretion

- Adaptive threshold constant `C` and exact OpenCV flags
- Deskew implementation method (Hough-line vs. Canny + minAreaRect)
- Bounding box detection method for scale correction
- Calibration overlay rectangle color and text styling
- Whether calibrate.py prints a stdout summary

## Deferred Ideas

None surfaced during discussion.
