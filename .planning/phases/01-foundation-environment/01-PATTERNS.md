# Phase 1: Foundation & Environment - Pattern Map

**Mapped:** 2026-04-28
**Files analyzed:** 10 (files to be created by Phase 1)
**Analogs found:** 0 / 10 — new project; no existing source code in repository

---

## New-Project Note

The repository contains only `CLAUDE.md`, `test.pdf`, and `.planning/` documents. There are no
existing Python source files to draw analogs from. All patterns below are conventional Python
patterns drawn from the verified code examples in `01-RESEARCH.md`. The planner should treat
RESEARCH.md Pattern 1–6 excerpts as the authoritative "copy from" references.

---

## File Classification

| New File | Role | Data Flow | Closest Analog | Match Quality |
|----------|------|-----------|----------------|---------------|
| `setup_check.py` | utility / entry-point-helper | request-response (subprocess probe) | None (new project) | — |
| `config_loader.py` | utility | transform (file → dict) | None (new project) | — |
| `settings.json` | config | — | None (new project) | — |
| `main.py` | entry-point stub | — | None (new project) | — |
| `models/__init__.py` | package marker | — | None (new project) | — |
| `models/field_result.py` | model / dataclass | transform | None (new project) | — |
| `config/__init__.py` | package marker | — | None (new project) | — |
| `config/base.py` | model / dataclass | transform | None (new project) | — |
| `config/cms1500.py` | config stub | — | None (new project) | — |
| `config/ub04.py` | config stub | — | None (new project) | — |
| `tests/__init__.py` | package marker | — | None (new project) | — |
| `tests/test_phase1.py` | test | request-response (unit) | None (new project) | — |

---

## Pattern Assignments

### `setup_check.py` (utility, request-response)

**Source:** RESEARCH.md Pattern 1 (lines 208–267) — verified by direct execution on this machine.

**Imports pattern:**
```python
import subprocess
import sys
from pathlib import Path
```

**Core dual-role pattern:**
```python
def _check_binary(path: str, binary_name: str, source: str) -> tuple[bool, str]:
    """Returns (ok, message). source is 'settings.json' or 'built-in default'."""
    try:
        subprocess.run(
            [path, "--version"],
            capture_output=True,
            shell=False,
            timeout=5,
        )
        return True, f"OK: {binary_name} found at {path} (from {source})"
    except FileNotFoundError:
        return False, f"ERROR: {binary_name} not found at {path} (from {source})"
    except PermissionError:
        return False, f"ERROR: {binary_name} at {path} is not executable (from {source})"


def run_checks(settings: dict | None = None, quiet: bool = False) -> bool:
    """Run dependency checks. Returns True if all pass.

    Accepts a pre-loaded settings dict or loads its own.
    quiet=True suppresses print output (for use at app startup before UI exists).
    """
    if settings is None:
        from config_loader import load_settings
        settings = load_settings()

    results = []

    tess_path = settings.get("tesseract_cmd", DEFAULTS["tesseract_cmd"])
    tess_source = "settings.json" if "tesseract_cmd" in settings else "built-in default"
    ok, msg = _check_binary(tess_path, "Tesseract", tess_source)
    results.append((ok, msg))

    pop_path = str(Path(settings.get("poppler_path", DEFAULTS["poppler_path"])) / "pdftoppm.exe")
    pop_source = "settings.json" if "poppler_path" in settings else "built-in default"
    ok, msg = _check_binary(pop_path, "Poppler (pdftoppm)", pop_source)
    results.append((ok, msg))

    all_ok = all(r[0] for r in results)
    if not quiet:
        for _, msg in results:
            print(msg)
    return all_ok


if __name__ == "__main__":
    ok = run_checks()
    sys.exit(0 if ok else 1)
```

**Key constraints (from D-01 to D-04):**
- `shell=False` always — never `shell=True` or `shutil.which()`
- Error message format locked: `ERROR: {name} not found at {path} (from {source})`
- `run_checks()` must never be called at module import time (no top-level side effects)
- Poppler probe binary is `pdftoppm.exe` inside the directory, not the directory itself

---

### `config_loader.py` (utility, transform)

**Source:** RESEARCH.md Pattern 2 (lines 279–302) and Code Examples ENV-02 (lines 548–568).

**Imports pattern:**
```python
import json
import pathlib
```

**Core settings-load pattern:**
```python
_DEFAULTS = {
    "tesseract_cmd": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    "poppler_path":  r"C:\Program Files\poppler\Library\bin",
    "confidence_threshold": 60,
    "output_dir": str(pathlib.Path.home() / "Desktop"),
}

def load_settings(path: str | None = None) -> dict:
    """Load settings.json, returning defaults for any missing keys.
    Never raises on missing file. path defaults to settings.json beside this module."""
    if path is None:
        path = str(pathlib.Path(__file__).parent / "settings.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            user = json.load(f)
        return {**_DEFAULTS, **user}   # user keys override defaults
    except FileNotFoundError:
        return _DEFAULTS.copy()
    except json.JSONDecodeError as e:
        raise ValueError(f"settings.json is not valid JSON: {e}") from e
```

**Key notes:**
- Use `Path(__file__).parent / "settings.json"` — anchors to script location, not CWD
  (resolves RESEARCH.md Open Question 2)
- `confidence_threshold` is stored as integer `60`, not float `0.60`
- Shallow merge `{**_DEFAULTS, **user}` is sufficient — no deep merge needed

---

### `settings.json` (config)

**Source:** RESEARCH.md ENV-02 section; values verified on this machine.

**Template:**
```json
{
    "tesseract_cmd": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
    "poppler_path":  "C:\\Program Files\\poppler\\Library\\bin",
    "confidence_threshold": 60,
    "output_dir": "C:\\Users\\shset\\Desktop"
}
```

**Key notes:**
- File is optional — `config_loader.py` falls back to hardcoded defaults when absent
- Should be added to `.gitignore` (machine-specific paths)
- All four keys must be present in defaults even when absent from file

---

### `main.py` (entry-point stub)

**Source:** Conventional Python entry-point pattern; no OCR or UI code in Phase 1.

**Stub pattern:**
```python
"""OCR Medical Billing Form Extractor — main entry point.

Phase 6 will populate this file with the tkinter UI and full startup sequence.
"""

# TODO Phase 6: import and call setup_check.run_checks() before any UI is shown
# TODO Phase 6: build tkinter root window and start main loop
```

**Key constraint:** Must remain an empty stub in Phase 1 — no functional code yet.

---

### `models/__init__.py` and `config/__init__.py` (package markers)

**Pattern:** Standard Python package `__init__.py` with re-export of the public symbol.

```python
# models/__init__.py
from .field_result import FieldResult

__all__ = ["FieldResult"]
```

```python
# config/__init__.py
from .base import FieldDef, TableFieldDef

__all__ = ["FieldDef", "TableFieldDef"]
```

This allows callers to write `from models import FieldResult` rather than
`from models.field_result import FieldResult`.

---

### `models/field_result.py` (model, dataclass)

**Source:** RESEARCH.md Pattern 3 (lines 316–325) and Code Examples (lines 573–580).

**Full file pattern:**
```python
# models/field_result.py
from dataclasses import dataclass


@dataclass
class FieldResult:
    """OCR result for a single form field."""
    field_name: str    # matches FieldDef.name
    value: str         # raw OCR text, stripped
    confidence: float  # 0.0–100.0; -1.0 if no text found in region
```

**Key notes:**
- `confidence: float` — not int; allows fractional mean confidence scores
- Sentinel value `-1.0` means region contained no text (mirrors pytesseract's own -1 sentinel)
- Field order matters for positional construction: `FieldResult("box1", "JOHN", 87.5)`

---

### `config/base.py` (model, dataclass)

**Source:** RESEARCH.md Pattern 4 (lines 346–368) and Code Examples (lines 585–603).

**Full file pattern:**
```python
# config/base.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class FieldDef:
    """Coordinate definition for a single-value form field."""
    name: str                              # e.g. "box1a_insured_id"
    box: tuple[int, int, int, int]         # (left, top, right, bottom) at 300 DPI
    psm: int = 6                           # Tesseract PSM mode; 6=block, 7=line, 8=word
    whitelist: Optional[str] = None        # tessedit_char_whitelist; None = no restriction
    label: str = ""                        # display label for Phase 2 calibration overlay


@dataclass
class TableFieldDef:
    """Coordinate definition for a repeating row structure.

    Used for Box 24 service lines (6 rows) and UB-04 revenue lines (22 rows).
    row_boxes[i] is the pixel region for row i (0-indexed).
    """
    name: str                                          # e.g. "box24_cpt"
    row_boxes: list[tuple[int, int, int, int]]         # one (l,t,r,b) per row
    psm: int = 7                                       # single line default for table cells
    whitelist: Optional[str] = None
    label: str = ""
```

**PSM mode reference (from `tesseract.exe --help-extra`, verified):**
- `psm=6` (`single_block`): multi-line text regions (name/address boxes)
- `psm=7` (`single_line`): single-value fields (IDs, dates, codes, dollar amounts)
- `psm=8` (`single_word`): checkbox/indicator fields

**Key notes:**
- `box` is a plain 4-tuple — PIL `Image.crop()` takes this exact format; no unpacking needed
- `row_boxes` is a list of 4-tuples, one per table row — length 6 for CMS-1500 Box 24, 22 for UB-04
- `label` field enables Phase 2 calibration overlay without changing the core coord contract

---

### `config/cms1500.py` and `config/ub04.py` (config stubs)

**Pattern:** Empty stubs that establish importable module paths for Phase 2.

```python
# config/cms1500.py
"""CMS-1500 field coordinate definitions.

Populated with pixel coordinates in Phase 2 after calibration against test.pdf.
"""
from config.base import FieldDef, TableFieldDef  # noqa: F401 — available for Phase 2

CMS1500_FIELDS: list[FieldDef] = []          # Phase 2 populates
CMS1500_TABLE_FIELDS: list[TableFieldDef] = []  # Phase 2 populates
```

```python
# config/ub04.py
"""UB-04 field coordinate definitions.

Populated with pixel coordinates in Phase 2 after calibration against test.pdf.
"""
from config.base import FieldDef, TableFieldDef  # noqa: F401 — available for Phase 2

UB04_FIELDS: list[FieldDef] = []             # Phase 2 populates
UB04_TABLE_FIELDS: list[TableFieldDef] = []  # Phase 2 populates
```

---

### `tests/test_phase1.py` (test, unit)

**Source:** RESEARCH.md Validation Architecture section (lines 697–715); pytest conventions.

**Full file pattern:**
```python
# tests/test_phase1.py
"""Phase 1 tests — ENV-01 (dependency check) and ENV-02 (settings + imports)."""
import subprocess
import sys
from pathlib import Path

import pytest

# --- ENV-01: setup_check behavior ---

def test_checks_pass():
    """run_checks() returns True when both binaries exist at configured paths."""
    import setup_check
    assert setup_check.run_checks(quiet=True) is True


def test_tesseract_missing():
    """run_checks() returns False when tesseract path is bogus."""
    import setup_check
    bogus = {"tesseract_cmd": r"C:\nonexistent\tesseract.exe",
             "poppler_path": setup_check.DEFAULTS["poppler_path"]}
    assert setup_check.run_checks(settings=bogus, quiet=True) is False


def test_poppler_missing():
    """run_checks() returns False when poppler path is bogus."""
    import setup_check
    bogus = {"tesseract_cmd": setup_check.DEFAULTS["tesseract_cmd"],
             "poppler_path": r"C:\nonexistent\poppler\bin"}
    assert setup_check.run_checks(settings=bogus, quiet=True) is False


def test_standalone_exit_ok(tmp_path):
    """python setup_check.py exits 0 when binaries are reachable."""
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent.parent / "setup_check.py")],
        capture_output=True,
    )
    assert result.returncode == 0


# --- ENV-02: settings + imports ---

def test_defaults_no_file(tmp_path, monkeypatch):
    """load_settings() returns all 4 keys when settings.json is absent."""
    monkeypatch.chdir(tmp_path)
    from config_loader import load_settings
    s = load_settings(path=str(tmp_path / "settings.json"))
    assert "tesseract_cmd" in s
    assert "poppler_path" in s
    assert "confidence_threshold" in s
    assert "output_dir" in s


def test_settings_override(tmp_path):
    """load_settings() merges user values over defaults."""
    import json
    cfg = tmp_path / "settings.json"
    cfg.write_text(json.dumps({"confidence_threshold": 80}), encoding="utf-8")
    from config_loader import load_settings
    s = load_settings(path=str(cfg))
    assert s["confidence_threshold"] == 80
    assert "tesseract_cmd" in s  # default still present


def test_imports():
    """FieldResult, FieldDef, TableFieldDef are importable from expected locations."""
    from models import FieldResult
    from config.base import FieldDef, TableFieldDef

    # Basic instantiation
    fr = FieldResult(field_name="box1", value="MEDICARE", confidence=95.0)
    assert fr.value == "MEDICARE"

    fd = FieldDef(name="box1a", box=(10, 20, 100, 40))
    assert fd.psm == 6  # default

    tfd = TableFieldDef(name="box24_cpt", row_boxes=[(10, 50, 100, 70)] * 6)
    assert tfd.psm == 7  # default
    assert len(tfd.row_boxes) == 6
```

---

## Shared Patterns

### No-side-effect module imports

**Apply to:** `setup_check.py`, `config_loader.py`, all `__init__.py` files

All module-level code must be pure definitions (constants, function/class definitions).
No I/O, no subprocess calls, no `sys.exit()` at import time.

```python
# CORRECT — side effects inside function, guarded block
def run_checks(...): ...

if __name__ == "__main__":
    ok = run_checks()
    sys.exit(0 if ok else 1)

# WRONG — side effects at module scope
run_checks()        # runs on every import
sys.exit(1)         # kills the process on import
```

### Path anchoring

**Apply to:** `config_loader.py` (settings.json location), any file that opens resources

Use `Path(__file__).parent` to anchor file paths to the module's directory, not the
current working directory. This makes the app launch-directory-independent.

```python
# CORRECT
settings_path = Path(__file__).parent / "settings.json"

# WRONG — breaks when launched from a different directory
settings_path = Path("settings.json")
```

### subprocess shell=False

**Apply to:** `setup_check.py` and any future binary probe code

Always pass a list to `subprocess.run()` with `shell=False`. Never use `shell=True`
or `shutil.which()` for binary detection (D-02).

```python
# CORRECT
subprocess.run([exe_path, "--version"], capture_output=True, shell=False, timeout=5)

# WRONG — bypasses exact-path check
subprocess.run(f"{exe_path} --version", shell=True)
```

### Error message format (D-03)

**Apply to:** `setup_check.py` error strings

```python
# OK path
f"OK: {binary_name} found at {path} (from {source})"
# source is one of: "settings.json" or "built-in default"

# ERROR path
f"ERROR: {binary_name} not found at {path} (from {source})"
```

---

## No Analog Found

All Phase 1 files have no existing analog — this is the first phase of a new project.
The planner should use RESEARCH.md Pattern 1–6 excerpts and the excerpts above as the
authoritative copy-from references.

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| All 12 files listed above | various | various | New project — no existing source code in repository |

---

## Metadata

**Analog search scope:** Full project root — `CLAUDE.md`, `test.pdf`, `.planning/` only; no Python source files present
**Files scanned:** 0 Python source files (none exist yet)
**Pattern extraction date:** 2026-04-28
**Primary reference:** `.planning/phases/01-foundation-environment/01-RESEARCH.md` Patterns 1–6 and Code Examples sections
