"""UB-04 field coordinate definitions.

Estimated pixel coordinates at 300 DPI (2550x3300 px).
Verify with: python pipeline/calibrate.py --page N --pdf test.pdf --form ub04
Adjust coordinates in this file directly after visual inspection (D-05, D-06).
"""
from config.base import FieldDef, TableFieldDef  # noqa: F401

# ---------------------------------------------------------------------------
# UB04_FIELDS — 24 single-value fields
# All boxes: (left, top, right, bottom) at 300 DPI / 2550x3300 px
# ---------------------------------------------------------------------------

UB04_FIELDS: list[FieldDef] = [
    FieldDef(name="box1_provider_name_addr",  box=(30,   30,  1270, 200),  psm=6, whitelist=None,                                         label="Box 1 — Provider Name/Address"),
    FieldDef(name="box3b_patient_control",    box=(30,  200,   700, 270),  psm=7, whitelist=None,                                         label="Box 3b — Patient Control Number"),
    FieldDef(name="box4_type_of_bill",        box=(700,  200,  1100, 270), psm=7, whitelist="0123456789",                                 label="Box 4 — Type of Bill"),
    FieldDef(name="box5_federal_tax",         box=(1100, 200,  1800, 270), psm=7, whitelist="0123456789- ",                               label="Box 5 — Federal Tax Number"),
    FieldDef(name="box6_statement_period",    box=(1800, 200,  2520, 270), psm=7, whitelist="0123456789/ ",                               label="Box 6 — Statement Period"),
    FieldDef(name="box8_patient_name",        box=(30,  270,  1270, 340),  psm=7, whitelist=None,                                         label="Box 8 — Patient Name"),
    FieldDef(name="box9_patient_address",     box=(30,  340,  1270, 410),  psm=6, whitelist=None,                                         label="Box 9 — Patient Address"),
    FieldDef(name="box10_birthdate",          box=(1270, 270,  1800, 340), psm=7, whitelist="0123456789/ ",                               label="Box 10 — Birthdate"),
    FieldDef(name="box11_sex",                box=(1800, 270,  2100, 340), psm=8, whitelist="MFU ",                                       label="Box 11 — Sex"),
    FieldDef(name="box12_admission_date",     box=(2100, 270,  2520, 340), psm=7, whitelist="0123456789/ ",                               label="Box 12 — Admission Date"),
    FieldDef(name="box14_admission_type",     box=(1270, 340,  1800, 410), psm=7, whitelist="0123456789",                                 label="Box 14 — Type of Admission"),
    FieldDef(name="box17_patient_status",     box=(1800, 340,  2520, 410), psm=7, whitelist="0123456789",                                 label="Box 17 — Patient Status"),
    FieldDef(name="box50_payer_name",         box=(30,  2700,  800, 2850), psm=6, whitelist=None,                                         label="Box 50 — Payer Name"),
    FieldDef(name="box51_health_plan_id",     box=(800,  2700, 1500, 2850), psm=6, whitelist=None,                                        label="Box 51 — Health Plan ID"),
    FieldDef(name="box54_prior_payments",     box=(1500, 2700, 1900, 2850), psm=7, whitelist="0123456789. ",                              label="Box 54 — Prior Payments"),
    FieldDef(name="box55_est_amount_due",     box=(1900, 2700, 2300, 2850), psm=7, whitelist="0123456789. ",                              label="Box 55 — Est. Amount Due"),
    FieldDef(name="box56_npi",                box=(2300, 2700, 2520, 2850), psm=7, whitelist="0123456789",                                label="Box 56 — NPI"),
    FieldDef(name="box58_insured_name",       box=(30,  2850,  900, 2950), psm=7, whitelist=None,                                         label="Box 58 — Insured Name"),
    FieldDef(name="box60_insured_unique_id",  box=(900,  2850, 1600, 2950), psm=7, whitelist=None,                                        label="Box 60 — Insured Unique ID"),
    FieldDef(name="box61_group_name",         box=(1600, 2850, 2200, 2950), psm=7, whitelist=None,                                        label="Box 61 — Group Name"),
    FieldDef(name="box63_treatment_auth",     box=(30,  2950,  900, 3050), psm=6, whitelist=None,                                         label="Box 63 — Treatment Auth Codes"),
    FieldDef(name="box64_doc_control",        box=(900,  2950, 1600, 3050), psm=7, whitelist=None,                                        label="Box 64 — Document Control Number"),
    FieldDef(name="box66_dx_codes",           box=(30,  3050, 2520, 3200), psm=6, whitelist="0123456789. ABCDEFGHIJKLMNOPQRSTUVWXYZ",    label="Box 66–75 — Diagnosis/Procedure Codes"),
    FieldDef(name="box76_attending_npi_name", box=(30,  3200, 2520, 3300), psm=6, whitelist=None,                                         label="Box 76 — Attending Provider NPI/Name"),
]


# ---------------------------------------------------------------------------
# UB04_TABLE_FIELDS — 7 revenue line sub-fields, 22 rows each
# Row y-ranges (top, bottom): RL1(410,515), RL2(515,620), RL3(620,725),
#   RL4(725,830), RL5(830,935), RL6(935,1040), RL7(1040,1145),
#   RL8(1145,1250), RL9(1250,1355), RL10(1355,1460), RL11(1460,1565),
#   RL12(1565,1670), RL13(1670,1775), RL14(1775,1880), RL15(1880,1985),
#   RL16(1985,2090), RL17(2090,2195), RL18(2195,2300), RL19(2300,2405),
#   RL20(2405,2510), RL21(2510,2595), RL22(2595,2700)
# ---------------------------------------------------------------------------

UB04_TABLE_FIELDS: list[TableFieldDef] = [
    TableFieldDef(
        name="ub04_rl_rev_code",
        row_boxes=[
            (30,  410,  200,  515),   # RL1
            (30,  515,  200,  620),   # RL2
            (30,  620,  200,  725),   # RL3
            (30,  725,  200,  830),   # RL4
            (30,  830,  200,  935),   # RL5
            (30,  935,  200, 1040),   # RL6
            (30, 1040,  200, 1145),   # RL7
            (30, 1145,  200, 1250),   # RL8
            (30, 1250,  200, 1355),   # RL9
            (30, 1355,  200, 1460),   # RL10
            (30, 1460,  200, 1565),   # RL11
            (30, 1565,  200, 1670),   # RL12
            (30, 1670,  200, 1775),   # RL13
            (30, 1775,  200, 1880),   # RL14
            (30, 1880,  200, 1985),   # RL15
            (30, 1985,  200, 2090),   # RL16
            (30, 2090,  200, 2195),   # RL17
            (30, 2195,  200, 2300),   # RL18
            (30, 2300,  200, 2405),   # RL19
            (30, 2405,  200, 2510),   # RL20
            (30, 2510,  200, 2595),   # RL21
            (30, 2595,  200, 2700),   # RL22
        ],
        psm=7,
        whitelist="0123456789",
        label="UB-04 Revenue Line — Rev Code",
    ),
    TableFieldDef(
        name="ub04_rl_description",
        row_boxes=[
            (200,  410,  700,  515),  # RL1
            (200,  515,  700,  620),  # RL2
            (200,  620,  700,  725),  # RL3
            (200,  725,  700,  830),  # RL4
            (200,  830,  700,  935),  # RL5
            (200,  935,  700, 1040),  # RL6
            (200, 1040,  700, 1145),  # RL7
            (200, 1145,  700, 1250),  # RL8
            (200, 1250,  700, 1355),  # RL9
            (200, 1355,  700, 1460),  # RL10
            (200, 1460,  700, 1565),  # RL11
            (200, 1565,  700, 1670),  # RL12
            (200, 1670,  700, 1775),  # RL13
            (200, 1775,  700, 1880),  # RL14
            (200, 1880,  700, 1985),  # RL15
            (200, 1985,  700, 2090),  # RL16
            (200, 2090,  700, 2195),  # RL17
            (200, 2195,  700, 2300),  # RL18
            (200, 2300,  700, 2405),  # RL19
            (200, 2405,  700, 2510),  # RL20
            (200, 2510,  700, 2595),  # RL21
            (200, 2595,  700, 2700),  # RL22
        ],
        psm=7,
        whitelist=None,
        label="UB-04 Revenue Line — Description",
    ),
    TableFieldDef(
        name="ub04_rl_hcpcs",
        row_boxes=[
            (700,  410, 1000,  515),  # RL1
            (700,  515, 1000,  620),  # RL2
            (700,  620, 1000,  725),  # RL3
            (700,  725, 1000,  830),  # RL4
            (700,  830, 1000,  935),  # RL5
            (700,  935, 1000, 1040),  # RL6
            (700, 1040, 1000, 1145),  # RL7
            (700, 1145, 1000, 1250),  # RL8
            (700, 1250, 1000, 1355),  # RL9
            (700, 1355, 1000, 1460),  # RL10
            (700, 1460, 1000, 1565),  # RL11
            (700, 1565, 1000, 1670),  # RL12
            (700, 1670, 1000, 1775),  # RL13
            (700, 1775, 1000, 1880),  # RL14
            (700, 1880, 1000, 1985),  # RL15
            (700, 1985, 1000, 2090),  # RL16
            (700, 2090, 1000, 2195),  # RL17
            (700, 2195, 1000, 2300),  # RL18
            (700, 2300, 1000, 2405),  # RL19
            (700, 2405, 1000, 2510),  # RL20
            (700, 2510, 1000, 2595),  # RL21
            (700, 2595, 1000, 2700),  # RL22
        ],
        psm=7,
        whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ",
        label="UB-04 Revenue Line — HCPCS",
    ),
    TableFieldDef(
        name="ub04_rl_svc_date",
        row_boxes=[
            (1000,  410, 1270,  515),  # RL1
            (1000,  515, 1270,  620),  # RL2
            (1000,  620, 1270,  725),  # RL3
            (1000,  725, 1270,  830),  # RL4
            (1000,  830, 1270,  935),  # RL5
            (1000,  935, 1270, 1040),  # RL6
            (1000, 1040, 1270, 1145),  # RL7
            (1000, 1145, 1270, 1250),  # RL8
            (1000, 1250, 1270, 1355),  # RL9
            (1000, 1355, 1270, 1460),  # RL10
            (1000, 1460, 1270, 1565),  # RL11
            (1000, 1565, 1270, 1670),  # RL12
            (1000, 1670, 1270, 1775),  # RL13
            (1000, 1775, 1270, 1880),  # RL14
            (1000, 1880, 1270, 1985),  # RL15
            (1000, 1985, 1270, 2090),  # RL16
            (1000, 2090, 1270, 2195),  # RL17
            (1000, 2195, 1270, 2300),  # RL18
            (1000, 2300, 1270, 2405),  # RL19
            (1000, 2405, 1270, 2510),  # RL20
            (1000, 2510, 1270, 2595),  # RL21
            (1000, 2595, 1270, 2700),  # RL22
        ],
        psm=7,
        whitelist="0123456789/ ",
        label="UB-04 Revenue Line — Service Date",
    ),
    TableFieldDef(
        name="ub04_rl_units",
        row_boxes=[
            (1270,  410, 1500,  515),  # RL1
            (1270,  515, 1500,  620),  # RL2
            (1270,  620, 1500,  725),  # RL3
            (1270,  725, 1500,  830),  # RL4
            (1270,  830, 1500,  935),  # RL5
            (1270,  935, 1500, 1040),  # RL6
            (1270, 1040, 1500, 1145),  # RL7
            (1270, 1145, 1500, 1250),  # RL8
            (1270, 1250, 1500, 1355),  # RL9
            (1270, 1355, 1500, 1460),  # RL10
            (1270, 1460, 1500, 1565),  # RL11
            (1270, 1565, 1500, 1670),  # RL12
            (1270, 1670, 1500, 1775),  # RL13
            (1270, 1775, 1500, 1880),  # RL14
            (1270, 1880, 1500, 1985),  # RL15
            (1270, 1985, 1500, 2090),  # RL16
            (1270, 2090, 1500, 2195),  # RL17
            (1270, 2195, 1500, 2300),  # RL18
            (1270, 2300, 1500, 2405),  # RL19
            (1270, 2405, 1500, 2510),  # RL20
            (1270, 2510, 1500, 2595),  # RL21
            (1270, 2595, 1500, 2700),  # RL22
        ],
        psm=7,
        whitelist="0123456789",
        label="UB-04 Revenue Line — Units",
    ),
    TableFieldDef(
        name="ub04_rl_total_charges",
        row_boxes=[
            (1500,  410, 1900,  515),  # RL1
            (1500,  515, 1900,  620),  # RL2
            (1500,  620, 1900,  725),  # RL3
            (1500,  725, 1900,  830),  # RL4
            (1500,  830, 1900,  935),  # RL5
            (1500,  935, 1900, 1040),  # RL6
            (1500, 1040, 1900, 1145),  # RL7
            (1500, 1145, 1900, 1250),  # RL8
            (1500, 1250, 1900, 1355),  # RL9
            (1500, 1355, 1900, 1460),  # RL10
            (1500, 1460, 1900, 1565),  # RL11
            (1500, 1565, 1900, 1670),  # RL12
            (1500, 1670, 1900, 1775),  # RL13
            (1500, 1775, 1900, 1880),  # RL14
            (1500, 1880, 1900, 1985),  # RL15
            (1500, 1985, 1900, 2090),  # RL16
            (1500, 2090, 1900, 2195),  # RL17
            (1500, 2195, 1900, 2300),  # RL18
            (1500, 2300, 1900, 2405),  # RL19
            (1500, 2405, 1900, 2510),  # RL20
            (1500, 2510, 1900, 2595),  # RL21
            (1500, 2595, 1900, 2700),  # RL22
        ],
        psm=7,
        whitelist="0123456789. ",
        label="UB-04 Revenue Line — Total Charges",
    ),
    TableFieldDef(
        name="ub04_rl_non_covered",
        row_boxes=[
            (1900,  410, 2200,  515),  # RL1
            (1900,  515, 2200,  620),  # RL2
            (1900,  620, 2200,  725),  # RL3
            (1900,  725, 2200,  830),  # RL4
            (1900,  830, 2200,  935),  # RL5
            (1900,  935, 2200, 1040),  # RL6
            (1900, 1040, 2200, 1145),  # RL7
            (1900, 1145, 2200, 1250),  # RL8
            (1900, 1250, 2200, 1355),  # RL9
            (1900, 1355, 2200, 1460),  # RL10
            (1900, 1460, 2200, 1565),  # RL11
            (1900, 1565, 2200, 1670),  # RL12
            (1900, 1670, 2200, 1775),  # RL13
            (1900, 1775, 2200, 1880),  # RL14
            (1900, 1880, 2200, 1985),  # RL15
            (1900, 1985, 2200, 2090),  # RL16
            (1900, 2090, 2200, 2195),  # RL17
            (1900, 2195, 2200, 2300),  # RL18
            (1900, 2300, 2200, 2405),  # RL19
            (1900, 2405, 2200, 2510),  # RL20
            (1900, 2510, 2200, 2595),  # RL21
            (1900, 2595, 2200, 2700),  # RL22
        ],
        psm=7,
        whitelist="0123456789. ",
        label="UB-04 Revenue Line — Non-Covered",
    ),
]
