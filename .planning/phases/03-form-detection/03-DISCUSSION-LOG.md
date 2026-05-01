# Phase 3: Form Detection - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-01
**Phase:** 03-form-detection
**Areas discussed:** Return type, UB-04 anchor rule, Module placement

---

## Return Type

| Option | Description | Selected |
|--------|-------------|----------|
| Plain string | 'CMS-1500', 'UB-04', 'UNKNOWN' — matches roadmap labels, simplest Phase 4 dispatch | ✓ |
| Enum (FormType) | Type-safe, autocomplete-friendly, but requires conversion to string for Excel output | |
| Dataclass (DetectionResult) | Includes matched_anchors for debugging, most verbose | |

**User's choice:** Plain string — `'CMS-1500'`, `'UB-04'`, `'UNKNOWN'`
**Notes:** Function name confirmed as `detect_form_type(image)`.

---

## UB-04 Anchor Rule

| Option | Description | Selected |
|--------|-------------|----------|
| Both must match (2-of-2) | Strictest — consistent with "2 anchors minimum" rule; clipped scans fall to UNKNOWN | |
| Either suffices (1-of-2) | More forgiving — one visible anchor classifies as UB-04; CMS-1500 still needs 2-of-3 | ✓ |

**User's choice:** 1-of-2 anchors suffices for UB-04
**Notes:** Conflict case (page matches both form types) → UNKNOWN. User confirmed UNKNOWN is safer than guessing on ambiguous scans.

---

## Module Placement

| Option | Description | Selected |
|--------|-------------|----------|
| pipeline/detector.py | Extends existing pipeline package; re-exported from pipeline/__init__.py | ✓ |
| detector.py at root | Flat, visible; breaks pipeline package pattern from Phase 2 | |

**User's choice:** `pipeline/detector.py`, re-exported from `pipeline/__init__.py`
**Notes:** Tests in `tests/test_phase3.py` — confirmed consistent with test_phase1.py / test_phase2.py naming.

---

## Claude's Discretion

- Strip height for header/footer crops before Tesseract
- PSM mode for detection OCR
- Whether to apply grayscale conversion before Tesseract call
- Case-insensitive vs exact anchor string matching
- `image_to_string` vs `image_to_data` for the detection call

## Deferred Ideas

None — discussion stayed within phase scope.
