# Phase 5: Output & Excel Export - Context

**Gathered:** 2026-05-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a writer module that accepts extracted `list[FieldResult]` per page and produces a formatted openpyxl Excel workbook — two sheets ("CMS-1500", "UB-04"), one row per physical page, human-readable column headers derived from `FieldDef.label`, yellow fill for low-confidence cells, text format for code/date/monetary columns, saved as `extracted_results.xlsx` in the configured output directory. No detection, no extraction, no UI — pure output formatting.

</domain>

<decisions>
## Implementation Decisions

### Column Headers
- **D-01:** Single-field column headers use `FieldDef.label` (e.g., "Claim/Member ID", "Box 1 Insurance Type"). When `label` is empty string (default), fall back to `FieldDef.name` — no empty column headers allowed.
- **D-02:** CMS-1500 service-line column headers: `{TableFieldDef.label} SL{N}` — e.g., "Date From SL1", "CPT SL1", "Rendering NPI SL6". Six service-line blocks always present even when blank.
- **D-03:** UB-04 revenue-line column headers: `{TableFieldDef.label} RL{N}` — e.g., "Rev Code RL1", "Description RL1", "Non-Covered RL22". Twenty-two revenue-line blocks always present even when blank.
- **D-04:** Same label-fallback rule applies to `TableFieldDef.label` — fall back to `TableFieldDef.name` if label is empty.

### Output File Path
- **D-05:** Output filename is always `extracted_results.xlsx`, saved in `settings['output_dir']` (default: Desktop — `config_loader._DEFAULTS['output_dir']`). Silent overwrite on each run; no timestamp suffix, no input-name prefix.
- **D-06:** Writer function returns the full output path as a `str` so Phase 6's "Open output file" button can open it without reconstructing the path.

### Text-Format Columns
- **D-07:** Columns matching OUT-05 are formatted as text (`@` number format): all NPI fields, CPT/HCPCS fields, ICD code fields (box21a–l, UB-04 diagnosis/procedure codes), ZIP fields, tax ID fields.
- **D-08:** Additionally, date and monetary fields are text-formatted to prevent Excel silent auto-conversion:
  - **CMS-1500 dates:** `box3_dob`, `box24_date_from_slN`, `box24_date_to_slN` (all 6 rows)
  - **CMS-1500 monetary:** `box28_total_charge`, `box29_amount_paid`
  - **UB-04 dates:** `box6_stmt_from`, `box6_stmt_through`, `box12_admission_date`, all revenue-line service date columns
  - **UB-04 monetary:** all revenue-line total-charge and non-covered-charge columns
- **D-09:** Text format is identified by matching field `name` substrings — e.g., contains "npi", "cpt", "zip", "tax", "icd", "dob", "date", "charge", "amount", "paid", "stmt", "hcpcs", "zip". Planner should compile the exact match set from the full field lists in `config/cms1500.py` and `config/ub04.py`.

### Source Metadata
- **D-10:** No metadata columns in Phase 5. `source_filename`, `page_number`, `form_type`, and `extraction_timestamp` remain deferred to v2 (META-01 in REQUIREMENTS.md). Billing staff use claim-native fields as row identifiers: Claim/Member ID for CMS-1500, Patient Control Number (`box3b_patient_ctrl_num`) for UB-04.

### Claude's Discretion
- **Writer module location:** `pipeline/writer.py` (consistent with existing pipeline pattern) or a new `output/` package — planner's call based on whether Phase 6 benefits from a separate package boundary.
- **Function signature shape:** `write_workbook(cms_pages: list[list[FieldResult]], ub_pages: list[list[FieldResult]], settings: dict) -> str` is the expected shape; planner may adjust parameter names or structure.
- **UNKNOWN page handling:** Pages classified as UNKNOWN are not passed to the Phase 5 writer (Phase 6 handles error rows per UI-04). Writer only receives pre-sorted CMS-1500 and UB-04 page result lists.
- **Frozen header row:** Add `freeze_panes` at row 2 so the header row stays visible when scrolling — standard for billing-staff Excel usability.
- **Column width:** Auto-fit or set a reasonable default width (e.g., 15) for all columns — avoids unreadable collapsed columns on first open.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Requirements
- `.planning/REQUIREMENTS.md` — OUT-01 through OUT-05 (full v1 acceptance criteria for this phase); META-01 (v2, deferred — do not implement)
- `.planning/ROADMAP.md` §Phase 5 — 5 success criteria defining exactly what must be true when this phase is complete

### Project Context
- `.planning/PROJECT.md` — complete field lists for CMS-1500 (all Box 1–Box 33 sub-fields) and UB-04 (Box 1–Box 76); context on billing staff use case
- `config_loader.py` — `load_settings()` provides `confidence_threshold` (default 60%) and `output_dir` (default Desktop); writer reads both

### Field Coordinate Definitions (read to build header tables)
- `config/cms1500.py` — `CMS1500_FIELDS` (29 FieldDef with `.label`) + `CMS1500_TABLE_FIELDS` (10 TableFieldDef, 6 rows each); iterate both to build the full CMS-1500 header list in correct order
- `config/ub04.py` — `UB04_FIELDS` (24 FieldDef with `.label`) + `UB04_TABLE_FIELDS` (7 TableFieldDef, 22 rows each); iterate both to build the full UB-04 header list
- `config/base.py` — `FieldDef.label` and `TableFieldDef.label` schema; `label` defaults to `""` — fallback to `.name` when empty

### Data Models
- `models/field_result.py` — `FieldResult(field_name, value, confidence)`; `field_name` is the key for column lookup; `confidence` compared against threshold for yellow fill; `-1.0` means no text found (treat as below threshold)

### Prior Phase Context
- `.planning/phases/04-field-extraction-cms-1500-ub-04/04-CONTEXT.md` — D-06/D-07: field naming conventions (`box24_date_from_sl1..sl6`, `rev_code_rl1..rl22`); D-10/D-11: confidence aggregation and -1.0 sentinel; D-09: both extractors re-exported from `pipeline/__init__.py`
- `pipeline/__init__.py` — Current exports: `convert_page`, `preprocess_page`, `detect_form_type`, `extract_cms1500`, `extract_ub04`; Phase 5 adds writer export

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `config.cms1500.CMS1500_FIELDS` — iterate for single-field headers: `header = fd.label or fd.name`
- `config.cms1500.CMS1500_TABLE_FIELDS` — iterate for service-line headers: `f"{tfd.label or tfd.name} SL{i+1}"` for i in range(6)
- `config.ub04.UB04_FIELDS` + `UB04_TABLE_FIELDS` — same pattern, `RL{i+1}` suffix
- `config_loader.load_settings()` — returns `confidence_threshold` and `output_dir`
- `openpyxl` — already a project dependency for Excel output (Phase 1 stack)

### Established Patterns
- Stateless functions: extractors take `(image, settings)`, return list — writer should follow same pattern: `write_workbook(cms_pages, ub_pages, settings) -> str`
- Windows-explicit paths: `output_dir` from settings may be a Windows path; use `pathlib.Path` for cross-segment joins
- Test file naming: `tests/test_phase5.py` — one file per phase, stubs-first Wave 0 pattern

### Integration Points
- Phase 6 collects: `form_type = detect_form_type(raw)` → routes page results to `cms_pages` or `ub_pages` list → calls `write_workbook(cms_pages, ub_pages, settings)` → receives output path → wires to "Open output file" button
- `FieldResult.confidence == -1.0` means no text found — treat as below threshold (yellow fill)
- Yellow fill: `openpyxl.styles.PatternFill(fill_type="solid", fgColor="FFFF00")`
- Text number format: `cell.number_format = "@"`

</code_context>

<specifics>
## Specific Ideas

- Header row frozen at row 2 (`freeze_panes = "A2"`) so billing staff can scroll data while keeping headers visible
- Default column width of ~15 units to prevent collapsed columns on first open
- Writer returns the full output path (`str`) so Phase 6 can open it with `os.startfile(path)` (Windows) without reconstructing

</specifics>

<deferred>
## Deferred Ideas

### Coordinate re-tuning & OCR accuracy pass
User raised during Phase 5 discussion: zone accuracy and OCR scan accuracy still need improvement. Known gaps from Phase 4:
- `box21a` reads 'TAX9' not 'I96' (whitelist OCR noise)
- Many single fields still return noisy/empty results
- UB-04 revenue-line column coordinates unverified

This should be a dedicated calibration pass — a new plan added to Phase 4 or a dedicated phase 4.5 — before Phase 5 output is used for production review. Added to `.planning/BACKLOG.md`.

</deferred>

---

*Phase: 5 — Output & Excel Export*
*Context gathered: 2026-05-06*
