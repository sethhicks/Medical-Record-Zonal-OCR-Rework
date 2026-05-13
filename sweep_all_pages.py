"""Full sweep: run all pages of test.pdf through the extractor and report results.

Usage:
    python sweep_all_pages.py [--pages N]   # default: all pages

Output: compact table with page, form type, and the 3 extracted fields.
Summary: hit counts (non-empty values) vs total.
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

from pdf2image import convert_from_path
from config_loader import load_settings
from pipeline.preprocessor import preprocess_page
from pipeline.detector import detect_form_type
from pipeline import extract_cms1500
from pipeline.extractor_ub04 import extract_ub04

PDF = str(_ROOT / "test.pdf")
settings = load_settings()

# Determine page count
pages_arg = None
for i, a in enumerate(sys.argv[1:], 1):
    if a == "--pages" and i < len(sys.argv):
        pages_arg = int(sys.argv[i + 1])

print(f"Converting PDF…")
raw_pages = convert_from_path(
    PDF,
    dpi=300,
    poppler_path=settings.get("poppler_path"),
)
total_pages = pages_arg if pages_arg else len(raw_pages)
print(f"Pages: {total_pages}\n")

# Track hits and totals
hits = 0
total_fields = 0

HDR = f"{'PG':>3}  {'TYPE':<7}  {'PATIENT NAME':<22}  {'CHARGE':<12}  {'DATE SL1':<12}"
SEP = "-" * len(HDR)
print(HDR)
print(SEP)

for pg_idx in range(total_pages):
    pg_num = pg_idx + 1
    raw_orig = raw_pages[pg_idx]
    # Normalise to 2550x3300 so detector and preprocessor receive the expected size
    if raw_orig.size != (2550, 3300):
        from PIL import Image as _Image
        raw = raw_orig.resize((2550, 3300), _Image.LANCZOS)
    else:
        raw = raw_orig
    form_type = detect_form_type(raw)   # detector needs raw image, not preprocessed
    img = preprocess_page(raw, settings)

    if form_type == "CMS-1500":
        results = extract_cms1500(img, settings)
    elif form_type == "UB-04":
        results = extract_ub04(img, settings)
    else:
        print(f"{pg_num:>3}  {'UNKNOWN':<7}  (skipped)")
        continue

    by_name = {r.field_name: r for r in results}

    # Normalise field names across form types
    name_r   = by_name.get("patient_name") or by_name.get("patient_name_ub04")
    charge_r = by_name.get("total_charge") or by_name.get("total_charges_ub04")
    date_r   = by_name.get("date_of_service_sl1") or by_name.get("date_of_service_rl1")

    name_v   = name_r.value   if name_r   else ""
    charge_v = charge_r.value if charge_r else ""
    date_v   = date_r.value   if date_r   else ""

    name_c   = name_r.confidence   if name_r   else -1
    charge_c = charge_r.confidence if charge_r else -1
    date_c   = date_r.confidence   if date_r   else -1

    row_hits = sum(1 for v in (name_v, charge_v, date_v) if v)
    hits += row_hits
    total_fields += 3

    # Annotate blanks
    def fmt(v, c):
        if v:
            return f"{v[:20]:<20} ({c:3.0f})"
        return f"{'':20} (---)"

    print(
        f"{pg_num:>3}  {form_type:<7}  "
        f"{name_v[:22]:<22}  "
        f"{charge_v[:12]:<12}  "
        f"{date_v[:12]:<12}"
    )

print(SEP)
print(f"\nHits: {hits}/{total_fields}  ({100*hits/total_fields:.1f}%)")
print(f"Empty fields: {total_fields - hits}")
