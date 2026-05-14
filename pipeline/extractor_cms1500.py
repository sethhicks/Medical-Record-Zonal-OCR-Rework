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

import cv2
import numpy as np
import pytesseract
from PIL import Image

from config.cms1500 import CMS1500_FIELDS, CMS1500_TABLE_FIELDS
from models.field_result import FieldResult

# Sub-cell widths (in pixels) relative to the date box's LEFT edge.
# MM cell is _DATE_MM_WIDTH px wide; DD cell is _DATE_DD_WIDTH px wide; YY takes the rest.
# Calibrated via OCR sweep on real test.pdf pages (p0/p1/p19) against zone (85,2200,340,2300).
_DATE_MM_WIDTH = 75   # MM: left → left+75
_DATE_DD_WIDTH = 60   # DD: left+75 → left+135


def _prepare_numeric_crop(crop: Image.Image, blur_k: int = 9) -> Image.Image:
    """Upscale, blur, and binarize a numeric crop for Tesseract digit recognition.

    Gaussian blur before Otsu is critical: it merges halftone/noise dots into a
    uniform grey background so Otsu finds a clean text-vs-background split.
    Without blur, Otsu misclassifies halftone dots as text and destroys reads.
    blur_k=9 for charges (coarser halftone), blur_k=5 for dates (finer cells).
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


def _ocr_service_date(image: Image.Image, box: tuple[int, int, int, int]) -> tuple[str, float]:
    """OCR a Box 24 date from the full zone, falling back to per-sub-cell reads.

    Strategy 1: try 8 preprocessing/PSM combos on the full MM/DD/YY zone in order,
    taking the first result where mm (1-12) and dd (1-31) are both valid.
    The order is: blur5+Otsu (original), thr=100, raw, 2× thr=128,
    3× blur3+Otsu PSM 6, 3× thr=128, 5× thr=100, no-whitelist PSM 6 sliding-window.

    Strategy 2 (fallback): read MM, DD, YY as three separate crops with PSM 8.

    Returns ("", -1.0) if no digits can be extracted.
    """
    left, top, right, bottom = box

    def _s1_try(crop):
        """Try multiple preprocessing strategies; return (date, conf, best_digits)."""
        gray = np.array(crop.convert("L"))
        h, w = gray.shape
        best_digits = ""

        def _ocr_d(arr, psm, dpi):
            img = Image.fromarray(arr).convert("RGB")
            r = pytesseract.image_to_string(
                img,
                config=f"--oem 1 --dpi {dpi} --psm {psm} -c tessedit_char_whitelist=0123456789",
            ).strip()
            return re.sub(r"\D", "", r)

        def _check(d):
            nonlocal best_digits
            if len(d) > len(best_digits):
                best_digits = d
            cands = (
                [d[1:7], d[:6]] if (len(d) == 7 and d[0] == "1")
                else ([d[:6]] if len(d) >= 6 else [])
            )
            for s in cands:
                mm, dd = int(s[:2]), int(s[2:4])
                if 1 <= mm <= 12 and 1 <= dd <= 31:
                    return f"{s[:2]}/{s[2:4]}/{s[4:]}", 70.0
            return None, None

        up2 = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)

        # S1: blur5 + Otsu, 2×, PSM 8 — original approach, preserves working pages
        bl5 = cv2.GaussianBlur(up2, (5, 5), 0)
        _, bw = cv2.threshold(bl5, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        val, conf = _check(_ocr_d(bw, 8, 600))
        if val: return val, conf, best_digits

        # S2: fixed thr=100, 1×, PSM 8 — handles medium halftone pages
        _, bw = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
        val, conf = _check(_ocr_d(bw, 8, 300))
        if val: return val, conf, best_digits

        # S3: raw, 1×, PSM 8 — fast path for clean-background scans
        val, conf = _check(_ocr_d(gray, 8, 300))
        if val: return val, conf, best_digits

        # S4: thr=128, 2×, PSM 8
        _, bw = cv2.threshold(up2, 128, 255, cv2.THRESH_BINARY)
        val, conf = _check(_ocr_d(bw, 8, 600))
        if val: return val, conf, best_digits

        up3 = cv2.resize(gray, (w * 3, h * 3), interpolation=cv2.INTER_CUBIC)

        # S5: blur3 + Otsu, 3×, PSM 6 — handles sub-cell separator interference
        bl3 = cv2.GaussianBlur(up3, (3, 3), 0)
        _, bw = cv2.threshold(bl3, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        val, conf = _check(_ocr_d(bw, 6, 900))
        if val: return val, conf, best_digits

        # S6: thr=128, 3×, PSM 8
        _, bw = cv2.threshold(up3, 128, 255, cv2.THRESH_BINARY)
        val, conf = _check(_ocr_d(bw, 8, 900))
        if val: return val, conf, best_digits

        # S7: thr=100, 5×, PSM 8 — very dense halftone pages
        up5 = cv2.resize(gray, (w * 5, h * 5), interpolation=cv2.INTER_CUBIC)
        _, bw = cv2.threshold(up5, 100, 255, cv2.THRESH_BINARY)
        val, conf = _check(_ocr_d(bw, 8, 1500))
        if val: return val, conf, best_digits

        # S8: no-whitelist PSM 6 + sliding-window — whitelist suppresses recognition
        # on dense halftone; removing it lets LSTM find digit sequences in noise
        r_noisy = pytesseract.image_to_string(
            crop, config="--oem 1 --dpi 300 --psm 6"
        ).strip()
        all_d = re.sub(r"\D", "", r_noisy)
        if len(all_d) > len(best_digits):
            best_digits = all_d
        for i in range(len(all_d) - 5):
            s = all_d[i:i+6]
            mm, dd = int(s[:2]), int(s[2:4])
            if 1 <= mm <= 12 and 1 <= dd <= 31:
                return f"{s[:2]}/{s[2:4]}/{s[4:]}", 50.0, all_d

        return None, None, best_digits

    primary_crop = image.crop(box)
    date_val, conf_val, digits = _s1_try(primary_crop)
    if date_val:
        return date_val, conf_val
    if not digits:  # primary zone completely blank — try y-jitter
        for dy in (20, -20):
            jcrop = image.crop((left, top + dy, right, bottom + dy))
            date_val, conf_val, _ = _s1_try(jcrop)
            if date_val:
                return date_val, conf_val

    # Strategy 2 — per-sub-cell fallback.
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
        sub_crop = _prepare_numeric_crop(image.crop(sub_box), blur_k=5)
        val, conf = _ocr_region(sub_crop, psm=8, whitelist="0123456789 ", oem=1, dpi=600)
        parts.append(val.strip())
        if conf >= 0:
            confs.append(conf)

    mm, dd, yy = parts

    # Row-number column bleeds past x=55 on some scans, prepending an extra '1' to MM.
    if mm and len(mm) > 2 and int(mm) > 12:
        mm = mm[1:]  # "112" → "12"

    # Left-edge clipping: single-digit MM when the full zone returned only 5 digits
    # means the leading '1' of months 10–12 was cut off at the box's left edge.
    if mm and len(mm) == 1 and len(digits) == 5:
        candidate = "1" + mm
        if 10 <= int(candidate) <= 12:
            mm = candidate

    if mm and dd and yy:
        try:
            if 1 <= int(mm) <= 12 and 1 <= int(dd) <= 31:
                return f"{mm}/{dd}/{yy}", min(confs) if confs else -1.0
        except ValueError:
            pass

    non_empty = [p for p in [mm, dd, yy] if p]
    if non_empty:
        joined = "/".join(non_empty)
        if '/' in joined:  # multiple sub-cells contributed — partial but structured
            try:
                if mm and not (1 <= int(mm) <= 12):
                    return "", -1.0
                if dd and not (1 <= int(dd) <= 31):
                    return "", -1.0
            except ValueError:
                return "", -1.0
            return joined, min(confs) if confs else -1.0
        # Single sub-cell read with no slash separator — likely garbage.
        # Try PSM 6 on the full zone: it often sees text that PSM 8 misses.
        raw6 = pytesseract.image_to_string(
            _prepare_numeric_crop(image.crop(box), blur_k=5),
            config="--oem 1 --dpi 600 --psm 6 -c tessedit_char_whitelist=0123456789",
        ).strip()
        d6 = "".join(re.findall(r"\d+", raw6))
        if len(d6) >= 6:
            s = d6[:6]
            mm6, dd6 = int(s[:2]), int(s[2:4])
            if 1 <= mm6 <= 12 and 1 <= dd6 <= 31:
                return f"{s[:2]}/{s[2:4]}/{s[4:]}", 50.0
    # Strategy 3: dense halftone recovery via CLAHE/bilateral on tight top crop.
    return _ocr_date_halftone(image, box)


def _ocr_date_halftone(image: Image.Image, box: tuple) -> tuple[str, float]:
    """Dense halftone fallback for Box 24 service dates.

    Standard strategies fail when heavy halftone dot patterns create similar
    brightness to digit strokes. CLAHE locally equalises contrast so digits
    stand out. Three CLAHE configurations handle distinct halftone densities:
    - S1: clip=3, blur_k=7, thr=70 — moderate halftone
    - S2: clip=2, blur_k=7, thr=100 — fine halftone pattern
    - S3: clip=2, blur_k=11, thr=60 — coarser halftone / shifted digit cells
    Tries the original left bound plus left-10 and left-20 shifts to handle
    scans where digit cells start slightly outside the configured left edge.
    Only reads the top 45px — digits occupy the top portion; heavier halftone
    in the lower cells corrupts standard approaches.
    """
    left, top, right, _ = box

    def _check_6(d: str) -> tuple[str, float]:
        cands = (
            [d[1:7], d[:6]] if len(d) == 7 and d[0] == "1"
            else [d[:6]] if len(d) >= 6 else []
        )
        for s in cands:
            mm, dd = int(s[:2]), int(s[2:4])
            if 1 <= mm <= 12 and 1 <= dd <= 31:
                return f"{s[:2]}/{s[2:4]}/{s[4:]}", 70.0
        return "", -1.0

    def _ocr_bw(arr: np.ndarray) -> str:
        img = Image.fromarray(arr).convert("RGB")
        cfg = "--oem 1 --psm 7 -c tessedit_char_whitelist=0123456789 --dpi 600"
        try:
            return re.sub(r"\D", "", pytesseract.image_to_string(img, config=cfg).strip())
        except Exception:
            return ""

    for dx in (0, -10, -20):
        x0 = max(0, left + dx)
        gray = np.array(image.crop((x0, top, right, top + 45)).convert("L"))
        ht, wt = gray.shape

        cl3 = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4)).apply(gray)
        up2_c3 = cv2.resize(cl3, (wt * 2, ht * 2), interpolation=cv2.INTER_CUBIC)
        cl2 = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4)).apply(gray)
        up2_c2 = cv2.resize(cl2, (wt * 2, ht * 2), interpolation=cv2.INTER_CUBIC)

        # S1: clip=3, blur_k=7, thr=70
        bl7_c3 = cv2.GaussianBlur(up2_c3, (7, 7), 0)
        _, bw1 = cv2.threshold(bl7_c3, 70, 255, cv2.THRESH_BINARY)
        val, conf = _check_6(_ocr_bw(bw1))
        if val:
            return val, conf

        # S2: clip=2, blur_k=7, thr=100
        bl7_c2 = cv2.GaussianBlur(up2_c2, (7, 7), 0)
        _, bw2 = cv2.threshold(bl7_c2, 100, 255, cv2.THRESH_BINARY)
        val, conf = _check_6(_ocr_bw(bw2))
        if val:
            return val, conf

        # S3: clip=2, blur_k=11, thr=60
        bl11_c2 = cv2.GaussianBlur(up2_c2, (11, 11), 0)
        _, bw3 = cv2.threshold(bl11_c2, 60, 255, cv2.THRESH_BINARY)
        val, conf = _check_6(_ocr_bw(bw3))
        if val:
            return val, conf

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


def _ocr_patient_name_cms1500(image: Image.Image, primary_box: tuple) -> tuple[str, float]:
    """Extract patient name from the primary Box 2 zone.

    PSM 6 assumes a dense text block and fails when the row contains sparse content
    (form borders, label artefacts mixed with a single name token). PSM 11 (sparse
    text) is used as a fallback. If both fail, tries a crop shifted 40px up — some
    scans place the name row above the calibrated primary zone.
    """
    crop = image.crop(primary_box)
    val, conf = _ocr_region(crop, psm=6, whitelist=None)
    name = _extract_from_name_band(val)
    if name:
        return name, conf
    val11, conf11 = _ocr_region(crop, psm=11, whitelist=None)
    name11 = _extract_from_name_band(val11)
    if name11:
        return name11, conf11
    left, top, right, bottom = primary_box
    shifted_crop = image.crop((left, top - 40, right, bottom))
    val_s, conf_s = _ocr_region(shifted_crop, psm=6, whitelist=None)
    return _extract_from_name_band(val_s), conf_s


def _ocr_total_charge_cms1500(image: Image.Image, primary_box: tuple) -> tuple[str, float]:
    """Vertical-jitter fallback for Box 28 total charge.

    Scan jitter shifts the charge row up to 40px across pages.
    Try the primary zone first; step through ±20 px and ±40 px offsets if empty.
    Require ≥3 digit characters to accept a read as a real amount.
    """
    left, top, right, bottom = primary_box
    for dy in (0, -20, 20, -40, 40):
        box = (left, top + dy, right, bottom + dy)
        raw_crop = image.crop(box)

        # Pass 1: raw image, PSM 7 — fast and accurate for clean-background scans.
        val, conf = _ocr_region(raw_crop, psm=7, whitelist="0123456789. ", oem=1, dpi=300)
        if not val:
            # Pass 2: blur(k=9)+Otsu — handles halftone/grey-cell backgrounds.
            # PSM 6 (block) handles the two-line crop (label + amount) better than PSM 7.
            val, conf = _ocr_region(
                _prepare_numeric_crop(raw_crop, blur_k=9),
                psm=6, whitelist="0123456789. ", oem=1, dpi=600,
            )
        if val:
            # Take the first token that looks like a dollar amount
            for token in re.split(r"\s+", val):
                token = re.sub(r"^\D+", "", token)
                token = re.sub(r"\D+$", "", token)
                digit_count = len(re.sub(r"\D", "", token))
                if 3 <= digit_count <= 6:
                    return token, conf
    return "", -1.0


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
            name, conf = _ocr_patient_name_cms1500(image, fd.box)
            results.append(FieldResult(field_name="patient_name", value=name, confidence=conf))
        elif fd.name == "total_charge":
            value, conf = _ocr_total_charge_cms1500(image, fd.box)
            results.append(FieldResult(field_name=fd.name, value=value, confidence=conf))
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
