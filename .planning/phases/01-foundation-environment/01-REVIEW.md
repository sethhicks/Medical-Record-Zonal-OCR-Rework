---
phase: 01-foundation-environment
reviewed: 2026-04-28T00:00:00Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - .gitignore
  - config/__init__.py
  - config/base.py
  - config/cms1500.py
  - config/ub04.py
  - config_loader.py
  - main.py
  - models/__init__.py
  - models/field_result.py
  - setup_check.py
  - tests/__init__.py
  - tests/test_phase1.py
findings:
  critical: 2
  warning: 5
  info: 3
  total: 10
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-04-28
**Depth:** standard
**Files Reviewed:** 12
**Status:** issues_found

## Summary

Phase 1 establishes the project scaffold: a settings loader, dependency validator,
dataclass models, and an initial test suite. The overall structure is clean and
intentional. However, two critical issues were found that will cause crashes or
incorrect failure behavior at runtime, and five warnings cover missing exception
handling, mutable shared state, and test guards that will break CI. Three info
items cover typing and annotation gaps that become load-bearing in later phases.

---

## Critical Issues

### CR-01: `_check_binary` does not catch `subprocess.TimeoutExpired` — crashes instead of returning `(False, msg)`

**File:** `setup_check.py:34-45`

**Issue:** `subprocess.run(..., timeout=5)` raises `subprocess.TimeoutExpired` when the
process does not exit within 5 seconds. `_check_binary` only catches `FileNotFoundError`
and `PermissionError`. `TimeoutExpired` is not a subclass of either, so it propagates
unhandled through `run_checks`, through the `__main__` block (which also has no
try/except), and crashes with a raw traceback instead of returning `False` and a clean
error message. On a misconfigured Windows machine where a stub "tesseract.exe" exists
but hangs, the user sees a crash instead of a diagnostic error.

**Fix:**
```python
    except FileNotFoundError:
        return False, f"ERROR: {name} not found at {exe_path} (from {source})"
    except PermissionError:
        return False, f"ERROR: {name} at {exe_path} is not executable (from {source})"
    except subprocess.TimeoutExpired:
        return False, f"ERROR: {name} at {exe_path} timed out after 5 s (from {source})"
```

---

### CR-02: `None` value in `settings.json` overrides a required path key with `None`, causing an untyped `TypeError` crash in `subprocess.run`

**File:** `config_loader.py:38` / `setup_check.py:67`

**Issue:** `load_settings` uses `{**_DEFAULTS, **user}` to merge. If `settings.json`
contains `{"tesseract_cmd": null}`, the merge produces `{"tesseract_cmd": None, ...}`.
`setup_check.run_checks` then passes `None` as `exe_path` to `_check_binary`, which
calls `subprocess.run([None, "--version"], ...)`. On Python 3.11/Windows this raises
`TypeError: expected str, bytes or os.PathLike object, not NoneType` — an unhandled
crash that bypasses the clean error message path entirely. Confirmed by runtime test.

The same crash occurs for `poppler_path: null` because `Path(None)` raises a
`TypeError` on line 73 of `setup_check.py` before `_check_binary` is even called.

**Fix — add a validation step in `load_settings` or at the top of `run_checks`:**
```python
# In run_checks, before using the values:
_PATH_KEYS = ("tesseract_cmd", "poppler_path")
for key in _PATH_KEYS:
    val = settings.get(key)
    if val is not None and not isinstance(val, str):
        raise ValueError(
            f"settings key '{key}' must be a string path, got {type(val).__name__!r}"
        )
```

Alternatively, add a `_validate_settings(d: dict) -> None` helper to `config_loader.py`
and call it before returning.

---

## Warnings

### WR-01: `DEFAULTS` in `setup_check.py` is a public mutable dict — mutation persists across tests

**File:** `setup_check.py:17-20`

**Issue:** `DEFAULTS` is a module-level `dict` referenced directly by `run_checks` as a
fallback (`settings.get("tesseract_cmd", DEFAULTS["tesseract_cmd"])`). Any code that
does `setup_check.DEFAULTS["tesseract_cmd"] = "evil"` — intentionally or by accident —
permanently alters the fallback for all subsequent calls within the same process.
`test_tesseract_missing` and `test_poppler_missing` both read `setup_check.DEFAULTS`
directly, so a mutation in an earlier test would silently corrupt their inputs. Confirmed
by runtime test.

**Fix:** Replace with a module-level constant tuple or a function that returns a fresh
copy, and have `run_checks` call the function rather than read the dict directly:
```python
# setup_check.py
_DEFAULTS: dict = {
    "tesseract_cmd": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    "poppler_path": r"C:\Program Files\poppler\Library\bin",
}

def get_defaults() -> dict:
    return _DEFAULTS.copy()

# Keep public alias for tests that read it, but document it is read-only:
DEFAULTS = _DEFAULTS  # read-only by convention; do not mutate
```
The more defensive option is to make it a `types.MappingProxyType(_DEFAULTS)`.

---

### WR-02: `test_checks_pass`, `test_standalone_exit_ok`, and related integration tests have no skip guard for environments without the binaries installed

**File:** `tests/test_phase1.py:21-53`

**Issue:** `test_checks_pass` calls `setup_check.run_checks(quiet=True)` against the real
filesystem. On any machine where Tesseract and/or Poppler are not installed at the
hardcoded Windows default paths, this test **fails** rather than skips. The same applies
to `test_standalone_exit_ok`. There is no `pytest.ini`, `pyproject.toml`, or
`setup.cfg`; there are no custom marks; there are no `pytest.mark.skipif` decorators.

In a CI environment (GitHub Actions, etc.) these tests will cause the entire suite to
fail unless the runners have the binaries pre-installed.

**Fix:** Guard the binary-dependent tests with a skip condition:
```python
import shutil

_TESS_AVAILABLE = shutil.which("tesseract") is not None or Path(
    setup_check.DEFAULTS["tesseract_cmd"]
).exists()

@pytest.mark.skipif(not _TESS_AVAILABLE, reason="Tesseract not installed on this machine")
def test_checks_pass():
    ...
```
Or define a custom `pytest` mark (`@pytest.mark.integration`) and document that it
requires real binaries, then exclude it in CI with `-m "not integration"`.

---

### WR-03: Both `test_standalone_exit_ok` and `test_standalone_exit_fail` call `subprocess.run` without a `timeout` — test suite can hang indefinitely

**File:** `tests/test_phase1.py:49-53`, `tests/test_phase1.py:68-80`

**Issue:** Both subprocess-spawning tests omit `timeout=`. If the child process (the
real `setup_check.py` or a stub binary) stalls, the test process blocks forever with no
way to recover short of killing it. This is a test reliability defect, not merely a
style preference.

**Fix:**
```python
result = subprocess.run(
    [...],
    capture_output=True,
    timeout=30,  # fail fast rather than hang
)
```

---

### WR-04: `FieldResult.value` is annotated `str` but accepts `None` at runtime — future `.strip()` call in Phase 4 will raise `AttributeError`

**File:** `models/field_result.py:9`

**Issue:** `pytesseract.image_to_string()` can return `None` in edge cases (e.g., empty
image region, tesseract crash). Because `FieldResult` is a plain `@dataclass` with no
`__post_init__`, passing `value=None` is silently accepted despite the `str` annotation.
The field comment says "raw OCR text, stripped" — implying callers will call `.strip()`
on it. That call raises `AttributeError: 'NoneType' object has no attribute 'strip'`.
Confirmed by runtime test.

**Fix — add `__post_init__` validation:**
```python
from dataclasses import dataclass

@dataclass
class FieldResult:
    field_name: str
    value: str
    confidence: float

    def __post_init__(self):
        if not isinstance(self.value, str):
            raise TypeError(
                f"FieldResult.value must be str, got {type(self.value).__name__!r} "
                f"for field {self.field_name!r}"
            )
        if not isinstance(self.confidence, (int, float)):
            raise TypeError(
                f"FieldResult.confidence must be numeric, got {type(self.confidence).__name__!r}"
            )
```
Alternatively, make the dataclass `frozen=True` to at least prevent post-construction
mutation of fields.

---

### WR-05: `output_dir` default is `Path.home() / "Desktop"` — evaluated once at import time and stored in a module-level dict; Desktop may not exist

**File:** `config_loader.py:15`

**Issue:** `str(pathlib.Path.home() / "Desktop")` is evaluated when the module is first
imported. On Windows Server, headless CI, or Linux environments, `~/Desktop` does not
exist. Any Phase 6 code that uses `output_dir` as a write target without first checking
`Path(output_dir).exists()` will raise a `FileNotFoundError` at the point of writing
output, not at startup, leaving users with a misleading error.

**Fix:** Document the assumption explicitly, and in Phase 6 add a preflight check:
```python
output_path = Path(settings["output_dir"])
output_path.mkdir(parents=True, exist_ok=True)
```
Or change the default to `Path.home()` (guaranteed to exist) rather than
`Path.home() / "Desktop"`.

---

## Info

### IN-01: `_check_binary` return type is annotated as bare `tuple` instead of `tuple[bool, str]`

**File:** `setup_check.py:23`

**Issue:** The function signature reads `-> tuple:`. Python 3.11 supports
`tuple[bool, str]` natively (no import needed). The bare `tuple` annotation gives type
checkers no information about the element types, which matters when `run_checks` unpacks
the result as `ok, msg = _check_binary(...)`.

**Fix:**
```python
def _check_binary(exe_path: str, name: str, source: str) -> tuple[bool, str]:
```

---

### IN-02: `cms1500.py` and `ub04.py` import `FieldDef` and `TableFieldDef` with `# noqa: F401` solely to suppress linter warnings — misleading comment

**File:** `config/cms1500.py:5`, `config/ub04.py:5`

**Issue:** The comment `# noqa: F401 -- available for Phase 2` implies these imports
will be used in-file in Phase 2. But Phase 2 will need these symbols in the body of
`cms1500.py` regardless — the import will be used when `CMS1500_FIELDS` is populated.
So the `noqa` suppression is hiding a currently-unused import that will become used, but
the intent is not clear. A developer cleaning up dead code might remove the import
thinking it is still unused after the noqa was added.

**Fix:** Either remove the import entirely until Phase 2 (the lists are empty; they need
no type references until populated), or add a brief inline comment:
```python
from config.base import FieldDef, TableFieldDef  # used when Phase 2 populates CMS1500_FIELDS
```
and keep the `noqa` so the linter does not complain on the empty lists.

---

### IN-03: `test_imports` does not assert the `-1.0` confidence sentinel is accepted by `FieldResult`

**File:** `tests/test_phase1.py:113-127`

**Issue:** The docstring for `FieldResult.confidence` says `-1.0 if no text found in
region`. This is a contract that Phase 4 OCR code will rely on (e.g., `if
result.confidence == -1.0: skip`). The test creates a `FieldResult` with
`confidence=95.0` but never exercises the sentinel value. If the sentinel contract is
broken (e.g., someone adds `__post_init__` validation that rejects negative values), no
existing test will catch it.

**Fix — add an assertion to `test_imports`:**
```python
# Verify the -1.0 sentinel is accepted (contract for Phase 4)
fr_no_text = FieldResult(field_name="box1", value="", confidence=-1.0)
assert fr_no_text.confidence == -1.0
```

---

_Reviewed: 2026-04-28_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
