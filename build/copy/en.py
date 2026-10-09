"""The English copy.

Moved here out of content.py unchanged, so that content.py holds only what
is true in every language: a phone number, a plot depth, a maps URL.

Every locale module in this package exposes exactly these names, and
tests/test_copy.py fails the build if one of them drifts.
"""

TAGLINE = "New Age Townhouses"
CREDIT = "A project by TAM Developers"
ADDRESS = ("Lake Tree Avenue, Waghodia Main Road, "
           "next to Spunpipe & Construction Co., Kamlapura, "
           "Vadodara 391760")
REGD_OFFICE = ("Regd. Office: 1-B Ramkrishna Chambers, BPC Road, "
               "Alkapuri, Vadodara 390007")

META_DESCRIPTION = ("48 two-bedroom townhouses on Waghodia Main Road, "
                    "Vadodara. A new launch by TAM Developers.")

# Internal only. The owner credits the firm, never the individuals.
WHATSAPP_MESSAGE = "Hi, I'd like to know more about Lake Tree Avenue."

PLAN_PAIR_NOTE = ("Each sheet draws two adjacent homes. "
                  "Every dimension is for one home.")

UNIT_LABELS = {"A": "Type A", "B": "Type B"}

# The plot range itself is language-neutral and lives in content.py; only
# the word in front of it changes.
PLOTS_LABEL = "Plots {range}"

SHEET_CAPTIONS = {"ground": "Ground floor", "first": "First floor"}

ROOM_LABELS = {
    "plot_width": "Plot width",
    "plot_depth": "Plot depth",
    "plot_area": "Plot area",
    "living": "Living room / dining",
    "kitchen": "Kitchen",
    "master_bed": "Master bedroom",
    "second_bed": "Second bedroom",
    "attached_toilet": "Attached toilet",
    "second_attached_toilet": "Second attached toilet",
    "ground_toilet": "Ground floor toilet",
    "standing_balcony": "Standing balcony",
    "also": "Also",
}

ROOM_VALUE_WORDS = {
    "standing_balcony": "2'-0\" wide, two",
    "also": "Store, wash area, otta, private terrace",
}

PROJECT_SCHEDULE = (
    ("Homes", "48 townhouses, two bedrooms each"),
    ("Plan types", "Type A, plots 01–06 / Type B, plots 07–48"),
    ("Approach road", "12.00 m town planning road"),
    ("Internal roads", "7.50 m, paved both sides"),
    ("Levels", "Ground, first and private terrace"),
    ("Parking", "On plot, plus open-space parking"),
)

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
    ("Road", "Waghodia Main Road frontage"),
    ("Between", "Parul University and Sumandeep College"),
    ("Next to", "Spunpipe & Construction Co."),
    ("Area", "Kamlapura, Vadodara"),
    ("Corridor", "Vadodara east, toward Halol"),
)

# The landmarks the key plan pins, and how far each one is by road.
#
# These figures exist nowhere else: the key plan carries them as artwork,
# and a picture of a number is invisible to a screen reader, to a search
# engine and to anyone who copies a line to send on. So they are set as
# text beside the drawing rather than left in its pixels.
#
# The Hindi and Gujarati sheets carry these names in their own script, so
# a reader of those pages never meets half a line of Latin.
KEY_PLAN_ROWS = (
    ("Parul University", "2.3 km"),
    ("Sumandeep Vidyapeeth", "2.3 km"),
    ("Dhiraj Hospital", "2.3 km"),
    ("Avalon World School", "2.5 km"),
    ("Waghodia GIDC", "4.2 km"),
    ("L&T Knowledge City", "8.8 km"),
    ("Nimeta Garden", "9.7 km"),
    ("AATAPI Wonderland", "10.1 km"),
    ("Vadodara Airport", "13.8 km"),
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
        "lead": "2 BHK townhouses in a gated campus on Waghodia Main Road.",
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
        "lead": "On Waghodia Main Road, in the stretch between Parul "
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

UI = {
    # The connector inside a measured range: 703 to 994 sq ft. The numbers
    # never move; only this word does.
    "range_to": "to",

    # calls to action
    "enquire_whatsapp": "Enquire on WhatsApp",
    "call": "Call {phone}",
    "whatsapp": "WhatsApp {phone}",
    "see_plot_map": "See the plot map",
    "get_directions": "Get directions",
    "directions_on_maps": "Directions on Google Maps",
    "download_pdf": "Download this brochure as a PDF",

    # headings
    "across_the_campus": "Across the campus",
    "call_or_message": "Call or message",
    "site": "Site",
    "developer": "Developer",
    "follow": "Follow",
    "website": "Website",
    "layout_plan": "LAYOUT PLAN",
    "sheet_subtitle": "Lake Tree Avenue, Waghodia Main Road, Vadodara",
    "ask_which_plots": "Ask us which plots are still open",
    "follow_line": "{handle} on Instagram and Facebook",

    # the sticky bar
    "bar_call": "Call",
    "bar_whatsapp": "WhatsApp",
    "bar_directions": "Directions",
    "bar_label": "Contact",

    # accessible names
    "aria_instagram": "Instagram {handle}",
    "aria_facebook": "Facebook {handle}",
    "aria_language": "Language",
    "alt_hero": "Lake Tree Avenue townhouses along the avenue",
    "alt_logo": "Lake Tree Avenue",
    "alt_site_plan": ("Site plan showing 48 numbered plots, the internal "
                      "roads, the common plot and the entry gate"),
    "key_plan_subtitle": "What stands either side of the gate",
    "nearby": "By road from the gate",
    "key_plan_note": "Distances are approximate, measured by road.",
    "alt_key_plan": ("Key plan: Lake Tree Avenue on Waghodia Main Road, with the "
                     "schools, hospitals, universities and landmarks either "
                     "side of it pinned along the road. Not to scale; the "
                     "distances are listed beside it."),
    "alt_plan_sheet": "{caption} plan for plots {range}, with room dimensions",
}

# The language pills read the same in every document: a reader looking for
# Gujarati is looking for the word "ગુજરાતી", whichever language is on
# screen when they start looking.
LANGUAGE_NAMES = {"en": "English", "hi": "हिन्दी",
                  "gu": "ગુજરાતી"}
