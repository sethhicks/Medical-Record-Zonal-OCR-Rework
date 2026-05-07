# pipeline/detector.py
"""Form type detector for OCR Medical Billing Form Extractor.

Standalone usage (for ad-hoc testing):
    python -c "from pipeline.detector import detect_form_type; from PIL import Image; img = Image.new('RGB',(2550,3300),255); print(detect_form_type(img))"

Importable usage:
    from pipeline import detect_form_type
    form_type = detect_form_type(image)  # returns 'CMS-1500', 'UB-04', or 'UNKNOWN'
"""
import pytesseract
from PIL import Image

from config_loader import load_settings as _load_settings

_settings = _load_settings()
pytesseract.pytesseract.tesseract_cmd = _settings['tesseract_cmd']

# Crop regions verified via pixel-level scan of all 30 test.pdf pages [2026-05-01]
_HEADER_STRIP = (0, 0, 2550, 600)     # top 600 px — captures HEALTH INSURANCE banner at any y-offset
_FOOTER_STRIP = (0, 2900, 2550, 3300)  # bottom 400 px — captures NUCC/FORM 1500 and NUBC copyright lines


def detect_form_type(image: "Image.Image") -> str:
    """Classify a raw page image as 'CMS-1500', 'UB-04', or 'UNKNOWN'.

    Args:
        image: Raw PIL Image from convert_page() — mode 'RGB', 2550x3300 px.
               Detection runs on the RAW image, not the preprocessed image.

    Returns:
        'CMS-1500' — cms_score >= 2 and ub04_score == 0
        'UB-04'    — ub04_score >= 1 and cms_score < 2
        'UNKNOWN'  — both match simultaneously, or neither matches threshold
    """
    if image is None:
        raise TypeError("detect_form_type requires a PIL Image, got None")
    w, h = image.size
    if (w, h) != (2550, 3300):
        raise ValueError(
            f"detect_form_type expects a 2550x3300 px image, got {w}x{h}. "
            "Pass the output of convert_page() directly."
        )

    # Crop to header and footer strips; convert to grayscale for Tesseract
    header_gray = image.crop(_HEADER_STRIP).convert('L')
    footer_gray = image.crop(_FOOTER_STRIP).convert('L')

    # 3 OCR calls: header PSM6, footer PSM6, footer PSM11
    # PSM6 assembles the NUCC footer line correctly; PSM11 finds scattered NUBC text
    header_text = pytesseract.image_to_string(header_gray, config='--psm 6').upper()
    footer_psm6 = pytesseract.image_to_string(footer_gray, config='--psm 6').upper()
    footer_psm11 = pytesseract.image_to_string(footer_gray, config='--psm 11').upper()

    # CMS-1500 anchor evaluation (partial substring matching — exact strings garble on scans)
    heal_hit = 'HEALTH' in header_text
    nuc_hit = 'NUC' in footer_psm6 or 'NUC' in footer_psm11
    form1500_hit = (
        ('FORM' in footer_psm6 and '1500' in footer_psm6) or
        ('FORM' in footer_psm11 and '1500' in footer_psm11)
    )
    cms_score = sum([heal_hit, nuc_hit, form1500_hit])  # 0-3; needs >= 2 to classify

    # UB-04 anchor evaluation
    nubc_hit = 'NUBC' in footer_psm6 or 'NUBC' in footer_psm11
    ub04_label_hit = (
        'UB-04' in footer_psm11 or
        'CMS-1450' in footer_psm11 or
        '1450' in footer_psm11
    )
    ub04_score = sum([nubc_hit, ub04_label_hit])  # 0-2; needs >= 1 to classify

    # Classification — D-05: both match -> UNKNOWN; D-06: neither -> UNKNOWN
    if cms_score >= 2 and ub04_score == 0:
        return 'CMS-1500'
    elif ub04_score >= 1 and cms_score < 2:
        return 'UB-04'
    else:
        return 'UNKNOWN'
