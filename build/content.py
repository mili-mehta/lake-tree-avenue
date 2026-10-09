"""Single source of truth for all Lake Tree Avenue brochure copy.

No I/O, no formatting decisions — renderers consume these values.
"""
from urllib.parse import quote

PROJECT = {
    "name": "Lake Tree Avenue",
    "tagline": "New Age Townhouses",
    "developer": "TAM Developers",
    "partners": "Udit Talati & Kinjal Mehta",
    "phone_e164": "+918758756666",
    "phone_display": "+91 87587 56666",
    "email": "laketreeavenue@gmail.com",
    "site_address": ("Lake Tree Avenue, Waghodia Main Road, "
                     "next to Spunpipe & Construction Co., Kamlapura, Vadodara"),
    "regd_office": "1-B Ramkrishna Chambers, BPC Road, Alkapuri, Vadodara 390007",
    "maps_url": "https://www.google.com/maps/search/?api=1&query="
                + quote("Spunpipe & Construction Co, Waghodia Road, Vadodara"),
    "unit_count": "48",
    "unit_type": "2 BHK townhouses",
}

FORBIDDEN = (
    "Leo Enterprise", "RAA07983", "RERA", "Ajwa", "Sikandarpura",
    "The Palace", "F.P. No. 42", "3 BHK", "A-TYPE 3",
    "Pioneer Homoeopathic", "22.71",
)


def tel_link() -> str:
    return "tel:" + PROJECT["phone_e164"]


def mail_link() -> str:
    return "mailto:" + PROJECT["email"]


def wa_link(message: str) -> str:
    # wa.me takes bare digits; a leading '+' breaks the path segment.
    digits = PROJECT["phone_e164"].lstrip("+")
    return f"https://wa.me/{digits}?text=" + quote(message, safe="")


def plot_wa_link(plot: int) -> str:
    return wa_link(f"Hi, I'm interested in Plot {plot:02d} at Lake Tree Avenue.")


UNIT_TYPES = {
    "A": {
        "label": "Type A",
        "plots": "Plots 01–06",
        "rooms": (
            ("Kitchen", "9'-9½\" × 9'-1½\""),
            ("Master bedroom", "10'-9½\" × 12'-6\""),
            ("Standing balcony", "2'-0\" wide"),
            ("Store", "Provided"),
        ),
    },
    "B": {
        "label": "Type B",
        "plots": "Plots 07–48",
        "rooms": (
            ("Kitchen", "10'-6\" × 8'-1½\""),
            ("Master bedroom", "11'-0\" × 12'-6\""),
            ("Second bedroom", "10'-1½\" × 10'-7½\""),
            ("Attached toilet", "6'-0\" × 5'-0\""),
            ("Standing balcony", "2'-0\" wide"),
            ("Plot size", "25'-3\" × 39'-1\"  [7.70 m × 11.91 m]"),
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

SECTIONS = (
    {
        "id": "cover",
        "title": "Lake Tree Avenue",
        "lead": "New Age Townhouses",
        "body": ("New launch by TAM Developers",
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
        "title": "A street, not a block",
        "lead": "Brick, stone and glass — repeated down a lit avenue.",
        "body": ("Each home stands on its own plot with a planted forecourt, "
                 "a standing balcony above the entrance and a full-width terrace.",),
    },
    {
        "id": "plans",
        "title": "Floor plans",
        "lead": "Ground, first and terrace levels.",
        "body": ("Every home has living and dining with the kitchen at ground "
                 "level, bedrooms above, and the full terrace at the top.",),
    },
    {
        "id": "layout",
        "title": "Choose your plot",
        "lead": "Tap any plot to enquire about that number.",
        "body": ("Forty-eight plots, a common plot and a landscaped garden, all "
                 "inside one gated boundary.",),
    },
    {
        "id": "specs",
        "title": "Specifications & campus",
        "lead": "What is built in, before you move a thing.",
        "body": (),
    },
    {
        "id": "location",
        "title": "Waghodia Main Road",
        "lead": "Next to Spunpipe & Construction Co., Kamlapura, Vadodara.",
        "body": ("On the main Waghodia road, on Vadodara's eastern growth "
                 "corridor toward Halol.",),
    },
    {
        "id": "contact",
        "title": "Come and see it",
        "lead": "Price on call.",
        "body": ("Site visits daily. Call or send a message on WhatsApp and we "
                 "will share directions.",),
    },
)
