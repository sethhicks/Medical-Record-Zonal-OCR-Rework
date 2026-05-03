---
phase: 03-form-detection
reviewed: 2026-05-03T00:00:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - pipeline/detector.py
  - tests/test_phase3.py
  - pipeline/__init__.py
findings:
  critical: 2
  warning: 3
  info: 1
  total: 6
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-05-03
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Three files were reviewed: `pipeline/detector.py` (the form-type detector), `tests/test_phase3.py` (the Phase 3 test suite), and `pipeline/__init__.py` (the package public API). The `__init__.py` is clean with no issues. The detector logic is generally sound for the happy path, but contains two bugs that can cause silent test failures in CI and one that mutates shared global state. The test suite has a structural defect that converts a missing-fixture condition into a hard `AssertionError` rather than a graceful skip.

---

## Critical Issues

### CR-01: Smoke tests crash with `AssertionError` when `test.pdf` is absent — no skip

**File:** `tests/test_phase3.py:109-124`

**Issue:** `test_cms1500_smoke` and `test_ub04_smoke` depend on the `test_pdf_path` session-scoped fixture. That fixture (in `conftest.py:11`) calls `assert path.exists()` and raises `AssertionError` if `test.pdf` is missing. Because the assertion is inside a session-scoped fixture with no `pytest.skip`, every test that uses the fixture will fail with `AssertionError: test.pdf not found at ...` — not a graceful `pytest.skip`. In CI environments where `test.pdf` is not committed (it is listed as untracked in the git status), the entire session's fixture setup will abort with an `ERROR` rather than a `SKIPPED`, blocking the mock-only tests from reporting their results cleanly.

Additionally, the smoke tests themselves have no explicit `@pytest.mark.skipif` guard checking for `test.pdf` or Tesseract presence, making them impossible to suppress in headless environments without modifying the fixture.

**Fix:** Change the fixture to skip rather than assert, and add a skip marker to each smoke test:

```python
# tests/conftest.py — replace assert with pytest.skip
@pytest.fixture(scope="session")
def test_pdf_path() -> str:
    path = Path(__file__).parent.parent / "test.pdf"
    if not path.exists():
        pytest.skip("test.pdf not found — smoke tests require the reference sample")
    return str(path)
```

```python
# tests/test_phase3.py — add explicit guard (belt-and-suspenders)
@pytest.mark.skipif(
    not (Path(__file__).parent.parent / "test.pdf").exists(),
    reason="test.pdf not present"
)
def test_cms1500_smoke(test_pdf_path):
    ...

@pytest.mark.skipif(
    not (Path(__file__).parent.parent / "test.pdf").exists(),
    reason="test.pdf not present"
)
def test_ub04_smoke(test_pdf_path):
    ...
```

---

### CR-02: `detect_form_type` mutates a module-level global (`pytesseract.tesseract_cmd`) on every call

**File:** `pipeline/detector.py:33-34`

**Issue:** `load_settings()` is called on every invocation of `detect_form_type()`, and its result is used to set `pytesseract.pytesseract.tesseract_cmd` — a module-level global — on every call. This is a shared-state side effect with two concrete problems:

1. **Thread-safety:** If the pipeline is ever called from multiple threads (e.g., processing a batch of pages in a thread pool), concurrent calls race on `pytesseract.pytesseract.tesseract_cmd`. One thread can overwrite the value while another thread is mid-call, causing non-deterministic Tesseract invocations pointing to an incorrect binary.

2. **Incorrect mock-patching surface in tests:** The mock tests patch `pytesseract.image_to_string` but do NOT neutralise the `load_settings()` call at line 33. In a clean CI environment without `settings.json` and without Tesseract installed, line 34 writes a non-existent Windows path (`C:\Program Files\Tesseract-OCR\tesseract.exe`) into the global before the mocked `image_to_string` is even reached. If anything between line 33 and the first `image_to_string` call reads `tesseract_cmd` (e.g., a future version validates it), the test environment will silently corrupt shared OCR state for other tests running in the same session.

**Fix:** Set `tesseract_cmd` once at module import time (or lazily via a module-level flag), not inside the hot-path function:

```python
# pipeline/detector.py — move settings init to module level
from config_loader import load_settings as _load_settings

_settings = _load_settings()
pytesseract.pytesseract.tesseract_cmd = _settings['tesseract_cmd']

_HEADER_STRIP = (0, 0, 2550, 600)
_FOOTER_STRIP = (0, 2900, 2550, 3300)


def detect_form_type(image: "Image.Image") -> str:
    # ... no load_settings() call here
    header_gray = image.crop(_HEADER_STRIP).convert('L')
    ...
```

This mirrors the pattern already used correctly in `pipeline/converter.py` (which also calls `load_settings()` at function entry) — however, moving settings init to module level is the right fix for both modules if thread-safety matters. For `detect_form_type` specifically the global mutation makes it more urgent.

---

## Warnings

### WR-01: `heal_hit` anchor is a substring match that will false-positive on common medical words

**File:** `pipeline/detector.py:47`

**Issue:** `'HEAL' in header_text` matches any occurrence of the four-letter sequence "HEAL" — including "HEALTHCARE", "HEALEY" (a patient surname), "HEALING", or any other word containing that substring. On a CMS-1500 form the expected text is "HEALTH INSURANCE CLAIM FORM"; the shorter anchor was presumably chosen for OCR robustness, but it is broad enough to match non-CMS pages that happen to contain the word "HEALTHCARE" or a patient name. Since `cms_score` requires only 2-of-3 anchors, a false "HEAL" match combined with a "NUC" footer match (which is equally short) is sufficient to misclassify a UB-04 page as CMS-1500.

**Fix:** Tighten the anchor to require "HEALTH" (still tolerant of garbled trailing characters) or use "HEALTH INSURANCE" as the substring:

```python
heal_hit = 'HEALTH' in header_text   # still robust to partial OCR garbling
```

---

### WR-02: Mock tests use a fragile iterator that raises `StopIteration` if call count changes

**File:** `tests/test_phase3.py:31-35, 77-81`

**Issue:** `test_cms1500_detection_mock` and `test_both_match_returns_unknown` build a `responses = iter([...])` with exactly 3 elements, then pass `lambda img, config='': next(responses)` as the mock. If the implementation of `detect_form_type` is modified to make a 4th OCR call (e.g., adding a second header strip or a new PSM pass), `next(responses)` raises `StopIteration`. Inside a lambda called by production code, this propagates as an unhandled exception that produces a confusing traceback pointing into Tesseract internals rather than the test assertion. The test would still fail, but the failure message would be misleading.

**Fix:** Use `itertools.cycle` for the final fallback response, or use `unittest.mock.Mock(side_effect=[...])` which raises `StopIteration` only after all values are consumed and converts it to a cleaner error:

```python
from unittest.mock import patch, Mock

def test_cms1500_detection_mock(monkeypatch):
    from pipeline import detect_form_type
    from PIL import Image

    mock_ocr = Mock(side_effect=[
        'HEALTH INSURANCE CLAIM FORM',
        'NUCC Instruction Manual FORM 1500',
        '',
    ])
    monkeypatch.setattr(pytesseract, 'image_to_string', mock_ocr)
    img = Image.new('RGB', (2550, 3300), 255)
    assert detect_form_type(img) == 'CMS-1500'
    assert mock_ocr.call_count == 3   # assert exact call count as a regression guard
```

---

### WR-03: No input validation — `None` or wrong-size image produces an unhelpful `AttributeError`

**File:** `pipeline/detector.py:37`

**Issue:** `detect_form_type` accepts `image: "Image.Image"` but performs no runtime check. If `None` is passed (e.g., a caller that does not check the return value of `convert_page`), `image.crop(...)` raises `AttributeError: 'NoneType' object has no attribute 'crop'`. If an image with the wrong dimensions is passed (e.g., a thumbnail), the crop regions `_HEADER_STRIP` and `_FOOTER_STRIP` silently produce smaller images, and Tesseract runs on the wrong content without any warning, producing a silent misclassification. The docstring states the function expects a 2550x3300 image but this is never enforced.

**Fix:** Add a guard at the top of the function:

```python
def detect_form_type(image: "Image.Image") -> str:
    if image is None:
        raise TypeError("detect_form_type requires a PIL Image, got None")
    w, h = image.size
    if (w, h) != (2550, 3300):
        raise ValueError(
            f"detect_form_type expects a 2550x3300 px image, got {w}x{h}. "
            "Pass the output of convert_page() directly."
        )
    ...
```

---

## Info

### IN-01: `test_unknown_result_is_string` duplicates `test_unknown_when_no_anchors`

**File:** `tests/test_phase3.py:89-100`

**Issue:** `test_unknown_result_is_string` uses the same mock setup as `test_unknown_when_no_anchors` (all OCR returns empty string) and asserts both `result == 'UNKNOWN'` and `isinstance(result, str)`. The `isinstance` check adds no coverage beyond what `assert result == 'UNKNOWN'` already guarantees, because string equality implicitly requires `result` to be a `str`. The test is not wrong, but it is redundant — it runs the same code path twice and provides no additional confidence.

**Fix:** Either remove `test_unknown_result_is_string` and add the `isinstance` assertion to `test_unknown_when_no_anchors`, or document clearly why both tests exist if there is a reason to keep them separate:

```python
def test_unknown_when_no_anchors(monkeypatch):
    ...
    result = detect_form_type(img)
    assert result == 'UNKNOWN'
    assert isinstance(result, str)   # fold the isinstance check here
```

---

_Reviewed: 2026-05-03_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
