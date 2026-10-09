# Lake Tree Avenue E-Brochure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build two self-contained, no-hosting sales artefacts for Lake Tree Avenue — a single-file offline HTML brochure and an A4-landscape PDF with live tap-to-contact link annotations — from one shared Python content source.

**Architecture:** A `build/` package holds the content facts, the plot-hotspot table, and the image pipeline as three independent modules with no knowledge of output format. Two renderer modules consume them: `build_html.py` emits one self-contained `.html` with base64 data URIs and an SVG hotspot overlay, `build_pdf.py` draws pages with PyMuPDF and attaches link annotations. A top-level `build.py` runs both and writes to `dist/`.

**Tech Stack:** Python 3.11 (system), PyMuPDF 1.28 (`fitz`) for PDF reading, rasterising and writing, Pillow 12.2 for image crop/resize/encode, stdlib `unittest` for tests (pytest is NOT installed and no network install is available — do not add dependencies).

**Spec:** `docs/superpowers/specs/2026-10-09-lake-tree-avenue-ebrochure-design.md`

## Global Constraints

- **No new dependencies.** Only Python 3.11 stdlib, `fitz` (PyMuPDF 1.28), `PIL` (Pillow 12.2). No pip installs, no network at build time or run time.
- **Phone:** `+918758756666` in all `tel:`/`wa.me` URIs; displayed as `+91 87587 56666`.
- **Email:** `laketreeavenue@gmail.com`
- **Developer attribution:** `TAM Developers` only. Partners `Udit Talati & Kinjal Mehta`.
- **Site address:** `Lake Tree Avenue, Waghodia Main Road, next to Spunpipe & Construction Co., Kamlapura, Vadodara`
- **Regd. office:** `1-B Ramkrishna Chambers, BPC Road, Alkapuri, Vadodara 390007`
- **Forbidden strings** in any generated artefact (case-insensitive): `Leo Enterprise`, `RAA07983`, `RERA`, `Ajwa`, `Sikandarpura`, `The Palace`, `F.P. No. 42`, `3 BHK`, `A-TYPE 3`, `Pioneer Homoeopathic`, `22.71`.
- **No price** anywhere. Enquiry CTAs read `Price on call`.
- **Light backgrounds only.** No dark mode, no dark sections. The page declares `color-scheme: light` and keeps a white or warm off-white ground throughout, in both artefacts. Owner's explicit instruction; it overrides the usual dark-mode default.
- **Unit mix:** 48 plots. Type A = plots 01–06. Type B = plots 07–48.
- **Size budgets:** HTML ≤ 6 MB hard ceiling (4 MB target); PDF ≤ 8 MB.
- **HTML self-containment:** zero external subresources; system font stack only.
- Run all tests with `python3 -I -m unittest discover -s tests -v` from the repo root.

## Review Focus

1. **Country code on the phone number.** The owner supplied `8758756666` with no `+91`. A `tel:` link missing the country code fails for any recipient roaming or saved with international format. Pinned in Task 1.
2. **Apostrophes and spaces in prefilled WhatsApp text.** `Hi, I'm interested in Plot 07` must be percent-encoded so WhatsApp receives it intact rather than truncating at the apostrophe or breaking the URL. Pinned in Task 1.
3. **HTML opened from `file://` on a phone.** No `fetch`, no `XMLHttpRequest`, no service worker, no module scripts — iOS Safari blocks several of these for `file://` origins, which would silently break the plot map. Pinned in Task 4.
4. **PDF viewers that ignore link annotations.** WhatsApp's in-app Android viewer often renders a PDF without live links. Every contact point must also appear as readable text, so a recipient can still dial it manually. Pinned in Task 5.
5. **Plot hotspots landing outside their plot.** Eight plots have no text label and are placed from manually-read coordinates; a mis-placed hotspot sends a buyer an enquiry for the wrong plot. Pinned in Task 2 and visually in Task 6.

---

## File Structure

| File | Responsibility |
|---|---|
| `build/__init__.py` | Empty package marker |
| `build/content.py` | Project facts, CTA link builders, section copy, specification and amenity text. No I/O. |
| `build/plots.py` | Plot number → hotspot rectangle table, normalised to 0–1 of the layout page |
| `build/assets.py` | Crop, downscale and encode every image; raster of the layout; floor-plan crops |
| `build/build_html.py` | Renders the single-file HTML |
| `build/build_pdf.py` | Renders the interactive PDF |
| `build.py` | Entry point: builds both into `dist/` |
| `tests/test_content.py` | Facts, link encoding, forbidden strings |
| `tests/test_plots.py` | Hotspot table completeness and bounds |
| `tests/test_assets.py` | Image budgets, dimensions, letterbox removal |
| `tests/test_html.py` | Self-containment, hotspots, budget |
| `tests/test_pdf.py` | Geometry, annotations, budget, readable contact text |
| `dist/Lake-Tree-Avenue.html` | Deliverable A (generated, committed) |
| `dist/Lake-Tree-Avenue-eBrochure.pdf` | Deliverable B (generated, committed) |
| `dist/qa-hotspots.png` | Hotspot overlay for visual verification (generated) |

---

### Task 1: Content module

**Files:**
- Create: `build/__init__.py`, `build/content.py`
- Test: `tests/test_content.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `PROJECT: dict[str, str]` with keys `name`, `tagline`, `developer`, `partners`, `phone_e164`, `phone_display`, `email`, `site_address`, `regd_office`, `maps_url`, `unit_count`, `unit_type`
  - `tel_link() -> str`
  - `mail_link() -> str`
  - `wa_link(message: str) -> str`
  - `plot_wa_link(plot: int) -> str`
  - `FORBIDDEN: tuple[str, ...]`
  - `SECTIONS: tuple[dict, ...]` — each `{"id": str, "title": str, "lead": str, "body": tuple[str, ...]}`
  - `SPEC_GROUPS: tuple[tuple[str, str], ...]` — `(label, text)`
  - `AMENITIES: tuple[str, ...]`
  - `UNIT_TYPES: dict[str, dict]` — `{"A": {"label","plots","rooms"}, "B": {...}}` where `rooms` is `tuple[tuple[str, str], ...]` of `(room, dimension)`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_content.py
import re, unittest
from urllib.parse import unquote
from build import content


class TestFacts(unittest.TestCase):
    def test_phone_is_e164_with_india_country_code(self):
        self.assertEqual(content.PROJECT["phone_e164"], "+918758756666")

    def test_phone_display_is_grouped(self):
        self.assertEqual(content.PROJECT["phone_display"], "+91 87587 56666")

    def test_tel_link_carries_country_code(self):
        self.assertEqual(content.tel_link(), "tel:+918758756666")

    def test_wa_link_uses_bare_digits_no_plus(self):
        # wa.me rejects a leading '+' in the path segment
        self.assertTrue(content.wa_link("hi").startswith("https://wa.me/918758756666?text="))

    def test_mail_link(self):
        self.assertEqual(content.mail_link(), "mailto:laketreeavenue@gmail.com")

    def test_developer_is_tam(self):
        self.assertEqual(content.PROJECT["developer"], "TAM Developers")
        self.assertEqual(content.PROJECT["partners"], "Udit Talati & Kinjal Mehta")


class TestWhatsAppEncoding(unittest.TestCase):
    def test_apostrophe_and_spaces_are_encoded(self):
        link = content.wa_link("Hi, I'm interested")
        self.assertNotIn(" ", link)
        self.assertNotIn("'", link)

    def test_message_round_trips(self):
        msg = "Hi, I'm interested in Plot 07 at Lake Tree Avenue."
        link = content.wa_link(msg)
        self.assertEqual(unquote(link.split("text=", 1)[1]), msg)

    def test_plot_link_is_zero_padded_and_specific(self):
        self.assertIn("Plot%2007", content.plot_wa_link(7))
        self.assertIn("Plot%2048", content.plot_wa_link(48))

    def test_every_plot_produces_a_distinct_link(self):
        links = {content.plot_wa_link(n) for n in range(1, 49)}
        self.assertEqual(len(links), 48)


class TestSupersededFacts(unittest.TestCase):
    def _all_strings(self):
        out = []
        for v in content.PROJECT.values():
            out.append(str(v))
        for s in content.SECTIONS:
            out.append(s["title"]); out.append(s["lead"]); out.extend(s["body"])
        for label, text in content.SPEC_GROUPS:
            out.append(label); out.append(text)
        out.extend(content.AMENITIES)
        for t in content.UNIT_TYPES.values():
            out.append(t["label"]); out.append(t["plots"])
            out.extend(r for pair in t["rooms"] for r in pair)
        return out

    def test_no_forbidden_term_in_any_copy(self):
        blob = " ".join(self._all_strings()).lower()
        for term in content.FORBIDDEN:
            self.assertNotIn(term.lower(), blob, f"forbidden term present: {term}")

    def test_no_price_digits_pattern(self):
        blob = " ".join(self._all_strings())
        self.assertIsNone(re.search(r"(₹|Rs\.?\s*\d|\d+\s*(lakh|lac|cr))", blob, re.I))


class TestStructure(unittest.TestCase):
    def test_eight_sections_in_spec_order(self):
        ids = [s["id"] for s in content.SECTIONS]
        self.assertEqual(ids, ["cover", "project", "render", "plans",
                               "layout", "specs", "location", "contact"])

    def test_unit_types_cover_all_48_plots(self):
        self.assertEqual(content.UNIT_TYPES["A"]["plots"], "Plots 01–06")
        self.assertEqual(content.UNIT_TYPES["B"]["plots"], "Plots 07–48")

    def test_type_b_dimensions_match_the_layout_drawing(self):
        rooms = dict(content.UNIT_TYPES["B"]["rooms"])
        self.assertEqual(rooms["Kitchen"], "10'-6\" × 8'-1½\"")
        self.assertEqual(rooms["Master bedroom"], "11'-0\" × 12'-6\"")
        self.assertEqual(rooms["Second bedroom"], "10'-1½\" × 10'-7½\"")
        self.assertEqual(rooms["Attached toilet"], "6'-0\" × 5'-0\"")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -I -m unittest tests.test_content -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'build'`

- [ ] **Step 3: Write minimal implementation**

```python
# build/__init__.py  (empty file)
```

```python
# build/content.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -I -m unittest tests.test_content -v`
Expected: PASS, 14 tests

- [ ] **Step 5: Commit**

```bash
git add build/__init__.py build/content.py tests/test_content.py
git commit -m "feat: add Lake Tree Avenue content module with CTA link builders"
```

---

### Task 2: Plot hotspot table

**Files:**
- Create: `build/plots.py`
- Test: `tests/test_plots.py`

**Interfaces:**
- Consumes: `REV.LAYOUT - 07-10-2026.pdf` at repo root
- Produces:
  - `LAYOUT_PDF: str` — path constant
  - `Hotspot` — `dataclass(number: int, x: float, y: float, w: float, h: float, unit_type: str)` with all geometry normalised to 0–1 of the layout page, `x`/`y` being the **top-left** corner
  - `extract_label_centres(pdf_path: str) -> dict[int, tuple[float, float]]` — PDF points
  - `MANUAL_CENTRES: dict[int, tuple[float, float]]` — PDF points for the eight unlabelled plots
  - `hotspots() -> tuple[Hotspot, ...]` — 48 entries, ordered by plot number

Background: 40 of 48 plot numbers carry a text layer at ~29 × 26 pt. Plots 07–13 and 42 are outlined vector art with no extractable text; their centres below were read off a render of the page and are in PDF points on a 1684 × 2384 pt page.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_plots.py
import unittest
import fitz
from build import plots


class TestExtraction(unittest.TestCase):
    def test_extracts_forty_labelled_plots(self):
        found = plots.extract_label_centres(plots.LAYOUT_PDF)
        self.assertEqual(len(found), 40)

    def test_extraction_misses_exactly_the_eight_known_gaps(self):
        found = plots.extract_label_centres(plots.LAYOUT_PDF)
        missing = sorted(set(range(1, 49)) - set(found))
        self.assertEqual(missing, [7, 8, 9, 10, 11, 12, 13, 42])

    def test_manual_centres_fill_exactly_the_gaps(self):
        self.assertEqual(sorted(plots.MANUAL_CENTRES), [7, 8, 9, 10, 11, 12, 13, 42])


class TestHotspots(unittest.TestCase):
    def setUp(self):
        self.spots = plots.hotspots()

    def test_all_forty_eight_plots_present_once_in_order(self):
        self.assertEqual([s.number for s in self.spots], list(range(1, 49)))

    def test_every_hotspot_is_inside_the_page(self):
        for s in self.spots:
            self.assertGreaterEqual(s.x, 0.0, f"plot {s.number}")
            self.assertGreaterEqual(s.y, 0.0, f"plot {s.number}")
            self.assertLessEqual(s.x + s.w, 1.0, f"plot {s.number}")
            self.assertLessEqual(s.y + s.h, 1.0, f"plot {s.number}")

    def test_hotspots_have_positive_area(self):
        for s in self.spots:
            self.assertGreater(s.w, 0.0)
            self.assertGreater(s.h, 0.0)

    def test_unit_type_split_matches_the_spec(self):
        by_num = {s.number: s.unit_type for s in self.spots}
        self.assertTrue(all(by_num[n] == "A" for n in range(1, 7)))
        self.assertTrue(all(by_num[n] == "B" for n in range(7, 49)))

    def test_no_two_hotspots_overlap_by_more_than_a_tenth(self):
        def area(a):
            return a.w * a.h

        def overlap(a, b):
            dx = min(a.x + a.w, b.x + b.w) - max(a.x, b.x)
            dy = min(a.y + a.h, b.y + b.h) - max(a.y, b.y)
            return max(dx, 0) * max(dy, 0)

        for i, a in enumerate(self.spots):
            for b in self.spots[i + 1:]:
                self.assertLess(overlap(a, b), 0.10 * min(area(a), area(b)),
                                f"plots {a.number} and {b.number} overlap")

    def test_each_hotspot_contains_its_own_label_where_a_label_exists(self):
        page = fitz.open(plots.LAYOUT_PDF)[0]
        pw, ph = page.rect.width, page.rect.height
        found = plots.extract_label_centres(plots.LAYOUT_PDF)
        by_num = {s.number: s for s in self.spots}
        for n, (cx, cy) in found.items():
            s = by_num[n]
            self.assertTrue(s.x <= cx / pw <= s.x + s.w, f"plot {n} label outside x")
            self.assertTrue(s.y <= cy / ph <= s.y + s.h, f"plot {n} label outside y")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -I -m unittest tests.test_plots -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'build.plots'`

- [ ] **Step 3: Write minimal implementation**

```python
# build/plots.py
"""Plot number -> hotspot rectangle, normalised to the layout page.

The same table drives the HTML SVG overlay and the PDF link annotations.
"""
import os
import re
from dataclasses import dataclass

import fitz

LAYOUT_PDF = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "REV.LAYOUT - 07-10-2026.pdf",
)

# Plot labels are drawn at ~29 x 26 pt. Dimension callouts are ~7 x 5 pt,
# so a height floor of 15 pt separates them cleanly.
_LABEL_MIN_HEIGHT = 15.0

# Plots 07-13 and 42 are outlined vector art with no text layer. Centres read
# off a render of the page, in PDF points (page is 1684 x 2384 pt).
MANUAL_CENTRES = {
    7: (610.0, 1228.0),
    8: (705.0, 1228.0),
    9: (792.0, 1228.0),
    10: (878.0, 1228.0),
    11: (963.0, 1228.0),
    12: (1247.0, 1228.0),
    13: (1333.0, 1228.0),
    42: (846.0, 405.0),
}

# Hotspot box drawn around a label centre, in PDF points.
# Plots 01-06 are a vertical column of wide, short cells; the rest are rows of
# narrow, tall cells.
_COLUMN_PLOTS = range(1, 7)
_COLUMN_BOX = (118.0, 82.0)   # w, h
_ROW_BOX = (84.0, 150.0)      # w, h


@dataclass(frozen=True)
class Hotspot:
    number: int
    x: float
    y: float
    w: float
    h: float
    unit_type: str


def extract_label_centres(pdf_path: str) -> dict[int, tuple[float, float]]:
    page = fitz.open(pdf_path)[0]
    centres: dict[int, tuple[float, float]] = {}
    for x0, y0, x1, y1, text, *_ in page.get_text("words"):
        if not re.fullmatch(r"\d{2}", text):
            continue
        if (y1 - y0) < _LABEL_MIN_HEIGHT:
            continue
        number = int(text)
        if 1 <= number <= 48:
            centres[number] = ((x0 + x1) / 2, (y0 + y1) / 2)
    return centres


def hotspots() -> tuple[Hotspot, ...]:
    page = fitz.open(LAYOUT_PDF)[0]
    pw, ph = page.rect.width, page.rect.height

    centres = extract_label_centres(LAYOUT_PDF)
    centres.update(MANUAL_CENTRES)

    out = []
    for number in range(1, 49):
        cx, cy = centres[number]
        bw, bh = _COLUMN_BOX if number in _COLUMN_PLOTS else _ROW_BOX
        x = (cx - bw / 2) / pw
        y = (cy - bh / 2) / ph
        out.append(Hotspot(
            number=number,
            x=max(0.0, x),
            y=max(0.0, y),
            w=min(bw / pw, 1.0 - max(0.0, x)),
            h=min(bh / ph, 1.0 - max(0.0, y)),
            unit_type="A" if number in _COLUMN_PLOTS else "B",
        ))
    return tuple(out)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -I -m unittest tests.test_plots -v`
Expected: PASS, 9 tests. If `test_no_two_hotspots_overlap_by_more_than_a_tenth` fails, shrink `_ROW_BOX` height until it passes — do not widen the overlap allowance.

- [ ] **Step 5: Commit**

```bash
git add build/plots.py tests/test_plots.py
git commit -m "feat: derive 48 plot hotspots from the revised layout drawing"
```

---

### Task 3: Image pipeline

**Files:**
- Create: `build/assets.py`
- Test: `tests/test_assets.py`

**Interfaces:**
- Consumes: `images/174E3041-9C9A-4984-BD36-BA254A0E98E2.PNG` (logo), `images/LAKE TREE.PNG` (render), `REV.LAYOUT - 07-10-2026.pdf`
- Produces:
  - `logo_png(height: int = 420) -> bytes` — trimmed, transparent-free PNG
  - `render_jpeg(width: int = 1600, quality: int = 78) -> bytes` — letterbox bars removed
  - `layout_png(width: int = 1600) -> bytes` — full layout page rasterised
  - `plan_crops() -> dict[str, bytes]` — keys `A`, `B`, `elevation`; JPEG bytes cropped from the layout page's drawing strip
  - `data_uri(blob: bytes, mime: str) -> str`

The render `LAKE TREE.PNG` is 1080 × 1080 with white letterbox bars top and bottom; the photograph occupies roughly the middle 70%. Trim by scanning rows for near-white content rather than hard-coding, so a replacement image still works.

The layout page's bottom strip carries two floor-plan sets and an elevation pair. In fractions of the 1684 × 2384 pt page: Type A plans `x 0.090–0.310, y 0.775–0.895`; Type B plans `x 0.345–0.565, y 0.775–0.895`; elevations `x 0.610–0.840, y 0.775–0.895`. Verify these visually in Task 6 and adjust if a crop clips a drawing.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_assets.py
import io
import unittest
from PIL import Image
from build import assets


def _open(blob):
    return Image.open(io.BytesIO(blob))


class TestLogo(unittest.TestCase):
    def test_logo_is_png_at_requested_height(self):
        img = _open(assets.logo_png(height=420))
        self.assertEqual(img.format, "PNG")
        self.assertEqual(img.height, 420)

    def test_logo_under_budget(self):
        self.assertLess(len(assets.logo_png()), 400_000)


class TestRender(unittest.TestCase):
    def setUp(self):
        self.blob = assets.render_jpeg(width=1600)
        self.img = _open(self.blob)

    def test_render_is_jpeg_at_requested_width(self):
        self.assertEqual(self.img.format, "JPEG")
        self.assertEqual(self.img.width, 1600)

    def test_letterbox_bars_are_trimmed(self):
        # Source is square with white bars; trimmed result must be wider than tall.
        self.assertGreater(self.img.width, self.img.height)

    def test_top_and_bottom_edges_are_not_blank_white(self):
        px = self.img.convert("RGB")
        for y in (0, px.height - 1):
            row = [px.getpixel((x, y)) for x in range(0, px.width, 40)]
            self.assertFalse(all(min(p) > 247 for p in row),
                             f"row {y} is still blank white")

    def test_render_under_budget(self):
        self.assertLess(len(self.blob), 900_000)


class TestLayout(unittest.TestCase):
    def test_layout_png_matches_page_aspect(self):
        img = _open(assets.layout_png(width=1600))
        self.assertEqual(img.width, 1600)
        # Page is 1684 x 2384 pt -> aspect 1.4157
        self.assertAlmostEqual(img.height / img.width, 2384 / 1684, places=2)

    def test_layout_under_budget(self):
        self.assertLess(len(assets.layout_png()), 2_500_000)


class TestPlanCrops(unittest.TestCase):
    def setUp(self):
        self.crops = assets.plan_crops()

    def test_three_crops_produced(self):
        self.assertEqual(sorted(self.crops), ["A", "B", "elevation"])

    def test_crops_are_non_trivial_images(self):
        for key, blob in self.crops.items():
            img = _open(blob)
            self.assertGreater(img.width, 300, key)
            self.assertGreater(img.height, 150, key)

    def test_crops_are_not_blank(self):
        for key, blob in self.crops.items():
            img = _open(blob).convert("L")
            extrema = img.getextrema()
            self.assertLess(extrema[0], 200, f"{key} crop looks blank")


class TestDataUri(unittest.TestCase):
    def test_data_uri_shape(self):
        uri = assets.data_uri(b"abc", "image/png")
        self.assertTrue(uri.startswith("data:image/png;base64,"))
        self.assertNotIn("\n", uri)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -I -m unittest tests.test_assets -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'build.assets'`

- [ ] **Step 3: Write minimal implementation**

```python
# build/assets.py
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
LOGO_SRC = os.path.join(ROOT, "images", "174E3041-9C9A-4984-BD36-BA254A0E98E2.PNG")
RENDER_SRC = os.path.join(ROOT, "images", "LAKE TREE.PNG")
LAYOUT_SRC = os.path.join(ROOT, "REV.LAYOUT - 07-10-2026.pdf")

_WHITE = 247  # a channel value above this counts as blank paper

PLAN_BOXES = {
    "A": (0.090, 0.775, 0.310, 0.895),
    "B": (0.345, 0.775, 0.565, 0.895),
    "elevation": (0.610, 0.775, 0.840, 0.895),
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
    img = Image.open(LOGO_SRC).convert("RGB")
    img = _trim_white(img)
    ratio = height / img.height
    img = img.resize((max(1, round(img.width * ratio)), height), Image.LANCZOS)
    return _encode(img, "PNG", optimize=True)


def render_jpeg(width: int = 1600, quality: int = 78) -> bytes:
    img = Image.open(RENDER_SRC).convert("RGB")
    img = _trim_white(img)
    ratio = width / img.width
    img = img.resize((width, max(1, round(img.height * ratio))), Image.LANCZOS)
    return _encode(img, "JPEG", quality=quality, optimize=True, progressive=True)


def _layout_pixmap(width: int) -> Image.Image:
    page = fitz.open(LAYOUT_SRC)[0]
    zoom = width / page.rect.width
    pm = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    return Image.frombytes("RGB", (pm.width, pm.height), pm.samples)


def layout_png(width: int = 1600) -> bytes:
    return _encode(_layout_pixmap(width), "PNG", optimize=True)


def plan_crops(width: int = 2400, quality: int = 82) -> dict[str, bytes]:
    full = _layout_pixmap(width)
    w, h = full.size
    out = {}
    for key, (x0, y0, x1, y1) in PLAN_BOXES.items():
        box = (round(x0 * w), round(y0 * h), round(x1 * w), round(y1 * h))
        out[key] = _encode(full.crop(box), "JPEG", quality=quality, optimize=True)
    return out


def data_uri(blob: bytes, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(blob).decode("ascii")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -I -m unittest tests.test_assets -v`
Expected: PASS, 13 tests.

Two budgets are likely to bite. If `test_render_under_budget` fails, lower `quality` to 72 before lowering `width`. If `test_layout_under_budget` fails — the layout is a dense CAD drawing and a 1600 px PNG of it can exceed 2.5 MB — reduce the default `width` to 1280 rather than switching to JPEG, because JPEG artefacts smear the thin plot boundary lines that the hotspots must align to.

- [ ] **Step 5: Commit**

```bash
git add build/assets.py tests/test_assets.py
git commit -m "feat: add image pipeline with letterbox trim and size budgets"
```

---

### Task 4: Single-file HTML builder

**Files:**
- Create: `build/build_html.py`
- Test: `tests/test_html.py`

**Interfaces:**
- Consumes: `build.content`, `build.plots.hotspots`, `build.assets`
- Produces: `render_html() -> str`, `write(path: str) -> str` (returns the path written)

Design notes for the implementer: one `<style>` block, no scripts beyond a single inline `<script>` using only `document.querySelector` and `classList` — no `fetch`, no modules, no service worker, because the file is opened from `file://` on phones. The plot map is an `<svg viewBox="0 0 1000 1416">` layered over the layout image with `<a href>` wrapping each `<rect>`; SVG anchors work without any JavaScript, so the map still functions if scripts are blocked. Colour tokens: cream `#FBF3E7`, terracotta `#C0824F`, ink `#2E2B28`, slate `#6F7275`; define them on `:root`, declare `color-scheme: light`, and give `body` an explicit light background. No dark mode and no dark-ground sections anywhere — the owner asked for white or light throughout. Accent blocks use terracotta on cream, never ink on a dark fill.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_html.py
import re
import unittest
from build import build_html, content, plots


class TestHtml(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = build_html.render_html()

    def test_has_title_and_viewport(self):
        self.assertIn("<title>Lake Tree Avenue</title>", self.html)
        self.assertIn('name="viewport"', self.html)

    def test_no_external_subresources(self):
        # Only tel:, mailto:, wa.me and the Maps link may leave the document.
        for m in re.finditer(r'(?:src|href)\s*=\s*"([^"]+)"', self.html):
            url = m.group(1)
            if url.startswith(("#", "data:", "tel:", "mailto:")):
                continue
            self.assertTrue(
                url.startswith("https://wa.me/")
                or url.startswith("https://www.google.com/maps/"),
                f"external subresource: {url}",
            )

    def test_no_dynamic_fetch_apis(self):
        for banned in ("fetch(", "XMLHttpRequest", "serviceWorker",
                       'type="module"', "import("):
            self.assertNotIn(banned, self.html, f"file:// hostile API: {banned}")

    def test_all_forty_eight_plot_links_present(self):
        for n in range(1, 49):
            self.assertIn(content.plot_wa_link(n), self.html, f"plot {n} link missing")

    def test_hotspot_rect_count_matches_plot_count(self):
        self.assertEqual(len(re.findall(r"<rect[^>]*class=\"plot\"", self.html)),
                         len(plots.hotspots()))

    def test_primary_ctas_present(self):
        self.assertIn(content.tel_link(), self.html)
        self.assertIn(content.mail_link(), self.html)
        self.assertIn(content.PROJECT["maps_url"], self.html)

    def test_phone_readable_as_text_not_only_as_link(self):
        self.assertIn(content.PROJECT["phone_display"], self.html)

    def test_no_forbidden_terms(self):
        low = self.html.lower()
        for term in content.FORBIDDEN:
            self.assertNotIn(term.lower(), low, f"forbidden term: {term}")

    def test_no_price(self):
        self.assertIsNone(re.search(r"(₹|Rs\.?\s*\d)", self.html))
        self.assertIn("Price on call", self.html)

    def test_light_only_with_explicit_body_background(self):
        self.assertIn("color-scheme: light", self.html)
        self.assertNotIn("prefers-color-scheme: dark", self.html)
        self.assertRegex(self.html, r"body\s*\{[^}]*background")

    def test_no_dark_page_ground(self):
        # Every declared background must be light. Guards against a dark hero
        # or footer slipping in.
        import re as _re
        for hexcode in _re.findall(r"background[^;:]*:\s*#([0-9a-fA-F]{6})", self.html):
            r, g, b = (int(hexcode[i:i + 2], 16) for i in (0, 2, 4))
            luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
            self.assertGreater(luma, 120, f"dark background #{hexcode}")

    def test_under_size_budget(self):
        self.assertLess(len(self.html.encode("utf-8")), 6 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -I -m unittest tests.test_html -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'build.build_html'`

- [ ] **Step 3: Write the implementation**

This step is prose rather than a literal code block by deliberate exception: the output is a designed page, and fixing its exact markup here would lock in layout decisions made without ever seeing it render. The implementer invokes the `frontend-design` skill, and the tests in Step 1 are the hard contract the design must satisfy.

Build `render_html()` to emit, in order: the eight sections from `content.SECTIONS`; the render as an inlined `<img>`; the Type A / Type B plan crops with a CSS-only toggle (two radio inputs and sibling selectors — no JavaScript); the layout image with the SVG hotspot overlay built from `plots.hotspots()`, each `<rect class="plot">` wrapped in `<a href="{content.plot_wa_link(n)}" target="_blank">` and carrying `<title>Plot {n:02d} · Type {t}</title>` for the native tooltip; the spec and amenity lists; the location block with the Maps link; and the contact block with `phone_display` as visible text alongside the `tel:` link. Append a fixed bottom action bar with Call, WhatsApp and Directions. `write(path)` creates the parent directory and writes UTF-8.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -I -m unittest tests.test_html -v`
Expected: PASS, 12 tests

- [ ] **Step 5: Commit**

```bash
git add build/build_html.py tests/test_html.py
git commit -m "feat: render single-file offline HTML brochure with plot hotspots"
```

---

### Task 5: Interactive PDF builder

**Files:**
- Create: `build/build_pdf.py`
- Test: `tests/test_pdf.py`

**Interfaces:**
- Consumes: `build.content`, `build.plots.hotspots`, `build.assets`
- Produces: `PAGE_SIZE = (842.0, 595.0)`, `build_doc() -> fitz.Document`, `write(path: str) -> str`

Design notes: pages are A4 landscape, 842 × 595 pt, matching the existing brochure geometry. Use base-14 fonts only (`helv`, `hebo`, `tiro`) so no font files are needed. Each page gets a footer strip drawn with `insert_textbox` showing `phone_display`, the email and the site line as **visible text**, with `page.insert_link` rectangles over each. The layout page scales `assets.layout_png()` to fit, then maps every hotspot's normalised rect into page coordinates for `insert_link(kind=fitz.LINK_URI)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_pdf.py
import os
import re
import tempfile
import unittest

import fitz
from build import build_pdf, content


class TestPdf(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = build_pdf.build_doc()
        fd, cls.path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        cls.doc.save(cls.path, deflate=True, garbage=4)

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.path)

    def test_eight_pages_a4_landscape(self):
        self.assertEqual(self.doc.page_count, 8)
        for page in self.doc:
            self.assertAlmostEqual(page.rect.width, 842.0, places=0)
            self.assertAlmostEqual(page.rect.height, 595.0, places=0)

    def _uris(self, page):
        return [l.get("uri", "") for l in page.get_links()
                if l["kind"] == fitz.LINK_URI]

    def test_every_page_carries_the_four_footer_ctas(self):
        for i, page in enumerate(self.doc):
            uris = self._uris(page)
            self.assertIn(content.tel_link(), uris, f"page {i+1} missing tel")
            self.assertIn(content.mail_link(), uris, f"page {i+1} missing mail")
            self.assertIn(content.PROJECT["maps_url"], uris, f"page {i+1} missing maps")
            self.assertTrue(any(u.startswith("https://wa.me/") for u in uris),
                            f"page {i+1} missing whatsapp")

    def test_all_link_rects_lie_inside_their_page(self):
        for i, page in enumerate(self.doc):
            for link in page.get_links():
                r = fitz.Rect(link["from"])
                self.assertTrue(r.is_valid and not r.is_empty, f"page {i+1} empty rect")
                self.assertTrue(r in page.rect, f"page {i+1} rect outside page: {r}")

    def test_layout_page_has_all_forty_eight_distinct_plot_links(self):
        page = self.doc[4]  # section order: cover, project, render, plans, layout
        plot_uris = {u for u in self._uris(page) if "Plot%20" in u}
        self.assertEqual(len(plot_uris), 48)
        for n in range(1, 49):
            self.assertIn(content.plot_wa_link(n), plot_uris, f"plot {n} missing")

    def test_contact_details_are_readable_text_not_only_links(self):
        # WhatsApp's in-app viewer often drops annotations; the number must still
        # be dialable by hand.
        text = "\n".join(p.get_text() for p in self.doc)
        self.assertIn(content.PROJECT["phone_display"], text)
        self.assertIn(content.PROJECT["email"], text)

    def test_no_forbidden_terms_in_extracted_text(self):
        text = "\n".join(p.get_text() for p in self.doc).lower()
        for term in content.FORBIDDEN:
            self.assertNotIn(term.lower(), text, f"forbidden term: {term}")

    def test_no_price_in_extracted_text(self):
        text = "\n".join(p.get_text() for p in self.doc)
        self.assertIsNone(re.search(r"(₹|Rs\.?\s*\d)", text))

    def test_under_size_budget(self):
        self.assertLess(os.path.getsize(self.path), 8 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -I -m unittest tests.test_pdf -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'build.build_pdf'`

- [ ] **Step 3: Write the implementation**

Prose rather than a literal code block, for the same reason as Task 4: page composition is a design decision best made against a render. The tests in Step 1 are the hard contract.

Implement `build_doc()` to create eight pages in `content.SECTIONS` order, each drawing its own content and then calling a shared `_footer(page)` helper that writes the visible contact line and attaches the four CTA links. The layout page additionally places `assets.layout_png()` with `page.insert_image` into a computed `fitz.Rect` and then, for each hotspot, computes `fitz.Rect(img.x0 + s.x*img.width, img.y0 + s.y*img.height, ...)` and calls `page.insert_link({"kind": fitz.LINK_URI, "from": rect, "uri": content.plot_wa_link(s.number)})`. `write(path)` saves with `deflate=True, garbage=4`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -I -m unittest tests.test_pdf -v`
Expected: PASS, 8 tests

- [ ] **Step 5: Commit**

```bash
git add build/build_pdf.py tests/test_pdf.py
git commit -m "feat: render interactive PDF brochure with per-plot link annotations"
```

---

### Task 6: Build entry point and visual verification

**Files:**
- Create: `build.py`, `build/qa.py`
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: `build.build_html.write`, `build.build_pdf.write`, `build.plots.hotspots`, `build.assets.layout_png`
- Produces: `build/qa.py:hotspot_overlay(path: str) -> str`; `build.py:main() -> int`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_build.py
import os
import tempfile
import unittest

from build import qa


class TestQaOverlay(unittest.TestCase):
    def test_overlay_is_written_and_non_trivial(self):
        with tempfile.TemporaryDirectory() as d:
            path = qa.hotspot_overlay(os.path.join(d, "qa.png"))
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 100_000)


class TestArtefactsOnDisk(unittest.TestCase):
    """Runs against dist/ after `python3 -I build.py`."""

    def setUp(self):
        self.html = os.path.join("dist", "Lake-Tree-Avenue.html")
        self.pdf = os.path.join("dist", "Lake-Tree-Avenue-eBrochure.pdf")
        if not (os.path.exists(self.html) and os.path.exists(self.pdf)):
            self.skipTest("run `python3 -I build.py` first")

    def test_html_within_budget(self):
        self.assertLess(os.path.getsize(self.html), 6 * 1024 * 1024)

    def test_pdf_within_budget(self):
        self.assertLess(os.path.getsize(self.pdf), 8 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -I -m unittest tests.test_build -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'build.qa'`

- [ ] **Step 3: Write the implementation**

```python
# build/qa.py
"""Draw every hotspot over the layout so placement can be eyeballed."""
import io
import os

from PIL import Image, ImageDraw

from build import assets, plots


def hotspot_overlay(path: str, width: int = 1600) -> str:
    img = Image.open(io.BytesIO(assets.layout_png(width))).convert("RGB")
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for s in plots.hotspots():
        box = (s.x * w, s.y * h, (s.x + s.w) * w, (s.y + s.h) * h)
        draw.rectangle(box, outline=(220, 20, 60), width=3)
        draw.text((box[0] + 5, box[1] + 5), f"{s.number:02d}", fill=(220, 20, 60))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    img.save(path, "PNG", optimize=True)
    return path
```

```python
# build.py
"""Build both Lake Tree Avenue artefacts into dist/."""
import os
import sys

from build import build_html, build_pdf, qa

DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")


def main() -> int:
    os.makedirs(DIST, exist_ok=True)
    html = build_html.write(os.path.join(DIST, "Lake-Tree-Avenue.html"))
    pdf = build_pdf.write(os.path.join(DIST, "Lake-Tree-Avenue-eBrochure.pdf"))
    overlay = qa.hotspot_overlay(os.path.join(DIST, "qa-hotspots.png"))
    for p in (html, pdf, overlay):
        print(f"{os.path.getsize(p) / 1024 / 1024:6.2f} MB  {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the build and the full suite**

Run: `python3 -I build.py && python3 -I -m unittest discover -s tests -v`
Expected: three files reported under budget; all tests PASS.

- [ ] **Step 5: Visual verification — hotspots**

Open `dist/qa-hotspots.png` and confirm all 48 red boxes land inside their own plot, paying particular attention to plots 07, 08, 09, 10, 11, 12, 13 and 42, whose centres were placed by hand. Correct any stray entry in `plots.MANUAL_CENTRES` and re-run.

- [ ] **Step 6: Visual verification — pages**

Render every PDF page to PNG and review each one for clipped text, overlapping blocks or a stretched image:

```bash
python3 -I -c "
import fitz
d = fitz.open('dist/Lake-Tree-Avenue-eBrochure.pdf')
for i, p in enumerate(d):
    p.get_pixmap(dpi=96).save(f'dist/qa-page{i+1}.png')
print('rendered', d.page_count, 'pages')
"
```

Then open `dist/Lake-Tree-Avenue.html` in a browser at 360 px width and at desktop width; confirm no horizontal scroll, the plan toggle works, and tapping a plot opens WhatsApp with the right plot number.

- [ ] **Step 7: Commit**

```bash
git add build.py build/qa.py tests/test_build.py dist/
git commit -m "feat: add build entry point, hotspot QA overlay and generated artefacts"
```

---

## Open items carried from the spec

These need the owner's input before the artefacts are sent to any buyer. None block implementation.

1. **RERA.** Built with no RERA line per the owner's instruction. Confirm with counsel before the Meta campaign goes live.
2. **Waghodia Road landmarks.** The location section ships with the site address and corridor only. A landmark list for Kamlapura needs owner confirmation before publishing.
3. **Google Maps pin.** `PROJECT["maps_url"]` currently searches for "Spunpipe & Construction Co, Waghodia Road, Vadodara". Replace with an exact dropped-pin URL when the owner supplies one.
4. **Type A dimensions.** Only four rows are known from the drawing. Complete them if the owner supplies the full Type A schedule.
