"""Draw every hotspot over the site plan so placement can be eyeballed.

Eight of the 48 plots carry no text label in the source drawing and are
placed by hand; this overlay is how that placement is checked.
"""
import io
import os

from PIL import Image, ImageDraw

from build import assets, plots


def hotspot_overlay(path: str, width: int = 1500) -> str:
    img = Image.open(
        io.BytesIO(assets.layout_png(width, plots.SITE_BOX))).convert("RGB")
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for s in plots.hotspots(plots.SITE_BOX):
        box = (s.x * w, s.y * h, (s.x + s.w) * w, (s.y + s.h) * h)
        draw.rectangle(box, outline=(220, 20, 60), width=3)
        draw.text((box[0] + 6, box[1] + 6), f"{s.number:02d}", fill=(200, 0, 60))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    img.save(path, "PNG", optimize=True)
    return path
