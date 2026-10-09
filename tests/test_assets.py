import io
import unittest
from PIL import Image
from build import assets


def _open(blob):
    return Image.open(io.BytesIO(blob))


class TestLogo(unittest.TestCase):
    def test_logo_is_png_at_requested_height(self):
        img = _open(assets.logo_png(height=420))
        self.assertEqual(img.format, "PNG")
        self.assertEqual(img.height, 420)

    def test_logo_background_is_transparent(self):
        # The logo sits on sand in both artefacts; a white plate around it
        # reads as a pasted sticker.
        img = _open(assets.logo_png(height=300))
        self.assertEqual(img.mode, "RGBA")
        self.assertEqual(img.getpixel((0, 0))[3], 0)

    def test_logo_keeps_its_artwork_opaque(self):
        img = _open(assets.logo_png(height=300)).convert("RGBA")
        alphas = img.getchannel("A").getdata()
        self.assertGreater(max(alphas), 250)

    def test_logo_under_budget(self):
        self.assertLess(len(assets.logo_png()), 400_000)


class TestRender(unittest.TestCase):
    def setUp(self):
        self.blob = assets.render_jpeg(width=1600)
        self.img = _open(self.blob)

    def test_render_is_jpeg_at_requested_width(self):
        self.assertEqual(self.img.format, "JPEG")
        self.assertEqual(self.img.width, 1600)

    def test_letterbox_bars_are_trimmed(self):
        self.assertGreater(self.img.width, self.img.height)

    def test_top_and_bottom_edges_are_not_blank_white(self):
        px = self.img.convert("RGB")
        for y in (0, px.height - 1):
            row = [px.getpixel((x, y)) for x in range(0, px.width, 40)]
            self.assertFalse(all(min(p) > 247 for p in row),
                             f"row {y} is still blank white")

    def test_render_under_budget(self):
        self.assertLess(len(self.blob), 900_000)


class TestLayout(unittest.TestCase):
    def test_layout_png_matches_page_aspect(self):
        img = _open(assets.layout_png(width=1600))
        self.assertEqual(img.width, 1600)
        self.assertAlmostEqual(img.height / img.width, 2384 / 1684, places=2)

    def test_layout_can_crop_to_the_site_plan(self):
        full = _open(assets.layout_png(width=1200))
        site = _open(assets.layout_png(width=1200, box=assets.SITE_BOX))
        self.assertEqual(site.width, 1200)
        # the site plan is wider relative to its height than the whole sheet
        self.assertLess(site.height / site.width, full.height / full.width)

    def test_layout_under_budget(self):
        self.assertLess(len(assets.layout_png()), 2_500_000)


class TestPlanSheets(unittest.TestCase):
    """The dedicated floor plan drawings, ground floor first, per type."""

    @classmethod
    def setUpClass(cls):
        cls.sheets = {key: assets.plan_sheets(key)
                      for key in assets.PLAN_SHEET_SRCS}

    def _every_sheet(self):
        for unit_key, sheets in self.sheets.items():
            for floor, blob in sheets.items():
                yield f"{unit_key} {floor}", blob

    def test_both_types_have_both_floors_ground_first(self):
        self.assertEqual(sorted(self.sheets), ["A", "B"])
        for unit_key, sheets in self.sheets.items():
            self.assertEqual(list(sheets), ["ground", "first"], unit_key)

    def test_sheets_keep_every_pixel_the_source_has(self):
        # Resampling to a nominal "brochure width" would upscale the
        # portrait sheets: more bytes, no more detail, and the room
        # dimensions are the first thing to turn to mush.
        for unit_key, srcs in assets.PLAN_SHEET_SRCS.items():
            for floor, src in srcs:
                want = assets._trim_white(Image.open(src).convert("RGB"))
                got = _open(self.sheets[unit_key][floor])
                self.assertEqual(got.size, want.size,
                                 f"{unit_key} {floor} was resampled")

    def test_sheets_are_encoded_well_enough_to_read_the_dimensions(self):
        # The room dimensions are 4 px strokes of dark text on a pale floor.
        # A thrifty JPEG smears them. Compression must stay light enough
        # that the drawing keeps a hard black and a clean white.
        for key, blob in self._every_sheet():
            lo, hi = _open(blob).convert("L").getextrema()
            self.assertLess(lo, 70, f"{key} sheet lost its darkest ink")
            self.assertGreater(hi, 230, f"{key} sheet lost its paper")
            pixels = _open(blob).width * _open(blob).height
            self.assertGreater(len(blob) / pixels, 0.15,
                               f"{key} sheet compressed too hard to read")

    def test_sheets_are_trimmed_to_their_ink(self):
        # The source PNGs carry a white surround. Left in, the drawing
        # floats in its frame and reads smaller than it needs to.
        #
        # The crops next door assert ink on the outermost row of pixels.
        # These sheets cannot: their outermost ink is a dimension line one
        # stroke thick, which a sampled edge steps over and a JPEG lifts a
        # shade or two anyway. What matters is that no band of dead paper
        # survived, so the finished sheet is re-trimmed and must barely move.
        for key, blob in self._every_sheet():
            img = _open(blob)
            again = assets._trim_white(img)
            self.assertLess(img.width - again.width, 10,
                            f"{key} sheet keeps a blank side margin")
            self.assertLess(img.height - again.height, 10,
                            f"{key} sheet keeps a blank top or bottom margin")

    def test_sheets_are_not_blank(self):
        for key, blob in self._every_sheet():
            self.assertLess(_open(blob).convert("L").getextrema()[0], 200,
                            f"{key} sheet looks blank")

    def test_every_sheet_is_a_distinct_drawing(self):
        blobs = [blob for _, blob in self._every_sheet()]
        self.assertEqual(len(blobs), 4)
        self.assertEqual(len(set(blobs)), 4, "a sheet is used twice")

    def test_sheets_under_budget(self):
        for key, blob in self._every_sheet():
            self.assertLess(len(blob), 700_000, key)


class TestDataUri(unittest.TestCase):
    def test_data_uri_shape(self):
        uri = assets.data_uri(b"abc", "image/png")
        self.assertTrue(uri.startswith("data:image/png;base64,"))
        self.assertNotIn("\n", uri)


if __name__ == "__main__":
    unittest.main()
