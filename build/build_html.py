"""Single-file HTML e-brochure.

Everything the page needs travels inside the document: images as base64 data
URIs, styles inline, no scripts. It is opened from file:// on phones, where
fetch, modules and service workers are blocked, so the plot map is built from
SVG anchors that work with no JavaScript at all.
"""
import html
import os

from build import assets, content, plots

CSS = """
:root {
  color-scheme: light;
  --paper: #ffffff;
  --sand: #f3eadb;
  --sand-deep: #e9dcc7;
  --ink: #33281f;
  --ink-soft: #6b5c4c;
  --terra: #b5793f;
  --terra-deep: #8f5a2a;
  --sage: #778a52;
  --rule: #d8ccb8;
  --serif: "Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua",
           Georgia, serif;
  --sans: "Avenir Next", Avenir, "Segoe UI", Roboto, system-ui, sans-serif;
}

* { box-sizing: border-box; }

html { -webkit-text-size-adjust: 100%; }

body {
  margin: 0;
  background: #ffffff;
  color: var(--ink);
  font-family: var(--serif);
  font-size: 18px;
  line-height: 1.62;
  overflow-x: hidden;
}

img { display: block; max-width: 100%; height: auto; }

a { color: var(--terra-deep); }

.wrap { max-width: 1180px; margin: 0 auto; padding: 0 28px; }
.measure { max-width: 34em; }

h1, h2, h3 { font-weight: 400; margin: 0; letter-spacing: -0.012em; }
h1 { font-size: clamp(2.6rem, 7vw, 4.6rem); line-height: 1.04; }
h2 { font-size: clamp(1.8rem, 3.6vw, 2.7rem); line-height: 1.14; }
h3 { font-size: 1.12rem; line-height: 1.3; }
p { margin: 0 0 1.05em; }
p:last-child { margin-bottom: 0; }

.lead { font-size: 1.22rem; color: var(--ink-soft); line-height: 1.5; }

/* ---------- hero: a spread, not a banner ---------- */
.hero { display: grid; grid-template-columns: 1fr; }
.hero-panel {
  background: #f3eadb;
  padding: 56px 28px 48px;
  display: flex; flex-direction: column; justify-content: center;
}
.hero-logo { width: 196px; margin-bottom: 36px; mix-blend-mode: multiply; }
.hero h1 { margin-bottom: 18px; }
.hero-sub {
  font-family: var(--sans); font-size: 0.95rem; letter-spacing: 0.04em;
  color: var(--ink-soft); margin-bottom: 30px;
}
.hero-figure { overflow: hidden; }
.hero-figure img { width: 100%; height: 100%; object-fit: cover;
  animation: settle 7s cubic-bezier(.2,.6,.2,1) both; }
@keyframes settle { from { transform: scale(1.06); } to { transform: scale(1); } }

/* ---------- actions ---------- */
.actions { display: flex; flex-wrap: wrap; gap: 12px; }
.btn {
  font-family: var(--sans); font-size: 0.97rem; font-weight: 600;
  text-decoration: none; padding: 13px 22px; border-radius: 2px;
  border: 1.5px solid var(--terra); color: var(--terra-deep);
  background: #ffffff; transition: background-color .18s ease, color .18s ease;
}
.btn:hover, .btn:focus-visible { background: #f6e9da; }
.btn-quiet { border-color: var(--rule); color: var(--ink); background: #ffffff; }
.btn-quiet:hover, .btn-quiet:focus-visible { background: #f6f1e8; }

a:focus-visible, .plot:focus-visible, input:focus-visible + label {
  outline: 2px solid var(--sage); outline-offset: 3px;
}

/* ---------- sections ---------- */
section { padding: 84px 0; }
.band { background: #f3eadb; }
.hd { margin-bottom: 34px; }
.hd h2 { margin-bottom: 10px; }

/* dimension-line divider, borrowed from the drawing sheet */
.dim { display: flex; align-items: center; gap: 14px; margin: 40px 0 0; }
.dim::before, .dim::after {
  content: ""; flex: 1; height: 1px; background: #d8ccb8;
}
.dim span {
  font-family: var(--sans); font-size: 0.82rem; letter-spacing: 0.08em;
  color: var(--ink-soft); white-space: nowrap;
}

/* schedule: the drawing's own notation, as a table of facts */
.schedule { width: 100%; border-collapse: collapse; margin-top: 30px; }
.schedule tr { border-top: 1px solid var(--rule); }
.schedule tr:last-child { border-bottom: 1px solid var(--rule); }
.schedule th, .schedule td { text-align: left; padding: 13px 0; vertical-align: top; }
.schedule th {
  font-family: var(--sans); font-weight: 600; font-size: 0.9rem;
  color: var(--ink-soft); width: 48%; padding-right: 20px;
}
.schedule td { font-variant-numeric: tabular-nums; }

/* ---------- render ---------- */
.bleed img { width: 100%; }
.caption {
  font-family: var(--sans); font-size: 0.85rem; color: var(--ink-soft);
  margin-top: 12px;
}

/* ---------- plans: CSS-only toggle ---------- */
.plans input { position: absolute; opacity: 0; pointer-events: none; }
.plan-tabs { display: flex; gap: 8px; margin-bottom: 26px; flex-wrap: wrap; }
.plan-tabs label {
  font-family: var(--sans); font-size: 0.93rem; padding: 10px 18px;
  border: 1px solid var(--rule); border-radius: 2px; cursor: pointer;
  background: #ffffff; color: var(--ink-soft);
}
#tab-a:checked ~ .plan-tabs label[for="tab-a"],
#tab-b:checked ~ .plan-tabs label[for="tab-b"] {
  border-color: var(--terra); color: var(--terra-deep); background: #f6e9da;
}
.plan-pane { display: none; }
#tab-a:checked ~ .plan-panes .pane-a { display: block; }
#tab-b:checked ~ .plan-panes .pane-b { display: block; }
.plan-grid { display: grid; grid-template-columns: 1fr; gap: 30px; align-items: start; }
.plan-sheet { border: 1px solid var(--rule); background: #ffffff; padding: 14px; }

/* ---------- the drawing sheet: the one loud thing ---------- */
.sheet {
  border: 1px solid var(--ink); padding: 7px; background: #ffffff;
  max-width: 820px; margin: 0 auto;
}
.sheet-inner { border: 1px solid var(--rule); padding: 16px; }
.sheet-title {
  display: flex; justify-content: space-between; align-items: baseline;
  gap: 16px; border-bottom: 1px solid var(--rule);
  padding-bottom: 12px; margin-bottom: 16px; flex-wrap: wrap;
}
.sheet-title b {
  font-family: var(--sans); font-weight: 600; font-size: 0.9rem;
  letter-spacing: 0.14em;
}
.sheet-title span {
  font-family: var(--sans); font-size: 0.8rem; color: var(--ink-soft);
}
.map { position: relative; }
.map img { width: 100%; }
.map svg { position: absolute; inset: 0; width: 100%; height: 100%; }
.plot {
  fill: #b5793f; fill-opacity: 0; stroke: #b5793f; stroke-width: 0;
  transition: fill-opacity .14s ease;
}
.map a:hover .plot, .map a:focus .plot { fill-opacity: 0.3; stroke-width: 2; }
.legend {
  font-family: var(--sans); font-size: 0.84rem; color: var(--ink-soft);
  margin-top: 14px; display: flex; gap: 22px; flex-wrap: wrap;
}
.swatch { display: inline-block; width: 11px; height: 11px; margin-right: 7px;
  background: #e9dcc7; border: 1px solid var(--terra); vertical-align: -1px; }

/* ---------- specifications ---------- */
.spec-list { margin: 0; }
.spec-list div {
  display: grid; grid-template-columns: 1fr; gap: 2px;
  padding: 15px 0; border-top: 1px solid var(--rule);
}
.spec-list div:last-child { border-bottom: 1px solid var(--rule); }
.spec-list dt {
  font-family: var(--sans); font-weight: 600; font-size: 0.92rem;
  color: var(--terra-deep);
}
.spec-list dd { margin: 0; color: var(--ink-soft); }

.amenities { list-style: none; margin: 26px 0 0; padding: 0;
  columns: 1; column-gap: 40px; }
.amenities li { padding: 7px 0 7px 22px; position: relative;
  break-inside: avoid; color: var(--ink-soft); }
.amenities li::before {
  content: ""; position: absolute; left: 0; top: 15px;
  width: 8px; height: 8px; background: #778a52;
}

/* ---------- contact ---------- */
.contact-grid { display: grid; grid-template-columns: 1fr; gap: 34px; margin-top: 30px; }
.contact-grid h3 { margin-bottom: 8px; font-family: var(--sans); font-size: 0.92rem;
  font-weight: 600; color: var(--ink-soft); }
.contact-grid p { color: var(--ink); }
.contact-grid a { text-decoration: none; }

footer { padding: 46px 0 120px; border-top: 1px solid var(--rule);
  font-family: var(--sans); font-size: 0.86rem; color: var(--ink-soft); }
footer img { width: 128px; margin-bottom: 18px; mix-blend-mode: multiply; }

/* ---------- sticky bar, phones only ---------- */
.bar { position: fixed; left: 0; right: 0; bottom: 0; display: flex;
  background: #ffffff; border-top: 1px solid var(--rule); z-index: 20; }
.bar a { flex: 1; text-align: center; padding: 15px 6px; font-family: var(--sans);
  font-size: 0.92rem; font-weight: 600; text-decoration: none;
  color: var(--terra-deep); }
.bar a + a { border-left: 1px solid var(--rule); }

@media (min-width: 820px) {
  body { font-size: 19px; }
  section { padding: 110px 0; }
  .hero { grid-template-columns: 0.92fr 1.08fr; min-height: 86vh; }
  .hero-panel { padding: 64px 56px; }
  .plan-grid { grid-template-columns: 1.55fr 1fr; gap: 46px; }
  .spec-list div { grid-template-columns: 210px 1fr; gap: 26px; }
  .amenities { columns: 2; }
  .contact-grid { grid-template-columns: repeat(3, 1fr); gap: 44px; }
  .bar { display: none; }
  footer { padding-bottom: 60px; }
}

@media (prefers-reduced-motion: reduce) {
  .hero-figure img { animation: none; }
  * { transition: none !important; }
}
"""


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _schedule_rows() -> str:
    rows = (
        ("Homes", "48 townhouses, two bedrooms each"),
        ("Plan types", "Type A, plots 01–06 &nbsp;/&nbsp; Type B, plots 07–48"),
        ("Approach road", "12.00 m town planning road"),
        ("Internal roads", "7.50 m, paved both sides"),
        ("Levels", "Ground, first and private terrace"),
        ("Parking", "On plot, plus open-space parking"),
    )
    return "".join(
        f"<tr><th scope=\"row\">{_esc(k)}</th><td>{v}</td></tr>" for k, v in rows
    )


def _plan_pane(key: str, crop_uri: str) -> str:
    unit = content.UNIT_TYPES[key]
    rows = "".join(
        f"<tr><th scope=\"row\">{_esc(room)}</th><td>{_esc(dim)}</td></tr>"
        for room, dim in unit["rooms"]
    )
    return (
        f'<div class="plan-pane pane-{key.lower()}">'
        f'<div class="plan-grid">'
        f'<div class="plan-sheet"><img src="{crop_uri}" '
        f'alt="Ground and first floor plans for {_esc(unit["plots"].lower())}"></div>'
        f'<div><table class="schedule">{rows}</table></div>'
        f"</div></div>"
    )


def _plot_overlay() -> str:
    spots = plots.hotspots(plots.SITE_BOX)
    x0, y0, x1, y1 = plots.SITE_BOX
    view_w = 1000.0
    view_h = round(view_w * ((y1 - y0) * 2384.0) / ((x1 - x0) * 1684.0))
    parts = []
    for s in spots:
        x = round(s.x * view_w, 2)
        y = round(s.y * view_h, 2)
        w = round(s.w * view_w, 2)
        h = round(s.h * view_h, 2)
        label = f"Plot {s.number:02d}, {content.UNIT_TYPES[s.unit_type]['label']}"
        parts.append(
            f'<a href="{content.plot_wa_link(s.number)}" target="_blank" '
            f'rel="noopener"><title>{_esc(label)} — enquire on WhatsApp</title>'
            f'<rect class="plot" x="{x}" y="{y}" width="{w}" height="{h}"></rect>'
            f"</a>"
        )
    return (
        f'<svg viewBox="0 0 {view_w:.0f} {view_h:.0f}" preserveAspectRatio="none" '
        f'role="group" aria-label="Plot map. Each plot opens a WhatsApp enquiry.">'
        + "".join(parts)
        + "</svg>"
    )


def render_html() -> str:
    p = content.PROJECT
    logo = assets.data_uri(assets.logo_png(420), "image/png")
    logo_small = assets.data_uri(assets.logo_png(260), "image/png")
    render = assets.data_uri(assets.render_jpeg(1600), "image/jpeg")
    layout = assets.data_uri(assets.layout_png(1500, plots.SITE_BOX), "image/png")
    crops = assets.plan_crops()
    crop_a = assets.data_uri(crops["A"], "image/jpeg")
    crop_b = assets.data_uri(crops["B"], "image/jpeg")
    elevation = assets.data_uri(crops["elevation"], "image/jpeg")

    s = {sec["id"]: sec for sec in content.SECTIONS}
    wa = content.wa_link(
        "Hi, I'd like to know more about Lake Tree Avenue."
    )

    out = []
    out.append("<!doctype html><html lang=\"en\"><head>")
    out.append('<meta charset="utf-8">')
    out.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    out.append("<title>Lake Tree Avenue</title>")
    out.append(
        '<meta name="description" content="48 two-bedroom townhouses on '
        'Waghodia Main Road, Vadodara. A new launch by TAM Developers.">')
    out.append(f"<style>{CSS}</style></head><body>")

    # hero
    out.append('<header class="hero">')
    out.append('<div class="hero-panel">')
    out.append(f'<img class="hero-logo" src="{logo}" alt="Lake Tree Avenue">')
    out.append(f"<h1>{_esc(s['cover']['title'])}</h1>")
    out.append(
        f'<p class="hero-sub">{_esc(s["cover"]["body"][0])}<br>'
        f'{_esc(s["cover"]["body"][1])}</p>')
    out.append('<div class="actions">')
    out.append(f'<a class="btn" href="{wa}" target="_blank" rel="noopener">'
               "Enquire on WhatsApp</a>")
    out.append(f'<a class="btn btn-quiet" href="#plots">See the plot map</a>')
    out.append("</div></div>")
    out.append(f'<div class="hero-figure"><img src="{render}" '
               'alt="Lake Tree Avenue townhouses at dusk, seen along the avenue">'
               "</div>")
    out.append("</header>")

    # the project
    out.append('<section><div class="wrap">')
    out.append('<div class="hd measure">')
    out.append(f"<h2>{_esc(s['project']['title'])}</h2>")
    out.append(f'<p class="lead">{_esc(s["project"]["lead"])}</p></div>')
    out.append('<div class="measure">')
    out.extend(f"<p>{_esc(b)}</p>" for b in s["project"]["body"])
    out.append("</div>")
    out.append(f'<table class="schedule">{_schedule_rows()}</table>')
    out.append("</div></section>")

    # render
    out.append('<section class="band"><div class="wrap">')
    out.append('<div class="hd measure">')
    out.append(f"<h2>{_esc(s['render']['title'])}</h2>")
    out.append(f'<p class="lead">{_esc(s["render"]["lead"])}</p></div>')
    out.append(f'<div class="bleed"><img src="{elevation}" '
               'alt="Front and rear elevations of a Lake Tree Avenue townhouse">')
    out.append(f'<p class="caption">{_esc(s["render"]["body"][0])}</p></div>')
    out.append("</div></section>")

    # plans
    out.append('<section id="plans"><div class="wrap">')
    out.append('<div class="hd measure">')
    out.append(f"<h2>{_esc(s['plans']['title'])}</h2>")
    out.append(f'<p class="lead">{_esc(s["plans"]["lead"])}</p></div>')
    out.append('<div class="plans">')
    out.append('<input type="radio" name="plan" id="tab-a">')
    out.append('<input type="radio" name="plan" id="tab-b" checked>')
    out.append('<div class="plan-tabs">')
    out.append(f'<label for="tab-a">{_esc(content.UNIT_TYPES["A"]["plots"])}</label>')
    out.append(f'<label for="tab-b">{_esc(content.UNIT_TYPES["B"]["plots"])}</label>')
    out.append("</div>")
    out.append('<div class="plan-panes">')
    out.append(_plan_pane("A", crop_a))
    out.append(_plan_pane("B", crop_b))
    out.append("</div></div>")
    out.append("</div></section>")

    # the drawing sheet
    out.append('<section class="band" id="plots"><div class="wrap">')
    out.append('<div class="hd measure">')
    out.append(f"<h2>{_esc(s['layout']['title'])}</h2>")
    out.append(f'<p class="lead">{_esc(s["layout"]["lead"])}</p></div>')
    out.append('<div class="sheet"><div class="sheet-inner">')
    out.append('<div class="sheet-title"><b>LAYOUT PLAN</b>'
               f'<span>{_esc(p["name"])}, Waghodia Main Road, Vadodara</span></div>')
    out.append(f'<div class="map"><img src="{layout}" '
               'alt="Site plan showing 48 numbered plots, the internal roads, '
               'the common plot and the entry gate">')
    out.append(_plot_overlay())
    out.append("</div>")
    out.append('<p class="legend"><span><span class="swatch"></span>'
               "Tap a plot to enquire about that number</span>"
               f"<span>{_esc(s['layout']['body'][0])}</span></p>")
    out.append("</div></div>")
    out.append("</div></section>")

    # specifications
    out.append('<section><div class="wrap">')
    out.append('<div class="hd measure">')
    out.append(f"<h2>{_esc(s['specs']['title'])}</h2>")
    out.append(f'<p class="lead">{_esc(s["specs"]["lead"])}</p></div>')
    out.append('<dl class="spec-list">')
    for label, text in content.SPEC_GROUPS:
        out.append(f"<div><dt>{_esc(label)}</dt><dd>{_esc(text)}</dd></div>")
    out.append("</dl>")
    out.append('<div class="dim"><span>Across the campus</span></div>')
    out.append('<ul class="amenities">')
    out.extend(f"<li>{_esc(a)}</li>" for a in content.AMENITIES)
    out.append("</ul>")
    out.append("</div></section>")

    # location
    out.append('<section class="band"><div class="wrap">')
    out.append('<div class="hd measure">')
    out.append(f"<h2>{_esc(s['location']['title'])}</h2>")
    out.append(f'<p class="lead">{_esc(s["location"]["lead"])}</p></div>')
    out.append('<div class="measure">')
    out.extend(f"<p>{_esc(b)}</p>" for b in s["location"]["body"])
    out.append(f"<p>{_esc(p['site_address'])}</p>")
    out.append('<div class="actions">')
    out.append(f'<a class="btn" href="{p["maps_url"]}" target="_blank" '
               'rel="noopener">Open in Google Maps</a>')
    out.append("</div></div>")
    out.append("</div></section>")

    # contact
    out.append('<section><div class="wrap">')
    out.append('<div class="hd measure">')
    out.append(f"<h2>{_esc(s['contact']['title'])}</h2>")
    out.append(f'<p class="lead">{_esc(s["contact"]["lead"])}</p></div>')
    out.append('<div class="measure">')
    out.extend(f"<p>{_esc(b)}</p>" for b in s["contact"]["body"])
    out.append("</div>")
    out.append('<div class="contact-grid">')
    out.append(f'<div><h3>Call or message</h3><p>'
               f'<a href="{content.tel_link()}">{_esc(p["phone_display"])}</a><br>'
               f'<a href="{content.mail_link()}">{_esc(p["email"])}</a></p></div>')
    out.append(f'<div><h3>Site</h3><p>{_esc(p["site_address"])}</p></div>')
    out.append(f'<div><h3>{_esc(p["developer"])}</h3>'
               f'<p>{_esc(p["partners"])}<br>{_esc(p["regd_office"])}</p></div>')
    out.append("</div>")
    out.append('<div class="actions" style="margin-top:34px">')
    out.append(f'<a class="btn" href="{wa}" target="_blank" rel="noopener">'
               "Enquire on WhatsApp</a>")
    out.append(f'<a class="btn btn-quiet" href="{content.tel_link()}">'
               f'Call {_esc(p["phone_display"])}</a>')
    out.append("</div>")
    out.append("</div></section>")

    # footer
    out.append('<footer><div class="wrap">')
    out.append(f'<img src="{logo_small}" alt="Lake Tree Avenue">')
    out.append(f"<p>{_esc(p['developer'])}, a partnership of "
               f"{_esc(p['partners'])}<br>{_esc(p['regd_office'])}</p>")
    out.append("</div></footer>")

    # sticky bar
    out.append('<nav class="bar" aria-label="Contact">')
    out.append(f'<a href="{content.tel_link()}">Call</a>')
    out.append(f'<a href="{wa}" target="_blank" rel="noopener">WhatsApp</a>')
    out.append(f'<a href="{p["maps_url"]}" target="_blank" rel="noopener">'
               "Directions</a>")
    out.append("</nav>")

    out.append("</body></html>")
    return "".join(out)


def write(path: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render_html())
    return path
