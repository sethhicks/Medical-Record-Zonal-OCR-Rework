# Phase 4: Field Extraction — CMS-1500 & UB-04 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-03
**Phase:** 4 — Field Extraction — CMS-1500 & UB-04
**Areas discussed:** ICD-10 dot format, Extractor return shape, Module structure, Confidence aggregation

---

## ICD-10 Dot Format

### Q1 — Dot format choice

| Option | Description | Selected |
|--------|-------------|----------|
| Keep the dot — F32.9 | Standard clinical notation; whitelist already includes '.'; billing staff expect this format | ✓ |
| Strip the dot — F329 | Some billing systems import without dot; simpler whitelist | |
| You decide | Leave to Claude | |

**User's choice:** Keep the dot — F32.9

---

### Q2 — ICD-10 character whitelist

| Option | Description | Selected |
|--------|-------------|----------|
| A-Z + 0-9 + dot + space | Correct for ICD-10-CM; update box21a–l whitelists from digits-only to include alpha prefix | ✓ |
| Current whitelist (digits+dot only) | Keeps '0123456789. ' — would drop letter prefix, returning '32.9' instead of 'F32.9' | |
| You decide | Leave character set to Claude | |

**User's choice:** A-Z + 0-9 + dot + space
**Notes:** Current `config/cms1500.py` whitelist for box21* fields is `"0123456789. "` — missing alpha. Must be updated to `"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789. "`.

---

### Q3 — CPT/HCPCS whitelist

| Option | Description | Selected |
|--------|-------------|----------|
| Digits-only: 0-9 and hyphen | Covers standard CPT codes; modifiers go in separate column; Roadmap SC-4 specifies digits-only | ✓ |
| Alpha+digits+hyphen | Covers HCPCS Level II codes (e.g., G0439); wider but more OCR noise risk | |
| You decide | Leave to Claude | |

**User's choice:** Digits-only (0-9 and hyphen)

---

### Q4 — UB-04 code field whitelists

| Option | Description | Selected |
|--------|-------------|----------|
| Diagnosis = A-Z+digits+dot, procedure = digits-only | Matches clinical reality: ICD-10-CM has alpha prefix; ICD-10-PCS is all-numeric | ✓ |
| All UB-04 code fields use A-Z+digits+dot | Simpler, uniform; small risk of noise on numeric procedure codes | |
| You decide | Leave to Claude | |

**User's choice:** Diagnosis = A-Z+digits+dot; procedure = digits-only

---

## Extractor Return Shape

### Q1 — Return type

| Option | Description | Selected |
|--------|-------------|----------|
| list[FieldResult] — flat list | Simple; consistent with existing FieldResult dataclass; Phase 5 iterates by field_name | ✓ |
| dict[str, FieldResult] | Phase 5 looks up by key; marginal convenience over list | |
| Typed result dataclass (CMS1500Result) | Explicit, IDE-friendly; large dataclass (29+ fields + table entries) | |

**User's choice:** list[FieldResult] — flat list

---

### Q2 — Box 24 service line naming

| Option | Description | Selected |
|--------|-------------|----------|
| box24_date_from_sl1 .. sl6 | TableFieldDef.name + _sl{row}; consistent with existing FieldDef naming; Phase 5 uses as column names | ✓ |
| sl1_date_from .. sl6_date_from | Row-first; matches Phase 5 roadmap column group naming SL1_date_from..SL6_rendering_npi | |
| You decide | Leave naming to Claude | |

**User's choice:** box24_date_from_sl1 .. box24_date_from_sl6

---

### Q3 — UB-04 revenue line naming

| Option | Description | Selected |
|--------|-------------|----------|
| rev_code_rl1 .. rl22 (matches box24 pattern) | TableFieldDef.name + _rl{row}; consistent with CMS-1500 pattern; Phase 5 uses as UB-04 column names | ✓ |
| rl1_rev_code .. rl22_non_covered | Row-first; matches Phase 5 roadmap's RL1_rev_code..RL22_non_covered column groups | |
| You decide | Leave UB-04 row naming to Claude | |

**User's choice:** rev_code_rl1 .. rev_code_rl22 (field-first, matches box24 pattern)

---

## Module Structure

### Q1 — File organization

| Option | Description | Selected |
|--------|-------------|----------|
| Split: extractor_cms1500.py + extractor_ub04.py | Each file focused; avoids 600+ line combined file; mirrors pipeline/ one-concern-per-file pattern | ✓ |
| Single extractor.py with both | Simpler import surface; one file; 500–700 lines | |
| You decide | Leave to Claude | |

**User's choice:** Split — extractor_cms1500.py + extractor_ub04.py

---

### Q2 — pipeline/__init__.py exposure

| Option | Description | Selected |
|--------|-------------|----------|
| Re-export both: extract_cms1500, extract_ub04 | Consistent with convert_page, preprocess_page, detect_form_type pattern | ✓ |
| Export a dispatch function: extract_page(image, form_type, settings) | Single entry point; hides split; easier for Phase 6 batch loop | |
| You decide | Leave public API shape to Claude | |

**User's choice:** Re-export both individually

---

## Confidence Aggregation

### Q1 — Multi-word field confidence

| Option | Description | Selected |
|--------|-------------|----------|
| Minimum word confidence | Conservative: if any word uncertain, whole field flagged yellow; safer for compliance review | ✓ |
| Mean word confidence | Average quality; fewer yellow cells on longer fields | |
| You decide | Leave to Claude | |

**User's choice:** Minimum word confidence

---

### Q2 — Blank row confidence

| Option | Description | Selected |
|--------|-------------|----------|
| -1.0 (existing FieldResult convention) | Reuses convention defined in models/field_result.py; Phase 5 detects blank rows by confidence == -1.0 | ✓ |
| 0.0 (explicit zero) | More numerically distinct; breaks existing -1.0 convention | |
| You decide | Leave to Claude | |

**User's choice:** -1.0 per existing convention

---

### Q3 — Confidence threshold calibration

| Option | Description | Selected |
|--------|-------------|----------|
| Leave 60% as-is, Phase 5 surfaces results | Don't change during Phase 4; adjust after seeing real Excel output | |
| Tune during Phase 4 against test.pdf | Run extraction, check distribution, confirm 60% separates clean reads from noise | |
| You decide | Leave threshold calibration to Claude | ✓ |

**User's choice:** You decide (Claude's discretion)

---

## Claude's Discretion

- Confidence threshold calibration: run extraction against test.pdf, inspect distribution, confirm or adjust 60% default; log any change in STATE.md
- `image_to_data()` implementation details (filtering empty segments, handling Tesseract errors)
- Grayscale pre-conversion for cropped regions (image is already preprocessed/thresholded)
- Per-field error handling: whether to return `FieldResult(confidence=-1.0)` or propagate on `image_to_data()` failure

## Deferred Ideas

None — discussion stayed within phase scope.
