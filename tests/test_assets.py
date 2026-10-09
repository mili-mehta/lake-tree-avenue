import io
import unittest
from PIL import Image
from build import assets, plots


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
        site = _open(assets.layout_png(width=1200, box=plots.SITE_BOX))
        self.assertEqual(site.width, 1200)
        # the site plan is wider relative to its height than the whole sheet
        self.assertLess(site.height / site.width, full.height / full.width)

    def test_layout_under_budget(self):
        self.assertLess(len(assets.layout_png()), 2_500_000)


class TestPlanCrops(unittest.TestCase):
    def setUp(self):
        self.crops = assets.plan_crops()

    def test_three_crops_produced(self):
        self.assertEqual(sorted(self.crops), ["A", "B", "elevation"])

    def test_crops_are_non_trivial_images(self):
        for key, blob in self.crops.items():
            img = _open(blob)
            self.assertGreater(img.width, 300, key)
            self.assertGreater(img.height, 150, key)

    def test_crops_are_tightly_framed_on_their_drawing(self):
        # A fixed crop box clips captions at one edge and leaves dead paper at
        # the other. Every edge of a finished crop must carry ink.
        for key, blob in self.crops.items():
            img = _open(blob).convert("L")
            w, h = img.size
            edges = {
                "top": [img.getpixel((x, 0)) for x in range(0, w, 4)],
                "bottom": [img.getpixel((x, h - 1)) for x in range(0, w, 4)],
                "left": [img.getpixel((0, y)) for y in range(0, h, 4)],
                "right": [img.getpixel((w - 1, y)) for y in range(0, h, 4)],
            }
            for name, samples in edges.items():
                self.assertLess(min(samples), 247,
                                f"{key} crop has a blank {name} edge")

    def test_crops_are_not_blank(self):
        for key, blob in self.crops.items():
            img = _open(blob).convert("L")
            extrema = img.getextrema()
            self.assertLess(extrema[0], 200, f"{key} crop looks blank")


class TestDataUri(unittest.TestCase):
    def test_data_uri_shape(self):
        uri = assets.data_uri(b"abc", "image/png")
        self.assertTrue(uri.startswith("data:image/png;base64,"))
        self.assertNotIn("\n", uri)


if __name__ == "__main__":
    unittest.main()
