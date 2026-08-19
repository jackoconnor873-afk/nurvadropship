#!/usr/bin/env python3
"""
Builds paste/nurva-collection.liquid — the shop/collection page as one
paste-ready Shopify section, scoped under .nurva.

Reuses the CSS scoping / minifying / defensive-reset / JS-extraction helpers
(duplicated from build-product.py, since that script runs its build
top-level and exits rather than being import-safe).
"""
import re, os, json

ROOT = os.path.dirname(os.path.abspath(__file__))
def read(p): return open(os.path.join(ROOT, p), encoding='utf-8').read()

PREFIX = '.nurva'

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
        body = css[j + 1:k - 1]
        if prelude.startswith('@'):
            at = re.split(r'[\s(]', prelude, 1)[0].lower()
            if at in ('@media', '@supports', '@layer', '@container'):
                out.append(prelude + '{' + scope_css(body, p) + '}')
            else:
                out.append(prelude + '{' + body + '}')
        else:
            sels = [s for s in prelude.split(',') if s.strip()]
            out.append(','.join(scope_selector(s, p) for s in sels) + '{' + body + '}')
        i = k
    return ''.join(out)

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

def trim_js(js):
    js = re.sub(r'/\*.*?\*/', '', js, flags=re.S)
    keep = []
    for line in js.split('\n'):
        s = line.strip()
        if not s or s.startswith('//'):
            continue
        keep.append(s)
    return '\n'.join(keep)

def extract_fn(js, name):
    """String/regex/comment-aware brace matcher — see build-product.py for why
    a naive char-count breaks on regex literals like /\\{\\{...\\}\\}/."""
    m = re.search(r'^function\s+' + name + r'\s*\(', js, re.M)
    if not m:
        raise SystemExit('could not find function ' + name + ' in nurva.js')
    n = len(js)
    i = js.index('{', m.end() - 1)
    depth, k = 1, i + 1
    while depth and k < n:
        c = js[k]
        if c in ('"', "'", '`'):
            quote = c
            k += 1
            while k < n and js[k] != quote:
                k += 2 if js[k] == '\\' else 1
            k += 1
            continue
        if c == '/' and k + 1 < n and js[k + 1] == '/':
            while k < n and js[k] != '\n':
                k += 1
            continue
        if c == '/' and k + 1 < n and js[k + 1] == '*':
            k += 2
            while k < n and not (js[k] == '*' and k + 1 < n and js[k + 1] == '/'):
                k += 1
            k += 2
            continue
        if c == '/':
            j = k - 1
            while j >= 0 and js[j] in ' \t\n':
                j -= 1
            prev = js[j] if j >= 0 else ''
            if prev in ('(', ',', '=', ':', '[', '!', '&', '|', '?', '{', ';', ''):
                k += 1
                in_class = False
                while k < n:
                    ch = js[k]
                    if ch == '\\':
                        k += 2
                        continue
                    if ch == '[':
                        in_class = True
                    elif ch == ']':
                        in_class = False
                    elif ch == '/' and not in_class:
                        k += 1
                        break
                    k += 1
                while k < n and js[k].isalpha():
                    k += 1
                continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
        k += 1
    return js[m.start():k]

PASTE_FNS = ['ready', 'initReveal', 'initCounters', 'initAccordion']

def paste_js(js):
    fns = '\n'.join(extract_fn(js, n) for n in PASTE_FNS)
    return (
        "(function () {\n'use strict';\n"
        "var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;\n"
        + fns + "\n"
        "function boot(root) {\n"
        "initReveal(root);\n"
        "initCounters(root);\n"
        "initAccordion(root);\n"
        "}\n"
        "ready(function () { boot(document); });\n"
        "document.addEventListener('shopify:section:load', function (e) { boot(e.target); });\n"
        "})();"
    )

# ---------------------------------------------------------------- markup

MARKUP = r'''<div class="nurva">
  <section class="section section--tight">
    <div class="wrap wrap--wide">
      <div class="sec-head sec-head--center stack" data-reveal>
        <span class="eyebrow">Shop</span>
        <h1 class="h1">{{ collection.title | default: 'All Products' }}</h1>
        {%- if collection.description != blank -%}
          <div class="lede rte" style="margin-inline:auto">{{ collection.description }}</div>
        {%- endif -%}
      </div>
    </div>
  </section>

  <div class="marquee" style="--marquee-speed:30s">
    <div class="marquee__track" data-marquee>
      <div class="marquee__group">
        <span class="marquee__item">BUY 1 GET 1 FREE<span class="marquee__dot"></span></span>
        <span class="marquee__item">SHIPS VIA AN POST<span class="marquee__dot"></span></span>
        <span class="marquee__item">30-NIGHT GUARANTEE<span class="marquee__dot"></span></span>
        <span class="marquee__item">DRUG FREE<span class="marquee__dot"></span></span>
      </div>
    </div>
  </div>

  <section class="section">
    <div class="wrap wrap--wide">
      {%- paginate collection.products by 24 -%}
        {%- if collection.products.size > 0 -%}
          <div class="grid grid--4 reveal-stagger">
            {%- for product in collection.products -%}
              {%- assign p_on_sale = false -%}
              {%- if product.compare_at_price > product.price -%}
                {%- assign p_on_sale = true -%}
              {%- endif -%}
              {%- assign p_has_alt_media = false -%}
              {%- if product.media.size > 1 -%}
                {%- assign p_has_alt_media = true -%}
              {%- endif -%}
              <a class="card" href="{{ product.url }}">
                <div class="card__media {% if p_has_alt_media %}card__media--alt{% endif %}">
                  {%- if product.featured_media -%}
                    {{ product.featured_media | image_url: width: 900 | image_tag:
                        loading: 'lazy',
                        sizes: '(min-width: 990px) 25vw, (min-width: 750px) 45vw, 90vw',
                        widths: '300,450,600,900',
                        alt: product.featured_media.alt | default: product.title }}
                    {%- if product.media[1] -%}
                      {{ product.media[1] | image_url: width: 900 | image_tag:
                          loading: 'lazy',
                          class: 'card__img-2',
                          sizes: '(min-width: 990px) 25vw, (min-width: 750px) 45vw, 90vw',
                          widths: '300,450,600,900',
                          alt: '' }}
                    {%- endif -%}
                  {%- else -%}
                    {{ 'product-1' | placeholder_svg_tag: 'placeholder-svg' }}
                  {%- endif -%}
                  {%- if p_on_sale -%}
                    <span class="card__tag">Buy 1 Get 1 Free</span>
                  {%- endif -%}
                </div>
                <div>
                  <div class="card__title">{{ product.title }}</div>
                </div>
                <div class="card__price">
                  <span>{{ product.price | money }}</span>
                  {%- if p_on_sale -%}
                    <s>{{ product.compare_at_price | money }}</s>
                  {%- endif -%}
                </div>
              </a>
            {%- endfor -%}
          </div>

          {%- if paginate.pages > 1 -%}
            <nav class="pagination" aria-label="Pagination">
              {%- for part in paginate.parts -%}
                {%- if part.is_link -%}
                  <a href="{{ part.url }}">{{ part.title }}</a>
                {%- else -%}
                  <span {% if part.title == paginate.current_page %}aria-current="page"{% endif %}>{{ part.title }}</span>
                {%- endif -%}
              {%- endfor -%}
            </nav>
          {%- endif -%}
        {%- else -%}
          <div class="empty-state stack">
            <h2 class="h3">Nothing here yet</h2>
            <p class="muted">This collection is empty. Check back soon.</p>
            <a class="btn" href="{{ routes.all_products_collection_url }}">Browse everything</a>
          </div>
        {%- endif -%}
      {%- endpaginate -%}
    </div>
  </section>

  <section class="section section--raised section--tight">
    <div class="wrap">
      <div class="trust-row" style="border-top:0;padding-top:0" data-reveal>
        <div><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7h11v9H2z"/><path d="M13 10h4l3 3v3h-7"/><circle cx="6.5" cy="18" r="1.6"/><circle cx="17" cy="18" r="1.6"/></svg><span>Delivered via An Post, 5&ndash;7 business days</span></div>
        <div><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 3v5.5c0 4.3-2.9 8-7 9.5-4.1-1.5-7-5.2-7-9.5V6z"/><polyline points="9.2 12 11.4 14.1 15 10.4"/></svg><span>30-night guarantee</span></div>
        <div><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 4C10 4 4 9 4 16c0 1.5.4 2.8 1 4"/><path d="M20 4c0 9-5 13-11 13-1.6 0-3-.4-4-1"/></svg><span>Drug free</span></div>
      </div>
    </div>
  </section>
</div>'''

# ---------------------------------------------------------------- CSS pruning

used = set(re.findall(r'class="([^"]*)"', MARKUP))
used = {c for group in used for c in group.split()}
used |= {'nurva', 'is-in', 'is-stuck', 'is-visible', 'no-js', 'placeholder-svg'}

def rule_is_used(selectors):
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

full_css = scope_css(minify_css(read('assets/nurva.css')), PREFIX)
lean_css = DEFENSIVE + prune(full_css)
js = paste_js(trim_js(read('assets/nurva.js')))

# ---------------------------------------------------------------- assemble

section_file = (
    "{%- comment -%}\n"
    "  NURVA PERFORMANCE — collection (shop) page section.\n"
    "\n"
    "  Online Store -> Themes -> Edit code -> Sections -> Add a new section,\n"
    "  name it  nurva-collection  (Shopify adds the .liquid), paste this in, Save.\n"
    "  Then open your COLLECTION template (Edit code -> Templates -> collection.json,\n"
    "  or Customize -> browse to any collection -> Add section) and add Nurva collection.\n"
    "\n"
    "  Uses the page's own `collection` object automatically — nothing to pick.\n"
    "  Card badges show 'Buy 1 Get 1 Free' on any product with a compare-at price\n"
    "  set above its price — set that on a product in Shopify to flag it.\n"
    "  Styles are scoped under .nurva and cannot affect the rest of your theme.\n"
    "{%- endcomment -%}\n\n"
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=Barlow+Condensed:wght@600;700;800&family=Inter:wght@400;500;600;700'
    '&family=Montserrat:wght@600;700;800&display=swap">\n\n'
    "<style>{% raw %}\n" + lean_css + "\n{% endraw %}</style>\n\n"
    '<noscript><style>.nurva [data-reveal],.nurva .reveal-stagger>*{opacity:1!important;transform:none!important}</style></noscript>\n\n'
    "<script>{% raw %}\n" + js + "\n{% endraw %}</script>\n\n"
    + MARKUP + "\n\n"
    + "{% schema %}\n"
    + json.dumps({"name": "Nurva collection", "tag": "section", "settings": []}, indent=2)
    + "\n{% endschema %}\n"
)

out_path = os.path.join(ROOT, 'paste', 'nurva-collection.liquid')
os.makedirs(os.path.join(ROOT, 'paste'), exist_ok=True)
open(out_path, 'w', encoding='utf-8').write(section_file)
print('css: full %d -> lean %d chars' % (len(full_css), len(lean_css)))
print('paste/nurva-collection.liquid: %d chars' % len(section_file))
