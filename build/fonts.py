"""The Devanagari and Gujarati faces, for both renderers.

Latin needs nothing from this module: the brochure's Palatino stack is
already on every device it opens on. Devanagari and Gujarati are not, so
the HTML carries them inline and the PDF embeds them.

Two formats, two renderers:

  woff2  base64'd into a <style> block. The page is opened from file://
         after a WhatsApp forward, where a linked font never arrives.
  ttf    handed to MuPDF through an fitz.Archive, which shapes it with
         HarfBuzz -- the only reason the PDF can draw these scripts at all.

Both are vendored under fonts/ by tools/fetch_fonts.py, never fetched here:
the build is offline and byte-reproducible.
"""
import base64
import functools
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "fonts")

# The CSS family name each locale's text asks for, by role. English is
# absent on purpose -- it resolves to the brochure's own Latin stack.
PDF_FAMILIES = {
    "hi": {"serif": "serif-deva", "sans": "sans-deva"},
    "gu": {"serif": "serif-gujr", "sans": "sans-gujr"},
}

FACE_NAMES = {
    "serif-deva": "Noto Serif Devanagari",
    "sans-deva": "Noto Sans Devanagari",
    "serif-gujr": "Noto Serif Gujarati",
    "sans-gujr": "Noto Sans Gujarati",
}

# Devanagari and Gujarati hang matras above and below the line. Set at the
# Latin leading they collide; set at the Latin size they read smaller than
# the Latin around them, because the scripts carry less of their weight on
# the x-height. Both are per script, so English is untouched.
LEADING = {"en": 1.62, "hi": 1.78, "gu": 1.76}
SCALE = {"en": 1.0, "hi": 1.05, "gu": 1.05}


def _read(name: str) -> bytes:
    with open(os.path.join(DIR, name), "rb") as fh:
        return fh.read()


@functools.lru_cache(maxsize=None)
def _data_uri(key: str) -> str:
    blob = base64.b64encode(_read(key + ".woff2")).decode("ascii")
    return "data:font/woff2;base64," + blob


@functools.lru_cache(maxsize=None)
def face_css(locale: str) -> str:
    """@font-face blocks for one locale, payload included.

    One variable file answers both weights, so each family is declared
    once over a weight range. Declaring 400 and 600 separately would be
    correct CSS and would also paste the same 120 KB of base64 into the
    page twice -- in a single-file document the payload is the declaration.
    """
    families = PDF_FAMILIES.get(locale)
    if not families:
        return ""
    return "\n".join(
        f"@font-face {{ font-family: '{FACE_NAMES[key]}';"
        f" font-style: normal; font-weight: 400 600;"
        f" font-display: swap; src: url({_data_uri(key)}) format('woff2'); }}"
        for key in families.values()
    )


def ttf_archive_dir() -> str:
    """The directory MuPDF reads the TTFs out of."""
    return DIR


def pdf_face_css(locale: str) -> str:
    """@font-face blocks naming the TTFs by filename, for fitz.Archive.

    MuPDF resolves these against the archive directory, so the payload
    stays out of the stylesheet -- unlike the HTML, which has nowhere to
    put a separate file.
    """
    families = PDF_FAMILIES.get(locale)
    if not families:
        return ""
    return "\n".join(
        f"@font-face {{ font-family: '{FACE_NAMES[key]}';"
        f" src: url({key}.ttf); }}"
        for key in families.values()
    )


def pdf_stack(locale: str, role: str) -> str:
    """The font-family MuPDF should use for one locale and role.

    English resolves to MuPDF's built-in serif and sans, which is what the
    brochure drew with before this module existed, so the English PDF does
    not shift when the Indic ones arrive.
    """
    builtin = "serif" if role == "serif" else "sans-serif"
    families = PDF_FAMILIES.get(locale)
    if not families:
        return builtin
    return f"'{FACE_NAMES[families[role]]}', {builtin}"
