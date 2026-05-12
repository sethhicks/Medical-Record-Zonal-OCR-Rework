# pipeline/extractor_ub04.py
"""UB-04 field extractor.

Public API:
    extract_ub04(image, settings) -> list[FieldResult]
        Extracts billing-critical UB-04 fields from a preprocessed PIL Image.
        Returns 25 FieldResult entries:
          - patient_last_name, patient_first_name  (split from Box 8 wide scan)
          - total_charge                           (EST. Amount Due row)
          - date_of_service_rl1 .. date_of_service_rl22  (revenue line service dates)

        Args:
            image: Preprocessed PIL Image from preprocess_page() — mode 'RGB', 2550x3300 px.
            settings: Settings dict from load_settings(); must contain 'tesseract_cmd'.

        Returns:
            Flat list[FieldResult] — always 25 entries, blank rows have value='' confidence=-1.0.
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

    # Single-value fields — patient_name expands to two results via regex parsing
    for fd in UB04_FIELDS:
        crop = image.crop(fd.box)
        value, conf = _ocr_region(crop, fd.psm, fd.whitelist)
        if fd.name == "patient_name":
            last, first = _extract_name_from_band(value)
            results.append(FieldResult(field_name="patient_last_name",  value=last,  confidence=conf))
            results.append(FieldResult(field_name="patient_first_name", value=first, confidence=conf))
        else:
            results.append(FieldResult(field_name=fd.name, value=value, confidence=conf))

    # Table fields: date_of_service × 22 = 22 entries
    for tfd in UB04_TABLE_FIELDS:
        for i, box in enumerate(tfd.row_boxes):
            field_name = f"{tfd.name}_rl{i + 1}"
            crop = image.crop(box)
            value, conf = _ocr_region(crop, tfd.psm, tfd.whitelist)
            results.append(FieldResult(field_name=field_name, value=value, confidence=conf))

    return results  # always 25 entries: 3 single + 22 table
