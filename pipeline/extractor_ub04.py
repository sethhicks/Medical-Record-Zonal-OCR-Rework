# pipeline/extractor_ub04.py
"""UB-04 field extractor.

Public API:
    extract_ub04(image, settings) -> list[FieldResult]
        Extracts all billing-critical UB-04 fields from a preprocessed PIL Image.
        Returns 178 FieldResult entries: 24 single-value fields + 154 revenue-line cells
        (7 sub-fields × 22 revenue line rows).

        Args:
            image: Preprocessed PIL Image from preprocess_page() — mode 'RGB', 2550x3300 px.
            settings: Settings dict from load_settings(); must contain 'tesseract_cmd'.

        Returns:
            Flat list[FieldResult] — always 178 entries, blank rows have value='' confidence=-1.0.
"""
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
            if int(c) > 0 and t.strip()
        ]
        if words:
            value = " ".join(t for t, _ in words).strip()
            confidence = float(min(c for _, c in words))  # D-10: minimum across words
            return value, confidence
        return "", -1.0   # D-11: blank region sentinel
    except Exception:
        return "", -1.0   # D-11: error path sentinel


def extract_ub04(image: Image.Image, settings: dict) -> list[FieldResult]:
    """Extract all UB-04 fields from a preprocessed page image.

    Args:
        image: Preprocessed PIL Image (RGB, 2550x3300 px) from preprocess_page().
        settings: Dict from load_settings(); must contain 'tesseract_cmd' key.

    Returns:
        Flat list[FieldResult] with exactly 178 entries.
        Single-field names: fd.name from UB04_FIELDS.
        Revenue-line names: "{tfd.name}_rl{i+1}" for i in range(len(tfd.row_boxes)).
        Example: "ub04_rl_rev_code_rl1" ... "ub04_rl_rev_code_rl22".
    """
    pytesseract.pytesseract.tesseract_cmd = settings["tesseract_cmd"]  # Windows required

    results: list[FieldResult] = []

    # 24 single-value fields
    for fd in UB04_FIELDS:
        crop = image.crop(fd.box)
        value, conf = _ocr_region(crop, fd.psm, fd.whitelist)
        results.append(FieldResult(field_name=fd.name, value=value, confidence=conf))

    # 7 TableFieldDef × 22 rows = 154 revenue-line cells (D-07: always 22 rows, even when blank)
    for tfd in UB04_TABLE_FIELDS:
        for i, box in enumerate(tfd.row_boxes):
            field_name = f"{tfd.name}_rl{i + 1}"  # D-07: _rl1 through _rl22
            crop = image.crop(box)
            value, conf = _ocr_region(crop, tfd.psm, tfd.whitelist)
            results.append(FieldResult(field_name=field_name, value=value, confidence=conf))

    return results  # always 178 entries: 24 single + 154 revenue-line cells
