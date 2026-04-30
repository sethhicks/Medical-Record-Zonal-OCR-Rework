# pipeline/calibrate.py
"""Calibration overlay CLI for OCR Medical Billing Form Extractor.

Renders a page of a PDF with all configured field regions drawn as labelled
rectangles. Used to visually verify pixel coordinates before Phase 4 extraction.

Usage:
    python pipeline/calibrate.py --page 0 --pdf test.pdf
    python pipeline/calibrate.py --page 0 --pdf test.pdf --form cms1500
    python pipeline/calibrate.py --page 2 --pdf test.pdf --form ub04

Output:
    calibration_overlay_p{N}.png  (written to current working directory — D-01)

Per decisions:
    D-01: PNG only, no auto-open, no cv2.imshow().
    D-02: --page N --pdf PATH [--form TYPE]
    D-03: Labels are full FieldDef.name drawn outside (above) each rectangle.
    D-04: Only the field set matching the detected form type is drawn.
"""
import sys
from pathlib import Path

# Ensure the project root is on sys.path so that project modules (config_loader,
# config, pipeline) are importable regardless of the working directory from which
# the script is invoked (the test harness runs with cwd=tmp_path).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Form type detection heuristic (Phase 2 only — replaced by Phase 3 detector)
# ---------------------------------------------------------------------------

def _detect_form_type(cv_img: "np.ndarray") -> str:
    """Best-effort form type detection via OCR on anchor text regions.

    Searches two small header regions for known anchor strings:
      - CMS-1500: "HEALTH INSURANCE" at top-left (~y=30-120)
      - UB-04: "UB-04" at top-right (~y=30-120)

    Returns "cms1500", "ub04", or "cms1500" (default if uncertain).
    """
    try:
        import pytesseract
        from config_loader import load_settings
        settings = load_settings()
        pytesseract.pytesseract.tesseract_cmd = settings["tesseract_cmd"]

        # Sample top strip of the image for anchor text
        top_strip = cv_img[30:150, :, :]
        text = pytesseract.image_to_string(top_strip, config="--psm 6").upper()

        if "UB-04" in text or "UNIFORM BILLING" in text or "UB04" in text:
            return "ub04"
        elif "HEALTH INSURANCE" in text or "1500" in text:
            return "cms1500"
        else:
            print(
                "WARNING: Could not auto-detect form type from anchor text. "
                "Defaulting to CMS-1500. Use --form to override.",
                file=sys.stderr,
            )
            return "cms1500"
    except Exception:
        # pytesseract unavailable or OCR fails — fall back to CMS-1500
        print(
            "WARNING: Auto-detection failed (pytesseract error). "
            "Defaulting to CMS-1500. Use --form ub04 to override.",
            file=sys.stderr,
        )
        return "cms1500"


# ---------------------------------------------------------------------------
# Overlay rendering
# ---------------------------------------------------------------------------

def _draw_overlay(cv_img: "np.ndarray", fields, table_fields) -> "np.ndarray":
    """Draw field regions on cv_img and return the annotated image.

    Args:
        cv_img: OpenCV BGR image (2550x3300).
        fields: list[FieldDef] — single-value fields; drawn as green rectangles.
        table_fields: list[TableFieldDef] — table rows; drawn as orange rectangles.

    Returns:
        Annotated BGR image.

    Visual conventions (Claude's discretion per CONTEXT.md):
        FieldDef:      green rectangle (0, 255, 0), thickness 2
        TableFieldDef: orange rectangle (0, 200, 255), thickness 1
        Labels:        red text (0, 0, 255), FONT_HERSHEY_SIMPLEX
                       drawn ABOVE the rectangle (outside, per D-03)
    """
    overlay = cv_img.copy()

    # Draw FieldDef regions — green, thickness 2
    for field in fields:
        l, t, r, b = field.box
        cv2.rectangle(overlay, (l, t), (r, b), (0, 255, 0), 2)
        # Label above the rectangle (D-03: full name, outside)
        label_y = max(t - 4, 12)  # clamp so label doesn't go off the top edge
        cv2.putText(
            overlay, field.name,
            (l, label_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1, cv2.LINE_AA,
        )

    # Draw TableFieldDef row regions — orange, thickness 1
    for table_field in table_fields:
        for row_idx, (l, t, r, b) in enumerate(table_field.row_boxes):
            cv2.rectangle(overlay, (l, t), (r, b), (0, 200, 255), 1)
            label = f"{table_field.name}_r{row_idx}"
            label_y = max(t - 4, 12)
            cv2.putText(
                overlay, label,
                (l, label_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 140, 255), 1, cv2.LINE_AA,
            )

    return overlay


# ---------------------------------------------------------------------------
# Main execution function
# ---------------------------------------------------------------------------

def _run(pdf_path: str, page_num: int, form_type: "str | None" = None) -> None:
    """Convert page, apply preprocessing, draw overlay, write PNG.

    Args:
        pdf_path: Path to PDF file.
        page_num: 0-indexed page number.
        form_type: "cms1500", "ub04", or None (auto-detect).
    """
    from config_loader import load_settings
    from pipeline.converter import convert_page
    from pipeline.preprocessor import preprocess_page
    from config.cms1500 import CMS1500_FIELDS, CMS1500_TABLE_FIELDS
    from config.ub04 import UB04_FIELDS, UB04_TABLE_FIELDS
    from PIL import Image

    settings = load_settings()

    # Convert raw page
    print(f"Converting page {page_num} of {pdf_path!r}...")
    raw_image = convert_page(pdf_path, page_num)

    # Preprocess (applies scale correction — D-05 specifics: overlay must use corrected coords)
    print("Preprocessing (scale correction + deskew + threshold)...")
    preprocessed = preprocess_page(raw_image, settings)

    # Convert preprocessed PIL Image → OpenCV BGR for overlay drawing
    cv_img = cv2.cvtColor(np.array(preprocessed), cv2.COLOR_RGB2BGR)

    # Determine form type
    if form_type is None:
        detected = _detect_form_type(cv_img)
        detection_source = "auto-detected"
    else:
        detected = form_type.lower()
        detection_source = "user-specified"

    # Load matching field sets (D-04: only draw fields for detected form type)
    if detected == "ub04":
        fields = UB04_FIELDS
        table_fields = UB04_TABLE_FIELDS
    else:
        # Default to CMS-1500 for any unrecognised value
        detected = "cms1500"
        fields = CMS1500_FIELDS
        table_fields = CMS1500_TABLE_FIELDS

    # Draw overlay
    overlay = _draw_overlay(cv_img, fields, table_fields)

    # Count regions for summary
    table_row_count = sum(len(tf.row_boxes) for tf in table_fields)

    # Write PNG to current working directory (D-01; tests use cwd=tmp_path)
    out_path = Path(f"calibration_overlay_p{page_num}.png")
    Image.fromarray(cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)).save(str(out_path))

    # Stdout summary (Claude's discretion per CONTEXT.md)
    print(f"Form type:  {detected.upper()} ({detection_source})")
    print(f"Page:       {page_num}")
    print(
        f"Fields:     {len(fields)} FieldDef + {len(table_fields)} TableFieldDef "
        f"({table_row_count} total row regions)"
    )
    print(f"Output:     {out_path.resolve()}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Render calibration overlay PNG for a PDF page.",
        epilog=(
            "Example: python pipeline/calibrate.py --page 0 --pdf test.pdf\n"
            "WARNING: --pdf accepts trusted developer input only (T-2-02)."
        ),
    )
    parser.add_argument(
        "--page", type=int, required=True,
        help="0-indexed page number to render",
    )
    parser.add_argument(
        "--pdf", required=True,
        help="Path to PDF file (trusted input only — developer tool)",
    )
    parser.add_argument(
        "--form",
        choices=["cms1500", "ub04"],
        default=None,
        help="Force form type (default: auto-detect from anchor text)",
    )
    args = parser.parse_args()

    _run(pdf_path=args.pdf, page_num=args.page, form_type=args.form)
    sys.exit(0)
