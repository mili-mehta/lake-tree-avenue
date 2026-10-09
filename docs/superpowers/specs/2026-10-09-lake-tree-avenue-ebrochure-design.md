# Lake Tree Avenue — Clickable E-Brochure

**Date:** 2026-10-09
**Status:** Approved for planning

## 1. Purpose

Lake Tree Avenue launches without a hosted website. All buyer-facing collateral must
therefore be self-contained files that can be sent over WhatsApp, email, or shown on a
sales device, while still carrying live calls-to-action.

Two artefacts are produced from one content source:

- `Lake-Tree-Avenue.html` — a single self-contained HTML file for sales devices and
  anyone who will open an attachment in a browser.
- `Lake-Tree-Avenue-eBrochure.pdf` — an A4-landscape PDF with live link annotations,
  for WhatsApp broadcast and email.

**Success criteria**

1. Both files open with no network connection and no hosting of any kind.
2. Every CTA in both files reaches the sales line: call, WhatsApp, email, or Maps.
3. A recipient can identify a specific plot and enquire about that plot by number in
   one tap.
4. Content attributes the project to TAM Developers only.

## 2. Project facts (source of truth)

| Field | Value |
|---|---|
| Project | Lake Tree Avenue — New Age Townhouses |
| Developer | TAM Developers (Talati & Mehta) |
| Partners | Udit Talati & Kinjal Mehta |
| Site address | Lake Tree Avenue, Waghodia Main Road, next to Spunpipe & Construction Co., Kamlapura, Vadodara |
| Regd. office | 1-B Ramkrishna Chambers, BPC Road, Alkapuri, Vadodara 390007 |
| Phone / WhatsApp | +91 87587 56666 (same number) |
| Email | laketreeavenue@gmail.com |
| Units | 48 townhouse plots, 2BHK |
| Unit types | Type A = plots 01–06; Type B = plots 07–48 |
| Price | Not published. CTA reads "Price on call". |
| RERA | Not to be mentioned. Owner states not applicable. |

### 2.1 Facts explicitly superseded

The repository's `Lake Tree Avenue Marketing Strategy.md` and `lake tree brocure.pdf`
describe the **earlier, different project** — Lake Tree, Ajwa Road, by Leo Enterprise
(Prop. Kinjal Mehta). The following must NOT be carried into Avenue collateral:

- Leo Enterprise name, logo, or registered-office block
- RERA number `PR/GJ/VADODARA/VADODARA/OTHERS/RAA07983/010221`
- Ajwa Nimeta Main Road / Sikandarpura / F.P. No. 42 / "Opposite The Palace" address
- The old key-plan landmarks (The Palace, Pioneer Homoeopathic College, New RTO,
  Laxmi Film City, Ajwa Chokdi, Sardar Estate, Dove Deck, APMC)
- A-Type 3BHK plans and the old 2BHK plot dimensions
- Any valuation claim sourced to the Ajwa Nimeta corridor (e.g. 22.71% YoY)

The Waghodia Main Road location requires its own landmark set, written fresh.

### 2.2 Assets available

| Asset | Path | Use |
|---|---|---|
| Avenue logo | `images/174E3041-9C9A-4984-BD36-BA254A0E98E2.PNG` (1254², white bg) | Cover, footers |
| Townhouse render | `images/LAKE TREE.PNG` (1080², white letterbox bars) | Hero; must be cropped |
| Revised layout | `REV.LAYOUT - 07-10-2026.pdf` (1 page, 1684×2384pt, vector) | Plot map, floor plans, dimensions |
| Old brochure | `lake tree brocure.pdf` (8 pages, flat raster) | Specification and amenity copy only |

### 2.3 Unit dimensions (from REV.LAYOUT, authoritative)

Type B (plots 07–48): kitchen 10'-6" × 8'-1½"; bedroom 11'-0" × 12'-6"; bedroom
10'-1½" × 10'-7½"; att. toilet 6'-0" × 5'-0"; standing balcony 2'-0" wide; store; O.T.S.
Plot frontage 25'-3" [7.70 m], depth 39'-1" [11.91 m].

Type A (plots 01–06): kitchen 9'-9½" × 9'-1½"; bedroom 10'-9½" × 12'-6"; store;
standing balcony 2'-0" wide. Remaining dimensions to be read off the layout during
implementation; nothing is to be invented.

### 2.4 Specification and amenity copy (carried forward, still accurate)

Structure as per architect and structure design. Wall finish: putty on internal wall,
exposed brick work on front exterior wall, exterior paint on other exterior walls.
Flooring: vitrified in all rooms with skirting, anti-skid ceramic in all balconies.
Kitchen: granite platform with stainless steel sink, ceramic tiles up to lintel level.
Bathrooms: designer wall tiles up to lintel level, good quality sanitary and plumbing
fixtures, stone door frame. Electrical: good quality modular switches, AC point in
master bedroom, geyser point in all bathrooms. Doors and windows: elegant main door and
internal flush doors with laminate and stone frame, colour-anodised aluminium windows
with safety grills. Terrace: brick bed waterproofing. Anti-termite treatment at ground
level. Water tank: overhead and underground.

Campus: impressive gate with security cabin, large open-space parking, underground
cabling for a wire-free campus, Tremix concrete internal roads with paved sides,
roadside plantation and street lights, rain water harvesting, garbage storage
provision, landscape garden with community hall.

## 3. Content structure (both artefacts, same order)

1. **Cover** — logo, "New Age Townhouses", new-launch line, TAM Developers
2. **The project** — 48 two-bedroom townhouses, gated campus, Waghodia Main Road
3. **Render** — cropped townhouse image, full bleed
4. **Floor plans** — Type A and Type B, ground / first / terrace, with real dimensions
5. **Layout map** — all 48 plots, each tappable, prefilled per-plot enquiry
6. **Specifications and amenities** — §2.4 copy, grouped
7. **Location** — site address, Waghodia Main Road context, Google Maps link
8. **Contact** — partners, regd. office, call / WhatsApp / email

## 4. Artefact A — single-file HTML

**Constraints**

- One `.html` file. Zero external requests: no CDN scripts, no web fonts, no remote
  images. System font stack only.
- All imagery base64-inlined as JPEG (render, photos) or PNG (logo, line art).
- Target total size ≤ 4 MB; hard ceiling 6 MB. Source PNGs are 2.3 MB and 1.4 MB, so
  downscale and re-encode before inlining.
- Mobile-first. Must be readable at 360 px wide with no horizontal scroll.

**Interaction**

- Sticky bottom action bar on mobile: Call · WhatsApp · Directions.
- Plot map: SVG overlay on a rasterised layout image. Each plot is a hotspot; tap or
  hover reveals plot number and type, plus a WhatsApp link prefilled with
  `Hi, I'm interested in Plot <n> at Lake Tree Avenue.`
- Floor-plan toggle between Type A and Type B.
- No price anywhere; enquiry CTAs read "Price on call".

**Explicitly out of scope:** EMI calculator (no price), plot availability or sold
states (no data), RERA block, lead-capture form (no backend), analytics.

## 5. Artefact B — interactive PDF

- Built with PyMuPDF. A4 landscape, 842 × 595 pt, matching the existing brochure's
  page geometry.
- Same eight sections as §3.
- Every page carries a footer link strip with four live annotations:
  `tel:+918758756666`, `https://wa.me/918758756666?text=<encoded>`,
  `mailto:laketreeavenue@gmail.com`, and the Google Maps URL.
- The layout-map page carries one link annotation per plot, each with a prefilled
  per-plot WhatsApp message.
- Target size ≤ 8 MB so WhatsApp accepts it comfortably (WhatsApp's document limit is
  100 MB, but large files deter opening on mobile data).

## 6. Plot hotspot derivation

Plot numbers are extracted from `REV.LAYOUT - 07-10-2026.pdf` via PyMuPDF word
positions, filtered to the label glyph size (~29 × 26 pt) to exclude dimension text
(~7 × 5 pt).

**Known gap:** 41 of 48 numbers carry a text layer. Plots **08, 09, 10, 11, 12, 13 and
42** are outlined vector art with no extractable text.

**Mitigation:** those seven sit inside otherwise regular rows. Their centres are
interpolated from the pitch of their labelled neighbours, then verified by rendering
the layout with every hotspot drawn and inspecting the image. A hotspot that does not
land inside its plot is corrected by hand before the artefacts are generated.

Coordinates are normalised to fractions of page width and height so the same table
drives both the HTML SVG overlay and the PDF annotation rectangles.

## 7. Distribution (context, not built here)

No hosting means no landing URL, so Meta campaigns must use destinations that need no
website:

- **Click-to-WhatsApp ads** pointing at `wa.me/918758756666`, with the PDF sent as the
  auto-reply — lowest friction for this audience.
- **Instant Form lead ads**, with the PDF as the thank-you download.
- Organic launch posts on the Facebook page and Instagram, using 1:1 and 4:5 crops of
  the render.

Accepted consequence: no pixel, no retargeting, no site analytics, no SEO or AI-search
presence. Attribution is limited to what Meta reports plus inbound call and WhatsApp
volume.

## 8. Verification

| Check | Method |
|---|---|
| PDF annotations | Assert every expected URI is present, on the right page, with a rect inside page bounds, and that all 48 plot links carry distinct plot numbers |
| HTML self-containment | Assert no `http://`, `https://` or `//` references in `src`/`href` except `tel:`, `mailto:`, `wa.me` and the Maps link; assert zero external subresources |
| Size budget | Assert HTML ≤ 6 MB and PDF ≤ 8 MB |
| Plot hotspot accuracy | Render the layout with hotspots drawn; inspect visually; all 48 land inside their plot |
| Visual review | Render all PDF pages to PNG and review; open the HTML and review at 360 px and desktop widths |
| Superseded facts | Grep both artefacts for `Leo Enterprise`, `RAA07983`, `Ajwa`, `Sikandarpura`, `The Palace`, `3 BHK` — all must return zero hits |

## 9. Open items

- **RERA.** Owner states no RERA registration applies. Gujarat RERA exempts projects of
  ≤500 sq m of land or ≤8 units; 48 townhouses falls outside that, and Section 3 bars
  advertising a project that requires registration. Flagged once; collateral is being
  built without any RERA line per the owner's instruction. Confirm with counsel before
  the Meta campaign goes live.
- **Waghodia Road landmarks.** The old key plan cannot be reused. A landmark set for the
  Kamlapura / Waghodia Main Road location is needed; drafted during implementation and
  confirmed by the owner before publishing.
- **Google Maps URL.** Exact pin for the site to be supplied or derived and confirmed.
- **Type A dimensions.** To be read off the layout during implementation.
