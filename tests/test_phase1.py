# tests/test_phase1.py
"""Phase 1 tests — ENV-01 (dependency check) and ENV-02 (settings + imports).

Skip markers are removed by Wave 1 plans as each feature is implemented:
  - test_checks_pass, test_tesseract_missing, test_poppler_missing,
    test_standalone_exit_ok, test_standalone_exit_fail  →  removed by 01-04-PLAN
  - test_defaults_no_file, test_settings_override        →  removed by 01-03-PLAN
  - test_imports                                         →  removed by 01-02-PLAN
"""
import subprocess
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# ENV-01: setup_check behavior
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="setup_check.py not yet created — implemented in 01-04-PLAN")
def test_checks_pass():
    """run_checks() returns True when both binaries exist at configured paths."""
    import setup_check
    assert setup_check.run_checks(quiet=True) is True


@pytest.mark.skip(reason="setup_check.py not yet created — implemented in 01-04-PLAN")
def test_tesseract_missing():
    """run_checks() returns False when tesseract path is bogus."""
    import setup_check
    bogus = {
        "tesseract_cmd": r"C:\nonexistent\tesseract.exe",
        "poppler_path": setup_check.DEFAULTS["poppler_path"],
    }
    assert setup_check.run_checks(settings=bogus, quiet=True) is False


@pytest.mark.skip(reason="setup_check.py not yet created — implemented in 01-04-PLAN")
def test_poppler_missing():
    """run_checks() returns False when poppler path is bogus."""
    import setup_check
    bogus = {
        "tesseract_cmd": setup_check.DEFAULTS["tesseract_cmd"],
        "poppler_path": r"C:\nonexistent\poppler\bin",
    }
    assert setup_check.run_checks(settings=bogus, quiet=True) is False


@pytest.mark.skip(reason="setup_check.py not yet created — implemented in 01-04-PLAN")
def test_standalone_exit_ok():
    """python setup_check.py exits 0 when binaries are reachable."""
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent.parent / "setup_check.py")],
        capture_output=True,
    )
    assert result.returncode == 0


@pytest.mark.skip(reason="setup_check.py not yet created — implemented in 01-04-PLAN")
def test_standalone_exit_fail():
    """python setup_check.py exits 1 when a binary path is bogus."""
    import json
    import tempfile
    import os

    bad_settings = {"tesseract_cmd": r"C:\nonexistent\tesseract.exe"}
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(bad_settings, f)
        tmp_path = f.name

    try:
        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).parent.parent / "setup_check.py"),
                "--settings",
                tmp_path,
            ],
            capture_output=True,
        )
        assert result.returncode == 1
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# ENV-02: settings loader + dataclass imports
# ---------------------------------------------------------------------------

def test_defaults_no_file(tmp_path):
    """load_settings() returns all 4 keys when settings.json is absent."""
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
    assert "tesseract_cmd" in s  # default key still present


def test_imports():
    """FieldResult, FieldDef, TableFieldDef are importable from expected locations."""
    from models import FieldResult
    from config.base import FieldDef, TableFieldDef

    # Basic instantiation — verifies field order and default values
    fr = FieldResult(field_name="box1", value="MEDICARE", confidence=95.0)
    assert fr.value == "MEDICARE"

    fd = FieldDef(name="box1a", box=(10, 20, 100, 40))
    assert fd.psm == 6  # default

    tfd = TableFieldDef(name="box24_cpt", row_boxes=[(10, 50, 100, 70)] * 6)
    assert tfd.psm == 7  # default
    assert len(tfd.row_boxes) == 6
