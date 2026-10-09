"""Interactive A4-landscape PDF brochure.

Every page carries the contact details twice over: as live link annotations
and as readable text, because WhatsApp's in-app viewer frequently renders a
PDF without its annotations and a recipient must still be able to dial the
number by hand.

Only base-14 fonts are used, so nothing has to be embedded and the file opens
identically everywhere.
"""
import io
import os

import fitz
from PIL import Image

from build import assets, content

class LayoutOverflow(RuntimeError):
    """Copy did not fit its box.

    insert_textbox writes only what fits and returns a negative value. Left
    unchecked that drops the tail of a sentence from the brochure silently,
    so the build fails loudly instead.
    """


PAGE_SIZE = (842.0, 595.0)

# The brochure's own date, not the moment of the build.
BUILD_DATE = "D:20261009000000+05'30'"

MARGIN = 54.0
FOOTER_TOP = 543.0

SERIF = "tiro"
SERIF_BOLD = "tibo"
SANS = "helv"
SANS_BOLD = "hebo"

INK = (0.200, 0.157, 0.122)
INK_SOFT = (0.420, 0.361, 0.298)
TERRA = (0.710, 0.475, 0.247)
TERRA_DEEP = (0.561, 0.353, 0.165)
SAGE = (0.467, 0.541, 0.322)
RULE = (0.847, 0.800, 0.722)
SAND = (0.953, 0.918, 0.859)
PAPER = (1.0, 1.0, 1.0)


# Base-14 fonts cannot encode these; PyMuPDF silently substitutes "?".
_SUBSTITUTIONS = {"\u2013": "-", "\u2014": "-", "\u2022": "-", "\u00b7": "-",
                  "\u2026": "...", "\u20b9": "Rs"}


def _plain(text: str) -> str:
    for bad, good in _SUBSTITUTIONS.items():
        text = text.replace(bad, good)
    return text


def _fill(page, rect, color):
    page.draw_rect(rect, color=None, fill=color)


def _line(page, x0, y, x1, color=RULE, width=0.7):
    page.draw_line(fitz.Point(x0, y), fitz.Point(x1, y), color=color, width=width)


def _text(page, rect, text, *, font=SERIF, size=11, color=INK, align=0,
          leading=None):
    return page.insert_textbox(
        rect, _plain(text), fontname=font, fontsize=size, color=color,
        align=align, lineheight=leading,
    )


def _crop_to_aspect(blob: bytes, aspect: float) -> bytes:
    """Centre-crop an encoded image to width/height == aspect."""
    img = Image.open(io.BytesIO(blob)).convert("RGB")
    w, h = img.size
    if w / h > aspect:
        new_w = round(h * aspect)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        new_h = round(w / aspect)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=82, optimize=True)
    return buf.getvalue()


def _place_image(page, blob, box, *, pad=0.0, frame=False):
    """Fit an image inside `box` at its own aspect and return the rect used."""
    img = Image.open(io.BytesIO(blob))
    avail = box + (pad, pad, -pad, -pad)
    aspect = img.width / img.height
    w, h = avail.width, avail.height
    if w / h > aspect:
        w = h * aspect
    else:
        h = w / aspect
    x0 = avail.x0 + (avail.width - w) / 2
    y0 = avail.y0 + (avail.height - h) / 2
    rect = fitz.Rect(x0, y0, x0 + w, y0 + h)
    if frame:
        plate = rect + (-pad, -pad, pad, pad)
        _fill(page, plate, PAPER)
        page.draw_rect(plate, color=RULE, width=0.7)
    page.insert_image(rect, stream=blob)
    return rect


def _footer(page):
    """Readable contact strip plus the four live links, on every page."""
    p = content.PROJECT
    _line(page, MARGIN, FOOTER_TOP, PAGE_SIZE[0] - MARGIN)

    width = (PAGE_SIZE[0] - 2 * MARGIN) / 4.0
    cells = (
        (f"Call {p['phone_display']}", content.tel_link()),
        (f"WhatsApp {p['phone_display']}",
         content.wa_link("Hi, I'd like to know more about Lake Tree Avenue.")),
        (p["email"], content.mail_link()),
        ("Open in Google Maps", p["maps_url"]),
    )
    for i, (label, uri) in enumerate(cells):
        rect = fitz.Rect(MARGIN + i * width, FOOTER_TOP + 8,
                         MARGIN + (i + 1) * width - 8, FOOTER_TOP + 30)
        _text(page, rect, label, font=SANS, size=8.5, color=TERRA_DEEP)
        page.insert_link({"kind": fitz.LINK_URI, "from": rect, "uri": uri})


def _heading(page, title, lead, *, y=MARGIN, width=430.0):
    rect = fitz.Rect(MARGIN, y, MARGIN + width, y + 70)
    _text(page, rect, title, font=SERIF, size=25, color=INK)
    if lead:
        lead_rect = fitz.Rect(MARGIN, y + 40, MARGIN + width, y + 76)
        _text(page, lead_rect, lead, font=SERIF, size=11.5, color=INK_SOFT)
    return y + (78 if lead else 52)


def _schedule(page, rows, x, y, width, *, label_w=150.0, size=9.5, pitch=26.0):
    """Hairline-ruled fact table, the drawing sheet's own way of listing.

    Raises if the table would run into the footer: a schedule that silently
    outgrows its page drops its last rows, and on the plans page that is the
    plot size.
    """
    end = y + pitch * len(rows)
    if end > FOOTER_TOP - 6:
        raise LayoutOverflow(
            f"schedule of {len(rows)} rows ends at {end:.0f} pt, past the "
            f"footer at {FOOTER_TOP:.0f} pt")
    for key, value in rows:
        _line(page, x, y, x + width)
        _text(page, fitz.Rect(x, y + 5, x + label_w, y + 5 + pitch), key,
              font=SANS, size=size, color=INK_SOFT)
        _text(page, fitz.Rect(x + label_w, y + 5, x + width, y + 9 + pitch),
              value, font=SERIF, size=size + 0.5, color=INK)
        y += pitch
    _line(page, x, y, x + width)
    return y


def _page(doc):
    return doc.new_page(width=PAGE_SIZE[0], height=PAGE_SIZE[1])


# --------------------------------------------------------------------------
# pages
# --------------------------------------------------------------------------

def _cover(doc, art):
    """The render across the full page width, titling on the sand below.

    The render is shown whole rather than cropped to a fixed band: it carries
    the logo in its own top corner, and a crop deep enough to fill a taller
    band would cut the mark off. Its height therefore sets where the sand
    starts, and the band is sized to whatever is left above the footer.
    """
    page = _page(doc)
    render = Image.open(io.BytesIO(art["render"]))
    band_top = round(PAGE_SIZE[0] * render.height / render.width, 2)
    page.insert_image(fitz.Rect(0, 0, PAGE_SIZE[0], band_top),
                      stream=art["render"])
    _fill(page, fitz.Rect(0, band_top, PAGE_SIZE[0], PAGE_SIZE[1]), SAND)

    # The band is only as deep as the render leaves it, so both lines are
    # checked: insert_textbox drops what does not fit and says so only in
    # its return value.
    lines = (
        (fitz.Rect(MARGIN, band_top + 8, 700, band_top + 42),
         content.PROJECT["name"], SERIF, 20, INK),
        (fitz.Rect(MARGIN + 1, band_top + 44, 700, band_top + 70),
         f"{content.CREDIT}   /   Waghodia Main Road, Vadodara",
         SANS, 10, INK_SOFT),
    )
    for rect, text, font, size, color in lines:
        if _text(page, rect, text, font=font, size=size, color=color) < 0:
            raise LayoutOverflow(
                f"cover line {text!r} does not fit the {rect.height:.0f} pt "
                f"band under a render {band_top:.0f} pt deep")
    _footer(page)
    return page


def _project(doc, art):
    page = _page(doc)
    s = art["sections"]["project"]
    # text-only pages sit optically centred rather than pinned to the top
    y = _heading(page, s["title"], s["lead"], y=132.0)
    body = "\n\n".join(s["body"])
    _text(page, fitz.Rect(MARGIN, y, MARGIN + 350, FOOTER_TOP - 20), body,
          font=SERIF, size=10.5, color=INK, leading=1.45)
    _schedule(page, (
        ("Homes", "48 townhouses, two bedrooms each"),
        ("Plan types", "Type A, plots 01-06   /   Type B, plots 07-48"),
        ("Approach road", "12.00 m town planning road"),
        ("Internal roads", "7.50 m, paved both sides"),
        ("Levels", "Ground, first and private terrace"),
        ("Parking", "On plot, plus open-space parking"),
    ), 440.0, y, PAGE_SIZE[0] - MARGIN - 440.0, label_w=120.0)
    _footer(page)
    return page


def _elevation(doc, art):
    page = _page(doc)
    s = art["sections"]["render"]
    _fill(page, fitz.Rect(0, 0, PAGE_SIZE[0], PAGE_SIZE[1]), SAND)
    y = _heading(page, s["title"], s["lead"])
    box = fitz.Rect(MARGIN, y + 6, PAGE_SIZE[0] - MARGIN, FOOTER_TOP - 40)
    placed = _place_image(page, art["elevation"], box, pad=16, frame=True)
    _text(page, fitz.Rect(placed.x0, FOOTER_TOP - 34, placed.x1, FOOTER_TOP - 4),
          s["body"][0], font=SANS, size=8.5, color=INK_SOFT)
    _footer(page)
    return page


def _plans(doc, art):
    page = _page(doc)
    s = art["sections"]["plans"]
    y = _heading(page, s["title"], s["lead"])
    half = (PAGE_SIZE[0] - 2 * MARGIN - 30) / 2
    for i, key in enumerate(("A", "B")):
        unit = content.UNIT_TYPES[key]
        x = MARGIN + i * (half + 30)
        _text(page, fitz.Rect(x, y, x + half, y + 20),
              f"{unit['label']}, {unit['plots'].lower()}",
              font=SANS_BOLD, size=9.5, color=TERRA_DEEP)
        placed = _place_image(page, art["crop_" + key],
                              fitz.Rect(x, y + 18, x + half, y + 162),
                              pad=9, frame=True)
        _schedule(page, unit["rooms"], x, placed.y1 + 22, half,
                  label_w=124.0, size=8.5, pitch=20.0)
    _footer(page)
    return page


def _layout(doc, art):
    page = _page(doc)
    s = art["sections"]["layout"]
    _fill(page, fitz.Rect(0, 0, PAGE_SIZE[0], PAGE_SIZE[1]), SAND)

    img = Image.open(io.BytesIO(art["site"]))
    avail_h = FOOTER_TOP - MARGIN - 16
    img_w = avail_h * img.width / img.height
    img_rect = fitz.Rect(MARGIN, MARGIN, MARGIN + img_w, MARGIN + avail_h)
    _fill(page, img_rect + (-8, -8, 8, 8), PAPER)
    page.draw_rect(img_rect + (-8, -8, 8, 8), color=RULE, width=0.7)
    page.insert_image(img_rect, stream=art["site"])

    tx = img_rect.x1 + 34
    tw = PAGE_SIZE[0] - MARGIN - tx
    _text(page, fitz.Rect(tx, MARGIN, tx + tw, MARGIN + 60), s["title"],
          font=SERIF, size=23, color=INK)
    _text(page, fitz.Rect(tx, MARGIN + 62, tx + tw, MARGIN + 140),
          s["lead"] + "\n\n" + s["body"][0], font=SERIF, size=10.5,
          color=INK_SOFT, leading=1.4)
    _line(page, tx, MARGIN + 180, tx + tw)
    _text(page, fitz.Rect(tx, MARGIN + 188, tx + tw, MARGIN + 290),
          "Type A\nPlots 01-06\n\nType B\nPlots 07-48\n\n"
          "Ask us which plots are still open.",
          font=SANS, size=9, color=INK_SOFT, leading=1.5)
    _footer(page)
    return page


def _specs(doc, art):
    page = _page(doc)
    s = art["sections"]["specs"]
    y = _heading(page, s["title"], s["lead"])
    col_w = (PAGE_SIZE[0] - 2 * MARGIN - 34) / 2
    groups = content.SPEC_GROUPS
    half = (len(groups) + 1) // 2
    for col, chunk in enumerate((groups[:half], groups[half:])):
        x = MARGIN + col * (col_w + 34)
        cy = y
        for label, text in chunk:
            _line(page, x, cy, x + col_w)
            _text(page, fitz.Rect(x, cy + 5, x + col_w, cy + 20), label,
                  font=SANS_BOLD, size=8.5, color=TERRA_DEEP)
            body_box = fitz.Rect(x, cy + 18, x + col_w, cy + 18 + 56)
            # insert_textbox returns the unused height, so this is the exact
            # space the wrapped text took. A negative value means it did not
            # fit and part of the sentence was dropped.
            remaining = _text(page, body_box, text, font=SERIF, size=9.5,
                              color=INK, leading=1.3)
            if remaining < 0:
                raise LayoutOverflow(
                    f"specification {label!r} does not fit its box "
                    f"(short by {abs(remaining):.1f} pt)")
            cy += 18 + (56 - remaining) + 10
    _fill(page, fitz.Rect(0, 432, PAGE_SIZE[0], FOOTER_TOP - 10), SAND)
    _text(page, fitz.Rect(MARGIN, 444, MARGIN + 300, 466), "Across the campus",
          font=SANS_BOLD, size=9, color=INK_SOFT)
    amen = content.AMENITIES
    third = (len(amen) + 2) // 3
    for col in range(3):
        chunk = amen[col * third:(col + 1) * third]
        x = MARGIN + col * ((PAGE_SIZE[0] - 2 * MARGIN) / 3)
        _text(page, fitz.Rect(x, 466, x + (PAGE_SIZE[0] - 2 * MARGIN) / 3 - 20,
                              FOOTER_TOP - 14),
              "\n".join(chunk), font=SERIF, size=9, color=INK, leading=1.45)
    _footer(page)
    return page


def _location(doc, art):
    page = _page(doc)
    s = art["sections"]["location"]
    p = content.PROJECT
    y = _heading(page, s["title"], s["lead"], y=132.0)
    _text(page, fitz.Rect(MARGIN, y, MARGIN + 340, y + 150),
          "\n\n".join(s["body"]) + "\n\n" + p["site_address"],
          font=SERIF, size=11, color=INK, leading=1.45)
    _schedule(page, content.LOCATION_ROWS, 440.0, y,
              PAGE_SIZE[0] - MARGIN - 440.0, label_w=96.0)
    rect = fitz.Rect(MARGIN, y + 150, MARGIN + 190, y + 178)
    page.draw_rect(rect, color=TERRA, width=1.2)
    _text(page, rect + (12, 8, 0, 0), "Open in Google Maps", font=SANS_BOLD,
          size=9.5, color=TERRA_DEEP)
    page.insert_link({"kind": fitz.LINK_URI, "from": rect, "uri": p["maps_url"]})
    _footer(page)
    return page


def _contact(doc, art):
    page = _page(doc)
    s = art["sections"]["contact"]
    p = content.PROJECT
    _fill(page, fitz.Rect(0, 0, PAGE_SIZE[0], PAGE_SIZE[1]), SAND)
    y = _heading(page, s["title"], s["lead"])
    _text(page, fitz.Rect(MARGIN, y, MARGIN + 330, y + 70), s["body"][0],
          font=SERIF, size=11, color=INK, leading=1.45)

    col_w = (PAGE_SIZE[0] - 2 * MARGIN) / 3 - 20
    blocks = (
        ("Call or message", f"{p['phone_display']}\n{p['email']}"),
        ("Site", p["site_address"]),
        ("Developer", f"{content.CREDIT}\n{p['regd_office']}"),
    )
    by = y + 96
    for i, (head, text) in enumerate(blocks):
        x = MARGIN + i * ((PAGE_SIZE[0] - 2 * MARGIN) / 3)
        _line(page, x, by, x + col_w)
        _text(page, fitz.Rect(x, by + 7, x + col_w, by + 24), head,
              font=SANS_BOLD, size=8.5, color=INK_SOFT)
        _text(page, fitz.Rect(x, by + 24, x + col_w, by + 110), text,
              font=SERIF, size=10.5, color=INK, leading=1.4)

    _place_image(page, art["logo"],
                 fitz.Rect(MARGIN, FOOTER_TOP - 96, MARGIN + 116,
                           FOOTER_TOP - 18))
    _footer(page)
    return page


def build_doc() -> fitz.Document:
    crops = assets.plan_crops()
    art = {
        "logo": assets.logo_png(420),
        "render": assets.render_jpeg(1800),
        "site": assets.site_plan_jpeg(1500),
        "crop_A": crops["A"],
        "crop_B": crops["B"],
        "elevation": crops["elevation"],
        "sections": {s["id"]: s for s in content.SECTIONS},
    }
    doc = fitz.open()
    for builder in (_cover, _project, _elevation, _plans, _layout, _specs,
                    _location, _contact):
        builder(doc, art)
    doc.set_metadata({
        "title": content.PROJECT["name"],
        "author": content.PROJECT["developer"],
        "subject": "48 two-bedroom townhouses, Waghodia Main Road, Vadodara",
        # Fixed dates keep successive builds byte-identical, so a rebuild
        # does not rewrite dist/ and dirty the working tree.
        "creationDate": BUILD_DATE,
        "modDate": BUILD_DATE,
    })
    return doc


def write(path: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    doc = build_doc()
    doc.save(path, deflate=True, garbage=4, no_new_id=True)
    doc.close()
    return path
