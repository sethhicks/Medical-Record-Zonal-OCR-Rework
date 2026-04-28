# Feature Landscape: CMS-1500 / UB-04 OCR Extraction Tool

**Domain:** Medical billing form OCR — scanned PDF to structured Excel
**Researched:** 2026-04-28
**Overall confidence:** HIGH (grounded in CMS-1500/UB-04 form specifications, billing workflow knowledge, and OCR tooling patterns)

---

## Table Stakes

Features billing staff require for the tool to be usable. Missing any of these = the tool fails to replace manual re-entry.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| All billing-critical fields extracted for both form types | Staff are replacing full manual re-entry — partial extraction creates more work, not less | Medium | All boxes listed in PROJECT.md must be present as columns |
| One Excel row per physical page, correct sheet per form type | Staff verify by flipping between the PDF and the spreadsheet — row = page is the mental model | Low | Already decided; do not break this |
| Box 24 service lines flattened to SL1_–SL6_ column groups | CMS-1500 has up to 6 service lines per page; each must appear in the row without row-explosion | Medium | See Box 24 section below |
| Yellow cell highlighting on low-confidence fields | Staff need to know which cells to eyeball — color is faster than reading numbers | Low | Already in design; threshold default 60% is reasonable |
| Source metadata columns on every row | Staff must be able to trace any Excel value back to the exact source page | Low | Minimum: source_filename, page_number, form_type |
| Form type auto-detection per page | Mixed PDFs are the real input — staff should not pre-sort by form type | Medium | CMS-1500 and UB-04 signature strings are reliable identifiers |
| Empty-but-not-absent cell for missing fields | A blank cell means "not found"; a missing column means "we forgot it" — staff cannot tell the difference | Low | Every defined field must have a column even if OCR returns nothing |
| Graceful handling of unreadable pages | A page that fails OCR must produce a row with all blank field cells, not crash or skip the page | Low | Row must include source metadata so staff know the page exists |
| Processing progress visible to user | ~100 pages at 300 DPI + Tesseract is 2–5 minutes; no feedback = staff assume it hung | Low | Per-page progress bar already in design |
| Output file opened from app on completion | Staff should not hunt for where the file was saved | Low | Already in design |

---

## Differentiators

Features that make the tool meaningfully better than a bare extraction dump. Not expected on day one, but high value once core extraction is solid.

### Tier 1 — High value, low complexity (build after core extraction works)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Format validation on known-structure fields | Catches OCR misreads that are plausible-looking but wrong (e.g., "O" read as "0" in NPI) | Low | See validation targets below |
| Average confidence column per row | Lets staff sort by worst-confidence rows first for review, rather than scanning all yellow cells | Low | `=AVERAGE(confidence_fields)` computed at write time, not in Excel |
| Low-confidence field count column per row | Quick triage: rows with 0 low-confidence fields need no review; rows with 10+ need full review | Low | Count of fields below threshold, per row |
| Run summary sheet in the same workbook | One-tab overview: total pages, total CMS-1500, total UB-04, total low-confidence cells, pages with errors | Low | Staff use this to decide whether the batch needs extra review time |
| Processing log file (per run) | Plaintext log alongside the Excel: which PDFs, how many pages, any failures, timestamp | Low | Required for basic operational traceability; see Audit section below |
| Extraction timestamp column | Every row records when it was extracted — useful when staff reprocess a corrected scan | Low | ISO 8601, per-run granularity is sufficient (not per-page) |

### Tier 2 — High value, medium complexity (plan for a later phase)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Duplicate claim detection within a batch | Flags when the same claim number (Box 26 / Box 3b) appears on more than one page in the same run | Medium | Catches duplicate-scan errors before submission; implemented as a post-processing pass over the completed sheet |
| Confidence-score column per field (optional display) | Lets power users see exact Tesseract confidence, not just yellow/not-yellow | Medium | Add as hidden columns that staff can unhide; do not clutter the default view |
| Multi-page CMS-1500 claim grouping indicator | When a claim spans two physical pages, a "continued" marker helps staff verify they have both pages | Medium | A `continuation_of_page` column pointing to the prior row; already referenced in PROJECT.md |
| Configurable confidence threshold | Different billing teams have different error tolerance — 60% default, adjustable via settings file | Low-Med | Store in a config file, not a UI slider; changing it requires a re-run |

### Tier 3 — Nice to have (only if explicitly requested)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Per-field confidence columns surfaced by default | Some teams want to see the number, not just the color | Medium | Makes the sheet very wide; hide by default |
| ICD/CPT code lookup validation | Confirm extracted codes exist in the current code set | High | Requires maintaining a local code reference database — significant ongoing maintenance burden |
| Batch comparison (current run vs prior run) | Detect if the same PDF was reprocessed with different results | High | Useful but out of scope for a single-user desktop tool |

---

## Anti-Features

Things that would over-engineer this tool relative to its purpose, user base, and deployment model.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| In-app field editing / correction UI | The project decision is "Excel is the review surface" — building a correction UI duplicates Excel and increases app scope by 3x | Let staff correct directly in Excel; it is already the output format |
| Database output or database backend | Staff want an Excel file they can email, open in Teams, or archive — a database requires installation and admin | Excel is the correct output; add a summary sheet if more structure is needed |
| Full ICD-10/CPT/HCPCS code validation against live code sets | Requires maintaining a versioned code database, handling annual updates, and dealing with crosswalks — a feature with ongoing ops cost | Do format-pattern validation only (ICD-10 pattern, CPT is 5 digits); surfacing the code for human review is sufficient |
| Web or cloud deployment | Out of scope per PROJECT.md; adds auth, hosting, HIPAA BAA surface area | Desktop only |
| Machine learning confidence calibration | Tesseract provides raw confidence; re-calibrating it adds complexity without a clear accuracy gain at this volume | Use Tesseract confidence directly, with a configurable threshold |
| Auto-correction of extracted values | Any auto-correction that is wrong silently introduces errors into billing submissions — the liability risk is severe | Always surface the raw OCR value; flag uncertainty with color; never silently alter |
| Configurable field mapping via UI | All forms are fixed-layout NUCC/NUBC government forms — field positions do not vary; a UI to remap coordinates adds scope with no real-world need | Hardcode field coordinates; make them editable in a developer config file only |
| Email or EHR integration | Pushing results into a billing system requires a separate integration project | Produce the Excel file; staff import it as they do today |
| Multi-user / concurrent processing | Out of scope per PROJECT.md | Single-user desktop; no locking or queuing needed |

---

## Box 24 Service Lines — Excel Layout

CMS-1500 Box 24 contains up to 6 service lines, each with 10 sub-fields. With one-row-per-page, the standard approach is **column-group flattening**: prefix each sub-field with the line number.

**Column naming convention:**

```
SL1_date_from    SL1_date_to    SL1_pos    SL1_emg    SL1_cpt    SL1_modifier
SL1_diag_ptr     SL1_charges    SL1_units  SL1_rendering_npi

SL2_date_from    SL2_date_to    ...

...through SL6_*
```

This produces 60 columns for service line data (6 lines × 10 fields). That is wide but correct — each column maps cleanly to a known field, enabling Excel filtering/sorting by CPT code across all rows.

**Do not use row-explosion (one row per service line):** It breaks the one-row-per-page mental model, requires a multi-level index, and makes the form-type sheets asymmetric.

**Empty service lines:** If a page has only 3 service lines filled, SL4_–SL6_* columns are blank. This is expected and correct.

**UB-04 Revenue Lines (Box 42–48):** UB-04 revenue lines are variable in count (can exceed 6). The practical approach is to capture up to a configurable maximum (default 22, the physical limit of the printed form) using the same prefix pattern: `RL1_rev_code`, `RL1_hcpcs`, `RL1_service_date`, `RL1_units`, `RL1_total_charges`, `RL1_noncovered_charges`. Rows with fewer lines leave higher-numbered columns blank.

---

## Output Metadata — Standard Useful Columns

Every row in both sheets should include these metadata columns, placed at the left of the sheet (before field columns) so they are always visible without scrolling.

| Column | Type | Purpose | Notes |
|--------|------|---------|-------|
| `source_filename` | String | Traces row back to source PDF | Basename only, not full path — paths are machine-specific |
| `page_number` | Integer | Page number within source PDF (1-indexed) | Essential for staff to open the PDF and verify |
| `form_type` | String | "CMS-1500" or "UB-04" | Redundant (they're on separate sheets) but useful when staff copy rows across sheets |
| `extraction_timestamp` | String | ISO 8601 datetime of the processing run | Per-run granularity (not per-page) — stamp set at run start |
| `avg_confidence` | Float | Mean Tesseract confidence across all extracted fields on this page | Enables sort-by-confidence for review triage |
| `low_confidence_count` | Integer | Number of fields below threshold on this page | Quick scan: 0 = no review needed, high = review carefully |
| `extraction_error` | String | Empty if clean; error message if page failed to process | Ensures failed pages are visible, not silently dropped |

**Claim grouping for multi-page CMS-1500 (recommended Tier 2):**

| Column | Type | Purpose |
|--------|------|---------|
| `claim_number` | String | Box 26 (Patient Account No.) — used to link continuation pages |
| `is_continuation` | Boolean | True if this page contains "CONTINUED ON NEXT PAGE" text |

---

## Format Validation Targets (Tier 1 Differentiator)

Implement as a post-extraction pass. Write validated values unchanged; add a `_valid` boolean column alongside each validated field, or (simpler) apply a distinct cell color (e.g., orange) for format-invalid values.

| Field | Validation Rule | Common OCR Error It Catches |
|-------|----------------|----------------------------|
| NPI (all NPI fields) | Exactly 10 digits, Luhn check optional | "O" misread as "0", truncated digits |
| ICD-10-CM codes (Box 21 A–L) | Regex: `[A-Z]\d{2}\.?\w{0,4}` | Missing letter prefix, decimal misread |
| CPT/HCPCS codes (Box 24E) | Regex: `\d{5}` or `[A-V]\d{4}` | Truncated to 4 digits, space inserted |
| Dates (all date fields) | Valid MM/DD/YYYY, not future, not before 1900 | "0" read as "O", impossible dates |
| ZIP codes | 5 digits or 5+4 format | Truncated, alpha characters |
| Federal Tax ID (Box 25) | 9 digits (EIN format XX-XXXXXXX) | Dash misread or dropped |
| Type of Bill (UB-04 Box 4) | 3 or 4 digits | Leading zero dropped |
| Revenue codes (UB-04 Box 42) | 4 digits, leading zero | Same as above |

Mark validation failures with orange cell fill (distinct from yellow = low confidence) so staff can distinguish "OCR was uncertain" from "OCR returned something that cannot be right."

---

## Audit and Logging Requirements

**Applicable compliance context:** HIPAA Security Rule requires covered entities and business associates to track access to PHI. A single-user desktop tool that reads scanned PHI and writes it to a local Excel file is within scope. However, the tool itself is not a "system" that stores PHI — it is a transient processor. The Excel output is the covered record.

**What is required:** A processing log that records what was processed, when, and by whom (username). This supports:
- Breach investigation (which PDFs were accessed, when)
- Error investigation (why did page 47 produce blanks)
- Operational QA (did the reprocessed batch differ from the original)

**Recommended log format — plaintext `.log` file, written alongside the Excel output:**

```
[2026-04-28T14:23:01] Run started by: WORKSTATION\jsmith
[2026-04-28T14:23:01] Input files (3): claims_batch_042.pdf, claims_batch_043.pdf, claims_batch_044.pdf
[2026-04-28T14:23:01] Confidence threshold: 60%
[2026-04-28T14:24:47] Processed: claims_batch_042.pdf — 34 pages (22 CMS-1500, 12 UB-04), 8 low-confidence pages
[2026-04-28T14:26:03] Processed: claims_batch_043.pdf — 28 pages (28 CMS-1500, 0 UB-04), 3 low-confidence pages
[2026-04-28T14:26:03] ERROR: claims_batch_043.pdf page 17 — OCR returned empty; page written with blanks
[2026-04-28T14:27:41] Processed: claims_batch_044.pdf — 41 pages (14 CMS-1500, 27 UB-04), 12 low-confidence pages
[2026-04-28T14:27:41] Run complete. Output: C:\Users\jsmith\billing\2026-04-28_claims.xlsx
[2026-04-28T14:27:41] Totals: 103 pages, 64 CMS-1500 rows, 39 UB-04 rows, 23 low-confidence pages, 1 extraction error
```

**What is NOT required at this scope:**
- Field-level change logging (what value was written to each cell) — the Excel file is the record
- User authentication or access control — single-user desktop, Windows session = identity
- Log encryption — logs contain operational metadata, not field values; no PHI in the log itself
- Log rotation or retention enforcement — an organizational policy question, not a tool responsibility

**Log filename convention:** `{output_basename}_{timestamp}.log` in the same directory as the Excel output.

---

## MVP Feature Set (Phase 1 Recommendation)

Build exactly this. Nothing less (unusable), nothing more (over-scope).

**Must have in MVP:**
1. Form type detection (CMS-1500 vs UB-04) per page
2. All billing-critical field extraction for both form types
3. Box 24 service lines SL1–SL6 column groups
4. UB-04 revenue lines RL1–RL22 column groups
5. Source metadata columns (source_filename, page_number, form_type, extraction_timestamp)
6. Yellow cell highlighting for fields below confidence threshold
7. avg_confidence and low_confidence_count columns per row
8. extraction_error column (blank when clean)
9. Graceful handling of unreadable pages (blank row, not crash)
10. Progress bar during processing
11. Open-output-file button on completion
12. Processing log file written alongside Excel output

**Defer to Phase 2:**
- Format validation (orange highlighting for format-invalid fields)
- Duplicate claim detection
- Run summary sheet
- Multi-page CMS-1500 continuation linking
- Configurable confidence threshold (hardcode at 60% for MVP)

**Never build (anti-features above):**
- In-app editing, database output, auto-correction, live code validation, EHR integration

---

## Sources

- CMS-1500 form specification: NUCC Instruction Manual, v. 7.0 (National Uniform Claim Committee)
- UB-04 form specification: NUBC Uniform Billing Manual (National Uniform Billing Committee)
- HIPAA Security Rule audit logging guidance: 45 CFR §164.312(b) — Audit controls
- Field format rules: CMS Provider Enrollment, Chain, and Ownership System (PECOS) NPI registry format; ICD-10-CM tabular list structure; AMA CPT code format specification
- Confidence: HIGH — all field specifications and form structures are from authoritative government/standards body sources; billing workflow analysis is from domain knowledge of billing staff re-entry workflows
