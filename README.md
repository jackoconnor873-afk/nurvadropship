# Nurva Performance — Shopify theme

A complete, animated Shopify Online Store 2.0 theme for **Nurva Performance Nasal Strips**.
Black / teal / white, heavy condensed display type, scroll animations throughout —
built to sit alongside brands like Intake and Breathe Right without looking like either.

**Brand voice used throughout:** *Perform | Breathe | Recover* · *Breathe Pure | Live Pure*

---

## Two ways to use this

### Option A — Upload the whole theme (recommended)

This gives you the full site: homepage, product page, collection, cart, blog, search,
404, and customer accounts, all editable from the Shopify theme editor.

1. Download this repository as a ZIP (**Code → Download ZIP** on GitHub), then unzip it.
2. **Important:** re-zip only the theme folders, not the outer wrapper folder. Select these
   and compress them together:

   ```
   assets/  config/  layout/  locales/  sections/  snippets/  templates/
   ```

   (Leave out `preview/`, `README.md` and `build-preview.sh` — Shopify ignores them, but a
   clean zip uploads faster.)
3. In Shopify admin go to **Online Store → Themes → Add theme → Upload zip file**.
4. Click **Customize** to edit any text, colour or image without touching code.
5. When you're happy, **Publish**.

### Option B — Paste the HTML into your existing theme

`preview/index.html` is a single self-contained file — all CSS and JavaScript are inlined,
nothing external except Google Fonts.

- **To preview:** open it in any browser.
- **To use inside Shopify:** in the theme editor add a **Custom Liquid** section to a page and
  paste in the parts you want. Or create a new page template and paste the whole `<body>`
  contents.

Option A is the better long-term choice — Option B can't be edited from the theme editor.

---

## Adding your product photos

The design deliberately ships with **no images**, so nothing of yours gets overwritten.
Where a photo belongs, you'll see a dashed placeholder box saying "Add your product image".

To add them: **Customize → click the section → Image → Select image**. The spots are:

| Section | What to put there |
|---|---|
| Hero | Wide, dark, high-contrast background shot (or leave empty for pure black) |
| "Your nose is the bottleneck" | Your product pouch shot |
| "One strip. Three jobs." | A lifestyle / training shot |
| Product page | Your product photos, uploaded to the product itself in **Products** |

Hero images work best dark and moody — the theme layers a black gradient over them so the
headline stays readable.

---

## Homepage sections (in order)

1. **Announcement bar** — rotating trust messages
2. **Hero** — line-by-line animated headline, breathing pulse rings, proof badges
3. **Marquee** — scrolling PERFORM · BREATHE · RECOVER · PRO band
4. **Badge row** — the four circular badges from your pouch (10 hours, sweat proof, performance boost, snoring relief), with a count-up animation
5. **Feature split — the science** — image + benefit list
6. **Stats band** — numbers that count up when scrolled into view
7. **How it works** — four numbered steps on a connecting line
8. **Feature split — use cases** — training, sleep, allergy season
9. **Comparison table** — Nurva vs drug-store strips vs internal dilators
10. **Bundles** — 1 / 3 / 6-pack pricing with a highlighted "most popular" card
11. **Testimonials** — swipeable review cards
12. **FAQ** — animated accordion
13. **CTA band** — email capture for the 15% first-order offer

Every section can be reordered, duplicated, hidden or removed in the theme editor.
All copy is editable — nothing is hard-coded.

---

## Connecting the bundle buttons to real products

The bundle cards show placeholder prices until you connect them.

1. Create your products in **Products** (e.g. "Nurva Pro — 1 Pack", "3 Pack", "6 Pack").
2. **Customize → Bundles section →** click a pack → **Product → Select product**.

Once connected, the card pulls the live price and compare-at price automatically, and the
button adds straight to cart without a page reload.

---

## Changing the colours

**Customize → Theme settings → Colours.** The defaults match your packaging:

| Token | Hex |
|---|---|
| Background | `#05070a` |
| Raised background | `#0a0e13` |
| Accent (teal) | `#14a5b8` |
| Accent bright | `#3bddef` |
| Accent deep | `#0c7280` |
| Text | `#f4f7f9` |

---

## Menus

Create these in **Online Store → Navigation** so the header and footer fill in:

- `main-menu` — Shop, Science, How it works, Reviews, FAQ
- `footer` — whatever you want in the footer's Shop column

---

## Regenerating the standalone HTML

If you edit `assets/nurva.css`, `assets/nurva.js` or `preview/_body.html`, rebuild the
single-file version with:

```bash
./build-preview.sh
```

---

## A note on the claims in the copy

The placeholder copy includes performance figures (38% more airflow, 10-hour hold, 4.8 rating,
2,400+ customers) and a medical disclaimer in the footer. **Replace the numbers with figures you
can actually substantiate before you go live** — nasal strips are a regulated product category in
most markets, and unsupported health claims are the fastest way to get an ad account or a store
shut down. The footer disclaimer is a starting point, not legal advice; have it reviewed for the
markets you sell into.

---

## Technical notes

- No build step, no dependencies, no jQuery — plain CSS and vanilla JavaScript.
- All animations respect `prefers-reduced-motion`.
- Fully responsive; the header collapses to a slide-in drawer below 990px.
- Fonts: Barlow Condensed (display), Montserrat (brand), Inter (body), loaded async from Google Fonts.
- Works with the theme editor — sections re-initialise their animations when you edit them.
