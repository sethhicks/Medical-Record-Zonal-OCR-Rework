"""OCR Medical Billing Form Extractor — main entry point.

Implements OCRApp: a tkinter desktop UI that wires all pipeline stages together.
Billing staff select PDFs, watch per-page progress, read inline errors, and open
the output Excel file — all without understanding the pipeline.

Decisions implemented: D-01 through D-14 from 06-CONTEXT.md.
"""
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path


class OCRApp:
    """Main application window for the OCR Medical Billing Form Extractor.

    Wires all pipeline stages behind a responsive tkinter UI.
    The worker runs on a background thread; widgets are only touched from the
    main thread via the poll_queue callback (threading model from STATE.md).
    """

    def __init__(self, root: tk.Tk, settings: dict) -> None:
        """Construct the application window.

        Args:
            root: The tkinter root window.
            settings: Dict from load_settings(); provides output_dir, tesseract_cmd,
                      poppler_path, confidence_threshold.
        """
        self.root = root
        self.settings = settings
        self._files: list[str] = []
        self._queue: queue.Queue = queue.Queue()
        self._output_path: str | None = None

        # Window configuration (D-03)
        root.title("OCR Medical Billing Extractor")
        root.geometry("500x400")
        root.resizable(False, False)

        # ---- Row 0: Button row (Select PDFs + Clear) ----
        btn_frame = tk.Frame(root)
        btn_frame.pack(fill=tk.X, padx=10, pady=(10, 4))
        self.btn_select = ttk.Button(btn_frame, text="Select PDFs", command=self.on_select)
        self.btn_select.pack(side=tk.LEFT, padx=(0, 6))
        self.btn_clear = ttk.Button(btn_frame, text="Clear", command=self.on_clear)
        self.btn_clear.pack(side=tk.LEFT)

        # ---- Row 1: File listbox (D-06) ----
        list_frame = tk.Frame(root)
        list_frame.pack(fill=tk.BOTH, padx=10, pady=4)
        self.listbox = tk.Listbox(list_frame, height=5, selectmode=tk.BROWSE)
        self.listbox.pack(fill=tk.BOTH, expand=True)

        # ---- Row 2: Output label (D-04, D-05) — always visible, read-only ----
        output_dir = settings.get("output_dir", str(Path.home() / "Desktop"))
        output_path_str = os.path.join(output_dir, "extracted_results.xlsx")
        self.lbl_output = tk.Label(root, text=f"Output: {output_path_str}",
                                   anchor="w", wraplength=480)
        self.lbl_output.pack(fill=tk.X, padx=10, pady=2)

        # ---- Row 3: Progress bar + page counter (D-10) ----
        prog_frame = tk.Frame(root)
        prog_frame.pack(fill=tk.X, padx=10, pady=4)
        self.progress_bar = ttk.Progressbar(prog_frame, orient=tk.HORIZONTAL,
                                            mode="determinate", maximum=100)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.lbl_page = tk.Label(prog_frame, text="Page 0 / 0", width=12, anchor="w")
        self.lbl_page.pack(side=tk.LEFT)

        # ---- Row 4: Error log — read-only Text widget with scrollbar (D-11) ----
        log_frame = tk.Frame(root)
        log_frame.pack(fill=tk.BOTH, padx=10, pady=4)
        scrollbar = tk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.error_log = tk.Text(log_frame, height=4, state=tk.DISABLED,
                                 yscrollcommand=scrollbar.set)
        self.error_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.error_log.yview)

        # ---- Row 5: Start + Open output buttons (D-07, D-09) ----
        bot_frame = tk.Frame(root)
        bot_frame.pack(fill=tk.X, padx=10, pady=(4, 10))
        self.btn_start = ttk.Button(bot_frame, text="Start", command=self.on_start)
        self.btn_start.pack(side=tk.LEFT)
        self.btn_open = ttk.Button(bot_frame, text="Open output file",
                                   command=self.on_open_output, state=tk.DISABLED)
        self.btn_open.pack(side=tk.RIGHT)

    # ------------------------------------------------------------------
    # File-selection handlers (UI-01)
    # ------------------------------------------------------------------

    def on_select(self) -> None:
        """Open file dialog and populate listbox with selected PDFs (D-07)."""
        paths = filedialog.askopenfilenames(
            title="Select PDF files",
            filetypes=[("PDF files", "*.pdf")]
        )
        if paths:
            self._files = list(paths)
            self.listbox.delete(0, tk.END)
            for p in self._files:
                self.listbox.insert(tk.END, os.path.basename(p))

    def on_clear(self) -> None:
        """Clear the file list and listbox (D-07)."""
        self._files = []
        self.listbox.delete(0, tk.END)

    # ------------------------------------------------------------------
    # Run lifecycle (UI-02)
    # ------------------------------------------------------------------

    def on_start(self) -> None:
        """Validate file selection, disable controls, and launch worker thread (D-08)."""
        if not self._files:
            messagebox.showwarning("No files", "Select at least one PDF before starting.")
            return
        # Disable controls during processing (D-08)
        self.btn_select.config(state=tk.DISABLED)
        self.btn_clear.config(state=tk.DISABLED)
        self.btn_start.config(state=tk.DISABLED)
        self.btn_open.config(state=tk.DISABLED)
        # Clear error log for new run (D-13)
        self.error_log.config(state=tk.NORMAL)
        self.error_log.delete("1.0", tk.END)
        self.error_log.config(state=tk.DISABLED)
        # Reset progress
        self.progress_bar["value"] = 0
        self.lbl_page.config(text="Page 0 / 0")
        # Start worker thread (threading model: threading.Thread + queue.Queue)
        t = threading.Thread(target=self._worker, daemon=True)
        t.start()
        # Begin polling (root.after(100) — never call widgets from worker thread)
        self.root.after(100, self.poll_queue)

    def _worker(self) -> None:
        """Background worker: convert → detect → extract → write workbook.

        Runs on a daemon thread. MUST NOT touch any tkinter widgets directly.
        All communication with the main thread is via self._queue.

        Queue messages posted:
            ("progress", current_page, total_pages)
            ("error", pdf_path, page_num, error_message)
            ("done", output_path, error_count)
        """
        import pipeline
        import openpyxl as _openpyxl
        files = list(self._files)
        settings = self.settings

        # Count total pages across all files
        from pdf2image import pdfinfo_from_path
        total = 0
        page_counts: list[int] = []
        for pdf_path in files:
            try:
                info = pdfinfo_from_path(pdf_path, poppler_path=settings.get("poppler_path"))
                n_pages = info["Pages"]
            except Exception:
                n_pages = 0
            page_counts.append(n_pages)
            total += n_pages

        cms_pages: list = []
        ub_pages: list = []
        error_pages: list[tuple[str, str]] = []  # (form_type_guess, error_message)
        current = 0

        for pdf_path, n_pages in zip(files, page_counts):
            for page_num in range(n_pages):
                current += 1
                self._queue.put(("progress", current, total))
                try:
                    raw = pipeline.convert_page(pdf_path, page_num)
                    form = pipeline.detect_form_type(raw)
                    if form == "UNKNOWN":
                        self._queue.put(("error", pdf_path, page_num,
                                         "UNKNOWN form type"))
                        error_pages.append(("UNKNOWN", "UNKNOWN form type"))
                    else:
                        proc = pipeline.preprocess_page(raw, settings)
                        if form == "CMS-1500":
                            results = pipeline.extract_cms1500(proc, settings)
                            cms_pages.append(results)
                        else:
                            results = pipeline.extract_ub04(proc, settings)
                            ub_pages.append(results)
                except Exception as exc:
                    self._queue.put(("error", pdf_path, page_num, str(exc)))
                    error_pages.append(("UNKNOWN", str(exc)))

        # Write workbook — WR-02 fix: ensure output_dir exists before saving
        output_path: str | None = None
        try:
            os.makedirs(settings.get("output_dir", str(Path.home() / "Desktop")),
                        exist_ok=True)
            output_path = pipeline.write_workbook(cms_pages, ub_pages, settings)
        except Exception as exc:
            self._queue.put(("error", "", 0, f"write_workbook failed: {exc}"))

        # Post-process: append blank rows for error pages to the CMS-1500 sheet (D-14 / SC-5).
        # write_workbook() signature is frozen (Phase 5 D-06) — do NOT pass error_pages to it.
        # Open the saved workbook and append one blank row per error page with only the
        # extraction_error column populated.
        if output_path and error_pages:
            try:
                wb = _openpyxl.load_workbook(output_path)
                ws = wb["Results"]
                # Find extraction_error column index (1-based) by scanning header row
                header_row = [ws.cell(row=1, column=c).value
                              for c in range(1, ws.max_column + 1)]
                try:
                    err_col = header_row.index("extraction_error") + 1
                except ValueError:
                    # Column not present — append as a new column after the last header
                    err_col = ws.max_column + 1
                    ws.cell(row=1, column=err_col, value="extraction_error")
                next_row = ws.max_row + 1
                for _, err_msg in error_pages:
                    ws.cell(row=next_row, column=err_col, value=err_msg)
                    next_row += 1
                wb.save(output_path)
            except Exception as exc:
                self._queue.put(("error", "", 0, f"error_pages write failed: {exc}"))

        self._queue.put(("done", output_path, len(error_pages)))

    def poll_queue(self) -> None:
        """Read all pending queue messages and update UI accordingly.

        Called every 100ms via root.after(100, self.poll_queue). Drains the entire
        queue in one tick for responsiveness. On "done", calls _on_done and stops
        re-scheduling itself.
        """
        done = False
        done_args: tuple = (None, 0)
        try:
            while True:
                msg = self._queue.get_nowait()
                kind = msg[0]
                if kind == "progress":
                    _, current, total = msg
                    pct = int(current / total * 100) if total > 0 else 0
                    self.progress_bar["value"] = pct
                    self.lbl_page.config(text=f"Page {current} / {total}")
                elif kind == "error":
                    _, filename, page_num, error_message = msg
                    basename = os.path.basename(filename) if filename else "unknown"
                    line = f"{basename} page {page_num}: {error_message}\n"
                    self.error_log.config(state=tk.NORMAL)
                    self.error_log.insert(tk.END, line)
                    self.error_log.see(tk.END)
                    self.error_log.config(state=tk.DISABLED)
                elif kind == "done":
                    _, output_path, error_count = msg
                    self._output_path = output_path
                    done_args = (output_path, error_count)
                    done = True
        except queue.Empty:
            pass

        if done:
            self._on_done(*done_args)
        else:
            self.root.after(100, self.poll_queue)

    def _on_done(self, output_path: str | None, error_count: int) -> None:
        """Handle run completion: re-enable controls, clear file list, show summary.

        Called from poll_queue on the main thread after receiving "done" message.

        Args:
            output_path: Full path to the written workbook, or None if write failed.
            error_count: Number of pages that failed (UNKNOWN or exception).
        """
        # Re-enable controls (D-09)
        self.btn_select.config(state=tk.NORMAL)
        self.btn_clear.config(state=tk.NORMAL)
        self.btn_start.config(state=tk.NORMAL)
        # Enable Open output button only if workbook was written (D-09)
        if output_path:
            self.btn_open.config(state=tk.NORMAL)
        # Clear file list for next batch (D-09)
        self._files = []
        self.listbox.delete(0, tk.END)
        # Set progress to 100%
        self.progress_bar["value"] = 100
        # Show failure count summary in error log (SC-5)
        if error_count > 0:
            self.error_log.config(state=tk.NORMAL)
            self.error_log.insert(
                tk.END,
                f"--- Run complete. {error_count} page(s) failed — see errors above. ---\n"
            )
            self.error_log.see(tk.END)
            self.error_log.config(state=tk.DISABLED)

    def on_open_output(self) -> None:
        """Open the output Excel file in the default application (Windows os.startfile)."""
        if self._output_path and os.path.exists(self._output_path):
            os.startfile(self._output_path)
        else:
            messagebox.showerror("File not found",
                                 f"Output file not found:\n{self._output_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from config_loader import load_settings
    settings = load_settings()

    from setup_check import run_checks
    ok = run_checks(settings=settings, quiet=True)
    if not ok:
        # Show error before any Tk() window (D-02)
        import sys
        _root = tk.Tk()
        _root.withdraw()
        messagebox.showerror(
            "Dependency Error",
            "Tesseract or Poppler not found.\n\nRun setup_check.py for details."
        )
        sys.exit(1)

    root = tk.Tk()
    app = OCRApp(root, settings)
    root.mainloop()
