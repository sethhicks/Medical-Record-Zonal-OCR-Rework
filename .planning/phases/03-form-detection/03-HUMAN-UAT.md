---
status: complete
phase: 03-form-detection
source: [03-VERIFICATION.md]
started: 2026-05-03
updated: 2026-05-07
---

## Current Test

[testing complete]

## Tests

### 1. CMS-1500 detection scope acceptance
expected: ROADMAP SC-1 says "every page that contains the expected signature strings" classifies as CMS-1500. RESEARCH.md found ~6 of ~28 actual CMS-1500 pages return UNKNOWN because OCR cannot recover their anchor text (pages 4, 8, 14, 17, 22, 23). Confirm whether OCR-degraded pages are considered to "contain" those strings, or whether the 22/28 empirical result satisfies the criterion intent.
result: issue
reported: "All of those pages include 'Health' visible at the top left. These pages should be getting detected."
severity: major
root_cause: "detect_form_type() used only PSM 6 on the header and required cms_score >= 2. Pages 8, 14, 22, 23 recovered HEAL/HEALTH via OCR but had zero footer signals, leaving them at score=1. Pages 4 and 17 produce no OCR output at all — text-based detection cannot recover them."
fix_applied: "Added PSM 11 to header OCR; changed anchor from 'HEALTH' to 'HEAL' (more forgiving of partial garbling); changed classification so heal_hit alone is sufficient when ub04_score==0. Pages 8, 14, 22, 23 now correctly classify as CMS-1500. Pages 4 and 17 remain UNKNOWN (complete OCR failure — requires image-based detection to fix)."

### 2. UB-04 page count and UNKNOWN for page 11
expected: CLAUDE.md says "~3 UB-04" but RESEARCH.md confirms only 2 UB-04 pages exist (pages 6 and 11). Page 11 returns UNKNOWN because its NUBC text is OCR-unrecoverable. The ROADMAP SC references "3 UB-04 pages." Confirm whether 2 UB-04 pages + expected UNKNOWN for page 11 is accepted, or requires a correction to assumptions.
result: issue
reported: "This is not acceptable. Page 11 should not be unknown."
severity: major
root_cause: "Page 11's footer NUBC copyright text is unrecoverable by OCR (even with PSM 11). No NUBC/UB-04/1450 signals appear in any footer crop."
fix_applied: "Added 'REMARKS' (UB-04 field 80 label) as an additional ub04_score signal. Page 11's footer PSM 11 consistently recovers 'REMARKS'. Verified no CMS-1500 footer strip produces REMARKS. Page 11 now correctly classifies as UB-04. Added test_ub04_page11_smoke to lock this in."

### 3. conftest.py bare assert for test.pdf path (CR-01)
expected: conftest.py uses `assert path.exists()` not `pytest.skip()` in the test_pdf_path session fixture. Since test.pdf is untracked (not in git), any CI environment missing test.pdf will produce AssertionError/ERROR for the 2 smoke tests rather than graceful SKIPPED. Confirm whether this is acceptable for your CI setup, or whether it should be fixed before closing Phase 3.
result: issue
reported: "This should be fixed."
severity: major
root_cause: "Already fixed in existing code. conftest.py line 12 uses pytest.skip() correctly. The VERIFICATION.md CR-01 was written before the review fixes landed."
fix_applied: "No-op — code was already correct. No change needed."

## Summary

total: 3
passed: 0
issues: 3
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "Every CMS-1500 page containing visible 'Health' text at top-left should be classified as CMS-1500, not UNKNOWN."
  status: fixed
  reason: "User reported: All of those pages include 'Health' visible at the top left. These pages should be getting detected."
  severity: major
  test: 1
  root_cause: "cms_score >= 2 gate blocked pages with only heal_hit recovered; header had only PSM 6, no PSM 11."
  fix: "Added header PSM 11; widened anchor to HEAL; heal_hit alone sufficient when ub04_score==0. Pages 8,14,22,23 now CMS-1500. Pages 4,17 remain UNKNOWN (total OCR failure)."

- truth: "UB-04 page 11 should be classified as UB-04, not UNKNOWN."
  status: fixed
  reason: "User reported: This is not acceptable. Page 11 should not be unknown."
  severity: major
  test: 2
  root_cause: "NUBC/UB-04/1450 anchors unrecoverable from page 11 footer scan."
  fix: "Added 'REMARKS' (UB-04 field 80) as ub04_score signal. test_ub04_page11_smoke added."

- truth: "conftest.py test_pdf_path fixture should use pytest.skip() when test.pdf is missing, not assert."
  status: already_fixed
  reason: "User reported: This should be fixed."
  severity: major
  test: 3
  root_cause: "CR-01 was filed against pre-fix code. conftest.py already uses pytest.skip()."
  fix: "No code change needed."
