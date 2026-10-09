"""Plot number -> hotspot rectangle, normalised to the layout page.

The same table drives the HTML SVG overlay and the PDF link annotations.
"""
import os
import re
from dataclasses import dataclass

import fitz

LAYOUT_PDF = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "REV.LAYOUT - 07-10-2026.pdf",
)

# Plot labels are drawn at ~29 x 26 pt. Dimension callouts are ~7 x 5 pt,
# so a height floor of 15 pt separates them cleanly.
_LABEL_MIN_HEIGHT = 15.0

# Plots 07-13 and 42 are outlined vector art with no text layer. Centres read
# off a render of the page, in PDF points (page is 1684 x 2384 pt).
MANUAL_CENTRES = {
    7: (610.0, 1228.0),
    8: (705.0, 1228.0),
    9: (792.0, 1228.0),
    10: (878.0, 1228.0),
    11: (963.0, 1228.0),
    12: (1247.0, 1228.0),
    13: (1333.0, 1228.0),
    42: (846.0, 405.0),
}

# Hotspot box drawn around a label centre, in PDF points.
# Plots 01-06 are a vertical column of wide, short cells; the rest are rows of
# narrow, tall cells.
# The drawing sheet carries the site plan in its upper two thirds and a strip
# of floor plans and elevations below. The brochure shows those drawings in
# their own section, so the plot map crops to the site plan alone — fractions
# of the rendered page.
SITE_BOX = (0.020, 0.055, 0.980, 0.775)

_COLUMN_PLOTS = range(1, 7)
_COLUMN_BOX = (118.0, 82.0)   # w, h
_ROW_BOX = (84.0, 150.0)      # w, h


@dataclass(frozen=True)
class Hotspot:
    number: int
    x: float
    y: float
    w: float
    h: float
    unit_type: str


def extract_label_centres(pdf_path: str) -> dict[int, tuple[float, float]]:
    """Plot number -> label centre, in *rendered* page coordinates.

    The drawing carries /Rotate 180: text extraction reports unrotated
    coordinates while get_pixmap renders the rotated page, so every centre is
    mapped through the page's rotation matrix to match what a reader sees.
    """
    page = fitz.open(pdf_path)[0]
    rotate = page.rotation_matrix
    centres: dict[int, tuple[float, float]] = {}
    for x0, y0, x1, y1, text, *_ in page.get_text("words"):
        if not re.fullmatch(r"\d{2}", text):
            continue
        if (y1 - y0) < _LABEL_MIN_HEIGHT:
            continue
        number = int(text)
        if 1 <= number <= 48:
            centre = fitz.Point((x0 + x1) / 2, (y0 + y1) / 2) * rotate
            centres[number] = (centre.x, centre.y)
    return centres


def hotspots(box: tuple[float, float, float, float] | None = None
             ) -> tuple[Hotspot, ...]:
    """Hotspots normalised to the page, or to `box` within it.

    `box` is (x0, y0, x1, y1) in page fractions — pass the same crop used for
    the image so overlay and raster share a frame.
    """
    page = fitz.open(LAYOUT_PDF)[0]
    pw, ph = page.rect.width, page.rect.height

    centres = extract_label_centres(LAYOUT_PDF)
    centres.update(MANUAL_CENTRES)

    out = []
    for number in range(1, 49):
        cx, cy = centres[number]
        bw, bh = _COLUMN_BOX if number in _COLUMN_PLOTS else _ROW_BOX
        x = max(0.0, (cx - bw / 2) / pw)
        y = max(0.0, (cy - bh / 2) / ph)
        w = min(bw / pw, 1.0 - x)
        h = min(bh / ph, 1.0 - y)
        if box is not None:
            bx0, by0, bx1, by1 = box
            sx, sy = bx1 - bx0, by1 - by0
            x, y, w, h = (x - bx0) / sx, (y - by0) / sy, w / sx, h / sy
        out.append(Hotspot(
            number=number,
            x=x,
            y=y,
            w=w,
            h=h,
            unit_type="A" if number in _COLUMN_PLOTS else "B",
        ))
    return tuple(out)
