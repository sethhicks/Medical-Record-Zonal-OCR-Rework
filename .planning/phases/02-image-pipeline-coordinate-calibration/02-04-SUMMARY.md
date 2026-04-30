---
phase: 02-image-pipeline-coordinate-calibration
plan: "04"
subsystem: config
tags: [coordinates, ub04, pixel-regions, ocr, field-definitions]

# Dependency graph
requires:
  - phase: 02-image-pipeline-coordinate-calibration
    provides: config/base.py with FieldDef and TableFieldDef dataclass schemas
provides:
  - UB04_FIELDS list of 24 FieldDef entries covering all billing-critical UB-04 single-value fields
  - UB04_TABLE_FIELDS list of 7 TableFieldDef entries each with 22 row_boxes for revenue lines RL1-RL22
affects:
  - pipeline/calibrate.py (imports UB04_FIELDS, UB04_TABLE_FIELDS for overlay rendering)
  - Phase 4 field extractor for UB-04 pages

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "UB-04 coordinate grid: 300 DPI / 2550x3300 px canvas, (left, top, right, bottom) tuples"
    - "Revenue lines use 105-pixel row height (RL1-RL20) with compressed final rows (RL21 85px, RL22 105px)"
    - "whitelist=None for free-text fields; digit/alpha whitelist strings for constrained fields"
    - "psm=6 for multi-line blocks, psm=7 for single-line fields, psm=8 for single-word fields"

key-files:
  created: []
  modified:
    - config/ub04.py

key-decisions:
  - "Coordinates are starting estimates (D-05); visual verification via calibrate.py against test.pdf is required before Phase 4"
  - "UB-04 revenue line table spans y=410 to y=2700 (22 rows x ~105px each)"
  - "non_covered column stops at x=2200 (not 2520) leaving rightmost strip for internal form codes"

patterns-established:
  - "UB-04 coordinate reference: header band y=30-410, revenue table y=410-2700, billing/payer footer y=2700-3050, dx/attending y=3050-3300"

requirements-completed:
  - EXTR-04

# Metrics
duration: 4min
completed: 2026-04-30
---

# Phase 2 Plan 04: UB-04 Coordinate Definitions Summary

**UB04_FIELDS (24 FieldDef) and UB04_TABLE_FIELDS (7 TableFieldDef x 22 rows) populated in config/ub04.py with estimated 300-DPI pixel coordinates for all billing-critical UB-04 form regions**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-04-30T17:14:29Z
- **Completed:** 2026-04-30T17:18:01Z
- **Tasks:** 1 of 1
- **Files modified:** 1

## Accomplishments

- Replaced empty placeholder lists in config/ub04.py with complete coordinate definitions
- 24 single-value FieldDef entries covering provider/patient header, payer footer, and diagnosis/attending bands
- 7 TableFieldDef entries (rev code, description, HCPCS, service date, units, total charges, non-covered), each with exactly 22 row_boxes spanning UB-04 revenue lines RL1-RL22
- Both target tests pass green: test_ub04_fields_populated, test_ub04_table_fields_row_count

## Task Commits

Each task was committed atomically:

1. **Task 1: Populate UB04_FIELDS and UB04_TABLE_FIELDS** - `ea26d16` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `config/ub04.py` - Fully populated with 24 FieldDef + 7 TableFieldDef (22 rows each); replaces empty placeholder lists

## Decisions Made

None - followed plan as specified. Coordinates are estimates per D-05 and D-06; visual calibration against test.pdf is required before Phase 4.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- config/ub04.py is the UB-04 coordinate source of truth (D-06); ready for pipeline/calibrate.py import in plan 02-07
- Coordinates are estimates — **visual verification via `python pipeline/calibrate.py --page N --pdf test.pdf --form ub04` must be done before Phase 4 field extraction**
- The calibrate.py script (plan 02-07) will render these boxes as overlays on real scans; adjust coordinates in config/ub04.py directly after inspection

---
*Phase: 02-image-pipeline-coordinate-calibration*
*Completed: 2026-04-30*

## Self-Check: PASSED

- config/ub04.py: FOUND
- 02-04-SUMMARY.md: FOUND
- Commit ea26d16: FOUND
