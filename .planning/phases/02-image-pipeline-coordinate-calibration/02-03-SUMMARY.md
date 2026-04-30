---
phase: 02-image-pipeline-coordinate-calibration
plan: "03"
subsystem: config
tags: [tesseract, psm, pixel-coordinates, cms1500, ocr, field-extraction]

# Dependency graph
requires:
  - phase: 02-image-pipeline-coordinate-calibration
    provides: FieldDef and TableFieldDef dataclasses (config/base.py) from plan 02-01
provides:
  - CMS1500_FIELDS — 29 FieldDef entries covering all CMS-1500 billing fields at 300 DPI
  - CMS1500_TABLE_FIELDS — 10 TableFieldDef entries for Box 24 service lines (6 rows each)
affects:
  - 02-07-calibrate (imports CMS1500_FIELDS/CMS1500_TABLE_FIELDS for overlay rendering)
  - 04-field-extraction (imports CMS1500_FIELDS/CMS1500_TABLE_FIELDS for OCR region cropping)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - FieldDef with (left, top, right, bottom) 4-tuple box at 300 DPI / 2550x3300 px
    - TableFieldDef with list of 6 row_box tuples for repeating service line rows
    - psm=7 (single line) default for most fields; psm=6 (block) for multi-line address fields; psm=8 (word) for checkbox fields
    - whitelist=None for free-text fields; numeric/alpha whitelists for structured fields

key-files:
  created: []
  modified:
    - config/cms1500.py

key-decisions:
  - "Coordinates are starting estimates per D-05; user must verify visually with calibrate.py overlay against test.pdf before Phase 4"
  - "CMS1500_FIELDS is the sole source of truth for CMS-1500 field regions per D-06; no coordinate duplication elsewhere"
  - "psm=6 used for multi-line address boxes (box5, box32, box33); psm=7 for single-line fields; psm=8 for single-word checkbox fields"

patterns-established:
  - "CMS1500_FIELDS pattern: FieldDef(name=snake_case_box_name, box=(l,t,r,b), psm=N, whitelist=chars_or_None, label=human_readable)"
  - "CMS1500_TABLE_FIELDS pattern: TableFieldDef(name=..., row_boxes=[6 tuples], psm=7, whitelist=..., label=...)"

requirements-completed:
  - EXTR-04

# Metrics
duration: 7min
completed: 2026-04-30
---

# Phase 2 Plan 03: CMS-1500 Coordinate Config Summary

**29 FieldDef entries and 10 TableFieldDef entries (6 rows each) populated in config/cms1500.py as the sole coordinate source of truth for CMS-1500 OCR field extraction at 300 DPI**

## Performance

- **Duration:** 7 min
- **Started:** 2026-04-30T17:05:32Z
- **Completed:** 2026-04-30T17:12:30Z
- **Tasks:** 1 of 1
- **Files modified:** 1

## Accomplishments

- Replaced stub empty lists in config/cms1500.py with fully populated coordinate definitions
- 29 FieldDef entries cover all CMS-1500 billing-critical fields (claim ID, boxes 1–33 per PROJECT.md)
- 10 TableFieldDef entries for Box 24 sub-fields each with exactly 6 row_boxes covering service lines SL1–SL6 (y-ranges 1130–2030)
- Both target tests pass green: test_cms1500_fields_populated and test_cms1500_table_fields_row_count

## Task Commits

1. **Task 1: Populate CMS1500_FIELDS and CMS1500_TABLE_FIELDS** — `fa25473` (feat)

**Plan metadata:** (committed below)

## Files Created/Modified

- `config/cms1500.py` — Replaced empty lists with 29 FieldDef + 10 TableFieldDef coordinate definitions

## Decisions Made

- Coordinates follow RESEARCH.md §4.1 and §4.2 estimates; they are starting values to be adjusted after visual verification with calibrate.py overlay (D-05)
- config/cms1500.py is the sole coordinate source of truth (D-06) — pipeline/calibrate.py and Phase 4 extractor both import from here
- psm assignments: psm=6 for multi-line address regions (box5_patient_address, box32_service_facility, box33_billing_provider); psm=8 for single-word checkbox field (box27_accept_assignment); psm=7 for all other single-line fields

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- config/cms1500.py is ready for import by pipeline/calibrate.py (plan 02-07) which will render the coordinate overlay
- User must visually verify coordinates against test.pdf using the calibration overlay before Phase 4 field extraction begins (D-05 hard gate per CLAUDE.md)
- No blockers for plans 02-04 through 02-07

---
*Phase: 02-image-pipeline-coordinate-calibration*
*Completed: 2026-04-30*

## Self-Check: PASSED

- config/cms1500.py: FOUND
- 02-03-SUMMARY.md: FOUND
- commit fa25473: FOUND
