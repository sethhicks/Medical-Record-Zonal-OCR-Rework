---
phase: 4
slug: field-extraction-cms-1500-ub-04
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-03
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | none — default discovery |
| **Quick run command** | `python -m pytest tests/test_phase4.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -q` |
| **Estimated runtime** | ~15 seconds (unit); ~60 seconds (full suite with real PDF) |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_phase4.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 0 | EXTR-01, EXTR-02, EXTR-03 | unit (stubs) | `python -m pytest tests/test_phase4.py -x -q` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 1 | EXTR-01 (D-02, D-03) | unit | `python -m pytest tests/test_phase4.py -x -q` | ❌ W0 | ⬜ pending |
| 04-03-01 | 03 | 1 | EXTR-01 | unit | `python -m pytest tests/test_phase4.py::test_extract_cms1500_returns_list -x` | ❌ W0 | ⬜ pending |
| 04-03-02 | 03 | 1 | EXTR-01 | unit | `python -m pytest tests/test_phase4.py::test_extract_cms1500_result_count -x` | ❌ W0 | ⬜ pending |
| 04-03-03 | 03 | 1 | EXTR-01 | unit | `python -m pytest tests/test_phase4.py::test_extract_cms1500_service_line_naming -x` | ❌ W0 | ⬜ pending |
| 04-03-04 | 03 | 1 | EXTR-03 | unit | `python -m pytest tests/test_phase4.py::test_cms1500_all_results_have_confidence -x` | ❌ W0 | ⬜ pending |
| 04-04-01 | 04 | 1 | EXTR-02 | unit | `python -m pytest tests/test_phase4.py::test_extract_ub04_returns_list -x` | ❌ W0 | ⬜ pending |
| 04-04-02 | 04 | 1 | EXTR-02 | unit | `python -m pytest tests/test_phase4.py::test_extract_ub04_result_count -x` | ❌ W0 | ⬜ pending |
| 04-04-03 | 04 | 1 | EXTR-02 | unit | `python -m pytest tests/test_phase4.py::test_extract_ub04_revenue_line_naming -x` | ❌ W0 | ⬜ pending |
| 04-04-04 | 04 | 1 | EXTR-03 | unit | `python -m pytest tests/test_phase4.py::test_ub04_all_results_have_confidence -x` | ❌ W0 | ⬜ pending |
| 04-05-01 | 05 | 1 | D-09 | unit | `python -m pytest tests/test_phase4.py::test_import_extract_cms1500_from_pipeline -x` | ❌ W0 | ⬜ pending |
| 04-06-01 | 06 | 2 | EXTR-01 SC-1 | integration | `python -m pytest tests/test_phase4.py::test_cms1500_smoke_80pct -x` | ❌ W0 | ⬜ pending |
| 04-06-02 | 06 | 2 | EXTR-02 SC-2 | integration | `python -m pytest tests/test_phase4.py::test_ub04_smoke_80pct -x` | ❌ W0 | ⬜ pending |
| 04-06-03 | 06 | 2 | EXTR-01 whitelist | integration | `python -m pytest tests/test_phase4.py::test_cms1500_whitelist_npi_chars -x` | ❌ W0 | ⬜ pending |
| 04-06-04 | 06 | 2 | EXTR-02 whitelist | integration | `python -m pytest tests/test_phase4.py::test_ub04_whitelist_icd10_chars -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase4.py` — 17 stubs (all tests as `@pytest.mark.skip`)
- [ ] `tests/conftest.py` — already has `test_pdf_path` and `sample_settings` fixtures; no changes needed

*Existing pytest infrastructure carries over from Phases 1–3.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Confidence distribution calibration | SC-1, SC-2 | Requires human judgment on threshold vs. real claim data | Run extractor on all CMS-1500 pages in test.pdf; inspect non-empty rates; identify best page; document achieved rate in STATE.md |
| 80% threshold achievability | SC-1, SC-2 | Live extraction shows 7–21% non-empty with current coordinates; adjust threshold or flag for coordinate re-tuning | See Pitfall 4 in RESEARCH.md; document final decision in STATE.md Open Decisions |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
