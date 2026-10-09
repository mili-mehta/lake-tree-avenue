"""Build both Lake Tree Avenue artefacts into dist/.

Named make_brochure rather than build so it cannot shadow the build package.
"""
import os
import sys

from build import build_html, build_pdf

DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")


def main() -> int:
    os.makedirs(DIST, exist_ok=True)
    html = build_html.write(os.path.join(DIST, "Lake-Tree-Avenue.html"))
    pdf = build_pdf.write(os.path.join(DIST, "Lake-Tree-Avenue-eBrochure.pdf"))
    for p in (html, pdf):
        print(f"{os.path.getsize(p) / 1024 / 1024:6.2f} MB  {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
