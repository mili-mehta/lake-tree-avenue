"""Build both Lake Tree Avenue artefacts into dist/, then publish them to docs/.

Named make_brochure rather than build so it cannot shadow the build package.

docs/ is what GitHub Pages serves: the HTML becomes index.html so the bare
Pages URL opens the brochure, and the PDF keeps its name so it can be shared
as a direct download link.
"""
import os
import shutil
import sys

from build import build_html, build_pdf

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
DOCS = os.path.join(ROOT, "docs")


def publish(html: str, pdf: str) -> list:
    """Copy the built artefacts into docs/ for GitHub Pages."""
    os.makedirs(DOCS, exist_ok=True)
    targets = [
        (html, os.path.join(DOCS, "index.html")),
        (pdf, os.path.join(DOCS, os.path.basename(pdf))),
    ]
    for src, dst in targets:
        shutil.copyfile(src, dst)
    return [dst for _, dst in targets]


def main() -> int:
    os.makedirs(DIST, exist_ok=True)
    html = build_html.write(os.path.join(DIST, "Lake-Tree-Avenue.html"))
    pdf = build_pdf.write(os.path.join(DIST, "Lake-Tree-Avenue-eBrochure.pdf"))
    for p in (html, pdf) + tuple(publish(html, pdf)):
        print(f"{os.path.getsize(p) / 1024 / 1024:6.2f} MB  {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
