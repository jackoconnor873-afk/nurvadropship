#!/usr/bin/env python3
"""
Builds paste/nurva-about.liquid — an About page section in the same clean,
scoped style as build-home-clean.py (hero, split story, badges, a real
purchase block, FAQ). Meant to be pasted in as a new Shopify Page section
via a page.about-nurva.json template (or dropped into any page through the
theme editor), so the store has a story page that looks and behaves like
the homepage instead of a bare Shopify "page" template.

Self-contained like build-product.py / build-collection.py / build-cart.py /
build-home-clean.py — copies the same helper functions so it has no import
dependency on those files.
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

PASTE_FNS = ['ready', 'initReveal', 'initCounters', 'initAccordion', 'initQty']

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
        "initQty(root);\n"
        "}\n"
        "ready(function () { boot(document); });\n"
        "document.addEventListener('shopify:section:load', function (e) { boot(e.target); });\n"
        "})();"
    )

# ---------------------------------------------------------------- markup

ABOUT_HERO = r'''<div class="nurva">
  <section class="hero" style="min-height:62vh">
    <div class="hero__veil"></div>
    <div class="hero__pulse" aria-hidden="true">
      <span class="hero__ring"></span><span class="hero__ring"></span><span class="hero__ring"></span><span class="hero__ring"></span>
    </div>

    <div class="wrap wrap--wide hero__inner">
      <div class="hero__content">
        <div class="hero__badge">
          <b>PRO</b>
          <span>Our story</span>
        </div>

        <h1 class="display hero__title">
          <span class="hero__line"><span>Built by people</span></span>
          <span class="hero__line"><span>who couldn't</span></span>
          <span class="hero__line"><span>breathe right.</span></span>
        </h1>

        <p class="lede hero__copy" data-reveal data-reveal-delay="450">
          Nurva started with a simple problem: training, sleeping and racing while breathing through
          a half-closed nose. We set out to build one strip that actually holds &mdash; through sweat,
          through the night, through everything.
        </p>

        <div class="hero__cta" data-reveal data-reveal-delay="600">
          <a class="btn btn--lg" href="#nurva-buy">
            Shop Nurva
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="12" x2="19" y2="12"/><polyline points="13 6 19 12 13 18"/></svg>
          </a>
          <a class="btn btn--lg btn--ghost" href="#nurva-mission">Our mission</a>
        </div>
      </div>
    </div>

    <div class="hero__scroll" aria-hidden="true"><i></i><span>Scroll</span></div>
  </section>
</div>'''

MISSION_SPLIT = r'''<div class="nurva">
  <section class="section" id="nurva-mission">
    <div class="wrap">
      <div class="split">
        <div class="split__media" data-reveal="left">
          <div class="split__placeholder">
            <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v9"/><path d="M12 8.5c-1.6-.6-2.8 0-3.3 1.3L6.2 16c-.7 1.9.4 3.8 2.3 4.1 1.5.2 2.6-.7 2.8-2.2l.7-4.6"/><path d="M12 8.5c1.6-.6 2.8 0 3.3 1.3L17.8 16c.7 1.9-.4 3.8-2.3 4.1-1.5.2-2.6-.7-2.8-2.2l-.7-4.6"/></svg>
            <span>Add your brand image</span>
          </div>
        </div>

        <div class="split__body stack" data-reveal="right">
          <span class="eyebrow">Why we started</span>
          <h2 class="h2">Breathing shouldn't be the bottleneck</h2>
          <p class="lede">
            Most nasal strips are an afterthought &mdash; flat, single-band, and gone by the second
            quarter or the third hour of sleep. We rebuilt the strip from the adhesive up: dual spring
            bands, a contour cut for the nasal valve, and a hold that survives sweat, movement and side
            sleeping.
          </p>

          <ul class="ticks stack">
            <li class="tick">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><polyline points="16 9.5 10.8 15 8 12.4"/></svg>
              <div><b>Designed for athletes first</b><p>Tested through training blocks, race days and recovery nights, not just a lab bench.</p></div>
            </li>
            <li class="tick">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><polyline points="16 9.5 10.8 15 8 12.4"/></svg>
              <div><b>No drugs, no sprays</b><p>Just mechanical lift on the nasal valve &mdash; nothing to absorb, nothing habit forming.</p></div>
            </li>
            <li class="tick">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><polyline points="16 9.5 10.8 15 8 12.4"/></svg>
              <div><b>Shipped from Ireland</b><p>Every order goes out via An Post and typically arrives in 5&ndash;7 business days.</p></div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </section>

  <section class="section section--raised">
    <div class="wrap">
      <div class="sec-head sec-head--center stack" data-reveal>
        <span class="eyebrow">What matters to us</span>
        <h2 class="h2">Perform | Breathe | Recover</h2>
      </div>

      <div class="badges reveal-stagger">
        <div class="badge-ring">
          <div class="badge-ring__disc">
            <span class="badge-ring__value"><span data-count="10"></span></span>
          </div>
          <span class="badge-ring__label">Hours of relief</span>
          <span class="badge-ring__note">One strip, from warm-up to lights out.</span>
        </div>
        <div class="badge-ring">
          <div class="badge-ring__disc">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3s6 6.4 6 10.4A6 6 0 0 1 6 13.4C6 9.4 12 3 12 3z"/><path d="M9.4 14.2a2.7 2.7 0 0 0 2.6 2.6"/></svg>
          </div>
          <span class="badge-ring__label">Sweat proof</span>
          <span class="badge-ring__note">Medical-grade adhesive that won't peel mid-set.</span>
        </div>
        <div class="badge-ring">
          <div class="badge-ring__disc">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><polygon points="13.4 2 4.5 13.6 11 13.6 10.2 22 19.5 10.2 12.8 10.2"/></svg>
          </div>
          <span class="badge-ring__label">Performance boost</span>
          <span class="badge-ring__note">More airflow means more oxygen where it counts.</span>
        </div>
        <div class="badge-ring">
          <div class="badge-ring__disc">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M20.5 14.2A8.6 8.6 0 0 1 9.8 3.5a8.6 8.6 0 1 0 10.7 10.7z"/></svg>
          </div>
          <span class="badge-ring__label">Snoring relief</span>
          <span class="badge-ring__note">Quieter nights, deeper recovery, sharper mornings.</span>
        </div>
      </div>
    </div>
  </section>
</div>'''

# Same real purchase block pattern as the homepage — a product picker, since
# an About page has no page-level product of its own.
BUY_BLOCK = r'''<div class="nurva">
  <section class="section section--raised" id="nurva-buy">
    <div class="wrap wrap--narrow">
      <div class="sec-head sec-head--center stack" data-reveal>
        <span class="eyebrow">Limited-time offer</span>
        <h2 class="h2">Get Nurva Pro</h2>
      </div>

      {%- if bp -%}
        <div class="product" style="grid-template-columns:minmax(0,0.9fr) minmax(0,1.1fr)" data-reveal="scale">
          <div class="product__gallery">
            <div class="product__main-img">
              {%- if bp.featured_media -%}
                {{ bp.featured_media | image_url: width: 1000 | image_tag:
                    loading: 'lazy',
                    sizes: '(min-width: 900px) 40vw, 100vw',
                    widths: '400,600,800,1000',
                    alt: bp.featured_media.alt | default: bp.title }}
              {%- else -%}
                {{ 'product-1' | placeholder_svg_tag: 'placeholder-svg' }}
              {%- endif -%}
            </div>
          </div>

          <div class="product__info stack">
            <div style="display:inline-flex;align-items:center;gap:8px;padding:8px 16px;border-radius:999px;background:var(--teal);color:#fff;font-family:var(--font-brand);font-weight:700;font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;width:fit-content">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 12V8H6a2 2 0 0 1-2-2c0-1.1.9-2 2-2h12v4"/><path d="M4 6v12c0 1.1.9 2 2 2h14v-4"/><path d="M18 12a2 2 0 0 0 0 4h4v-4Z"/></svg>
              <span>Buy 1, Get 1 Free</span>
            </div>

            <h3 class="product__title" style="font-size:clamp(1.8rem,3vw,2.6rem)">{{ bp.title }}</h3>

            <div class="product__price-row">
              <span class="product__price">{{ bpv.price | money }}</span>
              <span class="muted" style="font-size:.84rem">Ships in 5&ndash;7 business days</span>
            </div>

            <div class="rte muted">{{ bp.description | strip_html | truncate: 160 }}</div>

            {%- form 'product', bp, data-product-form: 'true', id: 'NurvaAboutBuyForm' -%}
              <input type="hidden" name="id" value="{{ bpv.id }}">

              <div class="buy-row">
                <div class="qty" data-qty>
                  <button type="button" data-qty-step="-1" aria-label="Decrease quantity">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="5" y1="12" x2="19" y2="12"/></svg>
                  </button>
                  <input type="number" name="quantity" value="2" min="1" aria-label="Quantity">
                  <button type="button" data-qty-step="1" aria-label="Increase quantity">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                  </button>
                </div>

                <button
                  type="submit"
                  class="btn btn--lg"
                  data-add-button
                  data-add-text="Add to cart"
                  data-soldout-text="Sold out"
                  {% unless bpv.available %}aria-disabled="true"{% endunless %}>
                  {%- if bpv.available -%}Add to cart{%- else -%}Sold out{%- endif -%}
                </button>
              </div>

              <p class="muted" style="font-size:.82rem">Add 2 to your cart &mdash; the discount for your free strip is applied automatically at checkout.</p>
              <p class="form-error" data-form-error hidden></p>
            {%- endform -%}

            <div class="trust-row">
              <div><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7h11v9H2z"/><path d="M13 10h4l3 3v3h-7"/><circle cx="6.5" cy="18" r="1.6"/><circle cx="17" cy="18" r="1.6"/></svg><span>Delivered via An Post</span></div>
              <div><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 3v5.5c0 4.3-2.9 8-7 9.5-4.1-1.5-7-5.2-7-9.5V6z"/><polyline points="9.2 12 11.4 14.1 15 10.4"/></svg><span>Buy 1, get 1 free</span></div>
              <div><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 4C10 4 4 9 4 16c0 1.5.4 2.8 1 4"/><path d="M20 4c0 9-5 13-11 13-1.6 0-3-.4-4-1"/></svg><span>Drug free</span></div>
            </div>
          </div>
        </div>
      {%- else -%}
        <div class="empty-state stack" data-reveal>
          <p class="muted">Connect your product below in the theme editor to activate this section.</p>
          <a class="btn" href="{{ routes.all_products_collection_url }}">Shop now</a>
        </div>
      {%- endif -%}
    </div>
  </section>
</div>'''

ABOUT_FAQ = r'''<div class="nurva">
  <section class="section">
    <div class="wrap wrap--narrow">
      <div class="sec-head sec-head--center stack" data-reveal>
        <span class="eyebrow">Answers</span>
        <h2 class="h2">Before you buy</h2>
      </div>

      <div class="faq" data-faq data-faq-single="true" data-reveal>
        <div class="faq__item" data-open="false">
          <h3><button class="faq__q" type="button" aria-expanded="false"><span>Who is Nurva for?</span><span class="faq__sign" aria-hidden="true"></span></button></h3>
          <div class="faq__a"><div><p>Anyone who wants to breathe easier &mdash; runners, lifters, snorers, and anyone training or sleeping through a blocked nose.</p></div></div>
        </div>

        <div class="faq__item" data-open="false">
          <h3><button class="faq__q" type="button" aria-expanded="false"><span>Where do you ship from?</span><span class="faq__sign" aria-hidden="true"></span></button></h3>
          <div class="faq__a"><div><p>Every order ships via An Post and typically arrives in 5&ndash;7 business days.</p></div></div>
        </div>

        <div class="faq__item" data-open="false">
          <h3><button class="faq__q" type="button" aria-expanded="false"><span>How does Buy 1, Get 1 Free work?</span><span class="faq__sign" aria-hidden="true"></span></button></h3>
          <div class="faq__a"><div><p>Add 2 to your cart and the discount for your free strip is applied automatically at checkout &mdash; no code needed.</p></div></div>
        </div>
      </div>
    </div>
  </section>
</div>'''

ALL_MARKUP = ABOUT_HERO + MISSION_SPLIT + BUY_BLOCK + ABOUT_FAQ

# ---------------------------------------------------------------- CSS pruning

used = set(re.findall(r'class="([^"]*)"', ALL_MARKUP))
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

section_schema = json.dumps({
    "name": "Nurva about",
    "tag": "section",
    "settings": [
        {"type": "header", "content": "Your product"},
        {"type": "product", "id": "product", "label": "Product",
         "info": "Pick your nasal strips product for the buy block on this page."}
    ],
    "presets": [{"name": "Nurva about"}]
}, indent=2)

section_file = (
    "{%- comment -%}\n"
    "  NURVA PERFORMANCE — About page section.\n"
    "\n"
    "  Online Store -> Themes -> Edit code -> Sections -> Add a new section,\n"
    "  name it  nurva-about  (Shopify adds the .liquid), paste this in, Save.\n"
    "\n"
    "  Then either:\n"
    "  A) Online Store -> Pages -> Add page, name it About, set its theme\n"
    "     template to a new one (e.g. page.about), and add this section to it\n"
    "     in Customize -> pick the About page -> Add section -> Nurva about.\n"
    "  B) Or just add it to any existing page/template the same way.\n"
    "  Pick your product in the section settings once added.\n"
    "\n"
    "  Same look and behaviour as the homepage: hero, story split, values,\n"
    "  a real Buy 1 Get 1 Free purchase block, and FAQ. Styles are scoped\n"
    "  under .nurva and cannot affect the rest of your theme.\n"
    "{%- endcomment -%}\n\n"
    "{%- assign bp = section.settings.product -%}\n"
    "{%- assign bpv = bp.selected_or_first_available_variant -%}\n\n"
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=Barlow+Condensed:wght@600;700;800&family=Inter:wght@400;500;600;700'
    '&family=Montserrat:wght@600;700;800&display=swap">\n\n'
    "<style>{% raw %}\n" + lean_css + "\n{% endraw %}</style>\n\n"
    '<noscript><style>.nurva [data-reveal],.nurva .reveal-stagger>*{opacity:1!important;transform:none!important}</style></noscript>\n\n'
    "<script>{% raw %}\n" + js + "\n{% endraw %}</script>\n\n"
    + ALL_MARKUP + "\n\n"
    + "{% schema %}\n" + section_schema + "\n{% endschema %}\n"
)

out_path = os.path.join(ROOT, 'paste', 'nurva-about.liquid')
open(out_path, 'w', encoding='utf-8').write(section_file)
print('css: full %d -> lean %d chars' % (len(full_css), len(lean_css)))
print('paste/nurva-about.liquid: %d chars' % len(section_file))
