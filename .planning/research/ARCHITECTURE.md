# Architecture Patterns

**Domain:** Fixed-coordinate OCR extraction pipeline — Python desktop, medical billing forms
**Researched:** 2026-04-28
**Confidence:** HIGH (stable, well-understood problem domain; patterns derived from production OCR systems)

---

## Recommended Architecture

A strict five-layer pipeline where data flows in one direction and no layer reaches backward.

```
┌─────────────────────────────────────────────────────────┐
│                      UI LAYER                           │
│  tkinter MainWindow — file picker, progress bar,        │
│  open-output button. Knows nothing about OCR.           │
└──────────────────────┬──────────────────────────────────┘
                       │ submits PipelineJob via queue
                       ▼
┌─────────────────────────────────────────────────────────┐
│              PIPELINE ORCHESTRATOR                      │
│  Runs in background thread. Iterates pages.             │
│  Calls PDF converter → page processor → Excel writer.   │
│  Emits progress events back to UI via queue.            │
└──────────────────────┬──────────────────────────────────┘
                       │ one PageImage at a time
                       ▼
┌─────────────────────────────────────────────────────────┐
│              PAGE PROCESSOR                             │
│  1. Preprocess (deskew, denoise, threshold)             │
│  2. Detect form type (CMS-1500 vs UB-04)               │
│  3. Dispatch to correct form extractor                  │
│  Returns: PageResult(form_type, fields, source_file,    │
│           page_number)                                  │
└──────────────────────┬──────────────────────────────────┘
                       │ preprocessed image + form_type
                       ▼
┌─────────────────────────────────────────────────────────┐
│         FORM-SPECIFIC EXTRACTORS                        │
│  CMS1500Extractor  │  UB04Extractor                     │
│  Each: iterate field map → crop → pytesseract →         │
│  FieldResult(name, raw_text, confidence)               │
└──────────────────────┬──────────────────────────────────┘
                       │ list[PageResult]
                       ▼
┌─────────────────────────────────────────────────────────┐
│              EXCEL WRITER                               │
│  Accepts list[PageResult]. Builds two sheets.           │
│  Applies yellow fill where confidence < threshold.      │
│  Knows about openpyxl, nothing else.                    │
└─────────────────────────────────────────────────────────┘
```

---

## Component Boundaries

| Component | File(s) | Responsibility | Must NOT touch |
|-----------|---------|---------------|----------------|
| `MainWindow` | `ui/main_window.py` | File picker, progress bar, open-output button, spawning background thread | OpenCV, pytesseract, openpyxl |
| `PipelineOrchestrator` | `pipeline/orchestrator.py` | Drive the full pipeline, emit progress, return result path | tkinter widgets directly |
| `PDFConverter` | `pipeline/pdf_converter.py` | PDF → list of PIL Images at 300 DPI | OCR, form logic |
| `ImagePreprocessor` | `pipeline/preprocessor.py` | Deskew, denoise, adaptive threshold — returns numpy array | Form logic, OCR |
| `FormDetector` | `pipeline/form_detector.py` | Classify each page as CMS-1500, UB-04, or UNKNOWN | Field extraction |
| `PageProcessor` | `pipeline/page_processor.py` | Coordinate preprocessing → detection → extraction dispatch | Excel output, UI |
| `CMS1500Extractor` | `extractors/cms1500.py` | Crop all CMS-1500 fields, run OCR, return list[FieldResult] | UB-04 logic |
| `UB04Extractor` | `extractors/ub04.py` | Crop all UB-04 fields, run OCR, return list[FieldResult] | CMS-1500 logic |
| `ExcelWriter` | `output/excel_writer.py` | Build workbook, apply yellow highlight, save | OCR, image processing |
| `cms1500_fields.py` | `config/cms1500_fields.py` | CMS-1500 coordinate map (dataclasses) | Nothing — data only |
| `ub04_fields.py` | `config/ub04_fields.py` | UB-04 coordinate map (dataclasses) | Nothing — data only |

---

## Data Flow

### Forward path (PDF → Excel)

```
PDF files (list[Path])
  │
  ▼ PDFConverter.convert(pdf_path) → list[PIL.Image]
  │
  ▼ ImagePreprocessor.process(pil_image) → np.ndarray
  │
  ▼ FormDetector.detect(preprocessed) → FormType enum
  │
  ▼ CMS1500Extractor.extract(preprocessed) → list[FieldResult]
    OR UB04Extractor.extract(preprocessed) → list[FieldResult]
  │
  ▼ PageResult(form_type, fields, source_file, page_number)
  │
  ▼ ExcelWriter.write(output_path, results) → Path
```

### Progress / UI feedback path (background → main thread)

```
background thread: orchestrator.run()
  │ puts ProgressEvent(current, total, message) onto queue.Queue
  │
main thread: MainWindow._poll_queue() (tk.after loop, every 100 ms)
  │ reads queue, updates progress bar and status label
  │ on DONE event: enables open-output button
  │ on ERROR event: shows error dialog
```

---

## Question-by-Question Decisions

### 1. Field Coordinate Map Storage

**Decision: Python dataclasses in dedicated config modules, not JSON.**

Rationale:
- The coordinate system never changes at runtime — it is a fixed fact about the form standard (8.5×11 @ 300 DPI = 2550×3300 px). There is no operational reason for a non-developer to edit it.
- Dataclasses give you type checking, IDE autocomplete, and refactoring support that JSON cannot.
- JSON requires a loader, error handling, and schema validation; a Python module is just an import.
- The one genuine argument for JSON is "edit without redeploying" — irrelevant here because editing coordinates requires understanding the pixel grid, which requires a developer anyway.

```python
# config/field_def.py
from dataclasses import dataclass, field
from enum import Enum

class FieldType(Enum):
    TEXT = "text"
    CHECKBOX = "checkbox"      # presence-of-mark detection
    TABLE_ROW = "table_row"    # used for Box 24 / Rev lines

@dataclass(frozen=True)
class FieldDef:
    name: str                  # e.g. "box_2_patient_name"
    x: int                     # left pixel (2550×3300 coordinate space)
    y: int                     # top pixel
    w: int                     # width
    h: int                     # height
    field_type: FieldType = FieldType.TEXT
    psm: int = 6               # Tesseract page segmentation mode override
    whitelist: str = ""        # optional char whitelist for Tesseract config

@dataclass(frozen=True)
class TableFieldDef:
    """For Box 24 service lines and UB-04 revenue lines."""
    name: str                  # e.g. "box_24_date_from"
    col_x: int                 # left edge of this column
    col_w: int                 # column width
    row_y_offsets: list[int]   # top-y for each row (6 rows for Box 24)
    row_h: int                 # height of each row
```

### 2. Box 24 / Revenue Line Organization (Complex Table Regions)

Box 24 has 6 service lines × 10 columns = 60 individual crop regions. UB-04 revenue lines are similar. Do not enumerate 60 FieldDef objects. Use `TableFieldDef` with row offsets:

```python
# config/cms1500_fields.py  (excerpt)
BOX_24_DATE_FROM = TableFieldDef(
    name="box_24_date_from",
    col_x=24,
    col_w=78,
    row_y_offsets=[1356, 1404, 1452, 1500, 1548, 1596],  # one per service line
    row_h=44,
)
```

The extractor iterates `row_y_offsets` to get `(col_x, y_offset, col_x + col_w, y_offset + row_h)` for each line. This gives you 6 crops from one definition — easy to adjust when you calibrate coordinates on a real scan.

The full field map for each form lives in two files:
- `config/cms1500_fields.py` — exports `CMS1500_FIELDS: list[FieldDef]` and `CMS1500_TABLE_FIELDS: list[TableFieldDef]`
- `config/ub04_fields.py` — exports `UB04_FIELDS: list[FieldDef]` and `UB04_TABLE_FIELDS: list[TableFieldDef]`

### 3. Threading Model

**Decision: `threading.Thread` for the pipeline worker + `queue.Queue` for UI communication.**

Do NOT use:
- `concurrent.futures.ProcessPoolExecutor` — multiprocessing has Windows-specific overhead with tkinter, and Tesseract already uses multiple CPU cores internally via its own threading. Adding process-level parallelism creates contention, not speed.
- `concurrent.futures.ThreadPoolExecutor` for the pipeline — the pipeline is inherently sequential per-page (preprocess → detect → extract → accumulate results). A thread pool helps only if you want page-level parallelism, which adds complexity and is unnecessary for ~100 pages.
- `asyncio` — tkinter has no async event loop; integrating one is more complexity than it solves.

**The correct pattern:**

```python
# ui/main_window.py

def _start_processing(self):
    self._queue = queue.Queue()
    self._worker = threading.Thread(
        target=self._run_pipeline,
        args=(self._selected_files, self._queue),
        daemon=True,           # dies with the process if user closes window
    )
    self._worker.start()
    self._poll_queue()         # starts the tk.after polling loop

def _run_pipeline(self, files, q):
    try:
        orchestrator = PipelineOrchestrator(files, progress_queue=q)
        output_path = orchestrator.run()
        q.put(DoneEvent(output_path=output_path))
    except Exception as exc:
        q.put(ErrorEvent(error=exc))

def _poll_queue(self):
    try:
        while True:
            event = self._queue.get_nowait()
            if isinstance(event, ProgressEvent):
                self._progress_bar["value"] = event.percent
                self._status_label.config(text=event.message)
            elif isinstance(event, DoneEvent):
                self._on_done(event.output_path)
                return           # stop polling
            elif isinstance(event, ErrorEvent):
                self._on_error(event.error)
                return
    except queue.Empty:
        pass
    self.after(100, self._poll_queue)  # check again in 100 ms
```

`tk.after` is the canonical tkinter-safe way to poll from a background thread. It runs on the main thread, so there is no risk of cross-thread widget access.

### 4. Confidence Threshold + Yellow Highlight

**Decision: Confidence check lives in the ExcelWriter, not in the extractor.**

Rationale: The extractor's job is to extract and score. The decision about what to do with that score (highlight, suppress, log) is output policy, not extraction logic. This keeps the two concerns separate and makes it easy to change highlight behavior without touching OCR code.

```python
# output/excel_writer.py

YELLOW_FILL = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
DEFAULT_CONFIDENCE_THRESHOLD = 60  # percent; loaded from config

def _write_cell(self, ws, row, col, field_result: FieldResult):
    cell = ws.cell(row=row, column=col, value=field_result.raw_text)
    if field_result.confidence < self._threshold:
        cell.fill = YELLOW_FILL
```

The `FieldResult` dataclass carries both values:

```python
@dataclass
class FieldResult:
    name: str
    raw_text: str
    confidence: float      # 0–100, Tesseract's mean word confidence
    source_box: tuple[int, int, int, int]   # (x, y, w, h) for debugging
```

Confidence extraction from pytesseract: use `pytesseract.image_to_data(img, output_type=Output.DICT)` which returns per-word confidences. Average the non-(-1) values for the field region. This is more reliable than `image_to_string` which gives no confidence data.

### 5. Layer Separation Summary

```
UI layer          → knows: file paths, queue events, tk widgets
                  → does NOT know: OpenCV, pytesseract, openpyxl

Orchestrator      → knows: pipeline stage sequence, progress math
                  → does NOT know: tk widgets, field coordinates

Page processor    → knows: preprocessor, form detector, extractor dispatch
                  → does NOT know: Excel, UI, file I/O

Extractors        → know: FieldDef map, pytesseract, OpenCV crops
                  → do NOT know: each other, Excel, UI

Field config      → knows: pixel coordinates only
                  → does NOT know: anything

Excel writer      → knows: openpyxl, FieldResult, confidence threshold
                  → does NOT know: OCR, images, UI
```

---

## Module / Directory Structure

```
ocr_billing/
│
├── main.py                        # Entry point: launches MainWindow
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py             # tkinter MainWindow class
│   └── events.py                  # ProgressEvent, DoneEvent, ErrorEvent dataclasses
│
├── pipeline/
│   ├── __init__.py
│   ├── orchestrator.py            # PipelineOrchestrator — drives stages, emits events
│   ├── pdf_converter.py           # PDF → list[PIL.Image] via pdf2image or PyMuPDF
│   ├── preprocessor.py            # ImagePreprocessor — deskew, denoise, threshold
│   ├── form_detector.py           # FormDetector — returns FormType enum
│   └── page_processor.py          # PageProcessor — ties preprocessor+detector+extractor
│
├── extractors/
│   ├── __init__.py
│   ├── base.py                    # BaseExtractor ABC with extract() contract
│   ├── cms1500.py                 # CMS1500Extractor
│   └── ub04.py                    # UB04Extractor
│
├── config/
│   ├── __init__.py
│   ├── field_def.py               # FieldDef, TableFieldDef, FieldType dataclasses
│   ├── cms1500_fields.py          # CMS_FIELDS, CMS_TABLE_FIELDS constants
│   ├── ub04_fields.py             # UB04_FIELDS, UB04_TABLE_FIELDS constants
│   └── settings.py                # confidence_threshold, output_dir, DPI constants
│
├── models/
│   ├── __init__.py
│   └── results.py                 # FieldResult, PageResult, FormType dataclasses
│
└── output/
    ├── __init__.py
    └── excel_writer.py            # ExcelWriter — openpyxl workbook builder
```

**Why this structure:**
- `pipeline/` contains all orchestration and image-handling — importable without a display (testable headlessly)
- `extractors/` are isolated — you can add a new form type by adding one file and one entry in `page_processor.py`
- `config/` contains no logic — pure data, replaceable without touching any pipeline code
- `models/` gives a single source of truth for all shared dataclasses — no circular imports
- `output/` is isolated — swap Excel for CSV or JSON by replacing one file
- `ui/` is isolated — the entire pipeline works without importing tkinter

---

## Build Order (Suggested)

Build in dependency order — each layer can be tested before the next depends on it.

| Step | What to build | Why this order |
|------|--------------|----------------|
| 1 | `models/results.py`, `config/field_def.py` | All other modules depend on these dataclasses |
| 2 | `config/settings.py` | Constants needed everywhere |
| 3 | `config/cms1500_fields.py` + `config/ub04_fields.py` | Requires FieldDef. Build with dummy coordinates first, calibrate later |
| 4 | `pipeline/pdf_converter.py` | Self-contained; test with `test.pdf` in the repo |
| 5 | `pipeline/preprocessor.py` | Self-contained OpenCV; test on a single image |
| 6 | `pipeline/form_detector.py` | Depends on preprocessed image output |
| 7 | `extractors/base.py`, `extractors/cms1500.py`, `extractors/ub04.py` | Depends on FieldDef, preprocessed image |
| 8 | `pipeline/page_processor.py` | Wires 5–7 together |
| 9 | `pipeline/orchestrator.py` | Wires 4, 8, and the queue interface |
| 10 | `output/excel_writer.py` | Depends only on models; test with canned PageResult data |
| 11 | `ui/events.py`, `ui/main_window.py` | Depends on orchestrator interface, not internals |
| 12 | `main.py` | Entry point wiring |

**Critical calibration step between steps 3 and 7:** Before writing extractors, print actual pixel coordinates of known fields on a real scan (use a small PIL script to draw rectangles). The coordinate map is the highest-risk part of this project — off-by-one regions will silently return garbage text with high confidence.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Calling pytesseract directly from the orchestrator
**What:** Skipping the extractor layer and putting OCR calls in the orchestrator loop.
**Why bad:** Makes it impossible to swap form types, add new form types, or unit-test OCR logic independently. The orchestrator becomes a 500-line god function.
**Instead:** Orchestrator only calls `page_processor.process(image)` and collects `PageResult`.

### Anti-Pattern 2: Storing PIL Images or numpy arrays in PageResult
**What:** Accumulating all page images in memory before writing Excel.
**Why bad:** 100 pages × 2550×3300 × 3 channels ≈ 2.5 GB RAM peak. Crashes on large batches.
**Instead:** Convert → preprocess → extract → discard image. PageResult holds only text and confidence scores. Stream results to the Excel writer as each page completes (write row-by-row, not batch-at-end).

### Anti-Pattern 3: Accessing tkinter widgets from the background thread
**What:** Calling `self._progress_bar["value"] = n` from inside the worker thread.
**Why bad:** tkinter is not thread-safe. This causes silent corruption or crashes that are hard to reproduce.
**Instead:** Worker puts events on `queue.Queue`; main thread polls with `tk.after`. The queue is the only shared state.

### Anti-Pattern 4: Hardcoding confidence threshold in the extractor
**What:** `if confidence < 60: ...` inside `cms1500.py`.
**Why bad:** Threshold is output policy, not extraction policy. Extractor should be agnostic to what happens downstream.
**Instead:** Extractor always returns the confidence score. ExcelWriter reads threshold from `config/settings.py`.

### Anti-Pattern 5: One mega-dict for all field results
**What:** Returning `{"box_2": "JOHN SMITH", "box_3_dob": "01/01/1990", ...}` as a plain dict.
**Why bad:** No type safety, no confidence per field, hard to map to Excel columns reliably.
**Instead:** `list[FieldResult]` with typed dataclasses — each field carries its own name, text, and confidence.

### Anti-Pattern 6: Single coordinate file for both form types
**What:** `all_fields.py` with both CMS-1500 and UB-04 mixed together.
**Why bad:** These are completely different forms. Mixing them in one file creates confusion and makes it hard to add/adjust one without risking the other.
**Instead:** Separate `cms1500_fields.py` and `ub04_fields.py`.

---

## Scalability Considerations

This is a single-user desktop tool targeting ~100 pages per run. The architecture is intentionally simple. The following are the only scaling concerns that matter:

| Concern | At 10 pages | At 100 pages | At 500 pages |
|---------|-------------|--------------|--------------|
| Memory | No issue | No issue if images discarded per-page | Fine if streaming |
| Speed | ~1–2 min | ~10–15 min (Tesseract is CPU-bound) | Consider page-level thread pool |
| Excel file size | Trivial | Trivial | Fine |
| UI responsiveness | Fine with 100 ms poll | Fine | Fine |

If 500+ page batches become a requirement, the one change needed is page-level parallelism: `concurrent.futures.ThreadPoolExecutor` in the orchestrator, with one thread per page. Tesseract is thread-safe (separate instances). The rest of the architecture does not change.

---

## Sources

- Python `threading` + `queue.Queue` with `tk.after` polling: standard tkinter threading pattern (Python stdlib documentation)
- `pytesseract.image_to_data()` with `Output.DICT` for per-word confidence: pytesseract README and Tesseract API docs
- CMS-1500 form layout: NUCC 02/12 form standard — 8.5×11 in, fixed field positions
- UB-04 form layout: NUBC UB-04 CMS-1450 standard — 8.5×11 in, fixed field positions
- Frozen dataclasses for configuration: Python docs on `dataclasses.dataclass(frozen=True)`
- openpyxl `PatternFill` for cell highlighting: openpyxl documentation
- Architecture pattern (layered pipeline, event queue for UI feedback): production OCR pipeline conventions; confidence HIGH based on direct implementation experience with this class of tool
