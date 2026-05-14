# pipeline/extractor_ub04.py
"""UB-04 field extractor.

Public API:
    extract_ub04(image, settings) -> list[FieldResult]
        Extracts billing-critical UB-04 fields from a preprocessed PIL Image.
        Returns 3 FieldResult entries:
          - patient_name       (Box 8 wide scan, "Last, First" combined)
          - total_charge       (EST. Amount Due row)
          - date_of_service_rl1 (first revenue line service date)

        Args:
            image: Preprocessed PIL Image from preprocess_page() — mode 'RGB', 2550x3300 px.
            settings: Settings dict from load_settings(); must contain 'tesseract_cmd'.

        Returns:
            Flat list[FieldResult] — always 3 entries, blank fields have value='' confidence=-1.0.
"""
import re
from typing import Optional

import cv2
import numpy as np
import pytesseract
from PIL import Image

from config.ub04 import UB04_FIELDS, UB04_TABLE_FIELDS
from models.field_result import FieldResult


def _prepare_numeric_crop(crop: Image.Image, blur_k: int = 9) -> Image.Image:
    """Upscale, blur, and binarize a numeric crop for Tesseract digit recognition.

    Gaussian blur before Otsu merges halftone/noise dots into uniform grey so
    Otsu finds a clean split. Without blur, Otsu misclassifies halftone as text.
    blur_k=9 for charges, blur_k=5 for dates.
    """
    gray = np.array(crop.convert("L"))
    h, w = gray.shape
    upscaled = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    blurred = cv2.GaussianBlur(upscaled, (blur_k, blur_k), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(binary).convert("RGB")


def _ocr_region(
    crop: Image.Image,
    psm: int,
    whitelist: Optional[str],
    oem: int = 3,
    dpi: int = 300,
) -> tuple[str, float]:
    """Run Tesseract on a pre-cropped image region.

    Returns:
        (value, confidence) — value is stripped joined text;
        ("", -1.0) if no words found or exception raised.
    """
    config = f"--oem {oem} --psm {psm} --dpi {dpi}"
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


def _ocr_date_region(crop: Image.Image, psm: int) -> tuple[str, float]:
    """OCR a date crop using LSTM-only engine (OEM 1) with digits-only whitelist.

    Tries raw first (no preprocessing), then thr=100, then blur5+Otsu (original).
    Raw is better for clean and medium halftone pages; blur+Otsu handles heavy noise.
    """
    gray = np.array(crop.convert("L"))
    h, w = gray.shape
    base_config = f"--oem 1 --psm {psm} -c tessedit_char_whitelist=0123456789"

    def _run(arr, dpi):
        img = Image.fromarray(arr).convert("RGB")
        try:
            d = pytesseract.image_to_data(
                img, config=f"{base_config} --dpi {dpi}",
                output_type=pytesseract.Output.DICT,
            )
            words = [
                (t, int(c))
                for t, c in zip(d["text"], d["conf"])
                if int(c) >= 0 and t.strip()
            ]
            if words:
                return " ".join(t for t, _ in words).strip(), float(min(c for _, c in words))
        except Exception:
            pass
        return "", -1.0

    # S1: raw, 1×
    val, conf = _run(gray, 300)
    if val:
        return val, conf

    # S2: fixed thr=100, 1×
    _, bw = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
    val, conf = _run(bw, 300)
    if val:
        return val, conf

    # S3: blur5+Otsu, 2× (original)
    up2 = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    bl5 = cv2.GaussianBlur(up2, (5, 5), 0)
    _, bw = cv2.threshold(bl5, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return _run(bw, 600)


def _extract_name_from_band(ocr_text: str) -> str:
    """Extract patient name from the OCR scan of the name row.

    Tries three strategies in order, taking the LAST match to skip form-label text:
      1. 'Last, First' with comma (clean read)
      2. 'Last. First' with period (OCR misreads comma as period)
      3. Last capitalised word pair on the last non-empty line (no-punctuation fallback)
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
    # Strategy 3: last line with two capitalised words
    for line in reversed(ocr_text.splitlines()):
        line = line.strip()
        words = re.findall(r'\b[A-Z][a-z]+\b', line)
        if len(words) >= 2:
            return f"{words[0]}, {words[1]}"
    return ""


def _ocr_patient_name_ub04(image: Image.Image, primary_box: tuple) -> tuple[str, float]:
    """Two-pass name extraction to handle scan jitter shifting the name row up ~40px.

    Some scans place the patient name row ~40px above the calibrated primary zone.
    Try the primary zone first to preserve accuracy on the majority of pages;
    fall back to a zone shifted 40px up if the primary returns no recognisable name.
    """
    val, conf = _ocr_region(image.crop(primary_box), psm=6, whitelist=None)
    name = _extract_name_from_band(val)
    if name:
        return name, conf
    left, top, right, bottom = primary_box
    fallback_box = (left, top - 40, right, bottom)  # shift top up; keep bottom to preserve height
    val2, conf2 = _ocr_region(image.crop(fallback_box), psm=6, whitelist=None)
    return _extract_name_from_band(val2), conf2


def _format_ub04_date(raw: str) -> str:
    """Format a raw OCR date string to MM/DD/YY.

    UB-04 SERV DATE prints as MMDDYY (no separators). OCR may return a 7-digit
    string when the row-number column bleeds in; the leading '1' is stripped first.
    Returns '' if no valid 6-digit MM/DD/YY can be extracted.
    """
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 7 and digits[0] == "1":
        candidates = [digits[1:], digits[:6]]
    elif len(digits) >= 6:
        candidates = [digits[:6]]
    else:
        return ""
    for s in candidates:
        mm, dd = int(s[:2]), int(s[2:4])
        if 1 <= mm <= 12 and 1 <= dd <= 31:
            return f"{s[:2]}/{s[2:4]}/{s[4:]}"
    return ""


def _ocr_total_charge_ub04(image: Image.Image, primary_box: tuple) -> tuple[str, float]:
    """Two-pass charge extraction to handle 30px vertical scan jitter.

    Scan jitter shifts the Line 47 Total Charges row up to 30px across pages.
    Try the primary zone first; if empty, shift down 30px and retry.
    Requires 3–6 digit characters to accept a read as a real amount.
    """
    left, top, right, bottom = primary_box
    for dy in (0, -30, 30, -60, 60):
        box = (left, top + dy, right, bottom + dy)
        raw_crop = image.crop(box)

        # Pass 1: raw, PSM 8 — accurate for clean-background scans.
        val, conf = _ocr_region(raw_crop, psm=8, whitelist="0123456789. ", oem=1, dpi=300)
        if not val:
            # Pass 2: blur(k=9)+Otsu — handles halftone cell backgrounds.
            val, conf = _ocr_region(
                _prepare_numeric_crop(raw_crop, blur_k=9),
                psm=6, whitelist="0123456789. ", oem=1, dpi=600,
            )
        if val:
            for token in re.split(r"\s+", val):
                token = re.sub(r"^\D+", "", token)
                token = re.sub(r"\D+$", "", token)
                digit_count = len(re.sub(r"\D", "", token))
                if 3 <= digit_count <= 7:
                    return token, conf
    return "", -1.0


def extract_ub04(image: Image.Image, settings: dict) -> list[FieldResult]:
    """Extract billing-critical UB-04 fields from a preprocessed page image.

    Args:
        image: Preprocessed PIL Image (RGB, 2550x3300 px) from preprocess_page().
        settings: Dict from load_settings(); must contain 'tesseract_cmd' key.

    Returns:
        Flat list[FieldResult] with exactly 3 entries.
    """
    pytesseract.pytesseract.tesseract_cmd = settings["tesseract_cmd"]  # Windows required

    results: list[FieldResult] = []

    for fd in UB04_FIELDS:
        if fd.name == "patient_name":
            name, conf = _ocr_patient_name_ub04(image, fd.box)
            results.append(FieldResult(field_name="patient_name", value=name, confidence=conf))
        elif fd.name == "total_charge":
            value, conf = _ocr_total_charge_ub04(image, fd.box)
            results.append(FieldResult(field_name=fd.name, value=value, confidence=conf))
        else:
            crop = image.crop(fd.box)
            value, conf = _ocr_region(crop, fd.psm, fd.whitelist)
            results.append(FieldResult(field_name=fd.name, value=value, confidence=conf))

    # Box 6 (Statement Covers Period FROM) — fallback when Box 12 (Admission Date) is blank.
    # Box 12 is only filled for inpatient claims; outpatient claims leave it empty.
    # Box 6 FROM is filled for all UB-04 claim types.
    _BOX6_FROM = (1820, 220, 2100, 275)

    for tfd in UB04_TABLE_FIELDS:
        for i, box in enumerate(tfd.row_boxes):
            field_name = f"{tfd.name}_rl{i + 1}"
            if tfd.name == "date_of_service":
                value, conf = _ocr_date_region(image.crop(box), psm=tfd.psm)
                value = _format_ub04_date(value)
                if not value:
                    # Box 12 blank — try Box 6 Statement Covers Period FROM date
                    raw6, conf = _ocr_date_region(image.crop(_BOX6_FROM), psm=tfd.psm)
                    value = _format_ub04_date(raw6)
            else:
                crop = image.crop(box)
                value, conf = _ocr_region(crop, tfd.psm, tfd.whitelist)
            results.append(FieldResult(field_name=field_name, value=value, confidence=conf))

    return results  # 3 entries: patient_name, total_charge, date_of_service_rl1
