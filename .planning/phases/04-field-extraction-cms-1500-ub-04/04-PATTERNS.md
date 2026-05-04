# Phase 4: Field Extraction — CMS-1500 & UB-04 - Pattern Map

**Mapped:** 2026-05-03
**Files analyzed:** 5 (2 new modules, 1 modified init, 1 modified config, 1 new test file)
**Analogs found:** 5 / 5

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `pipeline/extractor_cms1500.py` | service | request-response | `pipeline/detector.py` | role-match |
| `pipeline/extractor_ub04.py` | service | request-response | `pipeline/detector.py` | role-match |
| `pipeline/__init__.py` | config | — | `pipeline/__init__.py` (self) | exact |
| `config/cms1500.py` | config | — | `config/cms1500.py` (self) | exact |
| `tests/test_phase4.py` | test | — | `tests/test_phase3.py` | exact |

---

## Pattern Assignments

### `pipeline/extractor_cms1500.py` (service, request-response)

**Analog:** `pipeline/detector.py`

**Imports pattern** (detector.py lines 11–14):
```python
import pytesseract
from PIL import Image

from config_loader import load_settings
```

For the extractor, adapt to:
```python
# pipeline/extractor_cms1500.py
import pytesseract
from PIL import Image
from typing import Optional

from config.cms1500 import CMS1500_FIELDS, CMS1500_TABLE_FIELDS
from models.field_result import FieldResult
```

**Windows tesseract_cmd pattern** (detector.py lines 33–34):
```python
settings = load_settings()
pytesseract.pytesseract.tesseract_cmd = settings['tesseract_cmd']
```

For the extractor, `settings` arrives as a parameter (not loaded internally):
```python
def extract_cms1500(image: "Image.Image", settings: dict) -> list[FieldResult]:
    pytesseract.pytesseract.tesseract_cmd = settings['tesseract_cmd']
```

**Stateless function signature pattern** (detector.py lines 21–31):
```python
def detect_form_type(image: "Image.Image") -> str:
    """Classify a raw page image as 'CMS-1500', 'UB-04', or 'UNKNOWN'.

    Args:
        image: Raw PIL Image from convert_page() — mode 'RGB', 2550x3300 px.
               Detection runs on the RAW image, not the preprocessed image.

    Returns:
        'CMS-1500' — cms_score >= 2 and ub04_score == 0
        ...
    """
```

Extractor follows the same stateless pattern — no instance state, accepts `(image, settings)`, returns typed result.

**Core extraction loop** — derived from `config/cms1500.py` structure (FieldDef at lines 14–44, TableFieldDef at lines 53–194):
```python
results: list[FieldResult] = []

# 29 single-value fields — iterate CMS1500_FIELDS
for fd in CMS1500_FIELDS:
    crop = image.crop(fd.box)                      # fd.box = (left, top, right, bottom)
    value, conf = _ocr_region(crop, fd.psm, fd.whitelist)
    results.append(FieldResult(field_name=fd.name, value=value, confidence=conf))

# 10 TableFieldDef x 6 rows = 60 table cells (D-06: always 6 rows)
for tfd in CMS1500_TABLE_FIELDS:
    for i, box in enumerate(tfd.row_boxes):        # i is 0-indexed
        field_name = f"{tfd.name}_sl{i + 1}"      # D-06: _sl1 through _sl6
        crop = image.crop(box)
        value, conf = _ocr_region(crop, tfd.psm, tfd.whitelist)
        results.append(FieldResult(field_name=field_name, value=value, confidence=conf))

return results  # always 89 entries
```

**Private `_ocr_region` helper** — core OCR pattern with filtering:
```python
def _ocr_region(
    crop: "Image.Image",
    psm: int,
    whitelist: Optional[str],
) -> tuple[str, float]:
    """Run Tesseract on a pre-cropped image region.

    Returns:
        (value, confidence) — value is stripped joined text;
        ("", -1.0) if no words found or exception raised.
    """
    config = f"--psm {psm}"
    if whitelist:
        config += f" -c tessedit_char_whitelist={whitelist}"
    try:
        d = pytesseract.image_to_data(
            crop, config=config, output_type=pytesseract.Output.DICT
        )
        words = [
            (t, int(c))
            for t, c in zip(d["text"], d["conf"])
            if int(c) > 0 and t.strip()   # exclude conf=-1 (structural) and conf=0 (noise)
        ]
        if words:
            value = " ".join(t for t, _ in words).strip()
            confidence = float(min(c for _, c in words))  # D-10: minimum across words
            return value, confidence
        return "", -1.0   # D-11: blank region sentinel
    except Exception:
        return "", -1.0   # D-11: error path sentinel
```

**Config string pattern** (RESEARCH.md verified pattern):
```python
# PSM only (no whitelist):
config = f"--psm {fd.psm}"

# PSM + whitelist — NO quotes around whitelist value:
config = f"--psm {fd.psm} -c tessedit_char_whitelist={fd.whitelist}"
# WRONG: f'--psm 7 -c tessedit_char_whitelist="{fd.whitelist}"'
```

---

### `pipeline/extractor_ub04.py` (service, request-response)

**Analog:** `pipeline/detector.py` (same analog as CMS-1500 extractor)

**Imports pattern** — same structure as extractor_cms1500.py, different config source:
```python
# pipeline/extractor_ub04.py
import pytesseract
from PIL import Image
from typing import Optional

from config.ub04 import UB04_FIELDS, UB04_TABLE_FIELDS
from models.field_result import FieldResult
```

**Core extraction loop** — same loop structure as CMS-1500, different suffix and field lists:
```python
results: list[FieldResult] = []

# 24 single-value fields — iterate UB04_FIELDS
for fd in UB04_FIELDS:
    crop = image.crop(fd.box)
    value, conf = _ocr_region(crop, fd.psm, fd.whitelist)
    results.append(FieldResult(field_name=fd.name, value=value, confidence=conf))

# 7 TableFieldDef x 22 rows = 154 revenue-line cells (D-07: always 22 rows)
for tfd in UB04_TABLE_FIELDS:
    for i, box in enumerate(tfd.row_boxes):
        field_name = f"{tfd.name}_rl{i + 1}"      # D-07: _rl1 through _rl22
        crop = image.crop(box)
        value, conf = _ocr_region(crop, tfd.psm, tfd.whitelist)
        results.append(FieldResult(field_name=field_name, value=value, confidence=conf))

return results  # always 178 entries
```

**UB-04 table field names** (config/ub04.py line 54 — names have `ub04_rl_` prefix):
```python
# UB04_TABLE_FIELDS names: "ub04_rl_rev_code", "ub04_rl_hcpcs", etc.
# D-07 suffix produces: "ub04_rl_rev_code_rl1" ... "ub04_rl_rev_code_rl22"
# Phase 5 handles column name mapping — Phase 4 generates names as-is.
```

**`_ocr_region` helper** — duplicate verbatim from extractor_cms1500.py. Both modules are self-contained (D-08, RESEARCH.md recommendation A2).

---

### `pipeline/__init__.py` (config — export addition)

**Analog:** `pipeline/__init__.py` (self — the file being modified)

**Current export pattern** (pipeline/__init__.py lines 1–13):
```python
# pipeline/__init__.py
"""Image pipeline public API for OCR Medical Billing Form Extractor.

Exposes:
    convert_page(pdf_path, page_num) -> PIL.Image.Image
    preprocess_page(image, settings, debug=False) -> PIL.Image.Image
    detect_form_type(image) -> str
"""
from .converter import convert_page
from .preprocessor import preprocess_page
from .detector import detect_form_type

__all__ = ["convert_page", "preprocess_page", "detect_form_type"]
```

**After Phase 4 modification** — add two imports and expand `__all__`:
```python
# pipeline/__init__.py
"""Image pipeline public API for OCR Medical Billing Form Extractor.

Exposes:
    convert_page(pdf_path, page_num) -> PIL.Image.Image
    preprocess_page(image, settings, debug=False) -> PIL.Image.Image
    detect_form_type(image) -> str
    extract_cms1500(image, settings) -> list[FieldResult]
    extract_ub04(image, settings) -> list[FieldResult]
"""
from .converter import convert_page
from .preprocessor import preprocess_page
from .detector import detect_form_type
from .extractor_cms1500 import extract_cms1500
from .extractor_ub04 import extract_ub04

__all__ = [
    "convert_page",
    "preprocess_page",
    "detect_form_type",
    "extract_cms1500",
    "extract_ub04",
]
```

**Import path convention** (D-09): `from pipeline import extract_cms1500, extract_ub04` — identical pattern to `from pipeline import detect_form_type` already in use.

---

### `config/cms1500.py` (config — whitelist updates)

**Analog:** `config/cms1500.py` (self — the file being modified)

**Current whitelist values requiring update** (cms1500.py lines 24–35):

`box21a_diag` through `box21l_diag` — all 12 currently have:
```python
whitelist="0123456789. "
```

**Required change per D-02** — update all 12 to:
```python
whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789. "
```

Affected lines: 24 (`box21a_diag`), 25 (`box21b_diag`), 26 (`box21c_diag`), 27 (`box21d_diag`), 28 (`box21e_diag`), 29 (`box21f_diag`), 30 (`box21g_diag`), 31 (`box21h_diag`), 32 (`box21i_diag`), 33 (`box21j_diag`), 34 (`box21k_diag`), 35 (`box21l_diag`).

**Current `box24_cpt` whitelist** (cms1500.py line 122):
```python
whitelist="0123456789"
```

**Required change per D-03** — update to:
```python
whitelist="0123456789- "
```

Affected line: 122 (`box24_cpt` TableFieldDef).

**FieldDef structure to preserve** (cms1500.py lines 15–16 — representative examples):
```python
FieldDef(name="box21a_diag", box=(30, 960, 200, 1010), psm=7, whitelist="0123456789. ",  label="Box 21a — Diagnosis A"),
#                                                                          ^^^^^^^^^^^^^^ change this value only
```

**Update rule:** Change only the `whitelist=` argument. Do not alter `name`, `box`, `psm`, or `label` for any entry.

---

### `tests/test_phase4.py` (test)

**Analog:** `tests/test_phase3.py`

**File header pattern** (test_phase3.py lines 1–18):
```python
# tests/test_phase3.py
"""Phase 3 tests — PROC-03 (form type detection).

Skip markers are removed by Wave 1 plans as each feature is implemented:
  - test_cms1500_detection_mock     -> removed by 03-02-PLAN
  ...
"""
import pytest
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_TEST_PDF = str(_ROOT / "test.pdf")
```

For Phase 4:
```python
# tests/test_phase4.py
"""Phase 4 tests — EXTR-01, EXTR-02, EXTR-03 (field extraction).

Skip markers are removed by Wave 1 plans as each feature is implemented:
  - test_extract_cms1500_returns_list       -> removed by 04-02-PLAN
  - test_extract_cms1500_result_count       -> removed by 04-02-PLAN
  ...
"""
import pytest
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_TEST_PDF = str(_ROOT / "test.pdf")
```

**Unit test with monkeypatch pattern** (test_phase3.py lines 25–39):
```python
def test_cms1500_detection_mock(monkeypatch):
    """2-of-3 CMS-1500 anchors via mock OCR returns 'CMS-1500'."""
    import pytesseract
    from pipeline import detect_form_type
    from PIL import Image

    responses = iter([...])
    monkeypatch.setattr(pytesseract, 'image_to_string',
                        lambda img, config='': next(responses))
    img = Image.new('RGB', (2550, 3300), 255)
    assert detect_form_type(img) == 'CMS-1500'
```

For Phase 4 mock unit tests, patch `pytesseract.image_to_data`:
```python
def test_extract_cms1500_returns_list(monkeypatch):
    """extract_cms1500 returns a list."""
    import pytesseract
    from pipeline import extract_cms1500
    from PIL import Image

    empty_data = {'text': [], 'conf': []}
    monkeypatch.setattr(pytesseract, 'image_to_data',
                        lambda img, config='', output_type=None: empty_data)
    img = Image.new('RGB', (2550, 3300), 255)
    settings = {'tesseract_cmd': r'C:\Program Files\Tesseract-OCR\tesseract.exe'}
    result = extract_cms1500(img, settings)
    assert isinstance(result, list)
```

**Stub pattern** — all 17 Wave 0 stubs use `@pytest.mark.skip`:
```python
@pytest.mark.skip(reason="stub — implemented by Wave 1")
def test_extract_cms1500_returns_list(monkeypatch):
    ...
```

**Import-only test pattern** (test_phase3.py lines 103–106):
```python
def test_import_from_pipeline():
    """detect_form_type is importable from the pipeline package (per D-08)."""
    from pipeline import detect_form_type
    assert callable(detect_form_type)
```

For Phase 4:
```python
def test_import_extract_cms1500_from_pipeline():
    """extract_cms1500 is importable from pipeline (D-09)."""
    from pipeline import extract_cms1500
    assert callable(extract_cms1500)

def test_import_extract_ub04_from_pipeline():
    """extract_ub04 is importable from pipeline (D-09)."""
    from pipeline import extract_ub04
    assert callable(extract_ub04)
```

**Smoke test pattern using fixtures** (test_phase3.py lines 109–124):
```python
def test_cms1500_smoke(test_pdf_path):
    """Real test.pdf page 0 classifies as 'CMS-1500' (uses actual Tesseract, ~2s)."""
    from pipeline import convert_page, detect_form_type
    image = convert_page(test_pdf_path, 0)
    assert detect_form_type(image) == 'CMS-1500'
```

For Phase 4 smoke tests, use `test_pdf_path` and `sample_settings` fixtures from `conftest.py`:
```python
def test_cms1500_smoke_80pct(test_pdf_path, sample_settings):
    """Real CMS-1500 page: >= 80% non-empty fields (uses actual Tesseract)."""
    from pipeline import convert_page, preprocess_page, extract_cms1500
    raw = convert_page(test_pdf_path, 0)
    proc = preprocess_page(raw, sample_settings)
    results = extract_cms1500(proc, sample_settings)
    non_empty = sum(1 for r in results if r.value)
    rate = non_empty / len(results)
    assert rate >= CMS_THRESHOLD  # empirically calibrated in 04-06 — NOT hardcoded 0.80
```

**conftest.py fixtures available** (conftest.py lines 7–20 — no changes needed):
```python
@pytest.fixture(scope="session")
def test_pdf_path() -> str:
    path = Path(__file__).parent.parent / "test.pdf"
    assert path.exists(), f"test.pdf not found at {path}"
    return str(path)

@pytest.fixture(scope="session")
def sample_settings(tmp_path_factory) -> dict:
    from config_loader import load_settings
    tmp = tmp_path_factory.mktemp("settings")
    return load_settings(path=str(tmp / "settings.json"))
```

---

## Shared Patterns

### Windows Tesseract Binary Path
**Source:** `pipeline/detector.py` lines 33–34
**Apply to:** `pipeline/extractor_cms1500.py` and `pipeline/extractor_ub04.py` — first statement inside each public function
```python
pytesseract.pytesseract.tesseract_cmd = settings['tesseract_cmd']
```
This must occur before any `pytesseract.image_to_data()` call. The `settings` dict is passed in as a parameter; do not call `load_settings()` inside the extractor (unlike detector.py which loads its own settings).

### FieldResult Sentinel Convention
**Source:** `models/field_result.py` line 10
**Apply to:** `_ocr_region()` return values in both extractor modules
```python
# models/field_result.py
confidence: float  # 0.0-100.0; -1.0 if no text found in region
```
Both the blank-region path and the exception path return `("", -1.0)` to match this documented convention.

### image_to_data Filtering
**Source:** RESEARCH.md verified pattern (live pytesseract 0.3.13 inspection)
**Apply to:** `_ocr_region()` in both extractor modules
```python
words = [
    (t, int(c))
    for t, c in zip(d["text"], d["conf"])
    if int(c) > 0 and t.strip()
]
```
Filter rule: `int(c) > 0` (not `>= 0`) — `conf == -1` are structural (page/block/para/line) entries; `conf == 0` are noise words with no confidence. Both are excluded.

### PIL Crop Coordinate Convention
**Source:** `config/base.py` lines 9–10, verified in RESEARCH.md
**Apply to:** All `image.crop()` calls in both extractors
```python
# FieldDef.box = (left, top, right, bottom) at 300 DPI
# PIL Image.crop() = (left, upper, right, lower)
# These are identical — no coordinate transformation needed.
crop = image.crop(fd.box)
```

### Stateless Function Module Pattern
**Source:** `pipeline/detector.py` (entire file), `pipeline/preprocessor.py` (entire file)
**Apply to:** Both new extractor modules
- Module-level docstring explaining the function's contract
- No class, no instance state, no global mutable state
- One public function per module; private helpers prefixed with `_`
- Function accepts `(image: Image.Image, settings: dict)` and returns typed result
- Module-level constants (if any) are ALL_CAPS and documented with their source/verification note

### Test File Structure
**Source:** `tests/test_phase3.py` (entire file)
**Apply to:** `tests/test_phase4.py`
- File-level docstring listing all stubs and the Wave plan that removes each skip marker
- `_ROOT` and `_TEST_PDF` module-level constants for path resolution
- All Wave 0 stubs decorated with `@pytest.mark.skip(reason="stub — implemented by Wave 1")`
- Import statements inside test functions (not at module level) — avoids import errors when the module under test does not yet exist

---

## No Analog Found

All 5 files have close analogs. No files require falling back to RESEARCH.md patterns exclusively.

| File | Analog Quality | Notes |
|---|---|---|
| `pipeline/extractor_cms1500.py` | role-match | detector.py is stateless OCR pipeline module; extractor uses `image_to_data` vs `image_to_string`, but module structure is identical |
| `pipeline/extractor_ub04.py` | role-match | Same as CMS-1500 extractor; UB-04 suffix differs (`_rl` vs `_sl`) |
| `pipeline/__init__.py` | exact | Self-modification; add two lines following existing pattern |
| `config/cms1500.py` | exact | Self-modification; update `whitelist=` values only |
| `tests/test_phase4.py` | exact | test_phase3.py is a line-for-line structural template |

---

## Metadata

**Analog search scope:** `pipeline/`, `config/`, `models/`, `tests/`
**Files read:** 8 (detector.py, preprocessor.py, pipeline/__init__.py, cms1500.py, ub04.py, base.py, field_result.py, test_phase3.py, conftest.py)
**Pattern extraction date:** 2026-05-03
