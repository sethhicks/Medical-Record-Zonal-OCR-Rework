"""CMS-1500 field coordinate definitions.

Estimated pixel coordinates at 300 DPI (2550x3300 px).
Verify with: python pipeline/calibrate.py --page N --pdf test.pdf
Adjust coordinates in this file directly after visual inspection (D-05, D-06).
"""
from config.base import FieldDef, TableFieldDef  # noqa: F401

# ---------------------------------------------------------------------------
# CMS1500_FIELDS — 29 single-value fields
# All boxes: (left, top, right, bottom) at 300 DPI / 2550x3300 px
# ---------------------------------------------------------------------------

CMS1500_FIELDS: list[FieldDef] = [
    FieldDef(name="claim_member_id",        box=(30,  160, 1200, 220), psm=7, whitelist=None,                    label="Claim/Member ID"),
    FieldDef(name="box1_insurance_type",    box=(30,  220,  800, 270), psm=7, whitelist=None,                    label="Box 1 — Insurance Type"),
    FieldDef(name="box1a_insured_id",       box=(1270, 220, 2520, 270), psm=7, whitelist=None,                   label="Box 1a — Insured ID"),
    FieldDef(name="box2_patient_name",      box=(30,  270, 1270, 320), psm=7, whitelist=None,                    label="Box 2 — Patient Name"),
    FieldDef(name="box3_dob_sex",           box=(1270, 270, 2000, 320), psm=7, whitelist="0123456789/MF ",        label="Box 3 — DOB / Sex"),
    FieldDef(name="box5_patient_address",   box=(30,  320, 1270, 460), psm=6, whitelist=None,                    label="Box 5 — Patient Address"),
    FieldDef(name="box17_referring_name",   box=(30,  850, 1270, 900), psm=7, whitelist=None,                    label="Box 17 — Referring Provider"),
    FieldDef(name="box17b_referring_npi",   box=(1270, 850, 2000, 900), psm=7, whitelist="0123456789",           label="Box 17b — Referring NPI"),
    FieldDef(name="box19_additional_claim", box=(30,  900, 2520, 950), psm=7, whitelist=None,                    label="Box 19 — Additional Claim Info"),
    FieldDef(name="box21a_diag",            box=(30,  960,  200, 1010), psm=7, whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789. ", label="Box 21a — Diagnosis A"),
    FieldDef(name="box21b_diag",            box=(200, 960,  370, 1010), psm=7, whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789. ", label="Box 21b — Diagnosis B"),
    FieldDef(name="box21c_diag",            box=(370, 960,  540, 1010), psm=7, whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789. ", label="Box 21c — Diagnosis C"),
    FieldDef(name="box21d_diag",            box=(540, 960,  710, 1010), psm=7, whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789. ", label="Box 21d — Diagnosis D"),
    FieldDef(name="box21e_diag",            box=(30,  1010, 200, 1060), psm=7, whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789. ", label="Box 21e — Diagnosis E"),
    FieldDef(name="box21f_diag",            box=(200, 1010, 370, 1060), psm=7, whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789. ", label="Box 21f — Diagnosis F"),
    FieldDef(name="box21g_diag",            box=(370, 1010, 540, 1060), psm=7, whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789. ", label="Box 21g — Diagnosis G"),
    FieldDef(name="box21h_diag",            box=(540, 1010, 710, 1060), psm=7, whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789. ", label="Box 21h — Diagnosis H"),
    FieldDef(name="box21i_diag",            box=(710, 960,  880, 1010), psm=7, whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789. ", label="Box 21i — Diagnosis I"),
    FieldDef(name="box21j_diag",            box=(880, 960, 1050, 1010), psm=7, whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789. ", label="Box 21j — Diagnosis J"),
    FieldDef(name="box21k_diag",            box=(1050, 960, 1220, 1010), psm=7, whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789. ", label="Box 21k — Diagnosis K"),
    FieldDef(name="box21l_diag",            box=(1220, 960, 1390, 1010), psm=7, whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789. ", label="Box 21l — Diagnosis L"),
    FieldDef(name="box23_prior_auth",       box=(930, 1060, 1850, 1110), psm=7, whitelist="0123456789 ",         label="Box 23 — Prior Auth Number"),
    FieldDef(name="box25_federal_tax_id",   box=(30,  2590, 700,  2640), psm=7, whitelist="0123456789- ",        label="Box 25 — Federal Tax ID"),
    FieldDef(name="box26_patient_account",  box=(700, 2590, 1270, 2640), psm=7, whitelist=None,                  label="Box 26 — Patient Account No."),
    FieldDef(name="box27_accept_assignment",box=(1270, 2590, 1630, 2640), psm=8, whitelist=None,                 label="Box 27 — Accept Assignment"),
    FieldDef(name="box28_total_charge",     box=(1630, 2590, 2000, 2640), psm=7, whitelist="0123456789. ",       label="Box 28 — Total Charge"),
    FieldDef(name="box29_amount_paid",      box=(2000, 2590, 2300, 2640), psm=7, whitelist="0123456789. ",       label="Box 29 — Amount Paid"),
    FieldDef(name="box32_service_facility", box=(30,  2900, 1270, 3040), psm=6, whitelist=None,                  label="Box 32 — Service Facility"),
    FieldDef(name="box33_billing_provider", box=(1270, 2900, 2520, 3040), psm=6, whitelist=None,                 label="Box 33 — Billing Provider"),
]


# ---------------------------------------------------------------------------
# CMS1500_TABLE_FIELDS — 10 Box 24 sub-fields, 6 service line rows each
# Row y-ranges: SL1(1130–1280), SL2(1280–1430), SL3(1430–1580),
#               SL4(1580–1730), SL5(1730–1880), SL6(1880–2030)
# ---------------------------------------------------------------------------

CMS1500_TABLE_FIELDS: list[TableFieldDef] = [
    TableFieldDef(
        name="box24_date_from",
        row_boxes=[
            (30,  1130, 220, 1280),  # SL1
            (30,  1280, 220, 1430),  # SL2
            (30,  1430, 220, 1580),  # SL3
            (30,  1580, 220, 1730),  # SL4
            (30,  1730, 220, 1880),  # SL5
            (30,  1880, 220, 2030),  # SL6
        ],
        psm=7,
        whitelist="0123456789/ ",
        label="Box 24 — Date From",
    ),
    TableFieldDef(
        name="box24_date_to",
        row_boxes=[
            (220, 1130, 410, 1280),  # SL1
            (220, 1280, 410, 1430),  # SL2
            (220, 1430, 410, 1580),  # SL3
            (220, 1580, 410, 1730),  # SL4
            (220, 1730, 410, 1880),  # SL5
            (220, 1880, 410, 2030),  # SL6
        ],
        psm=7,
        whitelist="0123456789/ ",
        label="Box 24 — Date To",
    ),
    TableFieldDef(
        name="box24_pos",
        row_boxes=[
            (410, 1130, 500, 1280),  # SL1
            (410, 1280, 500, 1430),  # SL2
            (410, 1430, 500, 1580),  # SL3
            (410, 1580, 500, 1730),  # SL4
            (410, 1730, 500, 1880),  # SL5
            (410, 1880, 500, 2030),  # SL6
        ],
        psm=7,
        whitelist="0123456789",
        label="Box 24 — Place of Service",
    ),
    TableFieldDef(
        name="box24_emg",
        row_boxes=[
            (500, 1130, 560, 1280),  # SL1
            (500, 1280, 560, 1430),  # SL2
            (500, 1430, 560, 1580),  # SL3
            (500, 1580, 560, 1730),  # SL4
            (500, 1730, 560, 1880),  # SL5
            (500, 1880, 560, 2030),  # SL6
        ],
        psm=8,
        whitelist="0123456789YN",
        label="Box 24 — EMG",
    ),
    TableFieldDef(
        name="box24_cpt",
        row_boxes=[
            (560, 1130, 780, 1280),  # SL1
            (560, 1280, 780, 1430),  # SL2
            (560, 1430, 780, 1580),  # SL3
            (560, 1580, 780, 1730),  # SL4
            (560, 1730, 780, 1880),  # SL5
            (560, 1880, 780, 2030),  # SL6
        ],
        psm=7,
        whitelist="0123456789- ",
        label="Box 24 — CPT/HCPCS",
    ),
    TableFieldDef(
        name="box24_modifier",
        row_boxes=[
            (780, 1130, 950, 1280),  # SL1
            (780, 1280, 950, 1430),  # SL2
            (780, 1430, 950, 1580),  # SL3
            (780, 1580, 950, 1730),  # SL4
            (780, 1730, 950, 1880),  # SL5
            (780, 1880, 950, 2030),  # SL6
        ],
        psm=7,
        whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ",
        label="Box 24 — Modifier",
    ),
    TableFieldDef(
        name="box24_diag_ptr",
        row_boxes=[
            (950,  1130, 1080, 1280),  # SL1
            (950,  1280, 1080, 1430),  # SL2
            (950,  1430, 1080, 1580),  # SL3
            (950,  1580, 1080, 1730),  # SL4
            (950,  1730, 1080, 1880),  # SL5
            (950,  1880, 1080, 2030),  # SL6
        ],
        psm=7,
        whitelist="ABCDEFGHIJKL ",
        label="Box 24 — Diagnosis Pointer",
    ),
    TableFieldDef(
        name="box24_charges",
        row_boxes=[
            (1080, 1130, 1270, 1280),  # SL1
            (1080, 1280, 1270, 1430),  # SL2
            (1080, 1430, 1270, 1580),  # SL3
            (1080, 1580, 1270, 1730),  # SL4
            (1080, 1730, 1270, 1880),  # SL5
            (1080, 1880, 1270, 2030),  # SL6
        ],
        psm=7,
        whitelist="0123456789. ",
        label="Box 24 — Charges",
    ),
    TableFieldDef(
        name="box24_units",
        row_boxes=[
            (1270, 1130, 1450, 1280),  # SL1
            (1270, 1280, 1450, 1430),  # SL2
            (1270, 1430, 1450, 1580),  # SL3
            (1270, 1580, 1450, 1730),  # SL4
            (1270, 1730, 1450, 1880),  # SL5
            (1270, 1880, 1450, 2030),  # SL6
        ],
        psm=7,
        whitelist="0123456789",
        label="Box 24 — Days/Units",
    ),
    TableFieldDef(
        name="box24_rendering_npi",
        row_boxes=[
            (1830, 1130, 2520, 1280),  # SL1
            (1830, 1280, 2520, 1430),  # SL2
            (1830, 1430, 2520, 1580),  # SL3
            (1830, 1580, 2520, 1730),  # SL4
            (1830, 1730, 2520, 1880),  # SL5
            (1830, 1880, 2520, 2030),  # SL6
        ],
        psm=7,
        whitelist="0123456789",
        label="Box 24 — Rendering Provider NPI",
    ),
]
