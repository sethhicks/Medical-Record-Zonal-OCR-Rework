---
phase: 3
slug: form-detection
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-01
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (already installed) |
| **Config file** | none — existing pytest discovery |
| **Quick run command** | `pytest tests/test_phase3.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds (unit tests mock OCR; 2 integration tests ~2s each) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_phase3.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 0 | PROC-03 | — | N/A | stub | `pytest tests/test_phase3.py -x` | ❌ W0 | ⬜ pending |
| 3-02-01 | 02 | 1 | PROC-03 | — | N/A | unit | `pytest tests/test_phase3.py::test_cms1500_detection_mock -x` | ❌ W0 | ⬜ pending |
| 3-02-02 | 02 | 1 | PROC-03 | — | N/A | unit | `pytest tests/test_phase3.py::test_ub04_detection_mock -x` | ❌ W0 | ⬜ pending |
| 3-02-03 | 02 | 1 | PROC-03 | — | N/A | unit | `pytest tests/test_phase3.py::test_unknown_when_no_anchors -x` | ❌ W0 | ⬜ pending |
| 3-02-04 | 02 | 1 | PROC-03 | — | N/A | unit | `pytest tests/test_phase3.py::test_both_match_returns_unknown -x` | ❌ W0 | ⬜ pending |
| 3-02-05 | 02 | 1 | PROC-03 | — | N/A | unit | `pytest tests/test_phase3.py::test_import_from_pipeline -x` | ❌ W0 | ⬜ pending |
| 3-03-01 | 03 | 1 | PROC-03 | — | N/A | integration | `pytest tests/test_phase3.py::test_cms1500_smoke -x` | ❌ W0 | ⬜ pending |
| 3-03-02 | 03 | 1 | PROC-03 | — | N/A | integration | `pytest tests/test_phase3.py::test_ub04_smoke -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase3.py` — create with stubs for all 8 test cases above (all skip initially)
- `tests/conftest.py` — already exists with `test_pdf_path` and `sample_settings` fixtures; no changes needed

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Page 11 (UB-04, TUCSON MEDICAL CENTER) returns UNKNOWN | PROC-03 | Known OCR limitation — NUBC text not recoverable on this scan | Run `pytest tests/test_phase3.py::test_page11_unknown` or verify via calibrate.py; expected UNKNOWN, not a bug |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
