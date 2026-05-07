# tests/test_phase6.py
"""Phase 6 tests — UI-01, UI-02, UI-03, UI-04, PROC-04 (desktop UI & batch processing).

Skip markers are removed by Wave 1/2 plans as each feature is implemented:
  - test_startup_check_blocks_ui        -> removed by 06-02-PLAN
  - test_window_non_resizable           -> removed by 06-02-PLAN
  - test_select_pdfs_populates_listbox  -> removed by 06-02-PLAN
  - test_clear_empties_file_list        -> removed by 06-02-PLAN
  - test_output_label_shows_path        -> removed by 06-02-PLAN
  - test_queue_progress_message_format  -> removed by 06-02-PLAN
  - test_queue_error_message_format     -> removed by 06-02-PLAN
  - test_queue_done_message_format      -> removed by 06-02-PLAN
  - test_worker_unknown_page_posts_error -> removed by 06-02-PLAN
  - test_import_main                    -> removed by 06-02-PLAN
  - test_worker_smoke_real_pdf          -> removed by 06-03-PLAN
  - test_batch_multi_pdf_produces_output -> removed by 06-03-PLAN
"""
import pytest
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_TEST_PDF = str(_ROOT / "test.pdf")


# ---------------------------------------------------------------------------
# UI-01: File selection
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Phase 6 stub")
def test_select_pdfs_populates_listbox():
    """Selecting PDFs via filedialog populates the Listbox with basenames (D-06)."""
    pass


@pytest.mark.skip(reason="Phase 6 stub")
def test_clear_empties_file_list():
    """[Clear] button empties the Listbox and internal file list (D-07)."""
    pass


# ---------------------------------------------------------------------------
# UI-02: Progress display / threading model
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Phase 6 stub")
def test_queue_progress_message_format():
    """Worker posts ('progress', current_page, total_pages) tuples to the queue (D-10)."""
    pass


@pytest.mark.skip(reason="Phase 6 stub")
def test_queue_done_message_format():
    """Worker posts ('done', output_path) when all pages are processed (D-10)."""
    pass


# ---------------------------------------------------------------------------
# UI-03: Open output file
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Phase 6 stub")
def test_output_label_shows_path():
    """Output label text matches 'Output: {output_dir}\\extracted_results.xlsx' (D-05)."""
    pass


# ---------------------------------------------------------------------------
# UI-04: Error display
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Phase 6 stub")
def test_queue_error_message_format():
    """Worker posts ('error', filename, page_num, error_message) for failed pages (D-12)."""
    pass


@pytest.mark.skip(reason="Phase 6 stub")
def test_worker_unknown_page_posts_error():
    """UNKNOWN-classified pages post an error tuple with 'UNKNOWN form type' message (D-14)."""
    pass


# ---------------------------------------------------------------------------
# ENV / startup check
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Phase 6 stub")
def test_startup_check_blocks_ui():
    """run_checks() is called at startup; returns bool used to gate Tk() construction (D-02)."""
    pass


@pytest.mark.skip(reason="Phase 6 stub")
def test_window_non_resizable():
    """root.resizable(False, False) is present in main.py (D-03)."""
    pass


# ---------------------------------------------------------------------------
# Import smoke
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Phase 6 stub")
def test_import_main():
    """main module is importable without side effects when __name__ != '__main__'."""
    pass


# ---------------------------------------------------------------------------
# PROC-04: Batch / integration (activated by 06-03-PLAN)
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Phase 6 stub")
def test_worker_smoke_real_pdf(test_pdf_path):
    """Worker function processes all 30 pages of test.pdf without raising (real Tesseract, ~60s)."""
    pass


@pytest.mark.skip(reason="Phase 6 stub")
def test_batch_multi_pdf_produces_output(test_pdf_path, tmp_path):
    """Running worker with two copies of test.pdf produces extracted_results.xlsx with data rows."""
    pass
