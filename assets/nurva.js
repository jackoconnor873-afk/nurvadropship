/* ==========================================================================
   NURVA PERFORMANCE — Theme behaviour
   Vanilla JS, no dependencies. Everything degrades gracefully.
   ========================================================================== */

(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  /* ---------------------------------------------------------------------
     Scroll reveal
     --------------------------------------------------------------------- */
  function initReveal(root) {
    var scope = root || document;
    var targets = scope.querySelectorAll('[data-reveal], .reveal-stagger');
    if (!targets.length) return;

    if (reduceMotion || !('IntersectionObserver' in window)) {
      targets.forEach(function (el) { el.classList.add('is-in'); });
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-in');
        observer.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.12 });

    targets.forEach(function (el) {
      var delay = el.getAttribute('data-reveal-delay');
      if (delay) el.style.setProperty('--reveal-delay', delay + 'ms');
      observer.observe(el);
    });
  }

  /* ---------------------------------------------------------------------
     Count-up numbers  ->  <span data-count="98" data-suffix="%">
     --------------------------------------------------------------------- */
  function initCounters(root) {
    var scope = root || document;
    var nodes = scope.querySelectorAll('[data-count]');
    if (!nodes.length) return;

    function render(el, value) {
      var decimals = parseInt(el.getAttribute('data-decimals') || '0', 10);
      el.textContent =
        (el.getAttribute('data-prefix') || '') +
        value.toFixed(decimals) +
        (el.getAttribute('data-suffix') || '');
    }

    function run(el) {
      var target = parseFloat(el.getAttribute('data-count'));
      if (isNaN(target)) return;
      if (reduceMotion) { render(el, target); return; }

      var duration = parseInt(el.getAttribute('data-duration') || '1600', 10);
      var start = null;

      function frame(now) {
        if (start === null) start = now;
        var p = Math.min((now - start) / duration, 1);
        // easeOutExpo
        var eased = p === 1 ? 1 : 1 - Math.pow(2, -10 * p);
        render(el, target * eased);
        if (p < 1) requestAnimationFrame(frame);
      }
      requestAnimationFrame(frame);
    }

    if (!('IntersectionObserver' in window)) {
      nodes.forEach(run);
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        run(entry.target);
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.5 });

    nodes.forEach(function (el) {
      render(el, 0);
      observer.observe(el);
    });
  }

  /* ---------------------------------------------------------------------
     Sticky header state + scroll progress bar
     --------------------------------------------------------------------- */
  function initScrollChrome() {
    var header = document.querySelector('[data-header]');
    var progress = document.querySelector('[data-progress]');
    if (!header && !progress) return;

    var ticking = false;

    function update() {
      var y = window.scrollY || window.pageYOffset;

      if (header) header.classList.toggle('is-stuck', y > 12);

      if (progress) {
        var max = document.documentElement.scrollHeight - window.innerHeight;
        var ratio = max > 0 ? Math.min(y / max, 1) : 0;
        progress.style.transform = 'scaleX(' + ratio + ')';
      }
      ticking = false;
    }

    window.addEventListener('scroll', function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(update);
    }, { passive: true });

    update();
  }

  /* ---------------------------------------------------------------------
     Mobile drawer
     --------------------------------------------------------------------- */
  function initDrawer() {
    var drawer = document.querySelector('[data-drawer]');
    if (!drawer) return;

    var openers = document.querySelectorAll('[data-drawer-open]');
    var closers = drawer.querySelectorAll('[data-drawer-close]');
    var lastFocus = null;

    function setOpen(open) {
      drawer.setAttribute('data-open', open ? 'true' : 'false');
      document.body.style.overflow = open ? 'hidden' : '';
      openers.forEach(function (btn) { btn.setAttribute('aria-expanded', open ? 'true' : 'false'); });

      if (open) {
        lastFocus = document.activeElement;
        var links = drawer.querySelectorAll('.drawer__link');
        links.forEach(function (link, i) {
          link.style.transitionDelay = (0.12 + i * 0.055) + 's';
        });
        var first = drawer.querySelector('a, button');
        if (first) setTimeout(function () { first.focus(); }, 320);
      } else if (lastFocus) {
        lastFocus.focus();
      }
    }

    openers.forEach(function (btn) {
      btn.addEventListener('click', function () { setOpen(true); });
    });
    closers.forEach(function (btn) {
      btn.addEventListener('click', function () { setOpen(false); });
    });
    drawer.addEventListener('click', function (e) {
      if (e.target.hasAttribute('data-drawer-close')) setOpen(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && drawer.getAttribute('data-open') === 'true') setOpen(false);
    });
  }

  /* ---------------------------------------------------------------------
     FAQ accordion
     --------------------------------------------------------------------- */
  function initAccordion(root) {
    var scope = root || document;
    scope.querySelectorAll('[data-faq]').forEach(function (list) {
      var single = list.getAttribute('data-faq-single') !== 'false';

      list.querySelectorAll('.faq__q').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var item = btn.closest('.faq__item');
          var isOpen = item.getAttribute('data-open') === 'true';

          if (single) {
            list.querySelectorAll('.faq__item').forEach(function (other) {
              other.setAttribute('data-open', 'false');
              var q = other.querySelector('.faq__q');
              if (q) q.setAttribute('aria-expanded', 'false');
            });
          }

          item.setAttribute('data-open', isOpen ? 'false' : 'true');
          btn.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
        });
      });
    });
  }

  /* ---------------------------------------------------------------------
     Pointer-follow glow on cards
     --------------------------------------------------------------------- */
  function initCardGlow(root) {
    if (reduceMotion) return;
    var scope = root || document;
    scope.querySelectorAll('.bcard').forEach(function (card) {
      card.addEventListener('pointermove', function (e) {
        var r = card.getBoundingClientRect();
        card.style.setProperty('--mx', ((e.clientX - r.left) / r.width) * 100 + '%');
        card.style.setProperty('--my', ((e.clientY - r.top) / r.height) * 100 + '%');
      });
    });
  }

  /* ---------------------------------------------------------------------
     Marquee — duplicate the group so the loop is seamless
     --------------------------------------------------------------------- */
  function initMarquee(root) {
    var scope = root || document;
    scope.querySelectorAll('[data-marquee]').forEach(function (track) {
      if (track.getAttribute('data-cloned') === 'true') return;
      var group = track.querySelector('.marquee__group');
      if (!group) return;
      var clone = group.cloneNode(true);
      clone.setAttribute('aria-hidden', 'true');
      track.appendChild(clone);
      track.setAttribute('data-cloned', 'true');
    });
  }

  /* ---------------------------------------------------------------------
     Quantity stepper
     --------------------------------------------------------------------- */
  function initQty(root) {
    var scope = root || document;
    scope.querySelectorAll('[data-qty]').forEach(function (widget) {
      var input = widget.querySelector('input');
      if (!input) return;
      widget.querySelectorAll('button[data-qty-step]').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var step = parseInt(btn.getAttribute('data-qty-step'), 10) || 1;
          var min = parseInt(input.getAttribute('min') || '1', 10);
          var next = (parseInt(input.value, 10) || min) + step;
          input.value = Math.max(min, next);
          input.dispatchEvent(new Event('change', { bubbles: true }));
        });
      });
    });
  }

  /* ---------------------------------------------------------------------
     Product gallery thumbnails
     --------------------------------------------------------------------- */
  function initGallery(root) {
    var scope = root || document;
    scope.querySelectorAll('[data-gallery]').forEach(function (gallery) {
      var main = gallery.querySelector('[data-gallery-main] img');
      if (!main) return;
      gallery.querySelectorAll('[data-gallery-thumb]').forEach(function (thumb) {
        thumb.addEventListener('click', function () {
          var full = thumb.getAttribute('data-full');
          if (!full) return;
          main.style.opacity = '0';
          setTimeout(function () {
            main.src = full;
            var srcset = thumb.getAttribute('data-srcset');
            if (srcset) main.srcset = srcset;
            main.style.opacity = '1';
          }, 160);
          gallery.querySelectorAll('[data-gallery-thumb]').forEach(function (t) {
            t.setAttribute('aria-current', t === thumb ? 'true' : 'false');
          });
        });
      });
    });
  }

  /* ---------------------------------------------------------------------
     Sticky buy bar — shows once the main add-to-cart scrolls away
     --------------------------------------------------------------------- */
  function initBuyBar() {
    var bar = document.querySelector('[data-buybar]');
    var anchor = document.querySelector('[data-buybar-anchor]');
    if (!bar || !anchor || !('IntersectionObserver' in window)) return;

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        bar.classList.toggle('is-visible', !entry.isIntersecting && entry.boundingClientRect.top < 0);
      });
    }, { threshold: 0 });

    observer.observe(anchor);
  }

  /* ---------------------------------------------------------------------
     Cart count badge — keeps the header in sync after AJAX adds
     --------------------------------------------------------------------- */
  function refreshCartCount() {
    if (!window.Shopify) return;
    fetch(window.Shopify.routes && window.Shopify.routes.root ? window.Shopify.routes.root + 'cart.js' : '/cart.js', {
      headers: { 'Accept': 'application/json' }
    })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (cart) {
        if (!cart) return;
        document.querySelectorAll('[data-cart-count]').forEach(function (node) {
          node.textContent = cart.item_count;
          node.hidden = cart.item_count === 0;
        });
      })
      .catch(function () { /* silent — the badge is cosmetic */ });
  }

  /* ---------------------------------------------------------------------
     Variant picker — swaps price / availability / hidden id on change
     --------------------------------------------------------------------- */
  function initVariants(root) {
    var scope = root || document;
    scope.querySelectorAll('[data-variant-picker]').forEach(function (picker) {
      var form = picker.closest('form') || document.querySelector('[data-product-form]');
      if (!form) return;

      var dataEl = picker.querySelector('[data-variant-json]');
      if (!dataEl) return;

      var variants;
      try { variants = JSON.parse(dataEl.textContent); } catch (e) { return; }
      if (!Array.isArray(variants)) return;

      var idInput = form.querySelector('[data-variant-id]');
      var submit = form.querySelector('[data-add-button]');
      var priceEl = document.querySelector('[data-variant-price]');
      var compareEl = document.querySelector('[data-variant-compare]');

      function selectedOptions() {
        return Array.prototype.map.call(
          picker.querySelectorAll('[data-option-group]'),
          function (group) {
            var checked = group.querySelector('input:checked');
            return checked ? checked.value : null;
          }
        );
      }

      function money(cents) {
        var format = (window.Shopify && window.Shopify.moneyFormat) || '${{amount}}';
        var amount = (cents / 100).toFixed(2);
        return format.replace(/\{\{\s*amount[^}]*\}\}/, amount);
      }

      function update() {
        var chosen = selectedOptions();
        var match = variants.find(function (v) {
          return chosen.every(function (value, i) {
            return value === null || v.options[i] === value;
          });
        });

        if (!match) {
          if (submit) {
            submit.setAttribute('aria-disabled', 'true');
            submit.textContent = submit.getAttribute('data-unavailable-text') || 'Unavailable';
          }
          return;
        }

        if (idInput) idInput.value = match.id;
        if (priceEl) priceEl.textContent = money(match.price);

        if (compareEl) {
          var onSale = match.compare_at_price && match.compare_at_price > match.price;
          compareEl.textContent = onSale ? money(match.compare_at_price) : '';
          compareEl.hidden = !onSale;
        }

        if (submit) {
          submit.setAttribute('aria-disabled', match.available ? 'false' : 'true');
          submit.textContent = match.available
            ? (submit.getAttribute('data-add-text') || 'Add to cart')
            : (submit.getAttribute('data-soldout-text') || 'Sold out');
        }

        if (match.id && window.history && window.history.replaceState) {
          var url = new URL(window.location.href);
          url.searchParams.set('variant', match.id);
          window.history.replaceState({}, '', url.toString());
        }
      }

      picker.addEventListener('change', update);
      update();
    });
  }

  /* ---------------------------------------------------------------------
     AJAX add to cart
     --------------------------------------------------------------------- */
  function initAddToCart(root) {
    var scope = root || document;
    scope.querySelectorAll('[data-product-form]').forEach(function (form) {
      form.addEventListener('submit', function (e) {
        if (!window.Shopify) return; // outside Shopify, let the form behave normally
        e.preventDefault();

        var button = form.querySelector('[data-add-button]');
        var original = button ? button.textContent : '';
        if (button) {
          button.setAttribute('aria-disabled', 'true');
          button.textContent = 'Adding…';
        }

        var root = (window.Shopify.routes && window.Shopify.routes.root) || '/';

        fetch(root + 'cart/add.js', {
          method: 'POST',
          headers: { 'Accept': 'application/json' },
          body: new FormData(form)
        })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (data.status && data.status !== 200) throw new Error(data.description || 'Could not add to cart');
            if (button) button.textContent = 'Added ✓';
            refreshCartCount();
            setTimeout(function () {
              if (button) {
                button.textContent = original;
                button.setAttribute('aria-disabled', 'false');
              }
            }, 1800);
          })
          .catch(function (err) {
            if (button) {
              button.textContent = original;
              button.setAttribute('aria-disabled', 'false');
            }
            var note = form.querySelector('[data-form-error]');
            if (note) { note.textContent = err.message; note.hidden = false; }
          });
      });
    });
  }

  /* ---------------------------------------------------------------------
     Boot
     --------------------------------------------------------------------- */
  function boot(root) {
    initReveal(root);
    initCounters(root);
    initAccordion(root);
    initCardGlow(root);
    initMarquee(root);
    initQty(root);
    initGallery(root);
    initVariants(root);
    initAddToCart(root);
  }

  ready(function () {
    boot(document);
    initScrollChrome();
    initDrawer();
    initBuyBar();
    refreshCartCount();
  });

  /* Re-run when the Shopify theme editor swaps a section in */
  document.addEventListener('shopify:section:load', function (e) {
    boot(e.target);
    initBuyBar();
  });
  document.addEventListener('shopify:section:select', function (e) {
    boot(e.target);
  });

  window.Nurva = { boot: boot, refreshCartCount: refreshCartCount };
})();
