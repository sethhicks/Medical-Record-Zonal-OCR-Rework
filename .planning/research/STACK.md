# Technology Stack

**Project:** OCR Medical Billing Form Extractor
**Researched:** 2026-04-28
**Confidence:** HIGH for core stack (all choices well-established and stable); MEDIUM for exact version pins (training data cutoff August 2025)

---

## Recommended Stack

### Core Language

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python | 3.11.x | Application runtime | 3.11 has the best balance of speed improvements over 3.10 and ecosystem stability; 3.12 still has some rough edges with compiled packages on Windows (e.g., OpenCV wheels lag). Avoid 3.13 — too new, Tesseract bindings and OpenCV wheels may not exist yet on Windows. |

**Confidence: HIGH** — Python 3.11 is the de facto standard for data-processing desktop apps on Windows as of mid-2025.

---

### PDF-to-Image Conversion

**Recommendation: pdf2image (wrapping Poppler) as primary; PyMuPDF (fitz) as fallback.**

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| pdf2image | 1.17.x | Convert PDF pages to PIL Images at 300 DPI | Thin, purpose-built wrapper around Poppler's `pdftoppm`. Extremely reliable for scanned PDFs. Dead-simple API: `convert_from_path(path, dpi=300)`. |
| PyMuPDF (fitz) | 1.23.x | Fallback renderer; also useful for reading PDF metadata | Pure Python wheel on Windows — no Poppler dependency. Slightly different rendering engine; useful if Poppler install fails or is unavailable on a machine. Renders via its own MuPDF C library. |
| Pillow (PIL) | 10.x | Image manipulation, crop, save, format conversion | Required by pdf2image; used everywhere for `image.crop(box)` field extraction. |

**Confidence: HIGH** — pdf2image + Poppler is the established standard for 300 DPI scanned PDF workflows in Python.

**Why not PyMuPDF as primary:** pdf2image output is a plain PIL Image list — the simplest possible integration with pytesseract and OpenCV. PyMuPDF's `fitz.Pixmap` requires an extra conversion step. Use PyMuPDF as a fallback or if Poppler proves impossible to install on a particular machine.

---

### OCR Engine

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Tesseract | 5.x (5.3.x or later) | OCR engine binary | LSTM neural network engine in Tesseract 5 substantially outperforms Tesseract 4's legacy engine on printed forms. The `--psm 6` mode (uniform block of text) is optimal for fixed-region field crops. |
| pytesseract | 0.3.10+ | Python wrapper for Tesseract CLI | Provides `image_to_string()`, `image_to_data()` (returns per-word confidence scores), and `image_to_osd()`. The `image_to_data()` call with `output_type=pytesseract.Output.DATAFRAME` is the correct path to per-field confidence aggregation. |

**Confidence: HIGH** — Tesseract 5 + pytesseract is the canonical open-source OCR stack for Python desktop apps.

**Key pytesseract call pattern for confidence scores:**
```python
import pytesseract
import pandas as pd

data = pytesseract.image_to_data(
    cropped_image,
    config='--psm 6',
    output_type=pytesseract.Output.DATAFRAME
)
# Filter out empty/noise rows, then take mean confidence
words = data[data['conf'] > -1]
field_confidence = words['conf'].mean() if not words.empty else 0.0
field_text = ' '.join(words['text'].dropna().astype(str)).strip()
```

---

### Image Preprocessing

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| OpenCV (opencv-python) | 4.9.x | Deskew, denoise, adaptive threshold | Industry standard for image processing pipelines. `cv2.threshold()` with `THRESH_BINARY + THRESH_OTSU` is the correct call for printed form binarization. Deskew via Hough line transform or minAreaRect. |
| NumPy | 1.26.x | Array bridge between PIL and OpenCV | PIL Images must be converted to NumPy arrays for OpenCV: `np.array(pil_image)`. Required; not optional. |

**Confidence: HIGH** — OpenCV is the only serious choice here.

**PIL <-> OpenCV conversion pattern (critical to get right):**
```python
import cv2
import numpy as np
from PIL import Image

# PIL (RGB) -> OpenCV (BGR)
cv_img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

# OpenCV (BGR) -> PIL (RGB), for passing back to pytesseract
pil_img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
```

---

### Excel Output

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| openpyxl | 3.1.x | Write .xlsx workbook with formatting | The correct library for programmatically writing formatted .xlsx files. Supports cell fill colors (PatternFill), multiple sheets, and column width control. xlrd/xlwt are legacy and cannot write xlsx. pandas ExcelWriter uses openpyxl under the hood — go direct for full formatting control. |

**Confidence: HIGH** — openpyxl is the only maintained, feature-complete xlsx writer for Python.

**Yellow highlight pattern:**
```python
from openpyxl.styles import PatternFill

YELLOW_FILL = PatternFill(start_color='FFFF00', end_color='FFFF00', fill_type='solid')

# Apply:
ws['A1'].fill = YELLOW_FILL
```

---

### Desktop UI

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| tkinter | stdlib (ships with Python) | Desktop GUI: file picker, progress bar, open-file button | PROJECT.md lists tkinter as primary with PyQt5 as a potential upgrade. For this scope — file picker, progress bar, single button — tkinter is sufficient and requires zero additional install. Eliminates one installation step for end users. |

**Confidence: HIGH for tkinter as MVP choice.**

**Key tkinter components needed:**
- `tkinter.filedialog.askopenfilenames()` — multi-file picker (returns tuple of paths)
- `tkinter.ttk.Progressbar` — determinate mode, update per page
- `tkinter.messagebox.showinfo()` — completion dialog
- `subprocess.Popen(['start', '', output_path], shell=True)` — open Excel file from Windows

**When to upgrade to PyQt5:** Only if you need threading with UI updates without `after()` polling, or need a more professional look. tkinter's `after()` method is sufficient for progress updates from a background thread via a queue. Do not pre-emptively switch.

---

## Full Dependency List

### Runtime Dependencies

```
pdf2image==1.17.0
Pillow==10.4.0
pytesseract==0.3.10
opencv-python==4.9.0.80
numpy==1.26.4
openpyxl==3.1.2
PyMuPDF==1.23.26
```

### Dev/Test Dependencies

```
pytest==8.2.0
pytest-cov==5.0.0
```

---

## pip Install Commands

### 1. Create and activate virtual environment (do this first)

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install all runtime dependencies

```bash
pip install pdf2image Pillow pytesseract opencv-python numpy openpyxl PyMuPDF
```

### 3. Install dev dependencies

```bash
pip install pytest pytest-cov
```

### 4. Freeze for reproducibility

```bash
pip freeze > requirements.txt
```

---

## Windows-Specific Installation: Poppler

**Confidence: HIGH** — This is the single most common Windows blocker for pdf2image.

pdf2image is a thin wrapper around Poppler's `pdftoppm.exe` binary. Poppler does NOT ship with Python or pdf2image on Windows. You must install it separately and add it to PATH (or pass `poppler_path=` explicitly).

### Installation steps

**Option A: Direct binary download (recommended)**

1. Download the latest Windows Poppler release from:
   `https://github.com/oschwartz10612/poppler-windows/releases`
   (This is the maintained community Windows build. The official Poppler project does not ship Windows binaries.)

2. Extract to a stable path, e.g.:
   `C:\tools\poppler\`
   After extraction you should see:
   `C:\tools\poppler\Library\bin\pdftoppm.exe`
   `C:\tools\poppler\Library\bin\pdfinfo.exe`

3. Add to System PATH (Control Panel > System > Environment Variables > Path):
   `C:\tools\poppler\Library\bin`
   **OR** pass the path explicitly in code to avoid PATH dependency:

```python
from pdf2image import convert_from_path

images = convert_from_path(
    pdf_path,
    dpi=300,
    poppler_path=r'C:\tools\poppler\Library\bin'
)
```

**Option B: conda (if using Anaconda/Miniconda)**

```bash
conda install -c conda-forge poppler
```
This drops the binary into the conda environment's bin automatically. No PATH manipulation needed.

**Option C: Chocolatey (if choco is available)**

```bash
choco install poppler
```

### Verification

```bash
pdftoppm -v
```
Expected output: `pdftoppm version X.XX.X` — confirms the binary is on PATH.

### Common Poppler failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `PDFInfoNotInstalledError` | `pdfinfo.exe` not on PATH | Add Poppler bin dir to PATH or use `poppler_path=` |
| `PDFPageCountError` | `pdfinfo.exe` found but corrupted PDF | Check PDF is valid; test with `pdfinfo yourfile.pdf` |
| `pdf2image.exceptions.PDFSyntaxError` | Poppler version mismatch with PDF version | Upgrade to latest Poppler release |
| ImportError on pdf2image import | pdf2image not installed | `pip install pdf2image` |
| `FileNotFoundError: [WinError 2]` when calling convert | pdftoppm.exe not on PATH at all | See steps above |

---

## Windows-Specific Installation: Tesseract

**Confidence: HIGH** — Second most common Windows blocker.

pytesseract is a Python wrapper that shells out to the `tesseract.exe` binary. The binary must be installed separately.

### Installation steps

1. Download the Tesseract installer from the official UB Mannheim builds:
   `https://github.com/UB-Mannheim/tesseract/wiki`
   These are the canonical Windows installers. Download `tesseract-ocr-w64-setup-5.x.x.exe` (64-bit).

2. Run the installer. During installation:
   - Accept the default install path: `C:\Program Files\Tesseract-OCR\`
   - On the "Additional language data" screen, select **English** at minimum. The `eng.traineddata` file is required. If your forms ever contain non-ASCII characters, also select the relevant languages.
   - The installer does NOT add itself to PATH by default in all versions — verify after install.

3. Add to System PATH:
   `C:\Program Files\Tesseract-OCR\`

4. Tell pytesseract where the binary is (recommended: do this in code unconditionally to avoid machine-to-machine PATH issues):

```python
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

Place this line at module top-level, before any OCR calls. This is the single most reliable way to handle Tesseract on Windows — don't rely on PATH discovery.

### Verification

```bash
tesseract --version
```
Expected: `tesseract 5.x.x ...` with `Found AVX2` or similar SIMD line.

```bash
tesseract --list-langs
```
Expected: `eng` in the list. If missing, the `tessdata` directory is not correctly configured.

### TESSDATA_PREFIX (only needed if using custom models)

If you ever add custom `.traineddata` files, set:

```python
import os
os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'
```

For this project using only `eng.traineddata`, this is not required.

### Common Tesseract failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `TesseractNotFoundError` | Binary not on PATH and `tesseract_cmd` not set | Set `pytesseract.pytesseract.tesseract_cmd` explicitly |
| `Error opening data file ... eng.traineddata` | Language pack not installed | Re-run installer, select English; or manually copy `eng.traineddata` to `tessdata/` |
| Very low confidence on all fields (<30%) | Wrong `--psm` mode for region type | Use `--psm 6` for rectangular field crops; `--psm 7` for single-line fields |
| Garbled output on clean scans | Image not binarized before OCR | Apply OpenCV `THRESH_BINARY + THRESH_OTSU` before passing to pytesseract |
| `OSError: [WinError 6]` on multithreaded calls | Tesseract is not thread-safe at process level | Process pages serially in main thread, or use `concurrent.futures.ProcessPoolExecutor` (separate processes, not threads) |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| PDF renderer | pdf2image + Poppler | PyMuPDF only | pdf2image is more widely documented for scanned-PDF-to-PIL workflows; PyMuPDF kept as fallback |
| OCR engine | Tesseract 5 via pytesseract | EasyOCR, PaddleOCR, Google Vision API | Tesseract is free, offline, proven on printed forms, and gives per-word confidence scores natively. EasyOCR/PaddleOCR are heavier (deep learning models, GPU optional) with more complex installs. Google Vision requires internet + API key. |
| Image processing | OpenCV | scikit-image, imageio | OpenCV has the best Windows binary wheel support and the widest community for deskew/threshold patterns |
| Excel output | openpyxl | xlsxwriter, pandas to_excel | openpyxl gives full cell-level formatting control (fill, font, border) without going through pandas. xlsxwriter cannot read existing files. |
| GUI | tkinter | PyQt5, wxPython, customtkinter | tkinter ships with Python — zero additional install. For this scope (file picker + progress bar + one button) it is sufficient. |
| Python version | 3.11 | 3.12, 3.13 | OpenCV and some Tesseract-adjacent packages have had wheel delays on new Python versions; 3.11 has proven ecosystem support |

---

## Configuration File Strategy

The project already has a `config.json` skeleton. Expand it to include:

```json
{
  "ocr": {
    "dpi": 300,
    "confidence_threshold": 60,
    "tesseract_cmd": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
    "poppler_path": "C:\\tools\\poppler\\Library\\bin",
    "psm_mode": 6
  },
  "output": {
    "highlight_color": "FFFF00",
    "sheet_cms1500": "CMS-1500",
    "sheet_ub04": "UB-04"
  }
}
```

Making `tesseract_cmd` and `poppler_path` configurable (rather than hardcoded) lets the app work on different machines without code changes — critical for a tool deployed to billing staff.

---

## Sources

- pytesseract documentation and source: https://github.com/madmaze/pytesseract (HIGH confidence — training knowledge corroborated by API patterns)
- pdf2image documentation: https://github.com/Belval/pdf2image (HIGH confidence)
- Poppler Windows builds: https://github.com/oschwartz10612/poppler-windows (HIGH confidence — this is the canonical Windows Poppler binary source)
- Tesseract Windows installer: https://github.com/UB-Mannheim/tesseract/wiki (HIGH confidence — official UB Mannheim builds are referenced in Tesseract project docs)
- openpyxl documentation: https://openpyxl.readthedocs.io (HIGH confidence)
- OpenCV Python documentation: https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html (HIGH confidence)
- Tesseract PSM modes: https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html (HIGH confidence)

**Note on version pins:** Exact version numbers (pdf2image 1.17.0, opencv-python 4.9.0.80, etc.) reflect training knowledge as of August 2025. Before installing, verify current stable releases on PyPI. The library choices themselves are stable; minor version updates are expected and safe.
