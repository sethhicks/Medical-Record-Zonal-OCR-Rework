"""CMS-1500 field coordinate definitions.

Estimated pixel coordinates at 300 DPI (2550x3300 px).
Verify with: python pipeline/calibrate.py --page N --pdf test.pdf
Adjust coordinates in this file directly after visual inspection (D-05, D-06).
"""
from config.base import FieldDef, TableFieldDef  # noqa: F401

# ---------------------------------------------------------------------------
# CMS1500_FIELDS — 2 single-value config entries (produce 3 FieldResults)
# All boxes: (left, top, right, bottom) at 300 DPI / 2550x3300 px
#
# patient_name is a wide PSM-11 scan covering the full name+DOB row (y=530-640,
# ±25 px scan jitter).  The extractor parses it with regex to produce two
# FieldResults: patient_last_name, patient_first_name.
# ---------------------------------------------------------------------------

CMS1500_FIELDS: list[FieldDef] = [
    FieldDef(name="patient_name", box=(70, 540, 920, 610), psm=6, whitelist=None,             label="Box 2 — Patient Name row"),
    FieldDef(name="total_charge", box=(1590, 2800, 1850, 2860), psm=7,  whitelist="0123456789. ", label="Box 28 — Total Charge"),
]


# ---------------------------------------------------------------------------
# CMS1500_TABLE_FIELDS — 1 Box 24 sub-field, service line 1 only
# SL1 is always the first and most reliably filled row on every claim.
# ---------------------------------------------------------------------------

CMS1500_TABLE_FIELDS: list[TableFieldDef] = [
    TableFieldDef(
        name="date_of_service",
        row_boxes=[
            (60, 2185, 320, 2280),  # SL1 only
        ],
        psm=7,
        whitelist="0123456789/ ",
        label="Box 24 — Date of Service",
    ),
]
