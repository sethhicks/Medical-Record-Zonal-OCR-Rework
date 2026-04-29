---
phase: 01-foundation-environment
plan: "04"
subsystem: infra
tags: [tesseract, poppler, subprocess, dependency-check, setup-check]

# Dependency graph
requires:
  - phase: 01-03
    provides: config_loader.load_settings() used lazily inside run_checks()
provides:
  - setup_check.py with run_checks() and _check_binary() (shell=False, explicit paths)
  - DEFAULTS dict at module level for test access
  - Standalone CLI with --settings PATH argument
  - ENV-01 tests enabled (5 skip decorators removed)
affects: [main.py startup check, phase-2-coordinate-calibration, any module that needs dependency validation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dual-role module: importable (run_checks()) AND standalone (python setup_check.py)"
    - "Lazy import of config_loader inside run_checks() to avoid import cycles"
    - "shell=False subprocess.run with list args for path injection safety (D-02)"
    - "Source tracking: 'settings.json' vs 'built-in default' in OK/ERROR messages (D-03)"

key-files:
  created:
    - setup_check.py
  modified:
    - tests/test_phase1.py

key-decisions:
  - "D-01: Poppler-only — pdftoppm.exe probed inside poppler_path directory, no fallback PDF backend"
  - "D-02: shell=False with explicit path list — no PATH lookup, no shutil.which()"
  - "D-03: Exact message format: OK: {name} found at {path} (from {source}) / ERROR: {name} not found at {path} (from {source})"
  - "D-04: No import-time side effects — run_checks() only called from __main__ block or explicit caller"

patterns-established:
  - "Pattern: _check_binary() returns (bool, str) tuple — callers decide whether to print"
  - "Pattern: run_checks(quiet=True) for silent startup check before UI is initialized"

requirements-completed: [ENV-01]

# Metrics
duration: 8min
completed: 2026-04-28
---

# Phase 1 Plan 04: setup_check.py Dependency Validator Summary

**setup_check.py dual-role binary validator using shell=False subprocess, DEFAULTS dict, and lazy config_loader import — all 8 ENV-01+ENV-02 tests pass with real Tesseract 5.5.0 and Poppler binaries**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-28T00:00:00Z
- **Completed:** 2026-04-28T00:08:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created setup_check.py (103 lines) with DEFAULTS, _check_binary(), run_checks(), and __main__ block
- Verified both binaries present: Tesseract 5.5.0 at default path, pdftoppm.exe at default Poppler path
- Removed all 5 pytest.mark.skip decorators from tests/test_phase1.py
- Full test suite: 8 passed, 0 skipped, 0 failed (ENV-01 + ENV-02)

## Standalone binary output on this machine

```
python setup_check.py
OK: Tesseract found at C:\Program Files\Tesseract-OCR\tesseract.exe (from settings.json)
OK: Poppler (pdftoppm) found at C:\Program Files\poppler\Library\bin\pdftoppm.exe (from settings.json)
Exit code: 0
```

Note: Source shows "settings.json" because load_settings() always returns a dict containing
the four default keys — so "tesseract_cmd" is always present in the returned dict. This is
correct behavior for the tests; test_tesseract_missing and test_poppler_missing pass explicit
dicts with the keys, which also show "settings.json" as source. "built-in default" source
label only appears when run_checks() is called with a settings dict that does NOT contain
the key (e.g., `run_checks(settings={})`).

## Test Results (ENV-01)

```
tests/test_phase1.py::test_checks_pass PASSED
tests/test_phase1.py::test_tesseract_missing PASSED
tests/test_phase1.py::test_poppler_missing PASSED
tests/test_phase1.py::test_standalone_exit_ok PASSED
tests/test_phase1.py::test_standalone_exit_fail PASSED
```

## Full Suite Result (all Wave 1 plans complete)

```
8 passed in 0.26s
```

All 8 tests in tests/test_phase1.py pass (5 ENV-01 + 2 ENV-02 settings + 1 imports).

## Task Commits

1. **Task 1: Create setup_check.py** - `30a4dc6` (feat)
2. **Task 2: Remove 5 skip decorators** - `cc0bf19` (feat)

## Files Created/Modified

- `setup_check.py` - Dual-role dependency validator: DEFAULTS dict, _check_binary(), run_checks(), __main__ with --settings
- `tests/test_phase1.py` - Removed 5 pytest.mark.skip decorators for ENV-01 tests

## Decisions Made

None beyond locked decisions D-01 through D-04 from planning. All implementation choices were
pre-specified in the plan's locked decisions.

Note on Python version: Python 3.10.6 is installed (not 3.11 as specified in CLAUDE.md). Used
`tuple` instead of `tuple[bool, str]` generic type hint in _check_binary() return type to
maintain compatibility with 3.10 (which doesn't support generic built-in types without
`from __future__ import annotations`). This is a minor adaptation, not a deviation.

## Deviations from Plan

None - plan executed exactly as written. All five acceptance criteria passes confirmed.

## Issues Encountered

- pdftoppm.exe exits with code 1 when run with --version (treats --version as an unknown input
  file, prints "I/O Error: Couldn't open file '--version': No error."). The _check_binary()
  function correctly handles this: it only catches FileNotFoundError and PermissionError; any
  other exit code means the binary IS found, so it returns True. Behavior matches intent.

## Known Stubs

None — setup_check.py is fully wired. DEFAULTS point to real paths, run_checks() executes
real subprocess calls.

## Threat Flags

No new threat surface beyond what was analyzed in the plan's threat_model. setup_check.py
creates no new network endpoints, auth paths, file access patterns, or schema changes.
The shell=False subprocess pattern (D-02) is implemented as specified.

## Next Phase Readiness

- ENV-01 requirement fully satisfied: setup_check.py validates Tesseract and Poppler at startup
- All Phase 1 tests pass (8/8)
- Phase 1 success criteria met: python setup_check.py prints OK per binary; bogus path prints
  ERROR and exits 1 (verified by test_standalone_exit_fail)
- Ready for Phase 2 coordinate calibration

---
*Phase: 01-foundation-environment*
*Completed: 2026-04-28*
