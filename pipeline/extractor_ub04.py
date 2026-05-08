# pipeline/extractor_ub04.py
"""UB-04 field extractor.

Public API:
    extract_ub04(image, settings) -> list[FieldResult]
        Extracts billing-critical UB-04 fields from a preprocessed PIL Image.
        Returns 26 FieldResult entries:
          - patient_last_name, patient_first_name  (split from Box 8 wide scan)
          - patient_dob                            (Box 10, date extracted via regex)
          - total_charge                           (EST. Amount Due row)
          - date_of_service_rl1 .. date_of_service_rl22  (revenue line service dates)

        Args:
            image: Preprocessed PIL Image from preprocess_page() — mode 'RGB', 2550x3300 px.
            settings: Settings dict from load_settings(); must contain 'tesseract_cmd'.

        Returns:
            Flat list[FieldResult] — always 26 entries, blank rows have value='' confidence=-1.0.
"""
import re
from typing import Optional

import pytesseract
from PIL import Image

from config.ub04 import UB04_FIELDS, UB04_TABLE_FIELDS
from models.field_result import FieldResult


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


def _extract_name_from_band(ocr_text: str) -> tuple[str, str]:
    """Extract (last_name, first_name) from a wide PSM-11 OCR scan of the name row.

    Strategy 1: take the LAST strict 'Last, First' regex match to skip form labels.
    Strategy 2 (fallback): comma-split — first word before comma is last name, first
      word after comma is first name.  Handles 'Furcotte, S hown' where the space
      inside the first name breaks the strict regex.
    """
    matches = list(re.finditer(r'\b([A-Z][a-z]+),\s*([A-Z][a-z]+)\b', ocr_text))
    if matches:
        m = matches[-1]
        return m.group(1), m.group(2)
    # Fallback: find the last capitalized-word,word pair separated by comma
    comma_matches = list(re.finditer(r'\b([A-Z][a-z]+),\s*([A-Z]\w*)', ocr_text))
    if comma_matches:
        m = comma_matches[-1]
        return m.group(1), m.group(2)
    return "", ""


def _extract_dob(ocr_text: str) -> str:
    """Extract a date string from noisy OCR text using a regex.

    Matches M/D/YY and M/D/YYYY patterns.  Validates month (1-12), day (1-31),
    and year (1900-2024) to reject false positives like '0/10/10'.
    """
    m = re.search(r'\b(\d{1,2}/\d{1,2}/(\d{2,4}))\b', ocr_text)
    if not m:
        return ""
    date_str = m.group(1)
    month_s, day_s, year_str = date_str.split("/")
    month, day, year = int(month_s), int(day_s), int(year_str)
    if len(year_str) == 2:
        year = year + 1900 if year >= 24 else year + 2000
    if not (1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2024):
        return ""
    return date_str


def extract_ub04(image: Image.Image, settings: dict) -> list[FieldResult]:
    """Extract billing-critical UB-04 fields from a preprocessed page image.

    Args:
        image: Preprocessed PIL Image (RGB, 2550x3300 px) from preprocess_page().
        settings: Dict from load_settings(); must contain 'tesseract_cmd' key.

    Returns:
        Flat list[FieldResult] with exactly 26 entries.
    """
    pytesseract.pytesseract.tesseract_cmd = settings["tesseract_cmd"]  # Windows required

    results: list[FieldResult] = []

    # Single-value fields
    for fd in UB04_FIELDS:
        crop = image.crop(fd.box)
        value, conf = _ocr_region(crop, fd.psm, fd.whitelist)
        if fd.name == "patient_name":
            last, first = _extract_name_from_band(value)
            results.append(FieldResult(field_name="patient_last_name",  value=last,  confidence=conf))
            results.append(FieldResult(field_name="patient_first_name", value=first, confidence=conf))
        elif fd.name == "patient_dob":
            dob = _extract_dob(value)
            if not dob:
                # Retry shifted 15px down — compensates for ±15px scan jitter between pages
                shifted = (fd.box[0], fd.box[1] + 15, fd.box[2], fd.box[3] + 15)
                v2, c2 = _ocr_region(image.crop(shifted), fd.psm, fd.whitelist)
                dob = _extract_dob(v2)
                if dob:
                    conf = c2
            results.append(FieldResult(field_name="patient_dob", value=dob, confidence=conf))
        else:
            results.append(FieldResult(field_name=fd.name, value=value, confidence=conf))

    # Table fields: date_of_service × 22 = 22 entries
    for tfd in UB04_TABLE_FIELDS:
        for i, box in enumerate(tfd.row_boxes):
            field_name = f"{tfd.name}_rl{i + 1}"
            crop = image.crop(box)
            value, conf = _ocr_region(crop, tfd.psm, tfd.whitelist)
            results.append(FieldResult(field_name=field_name, value=value, confidence=conf))

    return results  # always 26 entries: 4 single + 22 table
