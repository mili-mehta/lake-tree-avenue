"""Single source of truth for all Lake Tree Avenue brochure copy.

No I/O, no formatting decisions — renderers consume these values.
"""
import re
from urllib.parse import quote

PROJECT = {
    "name": "Lake Tree Avenue",
    "tagline": "New Age Townhouses",
    "developer": "TAM Developers",
    "phone_e164": "+918758756666",
    "phone_display": "+91 87587 56666",
    "email": "laketreeavenue@gmail.com",
    "site_address": ("Lake Tree Avenue, Waghodia Main Road, "
                     "next to Spunpipe & Construction Co., Kamlapura, Vadodara"),
    "regd_office": "1-B Ramkrishna Chambers, BPC Road, Alkapuri, Vadodara 390007",
    "maps_url": "https://www.google.com/maps/search/?api=1&query="
                + quote("Spunpipe & Construction Co, Waghodia Road, "
                        "Kamlapura, Vadodara"),
    "unit_count": "48",
    "unit_type": "2 BHK townhouses",
}

CREDIT = "A project by TAM Developers"

# Internal only. The owner credits the firm, never the individuals, so these
# names must never reach a buyer-facing artefact. Bare surnames are listed too
# because "a Talati family project" would carry the same information.
PRIVATE_NAMES = (
    "Dhruv Talati", "Shalin Talati", "Kinjal Mehta",
    "Talati", "Mehta",
)

FORBIDDEN = (
    "Leo Enterprise", "RAA07983", "RERA", "Ajwa", "Sikandarpura",
    "The Palace", "F.P. No. 42", "3 BHK", "A-TYPE 3",
    "Pioneer Homoeopathic", "22.71",
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
    "A": {
        "label": "Type A",
        "plots": "Plots 01\u201306",
        "rooms": (
            ("Plot size", "17'-5\" \u00d7 40'-4\u00bd\"  [5.31 m \u00d7 12.30 m]"),
            ("Living room / dining", "16'-8\" \u00d7 15'-0\""),
            ("Kitchen", "9'-9\u00bd\" \u00d7 9'-1\u00bd\""),
            ("Master bedroom", "10'-9\u00bd\" \u00d7 12'-6\""),
            ("Second bedroom", "10'-9\u00bd\" \u00d7 11'-7\u00bd\""),
            ("Attached toilet", "5'-6\" \u00d7 5'-0\""),
            ("Second attached toilet", "4'-0\" \u00d7 7'-0\""),
            ("Ground floor toilet", "4'-6\" \u00d7 5'-0\""),
            ("Standing balcony", "2'-0\" wide, two"),
            ("Also", "Store, wash area, otta, private terrace"),
        ),
    },
    "B": {
        "label": "Type B",
        "plots": "Plots 07\u201348",
        "rooms": (
            ("Plot size", "18'-1\u00bd\" \u00d7 39'-1\"  [5.52 m \u00d7 11.91 m]"),
            ("Living room / dining", "17'-4\u00bd\" \u00d7 15'-0\""),
            ("Kitchen", "10'-6\" \u00d7 8'-1\u00bd\""),
            ("Master bedroom", "11'-0\" \u00d7 12'-6\""),
            ("Second bedroom", "10'-1\u00bd\" \u00d7 10'-7\u00bd\""),
            ("Attached toilet", "6'-0\" \u00d7 5'-0\""),
            ("Second attached toilet", "4'-0\" \u00d7 7'-0\""),
            ("Ground floor toilet", "4'-6\" \u00d7 5'-0\""),
            ("Standing balcony", "2'-0\" wide, two"),
            ("Also", "Store, wash area, otta, private terrace"),
        ),
    },
}

SPEC_GROUPS = (
    ("Structure", "As per architect and structure design."),
    ("Wall finish", "Putty on internal walls. Exposed brick work on the front "
                    "exterior wall as per architect design, exterior paint on "
                    "other exterior walls."),
    ("Flooring", "Vitrified flooring in all rooms with skirting. Anti-skid "
                 "ceramic tiles in all balconies."),
    ("Kitchen", "Granite platform with stainless steel sink, ceramic tiles up "
                "to lintel level."),
    ("Bathrooms", "Designer wall tiles up to lintel level, good quality sanitary "
                  "and plumbing fixtures, stone door frame."),
    ("Electrical", "Good quality modular switches, AC point in the master "
                   "bedroom, geyser point in all bathrooms."),
    ("Doors & windows", "Elegant main door and internal flush doors with laminate "
                        "and stone frame. Colour-anodised aluminium windows with "
                        "safety grills."),
    ("Terrace", "Brick bed waterproofing treatment."),
    ("Protection", "Anti-termite treatment at ground level. Overhead and "
                   "underground water tanks."),
)

AMENITIES = (
    "Impressive gate with security cabin",
    "Large open-space parking",
    "Underground cabling for a wire-free campus",
    "Tremix concrete internal roads with paved sides",
    "Roadside plantation and street lights",
    "Rain water harvesting system",
    "Garbage storage provision",
    "Landscape garden with community hall",
)

LOCATION_ROWS = (
    ("Road", "Main Waghodia Road frontage"),
    ("Between", "Parul University and Sumandeep College"),
    ("Next to", "Spunpipe & Construction Co."),
    ("Area", "Kamlapura, Vadodara"),
    ("Corridor", "Vadodara east, toward Halol"),
)

SECTIONS = (
    {
        "id": "cover",
        "title": "Lake Tree Avenue",
        "lead": "New Age Townhouses",
        "body": ("A project by TAM Developers",
                 "Waghodia Main Road, Vadodara"),
    },
    {
        "id": "project",
        "title": "Forty-eight homes on one quiet avenue",
        "lead": "2 BHK townhouses in a gated campus off Waghodia Main Road.",
        "body": (
            "Lake Tree Avenue is a gated campus of 48 two-bedroom townhouses, "
            "each with its own entrance, private terrace and parking.",
            "A 12-metre town planning road brings you to the gate. Inside, "
            "7.5-metre internal roads reach every door.",
            "Two plan types: six homes in the entrance row, forty-two along the "
            "avenue.",
        ),
    },
    {
        "id": "render",
        "title": "What the front gives away",
        "lead": "Front and rear elevation, drawn to scale.",
        "body": ("Exposed brick across the front, a standing balcony over the "
                 "entrance, and the terrace parapet carried through as a line "
                 "rather than a wall.",),
    },
    {
        "id": "plans",
        "title": "Floor plans",
        "lead": "Ground and first floor, drawn to scale.",
        "body": ("Living and dining with the kitchen at ground level, both "
                 "bedrooms above, and the full terrace over them.",),
    },
    {
        "id": "layout",
        "title": "The site plan",
        "lead": "Forty-eight plots, a common plot and a landscaped garden, "
                "all inside one gated boundary.",
        "body": ("Six homes stand in the entrance row; the other forty-two "
                 "line the avenue behind them.",),
    },
    {
        "id": "specs",
        "title": "Specifications & campus",
        "lead": "What is built in, before you move a thing.",
        "body": (),
    },
    {
        "id": "location",
        "title": "Between Parul and Sumandeep",
        "lead": "On the main Waghodia Road, in the stretch between Parul "
                "University and Sumandeep College.",
        "body": ("The gate opens onto the main road, so there is no approach "
                 "lane to negotiate and no last-mile detour.",
                 "Two of Vadodara's largest campuses sit either side of you, "
                 "which is what keeps this stretch of road serviced, lit and "
                 "in demand with tenants.",),
    },
    {
        "id": "contact",
        "title": "Come and see it",
        "lead": "Price on call.",
        "body": ("Site visits daily. Call or send a message on WhatsApp and we "
                 "will share directions.",),
    },
)
