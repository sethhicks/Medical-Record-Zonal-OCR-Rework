# tests/test_phase4.py
"""Phase 4 tests — EXTR-01, EXTR-02, EXTR-03 (field extraction).

Skip markers are removed by Wave 1/2 plans as each feature is implemented:
  - test_extract_cms1500_returns_list          -> removed by 04-03-PLAN
  - test_extract_cms1500_result_count          -> removed by 04-03-PLAN
  - test_extract_cms1500_single_field_names    -> removed by 04-03-PLAN
  - test_extract_cms1500_service_line_naming   -> removed by 04-03-PLAN
  - test_extract_cms1500_blank_row_sentinel    -> removed by 04-03-PLAN
  - test_cms1500_all_results_have_confidence   -> removed by 04-03-PLAN
  - test_extract_ub04_returns_list             -> removed by 04-04-PLAN
  - test_extract_ub04_result_count             -> removed by 04-04-PLAN
  - test_extract_ub04_revenue_line_naming      -> removed by 04-04-PLAN
  - test_extract_ub04_blank_rl_sentinel        -> removed by 04-04-PLAN
  - test_ub04_all_results_have_confidence      -> removed by 04-04-PLAN
  - test_import_extract_cms1500_from_pipeline  -> removed by 04-05-PLAN
  - test_import_extract_ub04_from_pipeline     -> removed by 04-05-PLAN
  - test_cms1500_whitelist_npi_chars           -> removed by 04-06-PLAN
  - test_ub04_whitelist_icd10_chars            -> removed by 04-06-PLAN
  - test_cms1500_smoke_80pct                   -> removed by 04-06-PLAN
  - test_ub04_smoke_80pct                      -> removed by 04-06-PLAN
"""
import pytest
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_TEST_PDF = str(_ROOT / "test.pdf")


# ---------------------------------------------------------------------------
# EXTR-01: extract_cms1500 — CMS-1500 field extraction
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="stub — implemented by Wave 1")
def test_extract_cms1500_returns_list(monkeypatch):
    """extract_cms1500 returns a list."""
    pass


@pytest.mark.skip(reason="stub — implemented by Wave 1")
def test_extract_cms1500_result_count(monkeypatch):
    """extract_cms1500 returns exactly 89 FieldResults (29 single + 60 table)."""
    pass


@pytest.mark.skip(reason="stub — implemented by Wave 1")
def test_extract_cms1500_single_field_names(monkeypatch):
    """all 29 single-field names are present in the result."""
    pass


@pytest.mark.skip(reason="stub — implemented by Wave 1")
def test_extract_cms1500_service_line_naming(monkeypatch):
    """Box 24 table entries use _sl1.._sl6 suffix (D-06)."""
    pass


@pytest.mark.skip(reason="stub — implemented by Wave 1")
def test_extract_cms1500_blank_row_sentinel(monkeypatch):
    """blank region returns FieldResult with confidence=-1.0 (D-11)."""
    pass


@pytest.mark.skip(reason="stub — implemented by Wave 1")
def test_cms1500_all_results_have_confidence(monkeypatch):
    """every CMS-1500 FieldResult has a numeric confidence attribute."""
    pass


# ---------------------------------------------------------------------------
# EXTR-02: extract_ub04 — UB-04 field extraction
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="stub — implemented by Wave 1")
def test_extract_ub04_returns_list(monkeypatch):
    """extract_ub04 returns a list."""
    pass


@pytest.mark.skip(reason="stub — implemented by Wave 1")
def test_extract_ub04_result_count(monkeypatch):
    """extract_ub04 returns exactly 178 FieldResults (24 single + 154 table)."""
    pass


@pytest.mark.skip(reason="stub — implemented by Wave 1")
def test_extract_ub04_revenue_line_naming(monkeypatch):
    """revenue line entries use _rl1.._rl22 suffix (D-07)."""
    pass


@pytest.mark.skip(reason="stub — implemented by Wave 1")
def test_extract_ub04_blank_rl_sentinel(monkeypatch):
    """blank RL region returns FieldResult with confidence=-1.0 (D-11)."""
    pass


@pytest.mark.skip(reason="stub — implemented by Wave 1")
def test_ub04_all_results_have_confidence(monkeypatch):
    """every UB-04 FieldResult has a numeric confidence attribute."""
    pass


# ---------------------------------------------------------------------------
# EXTR-01 + EXTR-02: pipeline import verification (D-09)
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="stub — implemented by Wave 1")
def test_import_extract_cms1500_from_pipeline():
    """extract_cms1500 importable from pipeline (D-09)."""
    pass


@pytest.mark.skip(reason="stub — implemented by Wave 1")
def test_import_extract_ub04_from_pipeline():
    """extract_ub04 importable from pipeline (D-09)."""
    pass


# ---------------------------------------------------------------------------
# EXTR-03: Integration tests — empirical calibration (Wave 2)
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="stub — implemented by Wave 2")
def test_cms1500_whitelist_npi_chars(test_pdf_path, sample_settings):
    """CMS-1500 NPI/CPT fields contain only whitelisted chars."""
    pass


@pytest.mark.skip(reason="stub — implemented by Wave 2")
def test_ub04_whitelist_icd10_chars(test_pdf_path, sample_settings):
    """UB-04 ICD-10 fields contain only alpha+digit+dot."""
    pass


@pytest.mark.skip(reason="stub — implemented by Wave 2")
def test_cms1500_smoke_80pct(test_pdf_path, sample_settings):
    """real CMS-1500 page: >=empirically-calibrated % non-empty fields."""
    pass


@pytest.mark.skip(reason="stub — implemented by Wave 2")
def test_ub04_smoke_80pct(test_pdf_path, sample_settings):
    """real UB-04 page: >=empirically-calibrated % non-empty fields."""
    pass
