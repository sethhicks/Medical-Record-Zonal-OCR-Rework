# Phase 1: Foundation & Environment - Research

**Researched:** 2026-04-28
**Domain:** Python project scaffolding, dependency validation, dataclass design, settings loading
**Confidence:** HIGH

---

## Summary

Phase 1 lays the importable foundation for all downstream phases: a project skeleton, a dual-role
dependency checker (`setup_check.py`), a settings loader (`settings.json` + hardcoded Windows
defaults), and three shared dataclasses (`FieldResult`, `FieldDef`, `TableFieldDef`). No OCR,
image processing, or UI code belongs here.

All major stack components are already installed and verified on this machine. Tesseract 5.5.0 is
at `C:\Program Files\Tesseract-OCR\tesseract.exe`. Poppler 25.12.0 is at
`C:\Program Files\poppler\Library\bin`. pdf2image 1.17.0 and pytesseract 0.3.13 are installed
under Python 3.10.6 and confirmed working together against `test.pdf`.

**Critical note on Python version:** CLAUDE.md and STATE.md specify Python 3.11. The machine
currently has Python 3.10.6 only — Python 3.11 is not installed. This is flagged as an open
question. All stdlib APIs needed (dataclasses, json, pathlib, subprocess, sys) are identical
between 3.10 and 3.11, so Phase 1 code is unaffected, but this must be resolved before
Phase 2 uses OpenCV (which has wheel gaps on Windows for 3.12/3.13, not 3.11 — 3.11 wheels exist).

**Primary recommendation:** Build `setup_check.py` as a module-level function `run_checks(quiet=False)
-> bool` called by `if __name__ == "__main__"` for standalone use and imported by app startup.
Use `subprocess.run(..., shell=False)` with `FileNotFoundError` catch as the detection
mechanism — do not rely on pytesseract's own error messages.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Poppler is the only supported PDF backend. No PyMuPDF fallback or alternative. If
  Poppler is absent, `setup_check.py` exits non-zero with a clear error — it does not attempt to
  switch backends or suggest alternatives beyond pointing to the download.
- **D-02:** `setup_check.py` reads paths from `settings.json` only (`tesseract_cmd`,
  `poppler_path`). If `settings.json` is absent it falls back to hardcoded Windows defaults
  (e.g. `C:\Program Files\Tesseract-OCR\tesseract.exe`). No PATH lookup is attempted —
  `subprocess` shell=False with the explicit path is the only check.
- **D-03:** Error messages name the specific binary and show exactly where the app looked:
  `ERROR: Tesseract not found at C:\Program Files\Tesseract-OCR\tesseract.exe (from
  settings.json)`. Sufficient detail to fix the issue without opening source code.
- **D-04:** `setup_check.py` serves dual roles — it is both a standalone script
  (`python setup_check.py` prints OK/ERROR per binary and exits) and called at app startup.
  On startup failure the app surfaces the error before showing any window (or via a simple
  messagebox) rather than crashing mid-session.

### Claude's Discretion

- **Project layout:** directory structure (flat vs. src/ package), module names, where
  `setup_check.py` lives. ROADMAP.md success criteria names `models/` for `FieldResult` and
  `config/` for `FieldDef`/`TableFieldDef` — those locations are fixed.
- **FieldDef / TableFieldDef schema:** what fields each dataclass carries beyond pixel
  coordinates (PSM mode, whitelist, label, etc.). These are the shared interface consumed by
  Phases 2–4; design for that downstream use.
- **settings.json Windows defaults:** concrete default paths for `tesseract_cmd` and
  `poppler_path` (use standard Windows install locations), and sensible default for `output_dir`
  (e.g. user's Desktop or same directory as input PDF).

### Deferred Ideas (OUT OF SCOPE)

None.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ENV-01 | Application verifies Tesseract and Poppler are installed and reachable at startup via `setup_check.py`; displays a clear error and exits if either is missing | Verified: `subprocess.run(shell=False)` raises `FileNotFoundError` on missing binary — caught cleanly. Tesseract at `C:\Program Files\Tesseract-OCR\tesseract.exe`, Poppler at `C:\Program Files\poppler\Library\bin\pdftoppm.exe`. Both confirmed reachable on this machine. |
| ENV-02 | Application reads `settings.json` for `tesseract_cmd`, `poppler_path`, `confidence_threshold`, and `output_dir`; uses sensible defaults if file is absent | Verified: `json.load` + `FileNotFoundError` catch with `{**DEFAULTS, **user}` merge tested and confirmed. Desktop default path resolves to `C:\Users\shset\Desktop`. |
</phase_requirements>

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Dependency validation | Standalone script + app startup | — | Pure Python subprocess calls; no UI layer needed. Dual role via `if __name__ == "__main__"` |
| Settings loading | App startup (module import) | — | stdlib json only; result passed down to all consumers |
| FieldResult dataclass | `models/` module | — | Return type contract for Phases 3–4 extractors |
| FieldDef / TableFieldDef | `config/` module | — | Coordinate contract consumed by Phases 2–4; populated in Phase 2 |
| Project layout | Flat project root | — | Small desktop app; no src/ layout overhead needed |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytesseract | 0.3.13 | Python wrapper for Tesseract; `tesseract_cmd` assignment; `image_to_data` for per-word conf scores | Installed, verified working |
| pdf2image | 1.17.0 | `convert_from_path(poppler_path=...)` — PDF to PIL Image list | Installed, verified working |
| Pillow | 12.2.0 | PIL Image type used by both pdf2image and pytesseract | Installed |
| dataclasses | stdlib | `@dataclass` for FieldResult, FieldDef, TableFieldDef | Python stdlib ≥3.7 |
| json | stdlib | `settings.json` loading | Python stdlib |
| pathlib | stdlib | `Path.exists()` / `Path.is_file()` for binary detection | Python stdlib |
| subprocess | stdlib | `subprocess.run(shell=False)` for binary version check | Python stdlib |
| sys | stdlib | `sys.exit(1)` for non-zero exit on validation failure | Python stdlib |

[VERIFIED: pip show + direct python execution on this machine]

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| opencv-python | 4.13.0.92 | Image preprocessing | Phase 2 onwards — not needed in Phase 1 |
| openpyxl | 3.1.5 | Excel output | Phase 5 — not needed in Phase 1 |
| numpy | 2.2.6 | Array ops for OpenCV | Phase 2 onwards |
| tkinter | stdlib | Desktop UI | Phase 6 — not needed in Phase 1 |

[VERIFIED: pip show on this machine]

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Poppler (pdf2image) | PyMuPDF | **Locked D-01** — Poppler only |
| subprocess binary check | pytesseract.get_tesseract_version() | pytesseract raises its own TesseractNotFoundError but message wording is fixed; subprocess gives full control over the error message per D-03 |
| json stdlib | pydantic Settings | Pydantic is heavier; project scope and CONTEXT.md preference is simple/stdlib |
| pathlib.Path.exists() | os.path.exists() | pathlib is idiomatic Python 3; functionally equivalent |

**Installation (already installed on this machine):**
```bash
pip install pytesseract pdf2image pillow
```

---

## Architecture Patterns

### System Architecture Diagram

```
settings.json (optional)
        |
        v
load_settings() -----> settings dict
        |                    |
        |          +---------+---------+
        |          |                   |
        v          v                   v
  tesseract_cmd  poppler_path   confidence_threshold, output_dir
        |          |
        v          v
  setup_check.run_checks()
        |          |
   [OK/ERROR]  [OK/ERROR]
        |
  if standalone: print + sys.exit
  if imported:   return bool -> caller decides (messagebox or sys.exit)

models/
  FieldResult(value, confidence, field_name)   <-- return type for all extraction

config/
  FieldDef(name, box, psm, whitelist, label)    <-- single-value field coords
  TableFieldDef(name, row_boxes, psm, whitelist, label)  <-- repeating row coords
```

### Recommended Project Structure

```
OCR-Rework/
├── setup_check.py       # standalone + importable dependency validator
├── settings.json        # user config (gitignored; defaults in code)
├── main.py              # app entry point (Phase 6; created but empty stub OK in Phase 1)
├── models/
│   ├── __init__.py
│   └── field_result.py  # FieldResult dataclass
├── config/
│   ├── __init__.py
│   ├── base.py          # FieldDef, TableFieldDef dataclasses
│   ├── cms1500.py       # CMS-1500 field definitions (populated Phase 2)
│   └── ub04.py          # UB-04 field definitions (populated Phase 2)
├── tests/
│   ├── __init__.py
│   └── test_phase1.py   # ENV-01, ENV-02 validation tests
├── test.pdf             # reference sample (already present)
└── .planning/           # GSD planning files
```

Note: `cms1500.py` and `ub04.py` are created as empty stubs in Phase 1 so import paths work
from day one; they are populated with real coordinates in Phase 2.

[ASSUMED] — flat layout (no `src/`) is conventional for single-user desktop scripts of this
size. The `models/` and `config/` locations are fixed by ROADMAP.md success criteria.

### Pattern 1: Dual-Role setup_check.py

**What:** A module that exports a callable function for import AND behaves as a standalone
script when run directly.

**When to use:** Any validation script that must work both as `python script.py` (for the user
to test manually) and as `import script; script.run_checks()` at app startup.

**Example:**
```python
# setup_check.py
import subprocess
import sys
from pathlib import Path
from config_loader import load_settings  # or inline the load

DEFAULTS = {
    "tesseract_cmd": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    "poppler_path": r"C:\Program Files\poppler\Library\bin",
}

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

[VERIFIED: subprocess.run(shell=False) raises FileNotFoundError on missing binary, tested
on this machine]

### Pattern 2: Settings Loader

**What:** Load `settings.json` with a safe fallback to hardcoded defaults when file is absent.

**Example:**
```python
# config_loader.py (or inline in setup_check.py)
import json
import pathlib

_DEFAULTS = {
    "tesseract_cmd": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    "poppler_path": r"C:\Program Files\poppler\Library\bin",
    "confidence_threshold": 60,
    "output_dir": str(pathlib.Path.home() / "Desktop"),
}

def load_settings(path: str = "settings.json") -> dict:
    """Load settings.json, returning defaults for any missing keys.
    Never raises on missing file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            user = json.load(f)
        return {**_DEFAULTS, **user}   # user keys override defaults
    except FileNotFoundError:
        return _DEFAULTS.copy()
    except json.JSONDecodeError as e:
        # Malformed JSON is a user error — raise with clear message
        raise ValueError(f"settings.json is not valid JSON: {e}") from e
```

[VERIFIED: Tested on this machine — FileNotFoundError path returns defaults cleanly]

### Pattern 3: FieldResult Dataclass

**What:** The return type for every per-field OCR call in Phases 3–4. Carries the extracted
text and the Tesseract confidence score.

**Design rationale:** `image_to_data(output_type=Output.DICT)` returns a dict with a `conf`
list of per-word confidence integers (0–100, or -1 for structure rows with no text).
The aggregated confidence per region is derived from these values (e.g., mean of values > 0).

```python
# models/field_result.py
from dataclasses import dataclass

@dataclass
class FieldResult:
    """OCR result for a single form field."""
    field_name: str          # matches FieldDef.name
    value: str               # raw OCR text, stripped
    confidence: float        # 0.0–100.0; -1.0 if no text found in region
```

[VERIFIED: dataclasses stdlib confirmed. confidence=-1 sentinel for empty-region case is
consistent with pytesseract's own -1 conf values for structural rows]

### Pattern 4: FieldDef / TableFieldDef Dataclasses

**What:** Coordinate definitions consumed by Phases 2–4. Defined in Phase 1, populated with
real pixel values in Phase 2.

**PSM mode guidance (from Tesseract help, verified on this machine):**
- PSM 6 (`single_block`): multi-line text regions (name/address boxes, Box 5, Box 32, Box 33)
- PSM 7 (`single_line`): single-value fields (IDs, dates, codes, dollar amounts)
- PSM 8 (`single_word`): checkbox/indicator fields (Box 1 insurance type, Box 27 accept assignment)

```python
# config/base.py
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class FieldDef:
    """Coordinate definition for a single-value form field."""
    name: str                              # e.g. "box1a_insured_id"
    box: tuple[int, int, int, int]         # (left, top, right, bottom) at 300 DPI
    psm: int = 6                           # Tesseract PSM mode; 6=block, 7=line, 8=word
    whitelist: Optional[str] = None        # tessedit_char_whitelist value; None = no restriction
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

[VERIFIED: Instantiation tested on this machine, Python 3.10 syntax confirmed]

### Pattern 5: pytesseract Configuration

**What:** Assigning the Tesseract binary path and passing PSM/whitelist config.

```python
import pytesseract

# Set once at startup (before any OCR call)
pytesseract.pytesseract.tesseract_cmd = settings["tesseract_cmd"]

# Per-field OCR with PSM and whitelist
config = f"--psm {field_def.psm}"
if field_def.whitelist:
    config += f" -c tessedit_char_whitelist={field_def.whitelist}"

data = pytesseract.image_to_data(
    cropped_img,
    config=config,
    output_type=pytesseract.Output.DICT,
)
# data["conf"] is List[int], -1 for structural rows, 0-100 for text
# data["text"] is List[str]
```

[VERIFIED: tesseract_cmd assignment confirmed working. image_to_data DICT keys confirmed:
level, page_num, block_num, par_num, line_num, word_num, left, top, width, height, conf, text]

### Pattern 6: pdf2image with explicit poppler_path

**What:** Convert PDF page to PIL Image at 300 DPI.

```python
from pdf2image import convert_from_path

pages = convert_from_path(
    pdf_path,
    dpi=300,
    poppler_path=settings["poppler_path"],   # directory, not the binary itself
)
# Returns List[PIL.Image.Image]
```

**Note:** `poppler_path` takes the DIRECTORY containing `pdftoppm.exe`, not the path to the
binary itself. `C:\Program Files\poppler\Library\bin` is the correct value.

[VERIFIED: Tested on test.pdf — 1 page returned, size (2478, 3228), mode RGB]

### Anti-Patterns to Avoid

- **PATH lookup for binaries:** D-02 explicitly forbids PATH lookup. Never use
  `shutil.which("tesseract")` or `shell=True` subprocess.
- **pytesseract TesseractNotFoundError as the check:** pytesseract raises this with its own
  hardcoded message text. We need D-03's exact message format, so we check independently.
- **Crashing on missing settings.json:** FileNotFoundError must be caught; missing file means
  use defaults, not crash. This is success criterion #2.
- **Poppler path pointing to the exe:** pdf2image `poppler_path` parameter expects the
  directory containing the binaries, NOT a path to `pdftoppm.exe` itself.
- **Calling run_checks() at module import time:** run_checks() must only run when explicitly
  called (standalone) or called at app startup. Import must be side-effect-free.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Binary detection | Custom PATH scanner | `subprocess.run(shell=False)` + FileNotFoundError | Exact-path semantics match D-02; FileNotFoundError is reliable |
| Settings merging | Custom deep-merge | `{**DEFAULTS, **user_dict}` | One-level settings dict; simple shallow merge is sufficient |
| Tesseract version parsing | Custom text parsing | `pytesseract.get_tesseract_version()` | Returns a packaging.Version object; already installed |
| Dataclass serialization | Custom dict/JSON encoders | Not needed in Phase 1 | Phases 4–5 serialize FieldResult to Excel rows directly |

**Key insight:** This phase is pure scaffolding — stdlib json, subprocess, pathlib, and
dataclasses handle all needs without any third-party additions.

---

## Common Pitfalls

### Pitfall 1: pdf2image poppler_path expects directory, not binary
**What goes wrong:** `convert_from_path(poppler_path="C:\\...\\pdftoppm.exe")` raises FileNotFoundError
internally because pdf2image appends the binary name to the path.
**Why it happens:** The parameter name says "path" but semantically means "directory containing
poppler binaries."
**How to avoid:** Always pass the DIRECTORY: `C:\Program Files\poppler\Library\bin`
**Warning signs:** `pdf2image.exceptions.PDFInfoNotInstalledError` or FileNotFoundError in
pdf2image internals.

[VERIFIED: Confirmed by inspecting convert_from_path signature and testing on this machine]

### Pitfall 2: test.pdf pages are 2478x3228, not 2550x3300
**What goes wrong:** Phase 2 success criterion says "2550x3300 pixels"; actual pages are
2478x3228 at 300 DPI.
**Why it happens:** The PDF was scanned at slightly less than exactly 8.5x11 in (or the scanner
cropped margins).
**How to avoid:** Phase 2 must measure actual dimensions from test.pdf rather than assuming the
theoretical maximum. The Phase 2 scale-correction step (PROC-02) handles this.
**Warning signs:** Coordinate calibration boxes consistently offset from expected positions.

[VERIFIED: convert_from_path on test.pdf page 1 returned (2478, 3228)]

### Pitfall 3: subprocess shell=True bypasses exact-path check
**What goes wrong:** `subprocess.run("tesseract --version", shell=True)` succeeds if Tesseract
is on PATH even when the explicit path is wrong.
**Why it happens:** shell=True delegates to the OS shell, which searches PATH.
**How to avoid:** Always use shell=False with a list argument per D-02.
**Warning signs:** setup_check.py reports OK on a machine where the configured path is
invalid but Tesseract happens to be on PATH.

[VERIFIED: D-02 constraint; FileNotFoundError behavior verified with shell=False]

### Pitfall 4: Python version mismatch
**What goes wrong:** CLAUDE.md/STATE.md require Python 3.11; the machine has Python 3.10.6
only.
**Why it happens:** Python 3.11 was not installed.
**How to avoid:** All Phase 1 stdlib APIs (dataclasses, json, pathlib, subprocess, sys) work
identically on 3.10. Phase 1 is safe to implement on 3.10. Before Phase 2 (OpenCV),
Python 3.11 should be installed.
**Warning signs:** `py -3.11 --version` fails; `python --version` shows 3.10.x.

[VERIFIED: `py -0` shows only Python 3.10 installed. Python 3.11 not found via py launcher]

### Pitfall 5: Calling pytesseract before setting tesseract_cmd
**What goes wrong:** If any code calls `pytesseract.image_to_string()` before
`pytesseract.pytesseract.tesseract_cmd` is assigned, pytesseract falls back to looking for
"tesseract" on PATH (its default is the string `"tesseract"`, not an absolute path).
**Why it happens:** pytesseract's default `tesseract_cmd = "tesseract"` relies on PATH.
**How to avoid:** `load_settings()` then `set_tesseract_cmd(settings)` must be the first two
calls in the app entry point, before any OCR-adjacent import resolves.
**Warning signs:** OCR succeeds on developer machine (Tesseract on PATH) but fails on user
machine (no PATH entry).

[VERIFIED: Default value `pytesseract.pytesseract.tesseract_cmd == "tesseract"` confirmed]

### Pitfall 6: run_checks() executed at import time
**What goes wrong:** If `setup_check.py` calls `run_checks()` at module scope (outside
`if __name__ == "__main__"`), importing it triggers the check and potentially exits the process.
**Why it happens:** Common mistake when converting a script to a module.
**How to avoid:** All side-effectful code (checks, prints, sys.exit) lives inside `run_checks()`
or under `if __name__ == "__main__"`.

---

## Code Examples

### ENV-01: Correct binary check
```python
# Source: verified via subprocess.run tests on this machine
import subprocess
from pathlib import Path

def _check_binary(exe_path: str, name: str, source: str) -> tuple[bool, str]:
    try:
        subprocess.run(
            [exe_path, "--version"],
            capture_output=True,
            shell=False,
            timeout=5,
        )
        return True, f"OK: {name} found at {exe_path} (from {source})"
    except FileNotFoundError:
        return False, f"ERROR: {name} not found at {exe_path} (from {source})"
    except PermissionError:
        return False, f"ERROR: {name} at {exe_path} is not executable (from {source})"
```

### ENV-01: Poppler check (directory + binary name)
```python
# Source: verified — poppler_path is directory; pdftoppm.exe is the binary to check
from pathlib import Path

poppler_dir = settings["poppler_path"]   # e.g. r"C:\Program Files\poppler\Library\bin"
pdftoppm_exe = str(Path(poppler_dir) / "pdftoppm.exe")
ok, msg = _check_binary(pdftoppm_exe, "Poppler (pdftoppm)", source)
```

### ENV-02: Settings loader
```python
# Source: verified via Python 3.10 test on this machine
import json
import pathlib

_DEFAULTS = {
    "tesseract_cmd": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    "poppler_path":  r"C:\Program Files\poppler\Library\bin",
    "confidence_threshold": 60,
    "output_dir": str(pathlib.Path.home() / "Desktop"),
}

def load_settings(path: str = "settings.json") -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            user = json.load(f)
        return {**_DEFAULTS, **user}
    except FileNotFoundError:
        return _DEFAULTS.copy()
    except json.JSONDecodeError as e:
        raise ValueError(f"settings.json is not valid JSON: {e}") from e
```

### FieldResult dataclass
```python
# models/field_result.py
from dataclasses import dataclass

@dataclass
class FieldResult:
    field_name: str   # matches FieldDef.name
    value: str        # raw OCR text, stripped
    confidence: float # 0.0–100.0; -1.0 if no text found
```

### FieldDef / TableFieldDef dataclasses
```python
# config/base.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class FieldDef:
    name: str
    box: tuple[int, int, int, int]   # (left, top, right, bottom) at 300 DPI
    psm: int = 6
    whitelist: Optional[str] = None
    label: str = ""

@dataclass
class TableFieldDef:
    name: str
    row_boxes: list[tuple[int, int, int, int]]
    psm: int = 7
    whitelist: Optional[str] = None
    label: str = ""
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Tesseract 4 (legacy engine) | Tesseract 5 LSTM engine | 2021 | Significantly better accuracy on printed forms |
| PyMuPDF as PDF backend | pdf2image + Poppler | Project decision D-01 | Poppler-only; no fallback |
| pydantic Settings | stdlib json + dict merge | This phase | Simpler, no extra dependency |

**Deprecated/outdated:**
- Tesseract 4 OEM 0 (legacy): superseded by OEM 1 (LSTM) in Tesseract 5. Default OEM 3 uses
  LSTM when available.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Flat project layout (no `src/`) is appropriate for this project | Architecture Patterns | Low — can restructure, but all imports in downstream phases would need updating |
| A2 | `settings.json` lives in the project root (same directory as `setup_check.py` and `main.py`) | Architecture Patterns | Low — easy to change; just affects the open() path |
| A3 | Poppler `pdftoppm.exe` is the right binary to probe for the ENV-01 Poppler check | Don't Hand-Roll | Medium — if Poppler installs without pdftoppm.exe but with pdfinfo.exe instead, check fails; however pdftoppm.exe confirmed present on this machine |
| A4 | `confidence_threshold` is stored as an integer (60) not a float (0.60) | Standard Stack | Low — both work; must be consistent with Phase 5 comparison logic |

---

## Open Questions

1. **Python 3.11 not installed**
   - What we know: Machine has Python 3.10.6 only. CLAUDE.md and STATE.md require 3.11.
   - What's unclear: Whether Phase 1 can be implemented on 3.10 (yes, it can) and whether
     Python 3.11 needs to be installed before Phase 2 begins.
   - Recommendation: Proceed with Phase 1 on 3.10 — all Phase 1 APIs are identical. Add
     a Wave 0 task to Phase 2 to install Python 3.11 before any OpenCV work.

2. **settings.json location relative to CWD**
   - What we know: `open("settings.json")` resolves against the current working directory,
     which may not be the project root if the app is launched differently.
   - What's unclear: How users will launch the app (from project root? from a shortcut?).
   - Recommendation: Use `Path(__file__).parent / "settings.json"` to anchor the path to
     the script's location, making it launch-directory-independent. This is a Phase 1 design
     decision with downstream impact.

3. **FieldDef box tuple vs. named fields**
   - What we know: `(left, top, right, bottom)` as a plain tuple is compact but silent
     about field order. PIL's `Image.crop()` uses this exact convention.
   - What's unclear: Whether downstream phases (Phase 2 calibration) benefit from named
     fields (e.g., `FieldDef.left`, `FieldDef.top`).
   - Recommendation: Keep it as a 4-tuple — PIL.Image.crop() takes a 4-tuple directly,
     no unpacking needed. Phase 2 can index as `box[0]` etc. or unpack with `l,t,r,b = box`.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All | Yes (3.10.6 — note: 3.11 required per CLAUDE.md) | 3.10.6 | Install Python 3.11 before Phase 2 |
| Tesseract | ENV-01, Phase 4 | Yes | 5.5.0.20241111 at `C:\Program Files\Tesseract-OCR\tesseract.exe` | None (user must install) |
| Poppler | ENV-01, Phase 2 | Yes | 25.12.0 at `C:\Program Files\poppler\Library\bin` | None (user must install per D-01) |
| pytesseract | ENV-01, Phase 4 | Yes | 0.3.13 | `pip install pytesseract` |
| pdf2image | ENV-01, Phase 2 | Yes | 1.17.0 | `pip install pdf2image` |
| Pillow | All | Yes | 12.2.0 | `pip install pillow` |
| opencv-python | Phase 2+ | Yes | 4.13.0.92 | `pip install opencv-python` |
| openpyxl | Phase 5+ | Yes | 3.1.5 | `pip install openpyxl` |
| numpy | Phase 2+ | Yes | 2.2.6 | `pip install numpy` |
| pytest | Testing | No | — | `pip install pytest` (Wave 0 gap) |
| test.pdf | Testing | Yes | — (30 pages in project root) | — |

**Missing dependencies with no fallback:**
- Python 3.11 (required per CLAUDE.md/STATE.md — only 3.10.6 installed; Phase 1 is safe on 3.10 but flag for Phase 2)

**Missing dependencies with fallback:**
- pytest — install as Wave 0 task in Phase 1

[VERIFIED: All entries checked via pip show, subprocess runs, and ls on this machine]

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (not yet installed) |
| Config file | None — Wave 0 gap |
| Quick run command | `python -m pytest tests/test_phase1.py -x` |
| Full suite command | `python -m pytest tests/ -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ENV-01 | setup_check.run_checks() returns True when both binaries reachable | unit | `python -m pytest tests/test_phase1.py::test_checks_pass -x` | No — Wave 0 |
| ENV-01 | setup_check.run_checks() returns False when tesseract path is bogus | unit | `python -m pytest tests/test_phase1.py::test_tesseract_missing -x` | No — Wave 0 |
| ENV-01 | setup_check.run_checks() returns False when poppler path is bogus | unit | `python -m pytest tests/test_phase1.py::test_poppler_missing -x` | No — Wave 0 |
| ENV-01 | Standalone `python setup_check.py` exits 0 on valid paths | smoke | manual or subprocess in test | No — Wave 0 |
| ENV-01 | Standalone `python setup_check.py` exits 1 on invalid path | unit | `python -m pytest tests/test_phase1.py::test_standalone_exit -x` | No — Wave 0 |
| ENV-02 | load_settings() returns all 4 keys when settings.json absent | unit | `python -m pytest tests/test_phase1.py::test_defaults_no_file -x` | No — Wave 0 |
| ENV-02 | load_settings() merges user values over defaults | unit | `python -m pytest tests/test_phase1.py::test_settings_override -x` | No — Wave 0 |
| ENV-02 | FieldResult importable from models | unit | `python -m pytest tests/test_phase1.py::test_imports -x` | No — Wave 0 |
| ENV-02 | FieldDef importable from config.base | unit | `python -m pytest tests/test_phase1.py::test_imports -x` | No — Wave 0 |
| ENV-02 | TableFieldDef importable from config.base | unit | `python -m pytest tests/test_phase1.py::test_imports -x` | No — Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/test_phase1.py -x`
- **Per wave merge:** `python -m pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `pip install pytest` — test runner not installed
- [ ] `tests/__init__.py` — package marker
- [ ] `tests/test_phase1.py` — covers ENV-01, ENV-02

---

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Single-user desktop; no auth |
| V3 Session Management | No | No sessions |
| V4 Access Control | No | No multi-user, no permissions |
| V5 Input Validation | Partial | `settings.json` JSON decode error caught and re-raised as ValueError with clear message; binary paths validated via subprocess, not executed with user input |
| V6 Cryptography | No | No crypto |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious settings.json path injection | Tampering | subprocess shell=False prevents shell injection; path is used only as an argument to the binary, not concatenated into a shell string |
| settings.json JSON parse bomb | Tampering | stdlib json is resistant to deeply nested payloads; JSONDecodeError caught |

---

## Sources

### Primary (HIGH confidence)

- Verified via Python 3.10.6 interactive testing on this machine — all subprocess, json, pathlib,
  dataclass behaviors confirmed by direct execution
- `pytesseract` 0.3.13 source introspection — `tesseract_cmd` default, `image_to_data` signature,
  `Output.DICT` keys, `TesseractNotFoundError` source
- `pdf2image` 1.17.0 source introspection — `convert_from_path` signature, `poppler_path` semantics
- Direct binary execution: `tesseract.exe --version` (5.5.0), `pdftoppm.exe -v` (25.12.0)
- Tesseract PSM modes list: `tesseract.exe --help-extra` output

### Secondary (MEDIUM confidence)

- ROADMAP.md / REQUIREMENTS.md / CONTEXT.md — project-defined names, locations, and success criteria

### Tertiary (LOW confidence)

- Flat project layout recommendation: [ASSUMED] based on scope; no external source consulted

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified installed and functional on this machine
- Architecture: HIGH — patterns verified via direct Python execution; one ASSUMED layout choice
- Pitfalls: HIGH — each pitfall verified via code or direct test on this machine

**Research date:** 2026-04-28
**Valid until:** 2026-07-28 (90 days — stable stdlib + locked binary versions)
