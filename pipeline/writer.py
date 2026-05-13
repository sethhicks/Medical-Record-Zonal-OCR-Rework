# pipeline/writer.py
"""Excel workbook writer for OCR extraction results.

Public API:
    write_workbook(cms_pages, ub_pages, settings) -> str
        Accepts per-page FieldResult lists for CMS-1500 and UB-04 pages and
        produces a formatted billing-staff-ready Excel workbook.

        Args:
            cms_pages: list of per-page FieldResult lists for CMS-1500 pages
            ub_pages: list of per-page FieldResult lists for UB-04 pages
            settings: dict from load_settings(); reads 'output_dir' and
                      'confidence_threshold' keys

        Returns:
            Full output path as str (e.g. "C:/Users/.../Desktop/extracted_results.xlsx")

Decisions implemented:
    D-05: Output filename is always 'extracted_results.xlsx'; silent overwrite
    D-06: Returns full output path as str for Phase 6 "Open output file" button
    D-08: Date and monetary columns: number_format = "@" (prevent Excel auto-convert)
    D-09: Text format via field_name substring matching
"""
from __future__ import annotations

import pathlib

import openpyxl

from models.field_result import FieldResult

# Substrings that trigger text format (@) — prevents Excel from converting
# dates, dollar amounts, and codes into numbers.
_TEXT_FORMAT_SUBSTRINGS = {"date", "charge", "name"}


def _needs_text_format(field_name: str) -> bool:
    name_lower = field_name.lower()
    return any(sub in name_lower for sub in _TEXT_FORMAT_SUBSTRINGS)


# ---------------------------------------------------------------------------
# Headers and column maps — 3 columns per sheet
# ---------------------------------------------------------------------------

def _cms_headers() -> list[str]:
    return ["Patient Name", "Total Charge", "Date of Service"]


def _ub_headers() -> list[str]:
    return ["Patient Name", "Total Charge", "Date of Service"]


def _cms_col_map() -> dict[str, int]:
    return {
        "patient_name": 1,
        "total_charge": 2,
        "date_of_service_sl1": 3,
    }


def _ub_col_map() -> dict[str, int]:
    return {
        "patient_name": 1,
        "total_charge": 2,
        "date_of_service_rl1": 3,
    }


# ---------------------------------------------------------------------------
# Sheet writing helper
# ---------------------------------------------------------------------------

def _write_sheet(
    ws,
    headers: list[str],
    col_map: dict[str, int],
    pages: list[list[FieldResult]],
) -> None:
    """Write a single sheet: header row + one data row per page."""
    for col_idx, header in enumerate(headers, start=1):
        ws.cell(row=1, column=col_idx, value=header)
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = 20

    ws.freeze_panes = "A2"

    for row_idx, page_results in enumerate(pages, start=2):
        result_map: dict[str, FieldResult] = {fr.field_name: fr for fr in page_results}
        for field_name, col_idx in col_map.items():
            fr = result_map.get(field_name)
            value = fr.value if fr else ""
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            if _needs_text_format(field_name):
                cell.number_format = "@"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def write_workbook(
    cms_pages: list[list[FieldResult]],
    ub_pages: list[list[FieldResult]],
    settings: dict,
) -> str:
    """Write extraction results to a formatted Excel workbook.

    Creates 'extracted_results.xlsx' in settings['output_dir'] with two sheets:
    'CMS-1500' and 'UB-04', each with 3 columns: Patient Name, Total Charge,
    Date of Service. Header row frozen at A2, columns width 20.

    Security note: output filename is hardcoded ('extracted_results.xlsx').
    Only the directory comes from settings — prevents path injection (T-05-02).

    Args:
        cms_pages: Per-page FieldResult lists for CMS-1500 pages.
        ub_pages: Per-page FieldResult lists for UB-04 pages.
        settings: Dict from load_settings(). Reads 'output_dir' (default Desktop).

    Returns:
        Full output path as str (D-06). Phase 6 passes this to os.startfile().
    """
    output_dir = pathlib.Path(settings.get("output_dir", str(pathlib.Path.home() / "Desktop")))
    output_path = output_dir / "extracted_results.xlsx"

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    ws_cms = wb.create_sheet("CMS-1500")
    _write_sheet(ws_cms, _cms_headers(), _cms_col_map(), cms_pages)

    ws_ub = wb.create_sheet("UB-04")
    _write_sheet(ws_ub, _ub_headers(), _ub_col_map(), ub_pages)

    wb.save(str(output_path))
    return str(output_path)
