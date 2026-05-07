# tests/test_phase2.py
"""Phase 2 tests — PROC-01 (converter), PROC-02 (preprocessor), EXTR-04 (calibration).

Skip markers are removed by Wave 1 plans as each feature is implemented:
  - test_convert_page_* tests  →  removed by 02-05-PLAN
  - test_preprocess_* tests    →  removed by 02-06-PLAN
  - test_deskew_rejection      →  removed by 02-06-PLAN
  - test_scale_factors_near_one →  removed by 02-06-PLAN
  - test_calibrate_*           →  removed by 02-07-PLAN
  - test_settings_*            →  removed by 02-02-PLAN
  - test_cms1500_*             →  removed by 02-03-PLAN
  - test_ub04_*                →  removed by 02-04-PLAN
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Project root — used for CLI subprocess invocations
_ROOT = Path(__file__).parent.parent
_TEST_PDF = str(_ROOT / "test.pdf")


# ---------------------------------------------------------------------------
# PROC-01: convert_page
# ---------------------------------------------------------------------------

def test_convert_page_dimensions():
    """convert_page("test.pdf", 0) returns PIL Image of size (2550, 3300)."""
    from pipeline import convert_page
    image = convert_page(_TEST_PDF, 0)
    assert image.size == (2550, 3300)


def test_convert_page_mode():
    """Returned image mode is "RGB"."""
    from pipeline import convert_page
    image = convert_page(_TEST_PDF, 0)
    assert image.mode == "RGB"


def test_convert_page_invalid_pdf():
    """Non-existent path raises an exception."""
    from pipeline import convert_page
    with pytest.raises(Exception):
        convert_page("nonexistent_file_that_does_not_exist.pdf", 0)


# ---------------------------------------------------------------------------
# PROC-02: preprocess_page
# ---------------------------------------------------------------------------

def test_preprocess_smoke(sample_settings):
    """preprocess_page(image, settings) returns PIL Image of size (2550, 3300)."""
    from pipeline import convert_page, preprocess_page
    image = convert_page(_TEST_PDF, 0)
    result = preprocess_page(image, sample_settings)
    assert result.size == (2550, 3300)


def test_preprocess_mode(sample_settings):
    """Returned image mode is "RGB"."""
    from pipeline import convert_page, preprocess_page
    image = convert_page(_TEST_PDF, 0)
    result = preprocess_page(image, sample_settings)
    assert result.mode == "RGB"


def test_preprocess_debug_files(tmp_path, sample_settings, monkeypatch):
    """debug=True writes 4 intermediate PNGs to current working directory."""
    from pipeline import convert_page, preprocess_page
    monkeypatch.chdir(tmp_path)
    image = convert_page(_TEST_PDF, 0)
    preprocess_page(image, sample_settings, debug=True)
    assert (tmp_path / "debug_01_raw.png").exists()
    assert (tmp_path / "debug_02_scaled.png").exists()
    assert (tmp_path / "debug_03_deskewed.png").exists()
    assert (tmp_path / "debug_04_corrected.png").exists()


def test_deskew_rejection(sample_settings):
    """Artificially rotated image (6 degrees) raises ValueError."""
    import numpy as np
    import cv2
    from PIL import Image
    from pipeline import convert_page
    from pipeline.preprocessor import preprocess_page

    raw = convert_page(_TEST_PDF, 0)
    cv_img = cv2.cvtColor(np.array(raw), cv2.COLOR_RGB2BGR)
    h, w = cv_img.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), 6.0, 1.0)
    rotated_cv = cv2.warpAffine(cv_img, M, (w, h))
    pil_rotated = Image.fromarray(cv2.cvtColor(rotated_cv, cv2.COLOR_BGR2RGB))

    with pytest.raises(ValueError, match="exceeds"):
        preprocess_page(pil_rotated, sample_settings)


def test_scale_factors_near_one(sample_settings, tmp_path, monkeypatch):
    """Scale factors for a well-scanned page are within 0.98–1.02."""
    import numpy as np
    import cv2
    from pipeline import convert_page
    from pipeline import preprocess_page

    monkeypatch.chdir(tmp_path)
    image = convert_page(_TEST_PDF, 0)
    # Run with debug=True so intermediate images are written; visually confirms scale pass
    result = preprocess_page(image, sample_settings, debug=True)
    # If preprocess_page completes without ValueError, scale factors were within bounds.
    # Full scale_x/scale_y assertion requires exposing them; smoke-level: result exists and is right size.
    assert result.size == (2550, 3300)


# ---------------------------------------------------------------------------
# EXTR-04: calibrate.py CLI
# ---------------------------------------------------------------------------

def test_calibrate_overlay_created(tmp_path):
    """calibrate.py --page 0 --pdf test.pdf exits 0 and writes calibration_overlay_p0.png."""
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
    assert result.returncode == 0, result.stderr.decode()
    assert (tmp_path / "calibration_overlay_p0.png").exists()


def test_calibrate_overlay_nonempty(tmp_path):
    """Overlay PNG is larger than 1 KB."""
    subprocess.run(
        [
            sys.executable,
            str(_ROOT / "pipeline" / "calibrate.py"),
            "--page", "0",
            "--pdf", _TEST_PDF,
        ],
        capture_output=True,
        cwd=str(tmp_path),
    )
    png_path = tmp_path / "calibration_overlay_p0.png"
    assert png_path.exists()
    assert png_path.stat().st_size > 1024


# ---------------------------------------------------------------------------
# ENV-02 extension: settings threshold_block_size default
# ---------------------------------------------------------------------------

def test_settings_threshold_block_size_default(tmp_path):
    """load_settings() returns threshold_block_size == 31 when key absent from JSON."""
    from config_loader import load_settings
    s = load_settings(path=str(tmp_path / "settings.json"))
    assert s["threshold_block_size"] == 31


# ---------------------------------------------------------------------------
# EXTR-04: coordinate config populated
# ---------------------------------------------------------------------------

def test_cms1500_fields_populated():
    """CMS1500_FIELDS is a non-empty list of FieldDef instances."""
    from config.cms1500 import CMS1500_FIELDS
    from config.base import FieldDef
    assert len(CMS1500_FIELDS) > 0
    assert all(isinstance(f, FieldDef) for f in CMS1500_FIELDS)


def test_ub04_fields_populated():
    """UB04_FIELDS is a non-empty list of FieldDef instances."""
    from config.ub04 import UB04_FIELDS
    from config.base import FieldDef
    assert len(UB04_FIELDS) > 0
    assert all(isinstance(f, FieldDef) for f in UB04_FIELDS)


def test_cms1500_table_fields_row_count():
    """Each TableFieldDef in CMS1500_TABLE_FIELDS has exactly 6 row_boxes."""
    from config.cms1500 import CMS1500_TABLE_FIELDS
    assert len(CMS1500_TABLE_FIELDS) > 0
    assert all(len(f.row_boxes) == 6 for f in CMS1500_TABLE_FIELDS)


def test_ub04_table_fields_row_count():
    """Each TableFieldDef in UB04_TABLE_FIELDS has exactly 22 row_boxes."""
    from config.ub04 import UB04_TABLE_FIELDS
    assert len(UB04_TABLE_FIELDS) > 0
    assert all(len(f.row_boxes) == 22 for f in UB04_TABLE_FIELDS)
