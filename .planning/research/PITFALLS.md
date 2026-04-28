# Domain Pitfalls: Python OCR Desktop Application (CMS-1500 / UB-04)

**Domain:** Fixed-layout medical form OCR extraction — scanned paper at 300 DPI
**Researched:** 2026-04-28
**Confidence note:** Bash and WebSearch tools were blocked in this session. All findings are from
training knowledge covering Tesseract, OpenCV, openpyxl, poppler, and Windows packaging
patterns. Confidence levels are assessed honestly below.

---

## Critical Pitfalls

Mistakes that cause rewrites, silent data corruption, or project abandonment.

---

### CRITICAL-1: Tesseract Misreads on Medical Codes Because No PSM/OEM and No Whitelist Are Set

**What goes wrong:**
Tesseract's default configuration (PSM 3 — fully automatic page segmentation) treats a small
cropped field as a document. It invents word breaks, adds spurious punctuation, and confuses
characters that are visually similar in printed type: `0` vs `O`, `1` vs `l` vs `I`, `8` vs `B`,
`5` vs `S`, `2` vs `Z`. In ICD-10 codes (format A00.0), CPT codes (5 digits, all numeric), and
NPI numbers (10 digits), a single character error produces a structurally valid-looking but
medically wrong code that downstream validation will not catch.

**Why it happens:**
- PSM 3 activates orientation detection and layout analysis — expensive and wrong for a
  single-field crop.
- OEM 3 (default: LSTM + legacy) defaults to LSTM, which has higher character-level accuracy on
  natural language but performs worse than the legacy engine on monospaced or printed
  alphanumeric strings with no linguistic context.
- Without `tessedit_char_whitelist`, Tesseract can produce any Unicode character including
  curly quotes, dashes, and letters from other scripts when ink bleed confuses the model.

**Consequences:**
- ICD-10 code `F32.9` read as `F3Z.9` — structurally plausible, medically wrong.
- CPT `99213` read as `9921З` (Cyrillic Ze) — passes string length check, fails numeric cast.
- Date fields like `01/15/2024` read as `O1/l5/2O24` — regex rejects the row silently.
- Silent data loss: if you strip unrecognised characters rather than flagging, the error
  disappears into empty cells.

**Prevention:**
- Set `--psm 7` (single line) for most field crops; use `--psm 8` for single-word crops (e.g.,
  two-char state code), `--psm 6` only if a field can span multiple lines.
- Set `--oem 1` (LSTM only) for most fields. Fall back to `--oem 0` (legacy) for date and
  numeric-only fields if accuracy does not meet threshold after testing.
- Apply per-field whitelists: numeric-only fields `0123456789`, date fields `0123456789/`,
  ICD-10 fields `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.`, CPT `0123456789`.
- Implement a post-OCR validator per field type: regex patterns for ICD-10, CPT, NPI, date,
  dollar amount — flag rather than silently accept anything that fails.
- Scale cropped images up to 2x before passing to Tesseract if the source crop is narrower
  than ~150px in height; Tesseract accuracy degrades noticeably below ~20px x-height.

**Warning signs:**
- Character-level accuracy looks "good" in quick spot-checks but structured fields have a 5-15%
  error rate when validated against known codes.
- Date columns in Excel output have mixed formats (some parsed as dates, some as strings).
- NPI fields occasionally contain lowercase letters.

**Phase:** Addressed in the preprocessing and OCR configuration phase (before any field
extraction logic is written). Do not treat it as "tunable later" — it affects every field.

---

### CRITICAL-2: Coordinate Drift — Fixed Pixel Regions Silently Clip or Miss Fields

**What goes wrong:**
Coordinates derived from a reference scan (2550 × 3300 px, 8.5 × 11 in @ 300 DPI) are applied
unchanged to every scan. Real scanner output varies: some scanners add a few pixels of white
border; some produce 2538 × 3284; some produce 2560 × 3318. A 1% size difference at 300 DPI
is 25–33 px, which is enough to clip a character on the right edge of a field box or miss the
top line of a two-line field entirely. Skew compounds this: a 0.5-degree rotation shifts the
right edge of a full-width field by about 23 px — nearly invisible to the eye but fatal to a
tight crop.

**Why it happens:**
- Region coordinates are derived manually from one "perfect" scan, then hardcoded.
- No affine correction or template matching is applied before extraction.
- Clipped crops produce partial characters that Tesseract reads as wrong characters or skips.
- The failure is silent: extraction runs and produces a value, it is just wrong.

**Consequences:**
- Dollar amounts lose their leading or trailing digit.
- Box 24 service line rows are misaligned — the wrong row's data ends up in the wrong output
  column.
- Multi-column fields (e.g., date of service From/To split into two sub-boxes) become merged
  or inverted.

**Prevention:**
- On every page, before extracting any field, detect the form's bounding rectangle using one
  of: (a) Hough line detection of the outer border, (b) template matching against a known
  anchor region (e.g., "HEALTH INSURANCE CLAIM FORM" header text area for CMS-1500, "UB-04"
  logo area for UB-04), or (c) contour detection of the outermost black box.
- Compute a scale factor: `scale_x = detected_width / 2550`, `scale_y = detected_height / 3300`.
  Apply to all region coordinates before cropping.
- Apply deskew before coordinate extraction. Use the Hough-line or projection-profile method
  to detect rotation angle, then `cv2.warpAffine` to correct it. Even 0.3-degree residual
  skew matters at the right edge of wide fields.
- Add 4–8 px of padding around every crop region as a buffer, then trim whitespace after OCR.
  This costs almost nothing in accuracy and prevents edge-clipping failures.

**Warning signs:**
- Spot-checking crops shows text that is obviously cut off on one side.
- Box 24 line items are consistently one row off in some batches but not others.
- Accuracy is perfect on your development scans but degrades on scans from a different office
  that uses a different scanner model.

**Phase:** Core architecture phase — the coordinate mapping layer must exist before field
extraction is built. Retrofitting scale/deskew correction after extraction logic is written
causes significant rework.

---

### CRITICAL-3: Grey-Banded Row Backgrounds in CMS-1500 Box 24 Destroy Tesseract Accuracy

**What goes wrong:**
CMS-1500 Box 24 alternates between white and light grey (approximately RGB 210–220, 210–220,
210–220) row backgrounds for the six service line rows. When Tesseract receives a crop from a
grey-banded row, its binarization (Otsu's method by default) struggles: the grey background is
close to the ink threshold, so it either (a) preserves the grey as foreground noise that
fragments characters, or (b) elevates the threshold and washes out light or small-font
characters. Both produce significantly worse accuracy than a white-background crop from the
same form.

**Why it happens:**
- Otsu's global threshold assumes a bimodal pixel distribution (background/foreground) — grey
  bands shift the distribution and misplace the threshold.
- Scanner variability makes the grey darker or lighter — what works on one batch fails on
  another.
- Adaptive thresholding fixes the global problem but introduces block-edge artifacts if block
  size is poorly chosen for the field height.

**Consequences:**
- Service line dates, CPT codes, modifiers, units, and charges all have elevated error rates.
- The exact rows affected vary by batch, making test coverage misleading.

**Prevention:**
- Before OCR, apply a grey-removal step to every crop:
  1. Convert to greyscale.
  2. Apply `cv2.threshold` with type `cv2.THRESH_BINARY + cv2.THRESH_OTSU` — but first check
     the mean pixel value. If mean > 200 (light field), proceed normally. If mean is between
     170–200 (grey band), boost contrast first: `cv2.convertScaleAbs(img, alpha=1.5, beta=20)`
     then threshold.
  3. Alternatively: convert to HSV, threshold the Saturation channel (grey pixels have near-zero
     saturation), flood-fill or replace grey background pixels with white before binarizing.
  4. Most robust: use `cv2.adaptiveThreshold` with `ADAPTIVE_THRESH_GAUSSIAN_C`, block size of
     31–51 (depending on x-height), constant C of 10. This adapts locally and eliminates the
     grey band effect without requiring manual threshold tuning.
- Test on both white-background and grey-background rows in your validation suite — they will
  have different failure modes.

**Warning signs:**
- Rows 2, 4, 6 in Box 24 (grey-banded rows) consistently have lower accuracy than rows 1, 3, 5.
- CPT codes in grey rows have extra noise characters appended.
- Units/charges in grey rows are occasionally blank despite clearly visible ink.

**Phase:** Preprocessing phase, specifically the image preparation pipeline for Box 24. Should
be designed as a per-crop preprocessing step, not a whole-page step, so non-grey fields are
not affected by overly aggressive contrast adjustment.

---

### CRITICAL-4: Form Type Detection That Relies on Fixed Coordinates Fails on Clipped Scans

**What goes wrong:**
A common approach is to look for a distinguishing text string at a fixed location — e.g., check
pixel region (X, Y, W, H) for "1500" or "UB-04". When the top of a page is partially clipped
by a scanner lid, or when a claim number stamp covers the corner, that region returns garbage
or nothing. The form type is misidentified, all subsequent field coordinates are wrong, and the
output is silently garbage rather than an error.

**Why it happens:**
- Single-anchor detection has no fallback.
- Stamps and annotations are most common on form corners — exactly where distinguishing
  identifiers live.
- Confidence is not propagated: if detection returns a low-score match, it is still treated as
  a firm decision.

**Consequences:**
- CMS-1500 pages run through the UB-04 extractor: all fields return empty or wrong values.
- No error is raised. Output rows look plausible (same column names, just wrong data).
- Mixed-batch files (both form types in one folder) produce silently corrupt output.

**Prevention:**
- Use multiple anchors, not one. For CMS-1500: "HEALTH INSURANCE CLAIM FORM" header text region
  AND the "NPI" label in Box 33, AND the structural pattern of Box 24's 6-row grid. Require at
  least 2 of 3 to agree.
- For UB-04: the "UB-04" text in the upper left AND the presence of revenue code column headers
  AND the 23-line service grid structure.
- Use template matching (cv2.matchTemplate) on a small distinctive sub-image rather than OCR
  for detection — it is faster, more robust to partial clipping, and does not require correct
  binarization.
- Assign a confidence score to detection. If confidence falls below threshold, write the page
  to an "undetected" holding folder rather than guessing and proceeding.
- Log detection decisions with the matched anchor evidence so failures are diagnosable.

**Warning signs:**
- A batch with both CMS-1500 and UB-04 files produces output that mixes fields from both forms
  into the same columns.
- Processing a new client's scans (different scanner, paper stock, or form vendor) suddenly has
  high misdetection.
- Detection works perfectly in isolation but fails when a stamp or handwritten annotation
  appears near the form identifier.

**Phase:** Form detection phase — must be the first processing step before any extraction. Must
have an "unknown/unconfident" exit path that does not silently produce garbage.

---

## Moderate Pitfalls

---

### MOD-1: Multi-Page Claim Grouping Based on "CONTINUED" Text Alone

**What goes wrong:**
A claim can span multiple pages with identical layouts. The naive approach is to look for
"CONTINUED ON NEXT PAGE" text at the bottom, or its absence to detect the last page. This
fails when: (a) the footer is clipped or smudged, (b) the footer text varies by form vendor
("CONTINUED..." vs "Page 1 of 3" vs no footer at all), (c) a single-page claim's footer area
happens to contain ink artifacts that look like text, or (d) the claim number stamp — present
on UB-04 continuation pages — is absent on the first page, making first/continuation
distinction ambiguous.

**Prevention:**
- Primary grouping key: claim number (Box 3 on CMS-1500 patient control, or the stamped
  number on UB-04). Extract and compare across consecutive pages.
- Secondary signal: "Page X of Y" text if present in footer.
- Tertiary signal: detect whether key header fields (patient name, insured name, date of birth)
  have values — they are filled only on the first page; continuation pages leave them blank.
- Never rely on a single signal. Implement a majority-vote grouping heuristic with a confidence
  score. Pages with ambiguous grouping should be flagged for manual review, not silently joined
  or split.
- Sort pages by filename/order before grouping — do not assume a PDF's internal page order is
  correct after batch scanning.

**Warning signs:**
- Claims with an odd number of service lines are split across an extra output row.
- Two unrelated claims are merged into one output row.
- Date-of-service ranges span impossible periods (e.g., January to December on one "claim"
  that is actually two merged claims).

**Phase:** Claim grouping / orchestration phase, after extraction is stable. Getting grouping
wrong early pollutes the entire output dataset.

---

### MOD-2: openpyxl Conditional Formatting Silently Produces Corrupt or Unrendered Output

**What goes wrong:**
openpyxl's ConditionalFormatting API accepts rules but does not validate them. Common mistakes:

- Passing a `PatternFill` with an invalid `fgColor` hex string (e.g., `"FFFF00"` instead of
  the ARGB format `"FFFFFF00"`) — Excel opens the file but renders no colour.
- Adding more than ~64 distinct conditional formatting rules to a single worksheet — Excel's
  older format limit; the file opens but rules beyond the limit are silently ignored.
- Using `FormulaRule` with a formula that references absolute cell addresses that do not shift
  correctly when the rule is applied to a range — rows at the bottom of the sheet get the
  formula evaluated against row 1's data.
- Writing conditional formatting to `.xlsx` and then opening in LibreOffice Calc — some rule
  types are rendered differently or not at all.
- Calling `ws.conditional_formatting.add()` inside a loop for every row rather than once with a
  range — generates a separate XML rule per row, inflating file size and slowing Excel open
  times dramatically for 100+ row outputs.

**Prevention:**
- Use ARGB 8-digit hex for all colours in openpyxl (`"FF" + "RRGGBB"`, e.g., `"FFFF0000"` for
  red).
- Apply conditional formatting as a single range rule, not per-row: `ws.conditional_formatting
  .add("A2:Z101", rule)`.
- Limit total conditional formatting rules per sheet to under 50. If highlighting logic is
  complex, consider applying cell fill colours directly at write time (data-driven colouring)
  rather than using Excel's conditional formatting engine.
- Test the output `.xlsx` in Excel (not just openpyxl's writer) before shipping — openpyxl
  silently writes invalid OOXML that only manifests as wrong rendering in the actual
  application.
- For validation highlighting (flag bad ICD codes, missing required fields), prefer direct
  `cell.fill = PatternFill(...)` keyed on your Python-side validation results rather than
  pushing rule logic into Excel.

**Warning signs:**
- Colour-highlighting looks correct when writing a 10-row test but disappears on a 100-row
  production output.
- File opens with "repaired content" warning in Excel after openpyxl writes it.
- Conditional formatting applies to row 1 data when viewing rows 50–100.

**Phase:** Export / output phase. Build a minimal working Excel writer first; add conditional
formatting in a dedicated hardening sub-phase with a real Excel test fixture.

---

### MOD-3: Windows Tesseract + Poppler Install Fragility

**What goes wrong:**
Tesseract on Windows is not a `pip install` — it requires a separate binary installer, and the
Python `pytesseract` wrapper has no knowledge of where it is installed until you tell it.
Poppler (required by `pdf2image` to rasterise PDFs) has the same problem: no official Windows
binary on PyPI, requires a separate download and PATH setup.

The failure modes, in order of frequency:

1. **`pytesseract.TesseractNotFoundError`** at first run — Tesseract installed but not on PATH
   and `pytesseract.pytesseract.tesseract_cmd` not set.
2. **Missing `eng.traineddata`** — Tesseract installed from an unofficial binary that omits
   the English language pack; OCR runs but returns empty strings.
3. **Wrong Tesseract version** — version 4.x (LSTM) vs 5.x have different `--oem` behaviour;
   some community builds labelled "5.0" are actually patched 4.1 builds with different accuracy
   profiles.
4. **Poppler `pdftoppm` not on PATH** — `pdf2image.convert_from_path` raises a FileNotFoundError
   that looks like a Python error, not a poppler error, confusing new users.
5. **PATH set in installer but not visible in the Python subprocess** — happens when Tesseract
   is installed to a user-level PATH on a machine where the Python environment runs as a
   different user or from a scheduled task.
6. **Antivirus quarantine** — on managed Windows machines, Tesseract's `.exe` is occasionally
   quarantined by corporate AV on first run. No error is raised; OCR silently returns empty
   strings because the subprocess call exits with a non-zero code that pytesseract swallows in
   some versions.

**Prevention:**
- Document and script the install sequence explicitly:
  1. Tesseract Windows installer from UB-Mannheim (the canonical Windows build):
     `https://github.com/UB-Mannheim/tesseract/wiki`. Install to a fixed, non-space path
     (e.g., `C:\Tesseract-OCR`). Select English language data during install.
  2. Poppler Windows binary from `https://github.com/oschwartz10612/poppler-windows/releases`.
     Extract to a fixed path (e.g., `C:\poppler\Library\bin`), add to user PATH.
- In `config.py` or startup code, set `pytesseract.pytesseract.tesseract_cmd` explicitly
  rather than relying on PATH. Add a startup self-test that runs `pytesseract.get_tesseract_
  version()` and raises a clear, user-readable error if it fails.
- Validate `eng.traineddata` exists at the tessdata path at startup.
- For `pdf2image`, pass `poppler_path=` explicitly rather than relying on PATH.
- Ship a `setup_check.py` script that end users run first — it tests Tesseract, poppler, and
  Python package versions and prints pass/fail for each.

**Warning signs:**
- Works on the developer machine but fails on client installs.
- OCR returns empty strings with no exception raised.
- `subprocess.CalledProcessError` in pytesseract that mentions exit code 1 with no further
  detail (classic AV quarantine symptom).

**Phase:** Project setup / Phase 1 foundations. The install fragility must be solved before any
OCR code is written, and a reproducible setup procedure must be documented and tested on a
clean machine before the project reaches the client.

---

### MOD-4: Stamp and Annotation Overlays Corrupt Underlying Field Data

**What goes wrong:**
UB-04 claim number stamps are physical ink applied on top of printed form fields. When a stamp
falls over a field being extracted (e.g., a revenue code, date of service, or charge amount),
the OCR crop contains both the original field data and the stamp ink. Tesseract tries to read
both as a single text region and produces gibberish. The field is not empty — it has a value —
so no "missing field" flag is raised.

**Prevention:**
- For known stamp locations (upper-right corner of UB-04 is the most common), exclude those
  pixel regions from any field that overlaps with them, or flag any field crop whose pixel
  density (ratio of dark pixels) is anomalously high as "possibly annotated."
- Use connected-component analysis: stamps tend to produce a cluster of large connected
  components at the same ink density as the form border. If a crop's largest connected
  component is much larger than the expected character size, flag it.
- At minimum, log any field whose OCR confidence score (available via `pytesseract.image_to_
  data` word-level confidence) is below a threshold (e.g., mean word confidence < 50) — these
  are candidates for annotation interference.

**Warning signs:**
- Specific fields on UB-04 pages always return garbled values on the same subset of documents.
- The garbled values are longer than the expected field length.
- Visual inspection of the crop shows ink from a different source overlaid on the field text.

**Phase:** Preprocessing and extraction phases. Stamp detection logic can be added in a hardening
iteration after core extraction works; the logging of low-confidence fields should be in from
the start.

---

## Minor Pitfalls

---

### MINOR-1: DPI Mismatch Between pdf2image Conversion and Coordinate System

**What goes wrong:**
`pdf2image.convert_from_path` has a `dpi` parameter that defaults to 200, not 300. If the PDF
contains embedded 300 DPI scan images and you rasterise at 200 DPI, you get a
1700 × 2200 px image. All coordinates derived from 2550 × 3300 are off by a factor of
0.667 — every field is extracted from the wrong location. This is immediately obvious on
spot-check but easy to miss if you are developing against pre-rasterised TIFFs and forget to
set the parameter when switching to PDF input.

**Prevention:**
- Always pass `dpi=300` explicitly to `convert_from_path`. Add an assertion on the returned
  image dimensions before processing any page.
- Document the canonical image size (2550 × 3300) in a constants file and assert against it at
  the image-loading boundary.

**Phase:** Input/ingestion phase. One-line fix but causes total coordinate failure if missed.

---

### MINOR-2: Tesseract Page Segmentation Hangs on Very Dark or Inverted Images

**What goes wrong:**
If a scan has high contrast with a very dark background (scanner lid open, toner bleed-through
from reverse side) or if binarization inverts the image (white text on black), Tesseract with
PSM 3 can spend 30–120 seconds per page in layout analysis before returning empty output. This
is not an error — Tesseract returns normally, just slowly and with no text.

**Prevention:**
- Before passing to Tesseract, check the image's mean pixel value. If it is below 80 (very
  dark), apply bitwise inversion (`cv2.bitwise_not`) before thresholding.
- Set a per-page timeout on the pytesseract call. pytesseract does not expose a native timeout,
  but you can wrap the subprocess call or use `multiprocessing` with a timeout to kill hung
  processes.
- PSM 7 (single line) and PSM 6 (uniform block) have significantly shorter layout analysis time
  than PSM 3 — use them for all field crops rather than whole-page OCR.

**Phase:** Preprocessing phase. Add the mean-pixel check to the image validation step.

---

### MINOR-3: openpyxl Number Format Strings Cause Excel to Treat Medical Codes as Numbers

**What goes wrong:**
openpyxl writes cell values as strings if you assign Python `str` values. But if a cell
contains a value that Excel recognises as a number (e.g., CPT code `99213`, NPI `1234567890`,
or a charge amount like `150.00`), Excel may auto-convert it to a number type on open,
stripping leading zeros if any exist. ZIP codes and NPI numbers that happen to start with 0
(`01234567890`) become `1234567890` silently.

**Prevention:**
- For all code fields (CPT, ICD-10, NPI, ZIP, revenue codes), set the cell's `number_format`
  to `"@"` (text) when writing: `cell.number_format = "@"`. This tells Excel to treat the
  cell as text permanently.
- Alternatively, write numeric-looking strings prefixed with a zero-width no-break space or
  use the `Quoting` pattern — but `number_format = "@"` is the canonical solution.

**Phase:** Export phase. Set once in the cell-writing utility function; applies globally.

---

### MINOR-4: ICD-10 Dot Removal Inconsistency

**What goes wrong:**
ICD-10 codes exist in two formats: with decimal (`F32.9`) and without (`F329`). CMS-1500 Box 21
printed forms typically omit the dot and use adjacent boxes to imply it. If your OCR reads the
dot from the separator line of the adjacent box as part of the code, you produce `F32.9` when
the billing system expects `F329`, or vice versa.

**Prevention:**
- Determine the expected format for the downstream system before building field extraction.
- Standardise all ICD-10 output to one format (without dot is the EDI/837 standard; with dot
  is the human-readable standard) at the normalisation layer, not ad-hoc per field.
- In Box 21, each ICD slot is a separate sub-region — crop each individually rather than
  cropping the entire box. This eliminates separator-line confusion.

**Phase:** Field extraction and normalisation phase.

---

### MINOR-5: Large Batch Processing Without Progress Feedback Appears Hung

**What goes wrong:**
Processing 50 two-page claims with preprocessing and OCR takes 3–10 minutes on a mid-range
laptop. Without any progress output, the desktop application appears frozen. Users kill it
and re-run, creating duplicate partial outputs or corrupted state.

**Prevention:**
- Emit progress at the page level (e.g., via a `tqdm` progress bar or a callback to a GUI
  progress indicator). Never process a batch silently.
- Write completed claims to output incrementally rather than holding everything in memory until
  the end. A crash at page 48 of 50 should not lose the first 47 claims' results.
- Log per-page processing time. If a page takes > 15 seconds it is almost certainly stuck in
  Tesseract layout analysis — this is your diagnostic signal.

**Phase:** Orchestration / UX phase.

---

## Phase-Specific Warnings Summary

| Phase | Topic | Likely Pitfall | Mitigation |
|-------|-------|---------------|------------|
| Phase 1 — Setup | Windows install | Tesseract/poppler PATH and missing tessdata | Scripted setup with startup self-test |
| Phase 1 — Setup | DPI constants | pdf2image defaults to 200 DPI | Explicit dpi=300, dimension assertion |
| Phase 2 — Preprocessing | Coordinate mapping | Scale and skew drift | Template-match anchor + scale factor before any crop |
| Phase 2 — Preprocessing | Grey band removal | Box 24 grey rows degrade accuracy | Adaptive threshold or HSV-based grey removal per crop |
| Phase 2 — Preprocessing | Dark/inverted scans | Tesseract hangs | Mean-pixel check + inversion before threshold |
| Phase 3 — Form detection | Clipped headers | Single-anchor detection fails silently | Multi-anchor detection with confidence score |
| Phase 3 — Form detection | Stamps on UB-04 | Overlays corrupt form-type anchor region | Template-match anchor avoidance + fallback anchors |
| Phase 4 — OCR config | Character errors | No PSM/whitelist set | Per-field PSM + whitelist + post-OCR regex validator |
| Phase 4 — OCR config | Stamp interference | Low-confidence OCR not flagged | Log word-confidence from image_to_data, threshold flag |
| Phase 5 — Grouping | Multi-page claims | Continuation detection from text alone | Claim number + header presence + page footer multi-signal |
| Phase 6 — Export | Excel formatting | Conditional formatting rules inflated per row | Range-level rules, ARGB colour format, direct fill preferred |
| Phase 6 — Export | Numeric code coercion | CPT/NPI/ZIP lose leading zeros in Excel | number_format = "@" on all code cells |
| Phase 6 — Export | ICD-10 dot format | Inconsistent decimal notation | Standardise to one format at normalisation layer |
| All phases | Silent failures | Errors produce empty strings, not exceptions | Field-level confidence logging + "unresolved" output column |

---

## Confidence Assessment

| Area | Confidence | Basis |
|------|------------|-------|
| Tesseract PSM/OEM/whitelist behaviour | HIGH | Tesseract official docs, well-documented in pytesseract |
| Adaptive threshold for grey backgrounds | HIGH | OpenCV official docs; standard technique |
| Coordinate drift and deskew | HIGH | Established computer vision pattern; OpenCV docs |
| Form detection multi-anchor strategy | MEDIUM | General CV pattern; specific CMS-1500/UB-04 anchors based on form knowledge |
| Multi-page grouping heuristics | MEDIUM | Pattern from general document processing; medical billing specifics from training knowledge |
| openpyxl conditional formatting limits | MEDIUM | openpyxl docs + known Excel OOXML limits; 64-rule limit is Excel format specific |
| openpyxl number_format "@" for text | HIGH | openpyxl official docs; standard Excel text-cell pattern |
| Windows Tesseract install path fragility | HIGH | Well-documented community pattern; UB-Mannheim is the canonical Windows build |
| Stamp/overlay corruption | MEDIUM | General OCR pattern; UB-04 stamp placement from medical billing knowledge |
| pdf2image DPI default | HIGH | pdf2image source and docs; default is 200 |

---

## Sources

- Tesseract documentation: https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html
- pytesseract README: https://github.com/madmaze/pytesseract
- UB-Mannheim Tesseract Windows builds: https://github.com/UB-Mannheim/tesseract/wiki
- Poppler Windows binaries: https://github.com/oschwartz10612/poppler-windows/releases
- pdf2image documentation: https://github.com/Belval/pdf2image
- OpenCV adaptive thresholding: https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html
- openpyxl documentation: https://openpyxl.readthedocs.io/en/stable/
- CMS-1500 form specification: https://www.nucc.org/index.php/code-sets-mainmenu-41/claim-form-mainmenu-42
- UB-04 form specification: https://www.nubc.org/ub-04

*Note: URLs listed for reference. Not directly fetched in this session due to tool restrictions —
confidence levels reflect training knowledge of these sources.*
