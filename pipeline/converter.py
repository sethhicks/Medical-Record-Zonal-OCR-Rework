# pipeline/converter.py
"""PDF-to-PIL page converter for OCR Medical Billing Form Extractor.

Standalone usage (for ad-hoc testing):
    python -c "from pipeline.converter import convert_page; img = convert_page('test.pdf', 0); print(img.size)"

Importable usage:
    from pipeline import convert_page
    image = convert_page(pdf_path, page_num)  # returns 2550x3300 RGB PIL Image
"""
from pathlib import Path

from pdf2image import convert_from_path
from PIL import Image

from config_loader import load_settings

# Target dimensions for US Letter at 300 DPI (D-13)
_TARGET_W = 2550
_TARGET_H = 3300

# Tolerance: accept pages within ±10% of target dimensions; wider deviations are
# not US Letter 8.5x11 forms and must be rejected. Scanners may produce slightly
# undersized pages (e.g. 2478x3228) due to scanner margin settings — these are
# normalised to the target coordinate space via Lanczos resize.
_TOLERANCE = 0.10


def convert_page(pdf_path: str, page_num: int) -> "Image.Image":
    """Convert one PDF page to a 300 DPI PIL Image normalised to 2550x3300 px.

    Args:
        pdf_path: Absolute or relative path to the PDF file.
        page_num: 0-indexed page number.

    Returns:
        PIL.Image.Image, mode "RGB", size 2550x3300 px.

    Raises:
        ValueError: If the resulting image deviates more than 10% from 2550x3300
                    (D-13) — indicates a non-US-Letter or landscape input that cannot
                    be normalised into the expected coordinate space.
        FileNotFoundError: If pdf_path does not exist.
        Exception: If pdf2image cannot parse the file (PDFInfoNotInstalledError,
                   PDFPageCountError, etc.) — not caught here; propagates to caller.

    Notes:
        - Always passes poppler_path explicitly from settings (never uses PATH).
        - pdf2image returns a list even for a single page; always indexes [0].
        - 300 DPI * 8.5 in = 2550 px wide; 300 DPI * 11 in = 3300 px tall.
        - Scanners may produce slightly undersized pages (e.g. 2478x3228 from an
          8.26x10.76 in scan). Pages within ±10% are resized to exactly 2550x3300
          so that all fixed coordinate regions remain valid.
        - Pages beyond ±10% of the target dimensions raise ValueError.
    """
    settings = load_settings()
    poppler_path = settings["poppler_path"]  # explicit path per Windows convention

    # pdf2image is 1-indexed; convert 0-indexed page_num
    pages = convert_from_path(
        pdf_path,
        dpi=300,
        first_page=page_num + 1,
        last_page=page_num + 1,
        poppler_path=poppler_path,
    )

    image = pages[0]  # always a list, even for single page

    w, h = image.size
    w_ratio = w / _TARGET_W
    h_ratio = h / _TARGET_H

    if abs(w_ratio - 1.0) > _TOLERANCE or abs(h_ratio - 1.0) > _TOLERANCE:
        raise ValueError(
            f"Expected ~2550x3300 px (±10%) at 300 DPI, got {image.size} "
            f"(page {page_num}, {str(Path(pdf_path).resolve())!r}). "
            "Input may not be a US Letter 8.5x11 in form."
        )

    # Normalise to exact target dimensions so all fixed coordinate regions are valid.
    # Lanczos (LANCZOS) is the highest-quality downsampling filter in Pillow.
    if image.size != (_TARGET_W, _TARGET_H):
        image = image.resize((_TARGET_W, _TARGET_H), Image.LANCZOS)

    return image
