---
phase: 02-image-pipeline-coordinate-calibration
verified: 2026-05-01T00:00:00Z
status: human_needed
score: 10/10 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Open calibration_overlay_p0.png and confirm that all labeled green rectangles land on the correct CMS-1500 form boxes (claim ID, Box 1, Box 2, Box 3, Box 5, Box 17, Box 17b, Box 19, Box 21 A-L, Box 23, Box 25-29, Box 32, Box 33)"
    expected: "Every labeled rectangle is visually aligned with the corresponding form field; no rectangle covers whitespace only or overlaps adjacent fields significantly"
    why_human: "Pixel coordinate accuracy on a scanned form cannot be verified programmatically — only the developer can confirm visual alignment by looking at the annotated PNG against the real form"
  - test: "Run: python pipeline/calibrate.py --page 0 --pdf test.pdf, open calibration_overlay_p0.png, inspect Box 24 service line table regions (orange rectangles for 10 sub-fields x 6 rows)"
    expected: "The 60 orange row rectangles cover the correct column regions across all 6 service lines with no systematic offset"
    why_human: "Table field coordinate alignment is the highest-risk region (Box 24 grey bands are the stated motivation for preprocessing); only visual inspection can confirm row height is correct"
  - test: "Run: python pipeline/calibrate.py --page 27 --pdf test.pdf --form ub04, open calibration_overlay_p27.png (or whichever is the first UB-04 page in test.pdf)"
    expected: "UB-04 field regions (24 green boxes + 7 x 22 = 154 orange row boxes) are drawn and align with the real UB-04 form boxes"
    why_human: "UB-04 coordinate set was estimated from published form dimensions; visual confirmation against an actual scan is required before Phase 4 begins. CLAUDE.md and ROADMAP both flag this as a hard gate."
  - test: "Confirm the preprocessing visually improves a CMS-1500 Box 24 region: run debug mode: python -c \"from pipeline import convert_page, preprocess_page; from config_loader import load_settings; import os; os.chdir('C:/tmp'); img=convert_page('test.pdf',0); preprocess_page(img,load_settings(),debug=True)\" and open debug_04_threshold.png"
    expected: "Box 24 grey-band rows appear clearly as black-and-white (grey banding is visibly removed by adaptive threshold)"
    why_human: "ROADMAP SC3 explicitly requires visual confirmation that grey-band removal works. No automated test can substitute for viewing the thresholded image."
---

# Phase 2: Image Pipeline & Coordinate Calibration — Verification Report

**Phase Goal:** Every PDF page converts to a correctly-scaled, deskewed, thresholded image and every field region is visually verified against real scans before extractor code is written.
**Verified:** 2026-05-01T00:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | convert_page("test.pdf", 0) returns PIL Image of size (2550, 3300) and mode "RGB" | VERIFIED | test_convert_page_dimensions and test_convert_page_mode both PASSED; converter resizes within ±10% tolerance using Lanczos, always outputs exactly 2550x3300 |
| 2 | convert_page raises an exception for a non-existent PDF path | VERIFIED | test_convert_page_invalid_pdf PASSED; pdf2image raises exception which propagates |
| 3 | preprocess_page returns PIL Image of size (2550, 3300) and mode "RGB" | VERIFIED | test_preprocess_smoke and test_preprocess_mode PASSED |
| 4 | preprocess_page raises ValueError with "exceeds" when skew > 5 degrees | VERIFIED | test_deskew_rejection PASSED; preprocessor.py line 107: `raise ValueError(f"Skew angle {skew_angle:.1f}° exceeds ...")` |
| 5 | debug=True writes exactly 4 intermediate PNGs (debug_01_raw.png through debug_04_threshold.png) | VERIFIED | test_preprocess_debug_files PASSED; 4 files written to CWD via monkeypatch.chdir |
| 6 | Pipeline step order is scale correction -> deskew -> adaptive threshold | VERIFIED | Step 1/2/3 comments confirmed in preprocessor.py; positions 651/1850/3250 chars confirm ordering |
| 7 | load_settings() returns threshold_block_size=31 when settings.json is absent | VERIFIED | test_settings_threshold_block_size_default PASSED; config_loader._DEFAULTS contains `"threshold_block_size": 31` |
| 8 | CMS1500_FIELDS has 29 FieldDef entries; CMS1500_TABLE_FIELDS has 10 TableFieldDef with exactly 6 row_boxes each | VERIFIED | test_cms1500_fields_populated and test_cms1500_table_fields_row_count PASSED; Python assertion `len(CMS1500_FIELDS)==29`, `all(len(f.row_boxes)==6 ...)` confirmed |
| 9 | UB04_FIELDS has 24 FieldDef entries; UB04_TABLE_FIELDS has 7 TableFieldDef with exactly 22 row_boxes each | VERIFIED | test_ub04_fields_populated and test_ub04_table_fields_row_count PASSED; Python assertion `len(UB04_FIELDS)==24`, `all(len(f.row_boxes)==22 ...)` confirmed |
| 10 | calibrate.py --page 0 --pdf test.pdf exits 0 and writes calibration_overlay_p0.png larger than 1 KB | VERIFIED | test_calibrate_overlay_created and test_calibrate_overlay_nonempty PASSED; subprocess exits 0; file created in tmp_path |

**Score:** 10/10 truths verified

### ROADMAP Success Criteria Mapping

| SC | Text | Automated Status | Notes |
|----|------|-----------------|-------|
| SC1 | Converter produces 2550x3300 PIL Image; non-standard DPI rejected | VERIFIED | Tests pass; ±10% tolerance with Lanczos resize — see deviation note below |
| SC2 | Calibration script renders page with every CMS-1500 and UB-04 field region as labeled rectangle; image can be visually inspected | PARTIAL — human needed | Script produces PNG with rectangles (automated confirmed); visual alignment requires human inspection (mandatory gate per CLAUDE.md) |
| SC3 | Box 24 grey-banded rows visibly cleaner after preprocessing; deskew corrects tilted test image to within 0.5 degrees | PARTIAL — human needed | deskew rejection at >5° VERIFIED by test; adaptive threshold code confirmed present; visual quality confirmation requires human |
| SC4 | scale_x and scale_y computed from bounding box; calibration overlay stays aligned on pages with slight size variation | VERIFIED | scale_x = 2550.0/w and scale_y = 3300.0/h confirmed in preprocessor.py; calibrate.py calls preprocess_page before _draw_overlay |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/test_phase2.py` | 15 test functions, no skip markers | VERIFIED | 15 functions confirmed, 0 skip markers, 15/15 PASSED |
| `tests/conftest.py` | test_pdf_path and sample_settings fixtures | VERIFIED | Both session-scoped fixtures present and working |
| `config_loader.py` | threshold_block_size=31 in _DEFAULTS | VERIFIED | Line 16: `"threshold_block_size": 31` |
| `config/cms1500.py` | CMS1500_FIELDS (29 FieldDef) and CMS1500_TABLE_FIELDS (10 TableFieldDef) | VERIFIED | Counts confirmed programmatically |
| `config/ub04.py` | UB04_FIELDS (24 FieldDef) and UB04_TABLE_FIELDS (7 TableFieldDef) | VERIFIED | Counts confirmed programmatically |
| `pipeline/__init__.py` | Re-exports convert_page and preprocess_page; no try/except guard | VERIFIED | Clean imports; `try:` not in file |
| `pipeline/converter.py` | convert_page() with explicit poppler_path, dimension validation, 300 DPI | VERIFIED | All checks pass; dpi=300, poppler_path=poppler_path, ValueError on >10% deviation |
| `pipeline/preprocessor.py` | Three-step OpenCV pipeline with block_size guard and ValueError for skew | VERIFIED | All implementation requirements confirmed |
| `pipeline/calibrate.py` | CLI with --page, --pdf, --form; overlay to CWD; D-01/D-03/D-04/T-2-02 documented | VERIFIED | All flags present; test_calibrate_* PASSED |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `pipeline/__init__.py` | `pipeline/converter.py` | `from .converter import convert_page` | WIRED | Confirmed in file |
| `pipeline/__init__.py` | `pipeline/preprocessor.py` | `from .preprocessor import preprocess_page` | WIRED | Confirmed; no try/except guard |
| `pipeline/converter.py` | `config_loader.load_settings` | `settings["poppler_path"]` | WIRED | load_settings() called; poppler_path used explicitly |
| `pipeline/preprocessor.py` | `settings["threshold_block_size"]` | `settings.get("threshold_block_size", 31)` | WIRED | Confirmed in preprocessor.py |
| `pipeline/calibrate.py` | `pipeline.converter.convert_page` | deferred import in `_run()` | WIRED | `from pipeline.converter import convert_page` in _run body |
| `pipeline/calibrate.py` | `config/cms1500.py` | `from config.cms1500 import CMS1500_FIELDS, CMS1500_TABLE_FIELDS` | WIRED | Confirmed; used in _run() field selection |
| `pipeline/calibrate.py` | `config/ub04.py` | `from config.ub04 import UB04_FIELDS, UB04_TABLE_FIELDS` | WIRED | Confirmed; used in _run() field selection |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `pipeline/calibrate.py` | `fields`, `table_fields` | `CMS1500_FIELDS` / `UB04_FIELDS` from config files | Yes — 29/24 FieldDef instances with real pixel coordinates | FLOWING |
| `pipeline/calibrate.py` | `cv_img` | `preprocess_page(convert_page(...))` chain | Yes — real PDF page rendered at 300 DPI then preprocessed | FLOWING |
| `pipeline/preprocessor.py` | `scale_x`, `scale_y` | `cv2.findContours` on real image | Yes — computed from largest contour of actual scanned form | FLOWING |
| `pipeline/converter.py` | `image` | `convert_from_path(pdf_path, dpi=300)` | Yes — real pdf2image call producing PIL Image | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full 15-test suite passes | `python -m pytest tests/test_phase2.py -v` | 15 passed in 15.35s | PASS |
| Phase 1 regression (8 tests) | `python -m pytest tests/test_phase1.py -v` | 8 passed in 0.28s | PASS |
| Coordinate counts correct | `python -c "from config.cms1500 import CMS1500_FIELDS, CMS1500_TABLE_FIELDS; print(len(CMS1500_FIELDS), len(CMS1500_TABLE_FIELDS))"` | 29 10 | PASS |
| UB04 coordinate counts correct | `python -c "from config.ub04 import UB04_FIELDS, UB04_TABLE_FIELDS; print(len(UB04_FIELDS), len(UB04_TABLE_FIELDS))"` | 24 7 | PASS |
| Pipeline imports work | `python -c "from pipeline import convert_page, preprocess_page"` | No error | PASS |
| threshold_block_size default | `python -c "from config_loader import load_settings; s = load_settings(path='nonexistent.json'); print(s['threshold_block_size'])"` | 31 | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| PROC-01 | 02-05-PLAN | Convert each PDF page to PIL Image at exactly 300 DPI via pdf2image + Poppler | SATISFIED | converter.py: `dpi=300`, explicit `poppler_path`; test_convert_page_dimensions PASSED |
| PROC-02 | 02-02-PLAN, 02-06-PLAN | OpenCV preprocessing: bounding-box scale correction, deskew via warp affine, adaptive threshold | SATISFIED | preprocessor.py implements all three steps in required order; 5 preprocessor tests PASSED; REQUIREMENTS.md checkbox not updated but implementation is present |
| EXTR-04 | 02-03-PLAN, 02-04-PLAN, 02-07-PLAN | Calibration script renders field regions as labeled rectangles for visual verification | SATISFIED (automated portion) — HUMAN NEEDED (visual gate) | calibrate.py fully implemented and tested; CLAUDE.md states visual verification is a "hard gate" before Phase 4 |

**Note on REQUIREMENTS.md checkbox state:** PROC-02 and EXTR-04 remain marked `[ ]` in REQUIREMENTS.md and ROADMAP.md still shows Phase 2 as "Ready to execute" with plan 02-07 unchecked. These are tracking artifacts that were not updated after execution. The implementation is fully present and all 15 tests pass.

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| None found | — | — | — |

No placeholders, TODOs, empty returns, or stub implementations found in any Phase 2 artifact.

### Deviation from Plan Spec — Converter Tolerance (INFO)

The 02-05-PLAN specified strict dimension validation: "raise ValueError if resulting image is not exactly 2550x3300". The implementation in `pipeline/converter.py` instead:
1. Accepts pages within ±10% of target dimensions
2. Resizes to exactly 2550x3300 using Lanczos resampling
3. Only raises ValueError if deviation exceeds 10%

This is a deliberate improvement documented in the converter's docstring ("Scanners may produce slightly undersized pages e.g. 2478x3228"). The test `test_convert_page_dimensions` still passes because the function always returns 2550x3300. This is not a blocker — it is a more robust implementation than the original spec, and all tests validate the same observable behavior (always returns 2550x3300 or raises).

### Human Verification Required

#### 1. CMS-1500 Field Coordinate Visual Alignment

**Test:** Run `python pipeline/calibrate.py --page 0 --pdf test.pdf` from the project root, then open `calibration_overlay_p0.png`
**Expected:** All 29 green-bordered rectangles land on their correct form boxes. Specifically verify: claim ID row at top, Box 1 insurance type, Box 2 patient name, Box 21 diagnosis codes (12 separate regions), Box 24 service line column headers
**Why human:** Pixel coordinate accuracy on a scanned form cannot be verified programmatically — only visual inspection of the annotated overlay against the real form can confirm alignment

#### 2. CMS-1500 Box 24 Table Coordinate Alignment

**Test:** In the same `calibration_overlay_p0.png`, inspect the orange rectangle regions in the Box 24 service line area (approximately the middle third of the form)
**Expected:** 10 sub-fields x 6 rows = 60 orange rectangles tile the Box 24 section correctly with no systematic vertical or horizontal offset; row heights match the actual service line row spacing
**Why human:** Box 24 is the densest part of the form with the most coordinates; misalignment here would cause all service line extraction to fail in Phase 4

#### 3. UB-04 Field Coordinate Visual Alignment

**Test:** Run `python pipeline/calibrate.py --page 27 --pdf test.pdf --form ub04` (adjust page number to the first UB-04 page in test.pdf — approximately page 27 based on ~27 CMS-1500 pages first), open `calibration_overlay_p27.png`
**Expected:** 24 green boxes and 7 x 22 = 154 orange row boxes are drawn and align with the actual UB-04 form fields (provider name, patient info, revenue lines 1-22, payer boxes, etc.)
**Why human:** UB-04 coordinates are estimated from published form dimensions; this has never been visually checked against the actual test.pdf scans. CLAUDE.md explicitly states "Phase 2 coordinate calibration is a hard gate — do not start Phase 4 until pixel regions are visually verified."

#### 4. Preprocessing Quality — Grey-Band Removal

**Test:** Run with debug mode from a temp directory:
```
mkdir C:\tmp\ocr_debug
cd C:\tmp\ocr_debug
python -c "import sys; sys.path.insert(0,'C:/Users/shset/Documents/GitHub/OCR-Rework'); from pipeline import convert_page, preprocess_page; from config_loader import load_settings; img=convert_page('C:/Users/shset/Documents/GitHub/OCR-Rework/test.pdf',0); preprocess_page(img,load_settings(),debug=True)"
```
Open `debug_04_threshold.png` and compare to `debug_01_raw.png`
**Expected:** debug_04_threshold.png shows the Box 24 area (roughly y=1130-2030) as cleanly black-and-white; any grey banding visible in debug_01_raw.png should be eliminated
**Why human:** ROADMAP SC3 explicitly requires visual confirmation that adaptive threshold removes the grey band; this is a subjective image quality assessment

### Gaps Summary

No automated gaps were found. All 10 must-have truths are VERIFIED. All artifacts exist and are substantive (not stubs). All key links are wired. All 15 tests pass. Phase 1 regression is clean (8/8).

The `human_needed` status reflects that ROADMAP Success Criteria 2 and 3 include explicit visual verification requirements. CLAUDE.md designates coordinate calibration as a "hard gate" before Phase 4. The automated code is complete; human sign-off on coordinate alignment is required.

---

_Verified: 2026-05-01T00:00:00Z_
_Verifier: Claude (gsd-verifier)_
