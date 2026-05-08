"""CMS-1500 field coordinate definitions.

Estimated pixel coordinates at 300 DPI (2550x3300 px).
Verify with: python pipeline/calibrate.py --page N --pdf test.pdf
Adjust coordinates in this file directly after visual inspection (D-05, D-06).
"""
from config.base import FieldDef, TableFieldDef  # noqa: F401

# ---------------------------------------------------------------------------
# CMS1500_FIELDS — 2 single-value config entries (produce 4 FieldResults)
# All boxes: (left, top, right, bottom) at 300 DPI / 2550x3300 px
#
# patient_name is a wide PSM-11 scan covering the full name+DOB row (y=530-640,
# ±25 px scan jitter).  The extractor parses it with regex to produce three
# FieldResults: patient_last_name, patient_first_name, patient_dob.
# patient_dob is NOT listed here — it comes out of the patient_name scan.
# ---------------------------------------------------------------------------

CMS1500_FIELDS: list[FieldDef] = [
    FieldDef(name="patient_name", box=(30, 530, 1270, 640), psm=11, whitelist=None,             label="Box 2 — Patient Name + DOB row (wide PSM-11 scan)"),
    FieldDef(name="total_charge", box=(1580, 2800, 1980, 2870), psm=7,  whitelist="0123456789. ", label="Box 28 — Total Charge"),
]


# ---------------------------------------------------------------------------
# CMS1500_TABLE_FIELDS — 2 Box 24 sub-fields, 6 service line rows each
# Row y-ranges: SL1(2185–2272), SL2(2272–2359), SL3(2359–2446),
#               SL4(2446–2533), SL5(2533–2620), SL6(2620–2707)
# date_of_service x: 55–180 — skips row-number label (x≈30–55) and To-date column
# ---------------------------------------------------------------------------

CMS1500_TABLE_FIELDS: list[TableFieldDef] = [
    TableFieldDef(
        name="date_of_service",
        row_boxes=[
            (55,  2185, 210, 2272),  # SL1
            (55,  2272, 210, 2359),  # SL2
            (55,  2359, 210, 2446),  # SL3
            (55,  2446, 210, 2533),  # SL4
            (55,  2533, 210, 2620),  # SL5
            (55,  2620, 210, 2707),  # SL6
        ],
        psm=7,
        whitelist="0123456789/ ",
        label="Box 24 — Date of Service (From date only)",
    ),
    TableFieldDef(
        name="cpt_code",
        row_boxes=[
            (780, 2185, 1000, 2272),  # SL1
            (780, 2272, 1000, 2359),  # SL2
            (780, 2359, 1000, 2446),  # SL3
            (780, 2446, 1000, 2533),  # SL4
            (780, 2533, 1000, 2620),  # SL5
            (780, 2620, 1000, 2707),  # SL6
        ],
        psm=7,
        whitelist="0123456789- ",
        label="Box 24 — CPT/HCPCS Code",
    ),
]
