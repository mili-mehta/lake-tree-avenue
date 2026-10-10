import re, unittest
from urllib.parse import unquote
from build import content, copy

# The schedule is keyed, not labelled, so that a sheet can find its rows
# in any language. These tests still read in English, so they resolve the
# labels through the English module -- which also proves the resolver
# reproduces exactly what the brochure said before it learned Hindi.
EN = copy.for_locale("en")


def _rooms(key):
    """One unit's schedule as an English reader sees it."""
    return dict(content.unit_rooms(content.UNIT_TYPES[key], EN))


class TestFacts(unittest.TestCase):
    def test_phone_is_e164_with_india_country_code(self):
        self.assertEqual(content.PROJECT["phone_e164"], "+918758756666")

    def test_phone_display_is_grouped(self):
        self.assertEqual(content.PROJECT["phone_display"], "+91 87587 56666")

    def test_tel_link_carries_country_code(self):
        self.assertEqual(content.tel_link(), "tel:+918758756666")

    def test_wa_link_uses_bare_digits_no_plus(self):
        self.assertTrue(content.wa_link("hi").startswith("https://wa.me/918758756666?text="))

    def test_mail_link(self):
        self.assertEqual(content.mail_link(), "mailto:info@laketreeavenue.com")

    def test_website_is_printed_bare_and_linked_with_a_scheme(self):
        self.assertEqual(content.PROJECT["website_display"],
                         "laketreeavenue.com")
        self.assertEqual(content.PROJECT["website_url"],
                         "https://laketreeavenue.com")

    def test_social_handle_is_the_same_on_both_networks(self):
        # One handle covers Instagram and Facebook, so a caption or a print
        # footer can name it once.
        self.assertEqual(content.PROJECT["social_handle"], "@laketreeavenue")

    def test_social_urls_point_at_that_handle(self):
        for key in ("instagram_url", "facebook_url"):
            url = content.PROJECT[key]
            self.assertTrue(url.startswith("https://"), f"{key} not https")
            self.assertIn("laketreeavenue", url, f"{key} is not the handle")

    def test_developer_is_tam(self):
        self.assertEqual(content.PROJECT["developer"], "TAM Developers")

    def test_no_partner_name_is_available_to_the_renderers(self):
        # Partner names are internal. Keeping them out of PROJECT entirely
        # means a renderer cannot print them by accident.
        self.assertNotIn("partners", content.PROJECT)

    def test_private_names_are_guarded(self):
        for name in ("Dhruv Talati", "Shalin Talati", "Kinjal Mehta"):
            self.assertIn(name, content.PRIVATE_NAMES)

    def test_guard_catches_a_partner_name_however_it_is_broken_up(self):
        self.assertIn("Dhruv Talati",
                      content.forbidden_hits("built by Dhruv\nTalati and co"))
        self.assertIn("Shalin Talati",
                      content.forbidden_hits("<td>Shalin</td><td>Talati</td>"))

    def test_guard_catches_a_bare_partner_surname(self):
        self.assertIn("Talati", content.forbidden_hits("a Talati family project"))

    def test_credit_line_names_the_firm_only(self):
        self.assertEqual(EN.CREDIT, "A project by TAM Developers")


class TestWhatsAppEncoding(unittest.TestCase):
    def test_apostrophe_and_spaces_are_encoded(self):
        link = content.wa_link("Hi, I'm interested")
        self.assertNotIn(" ", link)
        self.assertNotIn("'", link)

    def test_message_round_trips(self):
        msg = "Hi, I'm interested in Plot 07 at Lake Tree Avenue."
        link = content.wa_link(msg)
        self.assertEqual(unquote(link.split("text=", 1)[1]), msg)



class TestSupersededFacts(unittest.TestCase):
    def _all_strings(self):
        out = []
        for v in content.PROJECT.values():
            out.append(str(v))
        # Every language, not just English: a superseded term is just as
        # damaging in Gujarati, and the guard only earns its keep if it
        # sees the copy a buyer actually reads.
        for code in copy.LOCALES:
            words = copy.for_locale(code)
            out += [text for _, text in copy.strings(words)]
            for key in content.UNIT_TYPES:
                out += [v for pair in content.unit_rooms(
                    content.UNIT_TYPES[key], words) for v in pair]
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
        self.assertEqual(list(content.SECTION_IDS),
                         ["cover", "project", "plans",
                          "layout", "specs", "location", "contact",
                          "disclaimers"])
        for code in copy.LOCALES:
            ids = [s["id"] for s in copy.for_locale(code).SECTIONS]
            self.assertEqual(ids, list(content.SECTION_IDS), code)

    def test_unit_types_cover_all_48_plots(self):
        self.assertEqual(content.plots_label(content.UNIT_TYPES["A"], EN),
                         "Plots 01–06")
        self.assertEqual(content.plots_label(content.UNIT_TYPES["B"], EN),
                         "Plots 07–48")
        # The numbers are the same in every language; only the word moves.
        for code in copy.LOCALES:
            words = copy.for_locale(code)
            self.assertIn("07–48",
                          content.plots_label(content.UNIT_TYPES["B"], words))

    def test_type_b_dimensions_match_the_layout_drawing(self):
        rooms = _rooms("B")
        self.assertEqual(rooms["Kitchen"], "10'-6\" × 8'-1½\"")
        self.assertEqual(rooms["Master bedroom"], "11'-0\" × 12'-6\"")
        self.assertEqual(rooms["Second bedroom"], "10'-1½\" × 10'-7½\"")
        self.assertEqual(rooms["Living room / dining"], "17'-4½\" × 15'-0\"")

    def test_type_a_first_floor_dimensions_match_the_drawing(self):
        # Read off the plots 01-06 first floor sheet: the front bedroom and
        # its toilet are narrower than Type B's.
        rooms = _rooms("A")
        self.assertEqual(rooms["Master bedroom"], "10'-9½\" × 12'-6\"")
        self.assertEqual(rooms["Second bedroom"], "10'-9½\" × 11'-7½\"")
        self.assertEqual(rooms["Attached toilet"], "5'-6\" × 5'-0\"")
        self.assertEqual(rooms["Second attached toilet"], "4'-0\" × 7'-0\"")

    def test_type_a_ground_floor_dimensions_match_the_drawing(self):
        rooms = _rooms("A")
        self.assertEqual(rooms["Living room / dining"], "16'-8\" × 15'-0\"")
        self.assertEqual(rooms["Kitchen"], "9'-9½\" × 9'-1½\"")
        self.assertEqual(rooms["Ground floor toilet"], "4'-6\" × 5'-0\"")

    def test_both_types_are_drawn_ground_floor_then_first_floor(self):
        for key, unit in content.UNIT_TYPES.items():
            sheets = unit["sheets"]
            self.assertEqual([s["key"] for s in sheets], ["ground", "first"],
                             f"Type {key} sheet order")
            self.assertEqual([EN.SHEET_CAPTIONS[s["key"]] for s in sheets],
                             ["Ground floor", "First floor"], f"Type {key}")

    def test_every_row_sits_on_exactly_one_sheet(self):
        # A row on neither sheet never reaches the PDF; a row on both is
        # printed twice with no drawing to justify it.
        for key, unit in content.UNIT_TYPES.items():
            listed = [name for sheet in unit["sheets"] for name in sheet["rows"]]
            self.assertEqual(sorted(listed),
                             sorted(name for name, _ in unit["rooms"]),
                             f"Type {key} sheets do not cover its schedule")
            self.assertEqual(len(listed), len(set(listed)),
                             f"Type {key} repeats a row across both sheets")

    def test_sheet_rows_resolves_in_sheet_order(self):
        unit = content.UNIT_TYPES["A"]
        rows = content.sheet_rows(unit, unit["sheets"][1], EN)
        self.assertEqual(rows[0], ("Master bedroom", "10'-9½\" × 12'-6\""))
        self.assertEqual([name for name, _ in rows],
                         [EN.ROOM_LABELS[k] for k in unit["sheets"][1]["rows"]])

    def test_sheet_rows_rejects_a_row_the_unit_does_not_have(self):
        unit = content.UNIT_TYPES["A"]
        with self.assertRaises(KeyError):
            content.sheet_rows(unit, {"key": "x", "rows": ("wine_cellar",)},
                               EN)

    def test_bedrooms_are_scheduled_on_the_upper_floor(self):
        # Both bedrooms are drawn upstairs in both types. Listing one
        # beside the ground floor plan contradicts the drawing next to it.
        for key, unit in content.UNIT_TYPES.items():
            ground = [EN.ROOM_LABELS[r] for r in unit["sheets"][0]["rows"]]
            self.assertFalse([r for r in ground if "bedroom" in r.lower()],
                             f"Type {key} schedules a bedroom on the ground floor")

    def test_both_types_state_a_plot_area_in_square_feet(self):
        for key, unit in content.UNIT_TYPES.items():
            area = _rooms(key).get("Plot area")
            self.assertIsNotNone(area, f"Type {key} states no plot area")
            self.assertIn("sq ft", area, f"Type {key} area is not in square feet")

    def test_plot_area_is_the_range_the_developer_gave(self):
        self.assertEqual(_rooms("A")["Plot area"], "703 to 1041 sq ft")
        self.assertEqual(_rooms("B")["Plot area"], "707 to 1050 sq ft")

    def test_plot_width_and_depth_are_not_stated(self):
        for key in content.UNIT_TYPES:
            rooms = _rooms(key)
            self.assertNotIn("Plot width", rooms, f"Type {key}")
            self.assertNotIn("Plot depth", rooms, f"Type {key}")

    def test_no_private_terrace_is_scheduled_or_specified(self):
        """The issued facts do not list a private terrace; the prose may.

        The developer struck "private terrace" from the Also row and
        "ground, first and private terrace" from Levels: the schedule
        states what the sheets state, and the sheets state two floors.
        The elevation caption calls the terrace private on the client's
        instruction, so the guard now covers the surfaces that quote the
        developer -- the schedule, the specification, the room labels and
        the room values -- and leaves the prose to the client.
        """
        for code in copy.LOCALES:
            words = copy.for_locale(code)
            issued = list(words.ROOM_VALUE_WORDS.values())
            issued += list(words.ROOM_LABELS.values())
            issued += [f"{label} {value}"
                       for label, value in words.PROJECT_SCHEDULE]
            issued += [f"{label} {text}" for label, text in words.SPEC_GROUPS]
            issued += list(words.AMENITIES)
            blob = " ".join(issued)
            for term in ("private terrace", "निजी टेरेस", "ખાનગી ટેરેસ"):
                self.assertNotIn(term, blob, code)

    def test_plot_area_is_scheduled_with_the_ground_floor(self):
        for key, unit in content.UNIT_TYPES.items():
            self.assertIn("plot_area", unit["sheets"][0]["rows"], f"Type {key}")

    def test_no_type_advertises_a_dimension_chain_segment_as_a_plot_size(self):
        for key, unit in content.UNIT_TYPES.items():
            plot = " ".join(value for label, value in _rooms(key).items()
                            if label.startswith("Plot"))
            self.assertTrue(plot, f"Type {key} states no plot dimension")
            self.assertNotIn("7.70", plot, f"Type {key} reuses a depth segment")
            self.assertNotIn("25'-3", plot, f"Type {key} reuses a depth segment")

    def test_both_types_are_two_bedroom_homes_with_two_attached_toilets(self):
        # The cover sells "48 two-bedroom townhouses". A schedule that lists
        # one bedroom makes six of the plots look like a lesser product.
        for key, unit in content.UNIT_TYPES.items():
            labels = list(_rooms(key))
            beds = [l for l in labels if "bedroom" in l.lower()]
            toilets = [l for l in labels if "toilet" in l.lower()]
            self.assertGreaterEqual(len(beds), 2, f"Type {key} bedrooms")
            self.assertGreaterEqual(len(toilets), 2, f"Type {key} toilets")
            self.assertTrue(any("living" in l.lower() for l in labels),
                            f"Type {key} has no living room")


class TestLocation(unittest.TestCase):
    def test_corridor_landmarks_are_named(self):
        blob = " ".join(
            s["lead"] + " " + " ".join(s["body"])
            for s in EN.SECTIONS if s["id"] == "location")
        self.assertIn("Parul University", blob)
        self.assertIn("Sumandeep", blob)

    def test_maps_url_carries_the_exact_site_coordinates(self):
        # The pin the owner shared, to the digit. A text search would let
        # Google choose a point on Waghodia Road; this does not.
        self.assertEqual(content.SITE_LATLNG, "22.2918248,73.3433214")
        self.assertEqual(content.PROJECT["site_latlng"], content.SITE_LATLNG)
        self.assertIn("22.2918248%2C73.3433214", content.PROJECT["maps_url"])

    def test_maps_url_opens_directions_not_a_search(self):
        # api=1 "dir" is the documented universal form: the Maps app takes
        # it over from the browser and starts routing to the destination.
        self.assertTrue(content.PROJECT["maps_url"].startswith(
            "https://www.google.com/maps/dir/?api=1&destination="))
        self.assertIn("travelmode=driving", content.PROJECT["maps_url"])
        self.assertNotIn("/maps/search/", content.PROJECT["maps_url"])
        # Short links are redirects, and redirects rot. Print numbers.
        self.assertNotIn("goo.gl", content.PROJECT["maps_url"])


class TestForbiddenGuard(unittest.TestCase):
    """The guard must survive the text being wrapped across lines."""

    def test_detects_a_term_broken_by_a_line_wrap(self):
        self.assertEqual(
            content.forbidden_hits("a short drive from The\nPalace and on"),
            ["The Palace"])

    def test_detects_a_term_broken_by_markup_whitespace(self):
        self.assertEqual(
            content.forbidden_hits("<p>Leo</p>\n  <p>Enterprise</p>"),
            ["Leo Enterprise"])

    def test_is_case_insensitive(self):
        self.assertEqual(content.forbidden_hits("sold by leo   enterprise"),
                         ["Leo Enterprise"])

    def test_clean_text_has_no_hits(self):
        self.assertEqual(content.forbidden_hits("48 townhouses in Vadodara"), [])


if __name__ == "__main__":
    unittest.main()
