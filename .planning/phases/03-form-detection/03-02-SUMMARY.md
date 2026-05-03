---
plan: 03-02
phase: 03-form-detection
status: complete
completed: 2026-05-03
subsystem: pipeline
tags: [form-detection, ocr, unit-tests, mock]
dependency_graph:
  requires: [03-01]
  provides: [detect_form_type, pipeline/detector.py]
  affects: [pipeline/__init__.py, tests/test_phase3.py]
tech_stack:
  added: []
  patterns: [monkeypatch pytesseract.image_to_string, 3-call anchor OCR, deferred import in tests]
key_files:
  created:
    - pipeline/detector.py
  modified:
    - tests/test_phase3.py
    - pipeline/__init__.py
decisions:
  - "detect_form_type uses 3 OCR calls (header PSM6, footer PSM6, footer PSM11) — PSM6 assembles NUCC footer line; PSM11 finds scattered NUBC text"
  - "Classification requires cms_score >= 2 (not just 1) to avoid false positives from partial anchor matches"
  - "UNKNOWN returned when both cms and UB-04 thresholds simultaneously satisfied (D-05)"
metrics:
  duration: ~5 minutes
  completed: 2026-05-03
  tasks_completed: 2
  files_modified: 3
---

# Phase 03 Plan 02: detector.py + Unit Tests Summary

## One-liner

3-call anchor OCR classifier using HEAL/NUC/FORM1500 and NUBC/UB-04 substrings with score-based thresholds returning CMS-1500, UB-04, or UNKNOWN.

## What Was Built

Created `pipeline/detector.py` with `detect_form_type(image) -> str` implementing 3-call anchor OCR classification. The function crops two regions (_HEADER_STRIP top 600px, _FOOTER_STRIP bottom 400px), runs three pytesseract calls (header PSM6, footer PSM6, footer PSM11), scores CMS-1500 anchors (0-3, needs >=2) and UB-04 anchors (0-2, needs >=1), and returns one of three exact string constants.

Activated 5 unit tests in `tests/test_phase3.py` using monkeypatched pytesseract — no real Tesseract calls needed. Also exported `detect_form_type` from `pipeline/__init__.py` (Rule 3 deviation — required for the test imports).

## Key Files Created/Modified

- `pipeline/detector.py` (new) — detect_form_type with _HEADER_STRIP=(0,0,2550,600), _FOOTER_STRIP=(0,2900,2550,3300), CMS-1500/UB-04/UNKNOWN logic
- `tests/test_phase3.py` (modified) — 5 skip markers removed, test bodies implemented with iterator-based mock responses
- `pipeline/__init__.py` (modified, deviation) — added detect_form_type import and __all__ export

## Verification

- `pytest tests/test_phase3.py -v` exits 0 — 5 passed, 3 skipped
- `pytest tests/ -x` exits 0 — 28 passed, 3 skipped (no Phase 1/2 regressions)
- `python -c "from pipeline.detector import detect_form_type"` works
- `python -c "from pipeline import detect_form_type"` works
- Blank image returns 'UNKNOWN' (verified before commit)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added detect_form_type to pipeline/__init__.py**
- **Found during:** Task 2
- **Issue:** The 5 active test bodies all use `from pipeline import detect_form_type`, but pipeline/__init__.py did not export detect_form_type. Import would fail with ImportError.
- **Fix:** Added `from .detector import detect_form_type` to pipeline/__init__.py and added "detect_form_type" to __all__. This also satisfies test_import_from_pipeline (still skipped — will be formally activated in plan 03-03).
- **Files modified:** pipeline/__init__.py
- **Commit:** 30615ee

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes introduced. detect_form_type reads PIL image pixel data only; OCR output is checked for anchor substrings and discarded. T-03-02 through T-03-05 dispositions in plan threat model are fully satisfied.

## Self-Check: PASSED
