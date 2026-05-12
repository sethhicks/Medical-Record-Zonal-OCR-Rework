# tests/test_phase5.py
"""Phase 5 tests — OUT-01 through OUT-05 (Excel export writer).

All 12 stubs activated:
  - test_write_workbook_returns_str           -> activated by 05-02-PLAN
  - test_output_file_created                  -> activated by 05-02-PLAN
  - test_two_sheets_named_correctly           -> activated by 05-02-PLAN
  - test_cms1500_column_count                 -> activated by 05-02-PLAN
  - test_ub04_column_count                    -> activated by 05-02-PLAN
  - test_cms1500_header_row_frozen            -> activated by 05-02-PLAN
  - test_yellow_fill_below_threshold          -> activated by 05-02-PLAN
  - test_no_fill_above_threshold              -> activated by 05-02-PLAN
  - test_import_write_workbook_from_pipeline  -> activated by 05-03-PLAN
  - test_text_format_npi_column               -> activated by 05-03-PLAN
  - test_text_format_date_column              -> activated by 05-03-PLAN
  - test_cms1500_one_row_per_page             -> activated by 05-03-PLAN
"""
import pytest
from pathlib import Path

_ROOT = Path(__file__).parent.parent


def _make_results(field_names, value="", confidence=95.0):
    """Build a list of FieldResult objects for test setup.

    Args:
        field_names: iterable of field name strings
        value: OCR text value to assign to each result (default "")
        confidence: confidence score to assign (default 95.0)

    Returns:
        list[FieldResult]
    """
    from models.field_result import FieldResult
    return [FieldResult(field_name=name, value=value, confidence=confidence)
            for name in field_names]


# ---------------------------------------------------------------------------
# OUT-01 + OUT-02 + OUT-03: write_workbook — writer structure and file output
# Unit stubs (activated by 05-02-PLAN)
# ---------------------------------------------------------------------------

def test_write_workbook_returns_str(tmp_path):
    """write_workbook returns a str (file path to created workbook) (OUT-01)."""
    from pipeline import write_workbook
    result = write_workbook(
        cms_pages=[[]],
        ub_pages=[[]],
        settings={"output_dir": str(tmp_path), "confidence_threshold": 60},
    )
    assert isinstance(result, str)


def test_output_file_created(tmp_path):
    """write_workbook creates the output .xlsx file on disk (OUT-01)."""
    from pipeline import write_workbook
    result = write_workbook(
        cms_pages=[[]],
        ub_pages=[[]],
        settings={"output_dir": str(tmp_path), "confidence_threshold": 60},
    )
    assert Path(result).exists()


def test_two_sheets_named_correctly(tmp_path):
    """Workbook contains exactly two sheets: 'CMS-1500' and 'UB-04' (OUT-02)."""
    import openpyxl
    from pipeline import write_workbook
    result = write_workbook(
        cms_pages=[[]],
        ub_pages=[[]],
        settings={"output_dir": str(tmp_path), "confidence_threshold": 60},
    )
    wb = openpyxl.load_workbook(result)
    assert wb.sheetnames == ["CMS-1500", "UB-04"]


def test_cms1500_column_count(tmp_path):
    """CMS-1500 sheet has exactly 9 columns (one per FieldResult) (OUT-02)."""
    import openpyxl
    from pipeline import write_workbook
    field_names = (
        ["patient_last_name", "patient_first_name", "total_charge"]
        + [f"date_of_service_sl{i}" for i in range(1, 7)]
    )
    results = _make_results(field_names)
    result = write_workbook(
        cms_pages=[results],
        ub_pages=[[]],
        settings={"output_dir": str(tmp_path), "confidence_threshold": 60},
    )
    wb = openpyxl.load_workbook(result)
    ws = wb["CMS-1500"]
    assert ws.max_column == 9


def test_ub04_column_count(tmp_path):
    """UB-04 sheet has exactly 25 columns (one per FieldResult) (OUT-02)."""
    import openpyxl
    from pipeline import write_workbook
    field_names = (
        ["patient_last_name", "patient_first_name", "total_charge"]
        + [f"date_of_service_rl{i}" for i in range(1, 23)]
    )
    results = _make_results(field_names)
    result = write_workbook(
        cms_pages=[[]],
        ub_pages=[results],
        settings={"output_dir": str(tmp_path), "confidence_threshold": 60},
    )
    wb = openpyxl.load_workbook(result)
    ws = wb["UB-04"]
    assert ws.max_column == 25


def test_cms1500_header_row_frozen(tmp_path):
    """CMS-1500 sheet header row is frozen (freeze_panes == 'A2') (OUT-03)."""
    import openpyxl
    from pipeline import write_workbook
    result = write_workbook(
        cms_pages=[[]],
        ub_pages=[[]],
        settings={"output_dir": str(tmp_path), "confidence_threshold": 60},
    )
    wb = openpyxl.load_workbook(result)
    ws = wb["CMS-1500"]
    assert ws.freeze_panes == "A2"


def test_yellow_fill_below_threshold(tmp_path):
    """Cell for FieldResult with confidence below threshold is filled yellow (OUT-04)."""
    import openpyxl
    from pipeline import write_workbook
    from config.cms1500 import CMS1500_FIELDS
    label = next(fd.label or fd.name for fd in CMS1500_FIELDS if fd.name == "total_charge")
    results = _make_results(["total_charge"], value="150.00", confidence=10.0)
    result = write_workbook(
        cms_pages=[results],
        ub_pages=[[]],
        settings={"output_dir": str(tmp_path), "confidence_threshold": 60},
    )
    wb = openpyxl.load_workbook(result)
    ws = wb["CMS-1500"]
    header_row = [ws.cell(1, col).value for col in range(1, ws.max_column + 1)]
    col_idx = header_row.index(label) + 1
    cell = ws.cell(2, col_idx)
    # openpyxl stores colors as ARGB; value may be "FFFF00" or "00FFFF00" (with alpha prefix)
    assert cell.fill.fgColor.rgb.endswith("FFFF00")


def test_no_fill_above_threshold(tmp_path):
    """Cell for FieldResult with confidence above threshold has no yellow fill (OUT-04)."""
    import openpyxl
    from pipeline import write_workbook
    from config.cms1500 import CMS1500_FIELDS
    label = next(fd.label or fd.name for fd in CMS1500_FIELDS if fd.name == "total_charge")
    results = _make_results(["total_charge"], value="150.00", confidence=90.0)
    result = write_workbook(
        cms_pages=[results],
        ub_pages=[[]],
        settings={"output_dir": str(tmp_path), "confidence_threshold": 60},
    )
    wb = openpyxl.load_workbook(result)
    ws = wb["CMS-1500"]
    header_row = [ws.cell(1, col).value for col in range(1, ws.max_column + 1)]
    col_idx = header_row.index(label) + 1
    cell = ws.cell(2, col_idx)
    fill = cell.fill
    assert fill is None or fill.fill_type == "none" or fill.fgColor.rgb != "FFFF00"


# ---------------------------------------------------------------------------
# OUT-01 + OUT-05: pipeline import and text formatting
# Integration stubs (activated by 05-03-PLAN)
# ---------------------------------------------------------------------------

def test_import_write_workbook_from_pipeline():
    """write_workbook is importable from the pipeline package (OUT-01)."""
    from pipeline import write_workbook
    assert callable(write_workbook)


def test_text_format_charge_column(tmp_path):
    """Total charge column cells use text format '@' to prevent Excel number conversion (OUT-05)."""
    import openpyxl
    from pipeline import write_workbook
    from config.cms1500 import CMS1500_FIELDS
    charge_label = next(fd.label or fd.name for fd in CMS1500_FIELDS if fd.name == "total_charge")
    results = _make_results(["total_charge"], value="123.45", confidence=95.0)
    result = write_workbook(
        cms_pages=[results],
        ub_pages=[[]],
        settings={"output_dir": str(tmp_path), "confidence_threshold": 60},
    )
    wb = openpyxl.load_workbook(result)
    ws = wb["CMS-1500"]
    header_row = [ws.cell(1, col).value for col in range(1, ws.max_column + 1)]
    col_idx = header_row.index(charge_label) + 1
    cell = ws.cell(2, col_idx)
    assert cell.number_format == "@"


def test_text_format_date_column(tmp_path):
    """Date column cells use text format '@' to preserve date strings as-is (OUT-05)."""
    import openpyxl
    from pipeline import write_workbook
    from config.cms1500 import CMS1500_TABLE_FIELDS
    # Writer uses "{tfd.label or tfd.name} SL{N}" as header (D-02/D-04)
    date_tfd = next(tfd for tfd in CMS1500_TABLE_FIELDS if tfd.name == "date_of_service")
    date_sl1_header = f"{date_tfd.label or date_tfd.name} SL1"
    results = _make_results(["date_of_service_sl1"], value="01/01/2024", confidence=95.0)
    result = write_workbook(
        cms_pages=[results],
        ub_pages=[[]],
        settings={"output_dir": str(tmp_path), "confidence_threshold": 60},
    )
    wb = openpyxl.load_workbook(result)
    ws = wb["CMS-1500"]
    header_row = [ws.cell(1, col).value for col in range(1, ws.max_column + 1)]
    col_idx = header_row.index(date_sl1_header) + 1
    cell = ws.cell(2, col_idx)
    assert cell.number_format == "@"


def test_cms1500_one_row_per_page(tmp_path):
    """CMS-1500 sheet has one row per page (header + N data rows for N pages) (OUT-02)."""
    import openpyxl
    from pipeline import write_workbook
    page1 = _make_results(["box1_insurance_type"], value="X", confidence=90.0)
    page2 = _make_results(["box1_insurance_type"], value="Y", confidence=90.0)
    result = write_workbook(
        cms_pages=[page1, page2],
        ub_pages=[[]],
        settings={"output_dir": str(tmp_path), "confidence_threshold": 60},
    )
    wb = openpyxl.load_workbook(result)
    ws = wb["CMS-1500"]
    assert ws.max_row == 3  # header row + 2 data rows
