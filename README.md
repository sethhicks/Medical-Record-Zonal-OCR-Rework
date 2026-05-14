# OCR Medical Billing Form Extractor

Desktop application that extracts three billing fields from scanned CMS-1500 and UB-04 PDFs and writes them to Excel.

**Extracted fields (per page):**

| Field | CMS-1500 source | UB-04 source |
|-------|----------------|--------------|
| Patient Name | Box 2 | Box 8 |
| Total Charge | Box 28 | EST. Amount Due row |
| Date of Service | Box 24, first service line | First revenue line date |

Output is a single `extracted_results.xlsx` workbook with one row per PDF page.

## Prerequisites

Both must be installed before running.

**Tesseract 5**
Download the Windows installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).
Default install path: `C:\Program Files\Tesseract-OCR\tesseract.exe`

**Poppler for Windows**
Download from [oschwartz10612/poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases).
Extract the archive and note the path to the `Library\bin` folder.
Default expected path: `C:\Program Files\poppler\Library\bin`

**Python packages**
```
pip install pdf2image pillow pytesseract opencv-python numpy openpyxl
```

## Setup

1. Install Tesseract and Poppler as above.
2. Run the dependency check to confirm both are found:
   ```
   python setup_check.py
   ```
3. If your install paths differ from the defaults, create a `settings.json` in the project folder (see [Configuration](#configuration)).

## Running

```
python main.py
```

A window opens with:
- **Select PDFs** — pick one or more scanned PDF files; multiple files can be selected at once
- **Start** — process all selected files; a progress bar updates per page
- **Open output file** — opens the Excel workbook when processing is done

Pages that fail (bad scan, unrecognised form type) write a blank row with an error message in an `extraction_error` column. The error log in the window shows a summary of failures after the run completes.

## Output

Results are written to `extracted_results.xlsx` in the configured output directory (Desktop by default). The workbook has a single **Results** sheet:

- One row per PDF page, in the order pages were processed
- Three data columns: **Patient Name**, **Total Charge**, **Date of Service**
- Date and charge columns are formatted as text to prevent Excel from converting values like `01/02/25` or `338.00` into numbers
- Pages from multiple PDFs are combined into one sheet

## Known Limitations

- Input PDFs must be scanned from paper at 300 DPI, US Letter size. Digital (text-layer) PDFs are not supported.
- A small number of pages will produce blank fields due to:
  - **Label overlap** — pages where charge digits print inside the "TOTAL CHARGE" label area (left blank intentionally; wrong values are worse than blank)
  - **Scan degradation** — heavily halftone-screened pages where the text is unreadable
  - **Continuation pages** — CMS-1500 pages with "CONTINUATION" in Box 28 have no total charge by design
  - **Non-standard layouts** — occasional forms with unusual date or name field placement
- On the reference sample (30-page test batch), 88 of 96 field reads are non-empty (91.7%).

## Configuration

Create `settings.json` in the project folder to override any defaults:

```json
{
    "tesseract_cmd": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
    "poppler_path":  "C:\\Program Files\\poppler\\Library\\bin",
    "output_dir":    "C:\\Users\\YourName\\Desktop"
}
```

| Key | Default | Description |
|-----|---------|-------------|
| `tesseract_cmd` | `C:\Program Files\Tesseract-OCR\tesseract.exe` | Full path to `tesseract.exe` |
| `poppler_path` | `C:\Program Files\poppler\Library\bin` | Folder containing `pdftoppm.exe` |
| `output_dir` | Desktop | Folder where `extracted_results.xlsx` is written |

`settings.json` is gitignored — each machine keeps its own paths locally.
