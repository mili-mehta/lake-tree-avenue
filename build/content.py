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
    "email": "info@laketreeavenue.com",
    # The project's own domain. Printed bare, because that is what a
    # buyer types and what fits a footer cell; the link beside it
    # carries the scheme a browser and a PDF viewer both need.
    "website_display": "laketreeavenue.com",
    "website_url": "https://laketreeavenue.com",
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
               "contact", "disclaimers")

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


# Every plot on the site plan, and the area of the land under that home,
# as the developer issued them on one sheet. Site-plan order, so a reader
# with the drawing in front of them reads down the same numbers.
#
# The sheet also carried a price per plot and a payment schedule. Neither
# is here: the brochure quotes price on call, and a figure committed to a
# published file is a figure that outlives the week it was true.
#
# Two-digit numbers come from the renderers, not from this tuple -- these
# are the plot's number, and 7 is 7.
PLOT_AREAS = (
    (1, 1041), (2, 703), (3, 703), (4, 703), (5, 713), (6, 937),
    (7, 707), (8, 707), (9, 707), (10, 707), (11, 822), (12, 1007),
    (13, 1050), (14, 920), (15, 709), (16, 709), (17, 709), (18, 901),
    (19, 901), (20, 709), (21, 709), (22, 709), (23, 709), (24, 845),
    (25, 845), (26, 709), (27, 709), (28, 709), (29, 709), (30, 901),
    (31, 901), (32, 709), (33, 709), (34, 709), (35, 1013), (36, 898),
    (37, 714), (38, 713), (39, 713), (40, 712), (41, 873), (42, 872),
    (43, 710), (44, 709), (45, 709), (46, 709), (47, 709), (48, 863),
)

# The unit every measured area is given in. Latin in all three documents,
# the same as the dimensions inside the drawings: a buyer compares "709
# sq ft" against every other brochure they are holding.
AREA_UNIT = "sq ft"

# Most of the scheme is one plot: thirty-one homes stand on 703 to 714
# sq ft and read as the same piece of ground. Above this figure the plot
# is visibly bigger -- a corner, a head of a row, a wider frontage -- and
# those are the plots a buyer is choosing between. The schedules tint
# them so the reader finds them without comparing forty-eight numbers by
# eye.
LARGE_PLOT_SQFT = 715


UNIT_TYPES = {
    # Both types are read off their own pair of issued sheets, one per
    # floor, which supersede the strip of small plans on the layout page.
    # The homes within a type are identical inside; only the land under
    # them varies, so plot area is a range and every room is one figure.
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
            # As given by the developer. Plot width and depth are no longer
            # stated: the area is the one figure a buyer compares.
            ("plot_area", "703 {to} 1041 sq ft"),
            ("living", "16'-8\" × 15'-0\""),
            ("kitchen", "9'-9½\" × 9'-1½\""),
            ("master_bed", "10'-9½\" × 12'-6\""),
            ("second_bed", "10'-9½\" × 11'-7½\""),
            ("attached_toilet", "5'-6\" × 5'-0\""),
            ("second_attached_toilet", "4'-0\" × 7'-0\""),
            ("ground_toilet", "4'-6\" × 5'-0\""),
            ("standing_balcony", None),
            ("ots", None),
            ("also", None),
        ),
        # Which rows belong to which drawing. The PDF gives each floor a
        # page of its own, and a page that repeated all eleven rows beside
        # a drawing showing five of them would send the reader hunting.
        # Every row belongs to exactly one sheet; sheet_rows enforces it.
        "sheets": (
            {
                "key": "ground",
                "rows": ("plot_area", "living", "kitchen", "ground_toilet",
                         "also"),
            },
            {
                "key": "first",
                "rows": ("master_bed", "second_bed", "attached_toilet",
                         "second_attached_toilet", "standing_balcony",
                         "ots"),
            },
        ),
    },
    "B": {
        "plot_range": "07–48",
        "rooms": (
            ("plot_area", "707 {to} 1050 sq ft"),
            ("living", "17'-4½\" × 15'-0\""),
            ("kitchen", "10'-6\" × 8'-1½\""),
            ("master_bed", "11'-0\" × 12'-6\""),
            ("second_bed", "10'-1½\" × 10'-7½\""),
            ("attached_toilet", "6'-0\" × 5'-0\""),
            ("second_attached_toilet", "4'-0\" × 7'-0\""),
            ("ground_toilet", "4'-6\" × 5'-0\""),
            ("standing_balcony", None),
            ("ots", None),
            ("also", None),
        ),
        "sheets": (
            {
                "key": "ground",
                "rows": ("plot_area", "living", "kitchen", "ground_toilet",
                         "also"),
            },
            {
                "key": "first",
                "rows": ("master_bed", "second_bed", "attached_toilet",
                         "second_attached_toilet", "standing_balcony",
                         "ots"),
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


def plot_unit_key(number: int) -> str:
    """Which plan type the home on plot `number` is built to.

    Read off the type's own plot run rather than hard-coded, so the two
    cannot drift: the runs are what the drawings are titled with.
    """
    for key, unit in UNIT_TYPES.items():
        first, last = (int(part) for part in unit["plot_range"].split("\u2013"))
        if first <= number <= last:
            return key
    raise KeyError(f"plot {number} belongs to no plan type")


def plot_area_cells() -> tuple[tuple[str, str, bool], ...]:
    """The plot schedule, ready to set: number, area, and whether it is big.

    Nothing here is translated. A plot number is a plot number and the
    area is Latin numerals and `AREA_UNIT`; the flag is a fact about the
    land, not a word, and each renderer marks it in its own way.
    """
    return tuple((f"{number:02d}", f"{area} {AREA_UNIT}",
                  area > LARGE_PLOT_SQFT)
                 for number, area in PLOT_AREAS)
