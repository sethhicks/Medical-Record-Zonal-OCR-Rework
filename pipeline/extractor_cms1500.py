# pipeline/extractor_cms1500.py
"""CMS-1500 field extractor.

Public API:
    extract_cms1500(image, settings) -> list[FieldResult]
        Extracts billing-critical CMS-1500 fields from a preprocessed PIL Image.
        Returns 3 FieldResult entries:
          - patient_name        (Box 2 wide scan, "Last, First" combined)
          - total_charge        (Box 28)
          - date_of_service_sl1 (Box 24 first service line date)

        Args:
            image: Preprocessed PIL Image from preprocess_page() — mode 'RGB', 2550x3300 px.
            settings: Settings dict from load_settings(); must contain 'tesseract_cmd'.

        Returns:
            Flat list[FieldResult] with exactly 3 entries.
"""
import re
from typing import Optional

import pytesseract
from PIL import Image

from config.cms1500 import CMS1500_FIELDS, CMS1500_TABLE_FIELDS
from models.field_result import FieldResult

# Sub-cell widths (in pixels) relative to the date box's LEFT edge.
# MM cell is _DATE_MM_WIDTH px wide; DD cell is _DATE_DD_WIDTH px wide; YY takes the rest.
# Calibrated via OCR sweep on real test.pdf pages (p0/p1/p19) against zone (85,2200,340,2300).
_DATE_MM_WIDTH = 75   # MM: left → left+75
_DATE_DD_WIDTH = 60   # DD: left+75 → left+135


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


def _ocr_service_date(image: Image.Image, box: tuple[int, int, int, int]) -> tuple[str, float]:
    """OCR a Box 24 date by reading MM, DD, YY sub-cells as three separate crops.

    Box 24A 'From' date is printed in three sub-cells separated by vertical dividers at
    x≈107 and x≈165 (original image coordinates).  Reading each sub-cell independently
    with PSM 8 avoids Tesseract merging adjacent cells into a single token.

    Returns ("", -1.0) if all sub-cells are blank.
    """
    left, top, right, bottom = box
    mm_end = left + _DATE_MM_WIDTH
    dd_end = mm_end + _DATE_DD_WIDTH
    sub_boxes = [
        (left,   top, mm_end, bottom),  # MM
        (mm_end, top, dd_end, bottom),  # DD
        (dd_end, top, right,  bottom),  # YY
    ]
    parts: list[str] = []
    confs: list[float] = []
    for sub_box in sub_boxes:
        sub_crop = image.crop(sub_box)
        val, conf = _ocr_region(sub_crop, psm=8, whitelist="0123456789")
        parts.append(val.strip())
        if conf >= 0:
            confs.append(conf)

    mm, dd, yy = parts

    # Row-number column bleeds past x=55 on some scans, prepending an extra '1' to MM.
    # Strip it when the resulting value would be an impossible month.
    if mm and len(mm) > 2 and int(mm) > 12:
        mm = mm[1:]  # "112" → "12"

    if mm and dd and yy:
        return f"{mm}/{dd}/{yy}", min(confs) if confs else -1.0

    # Partial fallback: return whatever sub-cells we got
    non_empty = [p for p in [mm, dd, yy] if p]
    if non_empty:
        return "/".join(non_empty), min(confs) if confs else -1.0
    return "", -1.0


def _extract_from_name_band(ocr_text: str) -> str:
    """Extract patient name from the OCR scan of the name row.

    Tries three strategies in order, taking the LAST match to skip form-label text:
      1. 'Last, First' with comma (clean read)
      2. 'Last. First' with period (OCR misreads comma as period)
      3. Last capitalised word on the last non-empty line (fallback for no-punctuation reads)
    """
    # Strategy 1: comma separator
    m = list(re.finditer(r'\b([A-Z][a-z]+),\s*([A-Z][a-z]+)\b', ocr_text))
    if m:
        g = m[-1]
        return f"{g.group(1)}, {g.group(2)}"
    # Strategy 2: period OCR noise instead of comma
    m = list(re.finditer(r'\b([A-Z][a-z]+)\.\s*([A-Z][a-z]+)\b', ocr_text))
    if m:
        g = m[-1]
        return f"{g.group(1)}, {g.group(2)}"
    # Strategy 3: last line with two capitalised words (no punctuation between them)
    for line in reversed(ocr_text.splitlines()):
        line = line.strip()
        words = re.findall(r'\b[A-Z][a-z]+\b', line)
        if len(words) >= 2:
            return f"{words[0]}, {words[1]}"
    return ""


def extract_cms1500(image: Image.Image, settings: dict) -> list[FieldResult]:
    """Extract billing-critical CMS-1500 fields from a preprocessed page image.

    Args:
        image: Preprocessed PIL Image (RGB, 2550x3300 px) from preprocess_page().
        settings: Dict from load_settings(); must contain 'tesseract_cmd' key.

    Returns:
        Flat list[FieldResult] with exactly 3 entries.
    """
    pytesseract.pytesseract.tesseract_cmd = settings["tesseract_cmd"]  # Windows required

    results: list[FieldResult] = []

    for fd in CMS1500_FIELDS:
        crop = image.crop(fd.box)
        value, conf = _ocr_region(crop, fd.psm, fd.whitelist)
        if fd.name == "patient_name":
            name = _extract_from_name_band(value)
            results.append(FieldResult(field_name="patient_name", value=name, confidence=conf))
        elif fd.name == "total_charge":
            # Take only the first numeric token — adjacent column bleed adds trailing noise
            clean = value.split()[0] if value else ""
            results.append(FieldResult(field_name=fd.name, value=clean, confidence=conf))
        else:
            results.append(FieldResult(field_name=fd.name, value=value, confidence=conf))

    for tfd in CMS1500_TABLE_FIELDS:
        for i, box in enumerate(tfd.row_boxes):
            field_name = f"{tfd.name}_sl{i + 1}"
            if tfd.name == "date_of_service":
                value, conf = _ocr_service_date(image, box)
            else:
                crop = image.crop(box)
                value, conf = _ocr_region(crop, tfd.psm, tfd.whitelist)
            results.append(FieldResult(field_name=field_name, value=value, confidence=conf))

    return results  # 3 entries: patient_name, total_charge, date_of_service_sl1
