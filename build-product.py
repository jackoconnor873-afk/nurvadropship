#!/usr/bin/env python3
"""
Builds paste/nurva-product.liquid — the product page as one paste-ready
Shopify section, scoped under .nurva, matching templates/product.json.

Reuses the CSS scoping / minifying / defensive-reset helpers from
build-paste.py (duplicated here rather than imported, since build-paste.py
runs its build top-level and exits).
"""
import re, os, json

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

def extract_fn(js, name):
    """Brace-match a function body, aware of strings/template literals/regex
    literals/comments — a naive char-count misfires on code like
    /\\{\\{\\s*amount[^}]*\\}\\}/ (three '}' chars, two '{' chars)."""
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

PASTE_FNS = [
    'ready', 'initReveal', 'initCounters', 'initAccordion',
    'initQty', 'initGallery', 'initVariants', 'initAddToCart', 'initBuyBar',
]

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
        "initGallery(root);\n"
        "initVariants(root);\n"
        "initAddToCart(root);\n"
        "}\n"
        "ready(function () { boot(document); initBuyBar(); });\n"
        "document.addEventListener('shopify:section:load', function (e) { boot(e.target); initBuyBar(); });\n"
        "})();"
    )

# ---------------------------------------------------------------- markup

# Main product block: gallery + info stack, matching main-product.liquid with
# the exact default block settings from templates/product.json.
MAIN_PRODUCT = r'''<div class="nurva">
  <section class="section">
    <div class="wrap wrap--wide">
      <div class="product">

        <div class="product__gallery" data-gallery data-reveal="left">
          <div class="product__main-img" data-gallery-main>
            {%- if product.featured_media -%}
              {{ product.featured_media | image_url: width: 1400 | image_tag:
                  loading: 'eager',
                  fetchpriority: 'high',
                  sizes: '(min-width: 900px) 50vw, 100vw',
                  widths: '500,700,900,1200,1400',
                  alt: product.featured_media.alt | default: product.title }}
            {%- else -%}
              {{ 'product-1' | placeholder_svg_tag: 'placeholder-svg' }}
            {%- endif -%}
          </div>

          {%- if product.media.size > 1 -%}
            <div class="product__thumbs">
              {%- for media in product.media limit: 10 -%}
                <button
                  type="button"
                  class="product__thumb"
                  data-gallery-thumb
                  data-full="{{ media | image_url: width: 1400 }}"
                  aria-current="{% if forloop.first %}true{% else %}false{% endif %}"
                  aria-label="View image {{ forloop.index }}">
                  {{ media | image_url: width: 240 | image_tag: loading: 'lazy', alt: media.alt | default: product.title }}
                </button>
              {%- endfor -%}
            </div>
          {%- endif -%}
        </div>

        <div class="product__info stack" data-reveal="right">
          <span class="eyebrow">Perform | Breathe | Recover</span>

          <h1 class="product__title">{{ product.title }}</h1>

          <div class="product__rating">
            <span class="stars">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.6l2.9 5.9 6.5.9-4.7 4.6 1.1 6.5-5.8-3-5.8 3 1.1-6.5L2.6 9.4l6.5-.9z"/></svg><svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.6l2.9 5.9 6.5.9-4.7 4.6 1.1 6.5-5.8-3-5.8 3 1.1-6.5L2.6 9.4l6.5-.9z"/></svg><svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.6l2.9 5.9 6.5.9-4.7 4.6 1.1 6.5-5.8-3-5.8 3 1.1-6.5L2.6 9.4l6.5-.9z"/></svg><svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.6l2.9 5.9 6.5.9-4.7 4.6 1.1 6.5-5.8-3-5.8 3 1.1-6.5L2.6 9.4l6.5-.9z"/></svg><svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.6l2.9 5.9 6.5.9-4.7 4.6 1.1 6.5-5.8-3-5.8 3 1.1-6.5L2.6 9.4l6.5-.9z"/></svg>
            </span>
            <span>4.8 from 2,400+ reviews</span>
          </div>

          <div class="product__price-row">
            <span class="product__price" data-variant-price>{{ current_variant.price | money }}</span>
            <span class="price__compare" data-variant-compare {% unless on_sale %}hidden{% endunless %}>
              {%- if on_sale -%}
                {{ current_variant.compare_at_price | money }}
              {%- endif -%}
            </span>
            <span class="muted" style="font-size:.84rem">Free shipping over $35</span>
          </div>

          <div class="rte muted">{{ product.description }}</div>

          <ul class="ticks stack">
            <li class="tick">
              <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><polyline points="16 9.5 10.8 15 8 12.4"/></svg>
              <div><b>Up to 10 hours of hold</b></div>
            </li>
            <li class="tick">
              <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><polyline points="16 9.5 10.8 15 8 12.4"/></svg>
              <div><b>Sweat-proof medical-grade adhesive</b></div>
            </li>
            <li class="tick">
              <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><polyline points="16 9.5 10.8 15 8 12.4"/></svg>
              <div><b>Drug free, latex free, hypoallergenic</b></div>
            </li>
            <li class="tick">
              <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><polyline points="16 9.5 10.8 15 8 12.4"/></svg>
              <div><b>Works for training and for sleep</b></div>
            </li>
          </ul>

          <div data-buybar-anchor>
            {%- form 'product', product, data-product-form: 'true', id: 'NurvaProductForm' -%}
              <input type="hidden" name="id" value="{{ current_variant.id }}" data-variant-id>

              {%- unless product.has_only_default_variant -%}
                <div data-variant-picker class="stack" style="--stack:18px;margin-bottom:22px">
                  {%- for option in product.options_with_values -%}
                    <div class="opt stack" data-option-group>
                      <span class="opt__label">{{ option.name }}</span>
                      <div class="opt__choices">
                        {%- for value in option.values -%}
                          <label class="opt__choice">
                            <input
                              type="radio"
                              name="option-nurva-{{ forloop.parentloop.index0 }}"
                              value="{{ value | escape }}"
                              {% if option.selected_value == value %}checked{% endif %}>
                            <span>{{ value }}</span>
                          </label>
                        {%- endfor -%}
                      </div>
                    </div>
                  {%- endfor -%}

                  <script type="application/json" data-variant-json>
                    {{ product.variants | json }}
                  </script>
                </div>
              {%- endunless -%}

              <div class="buy-row">
                <div class="qty" data-qty>
                  <button type="button" data-qty-step="-1" aria-label="Decrease quantity">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="5" y1="12" x2="19" y2="12"/></svg>
                  </button>
                  <input type="number" name="quantity" value="1" min="1" aria-label="Quantity">
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
                  data-unavailable-text="Unavailable"
                  {% unless current_variant.available %}aria-disabled="true"{% endunless %}>
                  {%- if current_variant.available -%}Add to cart{%- else -%}Sold out{%- endif -%}
                </button>
              </div>

              <p class="form-error" data-form-error hidden></p>

              <div style="margin-top:12px">{{ form | payment_button }}</div>
            {%- endform -%}
          </div>

          <div class="trust-row">
            <div><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7h11v9H2z"/><path d="M13 10h4l3 3v3h-7"/><circle cx="6.5" cy="18" r="1.6"/><circle cx="17" cy="18" r="1.6"/></svg><span>Ships in 1 business day</span></div>
            <div><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 3v5.5c0 4.3-2.9 8-7 9.5-4.1-1.5-7-5.2-7-9.5V6z"/><polyline points="9.2 12 11.4 14.1 15 10.4"/></svg><span>30-night guarantee</span></div>
            <div><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 4C10 4 4 9 4 16c0 1.5.4 2.8 1 4"/><path d="M20 4c0 9-5 13-11 13-1.6 0-3-.4-4-1"/></svg><span>Drug free</span></div>
          </div>

          <div class="faq" data-faq>
            <div class="faq__item" data-open="false">
              <h3><button class="faq__q" type="button" aria-expanded="false"><span>How to apply</span><span class="faq__sign" aria-hidden="true"></span></button></h3>
              <div class="faq__a"><div><p>Clean and dry the bridge of your nose. Peel the liner, centre the strip just above the flare of your nostrils, press the ends for five seconds. Remove under warm water.</p></div></div>
            </div>
            <div class="faq__item" data-open="false">
              <h3><button class="faq__q" type="button" aria-expanded="false"><span>Shipping &amp; returns</span><span class="faq__sign" aria-hidden="true"></span></button></h3>
              <div class="faq__a"><div><p>Orders placed before 2pm ship the same business day with tracking. Free shipping over $35. If Nurva doesn't work for you, tell us within 30 nights for a full refund.</p></div></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</div>

<div class="buybar" data-buybar>
  <div class="buybar__info">
    <span class="buybar__name">{{ product.title | truncate: 34 }}</span>
    <span class="buybar__price">{{ current_variant.price | money }}</span>
  </div>
  <button class="btn" type="submit" form="NurvaProductForm">Add to cart</button>
</div>

<script type="application/ld+json">
  {{ product | structured_data }}
</script>'''

# Supplementary sections, matching templates/product.json's badges/how/reviews/faq
# blocks exactly (text, counts, order).

BADGES = r'''<div class="nurva">
  <section class="section section--raised">
    <div class="wrap">
      <div class="sec-head sec-head--center stack" data-reveal>
        <span class="eyebrow">What you get</span>
        <h2 class="h2">Four reasons it stays in your gym bag</h2>
      </div>

      <div class="badges reveal-stagger">
        <div class="badge-ring">
          <div class="badge-ring__disc">
            <span class="badge-ring__value"><span data-count="10"></span></span>
          </div>
          <span class="badge-ring__label">Hours of relief</span>
          <span class="badge-ring__note">One strip holds from warm-up to lights out.</span>
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

HOW = r'''<div class="nurva">
  <section class="section">
    <div class="wrap">
      <div class="sec-head sec-head--center stack" data-reveal>
        <span class="eyebrow">Three seconds to apply</span>
        <h2 class="h2">How Nurva works</h2>
      </div>

      <div class="steps">
        <div class="steps__line" aria-hidden="true"></div>
        <div class="grid grid--4 reveal-stagger">
          <div class="step stack">
            <div class="step__disc">1</div>
            <h3 class="h3">Clean &amp; dry</h3>
            <p class="muted">Wash and dry the bridge of your nose so the adhesive grips properly.</p>
          </div>
          <div class="step stack">
            <div class="step__disc">2</div>
            <h3 class="h3">Peel &amp; place</h3>
            <p class="muted">Remove the liner and centre the strip just above the flare of your nostrils.</p>
          </div>
          <div class="step stack">
            <div class="step__disc">3</div>
            <h3 class="h3">Press &amp; hold</h3>
            <p class="muted">Press the ends down for five seconds. The spring bands do the rest.</p>
          </div>
          <div class="step stack">
            <div class="step__disc">4</div>
            <h3 class="h3">Breathe</h3>
            <p class="muted">Train, race or sleep. Peel off gently under warm water.</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</div>'''

REVIEWS = r'''<div class="nurva">
  <section class="section section--raised">
    <div class="wrap wrap--wide">
      <div class="sec-head sec-head--center stack" data-reveal>
        <span class="eyebrow">Real users</span>
        <h2 class="h2">Trusted by people who train</h2>
      </div>

      <div class="quotes" data-reveal>
        <figure class="quote stack">
          <div class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
          <blockquote class="quote__text">First run where I wasn't gasping through my mouth by kilometre three.</blockquote>
          <figcaption class="quote__who">
            <span class="quote__avatar">M</span>
            <span><span class="quote__name">Marcus T.</span><br><span class="quote__meta">Verified buyer</span></span>
          </figcaption>
        </figure>

        <figure class="quote stack">
          <div class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
          <blockquote class="quote__text">My partner stopped elbowing me at 2am. Worth it for that alone.</blockquote>
          <figcaption class="quote__who">
            <span class="quote__avatar">P</span>
            <span><span class="quote__name">Priya R.</span><br><span class="quote__meta">Verified buyer</span></span>
          </figcaption>
        </figure>

        <figure class="quote stack">
          <div class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
          <blockquote class="quote__text">Holds twice as long as the drug-store brand and doesn't curl when I sweat.</blockquote>
          <figcaption class="quote__who">
            <span class="quote__avatar">D</span>
            <span><span class="quote__name">Danny K.</span><br><span class="quote__meta">Verified buyer</span></span>
          </figcaption>
        </figure>
      </div>
    </div>
  </section>
</div>'''

FAQ = r'''<div class="nurva">
  <section class="section">
    <div class="wrap wrap--narrow">
      <div class="sec-head sec-head--center stack" data-reveal>
        <span class="eyebrow">Answers</span>
        <h2 class="h2">Before you buy</h2>
      </div>

      <div class="faq" data-faq data-faq-single="true" data-reveal>
        <div class="faq__item" data-open="false">
          <h3><button class="faq__q" type="button" aria-expanded="false"><span>Will it stay on while I train?</span><span class="faq__sign" aria-hidden="true"></span></button></h3>
          <div class="faq__a"><div><p>Yes — sweat-resistant medical-grade adhesive rated for up to 10 hours, including humid conditions. Apply to clean, dry skin.</p></div></div>
        </div>

        <div class="faq__item" data-open="false">
          <h3><button class="faq__q" type="button" aria-expanded="false"><span>Does it help with snoring?</span><span class="faq__sign" aria-hidden="true"></span></button></h3>
          <div class="faq__a"><div><p>It helps when snoring is driven by nasal congestion or a narrow nasal valve. It is not a treatment for sleep apnoea — speak to a doctor if you suspect that.</p></div></div>
        </div>

        <div class="faq__item" data-open="false">
          <h3><button class="faq__q" type="button" aria-expanded="false"><span>Can I reuse a strip?</span><span class="faq__sign" aria-hidden="true"></span></button></h3>
          <div class="faq__a"><div><p>No. Each strip is single use.</p></div></div>
        </div>

        <div class="faq__item" data-open="false">
          <h3><button class="faq__q" type="button" aria-expanded="false"><span>What if it doesn't work for me?</span><span class="faq__sign" aria-hidden="true"></span></button></h3>
          <div class="faq__a"><div><p>Tell us within 30 nights and we'll refund you. You don't need to send the pack back.</p></div></div>
        </div>
      </div>
    </div>
  </section>
</div>'''

ALL_MARKUP = MAIN_PRODUCT + BADGES + HOW + REVIEWS + FAQ

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

BOOTSTRAP = (
    "<script>\n"
    "window.Shopify = window.Shopify || {};\n"
    "window.Shopify.moneyFormat = window.Shopify.moneyFormat || " + json.dumps("{{ shop.money_format }}") + ";\n"
    "window.Shopify.routes = window.Shopify.routes || {};\n"
    "window.Shopify.routes.root = window.Shopify.routes.root || " + json.dumps("{{ routes.root_url | append: '/' | replace: '//', '/' }}") + ";\n"
    "</script>\n"
)

section_file = (
    "{%- comment -%}\n"
    "  NURVA PERFORMANCE — product page section.\n"
    "\n"
    "  Online Store -> Themes -> Edit code -> Sections -> Add a new section,\n"
    "  name it  nurva-product  (Shopify adds the .liquid), paste this in, Save.\n"
    "  Then open your PRODUCT template (Edit code -> Templates -> product.json,\n"
    "  or Customize -> pick a product -> Add section) and add Nurva product.\n"
    "\n"
    "  Uses the page's own `product` object automatically — nothing to pick.\n"
    "  Styles are scoped under .nurva and cannot affect the rest of your theme.\n"
    "{%- endcomment -%}\n\n"
    "{%- assign current_variant = product.selected_or_first_available_variant -%}\n"
    "{%- assign on_sale = false -%}\n"
    "{%- if current_variant.compare_at_price > current_variant.price -%}\n"
    "  {%- assign on_sale = true -%}\n"
    "{%- endif -%}\n\n"
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=Barlow+Condensed:wght@600;700;800&family=Inter:wght@400;500;600;700'
    '&family=Montserrat:wght@600;700;800&display=swap">\n\n'
    "<style>{% raw %}\n" + lean_css + "\n{% endraw %}</style>\n\n"
    '<noscript><style>.nurva [data-reveal],.nurva .reveal-stagger>*{opacity:1!important;transform:none!important}</style></noscript>\n\n'
    + BOOTSTRAP + "\n"
    "<script>{% raw %}\n" + js + "\n{% endraw %}</script>\n\n"
    + ALL_MARKUP + "\n\n"
    + "{% schema %}\n"
    + json.dumps({"name": "Nurva product", "tag": "section", "settings": []}, indent=2)
    + "\n{% endschema %}\n"
)

out_path = os.path.join(ROOT, 'paste', 'nurva-product.liquid')
open(out_path, 'w', encoding='utf-8').write(section_file)
print('css: full %d -> lean %d chars' % (len(full_css), len(lean_css)))
print('paste/nurva-product.liquid: %d chars' % len(section_file))
