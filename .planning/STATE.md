# Project State — OCR Medical Billing Form Extractor

## Current Position
- Milestone: v1.0
- Current Phase: Phase 2 — Image Pipeline & Coordinate Calibration
- Last Updated: 2026-04-29

## Phase Status

| # | Phase | Status |
|---|-------|--------|
| 1 | Foundation & Environment | Complete (4/4 plans) |
| 2 | Image Pipeline & Coordinate Calibration | Not Started |
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

## Open Decisions

- ICD-10 dot format (F32.9 vs F329) — confirm with user before Phase 4; affects character whitelist and any downstream consumer of the Excel output
- Confidence threshold default (60%) — validate against a real representative batch during Phase 4 calibration
- Output filename/directory convention — confirm before Phase 6 UI build (affects open-output button target path)
- ~~PyMuPDF fallback~~ **Resolved (Phase 1):** Poppler-only; app exits with clear error if Poppler is missing — no fallback

## Notes

- `test.pdf` (30 pages) is available in the project root as the primary calibration and test sample
- Approximate composition of `test.pdf`: ~27 CMS-1500 pages, ~3 UB-04 pages
- All input PDFs are US Letter (8.5 x 11 in), 300 DPI, scanned from paper — this is a fixed assumption; digital PDFs are out of scope
- Phase 2 is the highest-risk phase: wrong pixel coordinates produce plausible-looking garbage with high Tesseract confidence; calibration overlay must be verified against real scans before any extractor code is written
- Python 3.11 required — 3.12/3.13 have OpenCV and pytesseract wheel gaps on Windows
- Tesseract and Poppler are non-pip binary installs; paths must be set explicitly in code, not via PATH
- Threading model: `threading.Thread` + `queue.Queue` + `tk.after(100, poll)` — never call tkinter widgets from the worker thread
