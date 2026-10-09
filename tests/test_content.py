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
        self.assertEqual(rooms["Living room / dining"], "17'-4½\" × 15'-0\"")

    def test_type_b_plot_size_is_the_drawn_plot_not_a_dimension_segment(self):
        # 25'-3" [7.70] is a segment of TYPE A's depth chain
        # (1.85 + 7.70 + 2.75 = 12.30). Pairing it with Type B's depth
        # advertises 91.7 m2 of land where the drawing gives 65.7 m2.
        rooms = dict(content.UNIT_TYPES["B"]["rooms"])
        self.assertEqual(rooms["Plot size"],
                         "18'-1½\" × 39'-1\"  [5.52 m × 11.91 m]")

    def test_type_a_plot_size_matches_the_drawing(self):
        rooms = dict(content.UNIT_TYPES["A"]["rooms"])
        self.assertEqual(rooms["Plot size"],
                         "17'-5\" × 40'-4½\"  [5.31 m × 12.30 m]")

    def test_no_type_advertises_a_dimension_chain_segment_as_a_plot_size(self):
        for key, unit in content.UNIT_TYPES.items():
            plot = dict(unit["rooms"])["Plot size"]
            self.assertNotIn("7.70", plot, f"Type {key} reuses a depth segment")
            self.assertNotIn("25'-3", plot, f"Type {key} reuses a depth segment")

    def test_both_types_are_two_bedroom_homes_with_two_attached_toilets(self):
        # The cover sells "48 two-bedroom townhouses". A schedule that lists
        # one bedroom makes six of the plots look like a lesser product.
        for key, unit in content.UNIT_TYPES.items():
            labels = [room for room, _ in unit["rooms"]]
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
            for s in content.SECTIONS if s["id"] == "location")
        self.assertIn("Parul University", blob)
        self.assertIn("Sumandeep", blob)

    def test_landmarks_appear_in_the_location_schedule(self):
        rows = dict(content.LOCATION_ROWS)
        self.assertIn("Between", rows)
        self.assertIn("Parul University", rows["Between"])
        self.assertIn("Sumandeep", rows["Between"])

    def test_maps_query_points_at_the_stretch_of_road(self):
        self.assertIn("Waghodia", content.PROJECT["maps_url"])
        self.assertTrue(content.PROJECT["maps_url"].startswith(
            "https://www.google.com/maps/search/?api=1&query="))


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
