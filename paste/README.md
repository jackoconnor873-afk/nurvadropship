# Copy-paste blocks for the Shopify editor

Six blocks you paste into **Custom Liquid** sections. Unlike plain HTML, these use
Liquid — so block 5 pulls your real product price and its **Add to cart** buttons
actually work.

## Where to paste

1. Shopify admin → **Online Store → Themes → Customize**
2. Pick the page you want (usually **Home page** in the top dropdown)
3. **Add section → Custom Liquid**
4. Paste one file's entire contents into the **Liquid** box → **Save**
5. Repeat for each block, keeping them in order

Add six Custom Liquid sections, one per file, top to bottom:

| Order | File | What it is | Edit anything? |
|---|---|---|---|
| 1 | `1-styles.liquid` | All the styling | No |
| 2 | `2-scripts.liquid` | Animations, counters, FAQ | No |
| 3 | `3-hero.liquid` | Headline + scrolling band | No |
| 4 | `4-benefits.liquid` | Badges, science, stats, how it works | No |
| 5 | `5-compare-and-buy.liquid` | Comparison table + buy boxes | **Yes — your product handle** |
| 6 | `6-reviews-faq-cta.liquid` | Reviews, FAQ, email capture | No |

Blocks 1 and 2 look empty in the editor — that's expected, they're styles and scripts.

## Linking your product (block 5)

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
