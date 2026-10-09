"""Everything about Lake Tree Avenue that is true in every language.

A phone number, a plot depth of 39'-1", a Google Maps URL and the list of
terms that must never reach a buyer do not change when the reader switches
to Gujarati. The words around them do, and those live in build/copy/.

No I/O, no formatting decisions — renderers consume these values.
"""
import re
from urllib.parse import quote

# The site pin, read straight off the owner's own Google Maps share link
# (https://maps.app.goo.gl/Lpv23NqKy2tFcg7Q8), which resolves to
# maps.google.com/?q=22.2918248,73.3433214. Coordinates, not a place name:
# a text search would leave Google to pick a stretch of Waghodia Road, and
# there are several it could pick. The short link itself is never printed --
# goo.gl links are redirects that can rot, and the numbers cannot.
SITE_LATLNG = "22.2918248,73.3433214"

PROJECT = {
    "name": "Lake Tree Avenue",
    "developer": "TAM Developers",
    "phone_e164": "+918758756666",
    "phone_display": "+91 87587 56666",
    "email": "laketreeavenue@gmail.com",
    # One handle on both networks, so a caption, a footer or a hoarding can
    # print it once and be right for either.
    "social_handle": "@laketreeavenue",
    "instagram_url": "https://www.instagram.com/laketreeavenue",
    "facebook_url": "https://www.facebook.com/laketreeavenue",
    "site_latlng": SITE_LATLNG,
    # Google's documented universal maps URL (api=1). A "dir" link, not a
    # "search" one, so a tap on a phone hands off to the Maps app and comes
    # up already routing to the gate from wherever the reader is standing;
    # on a desktop the same URL opens directions on maps.google.com.
    "maps_url": "https://www.google.com/maps/dir/?api=1&destination="
                + quote(SITE_LATLNG) + "&travelmode=driving",
    "unit_count": "48",
}

# The sections, in the order both renderers lay them out. The titles and
# the prose are per language; only the running order is shared.
SECTION_IDS = ("cover", "project", "plans", "layout", "specs", "location",
               "contact")

# Internal only. The owner credits the firm, never the individuals, so these
# names must never reach a buyer-facing artefact. Bare surnames are listed too
# because "a Talati family project" would carry the same information.
#
# Each entry is every spelling a reader could recognise it by. A guard that
# only knows the Latin spelling goes blind the moment the copy is Hindi:
# "अजवा" is the same claim to a buyer as "Ajwa".
PRIVATE_NAMES = (
    "Dhruv Talati", "Shalin Talati", "Kinjal Mehta",
    "Talati", "Mehta",
    "ध्रुव", "तलाटी",
    "मेहता",
    "ધ્રુવ", "તલાટી",
    "મેહતા",
)

FORBIDDEN = (
    "Leo Enterprise", "RAA07983", "RERA", "Ajwa", "Sikandarpura",
    "The Palace", "F.P. No. 42", "3 BHK", "A-TYPE 3",
    "Pioneer Homoeopathic", "22.71",
    # The same terms as a Hindi or Gujarati reader would meet them.
    "लियो",            # Leo
    "अजवा",            # Ajwa
    "सिकंदरपुरा",
    "रेरा",            # RERA
    "3 बीएचके",
    "લિયો",
    "અજવા",
    "સિકંદરપુરા",
    "રેરા",
    "3 બીએચકે",
)


def forbidden_hits(text: str) -> list[str]:
    """Superseded terms present in `text`, ignoring how it is broken up.

    A phrase that wraps across a line, a table cell or two paragraphs still
    reads as that phrase to a buyer, so whitespace and tags are collapsed
    before matching. Matching the raw string would miss "The\nPalace".
    """
    flat = re.sub(r"<[^>]+>", " ", text)
    flat = re.sub(r"\s+", " ", flat).lower()
    return [term for term in FORBIDDEN + PRIVATE_NAMES
            if re.sub(r"\s+", " ", term).lower() in flat]


def tel_link() -> str:
    return "tel:" + PROJECT["phone_e164"]


def mail_link() -> str:
    return "mailto:" + PROJECT["email"]


def wa_link(message: str) -> str:
    # wa.me takes bare digits; a leading '+' breaks the path segment.
    digits = PROJECT["phone_e164"].lstrip("+")
    return f"https://wa.me/{digits}?text=" + quote(message, safe="")


UNIT_TYPES = {
    # Both types are read off their own pair of issued sheets, one per
    # floor, which supersede the strip of small plans on the layout page.
    # The homes within a type are identical inside; only the land under
    # them varies, so plot width is a range and every room is one figure.
    #
    # Rows are keyed, not labelled. The label is the one part of a row that
    # changes with the reader's language, and a sheet that referenced its
    # rows by their English label would stop finding them in Hindi.
    #
    # A value of None means the row reads as prose rather than as a
    # measurement, so it comes from the locale's ROOM_VALUE_WORDS. "{to}"
    # is the range connector -- "to", "से", "થી".
    "A": {
        "plot_range": "01–06",
        "rooms": (
            ("plot_width", "17'-5\" {to} 24'-7½\"  "
                           "[5.31 m {to} 7.51 m]"),
            ("plot_depth", "40'-4½\"  [12.30 m]"),
            # Width times depth at each end of the range, rounded down so
            # the brochure never claims land the plot does not have. No
            # metric twin: the two rows above carry it, and spelled out in
            # full this one wrapped to a second line on its own.
            ("plot_area", "703 {to} 994 sq ft"),
            ("living", "16'-8\" × 15'-0\""),
            ("kitchen", "9'-9½\" × 9'-1½\""),
            ("master_bed", "11'-0\" × 12'-6\""),
            ("second_bed", "10'-1½\" × 11'-7½\""),
            ("attached_toilet", "6'-0\" × 5'-0\""),
            ("second_attached_toilet", "4'-0\" × 7'-0\""),
            ("ground_toilet", "4'-6\" × 5'-0\""),
            ("standing_balcony", None),
            ("also", None),
        ),
        # Which rows belong to which drawing. The PDF gives each floor a
        # page of its own, and a page that repeated all eleven rows beside
        # a drawing showing five of them would send the reader hunting.
        # Every row belongs to exactly one sheet; sheet_rows enforces it.
        "sheets": (
            {
                "key": "ground",
                "rows": ("plot_width", "plot_depth", "plot_area",
                         "living", "kitchen", "ground_toilet", "also"),
            },
            {
                "key": "first",
                "rows": ("master_bed", "second_bed", "attached_toilet",
                         "second_attached_toilet", "standing_balcony"),
            },
        ),
    },
    "B": {
        "plot_range": "07–48",
        "rooms": (
            ("plot_width", "18'-1½\" {to} 24'-8\"  "
                           "[5.52 m {to} 7.52 m]"),
            ("plot_depth", "39'-1\"  [11.91 m]"),
            ("plot_area", "708 {to} 964 sq ft"),
            ("living", "17'-4½\" × 15'-0\""),
            ("kitchen", "10'-6\" × 8'-1½\""),
            ("master_bed", "11'-0\" × 12'-6\""),
            ("second_bed", "10'-1½\" × 10'-7½\""),
            ("attached_toilet", "6'-0\" × 5'-0\""),
            ("second_attached_toilet", "4'-0\" × 7'-0\""),
            ("ground_toilet", "4'-6\" × 5'-0\""),
            ("standing_balcony", None),
            ("also", None),
        ),
        "sheets": (
            {
                "key": "ground",
                "rows": ("plot_width", "plot_depth", "plot_area",
                         "living", "kitchen", "ground_toilet", "also"),
            },
            {
                "key": "first",
                "rows": ("master_bed", "second_bed", "attached_toilet",
                         "second_attached_toilet", "standing_balcony"),
            },
        ),
    },
}


def room_value(unit: dict, key: str, words) -> str:
    """One schedule value, in the reader's language.

    The measurement itself is the same in every language -- Latin numerals,
    feet and inches as the architect issued them. Only the words inside it
    move: the range connector, and the two rows that are prose rather than
    a figure.
    """
    template = dict(unit["rooms"])[key]
    if template is None:
        return words.ROOM_VALUE_WORDS[key]
    return template.format(to=words.UI["range_to"])


def unit_rooms(unit: dict, words) -> tuple[tuple[str, str], ...]:
    """A whole schedule, labelled and valued in the reader's language."""
    return tuple((words.ROOM_LABELS[key], room_value(unit, key, words))
                 for key, _ in unit["rooms"])


def plots_label(unit: dict, words) -> str:
    """"Plots 07–48", in the reader's language. The numbers never move."""
    return words.PLOTS_LABEL.format(range=unit["plot_range"])


def sheet_rows(unit: dict, sheet: dict, words) -> tuple[tuple[str, str], ...]:
    """The schedule rows belonging to one floor's drawing.

    Raises on a row key that is not in the unit, so a renamed dimension
    cannot quietly drop off the page that was meant to carry it.
    """
    rooms = dict(unit["rooms"])
    missing = [key for key in sheet["rows"] if key not in rooms]
    if missing:
        raise KeyError(f"{sheet['key']} sheet lists unknown rows: {missing}")
    return tuple((words.ROOM_LABELS[key], room_value(unit, key, words))
                 for key in sheet["rows"])
