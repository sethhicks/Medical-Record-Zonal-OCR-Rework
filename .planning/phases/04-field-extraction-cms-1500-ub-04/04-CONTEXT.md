# Phase 4: Field Extraction — CMS-1500 & UB-04 - Context

**Gathered:** 2026-05-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Build `pipeline/extractor_cms1500.py` and `pipeline/extractor_ub04.py` — stateless functions that accept a preprocessed PIL Image and a settings dict, crop each field region using the coordinates in `config/cms1500.py` / `config/ub04.py`, call Tesseract with the field's configured PSM mode and character whitelist, and return a `list[FieldResult]` with `field_name`, `value`, and `confidence` for every field (including blank rows). No form detection, no Excel output, no UI — pure extraction.

</domain>

<decisions>
## Implementation Decisions

### ICD-10 Dot Format
- **D-01:** ICD-10 codes retain the decimal dot — store as `F32.9`, not `F329`. Standard clinical notation; billing staff expect this format in the Excel output.
- **D-02:** ICD-10 whitelist for `box21a` through `box21l` (CMS-1500) and all UB-04 diagnosis code fields: `"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789. "` — update the existing entries in `config/cms1500.py` (currently `"0123456789. "`, missing the alpha prefix needed for ICD-10-CM codes like `F32.9`).
- **D-03:** CPT/HCPCS whitelist (`box24_cpt` column on CMS-1500): `"0123456789- "` — digits and hyphen only. Modifiers go in the separate Modifier column; the CPT cell is purely numeric per Roadmap SC-4.
- **D-04:** UB-04 Box 66–75: diagnosis code fields use `"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789. "` (ICD-10-CM); procedure code fields use `"0123456789"` (ICD-10-PCS is all-numeric).

### Extractor Return Shape
- **D-05:** Both `extract_cms1500(image, settings)` and `extract_ub04(image, settings)` return `list[FieldResult]` — a flat list, one entry per field (or per row of a table field). No wrapper dataclass, no dict. Phase 5 identifies fields by `FieldResult.field_name`.
- **D-06:** Box 24 service line naming: `{TableFieldDef.name}_sl{row_index}` — e.g., `box24_date_from_sl1` through `box24_date_from_sl6`, `box24_cpt_sl1` through `box24_cpt_sl6`. Six rows always returned even when blank.
- **D-07:** UB-04 revenue line naming: `{TableFieldDef.name}_rl{row_index}` — e.g., `rev_code_rl1` through `rev_code_rl22`, `hcpcs_rl1` through `hcpcs_rl22`. Twenty-two rows always returned even when blank.

### Module Structure
- **D-08:** Split into two separate modules: `pipeline/extractor_cms1500.py` and `pipeline/extractor_ub04.py`. CMS-1500 has 29 single fields + 60 table cells; UB-04 has 24 single fields + 154 revenue-line cells — keeping them separate avoids a 600+ line file and mirrors the existing one-concern-per-file pattern in `pipeline/`.
- **D-09:** Both functions re-exported from `pipeline/__init__.py` alongside the existing exports: `from pipeline import extract_cms1500, extract_ub04`. Phase 5/6 use this import path.

### Confidence Aggregation
- **D-10:** Multi-word field confidence = **minimum** confidence across all words returned by `image_to_data()`. Conservative: if any word in a multi-line field (e.g., Box 5 Patient Address, Box 33 Billing Provider) is uncertain, the whole field is flagged yellow. Safer for compliance review.
- **D-11:** When a table row region contains no text (blank service line or revenue line): `FieldResult(field_name=..., value="", confidence=-1.0)` — reuses the existing convention defined in `models/field_result.py` (comment: `-1.0 if no text found in region`).

### Claude's Discretion

- **Confidence threshold calibration:** Run extraction against `test.pdf`, inspect the confidence distribution, confirm whether the 60% default separates clean reads from noise. Log any adjustment in `STATE.md` open decisions. This is the explicit calibration step flagged in STATE.md.
- `image_to_data()` vs `image_to_string()`: Use `image_to_data()` throughout (needed for per-word confidence). `image_to_string()` is simpler but returns no confidence.
- Whether to apply grayscale conversion to cropped regions before Tesseract (the preprocessed image is already thresholded, so this may be redundant).
- Error handling within a single field crop: if `image_to_data()` raises, return `FieldResult(field_name=..., value="", confidence=-1.0)` rather than propagating the exception (Phase 6 surfaces per-page errors, not per-field).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Requirements
- `.planning/REQUIREMENTS.md` — EXTR-01, EXTR-02, EXTR-03 are the requirements for this phase; full acceptance criteria text lives here
- `.planning/ROADMAP.md` §Phase 4 — 5 success criteria define exactly what must be true when this phase is complete (≥80% non-empty fields on CMS-1500 and UB-04 pages from test.pdf; confidence on every result; NPI/CPT/ICD-10 whitelist enforcement; 6 service line groups always returned)

### Project Context
- `.planning/PROJECT.md` — Complete field lists for CMS-1500 (Claim/Member ID, Box 1–Box 33) and UB-04 (Box 1–Box 76); technical approach; out-of-scope items
- `.planning/STATE.md` — ICD-10 dot format resolved here (keep dot, F32.9); confidence threshold open decision; output filename convention (still pending for Phase 6)

### Prior Phase Context (critical for integration)
- `.planning/phases/03-form-detection/03-CONTEXT.md` — D-08/D-09: `detect_form_type` exported from `pipeline/`; Phase 4 calls detect on raw image, then preprocess_page on same raw image before extraction. D-06: UNKNOWN form type produces error row — Phase 4 does NOT handle UNKNOWN pages.

### Existing Code (read before planning)
- `config/base.py` — `FieldDef(name, box, psm, whitelist, label)` and `TableFieldDef(name, row_boxes, psm, whitelist, label)`; understand their schema before iterating fields
- `config/cms1500.py` — `CMS1500_FIELDS` (29 FieldDef) + `CMS1500_TABLE_FIELDS` (10 TableFieldDef, 6 rows each); **NOTE: box21a–l whitelist must be updated from `"0123456789. "` to `"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789. "` per D-02**
- `config/ub04.py` — `UB04_FIELDS` (24 FieldDef) + `UB04_TABLE_FIELDS` (7 TableFieldDef, 22 rows each)
- `models/field_result.py` — `FieldResult(field_name, value, confidence)`; confidence = -1.0 means no text found
- `pipeline/__init__.py` — Current exports: `convert_page`, `preprocess_page`, `detect_form_type`; Phase 4 adds `extract_cms1500`, `extract_ub04`
- `config_loader.py` — `load_settings()`; returns `confidence_threshold` (default 60%) which Phase 5 uses for yellow highlighting; Phase 4 may read it for calibration

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `config.cms1500.CMS1500_FIELDS` — iterate to extract each single-value field: `for fd in CMS1500_FIELDS: crop = image.crop(fd.box); run OCR with fd.psm, fd.whitelist`
- `config.cms1500.CMS1500_TABLE_FIELDS` — iterate rows: `for tfd in CMS1500_TABLE_FIELDS: for i, box in enumerate(tfd.row_boxes): field_name = f"{tfd.name}_sl{i+1}"`
- `config.ub04.UB04_FIELDS` + `UB04_TABLE_FIELDS` — same pattern; revenue line suffix is `_rl{i+1}`
- `pipeline.convert_page` → raw image; `pipeline.preprocess_page(raw, settings)` → preprocessed image for extraction
- `pipeline.detect_form_type` → dispatches to correct extractor

### Established Patterns
- Windows-explicit binary paths: `pytesseract.pytesseract.tesseract_cmd = settings['tesseract_cmd']` before any OCR call — required on Windows
- Stateless functions: extractors take `(image, settings)`, return list; no instance state
- Test file naming: `tests/test_phase4.py` — one file per phase, stubs-first pattern (Wave 0)
- `image_to_data()` returns a dict with `'text'`, `'conf'` lists; filter `conf > 0` to exclude Tesseract's empty-segment entries

### Integration Points
- `pipeline.detect_form_type(raw_image)` → `'CMS-1500'` | `'UB-04'` | `'UNKNOWN'`
- `pipeline.preprocess_page(raw_image, settings)` → preprocessed image
- `pipeline.extract_cms1500(preprocessed_image, settings)` → `list[FieldResult]`
- `pipeline.extract_ub04(preprocessed_image, settings)` → `list[FieldResult]`
- Phase 5 reads `FieldResult.field_name` as Excel column key, `FieldResult.value` as cell value, `FieldResult.confidence` vs `settings['confidence_threshold']` for yellow fill

</code_context>

<specifics>
## Specific Ideas

- Full call sequence for one page: `raw = convert_page(pdf_path, page_num)` → `form_type = detect_form_type(raw)` → `proc = preprocess_page(raw, settings)` → `results = extract_cms1500(proc, settings)` (or `extract_ub04`)
- Phase 5 expects 6 service-line blocks named `box24_date_from_sl1..sl6`, `box24_cpt_sl1..sl6`, etc. as Excel column groups — the naming from D-06 maps directly to the roadmap's `SL1_date_from..SL6_rendering_npi` columns
- Phase 5 expects 22 revenue-line blocks named `rev_code_rl1..rl22`, `hcpcs_rl1..rl22`, etc. as Excel column groups

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 4 — Field Extraction — CMS-1500 & UB-04*
*Context gathered: 2026-05-03*
