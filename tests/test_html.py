import re
import unittest
from build import build_html, content

RULE = re.compile(r"([^{}]+)\{([^}]*)\}")
BACKGROUND = re.compile(r"background[^;:]*:\s*#([0-9a-fA-F]{6})")
# A filled button is an accent the size of a thumb, not a page ground, so it
# is held to text contrast (test_filled_button_carries_its_label) instead of
# to the light-ground rule.
ACCENT = re.compile(r"\.btn\b")


def _channels(hexcode):
    h = hexcode.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _luminance(hexcode):
    def lin(c):
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in _channels(hexcode))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(fg, bg):
    a, b = sorted((_luminance(fg), _luminance(bg)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def _tokens(css):
    return dict(re.findall(r"(--[a-z-]+):\s*(#[0-9a-fA-F]{6})", css))


def _declaration(css, selector, prop):
    """One resolved hex value from one rule, following a var() reference."""
    body = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css).group(1)
    raw = re.search(rf"(?<![-\w]){prop}:\s*([^;]+)", body).group(1).strip()
    var = re.fullmatch(r"var\((--[a-z-]+)\)", raw)
    return _tokens(css)[var.group(1)] if var else raw


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
                or url.startswith("https://www.google.com/maps/")
                or url in (content.PROJECT["instagram_url"],
                           content.PROJECT["facebook_url"]),
                f"external subresource: {url}",
            )

    def test_no_dynamic_fetch_apis(self):
        for banned in ("fetch(", "XMLHttpRequest", "serviceWorker",
                       'type="module"', "import("):
            self.assertNotIn(banned, self.html, f"file:// hostile API: {banned}")

    def test_contact_links_each_social_profile_by_handle(self):
        for key in ("instagram_url", "facebook_url"):
            self.assertIn(f'href="{content.PROJECT[key]}"', self.html,
                          f"{key} is not clickable")
        self.assertIn(content.PROJECT["social_handle"], self.markup)

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

    def test_every_maps_link_is_the_directions_url(self):
        # One pin, one URL. A stray search link would drop the reader on a
        # guessed point of Waghodia Road with no route running.
        links = re.findall(r'href="(https://www\.google\.com/maps/[^"]*)"',
                           self.html)
        self.assertTrue(links, "no Google Maps link in the page")
        for url in links:
            self.assertEqual(url, content.PROJECT["maps_url"])

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
        # Grounds only: a dark page washes out in WhatsApp's in-app viewer.
        for selector, body in RULE.findall(build_html.CSS):
            if ACCENT.search(selector):
                continue
            for hexcode in BACKGROUND.findall(body):
                r, g, b = _channels(hexcode)
                luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
                self.assertGreater(luma, 120,
                                   f"dark background #{hexcode} on {selector.strip()}")
        for style in re.findall(r'style="([^"]*)"', self.markup):
            self.assertEqual(BACKGROUND.findall(style), [], style)

    def test_filled_button_carries_its_label(self):
        # The one dark fill on the page. Its label is normal-size text, so
        # it owes 4.5:1, not the 3:1 that large text gets away with.
        css = build_html.CSS
        fill = _declaration(css, ".btn", "background")
        ink = _declaration(css, ".btn", "color")
        self.assertGreaterEqual(round(_contrast(ink, fill), 2), 4.5,
                                f"{ink} on {fill}")
        hover = _declaration(css, ".btn:hover, .btn:focus-visible", "background")
        self.assertGreaterEqual(round(_contrast(ink, hover), 2), 4.5,
                                f"{ink} on {hover}")

    def test_quiet_button_reads_as_the_second_tier(self):
        css = build_html.CSS
        self.assertNotEqual(_declaration(css, ".btn", "background"),
                            _declaration(css, ".btn-quiet", "background"))
        self.assertEqual(_declaration(css, ".btn-quiet", "background"), "#ffffff")

    def test_every_button_pairs_a_glyph_with_words(self):
        # A glyph alone is a guess; the words are what make it a CTA.
        for tag in re.findall(r'<a class="btn[^>]*>.*?</a>', self.markup):
            self.assertIn("<svg", tag, tag)
            self.assertRegex(re.sub(r"<[^>]+>", "", tag).strip(), r"[A-Za-z]")

    def test_social_chips_use_each_network_own_mark(self):
        # Original artwork, not a monochrome house glyph: Instagram's
        # gradient camera and Facebook's blue f are recognised on sight.
        self.assertIn('id="ig"', self.markup)
        self.assertIn('fill="url(#ig)"', self.markup)
        self.assertIn('fill="#1877F2"', self.markup)
        self.assertIn('fill="#25D366"', self.markup)
        for network, key in (("Instagram", "instagram_url"),
                             ("Facebook", "facebook_url")):
            self.assertRegex(
                self.markup,
                rf'<a class="chip" href="{re.escape(content.PROJECT[key])}"'
                rf'[^>]*aria-label="{network}',
                f"{network} chip is not labelled",
            )

    def test_chips_offer_whatsapp_and_click_to_call(self):
        chips = re.findall(r'<a class="chip"[^>]*>', self.markup)
        self.assertEqual(len(chips), 4, chips)
        self.assertTrue(any(content.tel_link() in c for c in chips), chips)
        self.assertTrue(any("wa.me" in c for c in chips), chips)
        for chip in chips:
            self.assertIn("aria-label=", chip, chip)

    def test_icons_are_decorative_only(self):
        svgs = re.findall(r"<svg[^>]*>", self.markup)
        self.assertGreater(len(svgs), 8)
        for svg in svgs:
            self.assertIn('aria-hidden="true"', svg, svg)
            self.assertIn('focusable="false"', svg, svg)

    def test_sticky_bar_is_three_labelled_icons(self):
        bar = self.markup.split('<nav class="bar"')[1].split("</nav>")[0]
        self.assertEqual(bar.count("<svg"), 3, bar)
        for word in ("Call", "WhatsApp", "Directions"):
            self.assertIn(f">{word}</a>", bar)
        self.assertIn("env(safe-area-inset-bottom", build_html.CSS)

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

    def _pane(self, key):
        """The markup of one plan tab, bounded by the next pane or section."""
        after = self.markup.split(f'class="plan-pane pane-{key}"')[1]
        for boundary in ('class="plan-pane', '<section'):
            after = after.split(boundary)[0]
        return after

    def test_both_panes_show_ground_floor_then_first_floor(self):
        for key in ("a", "b"):
            pane = self._pane(key)
            self.assertEqual(pane.count('class="plan-sheet"'), 2,
                             f"pane {key}: expected a ground and a first floor")
            self.assertIn("Ground floor", pane)
            self.assertIn("First floor", pane)
            self.assertLess(pane.index("Ground floor"),
                            pane.index("First floor"),
                            f"pane {key} puts the first floor first")

    def test_each_pane_says_it_draws_two_adjacent_homes(self):
        for key in ("a", "b"):
            self.assertIn(content.PLAN_PAIR_NOTE, self._pane(key),
                          f"pane {key} does not say the sheet shows a pair")

    def test_each_pane_names_its_own_plots_in_its_alt_text(self):
        for key, plots in (("a", "plots 01–06"), ("b", "plots 07–48")):
            alts = re.findall(r'alt="([^"]+)"', self._pane(key))
            self.assertEqual(len(alts), 2, f"pane {key}")
            for alt in alts:
                self.assertIn(plots, alt, f"pane {key} alt text: {alt!r}")

    def test_each_plan_sheet_has_its_own_alt_text(self):
        # Two sheets sharing one alt text tells a screen reader nothing
        # about which floor it is on.
        for key in ("a", "b"):
            alts = re.findall(r'alt="([^"]+)"', self._pane(key))
            self.assertEqual(len(set(alts)), 2,
                             f"pane {key} duplicate alt text: {alts}")
            self.assertTrue(any("ground floor" in a.lower() for a in alts), alts)
            self.assertTrue(any("first floor" in a.lower() for a in alts), alts)

    def test_no_pane_reuses_another_pane_drawing(self):
        # Both panes carry two sheets now. A copy-paste that pointed Type B
        # at Type A's drawings would still render and still look right.
        srcs = re.findall(r'<img src="(data:[^"]+)"', self.html)
        plans = [u for u in srcs if len(u) > 100_000]
        self.assertGreaterEqual(len(plans), 4)
        self.assertEqual(len(plans), len(set(plans)), "a drawing is reused")

    def test_both_tab_labels_survive_unchanged(self):
        self.assertIn(">Plots 01–06<", self.markup)
        self.assertIn(">Plots 07–48<", self.markup)

    def test_under_size_budget(self):
        self.assertLess(len(self.html.encode("utf-8")), 6 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
