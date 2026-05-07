# tests/test_phase3.py
"""Phase 3 tests — PROC-03 (form type detection).

Skip markers are removed by Wave 1 plans as each feature is implemented:
  - test_cms1500_detection_mock     -> removed by 03-02-PLAN
  - test_ub04_detection_mock        -> removed by 03-02-PLAN
  - test_unknown_when_no_anchors    -> removed by 03-02-PLAN
  - test_both_match_returns_unknown -> removed by 03-02-PLAN
  - test_unknown_result_is_string   -> removed by 03-02-PLAN
  - test_import_from_pipeline       -> removed by 03-03-PLAN
  - test_cms1500_smoke              -> removed by 03-03-PLAN
  - test_ub04_smoke                 -> removed by 03-03-PLAN
"""
import pytest
from pathlib import Path
from unittest.mock import Mock

_ROOT = Path(__file__).parent.parent
_TEST_PDF = str(_ROOT / "test.pdf")


# ---------------------------------------------------------------------------
# PROC-03: detect_form_type
# ---------------------------------------------------------------------------

def test_cms1500_detection_mock(monkeypatch):
    """2-of-3 CMS-1500 anchors via mock OCR returns 'CMS-1500'."""
    import pytesseract
    from pipeline import detect_form_type
    from PIL import Image

    mock_ocr = Mock(side_effect=[
        'HEALTH INSURANCE CLAIM FORM',          # call 1: header PSM6 -> HEALTH hit
        '',                                     # call 2: header PSM11
        'NUCC Instruction Manual FORM 1500',    # call 3: footer PSM6 -> NUC + FORM1500 hit
        '',                                     # call 4: footer PSM11 -> no UB-04 anchors
    ])
    monkeypatch.setattr(pytesseract, 'image_to_string', mock_ocr)
    img = Image.new('RGB', (2550, 3300), 255)
    assert detect_form_type(img) == 'CMS-1500'
    assert mock_ocr.call_count == 4


def test_ub04_detection_mock(monkeypatch):
    """NUBC anchor found via mock OCR returns 'UB-04'."""
    import pytesseract
    from pipeline import detect_form_type
    from PIL import Image

    mock_ocr = Mock(side_effect=[
        '',              # call 1: header PSM6 -> no HEALTH
        '',              # call 2: header PSM11 -> no HEALTH
        '',              # call 3: footer PSM6 -> no CMS anchors
        'NUBC',          # call 4: footer PSM11 -> NUBC hit -> ub04_score=1, cms_score=0
    ])
    monkeypatch.setattr(pytesseract, 'image_to_string', mock_ocr)
    img = Image.new('RGB', (2550, 3300), 255)
    assert detect_form_type(img) == 'UB-04'
    assert mock_ocr.call_count == 4


def test_unknown_when_no_anchors(monkeypatch):
    """All OCR returns empty string — result is 'UNKNOWN'."""
    import pytesseract
    from pipeline import detect_form_type
    from PIL import Image

    monkeypatch.setattr(pytesseract, 'image_to_string',
                        lambda img, config='': '')
    img = Image.new('RGB', (2550, 3300), 255)
    assert detect_form_type(img) == 'UNKNOWN'


def test_both_match_returns_unknown(monkeypatch):
    """cms_score>=2 AND ub04_score>=1 simultaneously -> 'UNKNOWN'."""
    import pytesseract
    from pipeline import detect_form_type
    from PIL import Image

    mock_ocr = Mock(side_effect=[
        'HEALTH INSURANCE',                     # call 1: header PSM6 -> HEALTH hit (cms+1)
        '',                                     # call 2: header PSM11
        'NUCC Instruction FORM 1500 NUBC',      # call 3: footer PSM6 -> NUC+FORM1500 (cms+2), NUBC (ub04+1)
        '',                                     # call 4: footer PSM11
    ])
    monkeypatch.setattr(pytesseract, 'image_to_string', mock_ocr)
    img = Image.new('RGB', (2550, 3300), 255)
    # cms_score=3, ub04_score=1 -> both match -> UNKNOWN
    assert detect_form_type(img) == 'UNKNOWN'
    assert mock_ocr.call_count == 4


def test_unknown_result_is_string(monkeypatch):
    """detect_form_type always returns a str; 'UNKNOWN' is str."""
    import pytesseract
    from pipeline import detect_form_type
    from PIL import Image

    monkeypatch.setattr(pytesseract, 'image_to_string',
                        lambda img, config='': '')
    img = Image.new('RGB', (2550, 3300), 255)
    result = detect_form_type(img)
    assert result == 'UNKNOWN'
    assert isinstance(result, str)


def test_import_from_pipeline():
    """detect_form_type is importable from the pipeline package (per D-08)."""
    from pipeline import detect_form_type
    assert callable(detect_form_type)


@pytest.mark.skipif(
    not (_ROOT / "test.pdf").exists(),
    reason="test.pdf not present"
)
def test_cms1500_smoke(test_pdf_path):
    """Real test.pdf page 0 classifies as 'CMS-1500' (uses actual Tesseract, ~2s)."""
    from pipeline import convert_page, detect_form_type
    image = convert_page(test_pdf_path, 0)
    assert detect_form_type(image) == 'CMS-1500'


@pytest.mark.skipif(
    not (_ROOT / "test.pdf").exists(),
    reason="test.pdf not present"
)
def test_ub04_smoke(test_pdf_path):
    """Real test.pdf page 6 classifies as 'UB-04' (uses actual Tesseract, ~2s)."""
    from pipeline import convert_page, detect_form_type
    image = convert_page(test_pdf_path, 6)
    assert detect_form_type(image) == 'UB-04'


@pytest.mark.skipif(
    not (_ROOT / "test.pdf").exists(),
    reason="test.pdf not present"
)
def test_ub04_page11_smoke(test_pdf_path):
    """Real test.pdf page 11 (scan-degraded UB-04) classifies as 'UB-04'."""
    from pipeline import convert_page, detect_form_type
    image = convert_page(test_pdf_path, 11)
    assert detect_form_type(image) == 'UB-04'
