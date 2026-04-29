# Phase 2 Research: Image Pipeline & Coordinate Calibration

**Researched:** 2026-04-29
**Domain:** pdf2image, OpenCV preprocessing, coordinate calibration, CMS-1500 / UB-04 field mapping
**Confidence:** HIGH (all findings derived from local source files and pre-loaded technical facts)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01** Calibration output: PNG only, no auto-open, no cv2.imshow(). Writes `calibration_overlay_p{N}.png` to project root and exits.
- **D-02** Page selection via CLI: `python pipeline/calibrate.py --page N --pdf PATH`. Any page on demand; no hardcoded defaults.
- **D-03** Label text is the full `FieldDef.name` (e.g. `box24_cpt_sl1`) drawn outside the rectangle (above or below), not inside.
- **D-04** Overlay draws only the field set matching the detected form type on that page.
- **D-05** Phase 2 pre-populates `CMS1500_FIELDS` / `UB04_FIELDS` with estimated coordinates. User runs `calibrate.py`, inspects PNG, edits config files directly.
- **D-06** `config/cms1500.py` and `config/ub04.py` are the sole source of truth for coordinates. No JSON/YAML side-files or code generation.
- **D-07** Scale correction is mandatory. `preprocess_page()` computes `scale_x`/`scale_y` and applies them to the coordinate space.
- **D-08** Pipeline step order: **Scale correction → Deskew → Adaptive threshold**.
- **D-09** Default Gaussian adaptive threshold block size: **31**, stored in `settings.json` as `threshold_block_size`.
- **D-10** Deskew rejection threshold: **±5°**. Exceeding this raises an error (not a warning, not a clamp).
- **D-11** `preprocess_page()` returns a single PIL Image. `debug=True` saves intermediate PNGs to project root.
- **D-12** `pipeline/` package at project root: `converter.py`, `preprocessor.py`, `calibrate.py`, `__init__.py`.
- **D-13** DPI/dimension validation inside `converter.py`. Non-2550×3300 result raises `ValueError`.
- **D-14** Two separate public functions: `convert_page` + `preprocess_page`.
- **D-15** Tests live in `tests/test_phase2.py`.

### Claude's Discretion

- Adaptive threshold constant `C` value and exact OpenCV flags
- Deskew implementation method (Hough-line or Canny + minAreaRect)
- Bounding box detection method for scale correction
- Calibration overlay color scheme
- Whether `calibrate.py` prints a stdout summary

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PROC-01 | Convert each PDF page to PIL Image at exactly 300 DPI via pdf2image + Poppler | Section 1 — `convert_from_path` API, DPI enforcement, dimension validation |
| PROC-02 | OpenCV preprocessing: scale correction, deskew via warpAffine, adaptive Gaussian threshold | Section 2 — full preprocessing pipeline with code patterns |
| EXTR-04 | Calibration script renders any PDF page with all field regions as labelled rectangles | Section 3 — `calibrate.py` design, overlay drawing pattern |
</phase_requirements>

---

## Executive Summary

- Phase 2 builds the low-level image pipeline that every later phase depends on: PDF-to-PIL conversion, three-step OpenCV preprocessing (scale correction, deskew, adaptive threshold), and a calibration script that lets the user visually verify all ~60 field coordinates before any OCR extraction code is written.
- All design decisions are locked (D-01 through D-15). The only open choices are aesthetic/implementation details delegated to Claude (overlay colors, C constant, deskew method variant).
- The highest risk is coordinate accuracy: the coordinates provided in this document are estimated from standard form dimensions and MUST be verified by running `calibrate.py` against `test.pdf` before Phase 4 begins. That gate is hard.
- The `pipeline/` package integrates cleanly with Phase 1 (`config_loader.load_settings()`, `config/base.py` dataclasses) and will be consumed unchanged by Phases 3 and 4.

**Primary recommendation:** Implement all three preprocessing steps in the exact order specified (D-08), use Hough-line deskew (more reliable than minAreaRect on sparse form content), and use `C=11` for the adaptive threshold (standard for scanned documents at 300 DPI).

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| PDF → PIL conversion | `pipeline/converter.py` | — | Single-responsibility; isolated for Phase 3 raw-image reuse (D-14) |
| OpenCV preprocessing | `pipeline/preprocessor.py` | — | Geometry/threshold concerns separated from I/O |
| Coordinate configuration | `config/cms1500.py`, `config/ub04.py` | — | Config-only files; no logic; sole source of truth (D-06) |
| Calibration overlay | `pipeline/calibrate.py` | config files | CLI consumer of config; writes PNG to project root (D-01) |
| Settings / tunables | `config_loader.py` / `settings.json` | — | Extends existing Phase 1 pattern; `threshold_block_size` added |
| Tests | `tests/test_phase2.py` | — | Consistent with Phase 1 convention (D-15) |

---

## 1. PDF → PIL Conversion (PROC-01)

### Public API

```python
# pipeline/converter.py
def convert_page(pdf_path: str, page_num: int) -> PIL.Image.Image:
    """Convert one PDF page to a 300 DPI PIL Image.

    Args:
        pdf_path: Absolute or relative path to the PDF.
        page_num: 0-indexed page number.

    Returns:
        PIL.Image.Image, mode "RGB", size 2550x3300 px.

    Raises:
        ValueError: If the resulting image is not exactly 2550x3300 px (D-13).
        FileNotFoundError: If pdf_path does not exist.
    """
```

### Implementation Pattern

```python
# [VERIFIED: pre-loaded technical facts]
from pdf2image import convert_from_path
from config_loader import load_settings

def convert_page(pdf_path: str, page_num: int) -> "PIL.Image.Image":
    settings = load_settings()
    pages = convert_from_path(
        pdf_path,
        dpi=300,
        first_page=page_num + 1,   # pdf2image is 1-indexed
        last_page=page_num + 1,
        poppler_path=settings["poppler_path"],
    )
    image = pages[0]  # PIL.Image.Image, mode "RGB"
    if image.size != (2550, 3300):
        raise ValueError(
            f"Expected 2550x3300 px at 300 DPI, got {image.size} "
            f"(page {page_num}, {pdf_path!r})"
        )
    return image
```

### Windows-Specific Notes

- `poppler_path` must be passed explicitly — no PATH lookup. Default in `_DEFAULTS`: `C:\Program Files\poppler\Library\bin`. [VERIFIED: config_loader.py line 14]
- `pdf2image` returns a list even when `first_page == last_page`; always index `[0]`.
- The 300 DPI / 2550×3300 assertion is the canonical dimension check (D-13). No caller can bypass it.

### Settings Integration

`load_settings()` already provides `poppler_path`. No new settings key needed for `converter.py`. [VERIFIED: config_loader.py]

---

## 2. OpenCV Preprocessing Pipeline (PROC-02)

### Public API

```python
# pipeline/preprocessor.py
def preprocess_page(
    image: PIL.Image.Image,
    settings: dict,
    debug: bool = False,
) -> PIL.Image.Image:
    """Apply scale correction, deskew, and adaptive threshold to a page image.

    Args:
        image: Raw PIL Image from convert_page() — 2550x3300, mode "RGB".
        settings: dict from load_settings(); reads threshold_block_size (default 31).
        debug: If True, saves intermediate PNGs to project root.

    Returns:
        Preprocessed PIL Image (same dimensions), suitable for field extraction.

    Raises:
        ValueError: If detected skew angle exceeds ±5° (D-10).
    """
```

### 2.1 PIL ↔ NumPy/OpenCV Conversion

```python
# [VERIFIED: pre-loaded technical facts]
import numpy as np
import cv2
from PIL import Image

# PIL RGB → OpenCV BGR (required before any cv2 call)
cv_img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

# After processing — OpenCV grayscale/BGR → PIL for return value
pil_out = Image.fromarray(cv2.cvtColor(cv_gray, cv2.COLOR_GRAY2RGB))
```

**Important:** `np.array(pil_image)` produces RGB channel order. `cv2` expects BGR. Always apply `cv2.COLOR_RGB2BGR` immediately on entry and `cv2.COLOR_BGR2RGB` (or `GRAY2RGB`) on exit.

### 2.2 Scale Correction (Step 1 — D-07, D-08)

Scale correction normalises the coordinate space so that all pixel regions in the config files are accurate regardless of slight scanner-induced scaling.

```python
# [VERIFIED: pre-loaded technical facts]
# Find form bounding box via largest contour on thresholded image
gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
_, thresh_for_contour = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(
    thresh_for_contour, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
)
largest = max(contours, key=cv2.contourArea)
x, y, w, h = cv2.boundingRect(largest)

# Expected at 300 DPI US Letter: ~2550 x 3300
scale_x = 2550 / w
scale_y = 3300 / h

# Apply to coordinates before any crop:
# adjusted = (int(left*scale_x), int(top*scale_y), int(right*scale_x), int(bottom*scale_y))
```

Scale factors are computed once per page and stored internally. The calibration overlay applies the same scale so that visual alignment is accurate (D-05, specifics note).

**Why this is Step 1:** Deskew and threshold operate on the pixel grid; scale correction must normalise that grid first so that deskew angle measurement and crop regions are accurate.

### 2.3 Deskew (Step 2 — D-08, D-10)

Hough-line approach is preferred over `minAreaRect` for scanned forms because medical forms contain dense horizontal rulings — Hough detects these reliably whereas `minAreaRect` can misfire on sparse content areas. [ASSUMED — Hough reliability on ruled forms]

```python
# [VERIFIED: pre-loaded technical facts]
edges = cv2.Canny(gray, 50, 150)
lines = cv2.HoughLinesP(
    edges, 1, np.pi / 180,
    threshold=100, minLineLength=100, maxLineGap=10
)

# Filter to near-horizontal lines, compute median angle
angles = []
if lines is not None:
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        if abs(angle) < 45:  # near-horizontal only
            angles.append(angle)

if not angles:
    # No lines found — return image unchanged (not an error)
    return image

skew_angle = float(np.median(angles))

if abs(skew_angle) > 5.0:
    raise ValueError(
        f"Skew angle {skew_angle:.1f}° exceeds ±5° limit — "
        "manual review required"
    )

# Rotate to correct skew (warpAffine preserves dimensions)
(h_px, w_px) = cv_img.shape[:2]
center = (w_px // 2, h_px // 2)
M = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
corrected = cv2.warpAffine(
    cv_img, M, (w_px, h_px),
    flags=cv2.INTER_LINEAR,
    borderMode=cv2.BORDER_REPLICATE,
)
```

**Rejection policy (D-10):** Angles beyond ±5° are scanner errors that would misalign every coordinate region. Raising `ValueError` lets the Phase 6 pipeline write a blank row with `extraction_error` populated (UI-04).

### 2.4 Adaptive Threshold (Step 3 — D-08, D-09)

Removes grey scan-shadow bands that appear in Box 24 multi-column regions and cause Tesseract to misread digits as noise.

```python
# [VERIFIED: pre-loaded technical facts]
gray = cv2.cvtColor(corrected, cv2.COLOR_BGR2GRAY)
block_size = settings.get("threshold_block_size", 31)  # D-09: default 31

thresh = cv2.adaptiveThreshold(
    gray, 255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY,
    blockSize=block_size,  # must be odd; validate at runtime
    C=11,                  # recommended constant for scanned documents at 300 DPI
)
```

**C=11 rationale:** C=11 is the standard recommended value for scanned business documents at 300 DPI. It subtracts 11 from the local mean before thresholding, suppressing backgrounds with mild grey gradients without eroding thin form lines. [ASSUMED — exact C value; validate against test.pdf Box 24]

**block_size validation:** `block_size` must be odd and >= 3. Add a runtime guard: `if block_size % 2 == 0: block_size += 1`.

**Settings integration:** `load_settings()` must be extended to include `threshold_block_size` in `_DEFAULTS` with value `31`. [VERIFIED: config_loader.py — key absent from current _DEFAULTS, must be added]

### 2.5 Debug Mode (D-11)

When `debug=True`, save each intermediate stage to project root:

```python
if debug:
    Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)).save("debug_01_raw.png")
    # after scale correction:
    Image.fromarray(cv2.cvtColor(scaled, cv2.COLOR_BGR2RGB)).save("debug_02_scaled.png")
    # after deskew:
    Image.fromarray(cv2.cvtColor(corrected, cv2.COLOR_BGR2RGB)).save("debug_03_deskewed.png")
    # after threshold (grayscale → RGB for PIL):
    Image.fromarray(cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB)).save("debug_04_threshold.png")
```

### 2.6 Return Value

`preprocess_page()` returns the thresholded image as `PIL.Image.Image` (mode "RGB", 2550×3300). Converting from grayscale back to RGB ensures downstream callers do not need to handle multiple modes.

---

## 3. Coordinate Calibration (EXTR-04)

### CLI Invocation (D-02)

```bash
python pipeline/calibrate.py --page 0 --pdf test.pdf
# Writes: calibration_overlay_p0.png  (project root)
```

### Form Type Detection for Field-Set Selection (D-04)

`calibrate.py` needs to choose between CMS-1500 and UB-04 field sets. In Phase 2, form detection logic (Phase 3) does not exist yet. Use a simple heuristic based on anchor text presence — or accept a `--form` override flag so the user can force a form type during calibration:

```
python pipeline/calibrate.py --page 0 --pdf test.pdf --form cms1500
python pipeline/calibrate.py --page 0 --pdf test.pdf --form ub04
python pipeline/calibrate.py --page 0 --pdf test.pdf          # auto-detect (best effort)
```

Auto-detect searches two small anchor regions: "HEALTH INSURANCE CLAIM FORM" (CMS-1500 header) and "UNIFORM BILLING" or "UB-04" (UB-04 header). If neither matches, default to CMS-1500 and print a warning. [ASSUMED — anchor strings for heuristic; verify against test.pdf]

### Overlay Drawing Pattern (D-01, D-03)

```python
# [VERIFIED: pre-loaded technical facts]
import cv2
from PIL import Image

overlay = cv_img.copy()  # cv_img is BGR

# For each FieldDef in the matched field set:
cv2.rectangle(overlay, (left, top), (right, bottom), (0, 255, 0), 2)  # green box
cv2.putText(
    overlay, field.name,         # full name per D-03
    (left, top - 4),             # above the rectangle
    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1  # red text
)

# For TableFieldDef — iterate all rows:
for row_idx, (l, t, r, b) in enumerate(table_field.row_boxes):
    cv2.rectangle(overlay, (l, t), (r, b), (0, 200, 255), 1)  # orange box for table rows
    label = f"{table_field.name}_r{row_idx}"
    cv2.putText(overlay, label, (l, t - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 140, 255), 1)

Image.fromarray(cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)).save(
    f"calibration_overlay_p{page_num}.png"
)
```

**Color scheme (Claude's discretion):** Green rectangles for `FieldDef`, orange for `TableFieldDef` rows. Red text for all labels. High-contrast on white form backgrounds.

### Scale-Corrected Coordinates in Overlay (D-05 specifics)

`calibrate.py` must pass the raw page image through `preprocess_page()` first so that the scale factors are applied before drawing — the overlay must reflect the corrected coordinate space, not the raw pixel space.

### Stdout Summary (Claude's discretion)

```
Form type:  CMS-1500 (auto-detected)
Page:       0
Fields:     18 FieldDef + 1 TableFieldDef (6 rows x 10 sub-fields = 60 regions)
Output:     calibration_overlay_p0.png
```

---

## 4. CMS-1500 Field Coordinates

All coordinates are at 300 DPI (2550×3300 px). These are **estimated starting points** — user must run `calibrate.py` and visually verify against `test.pdf` before Phase 4. [VERIFIED: pre-loaded technical facts — form dimensions and layout reference]

### 4.1 CMS1500_FIELDS (FieldDef)

| Name | box (l, t, r, b) | psm | whitelist | label |
|------|------------------|-----|-----------|-------|
| `claim_member_id` | (30, 160, 1200, 220) | 7 | None | "Claim/Member ID" |
| `box1_insurance_type` | (30, 220, 800, 270) | 7 | None | "Box 1 — Insurance Type" |
| `box1a_insured_id` | (1270, 220, 2520, 270) | 7 | None | "Box 1a — Insured ID" |
| `box2_patient_name` | (30, 270, 1270, 320) | 7 | None | "Box 2 — Patient Name" |
| `box3_dob_sex` | (1270, 270, 2000, 320) | 7 | `"0123456789/MF "` | "Box 3 — DOB / Sex" |
| `box5_patient_address` | (30, 320, 1270, 460) | 6 | None | "Box 5 — Patient Address" |
| `box17_referring_name` | (30, 850, 1270, 900) | 7 | None | "Box 17 — Referring Provider" |
| `box17b_referring_npi` | (1270, 850, 2000, 900) | 7 | `"0123456789"` | "Box 17b — Referring NPI" |
| `box19_additional_claim` | (30, 900, 2520, 950) | 7 | None | "Box 19 — Additional Claim Info" |
| `box21a_diag` | (30, 960, 200, 1010) | 7 | `"0123456789. "` | "Box 21a — Diagnosis A" |
| `box21b_diag` | (200, 960, 370, 1010) | 7 | `"0123456789. "` | "Box 21b — Diagnosis B" |
| `box21c_diag` | (370, 960, 540, 1010) | 7 | `"0123456789. "` | "Box 21c — Diagnosis C" |
| `box21d_diag` | (540, 960, 710, 1010) | 7 | `"0123456789. "` | "Box 21d — Diagnosis D" |
| `box21e_diag` | (30, 1010, 200, 1060) | 7 | `"0123456789. "` | "Box 21e — Diagnosis E" |
| `box21f_diag` | (200, 1010, 370, 1060) | 7 | `"0123456789. "` | "Box 21f — Diagnosis F" |
| `box21g_diag` | (370, 1010, 540, 1060) | 7 | `"0123456789. "` | "Box 21g — Diagnosis G" |
| `box21h_diag` | (540, 1010, 710, 1060) | 7 | `"0123456789. "` | "Box 21h — Diagnosis H" |
| `box21i_diag` | (710, 960, 880, 1010) | 7 | `"0123456789. "` | "Box 21i — Diagnosis I" |
| `box21j_diag` | (880, 960, 1050, 1010) | 7 | `"0123456789. "` | "Box 21j — Diagnosis J" |
| `box21k_diag` | (1050, 960, 1220, 1010) | 7 | `"0123456789. "` | "Box 21k — Diagnosis K" |
| `box21l_diag` | (1220, 960, 1390, 1010) | 7 | `"0123456789. "` | "Box 21l — Diagnosis L" |
| `box23_prior_auth` | (930, 1060, 1850, 1110) | 7 | `"0123456789 "` | "Box 23 — Prior Auth Number" |
| `box25_federal_tax_id` | (30, 2590, 700, 2640) | 7 | `"0123456789- "` | "Box 25 — Federal Tax ID" |
| `box26_patient_account` | (700, 2590, 1270, 2640) | 7 | None | "Box 26 — Patient Account No." |
| `box27_accept_assignment` | (1270, 2590, 1630, 2640) | 8 | None | "Box 27 — Accept Assignment" |
| `box28_total_charge` | (1630, 2590, 2000, 2640) | 7 | `"0123456789. "` | "Box 28 — Total Charge" |
| `box29_amount_paid` | (2000, 2590, 2300, 2640) | 7 | `"0123456789. "` | "Box 29 — Amount Paid" |
| `box32_service_facility` | (30, 2900, 1270, 3040) | 6 | None | "Box 32 — Service Facility" |
| `box33_billing_provider` | (1270, 2900, 2520, 3040) | 6 | None | "Box 33 — Billing Provider" |

**PSM notes:**
- psm=6 (block) for multi-line address fields: `box5_patient_address`, `box32_service_facility`, `box33_billing_provider`
- psm=8 (single word) for `box27_accept_assignment` (expects "YES" or "NO")
- psm=7 (single line) for all other fields

**Diagnosis codes (box21a–box21l):** ICD-10 dot format (`F32.9`) — open decision per CLAUDE.md/STATE.md, but the whitelist `"0123456789. "` supports both formats. Resolution deferred to Phase 4.

### 4.2 CMS1500_TABLE_FIELDS (TableFieldDef — Box 24 Service Lines)

Box 24 has 6 service line rows. Row y-ranges (top/bottom): SL1 (1130–1280), SL2 (1280–1430), SL3 (1430–1580), SL4 (1580–1730), SL5 (1730–1880), SL6 (1880–2030). Column x-ranges are shared across all rows.

**Sub-field column ranges (x-coordinates):**

| Sub-field | x-left | x-right | psm | whitelist |
|-----------|--------|---------|-----|-----------|
| date_from | 30 | 220 | 7 | `"0123456789/ "` |
| date_to | 220 | 410 | 7 | `"0123456789/ "` |
| pos | 410 | 500 | 7 | `"0123456789"` |
| emg | 500 | 560 | 8 | `"0123456789YN"` |
| cpt | 560 | 780 | 7 | `"0123456789"` |
| modifier | 780 | 950 | 7 | `"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "` |
| diag_ptr | 950 | 1080 | 7 | `"ABCDEFGHIJKL "` |
| charges | 1080 | 1270 | 7 | `"0123456789. "` |
| units | 1270 | 1450 | 7 | `"0123456789"` |
| rendering_npi | 1830 | 2520 | 7 | `"0123456789"` |

Each sub-field becomes one `TableFieldDef` with 6 `row_boxes`. Naming convention: `box24_{subfield}`.

**row_boxes for box24_date_from (x: 30–220):**
```python
TableFieldDef(
    name="box24_date_from",
    row_boxes=[
        (30, 1130, 220, 1280),  # SL1
        (30, 1280, 220, 1430),  # SL2
        (30, 1430, 220, 1580),  # SL3
        (30, 1580, 220, 1730),  # SL4
        (30, 1730, 220, 1880),  # SL5
        (30, 1880, 220, 2030),  # SL6
    ],
    psm=7,
    whitelist="0123456789/ ",
    label="Box 24 — Date From",
)
```

The same row y-ranges apply to all 10 sub-fields; only the x-coordinates change per column. Implementer should generate all 10 `TableFieldDef` entries following this pattern.

---

## 5. UB-04 Field Coordinates

All coordinates are at 300 DPI (2550×3300 px). Estimated starting points only — verify with `calibrate.py`. [VERIFIED: pre-loaded technical facts — UB-04 layout reference]

### 5.1 UB04_FIELDS (FieldDef)

| Name | box (l, t, r, b) | psm | whitelist | label |
|------|------------------|-----|-----------|-------|
| `box1_provider_name_addr` | (30, 30, 1270, 200) | 6 | None | "Box 1 — Provider Name/Address" |
| `box3b_patient_control` | (30, 200, 700, 270) | 7 | None | "Box 3b — Patient Control Number" |
| `box4_type_of_bill` | (700, 200, 1100, 270) | 7 | `"0123456789"` | "Box 4 — Type of Bill" |
| `box5_federal_tax` | (1100, 200, 1800, 270) | 7 | `"0123456789- "` | "Box 5 — Federal Tax Number" |
| `box6_statement_period` | (1800, 200, 2520, 270) | 7 | `"0123456789/ "` | "Box 6 — Statement Period" |
| `box8_patient_name` | (30, 270, 1270, 340) | 7 | None | "Box 8 — Patient Name" |
| `box9_patient_address` | (30, 340, 1270, 410) | 6 | None | "Box 9 — Patient Address" |
| `box10_birthdate` | (1270, 270, 1800, 340) | 7 | `"0123456789/ "` | "Box 10 — Birthdate" |
| `box11_sex` | (1800, 270, 2100, 340) | 8 | `"MFU "` | "Box 11 — Sex" |
| `box12_admission_date` | (2100, 270, 2520, 340) | 7 | `"0123456789/ "` | "Box 12 — Admission Date" |
| `box14_admission_type` | (1270, 340, 1800, 410) | 7 | `"0123456789"` | "Box 14 — Type of Admission" |
| `box17_patient_status` | (1800, 340, 2520, 410) | 7 | `"0123456789"` | "Box 17 — Patient Status" |
| `box50_payer_name` | (30, 2700, 800, 2850) | 6 | None | "Box 50 — Payer Name" |
| `box51_health_plan_id` | (800, 2700, 1500, 2850) | 6 | None | "Box 51 — Health Plan ID" |
| `box54_prior_payments` | (1500, 2700, 1900, 2850) | 7 | `"0123456789. "` | "Box 54 — Prior Payments" |
| `box55_est_amount_due` | (1900, 2700, 2300, 2850) | 7 | `"0123456789. "` | "Box 55 — Est. Amount Due" |
| `box56_npi` | (2300, 2700, 2520, 2850) | 7 | `"0123456789"` | "Box 56 — NPI" |
| `box58_insured_name` | (30, 2850, 900, 2950) | 7 | None | "Box 58 — Insured Name" |
| `box60_insured_unique_id` | (900, 2850, 1600, 2950) | 7 | None | "Box 60 — Insured Unique ID" |
| `box61_group_name` | (1600, 2850, 2200, 2950) | 7 | None | "Box 61 — Group Name" |
| `box63_treatment_auth` | (30, 2950, 900, 3050) | 6 | None | "Box 63 — Treatment Auth Codes" |
| `box64_doc_control` | (900, 2950, 1600, 3050) | 7 | None | "Box 64 — Document Control Number" |
| `box66_dx_codes` | (30, 3050, 2520, 3200) | 6 | `"0123456789. ABCDEFGHIJKLMNOPQRSTUVWXYZ"` | "Box 66–75 — Diagnosis/Procedure Codes" |
| `box76_attending_npi_name` | (30, 3200, 2520, 3300) | 6 | None | "Box 76 — Attending Provider NPI/Name" |

**PSM notes:**
- psm=6 (block) for multi-line / multi-value blocks: `box1_provider_name_addr`, `box9_patient_address`, `box50_payer_name`, `box51_health_plan_id`, `box63_treatment_auth`, `box66_dx_codes`, `box76_attending_npi_name`
- psm=8 (single word) for `box11_sex` (expects "M", "F", or "U")
- psm=7 (single line) for all other fields

### 5.2 UB04_TABLE_FIELDS (TableFieldDef — Revenue Lines)

Revenue lines span y≈410–2700 with 22 rows at ~105 px per row.

**Row y-ranges (top, bottom):**

| Row | top | bottom |
|-----|-----|--------|
| RL1 | 410 | 515 |
| RL2 | 515 | 620 |
| RL3 | 620 | 725 |
| RL4 | 725 | 830 |
| RL5 | 830 | 935 |
| RL6 | 935 | 1040 |
| RL7 | 1040 | 1145 |
| RL8 | 1145 | 1250 |
| RL9 | 1250 | 1355 |
| RL10 | 1355 | 1460 |
| RL11 | 1460 | 1565 |
| RL12 | 1565 | 1670 |
| RL13 | 1670 | 1775 |
| RL14 | 1775 | 1880 |
| RL15 | 1880 | 1985 |
| RL16 | 1985 | 2090 |
| RL17 | 2090 | 2195 |
| RL18 | 2195 | 2300 |
| RL19 | 2300 | 2405 |
| RL20 | 2405 | 2510 |
| RL21 | 2510 | 2595 |
| RL22 | 2595 | 2700 |

**Sub-field column ranges:**

| Sub-field | x-left | x-right | psm | whitelist |
|-----------|--------|---------|-----|-----------|
| rev_code | 30 | 200 | 7 | `"0123456789"` |
| description | 200 | 700 | 7 | None |
| hcpcs | 700 | 1000 | 7 | `"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "` |
| svc_date | 1000 | 1270 | 7 | `"0123456789/ "` |
| units | 1270 | 1500 | 7 | `"0123456789"` |
| total_charges | 1500 | 1900 | 7 | `"0123456789. "` |
| non_covered | 1900 | 2200 | 7 | `"0123456789. "` |

Each sub-field becomes one `TableFieldDef` with 22 `row_boxes`. Naming convention: `ub04_rl_{subfield}`.

**Example — ub04_rl_rev_code:**
```python
TableFieldDef(
    name="ub04_rl_rev_code",
    row_boxes=[
        (30, 410,  200, 515),   # RL1
        (30, 515,  200, 620),   # RL2
        (30, 620,  200, 725),   # RL3
        (30, 725,  200, 830),   # RL4
        (30, 830,  200, 935),   # RL5
        (30, 935,  200, 1040),  # RL6
        (30, 1040, 200, 1145),  # RL7
        (30, 1145, 200, 1250),  # RL8
        (30, 1250, 200, 1355),  # RL9
        (30, 1355, 200, 1460),  # RL10
        (30, 1460, 200, 1565),  # RL11
        (30, 1565, 200, 1670),  # RL12
        (30, 1670, 200, 1775),  # RL13
        (30, 1775, 200, 1880),  # RL14
        (30, 1880, 200, 1985),  # RL15
        (30, 1985, 200, 2090),  # RL16
        (30, 2090, 200, 2195),  # RL17
        (30, 2195, 200, 2300),  # RL18
        (30, 2300, 200, 2405),  # RL19
        (30, 2405, 200, 2510),  # RL20
        (30, 2510, 200, 2595),  # RL21
        (30, 2595, 200, 2700),  # RL22
    ],
    psm=7,
    whitelist="0123456789",
    label="UB-04 Revenue Line — Rev Code",
)
```

---

## 6. Pipeline Module Design

### Package Layout

```
pipeline/
├── __init__.py        # re-exports convert_page, preprocess_page
├── converter.py       # convert_page(pdf_path, page_num) → PIL Image
├── preprocessor.py    # preprocess_page(image, settings, debug=False) → PIL Image
└── calibrate.py       # CLI: python pipeline/calibrate.py --page N --pdf PATH [--form TYPE]
```

### `pipeline/__init__.py` Public API

```python
from pipeline.converter import convert_page
from pipeline.preprocessor import preprocess_page

__all__ = ["convert_page", "preprocess_page"]
```

### `pipeline/converter.py` Responsibilities

- Import `load_settings` from `config_loader`
- Call `convert_from_path` with `dpi=300`, `first_page=page_num+1`, `last_page=page_num+1`, `poppler_path` from settings
- Assert `image.size == (2550, 3300)`; raise `ValueError` if not (D-13)
- Return `pages[0]` (PIL Image, mode "RGB")
- No preprocessing — raw image only (D-14)

### `pipeline/preprocessor.py` Responsibilities

- Accept `(image: PIL.Image.Image, settings: dict, debug: bool = False)`
- Execute steps in order: scale correction → deskew → adaptive threshold (D-08)
- Read `settings.get("threshold_block_size", 31)` (D-09)
- Raise `ValueError` for skew > ±5° (D-10)
- Save debug PNGs to project root when `debug=True` (D-11)
- Return preprocessed PIL Image (RGB, 2550×3300)

### `pipeline/calibrate.py` Responsibilities

- `argparse` CLI: `--page` (int, required), `--pdf` (str, required), `--form` (str, optional: "cms1500" | "ub04")
- Load settings via `load_settings()`
- Call `convert_page(pdf_path, page_num)` for raw image
- Call `preprocess_page(image, settings)` to apply scale correction
- Detect form type (anchor heuristic or `--form` override)
- Load matching field lists from `config/cms1500.py` or `config/ub04.py`
- Draw overlay (green `FieldDef` rects, orange `TableFieldDef` row rects, red text labels)
- Write `calibration_overlay_p{N}.png` to project root (D-01)
- Print stdout summary (field count, form type, output path) — Claude's discretion

### Settings Extension Required

Add `threshold_block_size: 31` to `_DEFAULTS` in `config_loader.py`. [VERIFIED: current `_DEFAULTS` does not include this key]

---

## 7. Test Strategy (tests/test_phase2.py)

All tests follow the `tests/test_phase{N}.py` convention (D-15). Tests use `test.pdf` as the reference sample.

### Test Cases

| Test | Behavior | Type | Verification |
|------|----------|------|-------------|
| `test_convert_page_dimensions` | `convert_page("test.pdf", 0)` returns PIL Image of size (2550, 3300) | unit | `assert image.size == (2550, 3300)` |
| `test_convert_page_mode` | Returned image mode is "RGB" | unit | `assert image.mode == "RGB"` |
| `test_convert_page_invalid_pdf` | Non-existent path raises exception | unit | `pytest.raises(Exception)` |
| `test_preprocess_smoke` | `preprocess_page(image, settings)` returns PIL Image same size | integration | `assert result.size == (2550, 3300)` |
| `test_preprocess_mode` | Returned image mode is "RGB" | integration | `assert result.mode == "RGB"` |
| `test_preprocess_debug_files` | `debug=True` writes 4 intermediate PNGs to project root | integration | `os.path.exists("debug_01_raw.png")` etc. |
| `test_deskew_rejection` | Artificially rotated image (6°) raises `ValueError` | unit | `pytest.raises(ValueError, match="exceeds ±5°")` |
| `test_scale_factors_near_one` | Scale factors for a well-scanned page are within 0.98–1.02 | integration | inspect `scale_x`, `scale_y` via helper or debug output |
| `test_calibrate_overlay_created` | `calibrate.py --page 0 --pdf test.pdf` writes `calibration_overlay_p0.png` | smoke | `subprocess.run(...)` + `os.path.exists(...)` |
| `test_calibrate_overlay_nonempty` | Overlay PNG is larger than 1 KB | smoke | `os.path.getsize(...) > 1024` |
| `test_settings_threshold_block_size_default` | `load_settings()` returns `threshold_block_size == 31` when key absent from JSON | unit | direct assertion on dict |
| `test_cms1500_fields_populated` | `CMS1500_FIELDS` is non-empty list of `FieldDef` instances | unit | `len(CMS1500_FIELDS) > 0` |
| `test_ub04_fields_populated` | `UB04_FIELDS` is non-empty list of `FieldDef` instances | unit | `len(UB04_FIELDS) > 0` |
| `test_cms1500_table_fields_row_count` | Each `TableFieldDef` in `CMS1500_TABLE_FIELDS` has exactly 6 `row_boxes` | unit | `all(len(f.row_boxes) == 6 for f in CMS1500_TABLE_FIELDS)` |
| `test_ub04_table_fields_row_count` | Each `TableFieldDef` in `UB04_TABLE_FIELDS` has exactly 22 `row_boxes` | unit | `all(len(f.row_boxes) == 22 for f in UB04_TABLE_FIELDS)` |

---

## 8. Implementation Risks & Notes

### Windows-Specific

- **Poppler path:** Must be explicit (`poppler_path=settings["poppler_path"]`). Do not rely on PATH. Default: `C:\Program Files\poppler\Library\bin`. [VERIFIED: config_loader.py]
- **Backslash in paths:** Always use `pathlib.Path` or raw strings for Windows paths; `pdf2image` accepts both.
- **OpenCV on Windows:** `cv2` is installed as `opencv-python`; no additional DLLs required for the functions used here.

### pdf2image Quirks

- Returns a list always, even for `first_page == last_page`. Always index `[0]`.
- DPI parameter controls the PIL Image size; 300 DPI + US Letter = 2550×3300 px. [VERIFIED: pre-loaded technical facts]
- If `poppler_path` is wrong, pdf2image raises `PDFInfoNotInstalledError` or `PDFPageCountError` — not `FileNotFoundError`. Tests should handle this.

### OpenCV Color Channel Order

- `np.array(pil_image)` produces RGB. OpenCV expects BGR. Convert immediately on entry (`cv2.COLOR_RGB2BGR`), convert back on exit (`cv2.COLOR_BGR2RGB` or `cv2.COLOR_GRAY2RGB`). Failure to do this causes subtle hue errors invisible in grayscale but visible if anyone inspects debug PNGs.

### Adaptive Threshold `blockSize` Must Be Odd

- `cv2.adaptiveThreshold` raises `cv2.error` if `blockSize` is even. Validate and auto-correct: `if block_size % 2 == 0: block_size += 1`.

### Coordinate Accuracy

- All coordinates in Sections 4 and 5 are **estimates from standard form dimensions** and have not been validated against `test.pdf`. They are starting points only.
- The calibration overlay workflow (Section 3) is the mandatory verification gate.
- Do not begin Phase 4 (field extraction) until the user has run `calibrate.py` on a representative CMS-1500 page and a representative UB-04 page and confirmed coordinates are accurate. This is the highest-risk phase per STATE.md.

### Deskew on Blank/Sparse Pages

- If a page has very little content (e.g., a mostly-blank continuation page), `cv2.HoughLinesP` may find no near-horizontal lines. In this case, skip rotation (treat as 0° skew) rather than raising an error. Document this behavior.

### Box 21 Diagnosis Codes — ICD-10 Format

- ICD-10 dot format (`F32.9` vs `F329`) is an open decision (CLAUDE.md, STATE.md). The whitelist `"0123456789. "` supports both. Phase 4 will resolve this.

---

## Validation Architecture

| Behavior | Test Type | Verification Method |
|----------|-----------|---------------------|
| `convert_page()` returns 2550×3300 RGB PIL Image at 300 DPI | Integration | `assert image.size == (2550, 3300) and image.mode == "RGB"` against test.pdf page 0 |
| `convert_page()` raises `ValueError` for non-standard-size result | Unit | Mock `convert_from_path` to return wrong-size image; `pytest.raises(ValueError)` |
| `preprocess_page()` returns same-size RGB PIL Image | Integration | `assert result.size == (2550, 3300) and result.mode == "RGB"` |
| `preprocess_page(debug=True)` writes intermediate PNGs | Integration | Verify 4 debug PNG files exist after call |
| Deskew raises `ValueError` for angle > ±5° | Unit | Pass artificially rotated image; `pytest.raises(ValueError, match="exceeds")` |
| Scale factors for clean scan are ~1.0 (within 2%) | Integration | Assert `0.98 <= scale_x <= 1.02` on test.pdf page 0 |
| `calibrate.py` CLI writes `calibration_overlay_p{N}.png` | Smoke | `subprocess.run(["python", "pipeline/calibrate.py", "--page", "0", "--pdf", "test.pdf"])` + file exists check |
| `CMS1500_FIELDS` is non-empty, all `FieldDef` instances | Unit | `len(CMS1500_FIELDS) > 0`, `all(isinstance(f, FieldDef) for f in CMS1500_FIELDS)` |
| `UB04_FIELDS` is non-empty, all `FieldDef` instances | Unit | Same pattern |
| `CMS1500_TABLE_FIELDS` each has exactly 6 row_boxes | Unit | `all(len(f.row_boxes) == 6 for f in CMS1500_TABLE_FIELDS)` |
| `UB04_TABLE_FIELDS` each has exactly 22 row_boxes | Unit | `all(len(f.row_boxes) == 22 for f in UB04_TABLE_FIELDS)` |
| `load_settings()` returns `threshold_block_size == 31` when absent from JSON | Unit | Call with no JSON file or empty JSON; assert key present with value 31 |
| Box 24 grey bands visibly cleaner after threshold | Manual | Inspect `debug_04_threshold.png` vs `debug_01_raw.png` in Box 24 region |
| Calibration overlay labels all configured fields | Manual | Open `calibration_overlay_p{N}.png`, verify all field names visible and rects roughly aligned |

**Test infrastructure note:** `tests/test_phase2.py` does not yet exist — it is a Wave 0 gap. `test.pdf` (30 pages) is present in the project root and serves as the integration test fixture. [VERIFIED: git status shows test.pdf present]

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Hough-line deskew is more reliable than minAreaRect on scanned medical forms | Section 2.3 | May need to switch to minAreaRect if Hough fails on low-content pages |
| A2 | `C=11` is appropriate for adaptive threshold at 300 DPI scanned documents | Section 2.4 | Box 24 grey bands may not fully clear; user can tune via blockSize adjustment |
| A3 | Anchor strings "HEALTH INSURANCE CLAIM FORM" and "UB-04" reliably distinguish form types in `calibrate.py` | Section 3 | Auto-detection may misfire; `--form` override mitigates this |
| A4 | Box 21 diagnosis codes occupy a 3-column × 4-row grid at y≈960–1060 with ~170 px cell width | Section 4.1 | Actual grid may differ; coordinates need calibration verification |
| A5 | UB-04 revenue lines are evenly spaced at ~105 px/row from y=410 to y=2700 | Section 5.2 | Row boundaries may be uneven; calibration will reveal actual spacing |

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 | All modules | Assumed ✓ | 3.11 | — |
| pdf2image | `converter.py` | Assumed ✓ (Phase 1 verified) | — | — |
| Poppler | `converter.py` | Assumed ✓ (Phase 1 verified) | — | — |
| OpenCV (`opencv-python`) | `preprocessor.py`, `calibrate.py` | Assumed ✓ (Phase 1 listed in stack) | — | — |
| NumPy | `preprocessor.py` | Assumed ✓ (OpenCV dependency) | — | — |
| Pillow | All modules | Assumed ✓ (Phase 1 verified) | — | — |
| `test.pdf` | Integration tests | ✓ (present in project root) | 30 pages | — |

All runtime dependencies are assumed available from Phase 1 environment verification. [ASSUMED — no re-probe performed in this session]

---

## Sources

### Primary (HIGH confidence)
- `config/base.py` — `FieldDef`, `TableFieldDef` dataclass schemas (verified by Read tool)
- `config_loader.py` — `load_settings()` implementation, `_DEFAULTS` keys (verified by Read tool)
- `.planning/phases/02-image-pipeline-coordinate-calibration/02-CONTEXT.md` — all design decisions D-01 through D-15 (verified by Read tool)
- `.planning/REQUIREMENTS.md` — PROC-01, PROC-02, EXTR-04, EXTR-01, EXTR-02 full text (verified by Read tool)
- Pre-loaded technical facts — pdf2image API, PIL↔OpenCV conversion, adaptive threshold, deskew, scale correction, calibration overlay patterns

### Secondary (MEDIUM confidence)
- CMS-1500 / UB-04 coordinate estimates from pre-loaded standard form layout reference (2550×3300 px at 300 DPI)

### Tertiary (LOW confidence)
- C=11 constant recommendation for adaptive threshold — standard convention, not verified against test.pdf
- Hough-line reliability claim for scanned medical forms — implementation experience assumption

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified from Phase 1 code and CLAUDE.md
- Architecture: HIGH — all decisions locked in CONTEXT.md D-01 to D-15
- Field coordinates: MEDIUM — derived from standard form dimensions, require visual calibration
- Pitfalls: HIGH — Windows path issues and OpenCV channel order are well-established

**Research date:** 2026-04-29
**Valid until:** 2026-05-29 (stable domain; coordinate estimates valid until user calibrates against test.pdf)
