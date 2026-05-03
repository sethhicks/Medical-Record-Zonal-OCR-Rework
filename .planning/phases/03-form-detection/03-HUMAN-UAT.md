---
status: partial
phase: 03-form-detection
source: [03-VERIFICATION.md]
started: 2026-05-03
updated: 2026-05-03
---

## Current Test

[awaiting human testing]

## Tests

### 1. CMS-1500 detection scope acceptance
expected: ROADMAP SC-1 says "every page that contains the expected signature strings" classifies as CMS-1500. RESEARCH.md found ~6 of ~28 actual CMS-1500 pages return UNKNOWN because OCR cannot recover their anchor text (pages 4, 8, 14, 17, 22, 23). Confirm whether OCR-degraded pages are considered to "contain" those strings, or whether the 22/28 empirical result satisfies the criterion intent.
result: [pending]

### 2. UB-04 page count and UNKNOWN for page 11
expected: CLAUDE.md says "~3 UB-04" but RESEARCH.md confirms only 2 UB-04 pages exist (pages 6 and 11). Page 11 returns UNKNOWN because its NUBC text is OCR-unrecoverable. The ROADMAP SC references "3 UB-04 pages." Confirm whether 2 UB-04 pages + expected UNKNOWN for page 11 is accepted, or requires a correction to assumptions.
result: [pending]

### 3. conftest.py bare assert for test.pdf path (CR-01)
expected: conftest.py uses `assert path.exists()` not `pytest.skip()` in the test_pdf_path session fixture. Since test.pdf is untracked (not in git), any CI environment missing test.pdf will produce AssertionError/ERROR for the 2 smoke tests rather than graceful SKIPPED. Confirm whether this is acceptable for your CI setup, or whether it should be fixed before closing Phase 3.
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
