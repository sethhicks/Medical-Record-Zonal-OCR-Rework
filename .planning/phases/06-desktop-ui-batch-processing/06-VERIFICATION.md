---
phase: 06-desktop-ui-batch-processing
verified: 2026-05-07T17:14:12Z
status: human_needed
must_haves_verified: 4/5
score: 4/5
overrides_applied: 0
human_verification:
  - test: "Launch python main.py and perform a complete file-selection and run cycle"
    expected: "Window opens at ~500x400, non-resizable; file picker works; progress bar updates without freezing; error log populates for failures; Open output file button becomes active on completion"
    why_human: "SC-2 requires visual confirmation that the window stays responsive during a live OCR run — pytest tests verify the threading model structurally (queue messages, no widget calls from worker) but cannot confirm the window does not freeze during real processing"
---

# Phase 6: Desktop UI & Batch Processing Verification Report

**Phase Goal:** Billing staff can select one or more PDFs, watch per-page progress, and open the output file from a desktop window — with errors surfaced rather than silently dropped.
**Verified:** 2026-05-07T17:14:12Z
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | File picker dialog opens and selected PDFs populate the listbox | VERIFIED | `test_select_pdfs_populates_listbox` passes; `on_select` calls `filedialog.askopenfilenames`, inserts `os.path.basename(p)` into `self.listbox` |
| 2 | Progress bar and page counter update during processing without freezing the window | UNCERTAIN (human needed) | `test_queue_progress_message_format` and `test_queue_done_message_format` verify the queue contract; `threading.Thread(daemon=True)` + `root.after(100, self.poll_queue)` are present in main.py; actual responsiveness during a live OCR run requires human observation |
| 3 | Multi-PDF batch run produces a single combined extracted_results.xlsx | VERIFIED | `test_batch_multi_pdf_produces_output` passed (943s; 60 pages across two copies of test.pdf); workbook has CMS-1500 and UB-04 sheets with data rows |
| 4 | [Open output file] button is enabled on completion and opens the file | VERIFIED | `_on_done` calls `self.btn_open.config(state=tk.NORMAL)` when `output_path` is not None (main.py:287-288); `on_open_output` calls `os.startfile(self._output_path)` (main.py:307); `test_queue_done_message_format` verifies the done-message contract |
| 5 | UNKNOWN/exception pages appear as blank rows with extraction_error populated | VERIFIED | `test_worker_unknown_page_posts_error` passes: mocks `detect_form_type` to return "UNKNOWN", runs `_worker`, verifies (a) error tuple posted to queue, (b) error_count in done message >= 1, (c) `extraction_error` column present in CMS-1500 sheet with non-empty value |

**Score:** 4/5 truths verified; 1 requires human observation (SC-2 visual responsiveness)

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `main.py` | Full OCRApp class (>150 lines) | VERIFIED | 337 lines; parses cleanly (`python -c "import ast; ast.parse(...)"`) |
| `main.py` | `class OCRApp` | VERIFIED | Line 17 |
| `main.py` | `root.resizable(False, False)` | VERIFIED | Line 42 |
| `main.py` | `threading.Thread(` | VERIFIED | Line 136 |
| `main.py` | `queue.Queue()` | VERIFIED | Line 36 |
| `main.py` | `root.after(100, self.poll_queue)` | VERIFIED | Lines 139, 271 |
| `main.py` | `error_pages` accumulator | VERIFIED | Line 172 |
| `main.py` | `os.makedirs(` (WR-02 fix) | VERIFIED | Line 201 |
| `main.py` | `os.startfile(` | VERIFIED | Line 307 |
| `main.py` | `UNKNOWN form type` | VERIFIED | Lines 184, 185 |
| `main.py` | `extraction_error` post-processing | VERIFIED | Lines 215-223 |
| `tests/test_phase6.py` | 12 active tests, 0 skipped | VERIFIED | `grep @pytest.mark.skip` returns 0 matches; 12 functions collected |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `main.py _worker()` | `queue.Queue` | `self._queue.put(('progress', n, total))` | WIRED | Line 178 confirmed |
| `main.py poll_queue()` | `ttk.Progressbar` | `self.progress_bar['value'] = pct` | WIRED | Line 250 confirmed |
| `main.py on_open_output()` | `os.startfile` | `os.startfile(self._output_path)` | WIRED | Line 307 confirmed |
| `main.py _worker()` | `pipeline.write_workbook` | `pipeline.write_workbook(cms_pages, ub_pages, settings)` | WIRED | Line 203 confirmed |
| `main.py _on_done()` | `btn_open` enable | `self.btn_open.config(state=tk.NORMAL)` | WIRED | Line 288 — conditional on `output_path` being non-None |
| `tests/test_phase6.py test_worker_smoke_real_pdf` | `main.OCRApp._worker` | direct thread call on real OCRApp instance | WIRED | Test body at line 276-311 |
| `tests/test_phase6.py test_batch_multi_pdf_produces_output` | `pipeline.write_workbook` | `openpyxl.load_workbook` asserts data rows | WIRED | Test body at line 315-363 |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `main.py OCRApp` | `cms_pages` / `ub_pages` | `pipeline.extract_cms1500` / `pipeline.extract_ub04` called per page in `_worker` | Yes — populated from real OCR extraction pipeline | FLOWING |
| `main.py OCRApp` | `error_pages` | UNKNOWN branch and except clause in `_worker` | Yes — populated from real pipeline exceptions and UNKNOWN classifications | FLOWING |
| `main.py OCRApp` | `output_path` | `pipeline.write_workbook(cms_pages, ub_pages, settings)` return value | Yes — real file written to `output_dir` | FLOWING |
| `main.py OCRApp` | `self.progress_bar['value']` | queue message `('progress', current, total)` posted by `_worker`, consumed by `poll_queue` | Yes — advances per real page processed | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| main.py syntax is valid | `python -c "import ast; ast.parse(open('main.py').read())"` | `syntax OK` | PASS |
| main module importable without side effects | `python -m pytest tests/test_phase6.py::test_import_main -v` | PASSED | PASS |
| 10 unit/integration tests pass (non-long) | `pytest tests/test_phase6.py -k "not smoke and not batch"` | 10 passed, 0 failed | PASS |
| Prior 60 tests pass (phases 1-5, no regressions) | `pytest tests/ --ignore=tests/test_phase6.py` | 60 passed in 110s | PASS |
| Worker produces output on real PDF (integration) | SUMMARY confirms `test_worker_smoke_real_pdf` passed in 467s; `test_batch_multi_pdf_produces_output` passed in 943s | Accepted from SUMMARY — long-running tests not re-run during verification | PASS (prior run evidence) |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| UI-01 | 06-01, 06-02, 06-03 | Desktop GUI file-picker dialog filtered to *.pdf | SATISFIED | `on_select` calls `filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])`; `test_select_pdfs_populates_listbox` passes |
| UI-02 | 06-01, 06-02, 06-03 | Progress bar + page counter; UI responsive on background thread | SATISFIED (structural) | `threading.Thread(daemon=True)` + `root.after(100, poll_queue)` wired; queue message contract tested; visual responsiveness requires human check |
| UI-03 | 06-01, 06-02, 06-03 | On completion a button opens the output Excel in default app | SATISFIED | `btn_open` enabled in `_on_done`; `os.startfile` called in `on_open_output` |
| UI-04 | 06-01, 06-02, 06-03 | Failed pages appear as blank rows with extraction_error populated; errors displayed in UI | SATISFIED | `test_worker_unknown_page_posts_error` fully exercises this path end-to-end with openpyxl assertion |
| PROC-04 | 06-01, 06-02, 06-03 | Multiple PDFs in single run | SATISFIED | `test_batch_multi_pdf_produces_output` ran two copies of test.pdf; combined workbook with rows in both sheets |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `main.py` | 162-167 | `pdfinfo_from_path` exception silently sets `n_pages=0` — no error posted to queue | Warning | User gets no indication that a selected PDF was entirely skipped (WR-03 from 06-REVIEW.md) |
| `main.py` | 213-230 | openpyxl workbook opened without guaranteed close on KeyError path | Warning | File handle leak on partial-write workbook (WR-01 from 06-REVIEW.md); mitigated by CPython ref counting |
| `main.py` | 295-302 | `_on_done` inserts summary line without `see(tk.END)` | Warning | Summary line may not auto-scroll into view if error log is full (WR-02 from 06-REVIEW.md) |
| `pipeline/detector.py` | 33 | `detect_form_type` calls `load_settings()` on every invocation | Warning | 30+ disk reads per batch; settings could change mid-run (WR-04 from 06-REVIEW.md); does not break correctness today |

None of the anti-patterns block the phase goal. All were identified and documented in the 06-REVIEW.md code review. No anti-patterns were discovered during this verification that were not already known.

---

### Human Verification Required

#### 1. Visual UI Responsiveness (SC-2)

**Test:** Run `python main.py`. Load `test.pdf` via the file picker. Click Start. While OCR processing runs (~7-8 minutes for 30 pages):
- Move the window
- Observe that the progress bar and page counter advance every few seconds
- Confirm the window title bar remains interactive and does not show "(Not Responding)"
- Confirm the error log scrolls as errors are appended

**Expected:** Window remains fully interactive throughout the run. Progress bar and page counter update at each page boundary. No "not responding" freeze.

**Why human:** The threading model (`threading.Thread` + `queue.Queue` + `root.after(100)`) is structurally correct and verified by the queue-message tests. However, whether the window actually stays responsive under the real OCR workload — where each page may take 14+ seconds — can only be confirmed by a human watching the live application. A frozen main thread due to contention or polling overhead would not be caught by the automated test suite.

---

### Gaps Summary

No blocking gaps were found. All five phase success criteria have structural implementation verified in the codebase:

- SC-1 (file picker): Fully implemented and tested
- SC-2 (progress without freezing): Threading model is correctly implemented; responsiveness requires human confirmation
- SC-3 (multi-PDF combined output): Integration tests passed on real PDFs
- SC-4 (Open output button): Implemented and wired; `btn_open` enabled in `_on_done`
- SC-5 (blank rows with extraction_error): Fully implemented in `_worker` post-write openpyxl step; verified by `test_worker_unknown_page_posts_error`

Four code-quality warnings exist (WR-01 through WR-04, documented in 06-REVIEW.md) but none block the phase goal.

The `status: human_needed` reflects SC-2's visual responsiveness requirement only. Once a developer confirms the window stays responsive during a live processing run, this phase can be considered fully passed.

---

_Verified: 2026-05-07T17:14:12Z_
_Verifier: Claude (gsd-verifier)_
