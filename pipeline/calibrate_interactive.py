# pipeline/calibrate_interactive.py
"""Interactive calibration tool — visually adjust OCR field coordinates.

Displays a PDF page with the 3 extracted field regions overlaid. Click and drag
on the image to draw a new bounding box for the selected field. Type coordinates
directly into the spinboxes for precise adjustment. Saves updated coordinates
to config/cms1500.py or config/ub04.py.

Template PDFs live in templates/:
    templates/template_cms.pdf   — CMS-1500 blank form
    templates/template_ub.pdf    — UB-04 blank form

Usage (templates are used by default):
    python pipeline/calibrate_interactive.py --form cms1500
    python pipeline/calibrate_interactive.py --form ub04

Usage (override with a specific PDF and page):
    python pipeline/calibrate_interactive.py --form cms1500 --pdf test.pdf --page 0
    python pipeline/calibrate_interactive.py --form ub04 --pdf test.pdf --page 6

Controls:
    - Select a field using the radio buttons on the left
    - Click and drag on the image to draw a new box for that field
    - Edit L/T/R/B spinboxes directly for precise pixel values
    - "Save to Config" writes all 3 fields back to the config file
    - "Reset" reloads coordinates from the config file on disk
"""
import argparse
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk

# Scale factor: original image is 2550x3300; display at 30% → ~765x990 px
_SCALE = 0.3

# One color per logical field
_FIELD_COLORS = {
    "patient_name":    "#00cc44",  # green
    "total_charge":    "#2277ff",  # blue
    "date_of_service": "#ff8800",  # orange
}

_FIELD_LABELS = {
    "patient_name":    "Patient Name",
    "total_charge":    "Total Charge",
    "date_of_service": "Date of Service",
}

# Whether each field is stored as a TableFieldDef (row_boxes) vs FieldDef (box)
_IS_TABLE = {
    "patient_name":    False,
    "total_charge":    False,
    "date_of_service": True,
}

# Ordered list for radio button display
_FIELD_ORDER = ["patient_name", "total_charge", "date_of_service"]


# ---------------------------------------------------------------------------
# Config file I/O
# ---------------------------------------------------------------------------

def _load_boxes(form: str, reload_module: bool = False) -> dict[str, tuple[int, int, int, int]]:
    """Read current box coordinates from config module."""
    import importlib
    if form == "cms1500":
        import config.cms1500 as mod
        if reload_module:
            importlib.reload(mod)
        fields = mod.CMS1500_FIELDS
        table_fields = mod.CMS1500_TABLE_FIELDS
    else:
        import config.ub04 as mod
        if reload_module:
            importlib.reload(mod)
        fields = mod.UB04_FIELDS
        table_fields = mod.UB04_TABLE_FIELDS

    boxes: dict[str, tuple[int, int, int, int]] = {}
    for fd in fields:
        if fd.name in _FIELD_COLORS:
            boxes[fd.name] = fd.box
    for tfd in table_fields:
        if tfd.name in _FIELD_COLORS:
            boxes[tfd.name] = tfd.row_boxes[0]
    return boxes


def _save_boxes(form: str, boxes: dict[str, tuple[int, int, int, int]]) -> list[str]:
    """Write updated coordinates to config/cms1500.py or config/ub04.py.

    Uses regex replacement on the Python source file — safe for this fixed format.
    Returns list of field names that were changed.
    """
    config_path = _ROOT / "config" / (f"{form}.py")
    content = config_path.read_text(encoding="utf-8")
    changed: list[str] = []

    for field_name, box in boxes.items():
        l, t, r, b = (int(v) for v in box)
        if _IS_TABLE[field_name]:
            # Match the first tuple inside row_boxes=[...] for this TableFieldDef.
            # The pattern crosses two lines so we use DOTALL.
            pattern = (
                r'(name="' + re.escape(field_name) + r'"'
                r'.*?row_boxes=\[\s*\n\s*)\(\d+,\s*\d+,\s*\d+,\s*\d+\)'
            )
            replacement = rf'\g<1>({l}, {t}, {r}, {b})'
            new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        else:
            # Match box=(...) immediately after name="field_name", on the same line.
            pattern = (
                r'(name="' + re.escape(field_name) + r'",\s*box=)\(\d+,\s*\d+,\s*\d+,\s*\d+\)'
            )
            replacement = rf'\g<1>({l}, {t}, {r}, {b})'
            new_content = re.sub(pattern, replacement, content)

        if new_content != content:
            content = new_content
            changed.append(field_name)

    config_path.write_text(content, encoding="utf-8")
    return changed


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

class CalibrationApp:
    def __init__(self, root: tk.Tk, pdf_path: str, page_num: int, form: str):
        self.root = root
        self.pdf_path = pdf_path
        self.page_num = page_num
        self.form = form

        self.root.title(f"Calibrate — {form.upper()}  page {page_num}  |  {Path(pdf_path).name}")
        self.root.resizable(True, True)

        # Working copies of box coordinates [l, t, r, b]
        self.boxes: dict[str, list[int]] = {}

        # Currently selected field
        self.selected = tk.StringVar(value="patient_name")

        # Drag state
        self._drag_start: tuple[float, float] | None = None

        # Spinbox IntVars for coordinate display/edit
        self._coords = {k: tk.IntVar(value=0) for k in ("l", "t", "r", "b")}

        # Canvas items keyed by field name
        self._rect_ids: dict[str, int] = {}
        self._label_ids: dict[str, int] = {}

        # PIL image and PhotoImage (kept alive to prevent GC)
        self._pil_img: Image.Image | None = None
        self._photo: ImageTk.PhotoImage | None = None

        self._build_ui()
        self._load_page()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        # ── Left panel ────────────────────────────────────────────────
        left = ttk.Frame(self.root, padding=10)
        left.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(left, text=f"Form: {self.form.upper()}", font=("", 11, "bold")).pack(anchor=tk.W)
        ttk.Label(left, text=f"Page: {self.page_num}", foreground="gray").pack(anchor=tk.W, pady=(0, 10))

        # Field radio buttons
        ttk.Label(left, text="Field to edit:", font=("", 9, "bold")).pack(anchor=tk.W)
        for name in _FIELD_ORDER:
            color = _FIELD_COLORS[name]
            f = ttk.Frame(left)
            f.pack(anchor=tk.W, pady=1)
            tk.Radiobutton(
                f, text=_FIELD_LABELS[name],
                variable=self.selected, value=name,
                command=self._on_field_selected,
                fg=color, selectcolor="#f0f0f0",
                font=("", 9),
            ).pack(side=tk.LEFT)

        ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Coordinate spinboxes
        ttk.Label(left, text="Box coordinates (px):", font=("", 9, "bold")).pack(anchor=tk.W)
        grid = ttk.Frame(left)
        grid.pack(fill=tk.X)
        labels = [("l", "Left  "), ("t", "Top   "), ("r", "Right "), ("b", "Bottom")]
        for row, (key, lbl) in enumerate(labels):
            ttk.Label(grid, text=lbl, width=7).grid(row=row, column=0, sticky=tk.W, pady=1)
            sb = ttk.Spinbox(
                grid, textvariable=self._coords[key],
                from_=0, to=3300, width=7, increment=1,
            )
            sb.grid(row=row, column=1, sticky=tk.W, padx=4, pady=1)
            sb.bind("<Return>", lambda _e: self._apply_spinbox_coords())
            sb.bind("<FocusOut>", lambda _e: self._apply_spinbox_coords())

        ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Label(
            left, text="Click + drag on image\nto redefine box",
            foreground="gray", justify=tk.LEFT,
        ).pack(anchor=tk.W)

        ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        ttk.Button(left, text="Save to Config", command=self._save).pack(fill=tk.X, pady=2)
        ttk.Button(left, text="Reset from file", command=self._reset).pack(fill=tk.X, pady=2)
        ttk.Button(left, text="Close", command=self.root.destroy).pack(fill=tk.X, pady=2)

        # ── Canvas panel ──────────────────────────────────────────────
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="#222", cursor="crosshair")
        vbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        hbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)

        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self._drag_start)
        self.canvas.bind("<B1-Motion>", self._drag_move)
        self.canvas.bind("<ButtonRelease-1>", self._drag_end)

    # ------------------------------------------------------------------
    # Page loading
    # ------------------------------------------------------------------

    def _load_page(self):
        from config_loader import load_settings
        from pipeline.converter import convert_page
        from pipeline.preprocessor import preprocess_page

        settings = load_settings()
        print(f"Loading page {self.page_num} from {self.pdf_path!r}…")
        raw = convert_page(self.pdf_path, self.page_num)
        self._pil_img = preprocess_page(raw, settings)

        w, h = self._pil_img.size
        dw, dh = int(w * _SCALE), int(h * _SCALE)
        display = self._pil_img.resize((dw, dh), Image.LANCZOS)
        self._photo = ImageTk.PhotoImage(display)

        self.canvas.config(scrollregion=(0, 0, dw, dh))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self._photo, tags="bg")

        raw_boxes = _load_boxes(self.form)
        self.boxes = {k: list(v) for k, v in raw_boxes.items()}

        self._redraw_all()
        self._sync_spinboxes()

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _redraw_all(self):
        for name in _FIELD_ORDER:
            if name in self.boxes:
                self._draw_box(name)

    def _draw_box(self, name: str):
        color = _FIELD_COLORS[name]
        l, t, r, b = self.boxes[name]
        cl = int(l * _SCALE)
        ct = int(t * _SCALE)
        cr = int(r * _SCALE)
        cb = int(b * _SCALE)

        selected = name == self.selected.get()
        width = 3 if selected else 1
        dash = () if selected else (6, 3)

        for item_id in (self._rect_ids.pop(name, None), self._label_ids.pop(name, None)):
            if item_id:
                self.canvas.delete(item_id)

        self._rect_ids[name] = self.canvas.create_rectangle(
            cl, ct, cr, cb, outline=color, width=width, dash=dash,
        )
        self._label_ids[name] = self.canvas.create_text(
            cl + 4, ct + 4, anchor=tk.NW,
            text=_FIELD_LABELS[name],
            fill=color, font=("", 8, "bold"),
        )

    def _sync_spinboxes(self):
        name = self.selected.get()
        if name in self.boxes:
            l, t, r, b = self.boxes[name]
            self._coords["l"].set(int(l))
            self._coords["t"].set(int(t))
            self._coords["r"].set(int(r))
            self._coords["b"].set(int(b))

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_field_selected(self):
        self._redraw_all()
        self._sync_spinboxes()

    def _apply_spinbox_coords(self):
        name = self.selected.get()
        if name not in self.boxes:
            return
        try:
            self.boxes[name] = [
                self._coords["l"].get(),
                self._coords["t"].get(),
                self._coords["r"].get(),
                self._coords["b"].get(),
            ]
            self._draw_box(name)
        except tk.TclError:
            pass

    def _drag_start(self, event):
        self._drag_start_pos = (
            self.canvas.canvasx(event.x),
            self.canvas.canvasy(event.y),
        )

    def _drag_move(self, event):
        if not hasattr(self, "_drag_start_pos") or self._drag_start_pos is None:
            return
        x0, y0 = self._drag_start_pos
        x1 = self.canvas.canvasx(event.x)
        y1 = self.canvas.canvasy(event.y)
        name = self.selected.get()
        self.boxes[name] = [
            int(min(x0, x1) / _SCALE),
            int(min(y0, y1) / _SCALE),
            int(max(x0, x1) / _SCALE),
            int(max(y0, y1) / _SCALE),
        ]
        self._draw_box(name)
        self._sync_spinboxes()

    def _drag_end(self, event):
        self._drag_move(event)
        self._drag_start_pos = None

    # ------------------------------------------------------------------
    # Save / Reset
    # ------------------------------------------------------------------

    def _save(self):
        changed = _save_boxes(self.form, {k: tuple(v) for k, v in self.boxes.items()})
        if changed:
            messagebox.showinfo(
                "Saved",
                f"Updated config/{self.form}.py:\n" +
                "\n".join(f"  • {_FIELD_LABELS.get(f, f)}" for f in changed),
            )
        else:
            messagebox.showinfo("No change", "Coordinates match what is already in the config file.")

    def _reset(self):
        raw_boxes = _load_boxes(self.form, reload_module=True)
        self.boxes = {k: list(v) for k, v in raw_boxes.items()}
        for name in list(self._rect_ids):
            self.canvas.delete(self._rect_ids.pop(name))
        for name in list(self._label_ids):
            self.canvas.delete(self._label_ids.pop(name))
        self._redraw_all()
        self._sync_spinboxes()


# Template PDF paths (relative to project root)
_TEMPLATES = {
    "cms1500": _ROOT / "templates" / "template_cms.pdf",
    "ub04":    _ROOT / "templates" / "template_ub.pdf",
}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Interactive calibration for OCR field bounding boxes.",
        epilog=(
            "Default usage (loads template automatically):\n"
            "  python pipeline/calibrate_interactive.py --form cms1500\n"
            "  python pipeline/calibrate_interactive.py --form ub04\n\n"
            "Override with a specific PDF:\n"
            "  python pipeline/calibrate_interactive.py --form cms1500 --pdf test.pdf --page 0"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--form", choices=["cms1500", "ub04"], required=True,
        help="Form type to calibrate",
    )
    parser.add_argument(
        "--pdf", default=None,
        help="PDF to display (default: templates/template_cms.pdf or templates/template_ub.pdf)",
    )
    parser.add_argument(
        "--page", type=int, default=0,
        help="0-indexed page number (default: 0)",
    )
    args = parser.parse_args()

    # Resolve PDF path — prefer explicit arg, fall back to template
    if args.pdf:
        pdf_path = args.pdf
    else:
        template = _TEMPLATES[args.form]
        if not template.exists():
            parser.error(
                f"Template not found: {template}\n"
                f"Place the blank {args.form.upper()} form PDF at that path, "
                "or pass --pdf to specify a different file."
            )
        pdf_path = str(template)
        print(f"Using template: {template}")

    root = tk.Tk()
    CalibrationApp(root, pdf_path, args.page, args.form)
    root.mainloop()


if __name__ == "__main__":
    main()
