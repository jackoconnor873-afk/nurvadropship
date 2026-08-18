#!/usr/bin/env python3
"""
Builds paste/*.liquid — copy-paste blocks for Shopify's "Custom Liquid" section.

Differences from the uploadable theme:
  * All CSS is scoped under .nurva so it cannot leak into the host theme.
  * No header / footer / drawer (the host theme already has those).
  * The bundle buttons are real Liquid product forms, so they add to cart.
  * Each file stays well under Shopify's 50,000-character liquid-setting limit.
"""
import re, os

ROOT = os.path.dirname(os.path.abspath(__file__))
def read(p): return open(os.path.join(ROOT, p), encoding='utf-8').read()

PREFIX = '.nurva'

# ---------------------------------------------------------------- CSS scoping

def minify_css(css):
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    css = re.sub(r'\s+', ' ', css)
    css = re.sub(r'\s*([{};,])\s*', r'\1', css)
    css = re.sub(r';\}', '}', css)
    return css.strip()

def scope_selector(sel, p):
    sel = sel.strip()
    if sel in (':root', 'html', 'body'):
        return p
    if sel == '*':
        return p + ',' + p + ' *'
    if sel.startswith('*::') or sel.startswith('*:'):
        return p + ' *' + sel[1:]
    return p + ' ' + sel

def scope_css(css, p):
    """Prefix every rule with `p`, recursing into @media/@supports and
    leaving @keyframes/@font-face bodies alone."""
    out, i, n = [], 0, len(css)
    while i < n:
        j = css.find('{', i)
        if j == -1:
            out.append(css[i:])
            break
        prelude = css[i:j].strip()
        depth, k = 1, j + 1
        while k < n and depth:
            if css[k] == '{': depth += 1
            elif css[k] == '}': depth -= 1
            k += 1
        body = css[j + 1:k - 1]
        if prelude.startswith('@'):
            at = re.split(r'[\s(]', prelude, 1)[0].lower()
            if at in ('@media', '@supports', '@layer', '@container'):
                out.append(prelude + '{' + scope_css(body, p) + '}')
            else:                      # @keyframes, @font-face …
                out.append(prelude + '{' + body + '}')
        else:
            sels = [s for s in prelude.split(',') if s.strip()]
            out.append(','.join(scope_selector(s, p) for s in sels) + '{' + body + '}')
        i = k
    return ''.join(out)

# ---------------------------------------------------------------- JS trimming

def trim_js(js):
    js = re.sub(r'/\*.*?\*/', '', js, flags=re.S)
    keep = []
    for line in js.split('\n'):
        s = line.strip()
        if not s or s.startswith('//'):
            continue
        keep.append(s)
    return '\n'.join(keep)

# ---------------------------------------------------------------- body chunks

body = read('preview/_body.html')
chunks, order = {}, []
parts = re.split(r'<!--\s*=+\s*([A-Z][A-Z &]*?)\s*=+\s*-->', body)
for idx in range(1, len(parts), 2):
    name = parts[idx].strip()
    chunks[name] = parts[idx + 1]
    order.append(name)

def clean(html):
    html = html.replace('<main id="top">', '').replace('</main>', '')
    for a, b in [('id="how"', 'id="nurva-how"'), ('id="shop"', 'id="nurva-bundles"'),
                 ('id="science"', 'id="nurva-science"'), ('id="reviews"', 'id="nurva-reviews"'),
                 ('id="faq"', 'id="nurva-faq"'),
                 ('href="#how"', 'href="#nurva-how"'), ('href="#shop"', 'href="#nurva-bundles"'),
                 ('href="#science"', 'href="#nurva-science"'), ('href="#reviews"', 'href="#nurva-reviews"'),
                 ('href="#faq"', 'href="#nurva-faq"')]:
        html = html.replace(a, b)
    return html.strip('\n')

def wrap(*names):
    inner = '\n\n'.join(clean(chunks[n]) for n in names)
    return '<div class="nurva">\n' + inner + '\n</div>\n'

# ---------------------------------------------------------------- bundles (Liquid)

BUNDLES_LIQUID = r'''{%- comment -%}
  ==========================================================================
  LINK YOUR PRODUCT — change the handle on the next line to your product's.
  The handle is the last part of the product URL, e.g.
  yourstore.com/products/nurva-performance-nasal-strips
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  If your product has 3 variants (1 Pack / 3 Pack / 6 Pack) all three cards
  fill in automatically. With one variant, only the first card is live.
  ==========================================================================
{%- endcomment -%}

{%- assign nurva_handle = 'nurva-performance-nasal-strips' -%}

{%- assign np = all_products[nurva_handle] -%}
{%- assign v1 = np.variants[0] -%}
{%- assign v2 = np.variants[1] -%}
{%- assign v3 = np.variants[2] -%}

<div class="nurva">
<section class="section" id="nurva-bundles">
  <div class="wrap">
    <div class="sec-head sec-head--center stack" data-reveal>
      <span class="eyebrow">Choose your pack</span>
      <h2 class="h2">Stock up and save</h2>
      <p class="lede">Most people use one strip a night. The 3-pack is where the maths starts working in your favour.</p>
    </div>

    <div class="bundles reveal-stagger">

      <!-- ---------- Pack 1 ---------- -->
      <div class="bundle">
        <div>
          <div class="bundle__qty">Starter</div>
          <div class="bundle__sub">30 strips &middot; 1 month</div>
        </div>
        <div>
          <div class="bundle__price">
            <span class="bundle__now">{% if v1 %}{{ v1.price | money }}{% else %}$24.99{% endif %}</span>
            {%- if v1 and v1.compare_at_price > v1.price -%}
              <span class="bundle__was">{{ v1.compare_at_price | money }}</span>
            {%- endif -%}
          </div>
        </div>
        <ul class="bundle__list stack">
          <li><span>&#10003;</span><span>30 sweat-proof strips</span></li>
          <li><span>&#10003;</span><span>Tracked shipping</span></li>
          <li><span>&#10003;</span><span>30-night guarantee</span></li>
        </ul>
        {%- if v1 -%}
          <form method="post" action="{{ routes.cart_add_url }}">
            <input type="hidden" name="id" value="{{ v1.id }}">
            <input type="hidden" name="quantity" value="1">
            <button type="submit" class="btn btn--block btn--ghost">
              {% if v1.available %}Add to cart{% else %}Sold out{% endif %}
            </button>
          </form>
        {%- else -%}
          <a class="btn btn--block btn--ghost" href="{{ routes.all_products_collection_url }}">Shop now</a>
        {%- endif -%}
      </div>

      <!-- ---------- Pack 2 (highlighted) ---------- -->
      <div class="bundle bundle--best">
        <span class="bundle__flag">Most popular</span>
        <div>
          <div class="bundle__qty">3-Pack</div>
          <div class="bundle__sub">90 strips &middot; 3 months</div>
        </div>
        <div>
          <div class="bundle__price">
            <span class="bundle__now">{% if v2 %}{{ v2.price | money }}{% else %}$59.99{% endif %}</span>
            {%- if v2 and v2.compare_at_price > v2.price -%}
              <span class="bundle__was">{{ v2.compare_at_price | money }}</span>
            {%- else -%}
              <span class="bundle__was">$74.97</span>
            {%- endif -%}
          </div>
          <div class="bundle__save">Save 20% &middot; $0.66 per night</div>
        </div>
        <ul class="bundle__list stack">
          <li><span>&#10003;</span><span>90 sweat-proof strips</span></li>
          <li><span>&#10003;</span><span>Free express shipping</span></li>
          <li><span>&#10003;</span><span>30-night guarantee</span></li>
          <li><span>&#10003;</span><span>Free travel tin</span></li>
        </ul>
        {%- if v2 -%}
          <form method="post" action="{{ routes.cart_add_url }}">
            <input type="hidden" name="id" value="{{ v2.id }}">
            <input type="hidden" name="quantity" value="1">
            <button type="submit" class="btn btn--block">
              {% if v2.available %}Add to cart{% else %}Sold out{% endif %}
            </button>
          </form>
        {%- else -%}
          <a class="btn btn--block" href="{% if np %}{{ np.url }}{% else %}{{ routes.all_products_collection_url }}{% endif %}">Shop now</a>
        {%- endif -%}
      </div>

      <!-- ---------- Pack 3 ---------- -->
      <div class="bundle">
        <div>
          <div class="bundle__qty">6-Pack</div>
          <div class="bundle__sub">180 strips &middot; 6 months</div>
        </div>
        <div>
          <div class="bundle__price">
            <span class="bundle__now">{% if v3 %}{{ v3.price | money }}{% else %}$104.99{% endif %}</span>
            {%- if v3 and v3.compare_at_price > v3.price -%}
              <span class="bundle__was">{{ v3.compare_at_price | money }}</span>
            {%- else -%}
              <span class="bundle__was">$149.94</span>
            {%- endif -%}
          </div>
          <div class="bundle__save">Save 30% &middot; $0.58 per night</div>
        </div>
        <ul class="bundle__list stack">
          <li><span>&#10003;</span><span>180 sweat-proof strips</span></li>
          <li><span>&#10003;</span><span>Free express shipping</span></li>
          <li><span>&#10003;</span><span>30-night guarantee</span></li>
          <li><span>&#10003;</span><span>Free travel tin</span></li>
        </ul>
        {%- if v3 -%}
          <form method="post" action="{{ routes.cart_add_url }}">
            <input type="hidden" name="id" value="{{ v3.id }}">
            <input type="hidden" name="quantity" value="1">
            <button type="submit" class="btn btn--block btn--ghost">
              {% if v3.available %}Add to cart{% else %}Sold out{% endif %}
            </button>
          </form>
        {%- else -%}
          <a class="btn btn--block btn--ghost" href="{% if np %}{{ np.url }}{% else %}{{ routes.all_products_collection_url }}{% endif %}">Shop now</a>
        {%- endif -%}
      </div>

    </div>

    <p class="center muted" style="margin-top:26px;font-size:.8rem">
      Free shipping over $35 &middot; 30-night guarantee
    </p>
  </div>
</section>
</div>
'''

# ---------------------------------------------------------------- assemble

# Build the markup first so we know which classes are actually used, then keep
# only the CSS rules those classes need. The full stylesheet also covers the
# header, footer, cart, product page and card grids, none of which appear in
# these pasted blocks.

markup = {
    '3-hero.liquid': ('NURVA — Block 3 of 6: hero + scrolling band.', wrap('HERO', 'MARQUEE')),
    '4-benefits.liquid': ('NURVA — Block 4 of 6: badges, science, stats, how it works, use cases.',
                          wrap('BADGE ROW', 'SCIENCE SPLIT', 'STATS', 'HOW IT WORKS', 'USE CASES')),
    '5-compare-and-buy.liquid': ('NURVA — Block 5 of 6: comparison table + buy boxes. EDIT THE HANDLE BELOW.',
                                 wrap('COMPARISON') + '\n' + BUNDLES_LIQUID),
    '6-reviews-faq-cta.liquid': ('NURVA — Block 6 of 6: reviews, FAQ, email capture.',
                                 wrap('TESTIMONIALS', 'FAQ', 'CTA BAND')),
}

all_markup = '\n'.join(m for _, m in markup.values())
used = set(re.findall(r'class="([^"]*)"', all_markup))
used = {c for group in used for c in group.split()}
# classes the scripts add at runtime, plus the wrapper itself
used |= {'nurva', 'is-in', 'is-stuck', 'is-visible', 'no-js', 'placeholder-svg'}

def rule_is_used(selectors):
    """Keep a rule if every class it names is present in the markup."""
    for sel in selectors.split(','):
        classes = re.findall(r'\.([A-Za-z0-9_-]+)', sel)
        classes = [c for c in classes if c != 'nurva']
        if all(c in used for c in classes):
            return True
    return False

def prune(css):
    out, i, n = [], 0, len(css)
    while i < n:
        j = css.find('{', i)
        if j == -1:
            out.append(css[i:]); break
        prelude = css[i:j].strip()
        depth, k = 1, j + 1
        while k < n and depth:
            if css[k] == '{': depth += 1
            elif css[k] == '}': depth -= 1
            k += 1
        bodytext = css[j + 1:k - 1]
        if prelude.startswith('@'):
            at = re.split(r'[\s(]', prelude, 1)[0].lower()
            if at in ('@media', '@supports', '@layer', '@container'):
                inner = prune(bodytext)
                if inner.strip():
                    out.append(prelude + '{' + inner + '}')
            else:
                out.append(prelude + '{' + bodytext + '}')
        elif rule_is_used(prelude):
            out.append(prelude + '{' + bodytext + '}')
        i = k
    return ''.join(out)

# A host theme's own element selectors (h2{color}, .section{background}, …) can
# bleed INTO the pasted markup wherever our CSS relied on inheritance. This
# neutralises that first; every rule after it is more specific and still wins.
DEFENSIVE = (
    ".nurva h1,.nurva h2,.nurva h3,.nurva h4,.nurva h5,.nurva h6,"
    ".nurva p,.nurva div,.nurva span,.nurva a,.nurva ul,.nurva ol,.nurva li,"
    ".nurva blockquote,.nurva figure,.nurva figcaption,.nurva section,.nurva form,"
    ".nurva table,.nurva thead,.nurva tbody,.nurva tr,.nurva th,.nurva td,"
    ".nurva label,.nurva input,.nurva button,.nurva b,.nurva i,.nurva em,.nurva strong,"
    ".nurva svg{"
    "color:inherit;background-color:transparent;background-image:none;"
    "font-family:inherit;font-size:inherit;font-weight:inherit;font-style:inherit;"
    "line-height:inherit;letter-spacing:inherit;text-transform:none;"
    "text-decoration:none;text-align:inherit;"
    "margin:0;padding:0;border:0;border-radius:0;box-shadow:none;list-style:none}"
)

full_css = scope_css(minify_css(read('assets/nurva.css')), PREFIX)
lean_css = DEFENSIVE + prune(full_css)
js = trim_js(read('assets/nurva.js'))

files = {}

files['1-styles.liquid'] = (
    '{%- comment -%}\n'
    '  NURVA — Block 1 of 6: styles. Paste this first, at the top of the page.\n'
    '  Nothing to edit. Every rule is scoped under .nurva, so it cannot change\n'
    '  anything else in your theme.\n'
    '{%- endcomment -%}\n\n'
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=Barlow+Condensed:wght@600;700;800&family=Inter:wght@400;500;600;700'
    '&family=Montserrat:wght@600;700;800&display=swap">\n\n'
    '<style>{% raw %}\n' + lean_css + '\n{% endraw %}</style>\n\n'
    '<noscript><style>.nurva [data-reveal],.nurva .reveal-stagger>*{opacity:1!important;transform:none!important}</style></noscript>\n'
)

files['2-scripts.liquid'] = (
    '{%- comment -%}\n'
    '  NURVA — Block 2 of 6: scripts (scroll animations, counters, FAQ accordion).\n'
    '  Paste this second. Nothing to edit.\n'
    '{%- endcomment -%}\n\n'
    '<script>{% raw %}\n' + js + '\n{% endraw %}</script>\n\n'
    '<script>\n'
    'setTimeout(function(){\n'
    '  document.querySelectorAll(".nurva [data-reveal]:not(.is-in),.nurva .reveal-stagger:not(.is-in)")\n'
    '    .forEach(function(el){ el.classList.add("is-in"); });\n'
    '}, 4000);\n'
    '</script>\n'
)

for name, (label, body_html) in markup.items():
    files[name] = '{%- comment -%} ' + label + ' {%- endcomment -%}\n\n' + body_html

LIMIT = 50000
os.makedirs(os.path.join(ROOT, 'paste'), exist_ok=True)
print('css: full %d -> lean %d chars' % (len(full_css), len(lean_css)))
print(f'{"file":<32}{"chars":>8}   limit {LIMIT}')
print('-' * 56)
ok = True
for name, content in files.items():
    open(os.path.join(ROOT, 'paste', name), 'w', encoding='utf-8').write(content)
    size = len(content)
    if size >= LIMIT: ok = False
    print(f'{name:<32}{size:>8}   {"OK" if size < LIMIT else "TOO BIG"}')
raise SystemExit(0 if ok else 1)
