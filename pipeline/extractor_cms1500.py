# pipeline/extractor_cms1500.py
"""CMS-1500 field extractor.

Public API:
    extract_cms1500(image, settings) -> list[FieldResult]
        Extracts all billing-critical CMS-1500 fields from a preprocessed PIL Image.
        Returns 89 FieldResult entries: 29 single-value fields + 60 Box 24 table cells
        (10 sub-fields × 6 service line rows).

        Args:
            image: Preprocessed PIL Image from preprocess_page() — mode 'RGB', 2550x3300 px.
            settings: Settings dict from load_settings(); must contain 'tesseract_cmd'.

        Returns:
            Flat list[FieldResult] — always 89 entries, blank rows have value='' confidence=-1.0.
"""
from typing import Optional

import pytesseract
from PIL import Image

from config.cms1500 import CMS1500_FIELDS, CMS1500_TABLE_FIELDS
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


def extract_cms1500(image: Image.Image, settings: dict) -> list[FieldResult]:
    """Extract all CMS-1500 fields from a preprocessed page image.

    Args:
        image: Preprocessed PIL Image (RGB, 2550x3300 px) from preprocess_page().
        settings: Dict from load_settings(); must contain 'tesseract_cmd' key.

    Returns:
        Flat list[FieldResult] with exactly 89 entries.
        Single-field names: fd.name from CMS1500_FIELDS.
        Table-cell names: "{tfd.name}_sl{i+1}" for i in range(len(tfd.row_boxes)).
    """
    pytesseract.pytesseract.tesseract_cmd = settings["tesseract_cmd"]  # Windows required

    results: list[FieldResult] = []

    # 29 single-value fields
    for fd in CMS1500_FIELDS:
        crop = image.crop(fd.box)
        value, conf = _ocr_region(crop, fd.psm, fd.whitelist)
        results.append(FieldResult(field_name=fd.name, value=value, confidence=conf))

    # 10 TableFieldDef × 6 rows = 60 table cells (D-06: always 6 rows, even when blank)
    for tfd in CMS1500_TABLE_FIELDS:
        for i, box in enumerate(tfd.row_boxes):
            field_name = f"{tfd.name}_sl{i + 1}"  # D-06: _sl1 through _sl6
            crop = image.crop(box)
            value, conf = _ocr_region(crop, tfd.psm, tfd.whitelist)
            results.append(FieldResult(field_name=field_name, value=value, confidence=conf))

    return results  # always 89 entries: 29 single + 60 table
