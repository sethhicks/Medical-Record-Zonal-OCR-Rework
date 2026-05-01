---
status: partial
phase: 02-image-pipeline-coordinate-calibration
source: [02-VERIFICATION.md]
started: 2026-05-01
updated: 2026-05-01
---

## Current Test

Awaiting human visual verification of calibration overlays.

## Tests

### 1. CMS-1500 field coordinate alignment
Run `python pipeline/calibrate.py --page 0 --pdf test.pdf` and open the resulting `calibration_overlay_p0.png`.
expected: 29 green rectangles land on the correct CMS-1500 form boxes (claim ID, Box 1–33 fields). Labels readable above each rectangle.
result: [pending]

### 2. Box 24 table region alignment
On the same CMS-1500 overlay, inspect the Box 24 service line area.
expected: 60 orange rectangles (10 sub-fields × 6 service line rows) cover the correct columns for Date From, Date To, POS, EMG, CPT, Modifier, Dx Pointer, Charges, Units, NPI.
result: [pending]

### 3. UB-04 coordinate alignment
Identify a UB-04 page in test.pdf (approximately pages 27–29). Run `python pipeline/calibrate.py --page [UB04_PAGE] --pdf test.pdf --form ub04`.
expected: 24 green FieldDef rectangles + 154 orange TableFieldDef row boxes align with the actual UB-04 form layout. Revenue code column, description, HCPCS, dates, units, charges columns are all covered.
result: [pending]

### 4. Threshold image quality
Run `python pipeline/calibrate.py --page 0 --pdf test.pdf` with debug mode: temporarily edit `preprocess_page` call to pass `debug=True`, or call directly:
```
python -c "
from pipeline import convert_page, preprocess_page
from config_loader import load_settings
img = convert_page('test.pdf', 0)
preprocess_page(img, load_settings(), debug=True)
print('Done — check debug_04_threshold.png')
"
```
expected: `debug_04_threshold.png` shows clean black-and-white with legible text in the Box 24 service line area and no grey banding.
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps
