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
