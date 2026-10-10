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
LOGO_SRC = os.path.join(ROOT, "images", "Lake Tree Avenue new-Logo.png")
RENDER_SRC = os.path.join(ROOT, "images",
                          "lake-tree-avenue-street-view-hero-image.png")
LAYOUT_SRC = os.path.join(ROOT, "REV.LAYOUT - 07-10-2026.pdf")
SITE_PLAN_SRC = os.path.join(ROOT, "images",
                             "lake-tree-avenue-Layout Plan.png")
KEY_PLAN_SRC = os.path.join(ROOT, "images",
                            "Lake Tree Avenue Key Plan.png")

# The floor plans as issued: one portrait sheet per floor per unit type,
# each showing a single townhouse. Ground floor first, the order a visitor
# walks the house in.
def _plan_src(name: str) -> str:
    return os.path.join(ROOT, "images", name)


PLAN_SHEET_SRCS = {
    "A": (("ground", _plan_src("plot 1-06-ground Floor Plan.png")),
          ("first", _plan_src("plot 1-06-First Floor Plan.png"))),
    "B": (("ground", _plan_src("plot 7-48-Ground Floor Plan.png")),
          ("first", _plan_src("plot 7-48-First Floor Plan.png"))),
}

_WHITE = 247  # a channel value above this counts as blank paper

# The hero runs full width above a band of sand deep enough for the
# project name and the credit line. Shallower than this and the PDF
# cover has nowhere to set them.
RENDER_ASPECT = 1.8

# The drawing sheet carries the site plan in its upper two thirds and a strip
# of floor plans below. The brochure shows the floor plans from their own
# issued sheets, so the plot map crops to the site plan alone — fractions
# of the rendered page.
SITE_BOX = (0.020, 0.055, 0.980, 0.775)

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

    The source art already carries its own alpha, so the ground is kept as
    drawn: both artefacts place the logo on sand, where a white plate would
    read as a pasted sticker, and keying out near-white would eat the light
    strokes inside the leaves.
    """
    img = Image.open(LOGO_SRC).convert("RGBA")
    box = img.getchannel("A").getbbox()
    if box is not None:
        img = img.crop(box)
    ratio = height / img.height
    img = img.resize((max(1, round(img.width * ratio)), height), Image.LANCZOS)
    return _encode(img, "PNG", optimize=True)


def render_jpeg(width: int = 1600, quality: int = 78) -> bytes:
    """The street view, cropped to the band both artefacts are built for.

    The source render is squarer than the band the cover leaves it: shown
    whole it would push the PDF title off the page. Sky is the least told
    part of the picture, so the crop comes off the top and the mark in the
    lower corner is kept.
    """
    img = Image.open(RENDER_SRC).convert("RGB")
    img = _trim_white(img)
    keep = min(img.height, round(img.width / RENDER_ASPECT))
    img = img.crop((0, img.height - keep, img.width, img.height))
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


def key_plan_jpeg(width: int = 1672, quality: int = 85) -> bytes:
    """The landmark key plan: what stands either side of the gate, and how far.

    Unlike the site plan this is finished artwork rather than a drawing --
    it carries its own logo, its own "NOT TO SCALE" note and a photographic
    sky behind the pins, so it is placed whole and never trimmed. It is
    drawn 16:9 and bleeds to its own edges, which is why both artefacts run
    it edge to edge: its labels are sized relative to its width, so page
    width is legibility. The default is the source's own width -- there is
    no detail to gain by upscaling and none to spare by shrinking.

    Its labels are English in all three documents. Repainting a raster of
    someone else's artwork per language is not something a build should do,
    so the translation lives in the accessible name instead, which is also
    the only form a screen reader or a search engine ever sees.
    """
    img = Image.open(KEY_PLAN_SRC).convert("RGB")
    ratio = width / img.width
    img = img.resize((width, max(1, round(img.height * ratio))), Image.LANCZOS)
    return _encode(img, "JPEG", quality=quality, optimize=True,
                   progressive=True)


def plan_sheets(unit_key: str, quality: int = 92) -> dict[str, bytes]:
    """One unit type's floor plans, ground floor first.

    These are kept at the resolution they arrived at. The sources run
    940-1030 px across, and the figures that matter to a buyer -- 9'-9" x
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


def dimensions(blob: bytes) -> tuple[int, int]:
    """The pixel size of an encoded image.

    The HTML shows its pictures as CSS backgrounds so that the bytes are
    embedded once rather than once per language. A background box has no
    intrinsic size, so each one is given the aspect ratio its picture
    actually has -- otherwise the page reflows as the images paint.
    """
    with Image.open(io.BytesIO(blob)) as img:
        return img.size


def data_uri(blob: bytes, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(blob).decode("ascii")
