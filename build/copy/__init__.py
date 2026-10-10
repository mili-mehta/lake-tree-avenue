"""One copy module per language, behind a parity check.

A brochure that is missing a line in one language is worse than one that
is missing it in all three: nobody notices. So the modules are compared
against each other rather than trusted, and `keys()` is what the tests
compare. Adding a string to English and forgetting Gujarati fails the
build, not the buyer.
"""
import importlib

LOCALES = ("en", "hi", "gu")

# The locale whose document is on screen when the page opens.
DEFAULT = "en"

# Every name a renderer may read off a locale module.
EXPORTS = (
    "TAGLINE", "CREDIT", "ADDRESS", "REGD_OFFICE", "META_DESCRIPTION",
    "WHATSAPP_MESSAGE", "UNIT_LABELS", "PLOTS_LABEL",
    "SHEET_CAPTIONS", "ROOM_LABELS", "ROOM_VALUE_WORDS", "PROJECT_SCHEDULE",
    "SPEC_GROUPS", "AMENITIES",
    "SECTIONS", "UI",
    "LANGUAGE_NAMES",
)


def for_locale(code: str):
    if code not in LOCALES:
        raise KeyError(f"unknown locale: {code!r}")
    return importlib.import_module(f"{__name__}.{code}")


def keys(module) -> tuple:
    """The shape of one locale module, flattened to comparable keys.

    Values are deliberately ignored -- this answers "is anything missing",
    not "is anything translated". The second question is a different test,
    because a module can be complete and still be English throughout.
    """
    out = []
    for name in EXPORTS:
        value = getattr(module, name)
        if isinstance(value, dict):
            out += [f"{name}.{k}" for k in sorted(value)]
        elif isinstance(value, tuple) and value and isinstance(value[0], dict):
            # SECTIONS: keyed by section id, not by position, so a
            # reordering is not mistaken for a missing section.
            for item in value:
                out += [f"{name}.{item['id']}.{k}" for k in sorted(item)]
        elif isinstance(value, tuple):
            out.append(f"{name}[{len(value)}]")
        else:
            out.append(name)
    return tuple(sorted(out))


def strings(module):
    """Every translatable string in one module, as (key, text) pairs.

    Used by the tests that check a module is really in its own script.
    """
    def walk(prefix, value):
        if prefix.endswith(".id"):
            return  # a section id is structure, the same in every language
        if isinstance(value, str):
            yield prefix, value
        elif isinstance(value, dict):
            for k, v in value.items():
                yield from walk(f"{prefix}.{k}", v)
        elif isinstance(value, tuple):
            for i, v in enumerate(value):
                yield from walk(f"{prefix}[{i}]", v)

    for name in EXPORTS:
        if name == "LANGUAGE_NAMES":
            # Endonyms. The Gujarati pill says "ગુજરાતી" in the English
            # document too, because that is what a reader scans for.
            continue
        yield from walk(name, getattr(module, name))
