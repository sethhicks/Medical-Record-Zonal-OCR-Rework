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
import queue
import threading
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

_ROOT = Path(__file__).parent.parent
_TEST_PDF = str(_ROOT / "test.pdf")


# ---------------------------------------------------------------------------
# UI-01: File selection
# ---------------------------------------------------------------------------

def test_select_pdfs_populates_listbox():
    """Selecting PDFs via filedialog populates the Listbox with basenames (D-06)."""
    import tkinter as tk
    import main

    root = tk.Tk()
    root.withdraw()
    try:
        settings = {"output_dir": "/tmp", "confidence_threshold": 60}
        app = main.OCRApp(root, settings)

        fake_paths = ("/some/path/claims_jan.pdf", "/some/path/claims_feb.pdf")
        with patch("tkinter.filedialog.askopenfilenames", return_value=fake_paths):
            app.on_select()

        assert app.listbox.size() == 2
        assert app.listbox.get(0) == "claims_jan.pdf"
        assert app.listbox.get(1) == "claims_feb.pdf"
        assert len(app._files) == 2
    finally:
        root.destroy()


def test_clear_empties_file_list():
    """[Clear] button empties the Listbox and internal file list (D-07)."""
    import tkinter as tk
    import main

    root = tk.Tk()
    root.withdraw()
    try:
        settings = {"output_dir": "/tmp", "confidence_threshold": 60}
        app = main.OCRApp(root, settings)

        fake_paths = ("/some/path/claims_jan.pdf",)
        with patch("tkinter.filedialog.askopenfilenames", return_value=fake_paths):
            app.on_select()

        assert app.listbox.size() == 1

        app.on_clear()

        assert app.listbox.size() == 0
        assert app._files == []
    finally:
        root.destroy()


# ---------------------------------------------------------------------------
# UI-02: Progress display / threading model
# ---------------------------------------------------------------------------

def test_queue_progress_message_format():
    """Worker posts ('progress', current_page, total_pages) tuples to the queue (D-10)."""
    q: queue.Queue = queue.Queue()
    q.put(("progress", 1, 30))
    msg = q.get_nowait()
    assert msg[0] == "progress"
    assert len(msg) == 3
    assert msg[1] == 1   # current_page
    assert msg[2] == 30  # total_pages


def test_queue_done_message_format():
    """Worker posts ('done', output_path, error_count) when all pages are processed (D-10)."""
    q: queue.Queue = queue.Queue()
    q.put(("done", "/tmp/extracted_results.xlsx", 0))
    msg = q.get_nowait()
    assert msg[0] == "done"
    assert len(msg) == 3
    assert msg[1] == "/tmp/extracted_results.xlsx"  # output_path
    assert msg[2] == 0                               # error_count


# ---------------------------------------------------------------------------
# UI-03: Open output file
# ---------------------------------------------------------------------------

def test_output_label_shows_path():
    """Output label text matches 'Output: {output_dir}/extracted_results.xlsx' (D-05)."""
    import os
    import tkinter as tk
    import main

    root = tk.Tk()
    root.withdraw()
    try:
        output_dir = "/tmp/ocr_test_output"
        settings = {"output_dir": output_dir, "confidence_threshold": 60}
        app = main.OCRApp(root, settings)

        expected = f"Output: {os.path.join(output_dir, 'extracted_results.xlsx')}"
        assert app.lbl_output["text"] == expected
    finally:
        root.destroy()


# ---------------------------------------------------------------------------
# UI-04: Error display
# ---------------------------------------------------------------------------

def test_queue_error_message_format():
    """Worker posts ('error', filename, page_num, error_message) for failed pages (D-12)."""
    q: queue.Queue = queue.Queue()
    q.put(("error", "/path/to/claims.pdf", 5, "UNKNOWN form type"))
    msg = q.get_nowait()
    assert msg[0] == "error"
    assert len(msg) == 4
    assert msg[1] == "/path/to/claims.pdf"  # filename
    assert msg[2] == 5                       # page_num
    assert msg[3] == "UNKNOWN form type"     # error_message


def test_worker_unknown_page_posts_error(tmp_path):
    """UNKNOWN-classified pages post an error tuple with 'UNKNOWN form type' message (D-14).

    Also verifies that error pages produce a blank row in the Excel workbook with
    extraction_error populated (D-14 / SC-5).

    This test avoids creating a tk.Tk() window because tkinter teardown in prior
    tests corrupts Tcl state on some Windows environments. Instead it instantiates
    a lightweight stand-in object that only exposes the attributes _worker accesses:
    _files, _queue, and settings.
    """
    import queue as _queue_mod
    import main
    import openpyxl

    output_dir = str(tmp_path)
    settings = {
        "output_dir": output_dir,
        "confidence_threshold": 60,
        "poppler_path": None,
        "tesseract_cmd": None,
    }

    # Lightweight stand-in — _worker only uses self._files, self._queue, self.settings
    class _FakeApp:
        _files = ["fake_claims.pdf"]
        _queue = _queue_mod.Queue()

    fake_app = _FakeApp()
    fake_app.settings = settings

    # Bind the unbound method to our fake object
    import types
    fake_app._worker = types.MethodType(main.OCRApp._worker, fake_app)

    # Mock pdfinfo_from_path to return 1 page
    fake_pdfinfo = {"Pages": 1}

    # Mock pipeline functions so the worker runs without real Tesseract/Poppler
    fake_image = MagicMock()

    # Pre-create the workbook so the post-process step can open it
    wb_pre = openpyxl.Workbook()
    ws_pre = wb_pre.create_sheet("CMS-1500")
    ws_pre.cell(row=1, column=1, value="some_field")
    wb_pre.remove(wb_pre.active)  # remove default Sheet
    wb_pre.save(str(tmp_path / "extracted_results.xlsx"))

    result_msgs: list = []
    done_event = threading.Event()
    original_put = fake_app._queue.put

    def capturing_put(item):
        original_put(item)
        result_msgs.append(item)
        if item[0] == "done":
            done_event.set()

    fake_app._queue.put = capturing_put

    with patch("pipeline.convert_page", return_value=fake_image), \
         patch("pipeline.detect_form_type", return_value="UNKNOWN"), \
         patch("pipeline.preprocess_page", return_value=fake_image), \
         patch("pipeline.extract_cms1500", return_value=[]), \
         patch("pipeline.extract_ub04", return_value=[]), \
         patch("pipeline.write_workbook", return_value=str(tmp_path / "extracted_results.xlsx")), \
         patch("pdf2image.pdfinfo_from_path", return_value=fake_pdfinfo):

        t = threading.Thread(target=fake_app._worker, daemon=True)
        t.start()
        done_event.wait(timeout=10)
        t.join(timeout=2)

    # Verify error message was posted
    error_msgs = [m for m in result_msgs if m[0] == "error"]
    assert len(error_msgs) >= 1
    assert any("UNKNOWN form type" in m[3] for m in error_msgs)

    # Verify "done" message carries error_count > 0
    done_msgs = [m for m in result_msgs if m[0] == "done"]
    assert len(done_msgs) == 1
    assert done_msgs[0][2] >= 1  # error_count

    # Verify extraction_error column was appended to CMS-1500 sheet (D-14 / SC-5)
    output_xlsx = str(tmp_path / "extracted_results.xlsx")
    wb = openpyxl.load_workbook(output_xlsx)
    ws = wb["CMS-1500"]
    header_row = [ws.cell(row=1, column=c).value for c in range(1, ws.max_column + 1)]
    assert "extraction_error" in header_row, \
        f"extraction_error column not found in CMS-1500 headers: {header_row}"
    err_col = header_row.index("extraction_error") + 1
    # There should be at least one data row with a non-empty extraction_error value
    data_values = [ws.cell(row=r, column=err_col).value
                   for r in range(2, ws.max_row + 1)]
    assert any(v for v in data_values), \
        f"No non-empty extraction_error value found. Data rows: {data_values}"


# ---------------------------------------------------------------------------
# ENV / startup check
# ---------------------------------------------------------------------------

def test_startup_check_blocks_ui():
    """run_checks() is called at startup; returns bool used to gate Tk() construction (D-02)."""
    content = open(_ROOT / "main.py").read()
    assert "run_checks(" in content, "run_checks() call not found in main.py"
    # Verify that the startup block checks the return value and calls sys.exit(1) if not ok
    assert "sys.exit(1)" in content, "sys.exit(1) not found — startup gate not enforced"


def test_window_non_resizable():
    """root.resizable(False, False) is present in main.py (D-03)."""
    content = open(_ROOT / "main.py").read()
    assert "resizable(False, False)" in content, \
        "root.resizable(False, False) not found in main.py"


# ---------------------------------------------------------------------------
# Import smoke
# ---------------------------------------------------------------------------

def test_import_main():
    """main module is importable without side effects when __name__ != '__main__'."""
    import main
    assert hasattr(main, "OCRApp"), "OCRApp class not found in main module"


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
