import os
import re
import tempfile
import unittest

import fitz
from build import build_pdf, content

# cover, project, elevation, then a page per floor per type, then
# layout, specs, location, contact
PLAN_PAGES = {"A": (3, 4), "B": (5, 6)}
GROUND_PAGE = {key: pages[0] for key, pages in PLAN_PAGES.items()}
FIRST_PAGE = {key: pages[1] for key, pages in PLAN_PAGES.items()}
ALL_PLAN_PAGES = [i for pages in PLAN_PAGES.values() for i in pages]
LAYOUT_PAGE = 7
SPECS_PAGE = 8
CONTACT_PAGE = 10


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

    def test_eleven_pages_a4_landscape(self):
        # Both types take a page per floor. Two sheets sharing one page
        # shrink to roughly half the width, and at that size the room
        # dimensions printed inside them stop being readable.
        self.assertEqual(self.doc.page_count, 11)
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

    def test_no_per_plot_link_annotations(self):
        for i, page in enumerate(self.doc):
            self.assertFalse([u for u in self._uris(page) if "Plot%20" in u],
                             f"page {i+1} still carries per-plot links")

    def test_layout_page_carries_only_the_footer_links(self):
        self.assertEqual(len(self.doc[LAYOUT_PAGE].get_links()), 4)

    def test_contact_details_are_readable_text_not_only_links(self):
        text = "\n".join(p.get_text() for p in self.doc)
        self.assertIn(content.PROJECT["phone_display"], text)
        self.assertIn(content.PROJECT["email"], text)

    def test_contact_page_links_each_social_profile_by_handle(self):
        page = self.doc[-1]  # contact closes the brochure
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
        groups = (("Structure", long_copy),) + content.SPEC_GROUPS[1:]
        with unittest.mock.patch.object(content, "SPEC_GROUPS", groups):
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
        return " ".join(" ".join(self.doc[i].get_text().split()) for i in pages)

    def test_every_unit_room_appears_across_its_own_plans_pages(self):
        for key, pages in PLAN_PAGES.items():
            text = self._flat(*pages)
            for room, dim in content.UNIT_TYPES[key]["rooms"]:
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
            self.assertGreater(rect.height, 350,
                               f"page {i+1} plan is only {rect.height:.0f} pt tall")
            self.assertGreater(rect.width, 380,
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

    def test_each_plan_page_says_it_draws_two_adjacent_homes(self):
        for i in ALL_PLAN_PAGES:
            self.assertIn(" ".join(content.PLAN_PAIR_NOTE.split()),
                          self._flat(i),
                          f"page {i+1} does not say the sheet shows a pair")

    def test_each_plan_page_names_the_plots_it_is_drawing(self):
        for key, pages in PLAN_PAGES.items():
            plots = content.UNIT_TYPES[key]["plots"].replace("\u2013", "-")
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

    def test_every_specification_group_appears_in_full(self):
        text = " ".join(p.get_text() for p in self.doc)
        flat = " ".join(text.split())
        for label, body in content.SPEC_GROUPS:
            self.assertIn(" ".join(body.split()), flat,
                          f"{label} copy is cut short")

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


if __name__ == "__main__":
    unittest.main()


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
