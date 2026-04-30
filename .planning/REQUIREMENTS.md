# Requirements — OCR Medical Billing Form Extractor

## v1 Requirements

### ENV — Environment & Setup

- [ ] **ENV-01**: Application verifies Tesseract and Poppler are installed and reachable at startup via `setup_check.py`; displays a clear error and exits if either is missing
- [ ] **ENV-02**: Application reads `settings.json` for `tesseract_cmd`, `poppler_path`, `confidence_threshold`, and `output_dir`; uses sensible defaults if file is absent

### PROC — Processing Pipeline

- [x] **PROC-01**: Application converts each PDF page to a PIL Image at exactly 300 DPI using pdf2image + Poppler
- [ ] **PROC-02**: Application applies OpenCV preprocessing to each page image: bounding-box detection for scale correction, deskew via warp affine, and adaptive threshold (Gaussian, block size tunable) for grey-band removal in Box 24 regions
- [ ] **PROC-03**: Application auto-detects form type (CMS-1500 vs UB-04) for each page using multi-anchor detection (2-of-3 anchors must agree); pages where detection is uncertain are written as UNKNOWN rows rather than silently misclassified
- [ ] **PROC-04**: Application processes multiple PDF files in a single run; all pages from all input files flow through the same pipeline

### EXTR — Field Extraction

- [ ] **EXTR-01**: Application extracts all billing-critical CMS-1500 fields using fixed pixel-region crops with per-field Tesseract PSM modes and character whitelists:
  - Claim/Member ID, Box 1 (insurance type), Box 1a (Insured ID), Box 2 (patient name), Box 3 (DOB, sex), Box 5 (address), Box 17 (referring provider name + qualifier), Box 17b (referring provider NPI), Box 19 (additional claim info), Box 21 (diagnosis codes A–L), Box 23 (prior auth number), Box 24 service lines 1–6 (date from/to, place of service, EMG, CPT/HCPCS, modifier, diagnosis pointer, charges, days/units, rendering provider NPI), Box 25 (federal tax ID, SSN/EIN), Box 26 (patient account no.), Box 27 (accept assignment), Box 28 (total charge), Box 29 (amount paid), Box 32 (service facility name + address), Box 33 (billing provider name + address + phone + NPI)
- [ ] **EXTR-02**: Application extracts all billing-critical UB-04 fields using fixed pixel-region crops:
  - Box 1 (provider name/address), Box 3b (patient control number), Box 4 (type of bill), Box 5 (federal tax number), Box 6 (statement covers period from/through), Box 8 (patient name), Box 9 (patient address), Box 10 (birthdate), Box 11 (sex), Box 12 (admission date), Box 14 (type of admission), Box 17 (patient status), revenue lines 1–22 (rev code, description, HCPCS, service date, units, total charges, non-covered charges), Box 50 (payer name), Box 51 (health plan ID), Box 54 (prior payments), Box 55 (est. amount due), Box 56 (NPI), Box 58 (insured name), Box 60 (insured unique ID), Box 61 (group name), Box 63 (treatment auth codes), Box 64 (document control number), Box 66–75 (diagnosis + procedure codes), Box 76 (attending provider NPI + name)
- [ ] **EXTR-03**: Application captures Tesseract confidence score for every extracted field; each `FieldResult` carries a numeric confidence value (0–100)
- [ ] **EXTR-04**: A coordinate calibration script renders any PDF page with all configured field regions drawn as labelled rectangles, allowing visual verification of pixel coordinates before extractor code is deployed

### OUT — Output

- [ ] **OUT-01**: Application exports results to an Excel workbook with two sheets: "CMS-1500" and "UB-04"; one row per physical PDF page; columns are fixed per sheet (all fields always present, blank if not extracted)
- [ ] **OUT-02**: CMS-1500 sheet Box 24 service lines are flattened as `SL1_date_from`, `SL1_cpt`, … `SL6_rendering_npi` column groups (not row explosion)
- [ ] **OUT-03**: UB-04 sheet revenue lines are flattened as `RL1_rev_code`, `RL1_description`, … `RL22_non_covered` column groups
- [ ] **OUT-04**: Cells where OCR confidence is below the configured threshold (default 60%) are highlighted with a yellow fill; all other cells are unstyled
- [ ] **OUT-05**: Code-type columns (CPT, NPI, ICD codes, ZIP, tax ID) use text number format (`@`) to preserve leading zeros

### UI — User Interface

- [ ] **UI-01**: Desktop GUI allows user to select one or more PDF files via a standard file-picker dialog (filter: `*.pdf`)
- [ ] **UI-02**: A progress bar and page counter update during processing; UI remains responsive (worker runs on a background thread)
- [ ] **UI-03**: On completion, a button opens the output Excel file directly in the system default application
- [ ] **UI-04**: Pages that fail processing (conversion error, extraction exception) appear as blank rows with an `extraction_error` column populated; errors are displayed in the UI after the run

---

## v2 Requirements

*Deferred — not in v1 scope.*

- **META-01**: Source metadata columns on every row: `source_filename`, `page_number`, `form_type`, `extraction_timestamp`
- **META-02**: Processing log file written alongside the Excel output (input files, page counts, errors, run timestamp) for audit trail
- **VAL-01**: Post-extraction format validation pass: cells where extracted value fails format check (NPI = 10 digits, ICD-10 = [A-Z]\d{2}\.?\w*, CPT = 5 digits, dates = valid calendar date, ZIP = 5 or 9 digits) are highlighted orange, distinct from yellow confidence flags
- **DUP-01**: Duplicate claim detection: flag rows where claim number + patient name + date of service match another row in the same output

---

## Out of Scope

- In-app editing or correction of extracted values — Excel is the review surface
- Database output of any kind — Excel only
- Auto-correction or normalisation of OCR values (ICD-10 dot insertion, etc.) — raw OCR value is always written
- Multi-user or concurrent processing — single-user desktop only
- Web or server deployment
- Training or fine-tuning Tesseract models
- Live ICD-10 / CPT code lookup or validation against external registries
- EHR or billing platform integration
- Processing digitally-generated (text-layer) PDFs as a distinct code path — scanned images only

---

## Traceability

| REQ-ID | Phase |
|--------|-------|
| ENV-01 | Phase 1 |
| ENV-02 | Phase 1 |
| PROC-01 | Phase 2 |
| PROC-02 | Phase 2 |
| PROC-03 | Phase 3 |
| PROC-04 | Phase 6 |
| EXTR-01 | Phase 4 |
| EXTR-02 | Phase 4 |
| EXTR-03 | Phase 4 |
| EXTR-04 | Phase 2 |
| OUT-01 | Phase 5 |
| OUT-02 | Phase 5 |
| OUT-03 | Phase 5 |
| OUT-04 | Phase 5 |
| OUT-05 | Phase 5 |
| UI-01 | Phase 6 |
| UI-02 | Phase 6 |
| UI-03 | Phase 6 |
| UI-04 | Phase 6 |
