import html
import re
import unittest
from build import build_html, content, copy, fonts

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
        # Base64 payloads are image and font bytes, not copy. Scanning
        # them for words finds "rera" and "Rs6" inside a JPEG and fails on
        # nothing. The media type may carry a digit -- font/woff2 -- and a
        # class that forgot that let 600 KB of font through as if it were
        # prose.
        cls.markup = re.sub(r"data:[a-z0-9/+.-]+;base64,[A-Za-z0-9+/=]+",
                            "DATA", cls.html)

    def doc(self, locale):
        """One language's subtree, with the base64 already stripped."""
        return build_html.doc(self.markup, locale)

    def test_has_title_and_viewport(self):
        self.assertIn("<title>Lake Tree Avenue</title>", self.html)
        self.assertIn('name="viewport"', self.html)

    def test_no_external_subresources(self):
        for m in re.finditer(r'(?:src|href)\s*=\s*"([^"]+)"', self.html):
            url = m.group(1)
            if url.startswith(("#", "data:", "tel:", "mailto:")):
                continue
            if url in build_html.PDF_NAMES.values():
                continue  # the brochure's own PDF, served beside it
            self.assertTrue(
                url.startswith("https://wa.me/")
                or url.startswith("https://www.google.com/maps/")
                or url in (content.PROJECT["instagram_url"],
                           content.PROJECT["facebook_url"],
                           content.PROJECT["website_url"]),
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

    def test_the_website_is_named_and_clickable(self):
        self.assertIn(f'href="{content.PROJECT["website_url"]}"', self.html)
        self.assertIn(content.PROJECT["website_display"], self.markup)
        self.assertIn(f'<link rel="canonical" '
                      f'href="{content.PROJECT["website_url"]}">', self.html)

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
        # A glyph alone is a guess; the words are what make it a CTA. In
        # Hindi and Gujarati those words carry no Latin letters, so the
        # check is for a word, not for an English one.
        for tag in re.findall(r'<a class="btn[^>]*>.*?</a>', self.markup):
            self.assertIn("<svg", tag, tag)
            self.assertRegex(re.sub(r"<[^>]+>", "", tag).strip(), r"\w")

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
        for locale in copy.LOCALES:
            self._check_chips(self.doc(locale))

    def _check_chips(self, markup):
        chips = re.findall(r'<a class="chip"[^>]*>', markup)
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
        for locale in copy.LOCALES:
            words = copy.for_locale(locale)
            bar = self.doc(locale).split('<nav class="bar"')[1].split("</nav>")[0]
            self.assertEqual(bar.count("<svg"), 3, bar)
            for key in ("bar_call", "bar_whatsapp", "bar_directions"):
                self.assertIn(f">{words.UI[key]}</a>", bar, locale)
        self.assertIn("env(safe-area-inset-bottom", build_html.CSS)

    def test_plan_toggle_is_css_only_and_symmetric(self):
        # The toggle must work with scripting unavailable, so it is radio
        # inputs plus sibling selectors. Both directions must be wired,
        # and each document owns its own radio group -- three documents
        # sharing one group would move all three at once.
        for locale in copy.LOCALES:
            doc = self.doc(locale)
            for tab in ("a", "b"):
                self.assertIn(f'id="tab-{tab}-{locale}"', doc)
                self.assertIn(f'<label for="tab-{tab}-{locale}"', doc)
                self.assertIn(
                    f"#tab-{tab}-{locale}:checked ~ .plan-panes .pane-{tab}"
                    " { display: block; }", self.markup)
                self.assertIn(f'class="plan-pane pane-{tab}"', doc)
            self.assertEqual(doc.count(" checked>"), 1,
                             f"{locale}: exactly one plan tab starts selected")

    def _pane(self, key, locale="en"):
        """The markup of one plan tab, bounded by the next pane or section."""
        after = self.doc(locale).split(f'class="plan-pane pane-{key}"')[1]
        for boundary in ('class="plan-pane', '<section'):
            after = after.split(boundary)[0]
        return after

    def test_both_panes_show_ground_floor_then_first_floor(self):
        for locale in copy.LOCALES:
            captions = copy.for_locale(locale).SHEET_CAPTIONS
            for key in ("a", "b"):
                pane = self._pane(key, locale)
                self.assertEqual(
                    pane.count('class="plan-sheet"'), 2,
                    f"{locale} pane {key}: expected a ground and a first floor")
                self.assertIn(captions["ground"], pane)
                self.assertIn(captions["first"], pane)
                self.assertLess(pane.index(captions["ground"]),
                                pane.index(captions["first"]),
                                f"{locale} pane {key} puts the first floor first")

    def test_each_pane_names_its_own_plots_in_its_alt_text(self):
        # The pictures are CSS backgrounds, so the accessible name is an
        # aria-label. Every language gets its own; the plot numbers do not
        # move between them.
        for locale in copy.LOCALES:
            for key, plots in (("a", "01–06"), ("b", "07–48")):
                alts = re.findall(r'aria-label="([^"]+)"', self._pane(key, locale))
                self.assertEqual(len(alts), 2, f"{locale} pane {key}")
                for alt in alts:
                    self.assertIn(plots, alt, f"{locale} pane {key}: {alt!r}")

    def test_each_plan_sheet_has_its_own_alt_text(self):
        # Two sheets sharing one accessible name tells a screen reader
        # nothing about which floor it is on.
        for locale in copy.LOCALES:
            captions = copy.for_locale(locale).SHEET_CAPTIONS
            for key in ("a", "b"):
                alts = re.findall(r'aria-label="([^"]+)"', self._pane(key, locale))
                self.assertEqual(len(set(alts)), 2,
                                 f"{locale} pane {key} duplicate name: {alts}")
                for floor in ("ground", "first"):
                    self.assertTrue(
                        any(captions[floor] in a for a in alts),
                        f"{locale} pane {key} never names the {floor} floor")

    def test_no_pane_reuses_another_pane_drawing(self):
        # Both panes carry two sheets. A copy-paste that pointed Type B at
        # Type A's drawings would still render and still look right.
        urls = re.findall(r"background-image: url\((data:[^)]+)\)", self.html)
        plans = [u for u in urls if len(u) > 100_000]
        self.assertGreaterEqual(len(plans), 4)
        self.assertEqual(len(plans), len(set(plans)), "a drawing is reused")

    def test_both_tab_labels_survive_unchanged(self):
        for locale in copy.LOCALES:
            words = copy.for_locale(locale)
            doc = self.doc(locale)
            for unit_key in ("A", "B"):
                label = content.plots_label(content.UNIT_TYPES[unit_key], words)
                self.assertIn(f">{label}<", doc, locale)

    def test_under_size_budget(self):
        self.assertLess(len(self.html.encode("utf-8")), 6 * 1024 * 1024)


class TestDisclaimers(unittest.TestCase):
    """The legal block, which has to be complete in all three documents."""

    @classmethod
    def setUpClass(cls):
        cls.html = build_html.render_html()
        cls.markup = re.sub(r"data:[a-z0-9/+.-]+;base64,[A-Za-z0-9+/=]+",
                            "DATA", cls.html)

    def _list(self, locale):
        doc = build_html.doc(self.markup, locale)
        return doc.split('<ol class="disclaimers">')[1].split("</ol>")[0]

    def test_every_language_prints_all_seven_clauses_verbatim(self):
        # Not a sample of them, and not a paraphrase: the clause a buyer
        # reads has to be the clause the developer issued, in the language
        # that buyer switched to.
        for locale in copy.LOCALES:
            words = copy.for_locale(locale)
            items = re.findall(r"<li>(.*?)</li>", self._list(locale), re.S)
            self.assertEqual(len(items), 7, locale)
            for i, (rendered, clause) in enumerate(zip(items, words.DISCLAIMERS), 1):
                self.assertEqual(rendered, build_html._esc(clause),
                                 f"{locale} clause {i} does not match the copy")

    def test_the_clauses_are_an_ordered_list_so_they_keep_their_numbers(self):
        # They are quoted by number. A <ul> would drop the numbering, and
        # CSS counters would drop it again the moment the page is printed
        # or read out by a screen reader.
        for locale in copy.LOCALES:
            self.assertIn('<ol class="disclaimers">',
                          build_html.doc(self.markup, locale), locale)

    def test_the_disclaimers_close_the_brochure(self):
        # They qualify everything above them, so they come after the last
        # section and before the footer.
        for locale in copy.LOCALES:
            doc = build_html.doc(self.markup, locale)
            self.assertLess(doc.index(f'id="{locale}-contact"'),
                            doc.index(f'id="{locale}-disclaimers"'), locale)
            self.assertLess(doc.index(f'id="{locale}-disclaimers"'),
                            doc.index("<footer>"), locale)

    def test_the_small_print_is_still_readable(self):
        # Small print, not unreadable print: a legal block set below the
        # body size still has to be legible on a phone.
        rule = re.search(r"\.disclaimers \{([^}]*)\}", build_html.CSS).group(1)
        size = float(re.search(r"font-size: ([0-9.]+)rem", rule).group(1))
        self.assertGreaterEqual(size, 0.85)


class TestKeyPlan(unittest.TestCase):
    """The landmark drawing, which now stands on its own.

    The drawing pins the landmarks and prints the distances itself, so
    nothing repeats them under it. What a raster cannot give a screen
    reader or a search engine is in its accessible name instead, which is
    the one place those figures still have to be text.
    """

    @classmethod
    def setUpClass(cls):
        cls.html = build_html.render_html()

    def test_the_drawing_is_embedded_once(self):
        self.assertIn(".shot-key-plan {", self.html)
        self.assertEqual(self.html.count(".shot-key-plan {"), 1)

    def test_each_language_names_the_drawing_in_its_own_words(self):
        labels = re.findall(r'class="shot shot-key-plan" role="img" '
                            r'aria-label="([^"]+)"', self.html)
        self.assertEqual(len(labels), 3, labels)
        self.assertEqual(len(set(labels)), 3, "a language reuses another's alt")

    def test_every_distance_is_carried_by_the_accessible_name(self):
        # The figures are Latin digits in all three documents, so each
        # one has to appear in each language's alt text: that name is the
        # only form of them a screen reader or a crawler ever meets.
        labels = re.findall(r'class="shot shot-key-plan" role="img" '
                            r'aria-label="([^"]+)"', self.html)
        self.assertEqual(len(labels), 3, labels)
        for label in labels:
            for figure in ("2.3", "2.5", "4.2", "8.8", "9.7", "10.1", "13.8"):
                self.assertIn(figure, label, f"{figure} is missing: {label}")

    def test_the_drawing_sits_inside_the_location_section(self):
        # Beside the prose about the road, not stranded in another band.
        section = self.html.split('id="en-location"')[1].split("</section>")[0]
        self.assertIn("shot-key-plan", section)

    def test_nothing_repeats_the_drawing_under_it(self):
        # The distance list and the location schedule both said what the
        # artwork draws. Neither comes back.
        section = self.html.split('id="en-location"')[1].split("</section>")[0]
        self.assertNotIn('class="distances"', section)
        self.assertNotIn('class="schedule"', section)

    def test_the_drawing_is_called_not_to_scale(self):
        # The artwork prints "NOT TO SCALE" itself; the alt text says so
        # for a reader who only ever gets the alt text.
        for label in re.findall(r'class="shot shot-key-plan" role="img" '
                                r'aria-label="([^"]+)"', self.html):
            self.assertRegex(label, "(?i)not to scale|પ્રમાણસર નથી|पैमाने पर नहीं")


class TestLanguageToggle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = build_html.render_html()
        cls.markup = re.sub(r"data:[a-z0-9/+.-]+;base64,[A-Za-z0-9+/=]+",
                            "DATA", cls.html)

    def test_every_language_renders_a_complete_document(self):
        for code in copy.LOCALES:
            doc = build_html.doc(self.markup, code)
            for section in content.SECTION_IDS:
                self.assertIn(f'id="{code}-{section}"', doc,
                              f"{code} is missing the {section} section")

    def test_exactly_one_document_is_visible_per_choice(self):
        # A broken selector either stacks all three languages on top of
        # each other or hides every one of them and ships a blank page.
        self.assertIn(".doc { display: none; }", self.html)
        for code in copy.LOCALES:
            self.assertIn(f"#lang-{code}:checked ~ .doc-{code}"
                          " { display: block; }", self.html, code)

    def test_english_is_the_one_language_selected_on_open(self):
        radios = re.findall(
            r'<input class="lang-radio" type="radio" name="lang" '
            r'id="lang-(\w+)"([^>]*)>', self.markup)
        self.assertEqual([c for c, _ in radios], list(copy.LOCALES))
        self.assertEqual([c for c, attrs in radios if "checked" in attrs],
                         [copy.DEFAULT])

    def test_the_radios_precede_every_document(self):
        # The show/hide rules are plain sibling combinators, so a radio
        # that came after a document would never reach it.
        last_radio = self.markup.rindex('class="lang-radio"')
        self.assertLess(last_radio, self.markup.index('class="doc '))

    def test_the_toggle_needs_no_javascript(self):
        # The page is opened from file:// after a WhatsApp forward.
        self.assertNotIn("<script", self.html)
        self.assertNotIn("onclick", self.html)

    def test_the_pills_name_each_language_in_its_own_script(self):
        names = copy.for_locale("en").LANGUAGE_NAMES
        for code in copy.LOCALES:
            self.assertIn(f'<label for="lang-{code}" lang="{code}">'
                          f"{names[code]}</label>", self.markup)

    def test_each_language_offers_its_own_pdf(self):
        # A toggle that switched the page but handed out an English PDF
        # would undo itself at the last step.
        for code in copy.LOCALES:
            doc = build_html.doc(self.markup, code)
            self.assertIn(f'href="{build_html.PDF_NAMES[code]}" download',
                          doc, code)
            for other in copy.LOCALES:
                if other != code:
                    self.assertNotIn(f'href="{build_html.PDF_NAMES[other]}"',
                                     doc, f"{code} offers the {other} PDF")

    def test_each_document_declares_its_language(self):
        for code in copy.LOCALES:
            self.assertIn(f'<main class="doc doc-{code}" lang="{code}">',
                          self.markup)

    def test_the_indic_documents_embed_their_own_face(self):
        # The document redefines the two font tokens the whole stylesheet
        # reaches for, rather than naming elements -- naming elements had
        # left h1 out, and the Gujarati title set in a system sans.
        for code, face in (("hi", "Devanagari"), ("gu", "Gujarati")):
            rule = re.search(rf"\.doc-{code} \{{ --serif:([^}}]*)\}}",
                             self.html).group(1)
            self.assertIn(f"'Noto Serif {face}'", rule)
            self.assertIn(f"'Noto Sans {face}'", rule)
            # The Latin stack stays behind the Indic face, which is what
            # keeps the brand and the numerals in the brochure's serif.
            self.assertIn("Palatino", rule)
            # body resolved var(--serif) against the root token and passed
            # the answer down, so the document has to ask again.
            self.assertIn("font-family: var(--serif)", rule)
        self.assertNotIn(".doc-en { --serif", self.html)

    def test_the_indic_size_nudge_is_relative_to_the_body_not_the_root(self):
        # rem is the root's 16px; the body sets 18px. In rem the nudge
        # made the Indic documents smaller than the English one.
        for code in ("hi", "gu"):
            rule = re.search(rf"\.doc-{code} \{{ --serif:([^}}]*)\}}",
                             self.html).group(1)
            self.assertRegex(rule, r"font-size: 10[0-9]%")
            self.assertNotIn("rem", rule)

    def test_indic_text_is_given_more_room_than_the_latin(self):
        for code in ("hi", "gu"):
            self.assertIn(f"line-height: {fonts.LEADING[code]}", self.html)

    def test_no_font_is_fetched_from_the_network(self):
        self.assertNotIn("fonts.googleapis.com", self.html)
        self.assertNotIn("fonts.gstatic.com", self.html)

    def test_image_bytes_appear_once_not_once_per_language(self):
        # Three documents sharing one set of pictures is the whole reason
        # the images are CSS backgrounds. An <img> per document would be
        # 8.7 MB where 2.9 MB does.
        uris = re.findall(r"data:image/[a-z]+;base64,[A-Za-z0-9+/=]{200,}",
                          self.html)
        self.assertTrue(uris)
        self.assertEqual(len(uris), len(set(uris)),
                         "a picture is embedded more than once")

    def test_every_picture_declares_its_aspect_ratio(self):
        # A background box has no intrinsic size; without this the page
        # reflows under the reader as the pictures paint.
        rules = re.findall(r"\.shot-[a-z0-9-]+ \{([^}]*)\}", self.html)
        self.assertGreaterEqual(len(rules), 7)
        for rule in rules:
            self.assertIn("aspect-ratio:", rule)

    def test_under_size_budget(self):
        self.assertLess(len(self.html.encode("utf-8")), 6 * 1024 * 1024)


class TestPlotSchedule(unittest.TestCase):
    """Forty-eight plots and their areas, under the drawing that numbers them."""

    @classmethod
    def setUpClass(cls):
        cls.html = build_html.render_html()
        cls.markup = re.sub(r"data:[a-z0-9/+.-]+;base64,[A-Za-z0-9+/=]+",
                            "DATA", cls.html)

    def _section(self, locale):
        doc = build_html.doc(self.markup, locale)
        return doc.split(f'id="{locale}-layout"')[1].split("</section>")[0]

    def _schedule(self, locale):
        return self._section(locale).split('<div class="plot-areas">')[1]

    def test_the_schedule_sits_in_the_site_plan_section(self):
        # Not a section of its own: the drawing says where a plot is and
        # the schedule says how big it is, and a reader holding one wants
        # the other on the same screen.
        for locale in copy.LOCALES:
            section = self._section(locale)
            self.assertIn('<div class="plot-areas">', section)
            self.assertLess(section.index('class="map"'),
                            section.index('class="plot-areas"'), locale)

    def test_every_plot_is_listed_with_its_area(self):
        for locale in copy.LOCALES:
            schedule = self._schedule(locale)
            for number, area, _ in content.plot_area_cells():
                self.assertIn(f'<th scope="row">{number}</th>'
                              f"<td>{area}</td>", schedule,
                              f"{locale} is missing plot {number}")

    def test_the_forty_eight_run_in_three_columns_of_sixteen(self):
        for locale in copy.LOCALES:
            schedule = self._schedule(locale)
            self.assertEqual(schedule.count("<tbody>"), 3, locale)
            rows = re.findall(r'<th scope="row">\d\d</th>', schedule)
            self.assertEqual(len(rows), 48, locale)

    def test_each_column_carries_its_own_pair_of_heads(self):
        for locale in copy.LOCALES:
            ui = copy.for_locale(locale).UI
            schedule = self._schedule(locale)
            for head in (ui["plot_no_col"], ui["plot_area_col"]):
                self.assertEqual(
                    schedule.count(f'<th scope="col">{html.escape(head)}'
                                   "</th>"), 3, f"{locale} {head}")

    def test_the_larger_plots_are_tinted_in_place(self):
        # Marked where they sit in the schedule rather than lifted into a
        # list of their own, so the run of numbers still matches the
        # drawing above it.
        wide = [n for n, _, w in content.plot_area_cells() if w]
        for locale in copy.LOCALES:
            schedule = self._schedule(locale)
            self.assertEqual(schedule.count('class="plot-wide"'),
                             len(wide), locale)
            for number in wide:
                self.assertIn(f'<tr class="plot-wide"><th scope="row">'
                              f"{number}</th>", schedule, f"{locale} {number}")

    def test_no_price_or_payment_term_is_published_with_the_areas(self):
        for locale in copy.LOCALES:
            schedule = self._schedule(locale)
            self.assertIsNone(
                re.search(r"(\u20b9|Rs\.?\s*\d|\d+\s*%|\d{6,})", schedule),
                locale)


if __name__ == "__main__":
    unittest.main()
