import re
import unittest

from build import content, copy

# Latin that is *supposed* to survive inside a Hindi or Gujarati line.
# A Vadodara buyer reads these in Latin whatever language the sentence is
# in, and the owner asked for the brand, the email and the phone to stay
# English.
LATIN_OK = (
    "Lake Tree Avenue", "TAM Developers", "Parul University", "Parul",
    "Sumandeep", "WhatsApp", "Instagram", "Facebook", "Google Maps",
    "Google", "BHK", "sq ft", "Spunpipe & Construction Co.", "Spunpipe",
    "Construction", "LAYOUT PLAN", "Waghodia", "Vadodara", "Kamlapura",
    "Alkapuri", "Halol", "Ramkrishna Chambers", "BPC Road", "Regd",
    "Office", "info@laketreeavenue.com", "@laketreeavenue",
    "laketreeavenue.com",
    "AC", "PDF", "Tremix",
    # The two abbreviations in the disclaimers. A buyer in Vadodara reads
    # both in Latin on every bill and receipt they already hold, and a
    # transliterated "जी.एस.टी." would be a tax nobody recognises.
    "GST", "G.E.B.",
)

DEVANAGARI = r"ऀ-ॿ"
GUJARATI = r"઀-૿"
SCRIPT = {"hi": DEVANAGARI, "gu": GUJARATI}


def _residue(text: str) -> str:
    """What Latin is left once the sanctioned words are removed.

    Format placeholders go too: "{range}" is a slot the renderer fills,
    not a word anybody reads.
    """
    text = re.sub(r"\{\w+\}", " ", text)
    for ok in sorted(LATIN_OK, key=len, reverse=True):
        text = text.replace(ok, " ")
    return text


class TestCopyParity(unittest.TestCase):
    def test_every_locale_exposes_the_same_keys(self):
        base = copy.keys(copy.for_locale("en"))
        for code in copy.LOCALES:
            self.assertEqual(copy.keys(copy.for_locale(code)), base,
                             f"{code} has drifted from the English shape")

    def test_every_locale_is_listed_and_importable(self):
        self.assertEqual(copy.LOCALES, ("en", "hi", "gu"))
        for code in copy.LOCALES:
            self.assertTrue(copy.for_locale(code).SECTIONS)

    def test_an_unknown_locale_is_refused(self):
        with self.assertRaises(KeyError):
            copy.for_locale("mr")

    def test_the_sections_run_in_the_same_order_everywhere(self):
        for code in copy.LOCALES:
            ids = tuple(s["id"] for s in copy.for_locale(code).SECTIONS)
            self.assertEqual(ids, content.SECTION_IDS, code)

    def test_every_room_key_is_labelled_in_every_language(self):
        keys = {k for unit in content.UNIT_TYPES.values()
                for k, _ in unit["rooms"]}
        for code in copy.LOCALES:
            words = copy.for_locale(code)
            self.assertEqual(set(words.ROOM_LABELS), keys, code)

    def test_every_prose_row_has_words_in_every_language(self):
        # A row whose value is None takes its text from the locale. If a
        # locale is missing it, the schedule renders a hole.
        prose = {k for unit in content.UNIT_TYPES.values()
                 for k, v in unit["rooms"] if v is None}
        for code in copy.LOCALES:
            self.assertEqual(set(copy.for_locale(code).ROOM_VALUE_WORDS),
                             prose, code)

    def test_the_schedules_are_the_same_length_in_every_language(self):
        for code in copy.LOCALES:
            words = copy.for_locale(code)
            self.assertEqual(len(words.PROJECT_SCHEDULE),
                             len(copy.for_locale("en").PROJECT_SCHEDULE), code)
            self.assertEqual(len(words.SPEC_GROUPS), 9, code)
            self.assertEqual(len(words.AMENITIES), 6, code)

    def test_every_language_carries_all_seven_disclaimers(self):
        # The one block of copy here that is a legal statement. A clause
        # that went missing from the Gujarati document would be a clause
        # the Gujarati buyer was never shown, so the count is checked
        # rather than assumed -- and a clause is never merged into its
        # neighbour to make the count up, which is why each one is also
        # required to end in a full stop or a danda.
        for code in copy.LOCALES:
            clauses = copy.for_locale(code).DISCLAIMERS
            self.assertEqual(len(clauses), 7, code)
            for i, clause in enumerate(clauses, 1):
                self.assertRegex(clause, r"[.।]$", f"{code} clause {i}")
                self.assertGreater(len(clause), 40, f"{code} clause {i}")


class TestCopyIsActuallyTranslated(unittest.TestCase):
    def test_every_translated_string_carries_its_own_script(self):
        # A locale module can be complete by key and English throughout.
        # The English string decides whether there was anything to
        # translate: "Lake Tree Avenue" and "LAYOUT PLAN" are meant to stay
        # Latin, so they are exempt, and nothing else is.
        english = dict(copy.strings(copy.for_locale("en")))
        for code in ("hi", "gu"):
            for key, text in copy.strings(copy.for_locale(code)):
                if not re.search(r"[A-Za-z]", _residue(english[key])):
                    continue  # the English is sanctioned Latin throughout
                self.assertRegex(text, f"[{SCRIPT[code]}]",
                                 f"{code}.{key} is not translated: {text!r}")

    def test_no_untranslated_english_words_survive(self):
        for code in ("hi", "gu"):
            for key, text in copy.strings(copy.for_locale(code)):
                left = _residue(text)
                self.assertNotRegex(
                    left, r"[A-Za-z]{3,}",
                    f"{code}.{key} still reads English: {text!r}")

    def test_no_locale_borrows_another_script(self):
        for code in ("hi", "gu"):
            other = GUJARATI if code == "hi" else DEVANAGARI
            for key, text in copy.strings(copy.for_locale(code)):
                self.assertNotRegex(text, f"[{other}]",
                                    f"{code}.{key} is in the wrong script")

    def test_numerals_stay_latin(self):
        # The owner asked for Latin digits: 48, 703, 391760. Devanagari or
        # Gujarati digits in a dimension would be unreadable beside the
        # drawings, which are issued in Latin.
        for code in ("hi", "gu"):
            for key, text in copy.strings(copy.for_locale(code)):
                self.assertNotRegex(text, r"[०-९૦-૯]",
                                    f"{code}.{key} uses non-Latin digits")

    def test_the_language_pills_read_the_same_in_every_document(self):
        # A reader hunting for Gujarati looks for "ગુજરાતી", whichever
        # language happens to be on screen when they start looking.
        base = copy.for_locale("en").LANGUAGE_NAMES
        for code in copy.LOCALES:
            self.assertEqual(copy.for_locale(code).LANGUAGE_NAMES, base, code)


class TestNothingSupersededSurvivesTranslation(unittest.TestCase):
    def test_no_forbidden_term_in_any_locale(self):
        for code in copy.LOCALES:
            blob = "\n".join(t for _, t in copy.strings(copy.for_locale(code)))
            self.assertEqual(content.forbidden_hits(blob), [], code)

    def test_no_price_in_any_locale(self):
        for code in copy.LOCALES:
            blob = "\n".join(t for _, t in copy.strings(copy.for_locale(code)))
            self.assertIsNone(re.search(r"(₹|Rs\.?\s*\d)", blob), code)


if __name__ == "__main__":
    unittest.main()
