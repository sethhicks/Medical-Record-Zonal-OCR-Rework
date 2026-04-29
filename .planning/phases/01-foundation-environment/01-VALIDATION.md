---
phase: 1
slug: foundation-environment
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-28
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (not yet installed — Wave 0 installs) |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `python -m pytest tests/test_phase1.py -x` |
| **Full suite command** | `python -m pytest tests/ -x` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_phase1.py -x`
- **After every plan wave:** Run `python -m pytest tests/ -x`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 0 | — | — | N/A | infra | `python -m pytest --co -q` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | ENV-01 | — | subprocess shell=False; no PATH lookup | unit | `python -m pytest tests/test_phase1.py::test_checks_pass -x` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 1 | ENV-01 | — | Returns False + error msg when tesseract path bogus | unit | `python -m pytest tests/test_phase1.py::test_tesseract_missing -x` | ❌ W0 | ⬜ pending |
| 1-01-04 | 01 | 1 | ENV-01 | — | Returns False + error msg when poppler path bogus | unit | `python -m pytest tests/test_phase1.py::test_poppler_missing -x` | ❌ W0 | ⬜ pending |
| 1-01-05 | 01 | 1 | ENV-01 | — | Standalone exits 0 on valid paths | unit | `python -m pytest tests/test_phase1.py::test_standalone_exit_ok -x` | ❌ W0 | ⬜ pending |
| 1-01-06 | 01 | 1 | ENV-01 | — | Standalone exits 1 on invalid path | unit | `python -m pytest tests/test_phase1.py::test_standalone_exit_fail -x` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 1 | ENV-02 | — | Missing settings.json returns all 4 default keys | unit | `python -m pytest tests/test_phase1.py::test_defaults_no_file -x` | ❌ W0 | ⬜ pending |
| 1-02-02 | 02 | 1 | ENV-02 | — | User keys override defaults | unit | `python -m pytest tests/test_phase1.py::test_settings_override -x` | ❌ W0 | ⬜ pending |
| 1-03-01 | 03 | 1 | ENV-02 | — | FieldResult importable from models | unit | `python -m pytest tests/test_phase1.py::test_imports -x` | ❌ W0 | ⬜ pending |
| 1-03-02 | 03 | 1 | ENV-02 | — | FieldDef importable from config.base | unit | `python -m pytest tests/test_phase1.py::test_imports -x` | ❌ W0 | ⬜ pending |
| 1-03-03 | 03 | 1 | ENV-02 | — | TableFieldDef importable from config.base | unit | `python -m pytest tests/test_phase1.py::test_imports -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pip install pytest` — test runner not installed
- [ ] `tests/__init__.py` — package marker
- [ ] `tests/test_phase1.py` — stubs for ENV-01, ENV-02 (all test functions defined, skipped until implementation lands)

*Wave 0 must complete before any Wave 1 task can claim automated verification.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `python setup_check.py` output readability | ENV-01 | Human judgment on message clarity | Run `python setup_check.py` with real binaries; confirm each line is `OK: <name> found at <path> (from <source>)`; run with bogus path; confirm `ERROR: <name> not found at <path> (from <source>)` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
