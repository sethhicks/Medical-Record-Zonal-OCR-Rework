# pipeline/__init__.py
"""Image pipeline public API for OCR Medical Billing Form Extractor.

Exposes:
    convert_page(pdf_path, page_num) -> PIL.Image.Image
    preprocess_page(image, settings, debug=False) -> PIL.Image.Image
"""
from .converter import convert_page
from .preprocessor import preprocess_page

__all__ = ["convert_page", "preprocess_page"]
