"""Image preparation: crop, downscale, encode.

Every byte that lands in an artefact passes through here, so the size
budgets in the spec are enforced in one place.
"""
import base64
import io
import os

import fitz
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_SRC = os.path.join(ROOT, "images", "lake-tree-avenue-logo.PNG")
RENDER_SRC = os.path.join(ROOT, "images", "lake-tree-avenue.jpg")
LAYOUT_SRC = os.path.join(ROOT, "REV.LAYOUT - 07-10-2026.pdf")
SITE_PLAN_SRC = os.path.join(ROOT, "images", "site-plan.png")

# The floor plans as issued: one sheet per floor per unit type, each
# showing an adjacent pair of townhouses. Ground floor first, the order a
# visitor walks the house in.
def _plan_src(name: str) -> str:
    return os.path.join(ROOT, "images", name)


PLAN_SHEET_SRCS = {
    "A": (("ground", _plan_src("plot-1-6-ground-floor-plan.png")),
          ("first", _plan_src("plot-1-6-first-floor-plan.png"))),
    "B": (("ground", _plan_src("plot-7-48-ground-floor-plan.png")),
          ("first", _plan_src("plot-7-48-first-floor-plan.png"))),
}

_WHITE = 247  # a channel value above this counts as blank paper

# The drawing sheet carries the site plan in its upper two thirds and a strip
# of floor plans and elevations below. The brochure shows those drawings in
# their own section, so the plot map crops to the site plan alone — fractions
# of the rendered page.
SITE_BOX = (0.020, 0.055, 0.980, 0.775)

# Generous catch boxes over the rendered layout page's bottom strip, which
# carries two floor-plan sets and the elevation pair. Each box only has to
# contain its drawing and none of its neighbour's; the exact frame comes from
# trimming blank paper afterwards, so a caption is never clipped.
# Neither unit type is cropped from this strip any more: both have their
# own full-resolution sheets, which is the only way the room dimensions
# printed inside them survive to the page. The elevation pair has no
# separate source, so it is still lifted from here.
PLAN_BOXES = {
    "elevation": (0.592, 0.765, 0.862, 0.920),
}


def _encode(img: Image.Image, fmt: str, **kw) -> bytes:
    buf = io.BytesIO()
    img.save(buf, fmt, **kw)
    return buf.getvalue()


def _trim_white(img: Image.Image) -> Image.Image:
    """Drop blank rows and columns from the edges."""
    px = img.convert("RGB")
    w, h = px.size

    def row_blank(y):
        return all(min(px.getpixel((x, y))) > _WHITE for x in range(0, w, 8))

    def col_blank(x):
        return all(min(px.getpixel((x, y))) > _WHITE for y in range(0, h, 8))

    top = 0
    while top < h - 1 and row_blank(top):
        top += 1
    bottom = h - 1
    while bottom > top and row_blank(bottom):
        bottom -= 1
    left = 0
    while left < w - 1 and col_blank(left):
        left += 1
    right = w - 1
    while right > left and col_blank(right):
        right -= 1
    return img.crop((left, top, right + 1, bottom + 1))


def logo_png(height: int = 420) -> bytes:
    """Trimmed logo on a transparent ground.

    The source art is drawn on white. Both artefacts place the logo on sand,
    where a white plate would read as a pasted sticker, so near-white pixels
    become transparent and the artwork keeps its own edges.
    """
    img = Image.open(LOGO_SRC).convert("RGB")
    img = _trim_white(img)
    ratio = height / img.height
    img = img.resize((max(1, round(img.width * ratio)), height), Image.LANCZOS)

    rgba = img.convert("RGBA")
    px = rgba.load()
    w, h = rgba.size
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            lightest = max(r, g, b)
            if lightest > _WHITE:
                px[x, y] = (r, g, b, 0)
            elif lightest > 215:
                # feather the antialiased rim instead of leaving a hard edge
                px[x, y] = (r, g, b, round(255 * (_WHITE - lightest) / 32))
    return _encode(rgba, "PNG", optimize=True)


def render_jpeg(width: int = 1600, quality: int = 78) -> bytes:
    img = Image.open(RENDER_SRC).convert("RGB")
    img = _trim_white(img)
    ratio = width / img.width
    img = img.resize((width, max(1, round(img.height * ratio))), Image.LANCZOS)
    return _encode(img, "JPEG", quality=quality, optimize=True, progressive=True)


def _layout_pixmap(width: int) -> Image.Image:
    """Render the layout page as a reader sees it, rotation applied."""
    page = fitz.open(LAYOUT_SRC)[0]
    zoom = width / page.rect.width
    pm = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    return Image.frombytes("RGB", (pm.width, pm.height), pm.samples)


def layout_png(width: int = 1600, box=None) -> bytes:
    """Render the layout page, optionally cropped to `box` (page fractions)."""
    img = _layout_pixmap(width if box is None else round(width / (box[2] - box[0])))
    if box is not None:
        w, h = img.size
        img = img.crop((round(box[0] * w), round(box[1] * h),
                        round(box[2] * w), round(box[3] * h)))
    return _encode(img, "PNG", optimize=True)


def site_plan_jpeg(width: int = 1500, quality: int = 82) -> bytes:
    """The coloured layout plan, as drawn by the architect.

    This is its own rendering rather than a crop of the drawing sheet, so it
    arrives already framed and needs no trimming — only a downscale to the
    width the page shows it at.
    """
    img = Image.open(SITE_PLAN_SRC).convert("RGB")
    ratio = width / img.width
    img = img.resize((width, max(1, round(img.height * ratio))), Image.LANCZOS)
    return _encode(img, "JPEG", quality=quality, optimize=True, progressive=True)


def plan_sheets(unit_key: str, quality: int = 92) -> dict[str, bytes]:
    """One unit type's floor plans, ground floor first.

    These are kept at the resolution they arrived at. The sources run
    1050-1350 px across, and the figures that matter to a buyer -- 9'-9" x
    9'-1", 4'-6" x 5'-0" -- are a few pixels tall inside them, so there is
    nothing to spend on a downscale and everything to lose. Quality is set well
    above the photographic images for the same reason: the drawings are
    fine dark text over pale floor tiles, which is what JPEG smears first.
    """
    out = {}
    for key, src in PLAN_SHEET_SRCS[unit_key]:
        img = _trim_white(Image.open(src).convert("RGB"))
        out[key] = _encode(img, "JPEG", quality=quality, optimize=True,
                           progressive=True)
    return out


def plan_crops(width: int = 7200, quality: int = 90) -> dict[str, bytes]:
    """Drawings lifted off the layout sheet, at a width you can read them at.

    `width` is the whole layout page; each crop keeps about a fifth of it.
    The page is vector, so rendering it larger recovers real detail rather
    than inventing it, and these crops carry room dimensions set in type a
    couple of millimetres tall. At the old 2400 the Type B plan reached the
    brochure 514 px wide and those figures were a smudge.
    """
    full = _layout_pixmap(width)
    w, h = full.size
    out = {}
    for key, (x0, y0, x1, y1) in PLAN_BOXES.items():
        box = (round(x0 * w), round(y0 * h), round(x1 * w), round(y1 * h))
        out[key] = _encode(_trim_white(full.crop(box)), "JPEG",
                           quality=quality, optimize=True)
    return out


def data_uri(blob: bytes, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(blob).decode("ascii")
