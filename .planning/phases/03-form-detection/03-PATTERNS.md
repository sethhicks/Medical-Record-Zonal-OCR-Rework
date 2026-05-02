# Phase 3: Form Detection - Pattern Map

**Mapped:** 2026-05-01
**Files analyzed:** 3
**Analogs found:** 3 / 3

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `pipeline/detector.py` | service | transform (image-in / string-out) | `pipeline/preprocessor.py` | exact (PIL Image in, stateless function, pytesseract, load_settings) |
| `pipeline/__init__.py` | config | N/A (re-export only) | `pipeline/__init__.py` (current) | exact |
| `tests/test_phase3.py` | test | N/A | `tests/test_phase2.py` | exact |

---

## Pattern Assignments

### `pipeline/detector.py` (service, transform)

**Analog:** `pipeline/preprocessor.py`

**Imports pattern** (`pipeline/preprocessor.py` lines 1-10, `pipeline/converter.py` lines 1-16):

```python
# pipeline/detector.py — copy this import block
import pytesseract
from PIL import Image

from config_loader import load_settings

# Module-level constants for strip coordinates (mirrors _TARGET_W/_TARGET_H style)
_HEADER_STRIP = (0, 0, 2550, 600)     # top 600px — verified on all 30 test pages
_FOOTER_STRIP = (0, 2900, 2550, 3300)  # bottom 400px — verified on all 30 test pages
```

Note: `preprocessor.py` imports `cv2`/`numpy` but does NOT import `config_loader` (it takes `settings` as a parameter). `converter.py` does import `config_loader`. The `detect_form_type` function reads settings internally like `converter.py` does — use the `converter.py` import pattern.

**Windows tesseract_cmd pattern** (`pipeline/converter.py` lines 56-57, `pipeline/preprocessor.py` line 44):

```python
# converter.py — load_settings() called inside function, not at module level
def convert_page(pdf_path: str, page_num: int) -> "Image.Image":
    settings = load_settings()
    poppler_path = settings["poppler_path"]  # explicit path per Windows convention
```

Apply to `detect_form_type`: call `load_settings()` at the top of the function body, then immediately set `pytesseract.pytesseract.tesseract_cmd = settings['tesseract_cmd']` before any `image_to_string` call. This is the established Windows-path-safety pattern — never rely on PATH.

**Core function signature pattern** (`pipeline/preprocessor.py` lines 18-43):

```python
# preprocessor.py — stateless function, PIL Image in, type annotation style
def preprocess_page(
    image: "Image.Image",
    settings: dict,
    debug: bool = False,
) -> "Image.Image":
    """Apply scale correction, deskew, and adaptive threshold to a page image.

    Args:
        image: Raw PIL Image from convert_page() — mode "RGB", expected 2550x3300 px.
        settings: dict from load_settings(); reads "threshold_block_size" (default 31).
        ...
    Returns:
        Preprocessed PIL Image — mode "RGB", same dimensions as input.
    Raises:
        ValueError: If detected skew angle exceeds ±5 degrees (D-10).
    """
```

`detect_form_type` signature differs: no `settings` parameter (reads internally per D-A2), returns `str` not `Image.Image`. Copy the docstring style and the type-annotation-as-string pattern (`"Image.Image"` in quotes) for forward-reference safety.

**PIL image operations pattern** (`pipeline/preprocessor.py` lines 44-55):

```python
# preprocessor.py — PIL->grayscale conversion idiom
gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
```

For `detect_form_type`, the equivalent is pure PIL (no OpenCV needed):
```python
header_gray = image.crop(_HEADER_STRIP).convert('L')
footer_gray = image.crop(_FOOTER_STRIP).convert('L')
```

**Module-level constant style** (`pipeline/converter.py` lines 18-26):

```python
# converter.py — module-level constants with explanatory comments
_TARGET_W = 2550
_TARGET_H = 3300

# Tolerance: accept pages within ±10% of target dimensions; wider deviations are
# not US Letter 8.5x11 forms and must be rejected.
_TOLERANCE = 0.10
```

Use the same leading-underscore naming and inline-comment style for `_HEADER_STRIP` and `_FOOTER_STRIP`.

**Module docstring pattern** (`pipeline/converter.py` lines 1-10):

```python
# pipeline/converter.py
"""PDF-to-PIL page converter for OCR Medical Billing Form Extractor.

Standalone usage (for ad-hoc testing):
    python -c "from pipeline.converter import convert_page; img = convert_page('test.pdf', 0); print(img.size)"

Importable usage:
    from pipeline import convert_page
    image = convert_page(pdf_path, page_num)  # returns 2550x3300 RGB PIL Image
"""
```

Copy this structure for `detector.py`: file comment, then docstring with standalone usage and importable usage examples.

**No error raising in core path** — `converter.py` raises `ValueError` for out-of-spec inputs. `detect_form_type` should NOT raise — it returns `'UNKNOWN'` for all unrecognised inputs (D-05, D-06). This is a deliberate deviation from `converter.py`'s error-raise pattern.

---

### `pipeline/__init__.py` (config, re-export)

**Analog:** `pipeline/__init__.py` (current state, lines 1-11)

**Current file in full:**

```python
# pipeline/__init__.py
"""Image pipeline public API for OCR Medical Billing Form Extractor.

Exposes:
    convert_page(pdf_path, page_num) -> PIL.Image.Image
    preprocess_page(image, settings, debug=False) -> PIL.Image.Image
"""
from .converter import convert_page
from .preprocessor import preprocess_page

__all__ = ["convert_page", "preprocess_page"]
```

**Required modification — add two lines:**

```python
# pipeline/__init__.py — after modification
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

Pattern rules to follow:
- Relative imports only (`.detector`, not `pipeline.detector`)
- Alphabetical order in docstring is NOT required — maintain existing order and append
- `__all__` is a plain list of string names, no trailing comma

---

### `tests/test_phase3.py` (test)

**Analog:** `tests/test_phase2.py`

**File header pattern** (`tests/test_phase2.py` lines 1-23):

```python
# tests/test_phase2.py
"""Phase 2 tests — PROC-01 (converter), PROC-02 (preprocessor), EXTR-04 (calibration).

Skip markers are removed by Wave 1 plans as each feature is implemented:
  - test_convert_page_* tests  →  removed by 02-05-PLAN
  ...
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Project root — used for CLI subprocess invocations
_ROOT = Path(__file__).parent.parent
_TEST_PDF = str(_ROOT / "test.pdf")
```

Copy this exactly for `test_phase3.py`, replacing the phase-specific parts. The `_ROOT` and `_TEST_PDF` module-level constants are used by integration tests to avoid hardcoded paths.

**Import style for in-test imports** (`tests/test_phase2.py` lines 31-33):

```python
# Imports happen INSIDE each test function, not at module level
def test_convert_page_dimensions():
    from pipeline import convert_page
    image = convert_page(_TEST_PDF, 0)
    assert image.size == (2550, 3300)
```

All `from pipeline import ...` calls are inside test functions, not at module top level. This prevents collection-time import errors if the module does not exist yet. Copy this pattern.

**Fixture usage pattern** (`tests/test_phase2.py` lines 55-61, `tests/conftest.py` lines 7-20):

```python
# conftest.py — session-scoped fixtures available to all tests
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

Use `test_pdf_path` fixture (not `_TEST_PDF` constant) in tests that accept a fixture parameter. Use `_TEST_PDF` constant in tests that do NOT take fixture parameters. Both patterns appear in `test_phase2.py`.

**monkeypatch pattern for pytesseract** (`tests/test_phase2.py` — `monkeypatch` used in `test_preprocess_debug_files` line 71):

```python
def test_preprocess_debug_files(tmp_path, sample_settings, monkeypatch):
    from pipeline import convert_page, preprocess_page
    monkeypatch.chdir(tmp_path)
    ...
```

For Phase 3, the mocking target is `pytesseract.image_to_string`. The `monkeypatch.setattr` pattern for it (from RESEARCH.md, verified against project conventions):

```python
def test_cms1500_detection_via_mock(monkeypatch):
    import pytesseract
    from pipeline import detect_form_type
    from PIL import Image

    responses = iter([
        'HEALTH INSURANCE',                          # header PSM6
        'NUCC Instruction Manual available FORM 1500', # footer PSM6
        '',                                          # footer PSM11
    ])
    monkeypatch.setattr(pytesseract, 'image_to_string',
                        lambda img, config='': next(responses))
    img = Image.new('RGB', (2550, 3300), 255)
    assert detect_form_type(img) == 'CMS-1500'
```

`monkeypatch.setattr(pytesseract, 'image_to_string', ...)` patches the attribute on the `pytesseract` module object — this is the correct target because `detector.py` calls `pytesseract.image_to_string(...)` directly.

**pytest.raises pattern** (`tests/test_phase2.py` lines 47-49, 98-99):

```python
with pytest.raises(Exception):
    convert_page("nonexistent_file.pdf", 0)

with pytest.raises(ValueError, match="exceeds"):
    preprocess_page(pil_rotated, sample_settings)
```

Phase 3 has no expected-raise tests (detection never raises), so this pattern is not used in `test_phase3.py`.

**Section separator pattern** (`tests/test_phase2.py` lines 26-28):

```python
# ---------------------------------------------------------------------------
# PROC-01: convert_page
# ---------------------------------------------------------------------------
```

Use this exact separator style with the requirement ID and brief label. For Phase 3: `# PROC-03: detect_form_type`.

---

## Shared Patterns

### Windows Tesseract Path — set inside function, never at module level
**Source:** `pipeline/converter.py` lines 56-57
**Apply to:** `pipeline/detector.py`

```python
# Inside the function body, first thing before any OCR call:
settings = load_settings()
pytesseract.pytesseract.tesseract_cmd = settings['tesseract_cmd']
```

Never set `pytesseract.pytesseract.tesseract_cmd` at module import time. The project convention (established in Phase 2) is to call `load_settings()` inside the function on every call. This is safe because `load_settings()` is cheap (returns a cached dict after first read).

### load_settings() — call pattern
**Source:** `pipeline/converter.py` line 56, `config_loader.py` lines 20-43
**Apply to:** `pipeline/detector.py`

```python
from config_loader import load_settings

def detect_form_type(image: "Image.Image") -> str:
    settings = load_settings()  # reads settings.json, falls back to defaults
    pytesseract.pytesseract.tesseract_cmd = settings['tesseract_cmd']
    ...
```

`load_settings()` never raises on missing file — returns defaults. It raises `ValueError` only on malformed JSON. No try/except needed around the call.

### Module-level constant naming
**Source:** `pipeline/converter.py` lines 18-26
**Apply to:** `pipeline/detector.py`

All private constants use leading underscore: `_TARGET_W`, `_TOLERANCE`. For detector: `_HEADER_STRIP`, `_FOOTER_STRIP`. Include a comment with the pixel dimensions and why they were chosen (mirrors the `_TOLERANCE` explanatory comment pattern).

### In-test imports (deferred module loading)
**Source:** `tests/test_phase2.py` lines 31-34
**Apply to:** `tests/test_phase3.py`

All `from pipeline import ...` imports are inside test function bodies, not at the module top level. This is consistent across both existing test files and must be maintained in `test_phase3.py`.

### Fixture from conftest — no re-declaration
**Source:** `tests/conftest.py` lines 7-20
**Apply to:** `tests/test_phase3.py`

`test_pdf_path` and `sample_settings` are already defined in `tests/conftest.py` with `scope="session"`. Do not redeclare them in `test_phase3.py`. Accept them as function parameters: `def test_foo(test_pdf_path):`.

---

## No Analog Found

None — all three files have strong analogs in the existing codebase.

---

## Metadata

**Analog search scope:** `pipeline/`, `tests/`, `config_loader.py`
**Files scanned:** 6 (`pipeline/converter.py`, `pipeline/preprocessor.py`, `pipeline/__init__.py`, `tests/test_phase2.py`, `tests/test_phase1.py`, `tests/conftest.py`, `config_loader.py`)
**Pattern extraction date:** 2026-05-01
