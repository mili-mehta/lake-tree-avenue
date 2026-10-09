"""Interactive A4-landscape PDF brochure.

Every page carries the contact details twice over: as live link annotations
and as readable text, because WhatsApp's in-app viewer frequently renders a
PDF without its annotations and a recipient must still be able to dial the
number by hand.

Only base-14 fonts are used, so nothing has to be embedded and the file opens
identically everywhere.
"""
import contextlib
import html
import io
import os
import re

import fitz
from PIL import Image

from build import assets, content, copy, fonts

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


# MuPDF resolves the @font-face urls in _FACE_CSS against this archive.
_ARCHIVE = fitz.Archive(fonts.ttf_archive_dir())


def _fill(page, rect, color):
    page.draw_rect(rect, color=None, fill=color)


def _line(page, x0, y, x1, color=RULE, width=0.7):
    page.draw_line(fitz.Point(x0, y), fitz.Point(x1, y), color=color, width=width)


# Which locale the page builders are drawing for. A module-level handle
# rather than an argument on all forty _text() calls: the build is one
# document at a time, start to finish, and `_using` makes the scope of
# the setting visible at the one place it changes.
_LOCALE = "en"


@contextlib.contextmanager
def _using(locale: str):
    global _LOCALE
    before, _LOCALE = _LOCALE, locale
    try:
        yield
    finally:
        _LOCALE = before


_ROLE = {SERIF: ("serif", 400), SERIF_BOLD: ("serif", 700),
         SANS: ("sans", 400), SANS_BOLD: ("sans", 700)}

_ALIGN = {0: "left", 1: "center", 2: "right", 3: "justify"}


def _css(font, size, color, align, leading) -> str:
    role, weight = _ROLE[font]
    r, g, b = (round(c * 255) for c in color)
    line = f" line-height: {leading};" if leading else ""
    # The faces have to be declared, not merely named: MuPDF ships its own
    # Noto fallbacks and will quietly use those instead, which leaves the
    # sans asking for Devanagari and being handed the serif.
    return (fonts.pdf_face_css(_LOCALE)
            + "\n* { font-family: " + fonts.pdf_stack(_LOCALE, role) + ";"
            f" font-size: {size}px; font-weight: {weight};"
            f" color: rgb({r},{g},{b}); text-align: {_ALIGN[align]};"
            f"{line} margin: 0; }}"
            + ("" if _LOCALE == "en" else
               f"\n.lat {{ font-family: {'serif' if role == 'serif' else 'sans-serif'}; }}"))


# Devanagari and Gujarati, the two blocks whose runs belong to the Indic
# face. Everything else -- Latin, digits, 17'-5", the half sign, the
# brand -- belongs to the Latin one.
_INDIC = re.compile(r"[\u0900-\u097F\u0A80-\u0AFF]")


def _runs(text: str):
    """Split text into (is_indic, run) pieces.

    Without this the measurements are at the mercy of MuPDF's fallback
    search, which keeps using the Indic face for whatever follows an
    Indic word. None of the four Noto Indic faces carries U+00BD, so
    17'-5" to 24'-7½" came out with a tofu box where the half sign
    belongs -- but only when a Gujarati word preceded it on the line.
    Marking the runs removes the guesswork, and it is better typography
    besides: a dimension should set in the same Latin serif in all three
    languages, because that is how the drawing beside it is lettered.
    """
    runs, current, kind = [], [], None
    for ch in text:
        this = bool(_INDIC.match(ch))
        if kind is None or this == kind:
            current.append(ch)
        else:
            runs.append((kind, "".join(current)))
            current = [ch]
        kind = this
    if current:
        runs.append((bool(kind), "".join(current)))
    return runs


def _body(text: str) -> str:
    """One box of copy as HTML, with the Latin runs marked."""
    lines = []
    for line in _plain(text).split("\n"):
        if _LOCALE == "en":
            lines.append(html.escape(line))
            continue
        lines.append("".join(
            html.escape(run) if indic
            else f'<span class="lat">{html.escape(run)}</span>'
            for indic, run in _runs(line)))
    return "<br>".join(lines)


def _text(page, rect, text, *, font=SERIF, size=11, color=INK, align=0,
          leading=None):
    """Draw text and report the vertical space left over.

    Drawn through insert_htmlbox rather than insert_textbox because that
    is the only one of the two that shapes: Devanagari conjuncts and the
    matra reordering that makes कि out of क + ि happen in MuPDF's
    HarfBuzz layer, which insert_textbox never reaches. English goes the
    same way so that one engine lays out all three languages and the
    pages cannot drift apart.

    Returns the unused height, negative when the copy did not fit, which
    is the contract insert_textbox had and the callers still check.
    """
    spare, _ = page.insert_htmlbox(
        rect, _body(text),
        css=_css(font, size, color, align, leading),
        archive=_ARCHIVE,
        scale_low=1,  # never shrink to fit: an overflow must stay visible
    )
    return spare


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


def _footer(page, words):
    """Readable contact strip plus the four live links, on every page."""
    p = content.PROJECT
    ui = words.UI
    _line(page, MARGIN, FOOTER_TOP, PAGE_SIZE[0] - MARGIN)

    width = (PAGE_SIZE[0] - 2 * MARGIN) / 4.0
    cells = (
        (ui["call"].format(phone=p["phone_display"]), content.tel_link()),
        (ui["whatsapp"].format(phone=p["phone_display"]),
         content.wa_link(words.WHATSAPP_MESSAGE)),
        (p["email"], content.mail_link()),
        (ui["directions_on_maps"], p["maps_url"]),
    )
    for i, (label, uri) in enumerate(cells):
        rect = fitz.Rect(MARGIN + i * width, FOOTER_TOP + 8,
                         MARGIN + (i + 1) * width - 8, FOOTER_TOP + 30)
        _text(page, rect, label, font=SANS, size=8.5, color=TERRA_DEEP)
        page.insert_link({"kind": fitz.LINK_URI, "from": rect, "uri": uri})


def _heading(page, title, lead, *, y=MARGIN, width=430.0):
    """Title, then the lead under whatever height the title actually took.

    The lead used to sit at a fixed offset, which held only while every
    title was one line. "Forty-eight homes on one quiet avenue" is two
    lines, and Gujarati sets longer than English besides, so the offset
    has to be measured rather than assumed -- otherwise the lead prints
    through the second line of the title.
    """
    box = fitz.Rect(MARGIN, y, MARGIN + width, y + 100)
    spare = _text(page, box, title, font=SERIF, size=25, color=INK)
    if spare < 0:
        raise LayoutOverflow(f"heading {title!r} does not fit its box")
    bottom = y + (box.height - spare)
    if not lead:
        return bottom + 12
    lead_box = fitz.Rect(MARGIN, bottom + 4, MARGIN + width, bottom + 62)
    lead_spare = _text(page, lead_box, lead, font=SERIF, size=11.5,
                       color=INK_SOFT)
    if lead_spare < 0:
        raise LayoutOverflow(f"lead {lead!r} does not fit under its title")
    return bottom + 4 + (lead_box.height - lead_spare) + 14


def _schedule(page, rows, x, y, width, *, label_w=150.0, size=9.5, pitch=26.0):
    """Hairline-ruled fact table, the drawing sheet's own way of listing.

    A row is `pitch` deep unless its value wraps, in which case the row
    grows to hold every line. Fixed-pitch rows were fine while every value
    was a single dimension; "17'-5" to 24'-7½" [5.31 m to 7.51 m]" takes
    two lines in a narrow column, and the second one used to be drawn
    across the rule and into the row below.

    Raises if the table would run into the footer: a schedule that silently
    outgrows its page drops its last rows, and on a plans page that is the
    plot size.
    """
    for key, value in rows:
        _line(page, x, y, x + width)
        _text(page, fitz.Rect(x, y + 5, x + label_w, y + 5 + pitch), key,
              font=SANS, size=size, color=INK_SOFT)
        # insert_textbox returns the space it did not use, so measuring the
        # wrap means giving it room to wrap into and subtracting.
        box = pitch * 4
        remaining = _text(
            page, fitz.Rect(x + label_w, y + 5, x + width, y + 5 + box),
            value, font=SERIF, size=size + 0.5, color=INK)
        if remaining < 0:
            raise LayoutOverflow(
                f"schedule value {value!r} for {key!r} does not fit a "
                f"{width - label_w:.0f} pt column (short by {abs(remaining):.1f} pt)")
        y += max(pitch, box - remaining + 9)
        if y > FOOTER_TOP - 6:
            raise LayoutOverflow(
                f"schedule row {key!r} ends at {y:.0f} pt, past the footer "
                f"at {FOOTER_TOP:.0f} pt")
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
         f"{art['words'].CREDIT}   /   {art['words'].UI['sheet_subtitle']}",
         SANS, 10, INK_SOFT),
    )
    for rect, text, font, size, color in lines:
        if _text(page, rect, text, font=font, size=size, color=color) < 0:
            raise LayoutOverflow(
                f"cover line {text!r} does not fit the {rect.height:.0f} pt "
                f"band under a render {band_top:.0f} pt deep")
    _footer(page, art["words"])
    return page


def _project(doc, art):
    page = _page(doc)
    s = art["sections"]["project"]
    # text-only pages sit optically centred rather than pinned to the top
    y = _heading(page, s["title"], s["lead"], y=132.0)
    body = "\n\n".join(s["body"])
    _text(page, fitz.Rect(MARGIN, y, MARGIN + 350, FOOTER_TOP - 20), body,
          font=SERIF, size=10.5, color=INK, leading=1.45)
    _schedule(page, art["words"].PROJECT_SCHEDULE,
              440.0, y, PAGE_SIZE[0] - MARGIN - 440.0, label_w=120.0)
    _footer(page, art["words"])
    return page


# Everything the schedule column needs, so the drawing can have the rest.
# Two drawings sharing one page would each come out around half this wide,
# and the room dimensions printed inside them are only legible near full
# size. The Type A sheets are portrait and the Type B sheets landscape, so
# the drawing is given the whole box and fitted to its own aspect inside it.
PLAN_TEXT_W = 270.0
PLAN_TEXT_GAP = 34.0
PLAN_IMAGE_W = PAGE_SIZE[0] - 2 * MARGIN - PLAN_TEXT_GAP - PLAN_TEXT_W


def _plan_page(doc, art, *, unit, caption, blob, rows):
    """One drawing at the largest size the page allows, its schedule beside.

    The plans are the one page a buyer zooms into, so the drawing takes the
    full height of the page and the text takes the column that is left,
    rather than the drawing being sized to whatever the text leaves over.
    """
    page = _page(doc)
    s = art["sections"]["plans"]
    _place_image(page, blob,
                 fitz.Rect(MARGIN, MARGIN, MARGIN + PLAN_IMAGE_W, FOOTER_TOP),
                 pad=9, frame=True)

    tx = MARGIN + PLAN_IMAGE_W + PLAN_TEXT_GAP
    tw = PLAN_TEXT_W
    _text(page, fitz.Rect(tx, MARGIN, tx + tw, MARGIN + 42), s["title"],
          font=SERIF, size=23, color=INK)
    _text(page, fitz.Rect(tx, MARGIN + 40, tx + tw, MARGIN + 58),
          f"{art['words'].UNIT_LABELS[art['unit_key']]}, "
          f"{content.plots_label(unit, art['words']).lower()}",
          font=SANS_BOLD, size=9.5, color=TERRA_DEEP)
    _text(page, fitz.Rect(tx, MARGIN + 60, tx + tw, MARGIN + 86), caption,
          font=SERIF, size=15, color=INK_SOFT)
    if _text(page, fitz.Rect(tx, MARGIN + 90, tx + tw, MARGIN + 128),
             art["words"].PLAN_PAIR_NOTE, font=SANS, size=8.5, color=INK_SOFT,
             leading=1.35) < 0:
        raise LayoutOverflow("the plan pair note does not fit its box")
    _schedule(page, rows, tx, MARGIN + 136, tw,
              label_w=138.0, size=9.5, pitch=26.0)
    _footer(page, art["words"])
    return page


def _plans(doc, art):
    """A page per floor per unit type, ground floor first within each.

    Both types are drawn on issued sheets of their own rather than the
    strip of small plans on the layout page, and each sheet shows an
    adjacent pair of townhouses, so each one is worth a page.
    """
    pages = []
    words = art["words"]
    for key, unit in content.UNIT_TYPES.items():
        for sheet in unit["sheets"]:
            pages.append(_plan_page(
                doc, dict(art, unit_key=key), unit=unit,
                caption=words.SHEET_CAPTIONS[sheet["key"]],
                blob=art["sheet_%s_%s" % (key, sheet["key"])],
                rows=content.sheet_rows(unit, sheet, words)))
    return pages


def _layout_key(words) -> str:
    """The two plan types and their plot runs, beside the site plan."""
    lines = []
    for key, unit in content.UNIT_TYPES.items():
        lines.append(words.UNIT_LABELS[key])
        lines.append(content.plots_label(unit, words))
        lines.append("")
    lines.append(words.UI["ask_which_plots"])
    return "\n".join(lines)


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
          _layout_key(art["words"]),
          font=SANS, size=9, color=INK_SOFT, leading=1.5)
    _footer(page, art["words"])
    return page


def _specs(doc, art):
    page = _page(doc)
    s = art["sections"]["specs"]
    y = _heading(page, s["title"], s["lead"])
    col_w = (PAGE_SIZE[0] - 2 * MARGIN - 34) / 2
    groups = art["words"].SPEC_GROUPS
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
    _text(page, fitz.Rect(MARGIN, 444, MARGIN + 300, 466), art["words"].UI["across_the_campus"],
          font=SANS_BOLD, size=9, color=INK_SOFT)
    amen = art["words"].AMENITIES
    third = (len(amen) + 2) // 3
    for col in range(3):
        chunk = amen[col * third:(col + 1) * third]
        x = MARGIN + col * ((PAGE_SIZE[0] - 2 * MARGIN) / 3)
        _text(page, fitz.Rect(x, 466, x + (PAGE_SIZE[0] - 2 * MARGIN) / 3 - 20,
                              FOOTER_TOP - 14),
              "\n".join(chunk), font=SERIF, size=9, color=INK, leading=1.45)
    _footer(page, art["words"])
    return page


def _location(doc, art):
    page = _page(doc)
    s = art["sections"]["location"]
    p = content.PROJECT
    y = _heading(page, s["title"], s["lead"], y=132.0)
    _text(page, fitz.Rect(MARGIN, y, MARGIN + 340, y + 150),
          "\n\n".join(s["body"]) + "\n\n" + art["words"].ADDRESS,
          font=SERIF, size=11, color=INK, leading=1.45)
    _schedule(page, art["words"].LOCATION_ROWS, 440.0, y,
              PAGE_SIZE[0] - MARGIN - 440.0, label_w=96.0)
    rect = fitz.Rect(MARGIN, y + 150, MARGIN + 190, y + 178)
    page.draw_rect(rect, color=TERRA, width=1.2)
    _text(page, rect + (12, 8, 0, 0), art["words"].UI["get_directions"], font=SANS_BOLD,
          size=9.5, color=TERRA_DEEP)
    page.insert_link({"kind": fitz.LINK_URI, "from": rect, "uri": p["maps_url"]})

    # The key plan's distances, as text. The drawing itself is on the page
    # that follows, where its own labels set small; these are the figures a
    # reader can actually read, and the only form of them that translates.
    words = art["words"]
    _fill(page, fitz.Rect(0, 400, PAGE_SIZE[0], FOOTER_TOP - 10), SAND)
    _text(page, fitz.Rect(MARGIN, 412, MARGIN + 320, 434),
          words.UI["nearby"], font=SANS_BOLD, size=9, color=INK_SOFT)
    col_w = (PAGE_SIZE[0] - 2 * MARGIN) / 3
    rows = words.KEY_PLAN_ROWS
    third = (len(rows) + 2) // 3
    for col in range(3):
        _schedule(page, rows[col * third:(col + 1) * third],
                  MARGIN + col * col_w, 436.0, col_w - 20,
                  label_w=col_w - 76, size=8.5, pitch=24.0)
    _footer(page, art["words"])
    return page


def _key_plan(doc, art):
    """The landmark drawing, on a page of its own.

    It is four parts wide to three tall and this page is A4 landscape, so
    the page height is what limits it and there is no column to spare
    beside it. Nothing else goes on the sheet: the distances it pins are
    set as text on the location page facing it, where they can be read at
    a reading size rather than squinted at inside the artwork.
    """
    page = _page(doc)
    _fill(page, fitz.Rect(0, 0, PAGE_SIZE[0], PAGE_SIZE[1]), SAND)
    _place_image(page, art["key_plan"],
                 fitz.Rect(MARGIN, MARGIN, PAGE_SIZE[0] - MARGIN,
                           FOOTER_TOP - 24),
                 pad=8, frame=True)
    _text(page, fitz.Rect(MARGIN, FOOTER_TOP - 22, PAGE_SIZE[0] - MARGIN,
                          FOOTER_TOP - 4), art["words"].UI["key_plan_note"],
          font=SANS, size=8.5, color=INK_SOFT, align=1)
    _footer(page, art["words"])
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
    words = art["words"]
    blocks = (
        (words.UI["call_or_message"], f"{p['phone_display']}\n{p['email']}"),
        (words.UI["site"], words.ADDRESS),
        (words.UI["developer"], f"{words.CREDIT}\n{words.REGD_OFFICE}"),
    )
    by = y + 96
    for i, (head, text) in enumerate(blocks):
        x = MARGIN + i * ((PAGE_SIZE[0] - 2 * MARGIN) / 3)
        _line(page, x, by, x + col_w)
        _text(page, fitz.Rect(x, by + 7, x + col_w, by + 24), head,
              font=SANS_BOLD, size=8.5, color=INK_SOFT)
        _text(page, fitz.Rect(x, by + 24, x + col_w, by + 110), text,
              font=SERIF, size=10.5, color=INK, leading=1.4)

    # Follow takes a row of its own: each profile needs its own link rect,
    # and one textbox of two lines can only carry one.
    fy = by + 124
    _line(page, MARGIN, fy, MARGIN + col_w)
    _text(page, fitz.Rect(MARGIN, fy + 7, MARGIN + col_w, fy + 24), words.UI["follow"],
          font=SANS_BOLD, size=8.5, color=INK_SOFT)
    profiles = (
        (words.UI["aria_instagram"].format(handle=p["social_handle"]),
         p["instagram_url"]),
        (words.UI["aria_facebook"].format(handle=p["social_handle"]),
         p["facebook_url"]))
    for j, (label, uri) in enumerate(profiles):
        rect = fitz.Rect(MARGIN, fy + 24 + j * 20,
                         MARGIN + col_w, fy + 45 + j * 20)
        _text(page, rect, label, font=SERIF, size=10.5, color=TERRA_DEEP)
        page.insert_link({"kind": fitz.LINK_URI, "from": rect, "uri": uri})

    _place_image(page, art["logo"],
                 fitz.Rect(MARGIN, FOOTER_TOP - 96, MARGIN + 116,
                           FOOTER_TOP - 18))
    _footer(page, art["words"])
    return page


def build_doc(locale: str = copy.DEFAULT) -> fitz.Document:
    words = copy.for_locale(locale)
    art = {
        "logo": assets.logo_png(420),
        "render": assets.render_jpeg(1800),
        "site": assets.site_plan_jpeg(1500),
        "key_plan": assets.key_plan_jpeg(1400),
        "sections": {s["id"]: s for s in words.SECTIONS},
        "words": words,
        "locale": locale,
    }
    for key in content.UNIT_TYPES:
        for floor, blob in assets.plan_sheets(key).items():
            art[f"sheet_{key}_{floor}"] = blob
    doc = fitz.open()
    with _using(locale):
        for builder in (_cover, _project, _plans,
                        _layout, _specs, _location, _key_plan,
                        _contact):
            builder(doc, art)
    doc.set_metadata({
        "title": content.PROJECT["name"],
        "author": content.PROJECT["developer"],
        "subject": words.META_DESCRIPTION,
        # Fixed dates keep successive builds byte-identical, so a rebuild
        # does not rewrite dist/ and dirty the working tree.
        "creationDate": BUILD_DATE,
        "modDate": BUILD_DATE,
    })
    return doc


def write(path: str, locale: str = copy.DEFAULT) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    doc = build_doc(locale)
    # Four complete Noto faces would be most of the file. Only the glyphs
    # the brochure actually draws need to travel with it.
    doc.subset_fonts()
    doc.save(path, deflate=True, garbage=4, no_new_id=True)
    doc.close()
    return path
