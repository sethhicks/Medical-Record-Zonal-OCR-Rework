# Project State — OCR Medical Billing Form Extractor

## Current Position
- Milestone: v1.0
- Current Phase: Not started
- Last Updated: 2026-04-28

## Phase Status

| # | Phase | Status |
|---|-------|--------|
| 1 | Foundation & Environment | Not Started |
| 2 | Image Pipeline & Coordinate Calibration | Not Started |
| 3 | Form Detection | Not Started |
| 4 | Field Extraction — CMS-1500 & UB-04 | Not Started |
| 5 | Output & Excel Export | Not Started |
| 6 | Desktop UI & Batch Processing | Not Started |

## Recent Activity

- 2026-04-28: Project initialized, research complete, requirements defined (19 v1 requirements)
- 2026-04-28: Roadmap created — 6 phases, 19/19 v1 requirements mapped

## Open Decisions

- ICD-10 dot format (F32.9 vs F329) — confirm with user before Phase 4; affects character whitelist and any downstream consumer of the Excel output
- Confidence threshold default (60%) — validate against a real representative batch during Phase 4 calibration
- Output filename/directory convention — confirm before Phase 6 UI build (affects open-output button target path)
- PyMuPDF fallback — decide whether `setup_check.py` auto-switches to PyMuPDF when Poppler is absent, or requires explicit config flag (resolve in Phase 1)

## Notes

- `test.pdf` (30 pages) is available in the project root as the primary calibration and test sample
- Approximate composition of `test.pdf`: ~27 CMS-1500 pages, ~3 UB-04 pages
- All input PDFs are US Letter (8.5 x 11 in), 300 DPI, scanned from paper — this is a fixed assumption; digital PDFs are out of scope
- Phase 2 is the highest-risk phase: wrong pixel coordinates produce plausible-looking garbage with high Tesseract confidence; calibration overlay must be verified against real scans before any extractor code is written
- Python 3.11 required — 3.12/3.13 have OpenCV and pytesseract wheel gaps on Windows
- Tesseract and Poppler are non-pip binary installs; paths must be set explicitly in code, not via PATH
- Threading model: `threading.Thread` + `queue.Queue` + `tk.after(100, poll)` — never call tkinter widgets from the worker thread
