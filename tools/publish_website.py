"""Copy the built brochure into the website repo, for laketreeavenue.com/brochure/.

The website (github.com/mili-mehta/lake-tree-avenue-website) serves this
brochure from its public/brochure/ folder: the page as index.html, the
three PDFs beside it under the names the page's download buttons use.
This repo stays the brochure's source; the website only receives the
four finished files.

    python3 make_brochure.py                       # build into docs/
    python3 tools/publish_website.py [WEBSITE_DIR] # copy into the website

WEBSITE_DIR defaults to ../lta-website. The script writes those four
files and nothing else: it refuses a directory that is not a clone of
the website repo, and never deletes. It does not commit or push -- a
push to the website's main deploys laketreeavenue.com, so that step is
always taken by hand.
"""
import filecmp
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
DEFAULT_WEBSITE = os.path.join(os.path.dirname(ROOT), "lta-website")
WEBSITE_REPO = "mili-mehta/lake-tree-avenue-website"

# (built file in docs/, its name in the website's public/brochure/)
FILES = (
    ("index.html", "index.html"),
    ("Lake-Tree-Avenue-eBrochure.pdf", "Lake-Tree-Avenue-eBrochure.pdf"),
    ("Lake-Tree-Avenue-eBrochure-hi.pdf", "Lake-Tree-Avenue-eBrochure-hi.pdf"),
    ("Lake-Tree-Avenue-eBrochure-gu.pdf", "Lake-Tree-Avenue-eBrochure-gu.pdf"),
)


def _is_website_clone(path: str) -> bool:
    try:
        remotes = subprocess.run(
            ["git", "-C", path, "remote", "-v"], capture_output=True,
            text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return False
    return WEBSITE_REPO in remotes


def publish(website: str) -> list[tuple[str, str]]:
    """Copy the four files; return (name, what happened) for each."""
    if not _is_website_clone(website):
        raise SystemExit(f"{website} is not a clone of {WEBSITE_REPO}; "
                         "nothing copied")
    target = os.path.join(website, "public", "brochure")
    missing = [src for src, _ in FILES
               if not os.path.isfile(os.path.join(DOCS, src))]
    if missing:
        raise SystemExit(f"not built yet: {missing}; run make_brochure.py")
    os.makedirs(target, exist_ok=True)
    report = []
    for src, name in FILES:
        a, b = os.path.join(DOCS, src), os.path.join(target, name)
        if os.path.exists(b) and filecmp.cmp(a, b, shallow=False):
            report.append((name, "unchanged"))
            continue
        state = "updated" if os.path.exists(b) else "added"
        shutil.copyfile(a, b)
        report.append((name, state))
    return report


def main(argv: list[str]) -> int:
    website = os.path.abspath(argv[1] if len(argv) > 1 else DEFAULT_WEBSITE)
    for name, state in publish(website):
        print(f"{state:9}  public/brochure/{name}")
    print(f"\nNot committed or pushed. Review in {website}, then push its "
          "main to deploy laketreeavenue.com.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
