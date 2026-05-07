---
phase: 06-desktop-ui-batch-processing
reviewed: 2026-05-07T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - main.py
  - pipeline/preprocessor.py
  - pipeline/extractor_cms1500.py
  - pipeline/extractor_ub04.py
  - config/ub04.py
findings:
  critical: 0
  warning: 6
  info: 4
  total: 10
status: issues_found
---

# Phase 06: Code Review Report

**Reviewed:** 2026-05-07
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Reviewed the five Phase 6 source files: the new `main.py` tkinter UI, two modified
extractors, the modified preprocessor, and the modified UB-04 config. The threading
model (worker thread + `queue.Queue` + `root.after` poll loop) is correctly implemented
— no tkinter widget is touched from the worker thread. No hardcoded credentials,
injection vectors, or data-loss-level bugs were found.

Six warnings are raised. The most consequential are: (1) the openpyxl workbook opened
for error-page post-processing is never closed when an exception occurs, leaving a file
handle open for the rest of the process lifetime; (2) `_on_done` leaves the error log
unscrollable to its new summary line because `see(tk.END)` is not called after inserting
it; (3) the worker silently treats a PDF whose `pdfinfo_from_path` raises an exception
as having 0 pages, producing no progress ticks and no error message for that file; and
(4) the `detect_form_type` function re-calls `load_settings()` on every single page,
which is a correctness concern because it re-reads disk on each of the (potentially
hundreds of) pages and could silently use different settings mid-batch if the file is
modified during a run. Four informational items cover dead debug code, a duplicated
`_ocr_region` function body, a missing `tesseract_cmd` key guard, and a mutable default
assumption in the settings dict.

---

## Warnings

### WR-01: Workbook file handle leaked on exception in error-page post-processing

**File:** `main.py:213-230`

**Issue:** The openpyxl workbook is opened with `wb = _openpyxl.load_workbook(output_path)`
but the surrounding `try/except` does not guarantee the workbook is closed. If any
statement between `load_workbook` and `wb.save(output_path)` raises — for example if the
`"CMS-1500"` sheet does not exist (line 215 raises `KeyError`) — the workbook object is
left open. CPython's reference counting will typically close it immediately, but it is
not guaranteed under all runtimes and is a latent resource-leak risk. The sheet-missing
case is realistic: if `write_workbook` raises before creating the sheet and the outer
`except` on line 204 catches it, `output_path` will be `None` and the `if output_path`
guard on line 211 prevents entry — however if `write_workbook` partially completes with
only the "UB-04" sheet written, the guard passes but `wb["CMS-1500"]` on line 215 will
raise `KeyError`, leaving the handle open.

**Fix:** Use a `with` statement (openpyxl workbooks do not support context managers
natively, so close explicitly in a `finally`):

```python
if output_path and error_pages:
    try:
        wb = _openpyxl.load_workbook(output_path)
        try:
            ws = wb["CMS-1500"]
            header_row = [ws.cell(row=1, column=c).value
                          for c in range(1, ws.max_column + 1)]
            try:
                err_col = header_row.index("extraction_error") + 1
            except ValueError:
                err_col = ws.max_column + 1
                ws.cell(row=1, column=err_col, value="extraction_error")
            next_row = ws.max_row + 1
            for _, err_msg in error_pages:
                ws.cell(row=next_row, column=err_col, value=err_msg)
                next_row += 1
            wb.save(output_path)
        finally:
            wb.close()
    except Exception as exc:
        self._queue.put(("error", "", 0, f"error_pages write failed: {exc}"))
```

---

### WR-02: `_on_done` does not scroll error log to show summary line

**File:** `main.py:296-302`

**Issue:** When `error_count > 0`, `_on_done` inserts a summary line into the error
log but does not call `self.error_log.see(tk.END)`. If the error log is already full
(more lines than the visible height), the newly appended summary line will not be
visible to the user without manual scrolling. By contrast, the `poll_queue` handler
correctly calls `see(tk.END)` after every error insert (line 258). The omission in
`_on_done` is inconsistent and means the completion message can be hidden.

**Fix:** Add `self.error_log.see(tk.END)` after the insert:

```python
if error_count > 0:
    self.error_log.config(state=tk.NORMAL)
    self.error_log.insert(
        tk.END,
        f"--- Run complete. {error_count} page(s) failed — see errors above. ---\n"
    )
    self.error_log.see(tk.END)   # ADD THIS LINE
    self.error_log.config(state=tk.DISABLED)
```

---

### WR-03: `pdfinfo_from_path` failure silently skips entire PDF with no error message

**File:** `main.py:161-167`

**Issue:** If `pdfinfo_from_path` raises (Poppler not found, corrupt PDF, permissions
error, etc.) the exception is caught and `n_pages` is set to 0, appending 0 to
`page_counts`. The corresponding PDF is then silently skipped — the `for page_num in
range(0)` loop body never executes, no progress tick is emitted, and no error message
is posted to the queue. The user sees no indication that one of their selected PDFs was
not processed at all.

```python
try:
    info = pdfinfo_from_path(pdf_path, poppler_path=settings.get("poppler_path"))
    n_pages = info["Pages"]
except Exception:          # <-- exception swallowed; n_pages = 0; no error posted
    n_pages = 0
```

**Fix:** Post an error message when the count fails so the user knows the file was skipped:

```python
try:
    info = pdfinfo_from_path(pdf_path, poppler_path=settings.get("poppler_path"))
    n_pages = info["Pages"]
except Exception as exc:
    n_pages = 0
    self._queue.put(("error", pdf_path, 0,
                     f"Could not read page count: {exc}"))
```

---

### WR-04: `detect_form_type` calls `load_settings()` on every page

**File:** `pipeline/detector.py:33`

**Issue:** `detect_form_type` calls `load_settings()` at the top of every invocation.
In a 30-page batch this means 30 disk reads (or at minimum 30 `open()` calls). More
critically, because `load_settings()` reads `settings.json` fresh each time, it is
possible for the effective settings to change between pages mid-batch if the file is
modified externally, violating the expectation of a consistent run. The caller in
`_worker` already holds a frozen `settings` dict that is passed to every other pipeline
stage; `detect_form_type` ignores it and independently re-loads. The `tesseract_cmd`
set inside `detect_form_type` could therefore differ from what the extractors use if
settings change mid-run.

**Fix:** Accept `settings` as a parameter (consistent with every other pipeline
function) and remove the internal `load_settings()` call:

```python
def detect_form_type(image: "Image.Image", settings: dict | None = None) -> str:
    if settings is None:
        from config_loader import load_settings
        settings = load_settings()
    pytesseract.pytesseract.tesseract_cmd = settings['tesseract_cmd']
    ...
```

Then in `main.py` line 181:
```python
form = pipeline.detect_form_type(raw, settings)
```

Note: `converter.py` has the same pattern (calls `load_settings()` internally); the
same fix applies there but it is outside the Phase 6 diff scope.

---

### WR-05: `poll_queue` stops re-scheduling on "done" even if worker thread is still alive

**File:** `main.py:268-271`

**Issue:** `poll_queue` drains the queue in a single call, sets `done = True` when it
sees a "done" message, and then calls `_on_done` without rescheduling itself. If the
worker posts a "done" message and also has queued additional "error" messages in the
same queue flush (which cannot happen by construction — "done" is always the last
`put` in `_worker`) this is safe. However the queue is drained with `get_nowait()` in
FIFO order, so any messages posted before "done" are processed first in the same tick.
The real risk is subtler: because `done = True` and `_on_done` are reached only after
the `while True` loop exhausts the queue, messages after "done" (which cannot exist by
contract) are silently dropped. The code is correct by current contract but fragile —
if `_worker` ever posts anything after "done" (e.g., a future refactor), those messages
are silently lost. There is no assertion or comment documenting that "done" must be the
final message.

**Fix:** Add a defensive assertion or comment:

```python
# "done" is always the final message posted by _worker; nothing follows it.
# If the contract changes, messages after "done" will be silently dropped.
if done:
    self._on_done(*done_args)
    # Do NOT reschedule — worker is finished.
else:
    self.root.after(100, self.poll_queue)
```

Or add an assertion in `_worker` right before the final `put`:

```python
# Final message — must be last put() call in this method.
self._queue.put(("done", output_path, len(error_pages)))
```

---

### WR-06: Duplicate `_ocr_region` implementation in extractor_cms1500 and extractor_ub04

**File:** `pipeline/extractor_cms1500.py:26-55`, `pipeline/extractor_ub04.py:26-55`

**Issue:** The `_ocr_region` function is byte-for-byte identical in both extractor
modules. This is not a correctness bug today, but it is a maintainability defect: any
fix or tuning to OCR behaviour (e.g., changing the confidence sentinel, adjusting
whitespace stripping) must be applied in two places. The two copies will inevitably
diverge.

**Fix:** Extract `_ocr_region` into a shared internal module (e.g.,
`pipeline/_ocr_helpers.py` or `pipeline/extractor_base.py`) and import it in both
extractor files:

```python
# pipeline/_ocr_helpers.py
def _ocr_region(crop, psm, whitelist): ...

# pipeline/extractor_cms1500.py
from pipeline._ocr_helpers import _ocr_region

# pipeline/extractor_ub04.py
from pipeline._ocr_helpers import _ocr_region
```

---

## Info

### IN-01: Dead debug code — two saves of the same debug image

**File:** `pipeline/preprocessor.py:122-126`

**Issue:** When `debug=True`, the deskewed image is saved twice in a row to two
different filenames (`debug_03_deskewed.png` and `debug_04_corrected.png`) because the
adaptive threshold step was removed but the second debug save was not. The intent was
clearly to show the before/after of the threshold step. Now both saves write the same
`corrected` array, producing identical files and confusing any developer who relies on
the debug output.

```python
if debug:
    Image.fromarray(...).save("debug_03_deskewed.png")

if debug:                                               # dead — identical to above
    Image.fromarray(...).save("debug_04_corrected.png")
```

**Fix:** Remove the second block. Rename the remaining file to `debug_03_final.png` to
reflect that it is the final output:

```python
if debug:
    Image.fromarray(cv2.cvtColor(corrected, cv2.COLOR_BGR2RGB)).save("debug_03_final.png")
```

---

### IN-02: `scale_x` / `scale_y` computed but never used

**File:** `pipeline/preprocessor.py:67-75`

**Issue:** `scale_x` and `scale_y` are computed from the largest contour bounding box
(lines 67-68) but are never referenced again. The resize on line 75 ignores them and
always resizes to the hardcoded target `(2550, 3300)`. The dead computation adds
confusion about whether coordinate-adjusted scaling was intended.

**Fix:** Remove the unused variables:

```python
if contours:
    largest = max(contours, key=cv2.contourArea)
    # bounding rect used only to verify contours exist; resize is always to target
    _ = cv2.boundingRect(largest)  # or simply remove the block and resize unconditionally
else:
    pass  # blank page — resize to target anyway
scaled = cv2.resize(cv_img, (2550, 3300), interpolation=cv2.INTER_LINEAR)
```

---

### IN-03: Missing `tesseract_cmd` key raises `KeyError` rather than a helpful error

**File:** `pipeline/extractor_cms1500.py:70`, `pipeline/extractor_ub04.py:71`

**Issue:** Both extractors do `pytesseract.pytesseract.tesseract_cmd = settings["tesseract_cmd"]`
with a hard subscript, not `.get()`. If `settings` is ever constructed without the
`tesseract_cmd` key (e.g., a test helper that only partially populates the dict), the
call raises an unhelpful `KeyError: 'tesseract_cmd'` rather than a meaningful message.
The same pattern in `detector.py` line 34 has the same issue.

**Fix:** Use `.get()` with a fallback and a clear error:

```python
tess_cmd = settings.get("tesseract_cmd")
if not tess_cmd:
    raise ValueError("settings['tesseract_cmd'] is required but not set")
pytesseract.pytesseract.tesseract_cmd = tess_cmd
```

---

### IN-04: `on_select` replaces the file list rather than appending

**File:** `main.py:103-107`

**Issue:** `on_select` unconditionally replaces `self._files` with the new selection
(`self._files = list(paths)`). If a user calls "Select PDFs" twice to select files from
two different directories, only the second selection is kept. This is a UX limitation
rather than a correctness bug, but it is inconsistent with most multi-select file
pickers where successive calls accumulate selections. It is worth documenting
deliberately if replace-not-append is the intended design.

**Fix:** If accumulation is desired:
```python
if paths:
    self._files.extend(p for p in paths if p not in self._files)
    self.listbox.delete(0, tk.END)
    for p in self._files:
        self.listbox.insert(tk.END, os.path.basename(p))
```
If replace is intentional, add a comment: `# Intentional: each Select call replaces the previous selection (D-07).`

---

_Reviewed: 2026-05-07_
_Reviewer: Claude (adversarial code review)_
_Depth: standard_
