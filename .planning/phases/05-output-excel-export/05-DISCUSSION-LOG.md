# Phase 5: Output & Excel Export - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-06
**Phase:** 05-output-excel-export
**Areas discussed:** Column header format, Output filename convention, Text-format column scope, Source metadata columns

---

## Column Header Format

| Option | Description | Selected |
|--------|-------------|----------|
| OUT-02/03 spec exactly | SL1_date_from, SL6_rendering_npi, RL1_rev_code style — matches requirements text | |
| Raw field names as-is | box24_date_from_sl1, rev_code_rl1 — no transform, looks like internal codes | |
| Human-readable labels | FieldDef.label + SL/RL suffix — "Date From SL1", "CPT SL1", "Rev Code RL1" | ✓ |

**User's choice:** Human-readable labels using FieldDef.label / TableFieldDef.label
**Follow-up — empty label fallback:**

| Option | Description | Selected |
|--------|-------------|----------|
| Fall back to field_name | Use field_name when label is empty — guarantees no blank headers | ✓ |
| Fail loudly | Raise error if any FieldDef missing a label | |

**Notes:** Billing staff usability drove the choice — "Claim/Member ID" is more recognizable than "claim_member_id". Fallback to field_name prevents silent broken headers if any label was missed in config.

---

## Output Filename Convention

| Option | Description | Selected |
|--------|-------------|----------|
| Timestamp in output_dir | ocr_output_YYYYMMDD_HHMMSS.xlsx — new file per run, no overwrites | |
| Fixed name in output_dir | extracted_results.xlsx always in output_dir — simple, overwrites previous | ✓ |
| Input PDF stem + _extracted | {stem}_extracted.xlsx alongside input — problematic for multi-PDF runs | |

**User's choice:** Fixed name `extracted_results.xlsx` in `settings['output_dir']` (default Desktop), silent overwrite each run.
**Notes:** Billing staff always know where to look — Desktop, same filename every time. No accumulation of old files. Phase 6's "Open output file" button always targets the same path.

---

## Text-Format Column Scope

| Option | Description | Selected |
|--------|-------------|----------|
| OUT-05 + dates + amounts | Add date and monetary fields to prevent Excel silent auto-conversion | ✓ |
| OUT-05 list only | Exactly as written: NPI, CPT, ICD, ZIP, tax ID | |
| All columns as text | Format everything as text — safest, trades away numeric sorting | |

**User's choice:** Expand to OUT-05 + date fields (DOB, service dates, admission dates, statement period) + monetary fields (charges, amount paid).
**Notes:** Risk of silent corruption (e.g., "01/15/25" → Excel date serial) outweighs the benefit of keeping dates as general format. OCR output is always a raw string anyway — there's no benefit to Excel parsing it as a number.

---

## Source Metadata Columns

| Option | Description | Selected |
|--------|-------------|----------|
| source_filename + page_number only | Two metadata columns at row front — minimal v1 traceability | |
| No metadata (rely on claim data) | Claim/Member ID and Patient Control Number as natural identifiers | ✓ |
| All 4 META-01 columns now | Promote META-01 to v1 scope — full audit trail | |

**User's choice:** No metadata columns. Rely on claim-native fields. META-01 stays deferred to v2.
**Notes:** User then raised OCR accuracy concerns (see Deferred Ideas below).

---

## Claude's Discretion

- **Writer module location:** `pipeline/writer.py` vs new `output/` package — planner decides based on scope
- **Function signature:** `write_workbook(cms_pages, ub_pages, settings) -> str` — planner may adjust
- **UNKNOWN page handling:** Writer only receives pre-sorted CMS-1500 and UB-04 lists; Phase 6 handles UNKNOWN pages
- **Frozen header row:** `freeze_panes = "A2"` — standard usability for scrollable data
- **Column width:** Default ~15 units to prevent collapsed columns on first open
- **Text-format column identification:** Substring matching on field names — planner compiles exact set from config

## Deferred Ideas

### Coordinate re-tuning & OCR accuracy pass
User raised: zone accuracy and OCR scan accuracy still need improvement before the output is useful for production review. Known gaps: `box21a` whitelist noise, many noisy single fields, UB-04 revenue-line coords unverified. This is a Phase 4 / Phase 2 concern, not Phase 5. Added to `.planning/BACKLOG.md` as a calibration backlog item.
