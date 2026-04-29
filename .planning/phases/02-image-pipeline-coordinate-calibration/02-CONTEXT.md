# Phase 2: Image Pipeline & Coordinate Calibration - Context

**Gathered:** 2026-04-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the PDF→PIL converter, OpenCV preprocessing pipeline (scale correction, deskew, adaptive threshold), and coordinate calibration script. Populate `CMS1500_FIELDS` / `UB04_FIELDS` with estimated pixel coordinates and visually verify them against `test.pdf` using the calibration overlay before any extractor code is written. No form detection, no OCR field extraction — those belong in Phases 3 and 4.

</domain>

<decisions>
## Implementation Decisions

### Calibration Script Output
- **D-01:** Output is PNG only — no auto-open, no cv2.imshow(). Script writes `calibration_overlay_p{N}.png` to the project root and exits. User opens the PNG manually.
- **D-02:** Page selection via CLI argument: `python calibrate.py --page N --pdf test.pdf`. Any page can be inspected on demand; no hardcoded defaults.
- **D-03:** Field region labels are the full `FieldDef.name` (e.g. `box24_cpt_sl1`) drawn **outside** the rectangle (above or below), not inside. Verbose but unambiguous at any zoom level.
- **D-04:** The overlay draws only the field set that matches the detected form type on that page. CMS-1500 fields are not drawn on a UB-04 page and vice versa.

### Coordinate Entry Strategy
- **D-05:** Phase 2 pre-populates `CMS1500_FIELDS` and `UB04_FIELDS` with estimated pixel coordinates derived from standard form dimensions (2550×3300 px, known layout). User runs `calibrate.py`, inspects the overlay PNG, and adjusts coordinates directly in `config/cms1500.py` / `config/ub04.py`. No intermediate tooling — edit-and-re-run is the workflow.
- **D-06:** `config/cms1500.py` and `config/ub04.py` are the sole source of truth for coordinates. No JSON/YAML side-file or code generation.
- **D-07:** Scale correction is mandatory — `preprocess_page()` computes `scale_x`/`scale_y` from the detected form bounding box and applies them to the returned coordinate space. Required by ROADMAP.md success criterion 4.

### Preprocessing Pipeline
- **D-08:** Pipeline step order: **Scale correction → Deskew → Adaptive threshold**. Geometry is normalized first; threshold is applied to the corrected image.
- **D-09:** Default Gaussian adaptive threshold block size: **31**. Stored in `settings.json` as `threshold_block_size` (already tunable via ENV-02 settings schema). Constant `C` and method (`ADAPTIVE_THRESH_GAUSSIAN_C`) are Claude's discretion.
- **D-10:** Deskew rejection threshold: **±5°**. If the detected skew angle exceeds ±5°, `preprocess_page()` raises an error (not a warning, not a clamp). The Phase 6 pipeline treats it as a failed page — blank row with `extraction_error` populated.
- **D-11:** `preprocess_page()` returns a single PIL Image (the fully preprocessed page). A `debug=True` keyword argument saves intermediate PNGs to the project root if the caller needs to inspect stages. Default is `debug=False`.

### Pipeline Module Structure
- **D-12:** New `pipeline/` package at the project root with these sub-modules:
  - `pipeline/converter.py` — `convert_page(pdf_path, page_num) → PIL Image`
  - `pipeline/preprocessor.py` — `preprocess_page(image, settings, debug=False) → PIL Image`
  - `pipeline/calibrate.py` — standalone CLI script (entry point: `python pipeline/calibrate.py --page N --pdf PATH`)
  - `pipeline/__init__.py` — re-exports `convert_page` and `preprocess_page` as the public API
- **D-13:** DPI/dimension validation is enforced inside `converter.py`. If the resulting image is not 2550×3300 px, `convert_page()` raises `ValueError`. No caller can accidentally skip this check.
- **D-14:** Two separate public functions (`convert_page` + `preprocess_page`) rather than one combined call. This lets Phase 3 (form detection) call `convert_page` on the raw image for fast anchor-string scanning before committing to full preprocessing.
- **D-15:** Tests live in `tests/test_phase2.py` — consistent with the `tests/test_phase1.py` naming convention.

### Claude's Discretion

The following are left to Claude during implementation, constrained by the decisions above and ROADMAP.md success criteria:

- Adaptive threshold constant `C` value and exact OpenCV flags
- Deskew implementation method (Hough-line angle detection or Canny + minAreaRect — whichever is more reliable on scanned forms)
- Bounding box detection method for scale correction (contour of the outer form border)
- Color of the calibration overlay rectangles and text (high-contrast, readable on the form)
- Whether `calibrate.py` prints a summary to stdout (field count, form type detected, output path)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Requirements
- `.planning/REQUIREMENTS.md` — PROC-01, PROC-02, and EXTR-04 are the requirements for this phase; full acceptance criteria text lives here
- `.planning/ROADMAP.md` §Phase 2 — 4 success criteria define exactly what must be true when this phase is complete (pixel dimensions, calibration overlay, threshold effect on Box 24, scale correction validation)

### Project Context
- `.planning/PROJECT.md` — Core technical approach, form types (CMS-1500 / UB-04), fixed coordinate space (2550×3300 px at 300 DPI), out-of-scope items
- `.planning/STATE.md` — Open decisions (ICD-10 format, confidence threshold) that are NOT resolved yet; Phase 2 notes (highest-risk phase warning)

### Existing Phase 1 Code (reuse directly)
- `config/base.py` — `FieldDef` and `TableFieldDef` dataclasses; understand their schema before populating CMS-1500 / UB-04 field lists
- `config/cms1500.py` — `CMS1500_FIELDS` and `CMS1500_TABLE_FIELDS` lists to be populated in this phase
- `config/ub04.py` — `UB04_FIELDS` and `UB04_TABLE_FIELDS` lists to be populated in this phase
- `config_loader.py` — `load_settings()` returns a settings dict; `preprocess_page()` receives this dict and reads `threshold_block_size` from it
- `models/field_result.py` — `FieldResult` dataclass; Phase 2 does not produce FieldResults but must understand the interface Phase 4 will use

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `config/base.py` `FieldDef(name, box, psm, whitelist, label)` — box is `(left, top, right, bottom)` at 300 DPI; label is the human-readable display string for calibration overlays
- `config/base.py` `TableFieldDef(name, row_boxes, psm, whitelist, label)` — row_boxes is a list of one tuple per row; used for Box 24 (6 rows) and UB-04 revenue lines (22 rows)
- `config_loader.py` `load_settings()` — already handles `tesseract_cmd`, `poppler_path`, `confidence_threshold`, `output_dir`; Phase 2 adds `threshold_block_size` to the schema (default 31 if absent)

### Established Patterns
- Windows-explicit binary paths: `poppler_path` and `tesseract_cmd` are passed explicitly; no PATH lookup. The same pattern applies to `pdf2image.convert_from_path(poppler_path=...)`.
- Settings-driven defaults: all tunables go through `settings.json` + `load_settings()`; hardcoded fallbacks only for machine-specific paths.
- Test file naming: `tests/test_phase2.py` continues the `test_phaseN.py` convention.
- Non-zero exit on validation failure: `setup_check.py` raises or exits non-zero; `convert_page()` should raise `ValueError` (not sys.exit) so callers can handle it.

### Integration Points
- `pipeline.convert_page` → called by Phase 3 (form detection on raw image) and Phase 4 (extraction after preprocessing)
- `pipeline.preprocess_page` → called by Phase 4 before field extraction
- `config/cms1500.py` `CMS1500_FIELDS` + `CMS1500_TABLE_FIELDS` → consumed by Phase 4 extractor and Phase 2 calibration overlay
- `config/ub04.py` `UB04_FIELDS` + `UB04_TABLE_FIELDS` → same
- `settings.json` `threshold_block_size` → read by `preprocess_page()`; add to `load_settings()` defaults

</code_context>

<specifics>
## Specific Ideas

- Calibration script invocation: `python pipeline/calibrate.py --page 0 --pdf test.pdf` → writes `calibration_overlay_p0.png` to project root
- Label placement: full `FieldDef.name` (e.g. `box24_cpt_sl1`) drawn above or below each rectangle in the overlay PNG
- Scale-corrected coordinates must pass through the calibration overlay too — overlay should reflect post-scale coords so visual alignment is accurate on any page

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 2 — Image Pipeline & Coordinate Calibration*
*Context gathered: 2026-04-29*
