#!/usr/bin/env python3
"""
Builds paste/nurva-cart.liquid — the cart page as one paste-ready Shopify
section, scoped under .nurva. See build-collection.py for notes on the
duplicated helpers (build-product.py isn't import-safe).
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

PASTE_FNS = ['ready', 'initReveal', 'initQty']

def paste_js(js):
    fns = '\n'.join(extract_fn(js, n) for n in PASTE_FNS)
    return (
        "(function () {\n'use strict';\n"
        "var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;\n"
        + fns + "\n"
        "function boot(root) {\n"
        "initReveal(root);\n"
        "initQty(root);\n"
        "}\n"
        "ready(function () { boot(document); });\n"
        "document.addEventListener('shopify:section:load', function (e) { boot(e.target); });\n"
        "})();"
    )

# ---------------------------------------------------------------- markup

MARKUP = r'''<div class="nurva">
  <section class="section">
    <div class="wrap">
      <div class="sec-head stack" data-reveal>
        <span class="eyebrow">Your bag</span>
        <h1 class="h1">Cart</h1>
      </div>

      {%- if cart.item_count > 0 -%}
        <form action="{{ routes.cart_url }}" method="post" novalidate>
          <div class="cart-layout">
            <div>
              {%- for item in cart.items -%}
                <div class="cart-line">
                  <a href="{{ item.url }}">
                    {%- if item.image -%}
                      {{ item.image | image_url: width: 200 | image_tag: loading: 'lazy', alt: item.title, width: 92, height: 92 }}
                    {%- endif -%}
                  </a>

                  <div>
                    <a class="card__title" href="{{ item.url }}">{{ item.product.title }}</a>
                    {%- unless item.product.has_only_default_variant -%}
                      <div class="quote__meta">{{ item.variant.title }}</div>
                    {%- endunless -%}
                    <div class="muted" style="font-size:.85rem;margin-top:6px">{{ item.original_price | money }} each</div>

                    <div style="display:flex;gap:14px;align-items:center;margin-top:12px">
                      <div class="qty" data-qty>
                        <button type="button" data-qty-step="-1" aria-label="Decrease">
                          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="5" y1="12" x2="19" y2="12"/></svg>
                        </button>
                        <input type="number" name="updates[]" value="{{ item.quantity }}" min="0" aria-label="Quantity for {{ item.title | escape }}">
                        <button type="button" data-qty-step="1" aria-label="Increase">
                          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                        </button>
                      </div>
                      <a class="quote__meta" href="{{ item.url_to_remove }}">Remove</a>
                    </div>
                  </div>

                  <div class="cart-line__total" style="font-family:var(--font-brand);font-weight:700">
                    {{ item.final_line_price | money }}
                  </div>
                </div>
              {%- endfor -%}

              <div style="margin-top:22px">
                <button type="submit" name="update" class="btn btn--ghost btn--sm">Update cart</button>
              </div>

              <div style="margin-top:26px;padding:16px 20px;border:1px solid var(--line);border-radius:var(--radius-lg);display:flex;gap:12px;align-items:center">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex:none;color:var(--teal-bright)"><path d="M20 12V8H6a2 2 0 0 1-2-2c0-1.1.9-2 2-2h12v4"/><path d="M4 6v12c0 1.1.9 2 2 2h14v-4"/><path d="M18 12a2 2 0 0 0 0 4h4v-4Z"/></svg>
                <span class="muted" style="font-size:.9rem">Buy 1, Get 1 Free &mdash; add a second strip and the discount applies automatically at checkout.</span>
              </div>
            </div>

            <aside class="cart-summary stack">
              <h2 class="h3">Summary</h2>
              <div class="cart-summary__row">
                <span class="muted">Subtotal</span>
                <strong>{{ cart.total_price | money }}</strong>
              </div>
              {%- if cart.total_discount > 0 -%}
                <div class="cart-summary__row">
                  <span class="muted">Discount</span>
                  <strong class="tint">-{{ cart.total_discount | money }}</strong>
                </div>
              {%- endif -%}
              <p class="muted" style="font-size:.82rem">Taxes and shipping calculated at checkout.</p>

              <label class="opt__label" for="NurvaCartNote">Order note</label>
              <textarea id="NurvaCartNote" name="note" rows="3"
                style="width:100%;padding:12px 14px;border-radius:10px;border:1px solid var(--line-strong);background:rgba(0,0,0,.35);color:var(--text)">{{ cart.note }}</textarea>

              <button type="submit" name="checkout" class="btn btn--block btn--lg">Checkout</button>

              <div class="trust-row" style="grid-template-columns:1fr">
                <div><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="10.5" width="14" height="9.5" rx="2"/><path d="M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5"/></svg><span>Secure checkout</span></div>
                <div><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7h11v9H2z"/><path d="M13 10h4l3 3v3h-7"/><circle cx="6.5" cy="18" r="1.6"/><circle cx="17" cy="18" r="1.6"/></svg><span>Delivered via An Post, 5&ndash;7 business days</span></div>
                <div><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 12a8 8 0 1 1-2.4-5.7"/><polyline points="20 4 20 8.2 15.8 8.2"/></svg><span>30-night guarantee</span></div>
              </div>
            </aside>
          </div>
        </form>
      {%- else -%}
        <div class="empty-state stack">
          <h2 class="h2">Your cart is empty</h2>
          <p class="lede" style="margin-inline:auto">Nothing in the bag yet. Let's fix your breathing.</p>
          <div><a class="btn btn--lg" href="{{ routes.all_products_collection_url }}">Shop Nurva</a></div>
        </div>
      {%- endif -%}
    </div>
  </section>
</div>'''

# ---------------------------------------------------------------- CSS pruning

used = set(re.findall(r'class="([^"]*)"', MARKUP))
used = {c for group in used for c in group.split()}
used |= {'nurva', 'is-in', 'is-stuck', 'is-visible', 'no-js'}

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

# .cart-layout is defined inline in the full theme's homepage sections/main-cart.liquid
# (added post-hoc, see git history), not in assets/nurva.css. Ensure it's present here too.
CART_LAYOUT_CSS = (
    ".nurva .cart-layout{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(0,0.85fr);"
    "gap:clamp(26px,4vw,48px);align-items:start}"
    "@media (max-width:899px){.nurva .cart-layout{grid-template-columns:minmax(0,1fr)}}"
)

lean_css = DEFENSIVE + prune(full_css) + CART_LAYOUT_CSS
js = paste_js(trim_js(read('assets/nurva.js')))

# ---------------------------------------------------------------- assemble

section_file = (
    "{%- comment -%}\n"
    "  NURVA PERFORMANCE — cart page section.\n"
    "\n"
    "  Online Store -> Themes -> Edit code -> Sections -> Add a new section,\n"
    "  name it  nurva-cart  (Shopify adds the .liquid), paste this in, Save.\n"
    "  Then open your CART template (Edit code -> Templates -> cart.json,\n"
    "  or Customize -> Cart page -> Add section) and add Nurva cart.\n"
    "\n"
    "  Uses the page's own `cart` object automatically — nothing to pick.\n"
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
    + json.dumps({"name": "Nurva cart", "tag": "section", "settings": []}, indent=2)
    + "\n{% endschema %}\n"
)

out_path = os.path.join(ROOT, 'paste', 'nurva-cart.liquid')
os.makedirs(os.path.join(ROOT, 'paste'), exist_ok=True)
open(out_path, 'w', encoding='utf-8').write(section_file)
print('css: full %d -> lean %d chars' % (len(full_css), len(lean_css)))
print('paste/nurva-cart.liquid: %d chars' % len(section_file))
