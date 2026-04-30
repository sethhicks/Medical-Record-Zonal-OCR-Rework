# pipeline/__init__.py
"""Image pipeline public API for OCR Medical Billing Form Extractor.

Exposes:
    convert_page(pdf_path, page_num) -> PIL.Image.Image
    preprocess_page(image, settings, debug=False) -> PIL.Image.Image
"""
from .converter import convert_page

try:
    from .preprocessor import preprocess_page
except ImportError:
    preprocess_page = None  # type: ignore[assignment]  # populated by 02-06-PLAN

__all__ = ["convert_page", "preprocess_page"]
