# config_loader.py
"""Settings loader for OCR Medical Billing Form Extractor.

Reads settings.json from the same directory as this file and merges user values
over hardcoded Windows defaults. Returns defaults when settings.json is absent.
Never raises on a missing file.
"""
import json
import pathlib

_DEFAULTS: dict = {
    "tesseract_cmd": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    "poppler_path": r"C:\Program Files\poppler\Library\bin",
    "confidence_threshold": 60,
    "output_dir": str(pathlib.Path.home() / "Desktop"),
    "threshold_block_size": 31,
}


def load_settings(path: str | None = None) -> dict:
    """Load settings.json and merge with built-in defaults.

    Args:
        path: Explicit path to settings.json. Defaults to settings.json in the
              same directory as this module (script-relative, not CWD-relative).

    Returns:
        dict with keys: tesseract_cmd, poppler_path, confidence_threshold, output_dir.
        User keys override defaults; missing keys fall back to defaults.

    Raises:
        ValueError: If settings.json exists but contains invalid JSON.
    """
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
