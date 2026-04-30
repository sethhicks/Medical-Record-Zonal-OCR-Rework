---
phase: 02-image-pipeline-coordinate-calibration
plan: 02
subsystem: config
tags: [python, config_loader, settings, threshold_block_size, adaptive-threshold]

# Dependency graph
requires:
  - phase: 02-01
    provides: test_phase2.py with test_settings_threshold_block_size_default test stub
provides:
  - threshold_block_size=31 in _DEFAULTS of config_loader.py
  - settings-driven tunable for OpenCV adaptive threshold block size
affects:
  - 02-06 (pipeline/preprocessor.py reads threshold_block_size from settings)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Settings-driven defaults: all tunables added to _DEFAULTS dict, not hardcoded at call sites"

key-files:
  created: []
  modified:
    - config_loader.py

key-decisions:
  - "D-09: threshold_block_size default is 31; stored in _DEFAULTS so preprocessor reads via settings.get('threshold_block_size', 31)"
  - "Validation (odd block_size check) is deferred to preprocessor at point of use, not config_loader — per T-2-02-01"

patterns-established:
  - "Extend _DEFAULTS for each new tunable; merge logic handles absent/override automatically"

requirements-completed:
  - PROC-02

# Metrics
duration: 5min
completed: 2026-04-30
---

# Phase 2 Plan 02: Config Loader Extension Summary

**threshold_block_size=31 added to config_loader.py _DEFAULTS, wiring adaptive threshold block size as a settings-driven tunable for the preprocessor**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-04-30T16:56:14Z
- **Completed:** 2026-04-30T17:01:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Added `"threshold_block_size": 31` as the last entry in `_DEFAULTS` in `config_loader.py`
- Target test `test_settings_threshold_block_size_default` now passes green
- All 8 Phase 1 regression tests still pass (no regression)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add threshold_block_size to _DEFAULTS in config_loader.py** - `ad15f08` (feat)

**Plan metadata:** (docs commit to follow)

## Files Created/Modified
- `config_loader.py` — Added `"threshold_block_size": 31` to `_DEFAULTS` dict (one line change, lines 11–17)

## Decisions Made
None - followed plan as specified. The exact default value (31) and placement (last entry in _DEFAULTS) were pre-specified in D-09 and the plan action block. Validation of the odd block_size invariant is intentionally deferred to `preprocessor.py` at point of use (T-2-02-01).

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `config_loader.py` now exposes `threshold_block_size` in the settings dict; plan 02-06 (`pipeline/preprocessor.py`) can read it via `settings.get("threshold_block_size", 31)` without any additional setup
- Plans 02-03 and 02-04 (CMS-1500 and UB-04 field coordinates) are unblocked and independent of this change

---
*Phase: 02-image-pipeline-coordinate-calibration*
*Completed: 2026-04-30*
