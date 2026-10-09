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

    def test_no_per_plot_link_annotations(self):
        for i, page in enumerate(self.doc):
            self.assertFalse([u for u in self._uris(page) if "Plot%20" in u],
                             f"page {i+1} still carries per-plot links")

    def test_layout_page_carries_only_the_footer_links(self):
        self.assertEqual(len(self.doc[4].get_links()), 4)

    def test_contact_details_are_readable_text_not_only_links(self):
        text = "\n".join(p.get_text() for p in self.doc)
        self.assertIn(content.PROJECT["phone_display"], text)
        self.assertIn(content.PROJECT["email"], text)

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

    def test_every_unit_room_appears_on_the_plans_page(self):
        text = " ".join(self.doc[3].get_text().split())
        for key, unit in content.UNIT_TYPES.items():
            for room, dim in unit["rooms"]:
                self.assertIn(room, text, f"Type {key} missing row {room!r}")
                self.assertIn(" ".join(dim.split()), text,
                              f"Type {key} missing dimension for {room!r}")

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

    def test_specification_rows_do_not_collide(self):
        page = self.doc[5]
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


if __name__ == "__main__":
    unittest.main()
