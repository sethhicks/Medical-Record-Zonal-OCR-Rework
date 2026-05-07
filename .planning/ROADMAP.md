# Roadmap — OCR Medical Billing Form Extractor

## Phases

| # | Phase | Goal | Requirements | Status |
|---|-------|------|--------------|--------|
| 1 | Foundation & Environment | Project skeleton, dependency validation, and shared config are in place so all downstream phases build on a verified base | ENV-01, ENV-02 | Complete |
| 2 | Image Pipeline & Coordinate Calibration | Every PDF page converts to a correctly-scaled, deskewed, thresholded image and every field region is visually verified against real scans before extractor code is written | PROC-01, PROC-02, EXTR-04 | Complete |
| 3 | Form Detection | Each page is reliably classified as CMS-1500, UB-04, or UNKNOWN using multi-anchor logic so the correct extractor is always dispatched | PROC-03 | Complete |
| 4 | Field Extraction — CMS-1500 & UB-04 | All billing-critical fields for both form types are extracted with per-field PSM modes, character whitelists, and confidence scores attached to every result | EXTR-01, EXTR-02, EXTR-03 | Complete |
| 5 | Output & Excel Export | Extraction results are written to a correctly structured, formatted Excel workbook that billing staff can open and review immediately | OUT-01, OUT-02, OUT-03, OUT-04, OUT-05 | Complete |
| 6 | Desktop UI & Batch Processing | Billing staff can select one or more PDFs, watch per-page progress, and open the output file from a desktop window — with errors surfaced rather than silently dropped | UI-01, UI-02, UI-03, UI-04, PROC-04 | Not Started |

---

## Phase Details

### Phase 1: Foundation & Environment
**Goal:** Project skeleton, dependency validation, and shared config are in place so all downstream phases build on a verified base.
**Depends on:** Nothing (first phase)
**Requirements:** ENV-01, ENV-02
**Success Criteria:**
1. Running `python setup_check.py` on a machine with Tesseract and Poppler installed prints a clear "OK" confirmation for each binary; running it without either installed prints a specific error identifying which dependency is missing and exits non-zero.
2. A `settings.json` file with `tesseract_cmd`, `poppler_path`, `confidence_threshold`, and `output_dir` keys is read at startup and overrides the built-in defaults; removing `settings.json` entirely causes the application to start with defaults rather than crash.
3. The shared `FieldResult` dataclass and `FieldDef`/`TableFieldDef` coordinate dataclasses exist in the `models/` and `config/` modules and are importable from any other module in the project.
**Plans:** 4 plans
Plans:
- [x] 01-01-PLAN.md — Install pytest and create test scaffold (Wave 0)
- [x] 01-02-PLAN.md — Project skeleton: models/, config/ packages with dataclasses (Wave 1)
- [x] 01-03-PLAN.md — Settings loader: config_loader.py with load_settings() (Wave 1)
- [x] 01-04-PLAN.md — Dependency validator: setup_check.py with run_checks() (Wave 1)

### Phase 2: Image Pipeline & Coordinate Calibration
**Goal:** Every PDF page converts to a correctly-scaled, deskewed, thresholded image and every field region is visually verified against real scans before extractor code is written.
**Depends on:** Phase 1
**Requirements:** PROC-01, PROC-02, EXTR-04
**Success Criteria:**
1. Calling the PDF converter on any page of `test.pdf` produces a PIL Image whose width and height match the expected 2550x3300 pixels (300 DPI, US Letter); any other DPI is rejected at the input boundary.
2. The calibration script renders a chosen page of `test.pdf` with every configured CMS-1500 and UB-04 field region drawn as a labeled rectangle, and the resulting image can be visually inspected to confirm regions land on the correct form boxes.
3. After OpenCV preprocessing, the Box 24 grey-banded service line rows on a CMS-1500 page are visibly cleaner than the raw scan (adaptive threshold removes the grey band); deskew corrects a deliberately tilted test image back to within 0.5 degrees of vertical.
4. The scale-correction step computes `scale_x` and `scale_y` from the detected form bounding box and applies them to all field coordinates before any crop, confirmed by the calibration overlay remaining aligned on pages that differ slightly in physical scan size.
**Plans:** 7 plans
Plans:
- [x] 02-01-PLAN.md — Test scaffold: tests/test_phase2.py (15 stubs) + tests/conftest.py (Wave 0)
- [x] 02-02-PLAN.md — Settings extension: add threshold_block_size=31 to config_loader._DEFAULTS (Wave 1)
- [x] 02-03-PLAN.md — CMS-1500 coordinates: populate CMS1500_FIELDS (29) + CMS1500_TABLE_FIELDS (10) (Wave 1)
- [x] 02-04-PLAN.md — UB-04 coordinates: populate UB04_FIELDS (24) + UB04_TABLE_FIELDS (7) (Wave 1)
- [x] 02-05-PLAN.md — PDF converter: pipeline/__init__.py + pipeline/converter.py (Wave 1)
- [x] 02-06-PLAN.md — Preprocessor: pipeline/preprocessor.py — scale correction, deskew, adaptive threshold (Wave 1)
- [x] 02-07-PLAN.md — Calibration script: pipeline/calibrate.py CLI with overlay rendering (Wave 2)

### Phase 3: Form Detection
**Goal:** Each page is reliably classified as CMS-1500, UB-04, or UNKNOWN using multi-anchor logic so the correct extractor is always dispatched.
**Depends on:** Phase 2
**Requirements:** PROC-03
**Success Criteria:**
1. Running the form detector against the 27 CMS-1500 pages in `test.pdf` returns `CMS-1500` for every page that contains the expected signature strings ("HEALTH INSURANCE", "NUCC Instruction Manual", "FORM 1500").
2. Running the form detector against the 3 UB-04 pages in `test.pdf` returns `UB-04` for every page that contains the UB-04 signature strings ("NUBC", "UB-04 CMS-1450").
3. A test page with all anchor text obscured (simulating a stamped or clipped scan that matches fewer than 2 anchors) is classified as `UNKNOWN` rather than assigned to either form type.
4. Every page classified as `UNKNOWN` produces a result object that carries the `UNKNOWN` form type label so downstream stages can write it as an error row rather than silently skipping it.
**Plans:** 3 plans
Plans:
- [x] 03-01-PLAN.md — Test scaffold: tests/test_phase3.py with 8 skipped stubs (Wave 0)
- [x] 03-02-PLAN.md — Detector: pipeline/detector.py + 5 unit tests activated (Wave 1)

**Wave 2**
- [x] 03-03-PLAN.md — Wire: pipeline/__init__.py re-export + 3 integration tests activated (Wave 2)

Cross-cutting constraints:
- `pytesseract.tesseract_cmd` set inside `detect_form_type` via `load_settings()` (all plans)
- All pipeline imports deferred inside test function bodies (all plans)

### Phase 4: Field Extraction — CMS-1500 & UB-04
**Goal:** All billing-critical fields for both form types are extracted with per-field PSM modes, character whitelists, and confidence scores attached to every result.
**Depends on:** Phase 3
**Requirements:** EXTR-01, EXTR-02, EXTR-03
**Success Criteria:**
1. Processing a CMS-1500 page from `test.pdf` returns a result object containing non-empty extracted values for at least 80% of the defined fields (Claim/Member ID, Box 1, Box 1a, Box 2, Box 3, Box 5, Box 17, Box 17b, Box 19, Box 21 A–L, Box 23, Box 24 service lines 1–6, Box 25, Box 26, Box 27, Box 28, Box 29, Box 32, Box 33).
2. Processing a UB-04 page from `test.pdf` returns a result object containing non-empty extracted values for at least 80% of the defined fields (Box 1, Box 3b, Box 4, Box 5, Box 6, Box 8–12, Box 14, Box 17, revenue lines 1–22, Box 50–51, Box 54–56, Box 58, Box 60–61, Box 63–64, Box 66–75, Box 76).
3. Every field result carries a numeric confidence value between 0 and 100; no field result is missing a confidence score.
4. NPI and CPT fields use a digits-only character whitelist; ICD-10 fields use an alpha+digits+dot whitelist; the OCR output for these fields contains only characters from the respective whitelist.
5. Box 24 service line extraction returns six discrete line result groups (SL1–SL6) even when some lines are blank on the form.
**Plans:** 6 plans
Plans:
- [x] 04-01-PLAN.md — Test scaffold: tests/test_phase4.py with 17 skipped stubs (Wave 0)

**Wave 1** *(blocked on Wave 0 completion)*
- [x] 04-02-PLAN.md — Config updates: box21a–l and box24_cpt whitelists in config/cms1500.py (Wave 1)
- [x] 04-03-PLAN.md — CMS-1500 extractor: pipeline/extractor_cms1500.py + 6 unit tests activated (Wave 1, depends on 04-02)
- [x] 04-04-PLAN.md — UB-04 extractor: pipeline/extractor_ub04.py + 5 unit tests activated (Wave 1)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 04-05-PLAN.md — Wire: pipeline/__init__.py re-export + 2 import tests activated (Wave 2)

**Wave 3** *(blocked on Wave 2 completion — human checkpoint)*
- [ ] 04-06-PLAN.md — Integration calibration: sweep test.pdf, document rates, activate 4 integration tests (Wave 3)

Cross-cutting constraints:
- `pytesseract.pytesseract.tesseract_cmd = settings['tesseract_cmd']` set at start of each extractor function (all OCR plans)
- config whitelist update (04-02) must complete before CMS-1500 extractor (04-03) is written

### Phase 5: Output & Excel Export
**Goal:** Extraction results are written to a correctly structured, formatted Excel workbook that billing staff can open and review immediately.
**Depends on:** Phase 4
**Requirements:** OUT-01, OUT-02, OUT-03, OUT-04, OUT-05
**Success Criteria:**
1. Opening the output workbook in Excel shows exactly two sheets named "CMS-1500" and "UB-04"; each sheet has one data row per physical PDF page of the corresponding form type; columns are present for every defined field even when the extracted value is blank.
2. The CMS-1500 sheet contains `SL1_date_from` through `SL6_rendering_npi` column groups (six service-line blocks, each with all sub-fields) rather than separate rows per service line.
3. The UB-04 sheet contains `RL1_rev_code` through `RL22_non_covered` column groups (twenty-two revenue-line blocks, each with all sub-fields) rather than separate rows per revenue line.
4. Any cell whose field confidence is below the configured threshold (default 60%) is highlighted yellow; a cell with confidence at or above the threshold has no fill; changing the threshold in `settings.json` and rerunning produces a different set of yellow cells.
5. NPI, CPT, ICD code, ZIP, and tax ID columns are formatted as text (`@` number format) so that a value like `01234` displays as `01234` rather than `1234` in Excel.
**Plans:** 3 plans
Plans:
- [x] 05-01-PLAN.md — Test scaffold: tests/test_phase5.py with 12 skipped stubs (Wave 1)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 05-02-PLAN.md — Writer: pipeline/writer.py with write_workbook() + 8 unit stubs activated (Wave 2)

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 05-03-PLAN.md — Wire: pipeline/__init__.py write_workbook export + 4 integration stubs activated (Wave 3)

### Phase 6: Desktop UI & Batch Processing
**Goal:** Billing staff can select one or more PDFs, watch per-page progress, and open the output file from a desktop window — with errors surfaced rather than silently dropped.
**Depends on:** Phase 5
**Requirements:** UI-01, UI-02, UI-03, UI-04, PROC-04
**Success Criteria:**
1. Launching the application opens a desktop window with a button that opens a file-picker dialog filtered to `*.pdf`; the user can select multiple files in a single dialog interaction and they are queued for processing.
2. After starting a run, a progress bar and page counter update for each page processed without freezing the window; the UI remains responsive (buttons not grayed, window can be moved) while a background thread processes pages.
3. Selecting two or more PDF files and starting a run produces a single output workbook whose CMS-1500 and UB-04 sheets contain rows from all input files, in the order the pages were processed.
4. When processing completes, a button appears (or becomes active) that opens the output Excel file in the system default application with a single click.
5. Pages that fail during conversion or extraction appear as blank rows in the appropriate sheet with the `extraction_error` column populated with the error message; the UI displays a summary of how many pages failed after the run completes.
**Plans:** 3 plans
Plans:
- [ ] 06-01-PLAN.md — Test scaffold: tests/test_phase6.py with 12 skipped stubs (Wave 0)

**Wave 1** *(blocked on Wave 0 completion)*
- [ ] 06-02-PLAN.md — Full main.py: OCRApp class, startup check, file selection, worker thread, poll callback, error rows in Excel (Wave 1)

**Wave 2** *(blocked on Wave 1 completion — human checkpoint)*
- [ ] 06-03-PLAN.md — Integration: human UI verify checkpoint + smoke tests on real test.pdf (Wave 2)

Cross-cutting constraints:
- `threading.Thread` + `queue.Queue` + `root.after(100, poll_queue)` — never call tkinter widgets from worker thread (all plans)
- `run_checks()` called before `Tk()` construction — startup sequence enforced (06-02)
- Done message is a 3-tuple `("done", output_path, error_count)` — consumers must unpack 3 elements (all plans)

---

## Progress

| Phase | Status | Completed |
|-------|--------|-----------|
| 1. Foundation & Environment | Complete | 2026-04-29 |
| 2. Image Pipeline & Coordinate Calibration | Complete | 2026-05-01 |
| 3. Form Detection | Complete | 2026-05-03 |
| 4. Field Extraction — CMS-1500 & UB-04 | Complete | 2026-05-06 |
| 5. Output & Excel Export | Complete | 2026-05-06 |
| 6. Desktop UI & Batch Processing | Ready to execute | — |
