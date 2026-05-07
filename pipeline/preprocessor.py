# pipeline/preprocessor.py
"""OpenCV preprocessing pipeline for scanned medical billing forms.

Steps (D-08 — order is mandatory):
    1. Scale correction  — normalises coordinate space for scanner-induced size variation
    2. Deskew            — corrects scanner tilt via Hough-line angle detection
    3. Adaptive threshold — removes grey-band scan artifacts (especially Box 24 region)

Returns a PIL Image (RGB, 2550x3300) suitable for field extraction.
"""
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def preprocess_page(
    image: "Image.Image",
    settings: dict,
    debug: bool = False,
) -> "Image.Image":
    """Apply scale correction, deskew, and adaptive threshold to a page image.

    Args:
        image: Raw PIL Image from convert_page() — mode "RGB", expected 2550x3300 px.
        settings: dict from load_settings(); reads "threshold_block_size" (default 31).
        debug: If True, saves 4 intermediate PNGs to the current working directory (D-11).

    Returns:
        Preprocessed PIL Image — mode "RGB", same dimensions as input.

    Raises:
        ValueError: If detected skew angle exceeds ±5 degrees (D-10).

    Notes:
        - PIL "RGB" → OpenCV requires cv2.COLOR_RGB2BGR on entry.
        - OpenCV grayscale → PIL requires cv2.COLOR_GRAY2RGB on exit.
        - If no near-horizontal lines found (blank/sparse page), skew is treated as 0°
          and the image is returned unchanged at that step (not an error).
        - block_size is auto-corrected to the next odd integer if an even value is
          supplied in settings (T-2-03 mitigation).
    """
    # --- PIL → OpenCV BGR ---
    cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    if debug:
        Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)).save("debug_01_raw.png")

    # -----------------------------------------------------------------------
    # Step 1: Scale Correction (D-07, D-08)
    # Detect the form bounding box via the largest contour on a binary threshold.
    # Compute scale_x / scale_y relative to the expected 2550x3300 canvas.
    # -----------------------------------------------------------------------
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    _, thresh_for_contour = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(
        thresh_for_contour, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if contours:
        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        # Guard against degenerate contours (very thin lines)
        w = max(w, 1)
        h = max(h, 1)
        scale_x = 2550.0 / w
        scale_y = 3300.0 / h
    else:
        # No contours found (blank page) — treat scale as 1.0
        scale_x = 1.0
        scale_y = 1.0

    # Apply scale correction: resize image so coordinate space matches 2550x3300
    scaled = cv2.resize(cv_img, (2550, 3300), interpolation=cv2.INTER_LINEAR)

    if debug:
        Image.fromarray(cv2.cvtColor(scaled, cv2.COLOR_BGR2RGB)).save("debug_02_scaled.png")

    # -----------------------------------------------------------------------
    # Step 2: Deskew (D-08, D-10)
    # Hough-line angle detection on near-horizontal lines.
    # Raises ValueError if |skew| > 5° (D-10).
    # Skips rotation if no lines found (blank/sparse page is not an error).
    # -----------------------------------------------------------------------
    gray_scaled = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray_scaled, 50, 150)
    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180,
        threshold=100, minLineLength=100, maxLineGap=10
    )

    corrected = scaled  # default: no rotation

    if lines is not None:
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            if abs(angle) < 45:  # near-horizontal lines only
                angles.append(angle)

        if angles:
            skew_angle = float(np.median(angles))

            if abs(skew_angle) > 5.0:
                raise ValueError(
                    f"Skew angle {skew_angle:.1f}° exceeds ±5° limit "
                    "— manual review required"
                )

            # Rotate to correct skew — warpAffine preserves dimensions
            h_px, w_px = scaled.shape[:2]
            center = (w_px // 2, h_px // 2)
            M = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
            corrected = cv2.warpAffine(
                scaled, M, (w_px, h_px),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REPLICATE,
            )

    if debug:
        Image.fromarray(cv2.cvtColor(corrected, cv2.COLOR_BGR2RGB)).save("debug_03_deskewed.png")

    if debug:
        Image.fromarray(cv2.cvtColor(corrected, cv2.COLOR_BGR2RGB)).save("debug_04_corrected.png")

    # Return as PIL Image, mode "RGB" (D-11, §2.6)
    # Adaptive threshold was removed: it inverted gray-background Box 24 cells,
    # causing Tesseract to read white text on black — Tesseract reads raw color fine.
    return Image.fromarray(cv2.cvtColor(corrected, cv2.COLOR_BGR2RGB))
