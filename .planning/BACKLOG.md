# Backlog — OCR Medical Billing Form Extractor

Ideas and deferred work that didn't fit the current phase scope. Review before planning the next milestone.

---

## Calibration & OCR Accuracy

### Coordinate re-tuning & OCR accuracy pass
**Raised:** Phase 5 discussion (2026-05-06)
**Description:** Zone accuracy and OCR scan accuracy need another improvement pass before Phase 5 output is useful for production review. Known gaps from Phase 4 completion:
- `box21a` reads 'TAX9' instead of 'I96' — whitelist OCR noise on ICD codes
- Many single fields still return noisy or empty results
- UB-04 revenue-line column coordinates not yet visually verified

**Suggested approach:** A dedicated calibration pass — additional plan(s) in Phase 4, or a new phase 4.5 inserted between Phase 4 and Phase 5 execution. Use `pipeline/calibrate.py` for visual verification, `image_to_data` word-position sweep for x-coordinate alignment.

**Priority:** High — current non-empty rate ~29–37% on best pages; roadmap success criterion is 80%.

---

## v2 Requirements (from REQUIREMENTS.md)

These were explicitly deferred from v1 scope:

- **META-01:** Source metadata columns on every row (`source_filename`, `page_number`, `form_type`, `extraction_timestamp`)
- **META-02:** Processing log file written alongside Excel output (audit trail)
- **VAL-01:** Post-extraction format validation (NPI = 10 digits, ICD-10 pattern, CPT = 5 digits, dates, ZIP) — orange highlight distinct from yellow confidence flag
- **DUP-01:** Duplicate claim detection — flag rows where claim number + patient name + date of service match another row
