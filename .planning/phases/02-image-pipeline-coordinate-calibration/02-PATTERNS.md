# Phase 2: Image Pipeline & Coordinate Calibration - Pattern Map

**Mapped:** 2026-04-29
**Files analyzed:** 8
**Analogs found:** 8 / 8

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `pipeline/__init__.py` | package init | — | `config/__init__.py` | exact |
| `pipeline/converter.py` | utility / I/O | file-I/O | `setup_check.py` | role-match |
| `pipeline/preprocessor.py` | utility / transform | transform | `setup_check.py` (function structure) | role-match |
| `pipeline/calibrate.py` | CLI script | file-I/O | `setup_check.py` (argparse + main guard) | role-match |
| `config/cms1500.py` | config | — | `config/ub04.py` (mirrored structure) | exact |
| `config/ub04.py` | config | — | `config/cms1500.py` (mirrored structure) | exact |
| `config_loader.py` | config / utility | — | self (modify existing `_DEFAULTS`) | exact |
| `tests/test_phase2.py` | test | — | `tests/test_phase1.py` | exact |

---

## Pattern Assignments

### `pipeline/__init__.py` (package init)

**Analog:** `config/__init__.py` (lines 1–3) and `models/__init__.py` (lines 1–3)

Both existing package inits use relative imports plus `__all__`. The `pipeline/` package follows the exact same shape, re-exporting the two public functions.

**Init pattern** (`config/__init__.py` lines 1–3):
```python
from .base import FieldDef, TableFieldDef

__all__ = ["FieldDef", "TableFieldDef"]
```

**Apply as** (`pipeline/__init__.py`):
```python
from .converter import convert_page
from .preprocessor import preprocess_page

__all__ = ["convert_page", "preprocess_page"]
```

---

### `pipeline/converter.py` (utility, file-I/O)

**Analog:** `setup_check.py`

Key patterns to copy: deferred import of `load_settings` inside the function body is acceptable (see `setup_check.py` line 59), but for `converter.py` the import should be at module level since it is always needed. The binary-path pattern (never rely on PATH, always read from `settings`) is the critical convention.

**Module-level docstring pattern** (`setup_check.py` lines 1–11):
```python
"""Dependency validator for OCR Medical Billing Form Extractor.

Standalone usage:
    ...
Importable usage:
    ...
"""
```

**Settings load + explicit binary path pattern** (`setup_check.py` lines 58–66):
```python
def run_checks(settings=None, quiet: bool = False) -> bool:
    if settings is None:
        from config_loader import load_settings
        settings = load_settings()

    # Always read path from settings; never rely on PATH
    tess_path = settings.get("tesseract_cmd", DEFAULTS["tesseract_cmd"])
```

**Apply as** (`pipeline/converter.py`):
```python
"""PDF-to-PIL converter for OCR Medical Billing Form Extractor."""
from pdf2image import convert_from_path
from config_loader import load_settings


def convert_page(pdf_path: str, page_num: int) -> "PIL.Image.Image":
    """Convert one PDF page to a 300 DPI PIL Image.

    Args:
        pdf_path: Absolute or relative path to the PDF.
        page_num: 0-indexed page number.

    Returns:
        PIL.Image.Image, mode "RGB", size 2550x3300 px.

    Raises:
        ValueError: If resulting image is not exactly 2550x3300 px (D-13).
        FileNotFoundError: If pdf_path does not exist.
    """
    settings = load_settings()
    pages = convert_from_path(
        pdf_path,
        dpi=300,
        first_page=page_num + 1,   # pdf2image is 1-indexed
        last_page=page_num + 1,
        poppler_path=settings["poppler_path"],
    )
    image = pages[0]
    if image.size != (2550, 3300):
        raise ValueError(
            f"Expected 2550x3300 px at 300 DPI, got {image.size} "
            f"(page {page_num}, {pdf_path!r})"
        )
    return image
```

**Error type convention:** `ValueError` for validation failures (not `sys.exit`), so callers can handle it. See `config_loader.py` lines 41–42:
```python
    except json.JSONDecodeError as e:
        raise ValueError(f"settings.json is not valid JSON: {e}") from e
```

---

### `pipeline/preprocessor.py` (utility, transform)

**Analog:** `setup_check.py` (function structure and error-raise pattern)

No direct OpenCV analog exists in the codebase. Use `setup_check.py` for function signature and error-handling conventions; use RESEARCH.md code patterns for the OpenCV body.

**Function signature + docstring pattern** (`setup_check.py` lines 48–55):
```python
def run_checks(settings=None, quiet: bool = False) -> bool:
    """Check that Tesseract and Poppler binaries are reachable at configured paths.

    Args:
        settings: Pre-loaded settings dict. If None, loads from config_loader.
        quiet: If True, suppresses print output ...

    Returns:
        True if all dependency checks pass; False if any fail.
    """
```

**Settings key access with default pattern** (`config_loader.py` lines 38–40):
```python
    return {**_DEFAULTS, **user}   # user keys override defaults
```
and in `setup_check.py` lines 65–66:
```python
    tess_path = settings.get("tesseract_cmd", DEFAULTS["tesseract_cmd"])
    tess_source = "settings.json" if "tesseract_cmd" in settings else "built-in default"
```

**Apply as** (`pipeline/preprocessor.py` public signature):
```python
def preprocess_page(
    image: "PIL.Image.Image",
    settings: dict,
    debug: bool = False,
) -> "PIL.Image.Image":
    """Apply scale correction, deskew, and adaptive threshold.

    Args:
        image: Raw PIL Image from convert_page() — 2550x3300, mode "RGB".
        settings: dict from load_settings(); reads threshold_block_size (default 31).
        debug: If True, saves intermediate PNGs to project root.

    Returns:
        Preprocessed PIL Image (same dimensions, mode "RGB").

    Raises:
        ValueError: If detected skew angle exceeds ±5° (D-10).
    """
    block_size = settings.get("threshold_block_size", 31)
    if block_size % 2 == 0:
        block_size += 1
    ...
```

**ValueError raise pattern** (mirrors `config_loader.py` line 42 and `setup_check.py` implicit non-zero exit):
```python
    if abs(skew_angle) > 5.0:
        raise ValueError(
            f"Skew angle {skew_angle:.1f}° exceeds ±5° limit — "
            "manual review required"
        )
```

---

### `pipeline/calibrate.py` (CLI script, file-I/O)

**Analog:** `setup_check.py` (complete argparse + `if __name__ == "__main__"` pattern)

**Argparse + main guard pattern** (`setup_check.py` lines 84–103):
```python
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check OCR dependency binaries.")
    parser.add_argument(
        "--settings",
        metavar="PATH",
        default=None,
        help="Path to settings.json (default: settings.json beside this script)",
    )
    args = parser.parse_args()

    if args.settings is not None:
        from config_loader import load_settings
        _settings = load_settings(path=args.settings)
    else:
        _settings = None

    ok = run_checks(settings=_settings)
    sys.exit(0 if ok else 1)
```

**Apply as** (`pipeline/calibrate.py` main guard):
```python
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Render calibration overlay PNG for a PDF page."
    )
    parser.add_argument("--page", type=int, required=True, help="0-indexed page number")
    parser.add_argument("--pdf", required=True, help="Path to PDF file")
    parser.add_argument(
        "--form",
        choices=["cms1500", "ub04"],
        default=None,
        help="Force form type (default: auto-detect)",
    )
    args = parser.parse_args()

    _run(pdf_path=args.pdf, page_num=args.page, form_type=args.form)
    sys.exit(0)
```

**Imports pattern** (`setup_check.py` lines 1–15 — module-level stdlib, deferred project imports inside functions):
```python
import subprocess
import sys
from pathlib import Path
# project imports deferred to inside functions where appropriate
```

**Path construction via pathlib** (`setup_check.py` line 73):
```python
    pop_exe = str(Path(pop_dir) / "pdftoppm.exe")
```

Apply the same `Path` usage for the output PNG path:
```python
    out_path = Path(f"calibration_overlay_p{page_num}.png")
```

---

### `config/cms1500.py` (config — populate lists)

**Analog:** `config/ub04.py` (exact mirror structure); both currently empty.

**Current file structure** (`config/cms1500.py` lines 1–8):
```python
"""CMS-1500 field coordinate definitions.

Populated with pixel coordinates in Phase 2 after calibration against test.pdf.
"""
from config.base import FieldDef, TableFieldDef  # noqa: F401 -- available for Phase 2

CMS1500_FIELDS: list[FieldDef] = []            # Phase 2 populates
CMS1500_TABLE_FIELDS: list[TableFieldDef] = [] # Phase 2 populates
```

**FieldDef instantiation pattern** (`config/base.py` lines 6–13 — dataclass field order):
```python
@dataclass
class FieldDef:
    name: str                              # positional arg 1
    box: tuple[int, int, int, int]         # positional arg 2 — (left, top, right, bottom)
    psm: int = 6                           # keyword, default 6
    whitelist: Optional[str] = None        # keyword, default None
    label: str = ""                        # keyword, default ""
```

**TableFieldDef instantiation pattern** (`config/base.py` lines 16–27):
```python
@dataclass
class TableFieldDef:
    name: str                                        # positional arg 1
    row_boxes: list[tuple[int, int, int, int]]       # positional arg 2 — list of (l,t,r,b)
    psm: int = 7                                     # keyword, default 7
    whitelist: Optional[str] = None
    label: str = ""
```

**Verified usage example** (`tests/test_phase1.py` lines 120–127 — canonical instantiation):
```python
    fd = FieldDef(name="box1a", box=(10, 20, 100, 40))
    assert fd.psm == 6  # default

    tfd = TableFieldDef(name="box24_cpt", row_boxes=[(10, 50, 100, 70)] * 6)
    assert tfd.psm == 7  # default
    assert len(tfd.row_boxes) == 6
```

**Apply as** (representative excerpt for `CMS1500_FIELDS`):
```python
CMS1500_FIELDS: list[FieldDef] = [
    FieldDef(
        name="claim_member_id",
        box=(30, 160, 1200, 220),
        psm=7,
        whitelist=None,
        label="Claim/Member ID",
    ),
    FieldDef(
        name="box1_insurance_type",
        box=(30, 220, 800, 270),
        psm=7,
        whitelist=None,
        label="Box 1 — Insurance Type",
    ),
    # ... (29 total FieldDef entries per RESEARCH.md §4.1)
]

CMS1500_TABLE_FIELDS: list[TableFieldDef] = [
    TableFieldDef(
        name="box24_date_from",
        row_boxes=[
            (30, 1130, 220, 1280),  # SL1
            (30, 1280, 220, 1430),  # SL2
            (30, 1430, 220, 1580),  # SL3
            (30, 1580, 220, 1730),  # SL4
            (30, 1730, 220, 1880),  # SL5
            (30, 1880, 220, 2030),  # SL6
        ],
        psm=7,
        whitelist="0123456789/ ",
        label="Box 24 — Date From",
    ),
    # ... (10 total TableFieldDef entries per RESEARCH.md §4.2)
]
```

---

### `config/ub04.py` (config — populate lists)

**Analog:** `config/cms1500.py` — exact mirror. Same import block, same list type annotations, same `FieldDef` / `TableFieldDef` instantiation pattern.

**Current file structure** (`config/ub04.py` lines 1–8):
```python
"""UB-04 field coordinate definitions.

Populated with pixel coordinates in Phase 2 after calibration against test.pdf.
"""
from config.base import FieldDef, TableFieldDef  # noqa: F401 -- available for Phase 2

UB04_FIELDS: list[FieldDef] = []             # Phase 2 populates
UB04_TABLE_FIELDS: list[TableFieldDef] = []  # Phase 2 populates
```

**Apply as** (representative excerpt for `UB04_FIELDS`):
```python
UB04_FIELDS: list[FieldDef] = [
    FieldDef(
        name="box1_provider_name_addr",
        box=(30, 30, 1270, 200),
        psm=6,
        whitelist=None,
        label="Box 1 — Provider Name/Address",
    ),
    # ... (24 total FieldDef entries per RESEARCH.md §5.1)
]

UB04_TABLE_FIELDS: list[TableFieldDef] = [
    TableFieldDef(
        name="ub04_rl_rev_code",
        row_boxes=[
            (30, 410,  200, 515),   # RL1
            (30, 515,  200, 620),   # RL2
            # ... 22 rows total per RESEARCH.md §5.2
        ],
        psm=7,
        whitelist="0123456789",
        label="UB-04 Revenue Line — Rev Code",
    ),
    # ... (7 total TableFieldDef entries per RESEARCH.md §5.2)
]
```

---

### `config_loader.py` (modify — add `threshold_block_size` to `_DEFAULTS`)

**Target:** Add one key to the existing `_DEFAULTS` dict. No structural change.

**Existing `_DEFAULTS` block** (`config_loader.py` lines 11–16):
```python
_DEFAULTS: dict = {
    "tesseract_cmd": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    "poppler_path": r"C:\Program Files\poppler\Library\bin",
    "confidence_threshold": 60,
    "output_dir": str(pathlib.Path.home() / "Desktop"),
}
```

**Apply as** (add one line, keep all existing keys unchanged):
```python
_DEFAULTS: dict = {
    "tesseract_cmd": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    "poppler_path": r"C:\Program Files\poppler\Library\bin",
    "confidence_threshold": 60,
    "output_dir": str(pathlib.Path.home() / "Desktop"),
    "threshold_block_size": 31,
}
```

No other changes to `config_loader.py`. The merge logic (`{**_DEFAULTS, **user}`) already handles the new key correctly for both absent-key and override cases.

---

### `tests/test_phase2.py` (test)

**Analog:** `tests/test_phase1.py` — exact structural match.

**File header + section comment pattern** (`tests/test_phase1.py` lines 1–9):
```python
# tests/test_phase1.py
"""Phase 1 tests — ENV-01 (dependency check) and ENV-02 (settings + imports).

Skip markers are removed by Wave 1 plans as each feature is implemented:
  ...
"""
import subprocess
import sys
from pathlib import Path

import pytest
```

**Section separator pattern** (`tests/test_phase1.py` lines 17–19):
```python
# ---------------------------------------------------------------------------
# ENV-01: setup_check behavior
# ---------------------------------------------------------------------------
```

**Unit test with inline import pattern** (`tests/test_phase1.py` lines 21–24):
```python
def test_checks_pass():
    """run_checks() returns True when both binaries exist at configured paths."""
    import setup_check
    assert setup_check.run_checks(quiet=True) is True
```

**`tmp_path` fixture for file-isolation** (`tests/test_phase1.py` lines 88–97):
```python
def test_defaults_no_file(tmp_path):
    """load_settings() returns all 4 keys when settings.json is absent."""
    from config_loader import load_settings

    s = load_settings(path=str(tmp_path / "settings.json"))
    assert "tesseract_cmd" in s
```

**`subprocess.run` smoke test pattern** (`tests/test_phase1.py` lines 47–53):
```python
def test_standalone_exit_ok():
    """python setup_check.py exits 0 when binaries are reachable."""
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent.parent / "setup_check.py")],
        capture_output=True,
    )
    assert result.returncode == 0
```

**`pytest.raises` pattern** (`tests/test_phase1.py` lines 56–81 — tempfile + raises combo):
```python
    result = subprocess.run([...], capture_output=True)
    assert result.returncode == 1
```

**Apply as** (section structure for `tests/test_phase2.py`):
```python
# tests/test_phase2.py
"""Phase 2 tests — PROC-01 (converter), PROC-02 (preprocessor), EXTR-04 (calibration).

Skip markers are removed by Wave 2 plans as each feature is implemented.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Project root for fixture PDF
_ROOT = Path(__file__).parent.parent
_TEST_PDF = str(_ROOT / "test.pdf")

# ---------------------------------------------------------------------------
# PROC-01: convert_page
# ---------------------------------------------------------------------------

def test_convert_page_dimensions():
    from pipeline import convert_page
    image = convert_page(_TEST_PDF, 0)
    assert image.size == (2550, 3300)


def test_convert_page_mode():
    from pipeline import convert_page
    image = convert_page(_TEST_PDF, 0)
    assert image.mode == "RGB"


def test_convert_page_invalid_pdf():
    from pipeline import convert_page
    with pytest.raises(Exception):
        convert_page("nonexistent.pdf", 0)


# ---------------------------------------------------------------------------
# PROC-02: preprocess_page
# ---------------------------------------------------------------------------

def test_preprocess_smoke():
    from pipeline import convert_page, preprocess_page
    from config_loader import load_settings
    image = convert_page(_TEST_PDF, 0)
    result = preprocess_page(image, load_settings())
    assert result.size == (2550, 3300)


def test_preprocess_mode():
    from pipeline import convert_page, preprocess_page
    from config_loader import load_settings
    image = convert_page(_TEST_PDF, 0)
    result = preprocess_page(image, load_settings())
    assert result.mode == "RGB"


def test_deskew_rejection():
    """Artificially rotated image (6°) raises ValueError."""
    import numpy as np
    import cv2
    from PIL import Image
    from pipeline.preprocessor import preprocess_page
    from config_loader import load_settings

    # Rotate test page by 6° to exceed ±5° threshold
    from pipeline import convert_page
    raw = convert_page(_TEST_PDF, 0)
    cv_img = cv2.cvtColor(np.array(raw), cv2.COLOR_RGB2BGR)
    h, w = cv_img.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), 6.0, 1.0)
    rotated = cv2.warpAffine(cv_img, M, (w, h))
    pil_rotated = Image.fromarray(cv2.cvtColor(rotated, cv2.COLOR_BGR2RGB))

    with pytest.raises(ValueError, match="exceeds"):
        preprocess_page(pil_rotated, load_settings())


# ---------------------------------------------------------------------------
# EXTR-04: calibrate.py CLI
# ---------------------------------------------------------------------------

def test_calibrate_overlay_created(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(_ROOT / "pipeline" / "calibrate.py"),
            "--page", "0",
            "--pdf", _TEST_PDF,
        ],
        capture_output=True,
        cwd=str(tmp_path),
    )
    assert result.returncode == 0
    assert (tmp_path / "calibration_overlay_p0.png").exists()


def test_calibrate_overlay_nonempty(tmp_path):
    subprocess.run(
        [sys.executable, str(_ROOT / "pipeline" / "calibrate.py"),
         "--page", "0", "--pdf", _TEST_PDF],
        capture_output=True, cwd=str(tmp_path),
    )
    assert (tmp_path / "calibration_overlay_p0.png").stat().st_size > 1024


# ---------------------------------------------------------------------------
# Settings / config validation
# ---------------------------------------------------------------------------

def test_settings_threshold_block_size_default(tmp_path):
    from config_loader import load_settings
    s = load_settings(path=str(tmp_path / "settings.json"))
    assert s["threshold_block_size"] == 31


def test_cms1500_fields_populated():
    from config.cms1500 import CMS1500_FIELDS
    from config.base import FieldDef
    assert len(CMS1500_FIELDS) > 0
    assert all(isinstance(f, FieldDef) for f in CMS1500_FIELDS)


def test_ub04_fields_populated():
    from config.ub04 import UB04_FIELDS
    from config.base import FieldDef
    assert len(UB04_FIELDS) > 0
    assert all(isinstance(f, FieldDef) for f in UB04_FIELDS)


def test_cms1500_table_fields_row_count():
    from config.cms1500 import CMS1500_TABLE_FIELDS
    assert all(len(f.row_boxes) == 6 for f in CMS1500_TABLE_FIELDS)


def test_ub04_table_fields_row_count():
    from config.ub04 import UB04_TABLE_FIELDS
    assert all(len(f.row_boxes) == 22 for f in UB04_TABLE_FIELDS)
```

---

## Shared Patterns

### Windows Explicit Binary Path (all modules that call external tools)
**Source:** `config_loader.py` lines 11–16 + `setup_check.py` lines 17–20 and 65–66
**Apply to:** `pipeline/converter.py` (poppler_path), `pipeline/calibrate.py`
```python
# Always read from settings; never rely on system PATH
settings = load_settings()
poppler_path = settings["poppler_path"]   # "C:\Program Files\poppler\Library\bin"
```

### Settings-Driven Defaults (merge pattern)
**Source:** `config_loader.py` lines 36–40
**Apply to:** `config_loader.py` (`_DEFAULTS` extension), `pipeline/preprocessor.py` (reads `threshold_block_size`)
```python
return {**_DEFAULTS, **user}   # user keys override defaults; missing keys fall back
```
Consumers read via:
```python
block_size = settings.get("threshold_block_size", 31)
```

### ValueError for Validation Failures (not sys.exit)
**Source:** `config_loader.py` lines 41–42 (raise convention)
**Apply to:** `pipeline/converter.py` (dimension check), `pipeline/preprocessor.py` (deskew rejection)
```python
raise ValueError(f"<descriptive message with context>") from e
```
Callers can catch; Phase 6 pipeline catches `ValueError` to populate `extraction_error` column.

### pathlib for All Path Construction
**Source:** `config_loader.py` lines 9, 34 + `setup_check.py` lines 11, 73
**Apply to:** `pipeline/converter.py`, `pipeline/calibrate.py`, `tests/test_phase2.py`
```python
from pathlib import Path
path = pathlib.Path(__file__).parent / "settings.json"   # module-relative
out_path = Path(f"calibration_overlay_p{page_num}.png")  # output file
```

### Relative Imports in `__init__.py`
**Source:** `config/__init__.py` lines 1–3, `models/__init__.py` lines 1–3
**Apply to:** `pipeline/__init__.py`
```python
from .submodule import public_name
__all__ = ["public_name", ...]
```

### Test Inline Imports (inside test functions)
**Source:** `tests/test_phase1.py` lines 23, 30, 88
**Apply to:** `tests/test_phase2.py` — all test functions import from the module under test inside the function body, not at module level. This allows individual test isolation and avoids import-time failures from missing dependencies:
```python
def test_something():
    from pipeline import convert_page
    ...
```

### subprocess Smoke Test with `capture_output=True`
**Source:** `tests/test_phase1.py` lines 47–53
**Apply to:** `tests/test_phase2.py` calibrate CLI tests
```python
result = subprocess.run(
    [sys.executable, str(Path(__file__).parent.parent / "script.py"), "--arg", "val"],
    capture_output=True,
)
assert result.returncode == 0
```

---

## No Analog Found

All 8 files have analogs. No files require falling back to RESEARCH.md-only patterns.

Note: `pipeline/preprocessor.py` has no direct OpenCV analog in the codebase (the project has not previously used OpenCV). The function structure and error-handling conventions come from `setup_check.py`; the OpenCV body (PIL↔NumPy conversion, Hough deskew, adaptive threshold) comes from RESEARCH.md §2.1–2.4 which contains verified technical patterns.

---

## Metadata

**Analog search scope:** Project root — `config/`, `models/`, `tests/`, `config_loader.py`, `setup_check.py`, `main.py`
**Files scanned:** 10 source files read in full
**Pattern extraction date:** 2026-04-29
