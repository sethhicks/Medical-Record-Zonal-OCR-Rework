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
    D-01: Column headers use FieldDef.label, falling back to FieldDef.name if empty
    D-02: CMS-1500 service-line column headers: "{label} SL{N}" for N in 1..6
    D-03: UB-04 revenue-line column headers: "{label} RL{N}" for N in 1..22
    D-04: Same label-fallback rule for TableFieldDef; yellow fill for conf < threshold
    D-05: Output filename is always 'extracted_results.xlsx'; silent overwrite
    D-06: Returns full output path as str for Phase 6 "Open output file" button
    D-07: NPI, CPT/HCPCS, ICD code, ZIP, tax ID columns: number_format = "@"
    D-08: Date and monetary columns: number_format = "@" (prevent Excel auto-convert)
    D-09: Text format via field_name substring matching
    D-10: No metadata columns; billing staff use claim-native row identifiers
"""
from __future__ import annotations

import pathlib

import openpyxl
from openpyxl.styles import PatternFill

from config.cms1500 import CMS1500_FIELDS, CMS1500_TABLE_FIELDS
from config.ub04 import UB04_FIELDS, UB04_TABLE_FIELDS
from models.field_result import FieldResult

# ---------------------------------------------------------------------------
# Yellow fill constant (D-04)
# ---------------------------------------------------------------------------

_YELLOW = PatternFill(fill_type="solid", fgColor="FFFF00")

# ---------------------------------------------------------------------------
# Text-format substring set (D-07, D-08, D-09)
# Apply cell.number_format = "@" when any substring matches the field_name (lowercase)
# ---------------------------------------------------------------------------

_TEXT_FORMAT_SUBSTRINGS = {
    "npi",         # all NPI fields (box17b_referring_npi, box24_rendering_npi, box56_npi, box76)
    "cpt",         # box24_cpt_sl1..sl6
    "zip",         # any ZIP code fields
    "tax",         # box25_federal_tax_id, box5_federal_tax
    "icd",         # ICD code fields (fallback — box21x_diag uses "diag" below)
    "dob",         # box3_dob_sex
    "date",        # box24_date_from_sl1..sl6, ub04_rl_svc_date_rl1..rl22, box12_admission_date, box10_birthdate
    "charge",      # box28_total_charge, box24_charges_sl1..sl6, ub04_rl_total_charges_rl1..rl22
    "amount",      # box29_amount_paid, box55_est_amount_due
    "paid",        # box29_amount_paid, box54_prior_payments
    "stmt",        # box6_stmt_from/through (if present)
    "hcpcs",       # ub04_rl_hcpcs_rl1..rl22
    "rev_code",    # ub04_rl_rev_code_rl1..rl22
    "non_covered", # ub04_rl_non_covered_rl1..rl22
    "diag",        # box21a_diag..box21l_diag (ICD codes named with _diag not _icd)
    "dx",          # box66_dx_codes (UB-04 diagnosis/procedure codes)
    "statement",   # box6_statement_period (UB-04 statement period)
    "payment",     # box54_prior_payments (contains "payment" not "paid")
}


def _needs_text_format(field_name: str) -> bool:
    """Return True if this field should use Excel text format '@'.

    Checks field_name (lowercased) for any substring in _TEXT_FORMAT_SUBSTRINGS.
    """
    name_lower = field_name.lower()
    return any(sub in name_lower for sub in _TEXT_FORMAT_SUBSTRINGS)


# ---------------------------------------------------------------------------
# Header list builders
# ---------------------------------------------------------------------------

def _cms_headers() -> list[str]:
    """Build the ordered list of 89 CMS-1500 column headers."""
    headers: list[str] = []
    for fd in CMS1500_FIELDS:
        headers.append(fd.label or fd.name)   # D-01: label fallback to name
    for tfd in CMS1500_TABLE_FIELDS:
        col_label = tfd.label or tfd.name      # D-04: same fallback for TableFieldDef
        for i in range(6):                     # D-02: SL1..SL6
            headers.append(f"{col_label} SL{i + 1}")
    return headers


def _ub_headers() -> list[str]:
    """Build the ordered list of 178 UB-04 column headers."""
    headers: list[str] = []
    for fd in UB04_FIELDS:
        headers.append(fd.label or fd.name)   # D-01
    for tfd in UB04_TABLE_FIELDS:
        col_label = tfd.label or tfd.name      # D-04
        for i in range(22):                    # D-03: RL1..RL22
            headers.append(f"{col_label} RL{i + 1}")
    return headers


# ---------------------------------------------------------------------------
# Column map builders: field_name -> 1-based column index
# ---------------------------------------------------------------------------

def _cms_col_map() -> dict[str, int]:
    """Build mapping from CMS-1500 field_name to 1-based column index."""
    col: dict[str, int] = {}
    idx = 1
    for fd in CMS1500_FIELDS:
        col[fd.name] = idx
        idx += 1
    for tfd in CMS1500_TABLE_FIELDS:
        for i in range(6):
            col[f"{tfd.name}_sl{i + 1}"] = idx   # matches extractor naming (D-06)
            idx += 1
    return col


def _ub_col_map() -> dict[str, int]:
    """Build mapping from UB-04 field_name to 1-based column index."""
    col: dict[str, int] = {}
    idx = 1
    for fd in UB04_FIELDS:
        col[fd.name] = idx
        idx += 1
    for tfd in UB04_TABLE_FIELDS:
        for i in range(22):
            col[f"{tfd.name}_rl{i + 1}"] = idx   # matches extractor naming (D-07)
            idx += 1
    return col


# ---------------------------------------------------------------------------
# Sheet writing helper
# ---------------------------------------------------------------------------

def _write_sheet(
    ws,
    headers: list[str],
    col_map: dict[str, int],
    field_names_in_order: list[str],
    pages: list[list[FieldResult]],
    threshold: float,
) -> None:
    """Write a single sheet: header row + one data row per page.

    Args:
        ws: openpyxl Worksheet object
        headers: ordered list of column header strings
        col_map: dict mapping field_name -> 1-based column index
        field_names_in_order: ordered list of field names (parallel to col_map)
        pages: list of per-page FieldResult lists
        threshold: confidence threshold below which cells get yellow fill
    """
    # Write header row and set column widths
    for col_idx, header in enumerate(headers, start=1):
        ws.cell(row=1, column=col_idx, value=header)
        ws.column_dimensions[
            openpyxl.utils.get_column_letter(col_idx)
        ].width = 15

    ws.freeze_panes = "A2"

    # Write one data row per page
    for row_idx, page_results in enumerate(pages, start=2):
        # Build field_name -> FieldResult lookup for this page
        result_map: dict[str, FieldResult] = {
            fr.field_name: fr for fr in page_results
        }
        for field_name, col_idx in col_map.items():
            fr = result_map.get(field_name)
            value = fr.value if fr else ""
            confidence = fr.confidence if fr else -1.0

            cell = ws.cell(row=row_idx, column=col_idx, value=value)

            # Text format (D-07, D-08, D-09)
            if _needs_text_format(field_name):
                cell.number_format = "@"

            # Yellow fill for low confidence or -1.0 sentinel (D-04)
            if confidence == -1.0 or confidence < threshold:
                cell.fill = _YELLOW


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
    'CMS-1500' (89 columns) and 'UB-04' (178 columns). Header row frozen at A2,
    all columns width 15. Cells with confidence below threshold (or -1.0 sentinel)
    get yellow fill. Code/date/monetary columns formatted as text to prevent
    Excel auto-conversion.

    Security note: output filename is hardcoded ('extracted_results.xlsx').
    Only the directory comes from settings — prevents path injection via settings
    dict (T-05-02).

    Args:
        cms_pages: Per-page FieldResult lists for CMS-1500 pages. Each inner list
                   is the output of extract_cms1500() for one page.
        ub_pages: Per-page FieldResult lists for UB-04 pages. Each inner list is
                  the output of extract_ub04() for one page.
        settings: Dict from load_settings(). Reads:
                  'confidence_threshold' (default 60) — cells below this are yellow
                  'output_dir' (default Desktop) — directory to save the workbook

    Returns:
        Full output path as str (D-06). Phase 6 passes this to os.startfile().

    Note: If 'extracted_results.xlsx' already exists in output_dir, it is silently
    overwritten (D-05 — silent overwrite accepted per T-05-03).
    """
    threshold = float(settings.get("confidence_threshold", 60))
    output_dir = pathlib.Path(settings.get("output_dir", str(pathlib.Path.home() / "Desktop")))
    output_path = output_dir / "extracted_results.xlsx"   # D-05: hardcoded filename

    cms_headers = _cms_headers()
    ub_headers = _ub_headers()
    cms_col_map = _cms_col_map()
    ub_col_map = _ub_col_map()

    # field_names in column order (passed to _write_sheet for iteration)
    cms_field_names = (
        [fd.name for fd in CMS1500_FIELDS]
        + [f"{tfd.name}_sl{i + 1}" for tfd in CMS1500_TABLE_FIELDS for i in range(6)]
    )
    ub_field_names = (
        [fd.name for fd in UB04_FIELDS]
        + [f"{tfd.name}_rl{i + 1}" for tfd in UB04_TABLE_FIELDS for i in range(22)]
    )

    wb = openpyxl.Workbook()
    wb.remove(wb.active)   # remove default "Sheet"

    ws_cms = wb.create_sheet("CMS-1500")
    _write_sheet(ws_cms, cms_headers, cms_col_map, cms_field_names, cms_pages, threshold)

    ws_ub = wb.create_sheet("UB-04")
    _write_sheet(ws_ub, ub_headers, ub_col_map, ub_field_names, ub_pages, threshold)

    wb.save(str(output_path))
    return str(output_path)   # D-06: return full path as str
