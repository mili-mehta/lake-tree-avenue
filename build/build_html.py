"""Single-file HTML e-brochure.

Everything the page needs travels inside the document: images as base64 data
URIs, styles inline, no scripts. It is opened from file:// on phones, where
fetch, modules and service workers are blocked, so the plot map is built from
SVG anchors that work with no JavaScript at all.
"""
import html
import os

from build import assets, content

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

/* ---------- hero: the render edge to edge, titling beneath ---------- */
/* The render carries the logo and the name in its own top corner, so the
   page does not repeat the mark here; the band below it only names the
   address and offers the two ways in. */
.hero-figure { overflow: hidden; }
.hero-figure img { width: 100%; height: auto;
  animation: settle 7s cubic-bezier(.2,.6,.2,1) both; }
@keyframes settle { from { transform: scale(1.06); } to { transform: scale(1); } }
.hero-panel { background: #f3eadb; padding: 40px 0 44px; }
.hero h1 { margin-bottom: 18px; }
.hero-sub {
  font-family: var(--sans); font-size: 0.95rem; letter-spacing: 0.04em;
  color: var(--ink-soft); margin-bottom: 30px;
}

/* ---------- actions ---------- */
/* Two tiers only, and they share one geometry so a row of them keeps a
   straight baseline: the enquiry button is filled, everything else is the
   quiet outline. Both are at least 52px tall, which is a thumb. */
.actions { display: flex; flex-wrap: wrap; gap: 12px; }
.btn {
  display: inline-flex; align-items: center; gap: 10px; text-align: left;
  font-family: var(--sans); font-size: 0.97rem; font-weight: 600;
  text-decoration: none; padding: 14px 24px; min-height: 52px;
  border-radius: 2px; border: 1.5px solid var(--terra-deep);
  color: #ffffff; background: var(--terra-deep);
  transition: background-color .18s ease, border-color .18s ease;
}
.btn:hover, .btn:focus-visible { background: #7a4c22; border-color: #7a4c22; }
.btn:active { transform: translateY(1px); }
.btn-quiet { border-color: var(--rule); color: var(--ink); background: #ffffff; }
.btn-quiet:hover, .btn-quiet:focus-visible {
  background: #f6f1e8; border-color: var(--terra);
}

/* A glyph rides with its label, never instead of it: the networks' own
   marks are read faster than their names, but the name still has to be
   there for anyone who does not know the mark. */
.ico { display: block; flex: none; }
.with-ico { display: inline-flex; align-items: center; gap: 9px; }
.chips { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }
.chip {
  width: 48px; height: 48px; display: inline-flex; align-items: center;
  justify-content: center; border: 1px solid var(--rule); border-radius: 2px;
  background: #ffffff;
  transition: background-color .18s ease, border-color .18s ease;
}
.chip:hover, .chip:focus-visible {
  background: #f6f1e8; border-color: var(--terra);
}

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
  display: inline-flex; align-items: center; min-height: 46px;
  font-family: var(--sans); font-size: 0.93rem; font-weight: 600;
  padding: 12px 20px; border: 1px solid var(--rule); border-radius: 2px;
  cursor: pointer; background: #ffffff; color: var(--ink-soft);
  transition: background-color .18s ease, border-color .18s ease;
}
.plan-tabs label:hover { background: #f6f1e8; }
#tab-a:checked ~ .plan-tabs label[for="tab-a"],
#tab-b:checked ~ .plan-tabs label[for="tab-b"] {
  border-color: var(--terra); color: var(--terra-deep); background: #f6e9da;
}
.plan-pane { display: none; }
#tab-a:checked ~ .plan-panes .pane-a { display: block; }
#tab-b:checked ~ .plan-panes .pane-b { display: block; }
.plan-grid { display: grid; grid-template-columns: 1fr; gap: 30px; align-items: start; }
.plan-sheet { border: 1px solid var(--rule); background: #ffffff; padding: 14px;
  margin: 0; }
.plan-sheet + .plan-sheet { margin-top: 22px; }
.plan-sheet img { display: block; width: 100%; }
.plan-note {
  font-family: var(--sans); font-size: 0.86rem; color: var(--ink-soft);
  margin: 16px 0 0;
}
.plan-sheet figcaption {
  font-family: var(--sans); font-size: 0.8rem; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--ink-soft); padding-top: 12px;
}

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
.legend {
  font-family: var(--sans); font-size: 0.84rem; color: var(--ink-soft);
  margin-top: 14px; display: flex; gap: 22px; flex-wrap: wrap;
}
.inline-cta { font-family: var(--sans); font-size: 0.88rem; }

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
footer img { width: 128px; margin-bottom: 18px; }

/* ---------- sticky bar, phones only ---------- */
.bar { position: fixed; left: 0; right: 0; bottom: 0; display: flex;
  background: #ffffff; border-top: 1px solid var(--rule); z-index: 20; }
/* Glyph over label, and the bottom padding clears the home-bar inset so
   the last row is tappable on a notched phone. */
.bar a { flex: 1; display: flex; flex-direction: column; align-items: center;
  gap: 5px; padding: 11px 6px calc(11px + env(safe-area-inset-bottom, 0px));
  font-family: var(--sans); font-size: 0.8rem; font-weight: 600;
  letter-spacing: 0.02em; text-decoration: none; color: var(--ink); }
.bar a + a { border-left: 1px solid var(--rule); }
.bar a:active { background: #f6f1e8; }

@media (min-width: 820px) {
  body { font-size: 19px; }
  section { padding: 110px 0; }
  .hero-panel { padding: 54px 0 58px; }
  .plan-grid { grid-template-columns: 1.55fr 1fr; gap: 46px; }
  /* Drawings with their dimensions printed inside them need the full
     measure; the schedule goes underneath rather than alongside. */
  .plan-grid-stacked { grid-template-columns: 1fr; gap: 34px; }
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


# The two social marks are the networks' own artwork, down to Instagram's
# gradient and Facebook's blue, because a buyer scanning a phone screen
# recognises those before any word. WhatsApp, the handset, the pin and the
# sheet are drawn on the same 24-unit grid so they carry equal weight
# beside them.
IG_GRADIENT = (
    '<svg class="defs" width="0" height="0" aria-hidden="true" '
    'focusable="false"><defs>'
    '<linearGradient id="ig" x1="2" y1="22" x2="22" y2="2" '
    'gradientUnits="userSpaceOnUse">'
    '<stop offset="0" stop-color="#FEDA75"/>'
    '<stop offset=".25" stop-color="#FA7E1E"/>'
    '<stop offset=".5" stop-color="#D62976"/>'
    '<stop offset=".75" stop-color="#962FBF"/>'
    '<stop offset="1" stop-color="#4F5BD5"/>'
    "</linearGradient></defs></svg>"
)

_STROKE = ('fill="none" stroke="currentColor" stroke-width="1.7" '
           'stroke-linecap="round" stroke-linejoin="round"')

ICONS = {
    "whatsapp": (
        'fill="#25D366"',
        '<path d="M17.47 14.38c-.3-.15-1.76-.87-2.03-.97-.27-.1-.47-.15-.67.15'
        '-.2.3-.77.97-.97 1.16-.2.2-.4.22-.69.08-.3-.15-1.26-.47-2.39-1.48'
        '-.88-.79-1.48-1.76-1.65-2.06-.17-.3-.02-.46.13-.6.13-.14.35-.45'
        '.52-.67.17-.22.23-.4.35-.72.11-.32.06-.6-.03-.74-.08-.15-.67-1.62'
        '-.91-2.21-.25-.58-.49-.5-.67-.51h-.57c-.2 0-.52.07-.8.37-.27.3'
        '-1.04 1.02-1.04 2.48 0 1.46 1.07 2.87 1.22 3.07.15.2 2.1 3.2 5.08'
        ' 4.49.7.3 1.26.49 1.69.62.71.23 1.36.2 1.87.12.57-.08 1.76-.72 '
        '2.01-1.41.25-.7.25-1.29.17-1.41-.07-.13-.27-.2-.57-.35z"/>'
        '<path d="M20.46 3.49A11.82 11.82 0 0 0 12.05 0C5.5 0 .16 5.34.16 '
        '11.89c0 2.1.54 4.14 1.58 5.95L.06 24l6.3-1.65a11.88 11.88 0 0 0 '
        '5.69 1.45c6.55 0 11.89-5.34 11.89-11.9 0-3.17-1.23-6.16-3.48-8.41z'
        'M12.05 21.78a9.87 9.87 0 0 1-5.03-1.38l-.36-.21-3.74.98 1-3.65'
        '-.24-.37a9.86 9.86 0 0 1-1.51-5.26 9.89 9.89 0 0 1 16.87-6.99 '
        '9.83 9.83 0 0 1 2.9 6.99 9.89 9.89 0 0 1-9.89 9.89z"/>'
    ),
    "facebook": (
        'fill="#1877F2"',
        '<path d="M24 12.07C24 5.44 18.63.07 12 .07S0 5.44 0 12.07c0 5.99 '
        '4.39 10.95 10.13 11.85v-8.38H7.08v-3.47h3.05V9.43c0-3.01 1.79-4.67 '
        '4.53-4.67 1.31 0 2.69.24 2.69.24v2.95h-1.51c-1.49 0-1.96.93-1.96 '
        '1.87v2.25h3.33l-.53 3.47h-2.8v8.38C19.61 23.02 24 18.06 24 12.07z"/>'
    ),
    "instagram": (
        'fill="url(#ig)"',
        '<path d="M12 2.16c3.2 0 3.58.01 4.85.07 1.17.05 1.8.25 2.23.41.56.22'
        ' .96.48 1.38.9.42.42.68.82.9 1.38.17.43.36 1.06.41 2.23.06 1.27.07 '
        '1.65.07 4.85s-.01 3.58-.07 4.85c-.06 1.17-.25 1.8-.42 2.23-.22.56'
        '-.48.96-.9 1.38-.42.42-.82.68-1.38.9-.42.16-1.06.36-2.23.41-1.27.06'
        '-1.65.07-4.85.07s-3.59-.01-4.86-.07c-1.17-.06-1.82-.26-2.24-.42'
        '-.57-.22-.96-.48-1.38-.9-.42-.42-.69-.82-.9-1.38-.16-.42-.36-1.06'
        '-.42-2.23-.04-1.26-.06-1.65-.06-4.84 0-3.2.02-3.59.06-4.86.06-1.17'
        '.26-1.81.42-2.23.21-.57.48-.96.9-1.38.42-.42.81-.69 1.38-.9.42-.17'
        '1.05-.36 2.22-.42 1.28-.05 1.65-.06 4.86-.06zM12 0C8.74 0 8.33.01 '
        '7.05.07 5.78.13 4.91.33 4.14.63c-.79.31-1.46.72-2.13 1.38A5.9 5.9 0'
        ' 0 0 .63 4.14C.33 4.91.13 5.78.07 7.05.01 8.33 0 8.74 0 12s.01 3.67'
        '.07 4.95c.06 1.27.26 2.14.56 2.91.3.79.72 1.46 1.38 2.13a5.9 5.9 0 '
        '0 0 2.13 1.38c.77.3 1.64.5 2.91.56C8.33 23.99 8.74 24 12 24s3.67'
        '-.01 4.95-.07c1.27-.06 2.15-.26 2.91-.56.79-.31 1.46-.72 2.13-1.38'
        'a5.9 5.9 0 0 0 1.38-2.13c.3-.76.5-1.64.56-2.91.06-1.28.07-1.69.07'
        '-4.95s-.01-3.67-.07-4.95c-.06-1.27-.26-2.15-.56-2.91a5.9 5.9 0 0 0'
        '-1.38-2.13A5.9 5.9 0 0 0 19.86.63c-.76-.3-1.64-.5-2.91-.56C15.67.01'
        ' 15.26 0 12 0z"/>'
        '<path d="M12 5.84a6.16 6.16 0 1 0 0 12.32 6.16 6.16 0 0 0 0-12.32zM12'
        ' 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8z"/>'
        '<circle cx="18.41" cy="5.59" r="1.44"/>'
    ),
    "phone": (
        'fill="currentColor"',
        '<path d="M6.62 10.79a15.05 15.05 0 0 0 6.59 6.59l2.2-2.2a1 1 0 0 1 '
        '1.02-.24c1.12.37 2.33.57 3.57.57a1 1 0 0 1 1 1V20a1 1 0 0 1-1 1C10.3'
        ' 21 3 13.7 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.24.2 2.45.57 '
        '3.57a1 1 0 0 1-.25 1.02l-2.2 2.2z"/>'
    ),
    "pin": (
        _STROKE,
        '<path d="M12 21.5s7-6.4 7-11.5a7 7 0 1 0-14 0c0 5.1 7 11.5 7 11.5z"/>'
        '<circle cx="12" cy="10" r="2.6"/>'
    ),
    "sheet": (
        _STROKE,
        '<path d="M3.5 4.5h17v15h-17z"/><path d="M10 4.5v15"/>'
        '<path d="M10 12h10.5"/>'
    ),
    "mail": (
        _STROKE,
        '<path d="M3.5 5.5h17v13h-17z"/><path d="m4 6.5 8 6 8-6"/>'
    ),
}


def _icon(name: str, size: int = 20) -> str:
    """One decorative glyph; the link or button around it carries the words."""
    paint, body = ICONS[name]
    return (f'<svg class="ico" width="{size}" height="{size}" '
            f'viewBox="0 0 24 24" {paint} aria-hidden="true" '
            f'focusable="false">{body}</svg>')


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


def _plan_pane(key: str, sheets: list[tuple[str, str]]) -> str:
    """One tab's drawings and its schedule.

    `sheets` is (caption, data-uri) in the order a visitor walks the house.
    A pane carrying more than one drawing drops the side-by-side grid and
    runs them full width instead: these drawings have their room sizes
    printed inside them, and in a 55%-wide column those figures are too
    small to read.
    """
    unit = content.UNIT_TYPES[key]
    rows = "".join(
        f"<tr><th scope=\"row\">{_esc(room)}</th><td>{_esc(dim)}</td></tr>"
        for room, dim in unit["rooms"]
    )
    plots = _esc(unit["plots"].lower())
    figures = "".join(
        f'<figure class="plan-sheet"><img src="{uri}" '
        f'alt="{_esc(caption)} plan for {plots}, with room dimensions">'
        f"<figcaption>{_esc(caption)}</figcaption></figure>"
        for caption, uri in sheets
    )
    note = f'<p class="plan-note">{_esc(content.PLAN_PAIR_NOTE)}</p>'
    stacked = " plan-grid-stacked" if len(sheets) > 1 else ""
    return (
        f'<div class="plan-pane pane-{key.lower()}">'
        f'<div class="plan-grid{stacked}">'
        f"<div>{figures}{note}</div>"
        f'<div><table class="schedule">{rows}</table></div>'
        f"</div></div>"
    )


def render_html() -> str:
    p = content.PROJECT
    logo_small = assets.data_uri(assets.logo_png(260), "image/png")
    render = assets.data_uri(assets.render_jpeg(1600), "image/jpeg")
    layout = assets.data_uri(assets.site_plan_jpeg(1500), "image/jpeg")
    elevation = assets.data_uri(assets.plan_crops()["elevation"], "image/jpeg")
    plan_sheets = {}
    for key, unit in content.UNIT_TYPES.items():
        blobs = assets.plan_sheets(key)
        plan_sheets[key] = [
            (sheet["caption"],
             assets.data_uri(blobs[sheet["key"]], "image/jpeg"))
            for sheet in unit["sheets"]
        ]

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
    out.append(IG_GRADIENT)

    # hero
    out.append('<header class="hero">')
    out.append(f'<div class="hero-figure"><img src="{render}" '
               'alt="Lake Tree Avenue townhouses along the avenue">'
               "</div>")
    out.append('<div class="hero-panel"><div class="wrap">')
    out.append(f"<h1>{_esc(s['cover']['title'])}</h1>")
    out.append(
        f'<p class="hero-sub">{_esc(s["cover"]["body"][0])}<br>'
        f'{_esc(s["cover"]["body"][1])}</p>')
    out.append('<div class="actions">')
    out.append(f'<a class="btn" href="{wa}" target="_blank" rel="noopener">'
               f'{_icon("whatsapp")}Enquire on WhatsApp</a>')
    out.append(f'<a class="btn btn-quiet" href="{content.tel_link()}">'
               f'{_icon("phone")}Call {_esc(p["phone_display"])}</a>')
    out.append('<a class="btn btn-quiet" href="#plots">'
               f'{_icon("sheet")}See the plot map</a>')
    out.append("</div></div></div>")
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
    out.append(_plan_pane("A", plan_sheets["A"]))
    out.append(_plan_pane("B", plan_sheets["B"]))
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
    out.append("</div>")
    out.append(f'<p class="legend"><span>{_esc(s["layout"]["body"][0])}</span>'
               "<span>Ask us which plots are still open</span></p>")
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
    out.append("</div>")
    rows = "".join(
        f'<tr><th scope="row">{_esc(k)}</th><td>{_esc(v)}</td></tr>'
        for k, v in content.LOCATION_ROWS)
    out.append(f'<table class="schedule">{rows}</table>')
    out.append('<div class="actions" style="margin-top:30px">')
    out.append(f'<a class="btn btn-quiet" href="{p["maps_url"]}" '
               f'target="_blank" rel="noopener">{_icon("pin")}'
               f'{_esc(p["site_address"])}</a>')
    out.append("</div>")
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
    out.append(
        f'<div><h3>Call or message</h3><p>'
        f'<a class="with-ico" href="{content.tel_link()}">{_icon("phone", 18)}'
        f'{_esc(p["phone_display"])}</a><br>'
        f'<a class="with-ico inline-cta" data-cta="whatsapp" href="{wa}" '
        f'target="_blank" rel="noopener">{_icon("whatsapp", 18)}'
        f'WhatsApp {_esc(p["phone_display"])}</a><br>'
        f'<a class="with-ico" href="{content.mail_link()}">{_icon("mail", 18)}'
        f'{_esc(p["email"])}</a></p></div>')
    out.append(f'<div><h3>Site</h3><p><a class="with-ico" '
               f'href="{p["maps_url"]}" target="_blank" rel="noopener">'
               f'{_icon("pin", 18)}{_esc(p["site_address"])}</a></p></div>')
    out.append(f'<div><h3>Developer</h3>'
               f'<p>{_esc(content.CREDIT)}<br>{_esc(p["regd_office"])}</p></div>')
    handle = _esc(p["social_handle"])
    out.append(
        f'<div><h3>Follow</h3><p>{handle} on Instagram and Facebook</p>'
        f'<div class="chips">'
        f'<a class="chip" href="{p["instagram_url"]}" target="_blank" '
        f'rel="noopener" aria-label="Instagram {handle}">'
        f'{_icon("instagram", 24)}</a>'
        f'<a class="chip" href="{p["facebook_url"]}" target="_blank" '
        f'rel="noopener" aria-label="Facebook {handle}">'
        f'{_icon("facebook", 24)}</a>'
        f'<a class="chip" href="{wa}" target="_blank" rel="noopener" '
        f'aria-label="WhatsApp {_esc(p["phone_display"])}">'
        f'{_icon("whatsapp", 24)}</a>'
        f'<a class="chip" href="{content.tel_link()}" '
        f'aria-label="Call {_esc(p["phone_display"])}">'
        f'{_icon("phone", 24)}</a>'
        f"</div></div>")
    out.append("</div>")
    out.append('<div class="actions" style="margin-top:34px">')
    out.append(f'<a class="btn" href="{wa}" target="_blank" rel="noopener">'
               f'{_icon("whatsapp")}Enquire on WhatsApp</a>')
    out.append(f'<a class="btn btn-quiet" href="{content.tel_link()}">'
               f'{_icon("phone")}Call {_esc(p["phone_display"])}</a>')
    out.append("</div>")
    out.append("</div></section>")

    # footer
    out.append('<footer><div class="wrap">')
    out.append(f'<img src="{logo_small}" alt="Lake Tree Avenue">')
    out.append(f"<p>{_esc(content.CREDIT)}<br>{_esc(p['regd_office'])}</p>")
    out.append("</div></footer>")

    # sticky bar
    out.append('<nav class="bar" aria-label="Contact">')
    out.append(f'<a href="{content.tel_link()}">{_icon("phone", 22)}Call</a>')
    out.append(f'<a href="{wa}" target="_blank" rel="noopener">'
               f'{_icon("whatsapp", 22)}WhatsApp</a>')
    out.append(f'<a href="{p["maps_url"]}" target="_blank" rel="noopener">'
               f'{_icon("pin", 22)}Directions</a>')
    out.append("</nav>")

    out.append("</body></html>")
    return "".join(out)


def write(path: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render_html())
    return path
