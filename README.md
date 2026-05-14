# OCR Medical Billing Form Extractor

Desktop application that extracts billing fields from scanned CMS-1500 and UB-04 PDFs and writes them to Excel.

## Prerequisites

Both must be installed before running the app.

**Tesseract 5**
Download the Windows installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).
Default install path: `C:\Program Files\Tesseract-OCR\tesseract.exe`

**Poppler for Windows**
Download from [oschwartz10612/poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases).
Extract and note the `Library\bin` folder path.
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
- **Select PDFs** — pick one or more scanned PDF files
- **Start** — process all selected files; a progress bar updates per page
- **Open output file** — opens the Excel workbook when processing is done

Failed pages appear in the error log and write a blank row with an error message in the output file.

## Output

Results are written to `extracted_results.xlsx` on your Desktop (configurable). The workbook has a single **Results** sheet with one row per page. CMS-1500 and UB-04 fields appear as named columns. Cells with low-confidence OCR reads are highlighted yellow.

## Configuration

Create `settings.json` in the project folder to override any defaults:

```json
{
    "tesseract_cmd": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
    "poppler_path":  "C:\\Program Files\\poppler\\Library\\bin",
    "confidence_threshold": 60,
    "output_dir": "C:\\Users\\YourName\\Desktop"
}
```

| Key | Default | Description |
|-----|---------|-------------|
| `tesseract_cmd` | `C:\Program Files\Tesseract-OCR\tesseract.exe` | Full path to `tesseract.exe` |
| `poppler_path` | `C:\Program Files\poppler\Library\bin` | Folder containing `pdftoppm.exe` |
| `confidence_threshold` | `60` | OCR confidence below which a cell is highlighted yellow (0–100) |
| `output_dir` | Desktop | Folder where `extracted_results.xlsx` is written |

`settings.json` is gitignored — each machine keeps its own paths locally.

## Supported Forms

| Form | Fields extracted |
|------|-----------------|
| CMS-1500 | Boxes 1–33 including all six service lines (Box 24 SL1–SL6) |
| UB-04 | Boxes 1–76 including all 22 revenue lines |

Input PDFs must be scanned from paper at 300 DPI, US Letter size. Digital (text-layer) PDFs are not supported.
