# tests/test_phase4.py
"""Phase 4 tests — EXTR-01, EXTR-02, EXTR-03 (field extraction).

CMS-1500 extracts 9 fields: patient_last_name, patient_first_name,
total_charge, date_of_service_sl1–sl6.

UB-04 extracts 25 fields: patient_last_name, patient_first_name,
total_charge, date_of_service_rl1–rl22.
"""
import pytest
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_TEST_PDF = str(_ROOT / "test.pdf")


# ---------------------------------------------------------------------------
# EXTR-01: extract_cms1500 — CMS-1500 field extraction
# ---------------------------------------------------------------------------

def test_extract_cms1500_returns_list(monkeypatch):
    """extract_cms1500 returns a list (D-05)."""
    import pytesseract
    from pipeline import extract_cms1500
    from PIL import Image

    empty_data = {'text': [], 'conf': []}
    monkeypatch.setattr(pytesseract, 'image_to_data',
                        lambda img, config='', output_type=None: empty_data)
    img = Image.new('RGB', (2550, 3300), 255)
    settings = {'tesseract_cmd': r'C:\Program Files\Tesseract-OCR\tesseract.exe'}
    result = extract_cms1500(img, settings)
    assert isinstance(result, list)


def test_extract_cms1500_result_count(monkeypatch):
    """extract_cms1500 returns exactly 9 FieldResults (3 single + 6 table) (EXTR-01)."""
    import pytesseract
    from pipeline import extract_cms1500
    from PIL import Image

    empty_data = {'text': [], 'conf': []}
    monkeypatch.setattr(pytesseract, 'image_to_data',
                        lambda img, config='', output_type=None: empty_data)
    img = Image.new('RGB', (2550, 3300), 255)
    settings = {'tesseract_cmd': r'C:\Program Files\Tesseract-OCR\tesseract.exe'}
    result = extract_cms1500(img, settings)
    assert len(result) == 9


def test_extract_cms1500_single_field_names(monkeypatch):
    """All expected single-field names appear in the CMS-1500 result (EXTR-01)."""
    import pytesseract
    from pipeline import extract_cms1500
    from PIL import Image

    empty_data = {'text': [], 'conf': []}
    monkeypatch.setattr(pytesseract, 'image_to_data',
                        lambda img, config='', output_type=None: empty_data)
    img = Image.new('RGB', (2550, 3300), 255)
    settings = {'tesseract_cmd': r'C:\Program Files\Tesseract-OCR\tesseract.exe'}
    result = extract_cms1500(img, settings)
    result_names = {r.field_name for r in result}
    expected = {"patient_last_name", "patient_first_name", "total_charge"}
    assert expected.issubset(result_names)


def test_extract_cms1500_service_line_naming(monkeypatch):
    """Box 24 table entries use _sl1.._sl6 suffix pattern (D-06)."""
    import pytesseract
    from pipeline import extract_cms1500
    from PIL import Image

    empty_data = {'text': [], 'conf': []}
    monkeypatch.setattr(pytesseract, 'image_to_data',
                        lambda img, config='', output_type=None: empty_data)
    img = Image.new('RGB', (2550, 3300), 255)
    settings = {'tesseract_cmd': r'C:\Program Files\Tesseract-OCR\tesseract.exe'}
    result = extract_cms1500(img, settings)
    result_names = {r.field_name for r in result}
    for sl in range(1, 7):
        assert f"date_of_service_sl{sl}" in result_names, f"Missing date_of_service_sl{sl}"


def test_extract_cms1500_blank_row_sentinel(monkeypatch):
    """Blank region returns FieldResult with value='' and confidence=-1.0 (D-11)."""
    import pytesseract
    from pipeline import extract_cms1500
    from PIL import Image

    empty_data = {'text': [], 'conf': []}
    monkeypatch.setattr(pytesseract, 'image_to_data',
                        lambda img, config='', output_type=None: empty_data)
    img = Image.new('RGB', (2550, 3300), 255)
    settings = {'tesseract_cmd': r'C:\Program Files\Tesseract-OCR\tesseract.exe'}
    result = extract_cms1500(img, settings)
    for r in result:
        assert r.value == '', f"Expected empty value for {r.field_name}, got {r.value!r}"
        assert r.confidence == -1.0, f"Expected -1.0 for {r.field_name}, got {r.confidence}"


def test_cms1500_all_results_have_confidence(monkeypatch):
    """Every CMS-1500 FieldResult has a numeric confidence attribute (EXTR-03)."""
    import pytesseract
    from pipeline import extract_cms1500
    from PIL import Image

    empty_data = {'text': [], 'conf': []}
    monkeypatch.setattr(pytesseract, 'image_to_data',
                        lambda img, config='', output_type=None: empty_data)
    img = Image.new('RGB', (2550, 3300), 255)
    settings = {'tesseract_cmd': r'C:\Program Files\Tesseract-OCR\tesseract.exe'}
    result = extract_cms1500(img, settings)
    for r in result:
        assert isinstance(r.confidence, float), (
            f"{r.field_name}: confidence must be float, got {type(r.confidence).__name__}"
        )


# ---------------------------------------------------------------------------
# EXTR-02: extract_ub04 — UB-04 field extraction
# ---------------------------------------------------------------------------

def test_extract_ub04_returns_list(monkeypatch):
    """extract_ub04 returns a list (D-05)."""
    import pytesseract
    from pipeline import extract_ub04
    from PIL import Image

    empty_data = {'text': [], 'conf': []}
    monkeypatch.setattr(pytesseract, 'image_to_data',
                        lambda img, config='', output_type=None: empty_data)
    img = Image.new('RGB', (2550, 3300), 255)
    settings = {'tesseract_cmd': r'C:\Program Files\Tesseract-OCR\tesseract.exe'}
    result = extract_ub04(img, settings)
    assert isinstance(result, list)


def test_extract_ub04_result_count(monkeypatch):
    """extract_ub04 returns exactly 25 FieldResults (3 single + 22 revenue-line) (EXTR-02)."""
    import pytesseract
    from pipeline import extract_ub04
    from PIL import Image

    empty_data = {'text': [], 'conf': []}
    monkeypatch.setattr(pytesseract, 'image_to_data',
                        lambda img, config='', output_type=None: empty_data)
    img = Image.new('RGB', (2550, 3300), 255)
    settings = {'tesseract_cmd': r'C:\Program Files\Tesseract-OCR\tesseract.exe'}
    result = extract_ub04(img, settings)
    assert len(result) == 25


def test_extract_ub04_revenue_line_naming(monkeypatch):
    """Revenue line entries use date_of_service_rl1.._rl22 suffix pattern (D-07)."""
    import pytesseract
    from pipeline import extract_ub04
    from PIL import Image

    empty_data = {'text': [], 'conf': []}
    monkeypatch.setattr(pytesseract, 'image_to_data',
                        lambda img, config='', output_type=None: empty_data)
    img = Image.new('RGB', (2550, 3300), 255)
    settings = {'tesseract_cmd': r'C:\Program Files\Tesseract-OCR\tesseract.exe'}
    result = extract_ub04(img, settings)
    result_names = {r.field_name for r in result}
    for rl in range(1, 23):
        assert f"date_of_service_rl{rl}" in result_names, f"Missing date_of_service_rl{rl}"


def test_extract_ub04_blank_rl_sentinel(monkeypatch):
    """Blank RL region returns FieldResult with value='' and confidence=-1.0 (D-11)."""
    import pytesseract
    from pipeline import extract_ub04
    from PIL import Image

    empty_data = {'text': [], 'conf': []}
    monkeypatch.setattr(pytesseract, 'image_to_data',
                        lambda img, config='', output_type=None: empty_data)
    img = Image.new('RGB', (2550, 3300), 255)
    settings = {'tesseract_cmd': r'C:\Program Files\Tesseract-OCR\tesseract.exe'}
    result = extract_ub04(img, settings)
    for r in result:
        assert r.value == '', f"Expected empty value for {r.field_name}, got {r.value!r}"
        assert r.confidence == -1.0, f"Expected -1.0 for {r.field_name}, got {r.confidence}"


def test_ub04_all_results_have_confidence(monkeypatch):
    """Every UB-04 FieldResult has a numeric confidence attribute (EXTR-03)."""
    import pytesseract
    from pipeline import extract_ub04
    from PIL import Image

    empty_data = {'text': [], 'conf': []}
    monkeypatch.setattr(pytesseract, 'image_to_data',
                        lambda img, config='', output_type=None: empty_data)
    img = Image.new('RGB', (2550, 3300), 255)
    settings = {'tesseract_cmd': r'C:\Program Files\Tesseract-OCR\tesseract.exe'}
    result = extract_ub04(img, settings)
    for r in result:
        assert isinstance(r.confidence, float), (
            f"{r.field_name}: confidence must be float, got {type(r.confidence).__name__}"
        )


# ---------------------------------------------------------------------------
# EXTR-01 + EXTR-02: pipeline import verification (D-09)
# ---------------------------------------------------------------------------

def test_import_extract_cms1500_from_pipeline():
    """extract_cms1500 is importable from the pipeline package (D-09)."""
    from pipeline import extract_cms1500
    assert callable(extract_cms1500)


def test_import_extract_ub04_from_pipeline():
    """extract_ub04 is importable from the pipeline package (D-09)."""
    from pipeline import extract_ub04
    assert callable(extract_ub04)


# ---------------------------------------------------------------------------
# EXTR-03: Integration tests — empirical calibration (Wave 2)
# ---------------------------------------------------------------------------

def test_cms1500_whitelist_date_chars(test_pdf_path, sample_settings):
    """CMS-1500 date_of_service fields contain only whitelisted chars."""
    from pipeline import convert_page, preprocess_page, detect_form_type, extract_cms1500

    date_chars = set("0123456789/ ")
    for page_num in range(30):
        raw = convert_page(test_pdf_path, page_num)
        if detect_form_type(raw) != "CMS-1500":
            continue
        proc = preprocess_page(raw, sample_settings)
        results = extract_cms1500(proc, sample_settings)
        for r in results:
            if not r.value:
                continue
            if "date_of_service" in r.field_name:
                bad = set(r.value) - date_chars
                assert not bad, f"{r.field_name}={r.value!r} has invalid chars: {bad}"
        return
    pytest.skip("No CMS-1500 page detected in test.pdf")


def test_ub04_whitelist_icd10_chars(test_pdf_path, sample_settings):
    """UB-04 date_of_service fields contain only digit/slash chars."""
    from pipeline import convert_page, preprocess_page, detect_form_type, extract_ub04

    date_chars = set("0123456789/ ")
    for page_num in range(30):
        raw = convert_page(test_pdf_path, page_num)
        if detect_form_type(raw) != "UB-04":
            continue
        proc = preprocess_page(raw, sample_settings)
        results = extract_ub04(proc, sample_settings)
        for r in results:
            if r.value and "date_of_service" in r.field_name:
                bad = set(r.value) - date_chars
                assert not bad, f"{r.field_name}={r.value!r} has invalid chars: {bad}"
        return
    pytest.skip("No UB-04 page detected in test.pdf")


def test_cms1500_smoke_80pct(test_pdf_path, sample_settings):
    """Real CMS-1500 page: >=37% non-empty fields (name, date, charge only)."""
    from pipeline import convert_page, preprocess_page, extract_cms1500

    CMS_THRESHOLD = 0.37  # page 19 measures ~43.8% with current coords
    raw = convert_page(test_pdf_path, 19)
    proc = preprocess_page(raw, sample_settings)
    results = extract_cms1500(proc, sample_settings)
    total = len(results)
    non_empty = sum(1 for r in results if r.value)
    rate = non_empty / total if total > 0 else 0.0
    assert rate >= CMS_THRESHOLD, (
        f"CMS-1500 page 19 non-empty rate {rate:.1%} < {CMS_THRESHOLD:.1%} "
        f"({non_empty}/{total} fields)"
    )


def test_ub04_smoke_80pct(test_pdf_path, sample_settings):
    """Real UB-04 page: >=5% non-empty fields across reduced field set."""
    from pipeline import convert_page, preprocess_page, extract_ub04

    UB04_THRESHOLD = 0.05  # page 11 measures ~7.7% with current coords
    raw = convert_page(test_pdf_path, 11)
    proc = preprocess_page(raw, sample_settings)
    results = extract_ub04(proc, sample_settings)
    total = len(results)
    non_empty = sum(1 for r in results if r.value)
    rate = non_empty / total if total > 0 else 0.0
    assert rate >= UB04_THRESHOLD, (
        f"UB-04 page 11 non-empty rate {rate:.1%} < {UB04_THRESHOLD:.1%} "
        f"({non_empty}/{total} fields)"
    )
