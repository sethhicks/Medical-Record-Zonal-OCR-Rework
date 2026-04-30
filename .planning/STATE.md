# Project State — OCR Medical Billing Form Extractor

## Current Position
- Milestone: v1.0
- Current Phase: Phase 2 — Image Pipeline & Coordinate Calibration
- Last Updated: 2026-04-29

## Phase Status

| # | Phase | Status |
|---|-------|--------|
| 1 | Foundation & Environment | Complete (4/4 plans) |
| 2 | Image Pipeline & Coordinate Calibration | Ready to execute (7/7 plans) |
| 3 | Form Detection | Not Started |
| 4 | Field Extraction — CMS-1500 & UB-04 | Not Started |
| 5 | Output & Excel Export | Not Started |
| 6 | Desktop UI & Batch Processing | Not Started |

## Recent Activity

- 2026-04-28: Project initialized, research complete, requirements defined (19 v1 requirements)
- 2026-04-28: Roadmap created — 6 phases, 19/19 v1 requirements mapped
- 2026-04-28: Phase 1 context gathered — PDF backend decision locked (Poppler-only, no PyMuPDF fallback); resume: .planning/phases/01-foundation-environment/01-CONTEXT.md
- 2026-04-28: Phase 1 planned — 4 plans in 2 waves; Wave 0 (test infra), Wave 1 (skeleton, settings loader, dependency validator)
- 2026-04-28: Phase 1 complete — all 4 plans executed; 8/8 tests passing; Tesseract 5.5.0 and Poppler confirmed on machine
- 2026-04-29: Phase 1 verified — 3/3 success criteria met; VERIFICATION.md committed
- 2026-04-29: Phase 2 context gathered — pipeline/calibrate/coordinate decisions locked; resume: .planning/phases/02-image-pipeline-coordinate-calibration/02-CONTEXT.md
- 2026-04-29: Phase 2 planned — 7 plans in 3 waves; Wave 0 (test scaffold), Wave 1 (settings, coords, converter, preprocessor), Wave 2 (calibration script)
- 2026-04-30: Phase 2 plan 02-02 complete — threshold_block_size=31 added to config_loader._DEFAULTS; test_settings_threshold_block_size_default passes green
- 2026-04-30: Phase 2 plan 02-03 complete — CMS1500_FIELDS (29 FieldDef) and CMS1500_TABLE_FIELDS (10 TableFieldDef, 6 rows each) populated in config/cms1500.py; both coordinate tests pass green
- 2026-04-30: Phase 2 plan 02-04 complete — UB04_FIELDS (24 FieldDef) and UB04_TABLE_FIELDS (7 TableFieldDef, 22 rows each) populated in config/ub04.py; both coordinate tests pass green
- 2026-04-30: Phase 2 plan 02-05 complete — pipeline/__init__.py and pipeline/converter.py created; convert_page() returns 2550x3300 RGB PIL Image with Lanczos normalisation; real test.pdf pages are 2478x3228 at 300 DPI (8.26x10.76 in scan); all 3 test_convert_page_* tests pass green
- 2026-04-30: Phase 2 plan 02-06 complete — pipeline/preprocessor.py created with three-step OpenCV pipeline (scale correction, deskew, adaptive threshold); ValueError raised for skew >5°; block_size auto-corrects even values (T-2-03); all 5 preprocessor tests pass green; Phase 1 regression 8/8 green

## Open Decisions

- ICD-10 dot format (F32.9 vs F329) — confirm with user before Phase 4; affects character whitelist and any downstream consumer of the Excel output
- Confidence threshold default (60%) — validate against a real representative batch during Phase 4 calibration
- Output filename/directory convention — confirm before Phase 6 UI build (affects open-output button target path)
- ~~PyMuPDF fallback~~ **Resolved (Phase 1):** Poppler-only; app exits with clear error if Poppler is missing — no fallback
- ~~Exact scanner page size~~ **Discovered (Phase 2 plan 02-05):** test.pdf pages are 2478x3228 at 300 DPI (8.26x10.76 in, not 8.5x11 in). convert_page() resizes ±10% deviations to exactly 2550x3300 via Lanczos; coordinate calibration in 02-07 must verify alignment on resized images.

## Notes

- `test.pdf` (30 pages) is available in the project root as the primary calibration and test sample
- Approximate composition of `test.pdf`: ~27 CMS-1500 pages, ~3 UB-04 pages
- All input PDFs are US Letter (8.5 x 11 in), 300 DPI, scanned from paper — this is a fixed assumption; digital PDFs are out of scope
- Phase 2 is the highest-risk phase: wrong pixel coordinates produce plausible-looking garbage with high Tesseract confidence; calibration overlay must be verified against real scans before any extractor code is written
- Python 3.11 required — 3.12/3.13 have OpenCV and pytesseract wheel gaps on Windows
- Tesseract and Poppler are non-pip binary installs; paths must be set explicitly in code, not via PATH
- Threading model: `threading.Thread` + `queue.Queue` + `tk.after(100, poll)` — never call tkinter widgets from the worker thread
