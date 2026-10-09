"""Vendor the Noto Devanagari and Gujarati fonts into fonts/.

Run once, by hand, not as part of the build: the brochure build must be
offline and byte-reproducible, so the fonts live in the repository rather
than being fetched each time.

Two formats are needed for two renderers:

  *.ttf    the variable font, for the PDF. MuPDF reads it out of an
           fitz.Archive and shapes with HarfBuzz.
  *.woff2  the script-subset web font, for the HTML. Google already serves
           one subset file per family covering both weights, so this is a
           download rather than a subsetting job -- which is what keeps
           fonttools out of the dependency list.
"""
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "fonts")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# key -> (Google Fonts family, its unicode-range subset, the TTF in google/fonts)
FAMILIES = {
    "serif-deva": ("Noto+Serif+Devanagari", "devanagari",
                   "notoserifdevanagari/NotoSerifDevanagari%5Bwdth,wght%5D.ttf"),
    "sans-deva": ("Noto+Sans+Devanagari", "devanagari",
                  "notosansdevanagari/NotoSansDevanagari%5Bwdth,wght%5D.ttf"),
    "serif-gujr": ("Noto+Serif+Gujarati", "gujarati",
                   "notoserifgujarati/NotoSerifGujarati%5Bwght%5D.ttf"),
    "sans-gujr": ("Noto+Sans+Gujarati", "gujarati",
                  "notosansgujarati/NotoSansGujarati%5Bwdth,wght%5D.ttf"),
}

LICENSE_URL = ("https://raw.githubusercontent.com/google/fonts/main/ofl/"
               "notoserifdevanagari/OFL.txt")


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=120).read()


def _woff2_url(family: str, subset: str) -> str:
    """The one woff2 Google serves for this family's own script.

    The stylesheet declares a face per weight per subset, but a variable
    font answers every weight from one file, so the distinct URLs under
    the wanted subset collapse to one.
    """
    css = _get(f"https://fonts.googleapis.com/css2?family={family}"
               ":wght@400;600&display=swap").decode()
    parts = re.split(r"/\*\s*([a-z-]+)\s*\*/", css)
    urls = []
    for name, block in zip(parts[1::2], parts[2::2]):
        if name == subset:
            urls += re.findall(r"url\((https://[^)]+\.woff2)\)", block)
    if not urls:
        raise LookupError(f"{family}: no {subset} face in the stylesheet")
    return list(dict.fromkeys(urls))[0]


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    for key, (family, subset, ttf_path) in FAMILIES.items():
        ttf = _get("https://github.com/google/fonts/raw/main/ofl/" + ttf_path)
        open(os.path.join(OUT, key + ".ttf"), "wb").write(ttf)
        woff2 = _get(_woff2_url(family, subset))
        open(os.path.join(OUT, key + ".woff2"), "wb").write(woff2)
        print(f"{key:11} ttf {len(ttf):7,}  woff2 {len(woff2):7,}")
    open(os.path.join(OUT, "OFL.txt"), "wb").write(_get(LICENSE_URL))
    print("OFL.txt written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
