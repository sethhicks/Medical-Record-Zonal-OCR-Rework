# tests/conftest.py
"""Shared pytest fixtures for OCR Medical Billing Form Extractor tests."""
from pathlib import Path
import pytest


@pytest.fixture(scope="session")
def test_pdf_path() -> str:
    """Absolute path to test.pdf in the project root."""
    path = Path(__file__).parent.parent / "test.pdf"
    assert path.exists(), f"test.pdf not found at {path}"
    return str(path)


@pytest.fixture(scope="session")
def sample_settings(tmp_path_factory) -> dict:
    """Settings dict with no settings.json (returns defaults including threshold_block_size=31)."""
    from config_loader import load_settings
    tmp = tmp_path_factory.mktemp("settings")
    return load_settings(path=str(tmp / "settings.json"))
