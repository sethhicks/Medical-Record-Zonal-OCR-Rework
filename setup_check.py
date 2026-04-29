# setup_check.py
"""Dependency validator for OCR Medical Billing Form Extractor.

Standalone usage:
    python setup_check.py                  # uses settings.json or built-in defaults
    python setup_check.py --settings PATH  # uses specified settings file

Importable usage:
    from setup_check import run_checks
    ok = run_checks(settings=loaded_dict, quiet=True)  # True if all pass
"""
import subprocess
import sys
from pathlib import Path

# Module-level defaults so tests can access setup_check.DEFAULTS directly.
DEFAULTS: dict = {
    "tesseract_cmd": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    "poppler_path": r"C:\Program Files\poppler\Library\bin",
}


def _check_binary(exe_path: str, name: str, source: str) -> tuple:
    """Probe a binary by running it with --version.

    Args:
        exe_path: Absolute path to the executable.
        name: Human-readable name for messages (e.g. "Tesseract").
        source: Where the path came from ("settings.json" or "built-in default").

    Returns:
        (True, "OK: ...") if reachable, (False, "ERROR: ...") otherwise.
    """
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


def run_checks(settings=None, quiet: bool = False) -> bool:
    """Check that Tesseract and Poppler binaries are reachable at configured paths.

    Args:
        settings: Pre-loaded settings dict. If None, loads from config_loader.
        quiet: If True, suppresses print output (useful at app startup before UI exists).

    Returns:
        True if all dependency checks pass; False if any fail.
    """
    if settings is None:
        from config_loader import load_settings
        settings = load_settings()

    results = []

    # Tesseract check
    tess_path = settings.get("tesseract_cmd", DEFAULTS["tesseract_cmd"])
    tess_source = "settings.json" if "tesseract_cmd" in settings else "built-in default"
    ok, msg = _check_binary(tess_path, "Tesseract", tess_source)
    results.append((ok, msg))

    # Poppler check -- probe pdftoppm.exe inside the configured directory (D-01)
    pop_dir = settings.get("poppler_path", DEFAULTS["poppler_path"])
    pop_exe = str(Path(pop_dir) / "pdftoppm.exe")
    pop_source = "settings.json" if "poppler_path" in settings else "built-in default"
    ok, msg = _check_binary(pop_exe, "Poppler (pdftoppm)", pop_source)
    results.append((ok, msg))

    if not quiet:
        for _, message in results:
            print(message)

    return all(r[0] for r in results)


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
        _settings = None  # run_checks will load its own

    ok = run_checks(settings=_settings)
    sys.exit(0 if ok else 1)
