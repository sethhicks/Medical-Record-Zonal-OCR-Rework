# Phase 3: Form Detection - Context

**Gathered:** 2026-05-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Build `pipeline/detector.py` — a module that classifies each converted page image as `'CMS-1500'`, `'UB-04'`, or `'UNKNOWN'` using multi-anchor string matching. Detection runs on the **raw** image from `convert_page()` (not preprocessed) for speed. The correct form-type label drives Phase 4 extractor dispatch. No field extraction, no OCR of field regions — that belongs in Phase 4.

</domain>

<decisions>
## Implementation Decisions

### Return Type & Function Signature
- **D-01:** `detect_form_type(image: PIL.Image.Image) -> str` — returns a plain string: `'CMS-1500'`, `'UB-04'`, or `'UNKNOWN'`. Matches roadmap labels exactly. No enum or wrapper type.
- **D-02:** Function is the primary public API for this phase. No class-based detector, no stateful object.

### Anchor Rules
- **D-03:** CMS-1500 classification: **2-of-3 anchors** must be found in the page. Anchors: `"HEALTH INSURANCE"`, `"NUCC Instruction Manual"`, `"FORM 1500"`. Locked by PROC-03 ("2-of-3 anchors must agree").
- **D-04:** UB-04 classification: **1-of-2 anchors** suffices. Anchors: `"NUBC"`, `"UB-04 CMS-1450"`. More forgiving — partially clipped scans that hide one footer anchor still classify correctly.
- **D-05:** If a page matches the threshold for **both** CMS-1500 and UB-04 simultaneously → `'UNKNOWN'`. Ambiguous match is an error row, not a guess.
- **D-06:** A page that matches neither form type's threshold → `'UNKNOWN'`. UNKNOWN pages produce a result the downstream pipeline writes as an error row (not silently skipped).

### Module Placement
- **D-07:** `pipeline/detector.py` — extends the existing `pipeline/` package. Consistent with `converter.py`, `preprocessor.py`, `calibrate.py` placement.
- **D-08:** `detect_form_type` re-exported from `pipeline/__init__.py` alongside `convert_page` and `preprocess_page`. Phase 4 imports via `from pipeline import detect_form_type`.
- **D-09:** Tests in `tests/test_phase3.py` — consistent with `test_phase1.py` and `test_phase2.py` naming.

### Claude's Discretion

The following are left to Claude during implementation, constrained by the decisions above and ROADMAP.md success criteria:

- Strip height for header/footer region crops before Tesseract (e.g., top 400 px for header anchors, bottom 400 px for footer anchors)
- PSM mode for detection OCR (psm 11 sparse text is likely appropriate for scattered strings)
- Whether to apply minimal grayscale conversion to the crop before Tesseract (raw PIL image vs grayscale strip)
- Case-insensitive vs exact string matching for anchors
- Whether to use `image_to_string` or `image_to_data` for the detection call

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Requirements
- `.planning/REQUIREMENTS.md` — PROC-03 is the requirement for this phase; full acceptance criteria text: "multi-anchor detection (2-of-3 anchors must agree); pages where detection is uncertain written as UNKNOWN rows"
- `.planning/ROADMAP.md` §Phase 3 — 4 success criteria define exactly what must be true when this phase is complete (CMS-1500 on 27 pages, UB-04 on 3 pages, UNKNOWN on obscured pages, UNKNOWN result object for error rows)

### Project Context
- `.planning/PROJECT.md` — Form type anchor strings (CMS-1500 and UB-04 signature text), technical approach (detect on raw image), out-of-scope items
- `.planning/STATE.md` — Open decisions (ICD-10 format, confidence threshold) that are NOT resolved yet; pipeline notes

### Phase 2 Context (critical for integration)
- `.planning/phases/02-image-pipeline-coordinate-calibration/02-CONTEXT.md` — D-14: `convert_page` and `preprocess_page` are separate specifically so Phase 3 can call `convert_page` on the raw image; D-12: pipeline module structure established here

### Existing Code (read before planning)
- `pipeline/__init__.py` — Current exports: `convert_page`, `preprocess_page`; Phase 3 adds `detect_form_type`
- `pipeline/converter.py` — `convert_page(pdf_path, page_num) -> PIL.Image.Image`; returns 2550×3300 RGB image; Phase 3 calls this to get the raw image for anchor scanning
- `config_loader.py` — `load_settings()` returns settings dict; `detect_form_type` does not need settings, but may accept them for future tuning
- `models/field_result.py` — `FieldResult` dataclass; Phase 3 does NOT produce FieldResults — just the type string

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pipeline.convert_page(pdf_path, page_num)` — call this first to get the raw PIL Image; detection runs on this before preprocessing
- `config/cms1500.py` — `CMS1500_FIELDS` and `CMS1500_TABLE_FIELDS`; Phase 3 does not use coordinates but these confirm form structure
- `config/ub04.py` — `UB04_FIELDS` and `UB04_TABLE_FIELDS`; same

### Established Patterns
- Windows-explicit binary paths: `tesseract_cmd` passed explicitly via settings; `pytesseract.pytesseract.tesseract_cmd = settings['tesseract_cmd']` before any OCR call
- Non-zero exit on validation failure: functions raise exceptions (not `sys.exit`); callers handle errors
- Test file naming: `tests/test_phase3.py` — one file per phase
- Pipeline functions are stateless: `detect_form_type(image)` takes the full PIL Image, no instance state

### Integration Points
- `pipeline.convert_page` → called by Phase 3 (raw image for anchor scanning) and Phase 4 (image before preprocessing)
- `pipeline.detect_form_type` → called by Phase 4 to dispatch to the correct field extractor
- `pipeline.preprocess_page` → called by Phase 4 AFTER detection, on the same raw image
- `'UNKNOWN'` form type → Phase 5/6 pipeline writes a blank error row with `extraction_error` column populated

</code_context>

<specifics>
## Specific Ideas

- Phase 4 usage pattern: `form_type = detect_form_type(image)` → `if form_type == 'CMS-1500': extract_cms1500(...)` — plain string comparison throughout
- Detection should be fast: scan only header/footer strips of the raw image, not full-page OCR

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 3 — Form Detection*
*Context gathered: 2026-05-01*
