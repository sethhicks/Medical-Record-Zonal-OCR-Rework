---
phase: 05-output-excel-export
reviewed: 2026-05-06T00:00:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - pipeline/writer.py
  - pipeline/__init__.py
  - tests/test_phase5.py
findings:
  critical: 0
  warning: 3
  info: 2
  total: 5
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-05-06
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Reviewed `pipeline/writer.py` (the Excel workbook writer), `pipeline/__init__.py` (public API re-export), and `tests/test_phase5.py` (12 activated stubs). The writer logic is sound — column counts, header freeze, yellow-fill sentinel, and text-format routing are all correct. The `__init__.py` export is clean.

The critical-risk finding is in the test suite: `test_no_fill_above_threshold` contains a logically broken assertion that will **never** detect a regression where yellow fill is incorrectly applied to a high-confidence cell. This is confirmed by live execution: openpyxl stores the yellow color as `"00FFFF00"` (ARGB with alpha prefix), not `"FFFF00"`, so the `!= "FFFF00"` branch in the disjunction is always `True`, making the test vacuously pass regardless of what fill is actually present.

Two additional warnings cover a missing `output_dir` existence check (silent `FileNotFoundError` at save time) and an unused parameter in `_write_sheet`. Two info items cover test coverage gaps and a design gap in the text-format substring set.

---

## Warnings

### WR-01: `test_no_fill_above_threshold` assertion is always True — test cannot detect regression

**File:** `tests/test_phase5.py:177`

**Issue:** The assertion is:
```python
assert fill is None or fill.fill_type == "none" or fill.fgColor.rgb != "FFFF00"
```
openpyxl stores yellow fill after a save/load round-trip as `"00FFFF00"` (ARGB), not `"FFFF00"`. The third condition `fill.fgColor.rgb != "FFFF00"` evaluates to `True` for both the no-fill case (`"00000000"`) and the yellow-fill case (`"00FFFF00"`). The assertion therefore passes unconditionally — it can never fail even if the production code incorrectly applies yellow fill to every cell. This is confirmed by running the assertion against a cell that has yellow fill applied: the test still passes.

**Fix:** Mirror the `endswith` check used in the positive test:
```python
# Assert the cell does NOT have yellow fill
assert not cell.fill.fgColor.rgb.endswith("FFFF00")
```
This is consistent with `test_yellow_fill_below_threshold` line 154 which already uses `.endswith("FFFF00")` for the positive case.

---

### WR-02: `write_workbook` does not validate or create `output_dir` — silent `FileNotFoundError`

**File:** `pipeline/writer.py:233-234`

**Issue:** If `settings["output_dir"]` refers to a directory that does not exist, `wb.save(str(output_path))` on line 260 raises an unhandled `FileNotFoundError`. The error message will reference an internal openpyxl path and give no actionable guidance to the caller. For Phase 6's UI integration, the user will see a raw Python exception instead of a clear failure message.

```python
output_dir = pathlib.Path(settings.get("output_dir", str(pathlib.Path.home() / "Desktop")))
output_path = output_dir / "extracted_results.xlsx"
# ... no validation before wb.save()
wb.save(str(output_path))  # raises FileNotFoundError if output_dir missing
```

Additionally, if `settings["output_dir"]` is explicitly set to `None` (not absent), `pathlib.Path(None)` raises `TypeError` before any file I/O, with an equally opaque message.

**Fix:** Add a guard before `wb.save()`:
```python
output_dir = pathlib.Path(settings.get("output_dir") or str(pathlib.Path.home() / "Desktop"))
output_path = output_dir / "extracted_results.xlsx"
# ...
output_dir.mkdir(parents=True, exist_ok=True)   # create if absent; no-op if present
wb.save(str(output_path))
```
Using `mkdir(parents=True, exist_ok=True)` is the standard pattern for this case. If directory creation should be forbidden (i.e., the path must already exist), raise `FileNotFoundError` with a clear message before calling `wb.save()`.

---

### WR-03: `_write_sheet` accepts `field_names_in_order` parameter but never uses it

**File:** `pipeline/writer.py:151, 255, 258`

**Issue:** `_write_sheet` declares `field_names_in_order: list[str]` as its fourth parameter and documents it in the docstring, but the function body never references it. The inner loop iterates `col_map.items()` directly. The parameter is computed and passed at both call sites (lines 255 and 258) but is dead weight. A future maintainer could mistakenly assume the parameter controls iteration order, when it does not.

```python
def _write_sheet(
    ws,
    headers: list[str],
    col_map: dict[str, int],
    field_names_in_order: list[str],   # declared but never referenced
    pages: list[list[FieldResult]],
    threshold: float,
) -> None:
```

**Fix:** Remove the parameter from the signature, remove it from both call sites in `write_workbook`, and remove the construction of `cms_field_names` / `ub_field_names` on lines 242–249 (which exist only to feed this parameter). This is a clean simplification with no behavioral change.

---

## Info

### IN-01: `_TEXT_FORMAT_SUBSTRINGS` does not cover patient account numbers or insured member IDs

**File:** `pipeline/writer.py:52-71`

**Issue:** Several fields contain values that are alphanumeric identifiers with potential leading zeros but are not matched by any substring in `_TEXT_FORMAT_SUBSTRINGS`:

- `box26_patient_account` (CMS-1500 Box 26) — patient account number, no text format applied
- `box60_insured_unique_id` (UB-04 Box 60) — insured unique ID, no text format applied
- `box3b_patient_control` (UB-04 Box 3b) — patient control number, no text format applied
- `box23_prior_auth` (CMS-1500 Box 23) — prior authorization number, no text format applied

Without `number_format = "@"`, Excel may silently convert a purely-numeric value like `"001234"` to integer `1234`, destroying the leading zero. This matches exactly the problem D-07/D-08 were designed to prevent for NPI and date fields. The decision to omit these fields from the text-format set appears to be an oversight rather than an intentional design choice (D-09 states coverage via "field_name substring matching" but gives no rationale for exclusion).

**Fix:** Add the missing substrings to `_TEXT_FORMAT_SUBSTRINGS`:
```python
"account",   # box26_patient_account
"control",   # box3b_patient_control
"auth",      # box23_prior_auth (prior auth numbers)
"unique_id", # box60_insured_unique_id (or use "insured" but that's broad)
```
Alternatively, default all fields to text format and only opt-out fields where numeric behavior is desired — safer given this is billing data where data fidelity matters.

---

### IN-02: Test suite has no coverage for UB-04 sheet freeze_panes or UB-04 yellow fill

**File:** `tests/test_phase5.py:120-131, 134-154`

**Issue:** `test_cms1500_header_row_frozen` only verifies that the CMS-1500 sheet has `freeze_panes == "A2"`. The UB-04 sheet is written by the same `_write_sheet` call and also receives `ws.freeze_panes = "A2"`, but no test asserts this. Similarly, `test_yellow_fill_below_threshold` and `test_no_fill_above_threshold` only exercise the CMS-1500 sheet. A regression that accidentally skips `freeze_panes` or fill assignment for UB-04 would go undetected.

**Fix:** Extend the existing freeze-panes test to also assert `wb["UB-04"].freeze_panes == "A2"`, and add a parallel yellow-fill assertion for a UB-04 field (e.g., `ub04_rl_rev_code_rl1`). These can be appended to the existing test functions without adding new functions.

---

_Reviewed: 2026-05-06_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
