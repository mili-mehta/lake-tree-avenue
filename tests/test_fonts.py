import os
import re
import unittest

from build import fonts


class TestFonts(unittest.TestCase):
    def test_english_needs_no_embedded_font(self):
        # The Latin stack is already on every device. Shipping Noto to a
        # reader who will never see a Devanagari glyph is 600 KB wasted.
        self.assertEqual(fonts.face_css("en"), "")

    def test_face_css_embeds_rather_than_links(self):
        # A linked font is a network fetch, and the page is opened from
        # file:// after a WhatsApp forward.
        for locale in ("hi", "gu"):
            css = fonts.face_css(locale)
            self.assertIn("data:font/woff2;base64,", css)
            self.assertNotIn("https://", css)
            self.assertNotIn("url(fonts", css)

    def test_each_locale_carries_only_its_own_script(self):
        self.assertNotIn("Gujarati", fonts.face_css("hi"))
        self.assertNotIn("Devanagari", fonts.face_css("gu"))

    def test_each_locale_declares_a_serif_and_a_sans(self):
        for locale in ("hi", "gu"):
            families = set(re.findall(r"font-family:\s*'([^']+)'",
                                      fonts.face_css(locale)))
            self.assertEqual(len(families), 2, families)

    def test_both_weights_resolve_from_one_variable_file(self):
        # One variable woff2 per family covers 400 and 600. Declaring the
        # two weights separately would paste the same 120 KB of base64 into
        # the page twice: in a single-file document the payload IS the
        # declaration, so the weight range is a size decision, not a style.
        css = fonts.face_css("hi")
        self.assertEqual(re.findall(r"font-weight:\s*([\d ]+);", css),
                         ["400 600", "400 600"])
        payloads = re.findall(r"base64,([A-Za-z0-9+/=]+)", css)
        self.assertEqual(len(payloads), 2)
        self.assertEqual(len(payloads), len(set(payloads)))

    def test_pdf_families_name_files_that_exist(self):
        for locale in ("hi", "gu"):
            for role, family in fonts.PDF_FAMILIES[locale].items():
                path = os.path.join(fonts.DIR, family + ".ttf")
                self.assertTrue(os.path.exists(path), path)

    def test_the_pdf_archive_directory_holds_every_vendored_face(self):
        names = set(os.listdir(fonts.ttf_archive_dir()))
        self.assertTrue({"serif-deva.ttf", "sans-deva.ttf",
                         "serif-gujr.ttf", "sans-gujr.ttf"} <= names, names)

    def test_the_licence_travels_with_the_fonts(self):
        self.assertTrue(os.path.exists(os.path.join(fonts.DIR, "OFL.txt")))

    def test_indic_text_is_given_more_room_than_latin(self):
        # Devanagari and Gujarati hang matras above and below the line; at
        # the Latin leading they collide.
        for locale in ("hi", "gu"):
            self.assertGreater(fonts.LEADING[locale], fonts.LEADING["en"])
            self.assertGreater(fonts.SCALE[locale], 1.0)
        self.assertEqual(fonts.SCALE["en"], 1.0)


if __name__ == "__main__":
    unittest.main()
