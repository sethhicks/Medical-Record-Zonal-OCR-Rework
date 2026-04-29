# config/base.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class FieldDef:
    """Coordinate definition for a single-value form field."""
    name: str                              # e.g. "box1a_insured_id"
    box: tuple[int, int, int, int]         # (left, top, right, bottom) at 300 DPI
    psm: int = 6                           # Tesseract PSM mode; 6=block, 7=line, 8=word
    whitelist: Optional[str] = None        # tessedit_char_whitelist value; None = no restriction
    label: str = ""                        # display label for Phase 2 calibration overlay


@dataclass
class TableFieldDef:
    """Coordinate definition for a repeating row structure.

    Used for Box 24 service lines (6 rows) and UB-04 revenue lines (22 rows).
    row_boxes[i] is the pixel region for row i (0-indexed).
    """
    name: str                                        # e.g. "box24_cpt"
    row_boxes: list[tuple[int, int, int, int]]       # one (l,t,r,b) per row
    psm: int = 7                                     # single line default for table cells
    whitelist: Optional[str] = None
    label: str = ""
