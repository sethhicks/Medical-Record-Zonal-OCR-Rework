# Phase 6: Desktop UI & Batch Processing - Context

**Gathered:** 2026-05-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a tkinter desktop window in `main.py` that wires all pipeline stages together: billing staff select one or more PDFs, watch a per-page progress bar, and click "Open output file" on completion. The worker runs on a background thread; the UI stays responsive throughout. Errors surface inline rather than silently disappearing. No changes to detection, extraction, or writer logic — pure integration and UI.

</domain>

<decisions>
## Implementation Decisions

### UI Framework
- **D-01:** tkinter — ships with Python 3.11 stdlib, zero extra install for billing staff. No upgrade to PyQt5.
- **D-02:** Startup dependency check blocks the window from appearing. `setup_check.run_checks()` is called before `Tk()` is constructed. If Tesseract or Poppler is missing, show `messagebox.showerror(...)` and `sys.exit(1)`. Window only appears when deps are confirmed good.
- **D-03:** Fixed window size (~500×400 px), non-resizable (`root.resizable(False, False)`). Simple layout with no reflow needed.

### Output Directory
- **D-04:** Output location is always `settings['output_dir']` (default: Desktop). No per-run folder picker in the UI. Filename is always `extracted_results.xlsx` (locked in Phase 5 D-05). Users who want a different location edit `settings.json`. **This resolves the open decision flagged in STATE.md.**
- **D-05:** A read-only label in the window displays the full output path before and during the run. Format: `Output: {output_dir}\extracted_results.xlsx`. After completion, this label still points to the file the "Open output file" button will open.

### File List UX
- **D-06:** After selecting files, a `tk.Listbox` widget displays the selected filenames (basenames only via `os.path.basename`) so billing staff can review before starting.
- **D-07:** Three buttons in the top row: **[Select PDFs]** (calls `filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])`), **[Clear]** (clears the listbox and internal file list), **[Start]** (begins the run).
- **D-08:** No cancel button. During processing, disable [Select PDFs], [Clear], and [Start]. The UI remains responsive (progress bar and error log update) but the run cannot be interrupted.
- **D-09:** After a run completes, re-enable [Select PDFs], [Clear], and [Start]; clear the file list so billing staff can queue a new batch. The "Open output file" button stays visible and active. The window is fully reusable without restarting the app.

### Progress Display
- **D-10:** Progress bar (`ttk.Progressbar`, determinate mode) and a page counter label (e.g., `"Page 7 / 30"`) update for each page processed via `root.after(100, poll_queue)`. Threading model locked in STATE.md: `threading.Thread` + `queue.Queue` — never call tkinter widgets from the worker thread.

### Error Display
- **D-11:** A `tk.Text` widget (read-only, `state=DISABLED`, ~4 lines tall, with a `tk.Scrollbar`) is always visible in the layout — part of the fixed window from startup. It is empty at idle.
- **D-12:** Each error line format: `{basename(filename)} page {N}: {error_message}` — enough context for billing staff to identify which page to recheck manually.
- **D-13:** The error log is cleared at the start of each new run so stale errors from previous batches don't accumulate.
- **D-14:** UNKNOWN-classified pages are written as blank Excel rows with `extraction_error = "UNKNOWN form type"` (pre-existing behavior from Phase 3/4). The UI logs these to the error widget using the same line format as other errors.

### Claude's Discretion
- **Widget layout order:** top-to-bottom arrangement (file list → output label → progress bar + counter → error log → buttons) or side-by-side grouping — planner's call within the fixed ~500×400 window.
- **ttk vs plain tk:** Use `ttk` widgets where they give a better Windows native look (e.g., `ttk.Progressbar`, `ttk.Button`) but fall back to plain `tk` for widgets without a ttk equivalent (e.g., `tk.Listbox`, `tk.Text`).
- **`mkdir -p output_dir` before `write_workbook()`:** If `output_dir` doesn't exist (e.g., Desktop path on a new machine), create it silently rather than letting `write_workbook()` crash. This is the fix for the code review finding WR-02 noted in STATE.md.
- **Page counter strategy:** Worker thread posts `("progress", current, total)` tuples to the queue; the poll callback reads them and updates both the `Progressbar` value and the counter label in a single tick.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Requirements
- `.planning/REQUIREMENTS.md` — UI-01, UI-02, UI-03, UI-04, PROC-04 (full v1 acceptance criteria for this phase)
- `.planning/ROADMAP.md` §Phase 6 — 5 success criteria defining exactly what must be true when this phase is complete

### Project Context
- `.planning/PROJECT.md` — billing staff use case, stack decisions, out-of-scope items
- `.planning/STATE.md` — threading model decision (`threading.Thread` + `queue.Queue` + `root.after(100, poll)`); open decision for output filename convention (resolved by D-04); known code review issues WR-01/WR-02/WR-03 from Phase 5

### Prior Phase Outputs (integration contracts)
- `.planning/phases/05-output-excel-export/05-CONTEXT.md` — D-05: `write_workbook()` returns full output path as `str`; D-06: `write_workbook(cms_pages, ub_pages, settings) -> str`; D-10: UNKNOWN pages not passed to writer (Phase 6 handles as error rows)
- `pipeline/__init__.py` — current exports: `convert_page`, `preprocess_page`, `detect_form_type`, `extract_cms1500`, `extract_ub04`, `write_workbook`; Phase 6 calls all of these from the worker thread

### Existing Code (read before planning)
- `main.py` — Phase 6 entry point (currently a placeholder); Phase 6 populates this file with `Tk()` root, startup check, and `mainloop()`
- `setup_check.py` — `run_checks()` validates Tesseract + Poppler; returns/raises on failure; called before window opens (D-02)
- `config_loader.py` — `load_settings()` returns `output_dir`, `confidence_threshold`, `tesseract_cmd`, `poppler_path`; called once at startup and passed as `settings` dict throughout
- `models/field_result.py` — `FieldResult(field_name, value, confidence)`; worker thread returns lists of these per page

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pipeline.convert_page(pdf_path, page_num)` → raw PIL Image (per page)
- `pipeline.detect_form_type(raw_image)` → `'CMS-1500'` | `'UB-04'` | `'UNKNOWN'`
- `pipeline.preprocess_page(raw_image, settings)` → preprocessed PIL Image
- `pipeline.extract_cms1500(preprocessed, settings)` → `list[FieldResult]`
- `pipeline.extract_ub04(preprocessed, settings)` → `list[FieldResult]`
- `pipeline.write_workbook(cms_pages, ub_pages, settings)` → `str` (full output path)
- `setup_check.run_checks()` — call before `Tk()` construction
- `config_loader.load_settings()` — call once at startup

### Established Patterns
- Stateless functions: all pipeline stages take `(input, settings)` and return output — worker thread calls them in sequence
- Windows-explicit binary paths: `tesseract_cmd` and `poppler_path` from `settings` must be set before any OCR or PDF conversion
- Test file naming: `tests/test_phase6.py` — one file per phase, stubs-first Wave 0 pattern

### Integration Points
- Worker thread per-page sequence: `raw = convert_page(pdf, n)` → `form = detect_form_type(raw)` → `proc = preprocess_page(raw, settings)` → `results = extract_cms1500(proc, settings)` or `extract_ub04(proc, settings)` (or error row on UNKNOWN/exception)
- After all pages: `output_path = write_workbook(cms_pages, ub_pages, settings)` → post `("done", output_path)` to queue
- Poll callback reads queue: `("progress", n, total)` → update bar + label; `("error", filename, page, msg)` → append to error log; `("done", path)` → enable "Open output file" button, re-enable controls
- `os.startfile(output_path)` opens the Excel file in the system default application (Windows only — correct for this single-user Windows desktop tool)

</code_context>

<specifics>
## Specific Ideas

- Window layout sketch (top-to-bottom, fixed ~500×400):
  ```
  ┌─────────────────────────────────┐
  │  [Select PDFs]  [Clear]         │
  │ ┌──────────────────────────┐    │
  │ │ claims_jan.pdf           │    │
  │ │ claims_feb.pdf           │    │
  │ │ overflow_batch.pdf       │    │
  │ └──────────────────────────┘    │
  │  Output: Desktop\extracted...   │
  │  [████████░░░░░░] Page 7 / 30   │
  │ ┌──────────────────────────────┐│
  │ │ claims_jan.pdf page 4: ...   ││
  │ └──────────────────────────────┘│
  │  [Start]       [Open output]    │
  └─────────────────────────────────┘
  ```
- User selected this layout style during discussion (file list visible before start)
- "Open output file" button uses `os.startfile(output_path)` — Windows-native, no subprocess needed
- Error log Text widget: `state=NORMAL` to insert, then `state=DISABLED` to lock — standard tkinter read-only pattern

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 6 — Desktop UI & Batch Processing*
*Context gathered: 2026-05-07*
