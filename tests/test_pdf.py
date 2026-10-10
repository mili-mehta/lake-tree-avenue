import os
import re
import tempfile
import unittest

import io

import fitz
from PIL import Image
from build import assets, build_pdf, content, copy, fonts

EN = copy.for_locale("en")

# MuPDF's shaper substitutes the standard fi/fl ligatures, so extracted
# text reads "Ground ﬂoor". That is one character, not two, and every
# assertion below is about the words rather than the glyphs.
LIGATURES = {"\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl",
             "\ufb03": "ffi", "\ufb04": "ffl"}


def _unligate(text: str) -> str:
    for glyph, letters in LIGATURES.items():
        text = text.replace(glyph, letters)
    return text

# cover, project, the front elevation, then a page per floor per type,
# then layout, the plot schedule facing it, specs, location (prose and the
# key plan together), contact
ELEVATION_PAGE = 2
PLAN_PAGES = {"A": (3, 4), "B": (5, 6)}
GROUND_PAGE = {key: pages[0] for key, pages in PLAN_PAGES.items()}
FIRST_PAGE = {key: pages[1] for key, pages in PLAN_PAGES.items()}
ALL_PLAN_PAGES = [i for pages in PLAN_PAGES.values() for i in pages]
LAYOUT_PAGE = 7
PLOT_AREAS_PAGE = 8
SPECS_PAGE = 9
LOCATION_PAGE = 10
CONTACT_PAGE = 11
# The disclaimers close the brochure: they qualify every page before them.
DISCLAIMERS_PAGE = 12


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

    def test_thirteen_pages_a4_landscape(self):
        # Both types take a page per floor. Two sheets sharing one page
        # shrink to roughly half the width, and at that size the room
        # dimensions printed inside them stop being readable.
        self.assertEqual(self.doc.page_count, 13)
        for page in self.doc:
            self.assertAlmostEqual(page.rect.width, 842.0, places=0)
            self.assertAlmostEqual(page.rect.height, 595.0, places=0)

    def _uris(self, page):
        return [l.get("uri", "") for l in page.get_links()
                if l["kind"] == fitz.LINK_URI]

    def test_every_page_carries_the_five_footer_ctas(self):
        for i, page in enumerate(self.doc):
            uris = self._uris(page)
            self.assertIn(content.tel_link(), uris, f"page {i+1} missing tel")
            self.assertIn(content.mail_link(), uris, f"page {i+1} missing mail")
            self.assertIn(content.PROJECT["maps_url"], uris, f"page {i+1} missing maps")
            self.assertTrue(any(u.startswith("https://wa.me/") for u in uris),
                            f"page {i+1} missing whatsapp")
            self.assertIn(content.PROJECT["website_url"], uris,
                          f"page {i+1} missing website")

    def test_all_link_rects_lie_inside_their_page(self):
        for i, page in enumerate(self.doc):
            for link in page.get_links():
                r = fitz.Rect(link["from"])
                self.assertTrue(r.is_valid and not r.is_empty, f"page {i+1} empty rect")
                self.assertTrue(r in page.rect, f"page {i+1} rect outside page: {r}")

    def test_no_per_plot_link_annotations(self):
        for i, page in enumerate(self.doc):
            self.assertFalse([u for u in self._uris(page) if "Plot%20" in u],
                             f"page {i+1} still carries per-plot links")

    def test_layout_page_carries_only_the_footer_links(self):
        self.assertEqual(len(self.doc[LAYOUT_PAGE].get_links()), 5)

    def test_contact_details_are_readable_text_not_only_links(self):
        text = "\n".join(p.get_text() for p in self.doc)
        self.assertIn(content.PROJECT["phone_display"], text)
        self.assertIn(content.PROJECT["email"], text)
        self.assertIn(content.PROJECT["website_display"], text)

    def test_contact_page_links_each_social_profile_by_handle(self):
        page = self.doc[CONTACT_PAGE]
        uris = self._uris(page)
        for key in ("instagram_url", "facebook_url"):
            self.assertIn(content.PROJECT[key], uris,
                          f"{key} is not clickable")
        self.assertIn(content.PROJECT["social_handle"], page.get_text())

    def test_no_forbidden_terms_in_extracted_text(self):
        # insert_textbox wraps, and get_text reports a wrap as a newline, so a
        # raw substring check misses "The\nPalace". forbidden_hits collapses
        # whitespace first.
        text = "\n".join(p.get_text() for p in self.doc)
        self.assertEqual(content.forbidden_hits(text), [])

    def test_specification_text_is_never_silently_truncated(self):
        # insert_textbox returns a negative value when the copy does not fit
        # and writes only what did. Swallowing that drops the tail of a
        # specification mid-sentence with every test still green.
        import unittest.mock
        long_copy = ("Reinforced cement concrete frame with steel conforming "
                     "to IS 1786 for all reinforcement in columns, beams and "
                     "slabs, and an independent third party structural audit "
                     "before handover of each home. " * 6)
        groups = (("Structure", long_copy),) + EN.SPEC_GROUPS[1:]
        with unittest.mock.patch.object(EN, "SPEC_GROUPS", groups):
            with self.assertRaises(build_pdf.LayoutOverflow):
                build_pdf.build_doc()

    def test_schedule_rows_never_run_past_the_footer(self):
        # A schedule that outgrows its page silently drops its last rows —
        # on the plans page that is the plot size, the single number a buyer
        # most wants.
        for i, page in enumerate(self.doc):
            for block in page.get_text("blocks"):
                if not block[4].strip():
                    continue
                self.assertLessEqual(
                    block[3], build_pdf.FOOTER_TOP + 32,
                    f"page {i+1} text runs into the footer: {block[4][:40]!r}")

    def _flat(self, *pages):
        return _unligate(
            " ".join(" ".join(self.doc[i].get_text().split()) for i in pages))

    def test_every_unit_room_appears_across_its_own_plans_pages(self):
        for key, pages in PLAN_PAGES.items():
            text = self._flat(*pages)
            for room, dim in content.unit_rooms(content.UNIT_TYPES[key], EN):
                self.assertIn(room, text, f"Type {key} missing row {room!r}")
                self.assertIn(" ".join(dim.split()), text,
                              f"Type {key} missing dimension for {room!r}")

    def test_each_plan_page_carries_one_drawing_at_readable_size(self):
        # The point of a page per floor is size. A drawing that does not
        # fill most of the page has lost the argument for the extra page,
        # and its printed room dimensions go with it.
        for i in ALL_PLAN_PAGES:
            big = [fitz.Rect(info["bbox"])
                   for info in self.doc[i].get_image_info()
                   if fitz.Rect(info["bbox"]).height > 150]
            self.assertEqual(len(big), 1, f"page {i+1} is not a single plan")
            rect = big[0]
            # The sheets are portrait, so height is the dimension that runs
            # out first and the one that decides how big the text prints.
            self.assertGreater(rect.height, 440,
                               f"page {i+1} plan is only {rect.height:.0f} pt tall")
            self.assertGreater(rect.width, 220,
                               f"page {i+1} plan is only {rect.width:.0f} pt wide")

    def test_each_plan_page_fills_the_column_it_was_given(self):
        # Fitted to its own aspect, a drawing should run out of room in one
        # direction. Short in both means the box was sized for the other
        # type's drawings and this one is floating in white.
        for i in ALL_PLAN_PAGES:
            rect = max((fitz.Rect(info["bbox"])
                        for info in self.doc[i].get_image_info()),
                       key=lambda r: r.get_area())
            fills_height = rect.height > 0.9 * (build_pdf.FOOTER_TOP - build_pdf.MARGIN)
            fills_width = rect.width > 0.9 * build_pdf.PLAN_IMAGE_W
            self.assertTrue(fills_height or fills_width,
                            f"page {i+1} plan fills neither dimension")

    def test_plans_run_ground_floor_before_first_floor(self):
        for key, pages in PLAN_PAGES.items():
            ground = self._flat(GROUND_PAGE[key])
            first = self._flat(FIRST_PAGE[key])
            self.assertIn("Ground floor", ground, f"Type {key}")
            self.assertIn("First floor", first, f"Type {key}")
            self.assertNotIn("First floor", ground,
                             f"Type {key} first floor precedes its ground floor")

    def test_rooms_are_listed_on_the_floor_they_are_on(self):
        for key in PLAN_PAGES:
            ground = self._flat(GROUND_PAGE[key])
            first = self._flat(FIRST_PAGE[key])
            self.assertIn("Kitchen", ground, f"Type {key}")
            self.assertIn("Living room / dining", ground, f"Type {key}")
            self.assertNotIn("Kitchen", first, f"Type {key}")
            self.assertIn("Master bedroom", first, f"Type {key}")
            self.assertIn("Second bedroom", first, f"Type {key}")
            self.assertNotIn("Master bedroom", ground, f"Type {key}")

    def test_each_plan_page_names_the_plots_it_is_drawing(self):
        for key, pages in PLAN_PAGES.items():
            plots = content.plots_label(
                content.UNIT_TYPES[key], EN).replace("\u2013", "-")
            for i in pages:
                self.assertIn(plots.lower(), self._flat(i).lower(),
                              f"page {i+1} does not say which plots it shows")

    def test_no_plan_page_shows_another_types_drawing(self):
        seen = {}
        for i in ALL_PLAN_PAGES:
            xrefs = tuple(sorted(info[0] for info in self.doc.get_page_images(i)))
            self.assertNotIn(xrefs, seen,
                             f"page {i+1} repeats the drawing on page {seen.get(xrefs, 0)+1}")
            seen[xrefs] = i

    def test_every_section_lead_and_body_reaches_the_pdf(self):
        """What the web page says, the file a buyer is sent says too.

        Most buyers are forwarded the PDF rather than the link, so a
        paragraph that exists only in the HTML is a paragraph most
        readers never see. The plans lead and body were exactly that
        until the first plan page took them, and nothing in the build
        would have said so.
        """
        text = " ".join(p.get_text() for p in self.doc)
        flat = _unligate(" ".join(text.split()))
        for section in EN.SECTIONS:
            for key in ("lead", "body"):
                values = section[key]
                for value in ((values,) if isinstance(values, str) else values):
                    self.assertIn(" ".join(value.split()), flat,
                                  f"the {section['id']} {key} is not in the PDF")

    def test_every_specification_group_appears_in_full(self):
        text = " ".join(p.get_text() for p in self.doc)
        flat = _unligate(" ".join(text.split()))
        for label, body in EN.SPEC_GROUPS:
            self.assertIn(" ".join(body.split()), flat,
                          f"{label} copy is cut short")

    def test_every_disclaimer_appears_in_full_on_its_own_page(self):
        # The clauses are the one block here whose exact wording the owner
        # is held to. A clause that wrapped out of its box would print as
        # far as it fit and stop, which is how a brochure ends up
        # promising something the developer never wrote.
        flat = _unligate(" ".join(
            self.doc[DISCLAIMERS_PAGE].get_text().split()))
        for i, clause in enumerate(EN.DISCLAIMERS, 1):
            self.assertIn(" ".join(clause.split()), flat,
                          f"disclaimer {i} is cut short or missing")

    def test_the_disclaimers_are_numbered_the_way_they_were_issued(self):
        # They are quoted by number -- "clause 4" -- so the numbers are
        # part of the copy, not decoration, and they run 1 to 7 in order
        # down the left column and on into the right.
        text = self.doc[DISCLAIMERS_PAGE].get_text()
        numbers = [n for n in re.findall(r"(?m)^(\d)\.$", text)]
        self.assertEqual(numbers, [str(i) for i in range(1, 8)])

    def test_a_disclaimer_that_outgrows_its_box_fails_the_build(self):
        import unittest.mock
        long_clause = EN.DISCLAIMERS[0] + " " + ("Further, " + EN.DISCLAIMERS[4]) * 4
        clauses = (long_clause,) + EN.DISCLAIMERS[1:]
        with unittest.mock.patch.object(EN, "DISCLAIMERS", clauses):
            with self.assertRaises(build_pdf.LayoutOverflow):
                build_pdf.build_doc()

    def test_the_disclaimers_page_carries_nothing_but_the_footer_links(self):
        # Nothing to tap here: a legal page with a WhatsApp button in the
        # middle of it reads as a sales page with small print.
        self.assertEqual(len(self.doc[DISCLAIMERS_PAGE].get_links()), 5)

    def test_no_price_in_extracted_text(self):
        text = "\n".join(p.get_text() for p in self.doc)
        self.assertIsNone(re.search(r"(₹|Rs\.?\s*\d)", text))

    def test_no_unrenderable_characters(self):
        # Base-14 fonts drop characters they cannot encode and PyMuPDF
        # substitutes "?". No copy in this brochure contains a question mark,
        # so any "?" in the output is a dropped glyph.
        for i, page in enumerate(self.doc):
            self.assertNotIn("?", page.get_text(),
                             f"page {i+1} has an unrenderable character")

    def test_no_plan_page_text_collides(self):
        # A schedule value that wrapped used to be drawn straight through
        # the rule and into the row beneath it: "[5.31 m to 7.51 m]"
        # landing on top of "Plot depth".
        for i in ALL_PLAN_PAGES:
            blocks = [b for b in self.doc[i].get_text("blocks") if b[4].strip()]
            for j, a in enumerate(blocks):
                for b in blocks[j + 1:]:
                    x_overlap = min(a[2], b[2]) - max(a[0], b[0])
                    y_overlap = min(a[3], b[3]) - max(a[1], b[1])
                    self.assertFalse(
                        x_overlap > 4 and y_overlap > 2,
                        f"page {i+1} text collides: "
                        f"{a[4].strip()[:30]!r} / {b[4].strip()[:30]!r}")

    def test_specification_rows_do_not_collide(self):
        page = self.doc[SPECS_PAGE]
        blocks = [b for b in page.get_text("blocks") if b[4].strip()]
        for i, a in enumerate(blocks):
            for b in blocks[i + 1:]:
                x_overlap = min(a[2], b[2]) - max(a[0], b[0])
                y_overlap = min(a[3], b[3]) - max(a[1], b[1])
                self.assertFalse(
                    x_overlap > 4 and y_overlap > 2,
                    f"text collides: {a[4].strip()[:28]!r} / {b[4].strip()[:28]!r}",
                )

    def test_placed_images_keep_their_aspect_without_letterboxing(self):
        # Each placed image's rect must match the image's own aspect, so the
        # drawing fills its frame instead of floating in white.
        for i, page in enumerate(self.doc):
            for info in page.get_image_info():
                bbox = fitz.Rect(info["bbox"])
                if bbox.width < 60 or bbox.height < 60:
                    continue
                placed = bbox.width / bbox.height
                native = info["width"] / info["height"]
                self.assertAlmostEqual(
                    placed, native, delta=0.06 * native,
                    msg=f"page {i+1} image letterboxed: {placed:.3f} vs {native:.3f}",
                )

    def test_under_size_budget(self):
        self.assertLess(os.path.getsize(self.path), 8 * 1024 * 1024)


class TestSchedule(unittest.TestCase):
    """The ruled fact table both plan pages and the project page use."""

    def _rows(self, rows, width, label_w):
        doc = fitz.open()
        page = doc.new_page(width=build_pdf.PAGE_SIZE[0],
                            height=build_pdf.PAGE_SIZE[1])
        end = build_pdf._schedule(page, rows, build_pdf.MARGIN, 100.0, width,
                                  label_w=label_w, pitch=26.0)
        return page, end

    def test_a_value_that_wraps_makes_its_row_taller(self):
        # The bug: a two-line value in a fixed-height row was drawn across
        # the rule below it. The row has to grow instead.
        short = (("Plot depth", "39'-1\""),)
        long = (("Plot width", "18'-1½\" to 24'-8\"  [5.52 m to 7.52 m]"),)
        _, short_end = self._rows(short, 200.0, 138.0)
        _, long_end = self._rows(long, 200.0, 138.0)
        self.assertGreater(long_end, short_end,
                           "a wrapped value did not grow its row")

    def test_a_single_line_value_keeps_the_nominal_pitch(self):
        _, end = self._rows((("Plot depth", "39'-1\""),), 260.0, 138.0)
        self.assertAlmostEqual(end, 126.0, delta=0.5)

    def test_a_value_too_tall_for_the_page_is_refused(self):
        rows = tuple((f"Row {i}", "39'-1\"") for i in range(40))
        with self.assertRaises(build_pdf.LayoutOverflow):
            self._rows(rows, 260.0, 138.0)


class TestEveryLanguage(unittest.TestCase):
    """The Hindi and Gujarati documents, which no reviewer here proofreads."""

    @classmethod
    def setUpClass(cls):
        cls.docs = {}
        cls.paths = {}
        for locale in copy.LOCALES:
            fd, path = tempfile.mkstemp(suffix=f"-{locale}.pdf")
            os.close(fd)
            build_pdf.write(path, locale)
            cls.paths[locale] = path
            cls.docs[locale] = fitz.open(path)

    @classmethod
    def tearDownClass(cls):
        for locale, doc in cls.docs.items():
            doc.close()
            os.unlink(cls.paths[locale])

    def test_every_language_builds_the_same_thirteen_pages(self):
        # A LayoutOverflow during the build is the real assertion here:
        # Devanagari runs longer than English, and a box tuned for the
        # English would drop the tail of a sentence.
        for locale, doc in self.docs.items():
            self.assertEqual(doc.page_count, 13, locale)

    def test_every_indic_character_has_a_glyph(self):
        # A font missing one conjunct still renders the line, with a hole
        # in it. Checked at the source rather than in the pixels: the
        # pixels cannot tell an empty box from a space.
        for locale in ("hi", "gu"):
            words = copy.for_locale(locale)
            faces = [fitz.Font(fontfile=os.path.join(
                fonts.DIR, fonts.PDF_FAMILIES[locale][role] + ".ttf"))
                for role in ("serif", "sans")]
            used = set()
            for _, text in copy.strings(words):
                used |= {c for c in text if build_pdf._INDIC.match(c)}
            for key in content.UNIT_TYPES:
                for _, value in content.unit_rooms(
                        content.UNIT_TYPES[key], words):
                    used |= {c for c in value if build_pdf._INDIC.match(c)}
            for face in faces:
                missing = sorted(c for c in used if not face.has_glyph(ord(c)))
                self.assertEqual(missing, [], f"{locale} {face.name}")

    def test_the_latin_serif_carries_the_characters_the_indic_faces_lack(self):
        # None of the four Noto Indic faces has U+00BD. The half sign
        # appears in half the dimensions in this brochure, so the Latin
        # run it sits in has to be set in a face that does have it.
        for locale in ("hi", "gu"):
            for role in ("serif", "sans"):
                face = fitz.Font(fontfile=os.path.join(
                    fonts.DIR, fonts.PDF_FAMILIES[locale][role] + ".ttf"))
                self.assertFalse(face.has_glyph(0x00BD),
                                 f"{locale}/{role} gained a half sign; the "
                                 "run marking may no longer be needed")
        # So every half sign that reaches the page must have been set in
        # the Latin face instead. Checked on the built document, because
        # that is where the tofu box appeared.
        for locale in ("hi", "gu"):
            seen = 0
            for page in self.docs[locale]:
                for block in page.get_text("dict")["blocks"]:
                    for line in block.get("lines", ()):
                        for span in line["spans"]:
                            if "\u00bd" not in span["text"]:
                                continue
                            seen += 1
                            self.assertNotIn(
                                "Devanagari", span["font"],
                                f"{locale}: a half sign in the Indic face")
                            self.assertNotIn(
                                "Gujarati", span["font"],
                                f"{locale}: a half sign in the Indic face")
            self.assertGreater(seen, 0, f"{locale} draws no half sign at all")

    def test_measurements_are_marked_as_latin_runs(self):
        with build_pdf._using("gu"):
            body = build_pdf._body("\u0aaa\u0ab9\u0acb\u0ab3\u0abe\u0a88 "
                                   "24'-7\u00bd\"")
        self.assertIn('<span class="lat">', body)
        self.assertIn("\u00bd", body.split('<span class="lat">')[1])

    def test_english_is_left_exactly_as_it_was(self):
        # The English document needs no run marking, and adding it would
        # churn a file that is already published and being forwarded.
        with build_pdf._using("en"):
            self.assertNotIn("<span", build_pdf._body("17'-5\" to 24'-7\u00bd\""))

    def test_each_language_embeds_only_the_faces_it_draws_with(self):
        expected = {
            "en": set(),
            "hi": {"Noto Serif Devanagari", "Noto Sans Devanagari"},
            "gu": {"Noto Serif Gujarati", "Noto Sans Gujarati"},
        }
        for locale, doc in self.docs.items():
            names = {f[3] for page in doc for f in page.get_fonts()}
            for want in expected[locale]:
                self.assertTrue(any(want.replace(" ", "") in n.replace(" ", "")
                                    for n in names),
                                f"{locale} does not embed {want}: {names}")
            if locale == "en":
                self.assertFalse([n for n in names if "Noto Sans Dev" in n
                                  or "Gujarati" in n], names)

    def test_no_text_runs_into_the_footer_in_any_language(self):
        for locale, doc in self.docs.items():
            for i, page in enumerate(doc):
                for block in page.get_text("blocks"):
                    if not block[4].strip():
                        continue
                    self.assertLessEqual(
                        block[3], build_pdf.FOOTER_TOP + 32,
                        f"{locale} page {i+1}: {block[4][:40]!r}")

    def test_every_page_carries_the_footer_links_in_every_language(self):
        for locale, doc in self.docs.items():
            for i, page in enumerate(doc):
                uris = {link["uri"] for link in page.get_links()
                        if link.get("uri")}
                self.assertIn(content.tel_link(), uris, f"{locale} page {i+1}")
                self.assertIn(content.PROJECT["maps_url"], uris,
                              f"{locale} page {i+1}")

    def test_no_forbidden_term_reaches_any_language(self):
        # Extraction from the Indic documents is unreliable -- shaped
        # glyph runs have no clean reverse mapping -- so the guard runs
        # against the copy, which is where it can actually see.
        for locale in copy.LOCALES:
            blob = "\n".join(t for _, t in
                              copy.strings(copy.for_locale(locale)))
            self.assertEqual(content.forbidden_hits(blob), [], locale)

    def test_each_language_stays_under_the_size_budget(self):
        for locale, path in self.paths.items():
            self.assertLess(os.path.getsize(path), 4 * 1024 * 1024, locale)


class TestPlotSchedule(unittest.TestCase):
    """Every plot, on the page facing the drawing that numbers them."""

    @classmethod
    def setUpClass(cls):
        cls.doc = build_pdf.build_doc()
        cls.text = " ".join(
            cls.doc[PLOT_AREAS_PAGE].get_text().split())

    def test_every_one_of_the_forty_eight_plots_is_listed(self):
        # A schedule that quietly dropped a row would tell a buyer the
        # plot they are standing on does not exist.
        for number, area, _ in content.plot_area_cells():
            self.assertIn(f"{number} {area}", self.text, number)

    def test_the_areas_are_the_ones_the_developer_issued(self):
        pairs = re.findall(r"\b(\d\d) (\d{3,4}) sq ft\b", self.text)
        self.assertEqual([(int(n), int(a)) for n, a in pairs],
                         [(n, a) for n, a in content.PLOT_AREAS])

    def test_both_column_heads_repeat_over_all_three_columns(self):
        for head in (EN.UI["plot_no_col"], EN.UI["plot_area_col"]):
            self.assertEqual(self.text.count(head), 3, head)

    def test_no_price_reaches_the_schedule(self):
        # The sheet this came from carried a price and a payment
        # schedule beside every area. Neither is published.
        self.assertIsNone(
            re.search(r"(\u20b9|Rs\.?\s*\d|\d{6,}|\d+\s*%)", self.text))

    def test_every_language_prints_the_whole_schedule(self):
        for locale in copy.LOCALES:
            doc = build_pdf.build_doc(locale)
            text = " ".join(doc[PLOT_AREAS_PAGE].get_text().split())
            for number, area, _ in content.plot_area_cells():
                self.assertIn(f"{number} {area}", text, f"{locale} {number}")
            doc.close()


if __name__ == "__main__":
    unittest.main()


class TestKeyPlan(unittest.TestCase):
    """The landmark drawing, on the location page with the section's words."""

    @classmethod
    def setUpClass(cls):
        cls.doc = build_pdf.build_doc()

    def test_the_drawing_shares_the_location_page(self):
        page = self.doc[LOCATION_PAGE]
        self.assertEqual(len(page.get_images()), 1)
        text = _unligate(" ".join(page.get_text().split()))
        title = next(s["title"] for s in EN.SECTIONS if s["id"] == "location")
        self.assertIn(title, text)

    def test_the_drawing_takes_every_point_the_words_leave_it(self):
        # Its labels are sized relative to its width, so width is
        # legibility: it fills the band under the prose rather than
        # sitting in a column of its own.
        page = self.doc[LOCATION_PAGE]
        rect = page.get_image_rects(page.get_images()[0][0])[0]
        self.assertGreater(rect.width, 0.7 * page.rect.width)
        self.assertAlmostEqual(rect.y1, build_pdf.FOOTER_TOP - 14, places=0)
        self.assertAlmostEqual((rect.x0 + rect.x1) / 2,
                               page.rect.width / 2, places=0)

    def test_the_drawing_clears_the_prose_above_it(self):
        page = self.doc[LOCATION_PAGE]
        rect = page.get_image_rects(page.get_images()[0][0])[0]
        prose = [b for b in page.get_text("blocks") if b[1] < rect.y0]
        self.assertTrue(prose, "the prose is not above the drawing")
        self.assertGreater(rect.y0, max(b[3] for b in prose),
                           "the drawing prints through the prose")

    def test_the_drawing_keeps_its_own_proportions(self):
        # Stretched to fit, the pins would sit off the road they mark.
        page = self.doc[LOCATION_PAGE]
        rect = page.get_image_rects(page.get_images()[0][0])[0]
        with Image.open(io.BytesIO(assets.key_plan_jpeg())) as art:
            self.assertAlmostEqual(rect.width / rect.height,
                                   art.width / art.height, places=2)

    def test_the_drawing_is_a_link_to_the_directions(self):
        # The page no longer carries a button, so the artwork is the way
        # through to the map.
        page = self.doc[LOCATION_PAGE]
        rect = page.get_image_rects(page.get_images()[0][0])[0]
        uris = [l["uri"] for l in page.get_links()
                if l["kind"] == fitz.LINK_URI and rect.intersects(l["from"])]
        self.assertIn(content.PROJECT["maps_url"], uris)

    def test_nothing_on_the_page_repeats_the_drawing(self):
        # Neither the distance columns nor the road/between/next-to
        # schedule: both were the key plan in another typeface.
        text = _unligate(" ".join(self.doc[LOCATION_PAGE].get_text().split()))
        for place in ("Dhiraj Hospital", "Avalon World School",
                      "Waghodia GIDC", "L&T Knowledge City", "Nimeta Garden",
                      "AATAPI Wonderland", "Vadodara Airport"):
            self.assertNotIn(place, text, f"{place} repeats beside the drawing")
        for figure in ("2.3", "2.5", "4.2", "8.8", "9.7", "10.1", "13.8"):
            self.assertNotIn(f"{figure} km", text,
                             f"{figure} km is set as text beside the drawing")


class TestDeterminism(unittest.TestCase):
    def test_building_twice_produces_identical_bytes(self):
        # PDFs embed a creation timestamp by default, so every rebuild would
        # rewrite dist/ and leave the working tree dirty for no reason.
        paths = []
        for _ in range(2):
            fd, path = tempfile.mkstemp(suffix=".pdf")
            os.close(fd)
            build_pdf.write(path)
            paths.append(path)
        try:
            with open(paths[0], "rb") as a, open(paths[1], "rb") as b:
                self.assertEqual(a.read(), b.read(),
                                 "two builds of the same source differ")
        finally:
            for path in paths:
                os.unlink(path)
