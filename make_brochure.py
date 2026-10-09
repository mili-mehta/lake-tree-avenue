"""Build both Lake Tree Avenue artefacts into dist/, then publish them to docs/.

Named make_brochure rather than build so it cannot shadow the build package.

docs/ is what GitHub Pages serves: the HTML becomes index.html so the bare
Pages URL opens the brochure, and the PDF keeps its name so it can be shared
as a direct download link.
"""
import os
import shutil
import sys

from build import build_html, build_pdf, copy

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
DOCS = os.path.join(ROOT, "docs")


def publish(html: str, pdfs: list) -> list:
    """Copy the built artefacts into docs/ for GitHub Pages.

    The PDFs keep the names the page's download links use, so the link
    beside the Gujarati document finds the Gujarati file.
    """
    os.makedirs(DOCS, exist_ok=True)
    targets = [(html, os.path.join(DOCS, "index.html"))]
    targets += [(pdf, os.path.join(DOCS, os.path.basename(pdf)))
                for pdf in pdfs]
    for src, dst in targets:
        shutil.copyfile(src, dst)
    return [dst for _, dst in targets]


def main() -> int:
    os.makedirs(DIST, exist_ok=True)
    # One page carrying all three languages, and a PDF for each, because
    # a PDF cannot carry a toggle.
    html = build_html.write(os.path.join(DIST, "Lake-Tree-Avenue.html"))
    pdfs = [build_pdf.write(
        os.path.join(DIST, build_html.PDF_NAMES[code]), code)
        for code in copy.LOCALES]
    for p in [html] + pdfs + publish(html, pdfs):
        print(f"{os.path.getsize(p) / 1024 / 1024:6.2f} MB  {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
