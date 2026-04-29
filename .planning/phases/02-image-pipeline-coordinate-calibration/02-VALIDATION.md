---
phase: 2
slug: image-pipeline-coordinate-calibration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-29
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `tests/test_phase2.py` (Wave 0 creates this) |
| **Quick run command** | `pytest tests/test_phase2.py -x` |
| **Full suite command** | `pytest tests/` |
| **Estimated runtime** | ~30 seconds (integration tests hit test.pdf) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_phase2.py -x`
- **After every plan wave:** Run `pytest tests/`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 2-W0-01 | test scaffold | 0 | PROC-01 | — | N/A | unit stub | `pytest tests/test_phase2.py --collect-only` | ❌ W0 | ⬜ pending |
| 2-01-01 | converter | 1 | PROC-01 | T-2-01 | ValueError on non-2550×3300 | integration | `pytest tests/test_phase2.py::test_convert_page_dimensions` | ❌ W0 | ⬜ pending |
| 2-01-02 | converter | 1 | PROC-01 | T-2-02 | FileNotFoundError on bad path | unit | `pytest tests/test_phase2.py::test_convert_page_invalid_pdf` | ❌ W0 | ⬜ pending |
| 2-02-01 | preprocessor | 1 | PROC-02 | — | N/A | integration | `pytest tests/test_phase2.py::test_preprocess_smoke` | ❌ W0 | ⬜ pending |
| 2-02-02 | preprocessor | 1 | PROC-02 | — | ValueError on skew > ±5° | unit | `pytest tests/test_phase2.py::test_deskew_rejection` | ❌ W0 | ⬜ pending |
| 2-02-03 | preprocessor | 1 | PROC-02 | — | N/A | integration | `pytest tests/test_phase2.py::test_scale_factors_near_one` | ❌ W0 | ⬜ pending |
| 2-02-04 | preprocessor | 1 | PROC-02 | — | N/A | integration | `pytest tests/test_phase2.py::test_preprocess_debug_files` | ❌ W0 | ⬜ pending |
| 2-03-01 | settings | 1 | PROC-02 | — | N/A | unit | `pytest tests/test_phase2.py::test_settings_threshold_block_size_default` | ❌ W0 | ⬜ pending |
| 2-04-01 | cms1500 coords | 1 | EXTR-04 | — | N/A | unit | `pytest tests/test_phase2.py::test_cms1500_fields_populated` | ❌ W0 | ⬜ pending |
| 2-04-02 | cms1500 coords | 1 | EXTR-04 | — | N/A | unit | `pytest tests/test_phase2.py::test_cms1500_table_fields_row_count` | ❌ W0 | ⬜ pending |
| 2-05-01 | ub04 coords | 1 | EXTR-04 | — | N/A | unit | `pytest tests/test_phase2.py::test_ub04_fields_populated` | ❌ W0 | ⬜ pending |
| 2-05-02 | ub04 coords | 1 | EXTR-04 | — | N/A | unit | `pytest tests/test_phase2.py::test_ub04_table_fields_row_count` | ❌ W0 | ⬜ pending |
| 2-06-01 | calibrate.py | 2 | EXTR-04 | T-2-02 | No path traversal via --pdf | smoke | `pytest tests/test_phase2.py::test_calibrate_overlay_created` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase2.py` — stubs for PROC-01, PROC-02, EXTR-04
- [ ] `tests/conftest.py` — shared fixture: `test_pdf_path = "test.pdf"`, `sample_page` fixture (calls `convert_page("test.pdf", 0)`)

*Existing `tests/test_phase1.py` and `tests/__init__.py` are present; pytest is already installed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Box 24 grey bands visibly cleaner after adaptive threshold | PROC-02 | Visual quality judgment; no pixel-diff threshold is meaningful without ground truth | Run `python pipeline/preprocessor.py` with `debug=True` on a CMS-1500 page; compare `debug_01_raw.png` vs `debug_04_threshold.png` in Box 24 region |
| Calibration overlay labels land on correct form boxes | EXTR-04 | Coordinate accuracy is subjective; correct alignment requires human comparison vs scanned form | Run `python pipeline/calibrate.py --page 0 --pdf test.pdf`; open `calibration_overlay_p0.png`; verify all labeled rectangles enclose the correct form fields |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
