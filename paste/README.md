# Copy-paste blocks for the Shopify editor

There are two routes. Pick one — you do not need both.

## Route A — one file in the code editor (fewest steps)

Use `nurva-home.liquid`.

1. **Online Store → Themes → ⋯ → Edit code**
2. In the **Sections** folder, click **Add a new section**
3. Name it `nurva-home` — Shopify adds the `.liquid` itself. If it complains
   about a `.liquid` extension you typed a name it did not like; plain
   lowercase letters and hyphens only, no spaces, no dots.
4. Delete whatever Shopify pre-filled, paste the whole file in, **Save**
5. **Customize → Add section → Nurva home**
6. Click the section and **pick your product** from the dropdown — no code
   editing needed

## Route B — six Custom Liquid blocks (no code editor)

Use the six numbered files. This route never asks for a filename.

1. **Online Store → Themes → Customize**
2. **Add section → Custom Liquid**
3. Paste one file into the **Liquid** box → **Save**
4. Repeat, keeping the blocks in order

| Order | File | What it is | Edit anything? |
|---|---|---|---|
| 1 | `1-styles.liquid` | All the styling | No |
| 2 | `2-scripts.liquid` | Animations, counters, FAQ | No |
| 3 | `3-hero.liquid` | Headline + scrolling band | No |
| 4 | `4-benefits.liquid` | Badges, science, stats, how it works | No |
| 5 | `5-compare-and-buy.liquid` | Comparison table + buy boxes | **Yes — your product handle** |
| 6 | `6-reviews-faq-cta.liquid` | Reviews, FAQ, email capture | No |

Blocks 1 and 2 look empty in the editor — that's expected, they're styles and scripts.

## Linking your product (Route B, block 5)

Route A uses a product picker instead — nothing to edit.


Near the top of `5-compare-and-buy.liquid`:

```liquid
{%- assign nurva_handle = 'nurva-performance-nasal-strips' -%}
```

Change the text in quotes to your product's **handle** — the last part of its URL:

```
yourstore.com/products/nurva-performance-nasal-strips
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ this bit
```

Then:

- **Three variants** on the product (e.g. 1 Pack / 3 Pack / 6 Pack) → all three cards
  fill in with live prices and working Add to cart buttons, in variant order.
- **One variant** → the first card goes live; the other two keep their placeholder
  prices and link to the product page instead.

Prices, compare-at prices and sold-out states all come from Shopify, so you never
have to edit a price in the code.

## Editing the words

The text sits directly in the HTML. Search the file for the sentence you want and
type over it. Everything is plain text except the product handle above.

## Notes

- **Nothing leaks into your theme.** Every style is scoped under `.nurva`, and a
  defensive reset stops your theme's styles from bleeding in. Tested against a
  theme that deliberately reuses the same class names.
- **No header or footer** — your theme already has those. (The full theme upload in
  the repo root includes Nurva-styled ones if you'd rather replace them.)
- Each file is under Shopify's 50,000-character limit for a Custom Liquid box.
- Regenerate these files after editing `assets/nurva.css`, `assets/nurva.js` or
  `preview/_body.html` with `python3 build-paste.py`.

## Which approach should I use?

Pasting is the quick route and keeps your current theme. Uploading the full theme
(see the main README) is better long-term: every heading, price and review becomes
editable from the theme editor with proper form fields, instead of hunting through
code. Both link to the same products.
