---
phase: 03-form-detection
verified: 2026-05-03T00:00:00Z
status: human_needed
score: 11/13 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Confirm ROADMAP SC-1 intent: run form detector on all CMS-1500 pages in test.pdf and count how many return 'CMS-1500'"
    expected: "RESEARCH.md documents 22 of ~28 actual CMS-1500 pages return 'CMS-1500'; 6 return 'UNKNOWN' due to OCR-degraded anchor text. The SC wording says 'every page that contains the expected signature strings' — confirm whether OCR-degraded pages (4, 8, 14, 17, 22, 23) are considered to 'contain' the signature strings and therefore represent a gap, or whether the empirically verified 22/28 result satisfies the criterion intent."
    why_human: "The criterion wording is conditional but ambiguous. The RESEARCH.md explicitly documents the gap and accepts it. Cannot determine programmatically whether the intent was 'all CMS-1500 pages must pass' or 'only pages where OCR can recover the anchor text'. This requires a human decision on scope acceptance."
  - test: "Confirm ROADMAP SC-2 intent: test.pdf UB-04 page count and UNKNOWN for page 11"
    expected: "CLAUDE.md says '~3 UB-04' pages; RESEARCH.md confirms only 2 actual UB-04 pages exist (6 and 11), and page 11 produces no detectable OCR anchors, so it returns UNKNOWN. The SC says 'Running the form detector against the 3 UB-04 pages' — confirm whether 2 UB-04 pages (not 3) and page 11 returning UNKNOWN are accepted deviations."
    why_human: "The ROADMAP SC references '3 UB-04 pages' but RESEARCH.md confirms only 2 exist and one (page 11) is unreachable by OCR. The implementation correctly handles this per PROC-03 (UNKNOWN for uncertain pages). Needs human sign-off that the OCR limitation is accepted and the criterion intent is satisfied."
  - test: "Confirm CR-01 is not blocking in your CI environment: run 'pytest tests/ -x' without test.pdf present"
    expected: "If test.pdf is removed, the conftest.py session fixture raises AssertionError (not pytest.skip), causing test_cms1500_smoke and test_ub04_smoke to ERROR rather than SKIP. All other 6 Phase 3 tests should still pass or be collectable. Verify whether the bare assert in conftest.py causes suite-level aborts in your target CI environment."
    why_human: "test.pdf is listed as untracked in git status — it is not committed. In CI environments where test.pdf is absent, the 2 smoke tests will ERROR rather than SKIP. CR-01 in the code review identifies this as a critical issue but it does not affect local results where test.pdf is present. Human must decide whether this is a blocker for the phase gate or acceptable given that test.pdf is a local-only fixture."
---

# Phase 3: Form Detection Verification Report

**Phase Goal:** Each page is reliably classified as CMS-1500, UB-04, or UNKNOWN using multi-anchor logic so the correct extractor is always dispatched.
**Verified:** 2026-05-03T00:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth                                                                      | Status       | Evidence                                                                  |
|----|----------------------------------------------------------------------------|--------------|---------------------------------------------------------------------------|
| 1  | tests/test_phase3.py exists with 8 test stubs (now all active)             | VERIFIED     | File exists; `grep -c "def test_"` = 8; 0 skip markers remain            |
| 2  | pytest collects all 8 tests with no import errors                          | VERIFIED     | `pytest tests/test_phase3.py -v` collected 8 items, no errors             |
| 3  | Running the suite exits 0                                                  | VERIFIED     | `pytest tests/test_phase3.py -v` exits 0 — 8 passed in 5.87s             |
| 4  | pipeline/detector.py exists with detect_form_type(image) -> str           | VERIFIED     | File exists at pipeline/detector.py; function signature matches exactly    |
| 5  | CMS-1500 classified 'CMS-1500' when 2-of-3 anchors present (mock)        | VERIFIED     | test_cms1500_detection_mock PASSED; logic verified in detector.py lines 65-66 |
| 6  | UB-04 classified 'UB-04' when NUBC found (mock)                           | VERIFIED     | test_ub04_detection_mock PASSED; lines 67-68 in detector.py               |
| 7  | All-empty OCR returns 'UNKNOWN'                                            | VERIFIED     | test_unknown_when_no_anchors PASSED; blank image smoke also returns UNKNOWN |
| 8  | Both-match (cms>=2 AND ub04>=1) returns 'UNKNOWN'                         | VERIFIED     | test_both_match_returns_unknown PASSED; else branch at line 70 confirmed   |
| 9  | UNKNOWN return value is always a plain str                                 | VERIFIED     | test_unknown_result_is_string PASSED; `isinstance(result, str)` asserted  |
| 10 | 5 unit tests pass green (no real Tesseract calls)                         | VERIFIED     | 5 mock-based tests all PASSED                                              |
| 11 | detect_form_type importable from pipeline package                          | VERIFIED     | `from pipeline import detect_form_type; print('OK')` prints OK; pipeline/__init__.py line 11 |
| 12 | Real test.pdf page 0 classifies as 'CMS-1500'                             | VERIFIED     | test_cms1500_smoke PASSED with real Tesseract                              |
| 13 | Real test.pdf page 6 classifies as 'UB-04'                                | VERIFIED     | test_ub04_smoke PASSED with real Tesseract                                 |
| 14 | All 8 Phase 3 tests pass green                                             | VERIFIED     | `pytest tests/test_phase3.py` — 8 passed, 0 skipped, 0 errors             |
| 15 | Phase 1 and Phase 2 tests still pass (no regression)                      | VERIFIED     | `pytest tests/ -x` — 31 passed in 19.15s (8+15+8)                        |
| SC-1 | ROADMAP: 27 CMS-1500 pages return 'CMS-1500'                           | ? UNCERTAIN  | Only 22/28 actual CMS-1500 pages return 'CMS-1500'; 6 return UNKNOWN due to OCR-degraded anchors — see human verification |
| SC-2 | ROADMAP: 3 UB-04 pages return 'UB-04'                                  | ? UNCERTAIN  | Only 1 of 2 actual UB-04 pages (page 6) returns 'UB-04'; page 11 returns UNKNOWN; CLAUDE.md count of ~3 UB-04 is empirically incorrect — see human verification |
| SC-3 | ROADMAP: Obscured page classifies as UNKNOWN                            | VERIFIED     | test_unknown_when_no_anchors passes; blank image returns 'UNKNOWN' confirmed |
| SC-4 | ROADMAP: UNKNOWN result carries the form type label                     | VERIFIED     | detect_form_type returns the string 'UNKNOWN'; test_unknown_result_is_string asserts isinstance(result, str) |

**Score:** 11/13 plan must-haves verified (plus 2 ROADMAP SCs uncertain — require human decision)

---

### ROADMAP Success Criteria Gap Analysis

The ROADMAP defines 4 success criteria. SC-1 and SC-2 contain wording ("every page that contains the expected signature strings") that is empirically conditional:

**SC-1 gap:** The RESEARCH.md documents (empirically verified against all 30 pages) that 6 of ~28 actual CMS-1500 pages (pages 4, 8, 14, 17, 22, 23) produce no recoverable anchor text via OCR and classify as UNKNOWN. The implementation is correct per PROC-03 design — uncertain pages become UNKNOWN rows. The RESEARCH.md explicitly flags this: "The ROADMAP success criterion '27 CMS-1500 pages return CMS-1500' cannot be fully achieved by the anchor strategy on this test.pdf." The test suite only asserts page 0 (which reliably passes), not all 27.

**SC-2 gap:** CLAUDE.md estimates "~3 UB-04" pages in test.pdf. RESEARCH.md empirically found only 2 UB-04 pages (6 and 11), and page 11's NUBC text is not OCR-recoverable. The SC says "3 UB-04 pages" — the actual count is 2. The implementation handles page 11 correctly by returning UNKNOWN (correct per PROC-03), but the SC premise (3 pages) does not match the test data.

Both gaps are documented and resolved in RESEARCH.md, and the implementation behaves correctly per PROC-03's UNKNOWN-for-uncertain-pages design. However they remain UNCERTAIN at verification time because they represent unapproved scope deviations from the ROADMAP text.

---

### Required Artifacts

| Artifact              | Expected                               | Status     | Details                                                    |
|-----------------------|----------------------------------------|------------|------------------------------------------------------------|
| `tests/test_phase3.py`| 8 active tests, 0 skip markers         | VERIFIED   | 8 tests, 0 skip markers; all 8 pass                        |
| `pipeline/detector.py`| detect_form_type with _HEADER_STRIP, _FOOTER_STRIP, 3 return values | VERIFIED | All patterns present; logic substantive and correct |
| `pipeline/__init__.py`| from .detector import detect_form_type in __all__ | VERIFIED | Line 11: `from .detector import detect_form_type`; line 13: `__all__` includes it |

---

### Key Link Verification

| From                       | To                              | Via                                       | Status  | Details                                             |
|----------------------------|---------------------------------|-------------------------------------------|---------|-----------------------------------------------------|
| `pipeline/__init__.py`     | `pipeline/detector.py`          | `from .detector import detect_form_type`  | WIRED   | Line 11; importable as `from pipeline import detect_form_type` confirmed |
| `pipeline/detector.py`     | `config_loader.load_settings()` | `load_settings()` at function entry       | WIRED   | Line 33; returns settings dict including tesseract_cmd |
| `pipeline/detector.py`     | `pytesseract.image_to_string`   | 3 OCR calls on grayscale crops            | WIRED   | Lines 42-44; header PSM6, footer PSM6, footer PSM11  |
| `tests/test_phase3.py`     | `pipeline.detect_form_type`     | deferred import inside test body          | WIRED   | All 8 tests use deferred import pattern; no module-level pipeline imports |
| `tests/test_phase3.py::test_cms1500_smoke` | real Tesseract | `convert_page(test_pdf_path, 0)` + `detect_form_type(image)` | WIRED | PASSED in 5.87s total with real OCR |

---

### Data-Flow Trace (Level 4)

| Artifact              | Data Variable | Source                        | Produces Real Data | Status    |
|-----------------------|---------------|-------------------------------|--------------------|-----------|
| `pipeline/detector.py`| header_text, footer_psm6, footer_psm11 | `pytesseract.image_to_string` on real PIL image crops | Yes — real OCR on real page images | FLOWING |
| `tests/test_phase3.py` (mock tests) | responses iterator | monkeypatched pytesseract | Mock — controlled test inputs | FLOWING (by design) |
| `tests/test_phase3.py` (smoke tests) | image | `convert_page(test_pdf_path, page)` | Yes — real test.pdf pages | FLOWING |

---

### Behavioral Spot-Checks

| Behavior                                      | Command                                                                                                     | Result        | Status  |
|-----------------------------------------------|-------------------------------------------------------------------------------------------------------------|---------------|---------|
| Blank image returns 'UNKNOWN'                 | `python -c "from pipeline.detector import detect_form_type; from PIL import Image; img = Image.new('RGB',(2550,3300),255); print(detect_form_type(img))"` | `UNKNOWN` | PASS |
| `from pipeline import detect_form_type` works | `python -c "from pipeline import detect_form_type; print('OK')"`                                             | `OK`          | PASS    |
| Full Phase 3 suite passes                     | `pytest tests/test_phase3.py -v`                                                                             | 8 passed      | PASS    |
| No regressions in Phases 1+2                  | `pytest tests/ -x`                                                                                           | 31 passed     | PASS    |

---

### Requirements Coverage

| Requirement | Source Plan | Description                                      | Status       | Evidence                                              |
|-------------|-------------|--------------------------------------------------|--------------|-------------------------------------------------------|
| PROC-03     | 03-01, 03-02, 03-03 | Multi-anchor detection (2-of-3 must agree); UNKNOWN for uncertain pages | SATISFIED (with caveats) | detect_form_type implemented; 8 tests passing; UNKNOWN returned for ambiguous cases. Caveats: 6/28 CMS-1500 pages return UNKNOWN due to OCR limitations (documented in RESEARCH.md as accepted limitation); page 11 UB-04 also returns UNKNOWN |

---

### Anti-Patterns Found

| File                    | Line  | Pattern                                            | Severity | Impact                                                       |
|-------------------------|-------|----------------------------------------------------|----------|--------------------------------------------------------------|
| `tests/conftest.py`     | 11    | `assert path.exists()` — bare assert in session fixture | WARNING | CR-01: In CI without test.pdf, produces AssertionError/ERROR not pytest.skip; smoke tests cannot be suppressed without modifying conftest.py. Does NOT affect local runs where test.pdf is present. |
| `pipeline/detector.py`  | 33-34 | `pytesseract.pytesseract.tesseract_cmd = settings['tesseract_cmd']` inside hot-path function body | WARNING | CR-02: Global module state mutated on every call; thread-unsafe if ever called concurrently; mock tests do NOT neutralize the load_settings() call at line 33. In current single-threaded usage, this works correctly. |

**Stub classification note:** Neither anti-pattern prevents the current tests from passing or the classifier from working correctly in single-threaded usage. They are code quality issues identified by the code review, not functional blockers.

---

### Human Verification Required

#### 1. ROADMAP SC-1: Acceptance of OCR-Limited CMS-1500 Coverage

**Test:** Review the empirical page-by-page classification table in RESEARCH.md (Validation Architecture section). The table shows 22 pages return 'CMS-1500', 1 returns 'UB-04', and 7 return 'UNKNOWN' across 30 test.pdf pages. Pages 4, 8, 14, 17, 22, 23 are actual CMS-1500 forms that return UNKNOWN because OCR cannot recover their anchor text.

**Expected:** Either (a) accept that "every page that contains the expected signature strings" means only pages where OCR recovers those strings — in which case 22/22 passes and SC-1 is satisfied; OR (b) determine that all CMS-1500 pages must return 'CMS-1500' regardless of OCR quality — in which case SC-1 is not fully achieved and a gap exists.

**Why human:** This is a requirements interpretation decision. The implementation is functioning correctly per PROC-03 design (uncertain pages become UNKNOWN rows). The RESEARCH.md explicitly documents and accepts this limitation. Only the product owner can confirm whether the OCR-limited coverage is acceptable scope for this phase.

#### 2. ROADMAP SC-2: UB-04 Page Count and Page 11 UNKNOWN

**Test:** Confirm that test.pdf contains 2 UB-04 pages (not 3 as stated in CLAUDE.md). Run `pytest tests/test_phase3.py::test_ub04_smoke -v` (passes — page 6). Manually inspect page 11 classification: `python -c "from pipeline import convert_page, detect_form_type; img = convert_page('test.pdf', 11); print(detect_form_type(img))"` — expected output: UNKNOWN.

**Expected:** Confirm CLAUDE.md's "~3 UB-04" count is approximate and 2 is the actual count, and that page 11 returning UNKNOWN is accepted behavior (OCR limitation, not a bug).

**Why human:** The ROADMAP SC text says "3 UB-04 pages" — this premise is incorrect per empirical research. If the SC must be taken literally (3 pages), no implementation can satisfy it because the third page does not exist in test.pdf. If the SC is read as approximate, the single verified UB-04 (page 6) returning 'UB-04' satisfies the criterion intent. Human confirmation needed.

#### 3. CR-01: conftest.py bare assert in CI environments

**Test:** Run `pytest tests/ -x` in an environment where test.pdf is absent (remove or rename it temporarily). Observe whether the output shows `ERROR` (fixture AssertionError) or `SKIPPED` for test_cms1500_smoke and test_ub04_smoke.

**Expected:** Per CR-01, the conftest.py fixture raises AssertionError rather than calling pytest.skip, so the 2 smoke tests will ERROR and the session fixture will abort. The 6 mock-only tests should still run cleanly. Determine whether this behavior is acceptable for your CI setup.

**Why human:** test.pdf is not committed to git (it appears as untracked in git status). Whether this is a phase-blocking issue depends on CI configuration. The code review identifies this as a critical issue, but all local tests pass because test.pdf is present locally.

---

### Gaps Summary

No hard FAILED gaps in the implementation itself — all 13 plan must-have truths are satisfied in the codebase. The two UNCERTAIN items (SC-1 and SC-2) relate to ROADMAP success criteria interpretation, both of which are documented and resolved in RESEARCH.md but require human sign-off to formally close. The three human verification items above cover: (1) scope acceptance of OCR-limited coverage, (2) UB-04 page count discrepancy, and (3) CI behavior for the conftest.py assert vs skip pattern.

---

_Verified: 2026-05-03T00:00:00Z_
_Verifier: Claude (gsd-verifier)_
