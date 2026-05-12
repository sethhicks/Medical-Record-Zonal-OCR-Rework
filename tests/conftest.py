# tests/conftest.py
"""Shared pytest fixtures for OCR Medical Billing Form Extractor tests."""
from pathlib import Path
import pytest


@pytest.fixture(scope="session")
def test_pdf_path() -> str:
    """Absolute path to test.pdf in the project root."""
    path = Path(__file__).parent.parent / "test.pdf"
    if not path.exists():
        pytest.skip("test.pdf not found — smoke tests require the reference sample")
    return str(path)


@pytest.fixture(scope="session")
def sample_settings(tmp_path_factory) -> dict:
    """Settings dict with no settings.json (returns defaults including threshold_block_size=31)."""
    from config_loader import load_settings
    tmp = tmp_path_factory.mktemp("settings")
    return load_settings(path=str(tmp / "settings.json"))


@pytest.fixture(scope="session")
def tk_root():
    """Single withdrawn Tk root shared across all UI tests.

    Creating and destroying multiple tk.Tk() instances in the same process
    corrupts Tcl state on Windows (init.tcl unloaded after first destroy).
    One session-scoped root avoids this — individual tests must NOT call
    root.destroy(); the fixture tears it down once after all tests finish.
    """
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()
