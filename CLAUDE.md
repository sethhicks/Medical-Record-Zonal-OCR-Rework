# OCR Medical Billing Form Extractor

Python desktop app that extracts billing fields from scanned CMS-1500 and UB-04 PDFs using Tesseract OCR, outputs to Excel.

## GSD Workflow

This project uses GSD for planning and execution.

- **Check progress:** `/gsd-progress`
- **Plan next phase:** `/gsd-plan-phase <N>`
- **Execute phase:** `/gsd-execute-phase <N>`
- **Resume after break:** `/gsd-resume-work`

## Key Facts

- All input PDFs: US Letter, 8.5×11 in, 300 DPI, scanned from paper
- Fixed coordinate extraction — pixel regions are stable across all inputs
- `test.pdf` (30 pages, ~27 CMS-1500 + ~3 UB-04) is the reference sample
- Phase 2 coordinate calibration is a hard gate — do not start Phase 4 until pixel regions are visually verified

## Stack

- Python 3.11
- pdf2image + Poppler (PDF→image)
- Tesseract 5 / pytesseract (OCR)
- OpenCV + NumPy (preprocessing)
- openpyxl (Excel output)
- tkinter (desktop UI)

## Open Decisions (resolve before the relevant phase)

- ICD-10 dot format: `F32.9` or `F329`? (needed Phase 4)
- Confidence threshold: default 60%, validate against real batch (Phase 4)
- Output filename convention (needed Phase 6)
