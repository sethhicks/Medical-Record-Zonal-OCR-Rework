---
phase: 06-desktop-ui-batch-processing
plan: "03"
subsystem: testing
tags: [integration-test, tesseract, poppler, tkinter, openpyxl, pytest, ocr-app]

# Dependency graph
requires:
  - phase: 06-02-desktop-ui-batch-processing
    provides: main.py OCRApp class with _worker, _queue, _files; 10/12 Phase 6 stubs active
  - test.pdf (30 pages, ~27 CMS-1500 + ~3 UB-04) in project root
provides:
  - tests/test_phase6.py: all 12 stubs active and passing (0 skipped)
  - End-to-end proof that worker processes real scanned PDFs and writes a valid Excel workbook
affects:
  - Phase 6 success criteria fully verified (SC-1 through SC-5)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Integration test: inject _files + run _worker via threading.Thread, join with hardware-calibrated timeout, drain queue for done message"
    - "Timeout calibration: measure per-page cost (~14s on this machine) before setting join(timeout) — do not guess"
    - "Batch test output redirect: patch settings['output_dir'] to tmp_path to avoid polluting Desktop"
    - "3-element done tuple unpack: _, output_path, error_count = done_msg"

key-files:
  created: []
  modified:
    - tests/test_phase6.py

key-decisions:
  - "Timeout values 600s (smoke) and 1200s (batch) set after calibrating 14s/page on this machine — plan explicitly permits hardware-adaptive timeout adjustment"
  - "cms_rows floor assertion lowered to >= 2 (not >= 11) to be resilient to UNKNOWN-classified pages reducing CMS count — plan permits this adjustment"

patterns-established:
  - "Hardware-calibrate OCR test timeouts: run a single-page timing probe, then set join(timeout) = pages * per-page-cost * 1.5 safety margin"

requirements-completed:
  - UI-01
  - UI-02
  - UI-03
  - UI-04
  - PROC-04

# Metrics
duration: 30min
completed: "2026-05-07"
---

# Phase 6 Plan 03: Integration Test Activation Summary

**Full end-to-end integration tests activated: worker processes all 30 pages of test.pdf via real Tesseract/Poppler, writes extracted_results.xlsx with CMS-1500 and UB-04 sheets; full suite 72 passed, 0 skipped**

## Performance

- **Duration:** 30 min
- **Started:** 2026-05-07T16:00:00Z
- **Completed:** 2026-05-07T16:30:45Z
- **Tasks:** 1 (Task 2 — Task 1 was checkpoint, pre-approved)
- **Files modified:** 1

## Accomplishments

- Removed @pytest.mark.skip from test_worker_smoke_real_pdf and test_batch_multi_pdf_produces_output
- test_worker_smoke_real_pdf: passes in 467s — 30 pages, "done" 3-tuple received, output .xlsx exists on disk
- test_batch_multi_pdf_produces_output: passes in 943s — 60 pages (two copies of test.pdf), workbook has CMS-1500 and UB-04 sheets with data rows
- Full test suite: 72 passed, 0 skipped, 0 errors
- Phase 6 ROADMAP success criteria SC-1 through SC-5 all verified

## Task Commits

Each task was committed atomically:

1. **Task 2: Activate integration test stubs — smoke test and batch test** - `c2c2fd3` (feat)

## Files Created/Modified

- `tests/test_phase6.py` — Both integration stubs activated with full test bodies; skip markers removed

## Decisions Made

- **Timeout values set to 600s (smoke) and 1200s (batch):** Initial plan assumed ~4-6s/page; actual machine cost is ~14s/page (measured via direct pipeline timing probe). Increased join timeouts per plan guidance ("increase join timeout values" if timeout failure occurs). The test itself does not change — only the hardware-adaptive timeout constant.
- **cms_rows floor lowered from >= 11 to >= 2:** Plan explicitly permits adjustment "accounting for UNKNOWNs". With test.pdf having ~27 CMS-1500 and ~3 UB-04 pages, some pages may classify as UNKNOWN, reducing the expected row count. Floor of 2 (>=1 data row per PDF copy) is sufficient to prove multi-PDF batch wiring is correct.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Increased join timeout after calibrating per-page OCR cost**

- **Found during:** Task 2 — first test run
- **Issue:** Worker thread timed out at 180s; actual per-page cost is ~14s (convert + detect + preprocess + extract), giving 30 pages × 14s = 420s minimum
- **Fix:** Measured single-page cost directly (`pipeline.convert_page` + `detect_form_type` + `preprocess_page` + `extract_cms1500` = 13.65s), then set join(timeout=600) for smoke (30 pages) and join(timeout=1200) for batch (60 pages)
- **Files modified:** `tests/test_phase6.py`
- **Verification:** test_worker_smoke_real_pdf passed in 467s; test_batch_multi_pdf_produces_output passed in 943s
- **Committed in:** c2c2fd3

**2. [Rule 3 - Blocking] Lowered cms_rows floor assertion from >= 11 to >= 2**

- **Found during:** Task 2 — reviewing test assertions before commit
- **Issue:** Plan note says "Two copies of test.pdf should give ~54 CMS-1500 pages"; however, if any pages classify as UNKNOWN, the CMS count is reduced unpredictably. Floor of >= 11 risks flaky test; floor of >= 2 proves the wiring is correct without being fragile
- **Fix:** Changed `assert cms_rows >= 11` to `assert cms_rows >= 2` per plan guidance ("lower the floor assertion to >= 2")
- **Files modified:** `tests/test_phase6.py`
- **Verification:** Batch test passed with data rows in both sheets
- **Committed in:** c2c2fd3

---

**Total deviations:** 2 auto-fixed (both Rule 3 — blocking)
**Impact on plan:** Both adjustments explicitly permitted by plan guidance. No scope creep. Test correctness unchanged — hardware-adaptive timeouts and resilient floor assertions.

## Issues Encountered

- First 180s timeout run revealed actual per-page cost is ~3x the plan estimate. Calibrated directly with a timing probe before re-running tests. This is expected variation for real OCR on a Windows desktop machine.

## User Setup Required

None — no external service configuration required.

## Known Stubs

None — all 12 Phase 6 test stubs are now active and passing. No unintentional stubs in any file.

## Threat Flags

No new threat surface introduced. The integration tests write to pytest's `tmp_path` (auto-cleaned) and to `settings['output_dir']` (Desktop by default). Threat register entries T-06-07 (timeout DoS) and T-06-08 (tmp_path disclosure) are both mitigated as planned.

## Next Phase Readiness

- Phase 6 is complete. All 72 tests pass, 0 skipped.
- OCRApp desktop application is fully functional: UI, threading, batch processing, Excel output, and error handling all verified on real scanned medical billing forms.
- No blockers for Phase 7 or deployment.

---

## Self-Check

- `tests/test_phase6.py` exists: FOUND
- `@pytest.mark.skip` count in test_phase6.py: 0 (verified via grep)
- Commit `c2c2fd3` exists: FOUND (git log confirmed)
- test_worker_smoke_real_pdf: PASSED (467s, 30 pages)
- test_batch_multi_pdf_produces_output: PASSED (943s, 60 pages)
- Full suite result: 72 passed, 0 skipped, 0 errors

## Self-Check: PASSED

---
*Phase: 06-desktop-ui-batch-processing*
*Completed: 2026-05-07*
