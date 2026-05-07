---
phase: 06-desktop-ui-batch-processing
plan: "02"
subsystem: desktop-ui
tags: [tkinter, threading, queue, ocr-app, batch-processing, excel]

# Dependency graph
requires:
  - phase: 06-01-desktop-ui-batch-processing
    provides: tests/test_phase6.py with 12 skipped stubs
  - phase: 05-output-excel-export
    provides: write_workbook(cms_pages, ub_pages, settings) -> str
  - pipeline/__init__.py exports (convert_page, preprocess_page, detect_form_type, extract_cms1500, extract_ub04, write_workbook)
  - setup_check.run_checks() for startup dependency validation
  - config_loader.load_settings() for settings dict
provides:
  - main.py: OCRApp class with full tkinter desktop UI — 336 lines
  - tests/test_phase6.py: 10/12 stubs activated and passing; 2 remain for 06-03-PLAN
affects:
  - 06-03-PLAN (activates 2 remaining stubs — worker smoke + batch multi-PDF integration)

# Tech tracking
tech-stack:
  added:
    - tkinter (stdlib) — Tk root window, ttk.Button, ttk.Progressbar, tk.Listbox, tk.Text, tk.Scrollbar
    - threading.Thread — background worker for OCR pipeline
    - queue.Queue — thread-safe UI update channel
    - openpyxl (already in stack) — post-write blank-row append for error pages (D-14/SC-5)
  patterns:
    - "Queue message contract: ('progress', n, total) | ('error', file, page, msg) | ('done', path, error_count)"
    - "poll_queue: root.after(100, self.poll_queue) — drains queue per tick, stops on 'done'"
    - "Worker never touches tkinter widgets — all UI updates via queue + main thread poll"
    - "Post-write openpyxl: open saved workbook, append blank rows for error_pages with extraction_error col"
    - "WR-02 fix: os.makedirs(output_dir, exist_ok=True) before write_workbook()"
    - "Startup gate: run_checks(quiet=True) -> bool; sys.exit(1) if False, before Tk() construction"
    - "Fake-app technique for tkinter worker tests: bind unbound method to lightweight stand-in object"

key-files:
  created: []
  modified:
    - main.py
    - tests/test_phase6.py

key-decisions:
  - "D-01 through D-14 from 06-CONTEXT.md all implemented in main.py"
  - "Worker uses daemon=True thread so it terminates automatically if main thread exits (T-06-03 mitigate)"
  - "test_worker_unknown_page_posts_error uses lightweight _FakeApp stand-in instead of tk.Tk() to avoid Windows Tcl teardown issue across tests"
  - "Startup error dialog: create temporary hidden Tk() to host messagebox before sys.exit(1) — messagebox requires Tk to be initialized"

# Metrics
duration: 6min
completed: "2026-05-07"
---

# Phase 6 Plan 02: OCRApp Desktop UI Implementation Summary

**Full tkinter OCRApp class (336 lines) wiring all pipeline stages behind a responsive 500x400 windowed interface with threading.Thread + queue.Queue model; 10/12 Phase 6 test stubs activated and green**

## Performance

- **Duration:** 6 min
- **Started:** 2026-05-07T15:28:45Z
- **Completed:** 2026-05-07T15:34:45Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- main.py completely replaced (placeholder to full 336-line OCRApp class)
- All D-01 through D-14 decisions from 06-CONTEXT.md implemented
- Window: 500x400 fixed, non-resizable, title "OCR Medical Billing Extractor"
- Layout: Select PDFs + Clear buttons, Listbox (5 rows), output label, progress bar + page counter, error log (Text+Scrollbar), Start + Open output buttons
- Worker thread: threading.Thread(daemon=True) + queue.Queue; NEVER touches tkinter widgets
- poll_queue: root.after(100) tick — drains queue; updates progressbar, error log; calls _on_done on "done"
- UNKNOWN pages and exception pages both post ("error", ...) to queue AND accumulate in error_pages list
- After write_workbook() returns, _worker opens saved .xlsx with openpyxl and appends blank rows for each error page with extraction_error column populated (D-14 / SC-5)
- ("done", output_path, error_count) 3-tuple carries failure count; _on_done shows summary line when error_count > 0
- os.makedirs(output_dir, exist_ok=True) called before write_workbook() — WR-02 fix
- os.startfile(output_path) opens Excel in default app; shows showerror if file not found
- 10/12 test stubs activated and passing; 2 integration stubs remain for 06-03-PLAN
- Phase 6 test suite: 10 passed, 2 skipped, 0 failed (in worktree environment)

## Task Commits

Each task was committed atomically:

1. **Task 1: OCRApp window construction and file-selection handlers** - `9faeb49` (feat)
2. **Task 2: Activate 10 Phase 6 test stubs; worker thread + completion handler** - `38ff4a5` (feat)

## Files Created/Modified

- `main.py` — Full OCRApp class implementation (336 lines; created from placeholder)
- `tests/test_phase6.py` — 10 stubs activated with real test implementations; 2 remain for 06-03-PLAN

## Decisions Made

- D-01 through D-14 from 06-CONTEXT.md all implemented (see key-decisions)
- _on_done: Only enables "Open output file" if output_path is not None (handles write_workbook exception case)
- Startup messagebox requires an initialized Tk instance; created a hidden temporary root for the error dialog before sys.exit(1)
- Worker test uses lightweight _FakeApp object (binds unbound method via types.MethodType) to avoid Windows Tcl teardown corruption across test suite

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Windows tkinter Tcl teardown in test_worker_unknown_page_posts_error**

- **Found during:** Task 2 — test activation
- **Issue:** On Windows, after multiple `tk.Tk()` create+destroy cycles in the same process, the Tcl state becomes corrupted. `test_worker_unknown_page_posts_error` was the 7th test to call `tk.Tk()` and received `TclError: Can't find a usable init.tcl`. The test passes in isolation but fails in the full suite.
- **Fix:** Replaced `tk.Tk()` + `OCRApp(root, settings)` in the test with a lightweight `_FakeApp` stand-in object that only exposes `_files`, `_queue`, and `settings` (the only attributes `_worker` accesses). Used `types.MethodType(main.OCRApp._worker, fake_app)` to bind the unbound method. The worker logic is fully exercised without constructing a Tk window.
- **Files modified:** `tests/test_phase6.py`
- **Commit:** `38ff4a5`

## Known Stubs

Two intentional test stubs remain skipped for Wave 2 (06-03-PLAN):
- `test_worker_smoke_real_pdf` — requires real Tesseract + test.pdf (~60s runtime)
- `test_batch_multi_pdf_produces_output` — requires real Tesseract + test.pdf

No unintentional stubs in main.py. All UI paths are fully wired.

## Threat Flags

No new threat surface beyond what is documented in the plan's threat model:

| Flag | File | Description |
|------|------|-------------|
| (none) | main.py | No new network endpoints, auth paths, or trust boundaries introduced |

All threats from the plan's STRIDE register are addressed:
- T-06-03: daemon=True thread auto-terminates on main exit
- T-06-06: run_checks() gates Tk() construction; sys.exit(1) on failure

## Self-Check: PASSED

- `main.py` exists: FOUND (336 lines)
- `tests/test_phase6.py` exists: FOUND
- `class OCRApp` in main.py: VERIFIED
- `root.resizable(False, False)` in main.py: VERIFIED
- `threading.Thread(` in main.py: VERIFIED
- `queue.Queue()` in main.py: VERIFIED
- `root.after(100, self.poll_queue)` in main.py: VERIFIED
- `error_pages` in main.py: VERIFIED
- `os.makedirs(` in main.py: VERIFIED
- `os.startfile(` in main.py: VERIFIED
- `UNKNOWN form type` in main.py: VERIFIED
- `extraction_error` in main.py: VERIFIED
- Commit `9faeb49` exists: FOUND
- Commit `38ff4a5` exists: FOUND
- pytest tests/test_phase6.py: 10 passed, 2 skipped, 0 failed: VERIFIED

---
*Phase: 06-desktop-ui-batch-processing*
*Completed: 2026-05-07*
