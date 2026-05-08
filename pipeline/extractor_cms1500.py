# pipeline/extractor_cms1500.py
"""CMS-1500 field extractor.

Public API:
    extract_cms1500(image, settings) -> list[FieldResult]
        Extracts billing-critical CMS-1500 fields from a preprocessed PIL Image.
        Returns 16 FieldResult entries:
          - patient_last_name, patient_first_name, patient_dob  (parsed from Box 2 wide scan)
          - total_charge                                         (Box 28)
          - date_of_service_sl1 .. date_of_service_sl6          (Box 24 date from)
          - cpt_code_sl1 .. cpt_code_sl6                        (Box 24 CPT/HCPCS)

        Args:
            image: Preprocessed PIL Image from preprocess_page() — mode 'RGB', 2550x3300 px.
            settings: Settings dict from load_settings(); must contain 'tesseract_cmd'.

        Returns:
            Flat list[FieldResult] with exactly 16 entries.
"""
import re
from typing import Optional

import pytesseract
from PIL import Image

from config.cms1500 import CMS1500_FIELDS, CMS1500_TABLE_FIELDS
from models.field_result import FieldResult

# X boundaries (in original image coordinates) that separate MM / DD / YY
# within the Box 24 date strip.  Dividers between sub-cells land at x≈107 and x≈165.
_DATE_DD_START = 107
_DATE_YY_START = 165


def _ocr_region(
    crop: Image.Image,
    psm: int,
    whitelist: Optional[str],
) -> tuple[str, float]:
    """Run Tesseract on a pre-cropped image region.

    Returns:
        (value, confidence) — value is stripped joined text;
        ("", -1.0) if no words found or exception raised.
    """
    config = f"--psm {psm}"
    if whitelist:
        config += f" -c tessedit_char_whitelist={whitelist}"
    try:
        d = pytesseract.image_to_data(
            crop, config=config, output_type=pytesseract.Output.DICT
        )
        words = [
            (t, int(c))
            for t, c in zip(d["text"], d["conf"])
            if int(c) >= 0 and t.strip()
        ]
        if words:
            value = " ".join(t for t, _ in words).strip()
            confidence = float(min(c for _, c in words))  # D-10: minimum across words
            return value, confidence
        return "", -1.0   # D-11: blank region sentinel
    except Exception:
        return "", -1.0   # D-11: error path sentinel


def _ocr_service_date(crop: Image.Image, box_left: int) -> tuple[str, float]:
    """OCR a Box 24 date strip and reconstruct 'MM/DD/YY' from per-word x positions.

    Box 24A 'From' date is printed in three separate sub-cells (MM, DD, YY) separated
    by vertical dividers.  Tesseract reads them as space-separated tokens.  This
    function assigns each digit token to its sub-cell by x position, then joins them.

    Returns ("", -1.0) if no digit tokens are found.
    """
    config = "--psm 6 -c tessedit_char_whitelist=0123456789"
    try:
        d = pytesseract.image_to_data(crop, config=config, output_type=pytesseract.Output.DICT)
        lefts = d.get("left", [0] * len(d["text"]))
    except Exception:
        return "", -1.0

    mm_parts: list[str] = []
    dd_parts: list[str] = []
    yy_parts: list[str] = []
    confs: list[int] = []
    for txt, conf, left in zip(d["text"], d["conf"], lefts):
        if int(conf) < 0 or not txt.strip().isdigit():
            continue
        orig_x = box_left + left  # convert crop-relative x to original image x
        confs.append(int(conf))
        if orig_x < _DATE_DD_START:
            mm_parts.append(txt.strip())
        elif orig_x < _DATE_YY_START:
            dd_parts.append(txt.strip())
        else:
            yy_parts.append(txt.strip())

    mm = "".join(mm_parts)
    dd = "".join(dd_parts)
    yy = "".join(yy_parts)

    # If x-position bucketing produced a valid 3-part date, use it
    if mm and dd and yy:
        return f"{mm}/{dd}/{yy}", float(min(confs))

    # Fallback: join all digit tokens in order and split by digit-count
    all_digits = mm + dd + yy
    if not all_digits:
        return "", -1.0
    n = len(all_digits)
    if n == 6:
        value = f"{all_digits[:2]}/{all_digits[2:4]}/{all_digits[4:]}"
    elif n == 4:
        value = f"{all_digits[:2]}/{all_digits[2:]}"
    else:
        # Return what we have — partial date
        parts = [p for p in [mm, dd, yy] if p]
        value = "/".join(parts) if len(parts) > 1 else all_digits
    return value, float(min(confs))


def _extract_from_name_band(ocr_text: str) -> tuple[str, str, str]:
    """Parse last_name, first_name, dob from a wide PSM-11 OCR scan of the name+DOB row.

    Takes the LAST 'Last, First' match to skip form-label text that appears before
    the real patient data (e.g. 'Last Name, First Name' printed on the form).
    DOB allows 2- or 4-digit years; implausible years (not 1900-2024) are rejected.
    """
    dob = ""
    dob_match = re.search(r'\b(\d{1,2}/\d{1,2}/(\d{2,4}))\b', ocr_text)
    if dob_match:
        date_str = dob_match.group(1)
        month_s, day_s, year_str = date_str.split("/")
        month, day, year = int(month_s), int(day_s), int(year_str)
        if len(year_str) == 2:
            year = year + 1900 if year >= 24 else year + 2000
        if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2024:
            dob = date_str

    name_matches = list(re.finditer(r'\b([A-Z][a-z]+),\s*([A-Z][a-z]+)\b', ocr_text))
    if name_matches:
        m = name_matches[-1]
        return m.group(1), m.group(2), dob
    return "", "", dob


def extract_cms1500(image: Image.Image, settings: dict) -> list[FieldResult]:
    """Extract billing-critical CMS-1500 fields from a preprocessed page image.

    Args:
        image: Preprocessed PIL Image (RGB, 2550x3300 px) from preprocess_page().
        settings: Dict from load_settings(); must contain 'tesseract_cmd' key.

    Returns:
        Flat list[FieldResult] with exactly 16 entries.
    """
    pytesseract.pytesseract.tesseract_cmd = settings["tesseract_cmd"]  # Windows required

    results: list[FieldResult] = []

    # Single-value fields — patient_name expands to three results via regex parsing
    for fd in CMS1500_FIELDS:
        crop = image.crop(fd.box)
        value, conf = _ocr_region(crop, fd.psm, fd.whitelist)
        if fd.name == "patient_name":
            last, first, dob = _extract_from_name_band(value)
            results.append(FieldResult(field_name="patient_last_name",  value=last,  confidence=conf))
            results.append(FieldResult(field_name="patient_first_name", value=first, confidence=conf))
            results.append(FieldResult(field_name="patient_dob",        value=dob,   confidence=conf))
        else:
            results.append(FieldResult(field_name=fd.name, value=value, confidence=conf))

    # Table fields: date_of_service × 6 + cpt_code × 6 = 12 entries
    for tfd in CMS1500_TABLE_FIELDS:
        for i, box in enumerate(tfd.row_boxes):
            field_name = f"{tfd.name}_sl{i + 1}"
            crop = image.crop(box)
            if tfd.name == "date_of_service":
                value, conf = _ocr_service_date(crop, box[0])
            else:
                value, conf = _ocr_region(crop, tfd.psm, tfd.whitelist)
            results.append(FieldResult(field_name=field_name, value=value, confidence=conf))

    return results  # always 16 entries: 4 single + 12 table
