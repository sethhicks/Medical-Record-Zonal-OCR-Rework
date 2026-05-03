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

_ROOT = Path(__file__).parent.parent
_TEST_PDF = str(_ROOT / "test.pdf")


# ---------------------------------------------------------------------------
# PROC-03: detect_form_type
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Wave 1 — detector not implemented yet")
def test_cms1500_detection_mock(monkeypatch):
    """2-of-3 CMS-1500 anchors via mock OCR returns 'CMS-1500'."""
    pass


@pytest.mark.skip(reason="Wave 1 — detector not implemented yet")
def test_ub04_detection_mock(monkeypatch):
    """NUBC anchor found via mock OCR returns 'UB-04'."""
    pass


@pytest.mark.skip(reason="Wave 1 — detector not implemented yet")
def test_unknown_when_no_anchors(monkeypatch):
    """All OCR returns empty string — result is 'UNKNOWN'."""
    pass


@pytest.mark.skip(reason="Wave 1 — detector not implemented yet")
def test_both_match_returns_unknown(monkeypatch):
    """cms_score>=2 AND ub04_score>=1 simultaneously -> 'UNKNOWN'."""
    pass


@pytest.mark.skip(reason="Wave 1 — detector not implemented yet")
def test_unknown_result_is_string(monkeypatch):
    """detect_form_type always returns a str; 'UNKNOWN' is str."""
    pass


@pytest.mark.skip(reason="Wave 1 — detector not implemented yet")
def test_import_from_pipeline():
    """detect_form_type is importable from the pipeline package."""
    pass


@pytest.mark.skip(reason="Wave 1 — detector not implemented yet")
def test_cms1500_smoke(test_pdf_path):
    """Real test.pdf page 0 classifies as 'CMS-1500' (uses actual Tesseract, ~2s)."""
    pass


@pytest.mark.skip(reason="Wave 1 — detector not implemented yet")
def test_ub04_smoke(test_pdf_path):
    """Real test.pdf page 6 classifies as 'UB-04' (uses actual Tesseract, ~2s)."""
    pass
