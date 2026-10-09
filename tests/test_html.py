import re
import unittest
from build import build_html, content


class TestHtml(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = build_html.render_html()
        # Base64 payloads are image bytes, not copy. Scanning them for words
        # finds "rera" and "Rs6" inside a JPEG and fails on nothing.
        cls.markup = re.sub(r"data:[a-z/+-]+;base64,[A-Za-z0-9+/=]+", "DATA",
                            cls.html)

    def test_has_title_and_viewport(self):
        self.assertIn("<title>Lake Tree Avenue</title>", self.html)
        self.assertIn('name="viewport"', self.html)

    def test_no_external_subresources(self):
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

    def test_no_per_plot_links(self):
        # The plots are near-identical, so 48 separate enquiry links were
        # noise. One enquiry CTA, not forty-eight.
        self.assertNotIn("Plot%20", self.html)
        self.assertNotIn('class="plot"', self.html)

    def test_phone_number_offers_both_calling_and_whatsapp(self):
        self.assertIn(content.tel_link(), self.html)
        self.assertIn('data-cta="whatsapp"', self.markup)

    def test_address_opens_google_maps(self):
        self.assertIn(content.PROJECT["maps_url"], self.html)

    def test_primary_ctas_present(self):
        self.assertIn(content.tel_link(), self.html)
        self.assertIn(content.mail_link(), self.html)
        self.assertIn(content.PROJECT["maps_url"], self.html)

    def test_phone_readable_as_text_not_only_as_link(self):
        self.assertIn(content.PROJECT["phone_display"], self.html)

    def test_no_forbidden_terms(self):
        # Element boundaries split phrases too: "3 BHK" spanning </td><td>
        # would slip past a raw substring check.
        self.assertEqual(content.forbidden_hits(self.markup), [])

    def test_no_price(self):
        self.assertIsNone(re.search(r"(₹|Rs\.?\s*\d)", self.markup))
        self.assertIn("Price on call", self.html)

    def test_light_only_with_explicit_body_background(self):
        self.assertIn("color-scheme: light", self.html)
        self.assertNotIn("prefers-color-scheme: dark", self.html)
        self.assertRegex(self.html, r"body\s*\{[^}]*background")

    def test_no_dark_page_ground(self):
        for hexcode in re.findall(r"background[^;:]*:\s*#([0-9a-fA-F]{6})", self.html):
            r, g, b = (int(hexcode[i:i + 2], 16) for i in (0, 2, 4))
            luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
            self.assertGreater(luma, 120, f"dark background #{hexcode}")

    def test_plan_toggle_is_css_only_and_symmetric(self):
        # The toggle must work with scripting unavailable, so it is radio
        # inputs plus sibling selectors. Both directions must be wired.
        self.assertIn('id="tab-a"', self.markup)
        self.assertIn('id="tab-b"', self.markup)
        self.assertEqual(self.markup.count(' checked>'), 1,
                         "exactly one plan tab starts selected")
        self.assertIn("#tab-a:checked ~ .plan-panes .pane-a { display: block; }",
                      self.markup)
        self.assertIn("#tab-b:checked ~ .plan-panes .pane-b { display: block; }",
                      self.markup)
        self.assertIn('class="plan-pane pane-a"', self.markup)
        self.assertIn('class="plan-pane pane-b"', self.markup)
        for label in ("tab-a", "tab-b"):
            self.assertIn(f'<label for="{label}"', self.markup)

    def test_under_size_budget(self):
        self.assertLess(len(self.html.encode("utf-8")), 6 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
