"""UB-04 field coordinate definitions.

Estimated pixel coordinates at 300 DPI (2550x3300 px).
Verify with: python pipeline/calibrate.py --page N --pdf test.pdf --form ub04
Adjust coordinates in this file directly after visual inspection (D-05, D-06).
"""
from config.base import FieldDef, TableFieldDef  # noqa: F401

# ---------------------------------------------------------------------------
# UB04_FIELDS — 2 single-value config entries (produce 3 FieldResults)
# All boxes: (left, top, right, bottom) at 300 DPI / 2550x3300 px
#
# patient_name: wide PSM-11 band covering ±30px scan jitter; regex in extractor
#   finds the LAST "Last, First" pattern to skip form label text.  Produces two
#   FieldResults: patient_last_name, patient_first_name.
# total_charge: reads the "EST. AMOUNT DUE" row which is the cleanest numeric
#   region on these scans (conf≈96 vs noise at the TOTALS row).
# ---------------------------------------------------------------------------

UB04_FIELDS: list[FieldDef] = [
    FieldDef(name="patient_name", box=(80, 320, 930, 370), psm=6,  whitelist=None,             label="Box 8 — Patient Name row"),
    FieldDef(name="total_charge", box=(1700, 1975, 2130, 2040), psm=8,  whitelist="0123456789. ", label="Line 47 Total Charges (primary zone; fallback at y+30 in extractor)"),
]


# ---------------------------------------------------------------------------
# UB04_TABLE_FIELDS — 1 revenue line sub-field, row 1 only
# RL1 is always the first and most reliably filled row on every claim.
# Column 45 (SERV DATE): x=1000–1270; row 1 y=860–907.
# ---------------------------------------------------------------------------

UB04_TABLE_FIELDS: list[TableFieldDef] = [
    TableFieldDef(
        name="date_of_service",
        row_boxes=[
            (330, 400, 560, 455),  # RL1 only — Box 45 SERV DATE, shifted 20px up from original calibration
        ],
        psm=7,
        whitelist="0123456789/ ",
        label="UB-04 Revenue Line — Service Date",
    ),
]
