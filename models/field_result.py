# models/field_result.py
from dataclasses import dataclass


@dataclass
class FieldResult:
    """OCR result for a single form field."""
    field_name: str    # matches FieldDef.name
    value: str         # raw OCR text, stripped
    confidence: float  # 0.0-100.0; -1.0 if no text found in region
