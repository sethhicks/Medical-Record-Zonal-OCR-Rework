# Research Summary — OCR Medical Billing Form Extractor

## Recommended Stack

The correct stack is narrow and well-established. Use **pdf2image + Poppler** for PDF-to-image at 300 DPI, **Tesseract 5 via pytesseract** for OCR with per-word confidence scores, **OpenCV + NumPy** for preprocessing, **openpyxl** for formatted xlsx output, and **tkinter** for the desktop UI. Python 3.11 is required — 3.12/3.13 have OpenCV and pytesseract wheel gaps on Windows.

```
pip install pdf2image Pillow pytesseract opencv-python numpy openpyxl PyMuPDF
pip install pytest pytest-cov
```

Tesseract and Poppler are non-pip binary installs (UB-Mannheim builds for Tesseract; `oschwartz10612/poppler-windows` for Poppler). Both must be set via explicit paths in code — do not rely on PATH. A `setup_check.py` startup validator must verify both before any processing begins.

---

## Table Stakes Features

Features billing staff require for the tool to replace manual re-entry. Missing any one = unusable.

- Form type auto-detection per page (CMS-1500 vs UB-04; mixed PDFs are the real input)
- All billing-critical fields extracted for both form types
- One Excel row per physical page, correct sheet per form type
- Box 24 service lines flattened as `SL1_–SL6_` column groups (not row explosion)
- UB-04 revenue lines flattened as `RL1_–RL22_` column groups
- Source metadata on every row: `source_filename`, `page_number`, `form_type`, `extraction_timestamp`
- Yellow highlight on fields below confidence threshold (default 60%)
- `avg_confidence` and `low_confidence_count` columns per row
- `extraction_error` column — failed pages appear as blank rows, never silently skipped
- Processing progress bar (100 pages = 2–5 min; no feedback looks like a hang)
- Open-output button on completion
- Processing log file written alongside the Excel output (HIPAA audit support)

**Defer to Phase 2:** format validation (orange highlight for format-invalid values), duplicate claim detection, run summary sheet, continuation linking, configurable threshold.

**Never build:** in-app editing, database output, auto-correction of OCR values, live code lookups, EHR integration, web/cloud deployment.

---

## Architecture at a Glance

Strict five-layer pipeline — data flows forward only:

```
UI (tkinter)
  -> Pipeline Orchestrator  [background thread; queue.Queue -> tk.after for UI updates]
    -> Page Processor       [preprocess -> detect form type -> dispatch to extractor]
      -> CMS1500Extractor / UB04Extractor  [crop regions -> pytesseract -> FieldResult]
        -> Excel Writer     [openpyxl; applies yellow fill; knows nothing about OCR]
```

Module layout: `ui/`, `pipeline/` (orchestrator, pdf_converter, preprocessor, form_detector, page_processor), `extractors/` (base, cms1500, ub04), `config/` (field_def, cms1500_fields, ub04_fields, settings), `models/` (results), `output/` (excel_writer).

Field coordinates are frozen Python dataclasses (`FieldDef`, `TableFieldDef`) in `config/` — not JSON. Box 24 and UB-04 revenue lines use `TableFieldDef` with `row_y_offsets` lists to avoid enumerating 60+ individual crop definitions. The confidence check lives in `ExcelWriter`, not in the extractors.

**Critical coordinate calibration gate:** Before writing any extractor code, render a real scan and draw rectangles over every field region to verify pixel coordinates. Wrong coordinates produce plausible-looking garbage with high Tesseract confidence. This cannot be deferred.

**Threading:** `threading.Thread` + `queue.Queue` + `tk.after(100, poll)`. Never call tkinter widgets from the worker thread.

---

## Top Pitfalls to Avoid

1. **No per-field PSM mode or character whitelist** (CRITICAL) — use `--psm 7` for single-line fields; apply per-field char whitelists (digits-only for CPT/NPI/ZIP, alpha+digits+dot for ICD-10).

2. **Coordinate drift from scanner size variation** (CRITICAL) — detect the form bounding box per page, compute `scale_x = detected_width / 2550`, `scale_y = detected_height / 3300`, apply before any crop. Deskew first.

3. **Box 24 grey-banded rows destroying OCR accuracy** (CRITICAL) — global Otsu threshold fails on grey backgrounds. Use `cv2.adaptiveThreshold` with `ADAPTIVE_THRESH_GAUSSIAN_C` (block size 31–51) per crop for all service line regions.

4. **Single-anchor form type detection failing on stamped/clipped scans** (CRITICAL) — require 2-of-3 independent anchors to agree; route UNKNOWN pages to an error column rather than guessing.

5. **Tesseract and Poppler install fragility on Windows** (HIGH) — set paths explicitly in code; ship `setup_check.py` that validates both before the first run.

**Also watch:** `pdf2image` defaults to 200 DPI — always pass `dpi=300`. openpyxl strips leading zeros from codes — set `number_format = "@"` on code columns. Apply cell fill directly in Python rather than using openpyxl conditional formatting rules (corrupt at 100+ rows).

---

## Key Open Questions

Must be resolved before or during Phase 1:

1. **ICD-10 dot format** — downstream system expects `F32.9` or `F329`? Decide before normalisation layer is built.
2. **Pixel coordinate calibration** — coordinates must be verified against real scans from the actual scanners in use before extractor code is written.
3. **Confidence threshold value** — 60% is the default; validate against a representative client batch.
4. **Output filename/directory convention** — decide before building the UI.
5. **PyMuPDF fallback** — on machines where Poppler can't be installed, does `setup_check.py` auto-switch or require explicit config?

---

## Recommended Build Order

1. **Foundation & Environment** — binary installs, `setup_check.py`, shared dataclasses, `config/settings.py`, DPI assertion at input boundary
2. **Coordinate Calibration** *(highest-risk phase)* — `pdf_converter.py`, calibration diagnostic script, `cms1500_fields.py`, `ub04_fields.py`, `preprocessor.py` (deskew + scale + adaptive threshold)
3. **Form Detection** — `form_detector.py` with multi-anchor logic, confidence score, UNKNOWN exit path
4. **Field Extraction** — `extractors/base.py`, `cms1500.py`, `ub04.py` with per-field PSM + whitelists, `page_processor.py`
5. **Orchestration & Excel Output** — `orchestrator.py` (streaming, no image accumulation in memory), `excel_writer.py`, processing log
6. **Desktop UI** — `ui/main_window.py`, progress bar, file picker, open-output button, `main.py`
7. **Hardening & Phase 2 Features** — format validation (orange highlight), duplicate detection, run summary sheet, batch testing, threshold calibration

---

*Generated 2026-04-28 from parallel research: STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md*
