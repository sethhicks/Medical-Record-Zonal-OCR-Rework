# OCR Medical Billing Form Extractor

## What This Is

A Python desktop application that ingests scanned PDF files containing medical billing forms, runs Tesseract OCR against each page, auto-detects whether each page is a CMS-1500 (professional claim) or UB-04 (institutional claim), extracts billing-critical fields using fixed pixel-region coordinates, and exports the results to a structured Excel workbook with separate sheets per form type.

The core problem it solves: billing staff currently extract data from scanned claim forms manually. This tool eliminates that manual re-keying by automating extraction into a reviewable Excel file, with low-confidence cells flagged in yellow for human follow-up.

## Core Value

**Accurate, structured extraction of billing-critical fields from scanned CMS-1500 and UB-04 PDFs into a reviewable Excel file — without manual data entry.**

## Context

- All input PDFs are US Letter (8.5 × 11 in), 300 DPI, scanned from paper
- PDFs contain mixed page types — CMS-1500 and UB-04 pages appear in the same file in no guaranteed order
- Some CMS-1500 claims span multiple physical pages ("CONTINUED ON NEXT PAGE") — each page becomes one Excel row, grouped by claim number
- Medium volume: dozens of PDFs, up to ~100 pages per processing run
- Output is one Excel workbook per run: one sheet for CMS-1500 pages, one sheet for UB-04 pages
- Low-confidence OCR cells are highlighted yellow for human review
- Tool is for internal billing staff use — single-user desktop app on Windows

## Form Types

### CMS-1500 (Professional Claims)
Standard NUCC health insurance claim form. Identified by:
- "HEALTH INSURANCE" banner in top-left
- "NUCC Instruction Manual" footer text
- "FORM 1500" in bottom-right footer

Billing-critical fields to extract:
- Claim/Member ID (top area)
- Box 1: Insurance type (Medicare/Medicaid/Tricare/CHAMPVA/Group/FECA/Other)
- Box 1a: Insured's ID Number
- Box 2: Patient Name
- Box 3: Patient DOB, Sex
- Box 5: Patient Address (Street, City, State, ZIP)
- Box 17: Referring Provider Name + Qualifier
- Box 17b: Referring Provider NPI
- Box 19: Additional Claim Information
- Box 21: Diagnosis Codes A–L (ICD codes)
- Box 23: Prior Authorization Number
- Box 24 (service lines 1–6): Date From, Date To, Place of Service, EMG, CPT/HCPCS, Modifier, Diagnosis Pointer, $ Charges, Days/Units, Rendering Provider NPI
- Box 25: Federal Tax ID, SSN/EIN indicator
- Box 26: Patient Account No.
- Box 27: Accept Assignment
- Box 28: Total Charge
- Box 29: Amount Paid
- Box 32: Service Facility Name + Address
- Box 33: Billing Provider Name + Address + Phone + NPI

### UB-04 (Institutional Claims)
Standard NUBC uniform billing form. Identified by:
- Facility name/address directly at top-left (no "HEALTH INSURANCE" banner)
- "NUBC" footer text
- "JB-04 CMS-1450" or "UB-04 CMS-1450" bottom-left text

Billing-critical fields to extract:
- Box 1: Provider Name + Address
- Box 3b: Patient Control Number
- Box 4: Type of Bill
- Box 5: Federal Tax Number
- Box 6: Statement Covers Period (From / Through)
- Box 8: Patient Name
- Box 9: Patient Address
- Box 10: Patient Birthdate
- Box 11: Sex
- Box 12: Admission Date
- Box 14: Type of Admission
- Box 17: Patient Status
- Box 42–48: Revenue lines (Rev Code, Description, HCPCS, Service Date, Units, Total Charges, Non-covered Charges)
- Box 50: Payer Name
- Box 51: Health Plan ID
- Box 54: Prior Payments
- Box 55: Est. Amount Due
- Box 56: NPI
- Box 58: Insured's Name
- Box 60: Insured's Unique ID
- Box 61: Group Name
- Box 63: Treatment Authorization Codes
- Box 64: Document Control Number
- Box 66–75: Diagnosis + Procedure Codes
- Box 76: Attending Provider NPI + Name

## Technical Approach

- **Language:** Python
- **PDF → image:** pdf2image (wraps poppler) or PyMuPDF — convert each page to PIL Image at native DPI
- **Preprocessing:** OpenCV — deskew, denoise, adaptive threshold to improve OCR accuracy on scanned forms
- **OCR engine:** Tesseract 5.x via pytesseract — with `--psm 6` (uniform block) for field regions; confidence scores captured per field
- **Form detection:** Scan top and bottom strip of each page for CMS-1500/UB-04 signature strings; fall back to layout analysis if text is unclear
- **Field extraction:** Fixed pixel-region crops at known coordinates (all forms are 8.5×11 @ 300 DPI = 2550×3300 px), one `image.crop(box)` + `pytesseract.image_to_data()` per field
- **Excel output:** openpyxl — two sheets (CMS-1500, UB-04), one row per physical page, yellow fill on low-confidence cells (confidence < configurable threshold, default 60%)
- **UI:** tkinter desktop app — file picker for PDFs, progress bar during processing, open-output-file button on completion

## Requirements

### Active

- [ ] User can select one or more PDF files via desktop file picker
- [ ] App converts each PDF page to a 300 DPI image using pdf2image/PyMuPDF
- [ ] App preprocesses each page image with OpenCV (deskew, denoise, threshold) before OCR
- [ ] App auto-detects form type (CMS-1500 vs UB-04) for each page
- [ ] App extracts all billing-critical CMS-1500 fields using fixed coordinate regions
- [ ] App extracts all billing-critical UB-04 fields using fixed coordinate regions
- [ ] App captures Tesseract confidence score per field
- [ ] App exports results to Excel with separate CMS-1500 and UB-04 sheets
- [ ] Each physical page maps to one Excel row
- [ ] Cells with OCR confidence below threshold are highlighted yellow
- [ ] User can see processing progress (per-page progress bar)
- [ ] User can open the output Excel file directly from the app on completion
- [ ] App handles multi-page CMS-1500 claims (groups by claim number column)

### Out of Scope

- Web or server deployment — desktop only
- Database output — Excel only
- Editing or correcting extracted values in-app — Excel is the review surface
- Training or fine-tuning Tesseract models
- Processing non-scanned (digital/text-layer) PDFs as a special case
- Multi-user or concurrent processing

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Fixed coordinate extraction | All PDFs are identical size/DPI — pixel regions are stable and far more reliable than label-finding | Committed |
| One row per physical page | Multi-page claims can have 40+ service lines; flattening to one claim row would create 40+ columns or truncate | Committed |
| Separate Excel sheets by form type | CMS-1500 and UB-04 have completely different field structures — mixing columns would be unusable | Committed |
| Yellow highlight for low confidence | "Best effort" accuracy preference — don't suppress uncertain values, flag them instead | Committed |
| tkinter UI | Ships with Python stdlib, no additional install for end user | Pending — may upgrade to PyQt5 if tkinter proves too limited |
| Tesseract 5.x | LSTM engine significantly outperforms legacy Tesseract 4 on printed forms | Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-28 after initialization*
