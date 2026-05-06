# pipeline/__init__.py
"""Image pipeline public API for OCR Medical Billing Form Extractor.

Exposes:
    convert_page(pdf_path, page_num) -> PIL.Image.Image
    preprocess_page(image, settings, debug=False) -> PIL.Image.Image
    detect_form_type(image) -> str
    extract_cms1500(image, settings) -> list[FieldResult]
    extract_ub04(image, settings) -> list[FieldResult]
    write_workbook(cms_pages, ub_pages, settings) -> str
"""
from .converter import convert_page
from .preprocessor import preprocess_page
from .detector import detect_form_type
from .extractor_cms1500 import extract_cms1500
from .extractor_ub04 import extract_ub04
from .writer import write_workbook

__all__ = [
    "convert_page",
    "preprocess_page",
    "detect_form_type",
    "extract_cms1500",
    "extract_ub04",
    "write_workbook",
]
