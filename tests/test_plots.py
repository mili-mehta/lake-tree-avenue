import unittest
import fitz
from build import plots


class TestExtraction(unittest.TestCase):
    def test_extracts_forty_labelled_plots(self):
        found = plots.extract_label_centres(plots.LAYOUT_PDF)
        self.assertEqual(len(found), 40)

    def test_extraction_misses_exactly_the_eight_known_gaps(self):
        found = plots.extract_label_centres(plots.LAYOUT_PDF)
        missing = sorted(set(range(1, 49)) - set(found))
        self.assertEqual(missing, [7, 8, 9, 10, 11, 12, 13, 42])

    def test_manual_centres_fill_exactly_the_gaps(self):
        self.assertEqual(sorted(plots.MANUAL_CENTRES), [7, 8, 9, 10, 11, 12, 13, 42])


class TestHotspots(unittest.TestCase):
    def setUp(self):
        self.spots = plots.hotspots()

    def test_all_forty_eight_plots_present_once_in_order(self):
        self.assertEqual([s.number for s in self.spots], list(range(1, 49)))

    def test_every_hotspot_is_inside_the_page(self):
        for s in self.spots:
            self.assertGreaterEqual(s.x, 0.0, f"plot {s.number}")
            self.assertGreaterEqual(s.y, 0.0, f"plot {s.number}")
            self.assertLessEqual(s.x + s.w, 1.0, f"plot {s.number}")
            self.assertLessEqual(s.y + s.h, 1.0, f"plot {s.number}")

    def test_hotspots_have_positive_area(self):
        for s in self.spots:
            self.assertGreater(s.w, 0.0)
            self.assertGreater(s.h, 0.0)

    def test_unit_type_split_matches_the_spec(self):
        by_num = {s.number: s.unit_type for s in self.spots}
        self.assertTrue(all(by_num[n] == "A" for n in range(1, 7)))
        self.assertTrue(all(by_num[n] == "B" for n in range(7, 49)))

    def test_no_two_hotspots_overlap_by_more_than_a_tenth(self):
        def area(a):
            return a.w * a.h

        def overlap(a, b):
            dx = min(a.x + a.w, b.x + b.w) - max(a.x, b.x)
            dy = min(a.y + a.h, b.y + b.h) - max(a.y, b.y)
            return max(dx, 0) * max(dy, 0)

        for i, a in enumerate(self.spots):
            for b in self.spots[i + 1:]:
                self.assertLess(overlap(a, b), 0.10 * min(area(a), area(b)),
                                f"plots {a.number} and {b.number} overlap")

    def test_each_hotspot_contains_its_own_label_where_a_label_exists(self):
        page = fitz.open(plots.LAYOUT_PDF)[0]
        pw, ph = page.rect.width, page.rect.height
        found = plots.extract_label_centres(plots.LAYOUT_PDF)
        by_num = {s.number: s for s in self.spots}
        for n, (cx, cy) in found.items():
            s = by_num[n]
            self.assertTrue(s.x <= cx / pw <= s.x + s.w, f"plot {n} label outside x")
            self.assertTrue(s.y <= cy / ph <= s.y + s.h, f"plot {n} label outside y")


if __name__ == "__main__":
    unittest.main()
