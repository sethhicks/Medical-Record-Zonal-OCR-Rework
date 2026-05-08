"""UB-04 field coordinate definitions.

Estimated pixel coordinates at 300 DPI (2550x3300 px).
Verify with: python pipeline/calibrate.py --page N --pdf test.pdf --form ub04
Adjust coordinates in this file directly after visual inspection (D-05, D-06).
"""
from config.base import FieldDef, TableFieldDef  # noqa: F401

# ---------------------------------------------------------------------------
# UB04_FIELDS — 3 single-value config entries (produce 4 FieldResults)
# All boxes: (left, top, right, bottom) at 300 DPI / 2550x3300 px
#
# patient_name: wide PSM-11 band covering ±30px scan jitter; regex in extractor
#   finds the LAST "Last, First" pattern to skip form label text.
# patient_dob: LEFT side of form (Box 10); no whitelist — regex extracts date.
# total_charge: reads the "EST. AMOUNT DUE" row which is the cleanest numeric
#   region on these scans (conf≈96 vs noise at the TOTALS row).
# ---------------------------------------------------------------------------

UB04_FIELDS: list[FieldDef] = [
    FieldDef(name="patient_name", box=(30,  230, 1270,  360), psm=11, whitelist=None,            label="Box 8 — Patient Name (wide PSM-11 scan)"),
    FieldDef(name="patient_dob",  box=(30,  363,  700,  450), psm=11, whitelist="0123456789/ ", label="Box 10 — Birthdate (LEFT side; extractor retries +15px if miss)"),
    FieldDef(name="total_charge", box=(1700, 2060, 2300, 2150), psm=7, whitelist="0123456789. ", label="EST. Amount Due row — Total Charges proxy"),
]


# ---------------------------------------------------------------------------
# UB04_TABLE_FIELDS — 1 revenue line sub-field, 22 rows
# Revenue section starts at y≈860 (first data row after column headers at y≈790).
# Row height: 47px.  Column 45 (SERV DATE): x=1000–1270.
# Note: column 45 is blank on inpatient claims; present for outpatient claims.
# ---------------------------------------------------------------------------

UB04_TABLE_FIELDS: list[TableFieldDef] = [
    TableFieldDef(
        name="date_of_service",
        row_boxes=[
            (1000,  860, 1270,  907),  # RL1
            (1000,  907, 1270,  954),  # RL2
            (1000,  954, 1270, 1001),  # RL3
            (1000, 1001, 1270, 1048),  # RL4
            (1000, 1048, 1270, 1095),  # RL5
            (1000, 1095, 1270, 1142),  # RL6
            (1000, 1142, 1270, 1189),  # RL7
            (1000, 1189, 1270, 1236),  # RL8
            (1000, 1236, 1270, 1283),  # RL9
            (1000, 1283, 1270, 1330),  # RL10
            (1000, 1330, 1270, 1377),  # RL11
            (1000, 1377, 1270, 1424),  # RL12
            (1000, 1424, 1270, 1471),  # RL13
            (1000, 1471, 1270, 1518),  # RL14
            (1000, 1518, 1270, 1565),  # RL15
            (1000, 1565, 1270, 1612),  # RL16
            (1000, 1612, 1270, 1659),  # RL17
            (1000, 1659, 1270, 1706),  # RL18
            (1000, 1706, 1270, 1753),  # RL19
            (1000, 1753, 1270, 1800),  # RL20
            (1000, 1800, 1270, 1847),  # RL21
            (1000, 1847, 1270, 1894),  # RL22
        ],
        psm=7,
        whitelist="0123456789/ ",
        label="UB-04 Revenue Line — Service Date (col 45)",
    ),
]
