"""Kaayal design system — shared tokens + page shell.

Brand direction: "Backwater Editorial" (see docs/design/KAAYAL_DESIGN_SYSTEM.md).
Same tokens serve all three expressions: tourist-facing editorial pages,
Lagoon Glass voice surfaces, and Coastal Utility operator/admin screens.
"""

import html

# --- Design tokens -----------------------------------------------------------
LAGOON = "#123F3C"
TEAL = "#267A73"
IVORY = "#F7F5EE"
MIST = "#D9E6DE"
SAND = "#C68E55"
INK = "#17302E"

# Satoshi (Fontshare) for UI text; Fraunces for editorial display;
# Noto Sans Malayalam for Malayalam script.
_FAVICON = (
    '<link rel="icon" href="data:image/svg+xml,%3Csvg'
    " xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
    "%3Crect width='32' height='32' rx='8' fill='%23123F3C'/%3E"
    "%3Cpath d='M5 17c4-3 8-3 12 0s8 3 10 0' stroke='%23F7F5EE'"
    " fill='none' stroke-width='2' stroke-linecap='round'/%3E"
    "%3Cpath d='M5 23c4-3 8-3 12 0s8 3 10 0' stroke='%23267A73'"
    " fill='none' stroke-width='2' stroke-linecap='round'/%3E%3C/svg%3E\">"
)

_FONT_LINKS = (
    '<link rel="preconnect" href="https://api.fontshare.com">'
    '<link rel="preconnect" href="https://cdn.fontshare.com" crossorigin>'
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700&display=swap" rel="stylesheet">'
    '<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500'
    "&family=Noto+Sans+Malayalam:wght@400;500;700&display=swap\" rel=\"stylesheet\">"
)

BODY_FONT = "'Satoshi','Noto Sans Malayalam',system-ui,-apple-system,sans-serif"
DISPLAY_FONT = "'Fraunces','Noto Sans Malayalam',Georgia,serif"

CSS = f"""
:root {{
  --lagoon: {LAGOON}; --teal: {TEAL}; --ivory: {IVORY};
  --mist: {MIST}; --sand: {SAND}; --ink: {INK};
  --line: #D8DED6; --line: color-mix(in srgb, var(--lagoon) 18%, transparent);
}}
* {{ box-sizing: border-box; }}
html {{ -webkit-tap-highlight-color: transparent; }}
body {{
  font-family: {BODY_FONT};
  background: var(--ivory);
  color: var(--ink);
  max-width: 44rem;
  margin: 0 auto;
  padding: 2.5rem 1.25rem 4rem;
  line-height: 1.6;
  font-size: 1.0625rem;
}}
body.wide {{ max-width: 62rem; }}
.tablewrap {{ overflow-x: auto; }}
.notice {{
  border: 1px solid var(--line); border-left: 3px solid var(--teal);
  border-radius: .25rem; padding: .55rem 1rem; margin: 1rem 0;
  background: color-mix(in srgb, var(--teal) 8%, var(--ivory));
  font-size: .95rem;
}}
.skip {{
  position: absolute; left: -9999px; top: 0;
  background: var(--lagoon); color: var(--ivory); padding: .5rem 1rem; z-index: 10;
}}
.skip:focus {{ left: 0; }}
h1, h2, h3 {{ font-family: {DISPLAY_FONT}; color: var(--lagoon); text-wrap: balance; line-height: 1.15; }}
h1 {{ font-size: 2.25rem; font-weight: 500; margin: 0 0 .5rem; }}
h2 {{ font-size: 1.35rem; font-weight: 500; margin: 2.5rem 0 .75rem; }}
h3 {{ font-size: 1.05rem; font-weight: 500; margin: 0 0 .5rem; font-family: {BODY_FONT}; }}
a {{ color: var(--teal); text-underline-offset: .18em; }}
a:hover {{ color: var(--lagoon); }}
a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible, summary:focus-visible {{
  outline: 2px solid var(--teal); outline-offset: 2px;
}}
table {{ border-collapse: collapse; width: 100%; font-size: .95rem; }}
th {{ text-align: left; font-weight: 500; color: var(--teal); font-size: .8rem;
     border-bottom: 1px solid var(--lagoon); padding: .4rem .5rem .4rem 0; }}
td {{ border-bottom: 1px solid var(--line); padding: .55rem .5rem .55rem 0; vertical-align: top; }}
.badge {{
  display: inline-block; padding: .15rem .6rem; border-radius: 999px;
  font-size: .78rem; font-weight: 500; border: 1px solid transparent;
}}
.ok {{ background: color-mix(in srgb, var(--teal) 14%, var(--ivory)); color: var(--lagoon); border-color: color-mix(in srgb, var(--teal) 40%, transparent); }}
.wait {{ background: color-mix(in srgb, var(--sand) 18%, var(--ivory)); color: #6B4A26; border-color: color-mix(in srgb, var(--sand) 55%, transparent); }}
.bad {{ background: #F3E3E1; color: #7A2E2E; border-color: #D9AFAF; }}
form.inline {{ display: inline; }}
label {{ display: block; font-size: .85rem; font-weight: 500; color: var(--lagoon); margin: .9rem 0 .25rem; }}
input, select {{
  font: inherit; font-size: .95rem; color: var(--ink);
  background: #FDFCF9; border: 1px solid #9DB3AC; border-radius: .375rem;
  padding: .55rem .7rem; width: 100%; max-width: 26rem;
  touch-action: manipulation;
}}
input::placeholder {{ color: #6E857E; }}
button, .btn {{
  font: inherit; font-weight: 500; font-size: .95rem; cursor: pointer;
  background: var(--teal); color: var(--ivory);
  border: 1px solid var(--teal); border-radius: .375rem;
  padding: .55rem 1.1rem; touch-action: manipulation;
  min-height: 2.75rem; display: inline-flex; align-items: center;
  transition: background-color .15s ease, border-color .15s ease, transform .15s ease;
}}
button:hover, .btn:hover {{
  background: var(--lagoon); border-color: var(--lagoon); color: var(--ivory);
  transform: translateY(-1px);
}}
button:active, .btn:active {{ transform: translateY(0); }}
button.secondary {{ background: transparent; color: var(--teal); border-color: var(--mist); }}
button.secondary:hover {{ border-color: var(--teal); color: var(--lagoon); background: transparent; }}
button.danger {{ background: transparent; color: #7A2E2E; border-color: #D9AFAF; }}
button.danger:hover {{ background: #F3E3E1; color: #7A2E2E; border-color: #7A2E2E; }}
.card {{
  border: 1px solid var(--line); border-left: 3px solid var(--sand);
  border-radius: .25rem; padding: 1rem 1.25rem; margin: 1rem 0;
  background: #FDFCF9;
}}
.card h2, .card h3 {{ margin: 0 0 .25rem; font-family: {DISPLAY_FONT}; font-size: 1.2rem; color: var(--lagoon); }}
.faq-q {{ font-family: {BODY_FONT}; font-size: 1.05rem; font-weight: 500; margin: 1.75rem 0 .35rem; }}
.muted {{ color: #4A6B66; }}
.small {{ font-size: .85rem; }}
.rule {{ border: 0; border-top: 1px solid var(--line); margin: 2.5rem 0; }}
ol ::marker {{ color: var(--teal); font-family: {DISPLAY_FONT}; }}
.lead {{ font-size: 1.15rem; max-width: 34rem; }}
.kick {{
  letter-spacing: .14em; text-transform: uppercase; font-size: .72rem;
  font-weight: 600; color: #8A5F33; margin: 0 0 .2rem;
}}
/* --- editorial landing ---------------------------------------------------- */
.hero {{ display: grid; grid-template-columns: minmax(0,1fr) auto; gap: 1.5rem 3rem; align-items: center; }}
.hero h1 {{ font-size: clamp(2.4rem, 5.5vw, 3.4rem); margin: .3rem 0 .9rem; }}
.hero-art {{ margin: 0; text-align: center; }}
.hero-art figcaption {{ margin-top: 1rem; }}
.avatar-wrap {{ position: relative; display: inline-block; }}
.avatar-wrap img {{ display: block; border-radius: 50%; border: 2px solid var(--mist); background: #FDFCF9; }}
.avatar-wrap::after {{
  content: ""; position: absolute; inset: -9px; border-radius: 50%;
  border: 2px solid transparent; border-top-color: var(--sand);
  transform: rotate(-28deg); pointer-events: none;
}}
.paayal-fig {{ display: grid; grid-template-columns: auto 1fr; gap: 2rem; align-items: start; margin: 1rem 0 1.75rem; }}
.paayal-portrait {{ text-align: center; }}
.paayal-portrait .voicewave {{ display: block; margin: 1.1rem auto .35rem; }}
.paayal-portrait .greeting {{ font-size: 1.15rem; color: var(--lagoon); margin: .45rem 0 0; }}
.paayal-portrait .muted {{ margin-top: .15rem; }}
.voicewave rect {{ transform-box: fill-box; transform-origin: center; }}
.asks {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(14rem,1fr)); gap: .6rem; margin: .6rem 0 1rem; }}
.ask {{
  font-family: {DISPLAY_FONT}; font-size: 1.05rem; color: var(--lagoon); margin: 0;
  padding: .6rem .9rem; border-left: 3px solid var(--sand);
  background: #FDFCF9; border-radius: .25rem;
}}
.flow {{ list-style: none; padding: 0; margin: 1rem 0 1.5rem; counter-reset: step; max-width: 40rem; }}
.flow li {{ counter-increment: step; position: relative; padding: .45rem 0 .45rem 2.5rem;
  border-left: 1px solid var(--line); margin-left: .7rem; }}
.flow li::before {{
  content: counter(step,decimal-leading-zero); position: absolute; left: -.85rem; top: .55rem;
  width: 1.7rem; height: 1.7rem; background: var(--ivory); border: 1px solid var(--line);
  border-radius: 50%; text-align: center; font-size: .7rem; line-height: 1.7rem;
  color: var(--teal); font-weight: 500;
}}
details.faq-item {{ border-bottom: 1px solid var(--line); padding: .55rem 0; max-width: 42rem; }}
details.faq-item summary {{
  cursor: pointer; font-weight: 500; font-size: 1.02rem; color: var(--ink);
  list-style: none; position: relative; padding: .35rem 0 .35rem 1.5rem;
}}
details.faq-item summary::-webkit-details-marker {{ display: none; }}
details.faq-item summary::before {{
  content: "+"; position: absolute; left: .2rem; color: var(--teal); font-weight: 500;
  transition: transform .15s ease;
}}
details.faq-item[open] summary::before {{ transform: rotate(45deg); }}
details.faq-item p {{ margin: .3rem 0 .8rem 1.5rem; }}
.dropcap::first-letter {{
  font-family: {DISPLAY_FONT}; font-size: 3.1em; float: left; line-height: .82;
  padding: .06em .12em 0 0; color: var(--lagoon);
}}
section > p, section > ul {{ max-width: 42rem; }}
.duo {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0 2.5rem; }}
@media (max-width: 700px) {{ .duo {{ grid-template-columns: 1fr; }} }}
[data-plx] {{ will-change: transform; }}
/* Section bands — flat tonal slabs with a faint grain texture, no gradients. */
.band {{
  background-color: color-mix(in srgb, var(--mist) 42%, var(--ivory));
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='140' height='140'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.07 0 0 0 0 0.25 0 0 0 0 0.24 0 0 0 0.045 0'/></filter><rect width='140' height='140' filter='url(%23n)'/></svg>");
  margin: 0 -1.25rem; padding: .75rem 1.25rem 2.25rem;
}}
.band-dark {{
  background-color: var(--lagoon); color: var(--ivory);
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='140' height='140'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.97 0 0 0 0 0.96 0 0 0 0 0.93 0 0 0 0.05 0'/></filter><rect width='140' height='140' filter='url(%23n)'/></svg>");
  margin: 0 -1.25rem; padding: .75rem 1.25rem 2.5rem;
}}
.band-dark h2, .band-dark h3 {{ color: var(--ivory); }}
.band-dark .kick {{ color: var(--sand); }}
.band-dark .muted {{ color: var(--mist); }}
.band-dark a {{ color: var(--mist); }}
.band-dark a:hover {{ color: var(--ivory); }}
.band-dark .btn {{
  background: var(--ivory); color: var(--lagoon); border-color: var(--ivory);
}}
.band-dark .btn:hover {{
  background: var(--sand); border-color: var(--sand); color: var(--ivory);
}}
@media (max-width: 700px) {{
  .hero {{ grid-template-columns: 1fr; }}
  .hero-art {{ text-align: left; }}
  .paayal-fig {{ grid-template-columns: 1fr; }}
  .paayal-portrait {{ text-align: left; }}
  .paayal-portrait .voicewave {{ margin-left: 0; }}
}}
@media (max-width: 640px) {{
  .topnav {{ flex-wrap: nowrap; overflow-x: auto; gap: .95rem; scrollbar-width: none; }}
  .topnav::-webkit-scrollbar {{ display: none; }}
  .topnav .wordmark {{ font-size: 1.2rem; }}
  .topnav a.navlink {{ white-space: nowrap; }}
}}
html {{ scroll-behavior: smooth; }}
section[id] {{ scroll-margin-top: 5.5rem; margin-top: 3.25rem; }}
h2[id] {{ scroll-margin-top: 4.5rem; }}
td.actions, th.actions {{ white-space: nowrap; text-align: right; }}
.tablewrap td {{ vertical-align: middle; }}
td.actions form.inline button {{ min-height: 2.5rem; padding: .35rem .8rem; font-size: .85rem; margin: .1rem .3rem .1rem 0; }}
@keyframes ping {{
  0% {{ box-shadow: 0 0 0 0 rgba(38, 122, 115, .32); }}
  100% {{ box-shadow: 0 0 0 20px rgba(38, 122, 115, 0); }}
}}
.sonar {{ animation: ping 2.8s ease-out infinite; }}
.sonar:hover {{ animation-play-state: paused; }}
@keyframes ripple {{
  0% {{ transform: scale(.75); opacity: .55; }}
  100% {{ transform: scale(1.7); opacity: 0; }}
}}
.rip {{
  transform-box: fill-box; transform-origin: center; opacity: 0;
  animation: ripple 3.8s ease-out infinite;
}}
.rip2 {{ animation-delay: 1.9s; }}
.ml {{ font-family: 'Noto Sans Malayalam', {BODY_FONT}; }}
.topnav {{
  display: flex; align-items: baseline; gap: 1.15rem; flex-wrap: nowrap;
  overflow-x: auto; scrollbar-width: none;
  border-bottom: 1px solid var(--line); padding-bottom: .85rem; margin-bottom: 2.25rem;
  position: sticky; top: 0; z-index: 5; background: var(--ivory); padding-top: .9rem;
}}
.topnav::-webkit-scrollbar {{ display: none; }}
.topnav .wordmark {{
  font-family: {DISPLAY_FONT}; font-size: 1.35rem; color: var(--lagoon);
  text-decoration: none; margin-right: auto; white-space: nowrap; flex-shrink: 0;
}}
.topnav .wordmark:hover {{ color: var(--teal); }}
.topnav a.navlink {{
  color: var(--ink); text-decoration: none; font-size: .95rem; padding: .45rem 0;
  white-space: nowrap; flex-shrink: 0;
}}
.topnav a.navlink:hover {{ color: var(--teal); text-decoration: underline; }}
.fab-call {{
  position: fixed; right: 1.25rem; z-index: 6;
  bottom: calc(1.25rem + env(safe-area-inset-bottom, 0px));
  display: inline-flex; align-items: center; gap: .55rem;
  background: var(--teal); color: var(--ivory); border: none; border-radius: .25rem;
  padding: .75rem 1.15rem; font: 600 .95rem/1 {BODY_FONT}; letter-spacing: .01em;
  text-decoration: none; cursor: pointer;
  box-shadow: 0 0 0 1.5px var(--ivory), 0 6px 18px rgba(18,63,60,.28);
}}
.fab-call:hover {{ background: var(--lagoon); text-decoration: none; }}
.fab-call .voicewave rect {{ transform-origin: bottom; }}
.site-footer {{
  border-top: 1px solid var(--line); margin-top: 3rem; padding-top: 1.1rem;
  font-size: .95rem; color: #4A6B66; padding-bottom: 4.5rem;
}}
.chip {{
  display: inline-block; padding: .1rem .55rem; border: 1px solid var(--mist);
  border-radius: 999px; font-size: .8rem; color: var(--lagoon); margin: .1rem .15rem .1rem 0;
}}
.error-box {{
  border: 1px solid #D9AFAF; border-left: 3px solid #7A2E2E; border-radius: .25rem;
  background: #F3E3E1; color: #7A2E2E; padding: .7rem 1rem; margin: 1rem 0; font-size: .95rem;
}}
code {{
  font-family: ui-monospace, 'SF Mono', Menlo, monospace; font-size: .85em;
  background: var(--mist); padding: .1em .4em; border-radius: .25rem;
  word-break: break-all;
}}
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ transition: none !important; animation: none !important; }}
  html {{ scroll-behavior: auto; }}
}}
"""


# Progressive-enhancement motion (motion.dev, pinned CDN build). If the CDN or
# the module fails, everything still renders statically — animations only ever
# run FROM hidden states, never TO them. prefers-reduced-motion skips all of it.
_MOTION = """
<script type="module">
try {
  const {animate, inView, scroll} =
    await import("https://cdn.jsdelivr.net/npm/motion@12.43.0/+esm");
  if (!matchMedia("(prefers-reduced-motion: reduce)").matches) {
    const ease = [.22, .61, .36, 1];
    const narrow = matchMedia("(max-width:640px)").matches;
    const h1 = document.querySelector("main h1");
    if (h1) animate(h1, {opacity: [0, 1], y: [18, 0]}, {duration: .55, easing: ease});
    document.querySelectorAll("main .lead, main .call_line").forEach((el, i) =>
      animate(el, {opacity: [0, 1], y: [14, 0]}, {duration: .55, delay: .12 + i * .1, easing: ease}));
    inView("main h2, main h3, main .card, main ol li, main .ask, main .faq-item",
      (el) => animate(el, {opacity: [0, 1], y: [12, 0]}, {duration: .45, easing: ease}),
      {amount: .25});
    // Scroll-linked parallax on tagged elements — transform only, damped on mobile.
    document.querySelectorAll("[data-plx]").forEach((el) => {
      const d = parseFloat(el.dataset.plx || "0") * (narrow ? .35 : 1);
      if (d) scroll(animate(el, {y: [d * 55, -d * 55]}),
                    {target: el, offset: ["start end", "end start"]});
    });
    // Paayal: gentle container float + decorative waveform bars (container only —
    // the illustration itself is untouched).
    const med = document.querySelector(".avatar-wrap");
    if (med) animate(med, {y: [0, -5, 0]}, {duration: 5, repeat: Infinity, easing: "ease-in-out"});
    document.querySelectorAll(".voicewave rect").forEach((b, i) =>
      animate(b, {scaleY: [.35, 1, .35]},
              {duration: 1.3 + i * .07, repeat: Infinity, easing: "ease-in-out"}));
    document.querySelectorAll("svg.contours").forEach((svg) => {
      const paths = svg.querySelectorAll("path");
      paths.forEach((p, i) =>
        animate(p, {y: [0, i % 2 ? 5 : -5, 0]},
                {duration: 6 + i * 1.1, delay: i * .4, repeat: Infinity,
                 easing: "ease-in-out"}));
      inView(svg, () => paths.forEach((p, i) => {
        const len = p.getTotalLength();
        p.style.strokeDasharray = len;
        animate(p, {strokeDashoffset: [len, 0]},
                {duration: 1.8, delay: i * .12, easing: "ease-in-out"});
      }), {amount: .4});
    });
    document.querySelectorAll("svg.scene").forEach((scene, si) => {
      inView(scene, () => {
        scene.querySelectorAll("path").forEach((p, i) => {
          try {
            const len = p.getTotalLength();
            p.style.strokeDasharray = len;
            animate(p, {strokeDashoffset: [len, 0]},
                    {duration: 2.4, delay: .15 + i * .09, easing: "ease-in-out"});
          } catch (e) {}
        });
      }, {amount: .35});
      scene.querySelectorAll(".waves path").forEach((p, i) =>
        animate(p, {y: [0, i % 2 ? 4 : -4, 0]},
                {duration: 5.5 + i, delay: i * .5, repeat: Infinity,
                 easing: "ease-in-out"}));
      scene.querySelectorAll(".reeds path").forEach((p, i) =>
        animate(p, {x: [0, i % 2 ? 2.5 : -2.5, 0]},
                {duration: 4.2 + i * .6, delay: i * .3, repeat: Infinity,
                 easing: "ease-in-out"}));
      const boat = scene.querySelector(".boat");
      if (boat) {
        animate(boat, {x: [0, 26, 0]},
                {duration: 18 + si * 4, repeat: Infinity, easing: "ease-in-out"});
        animate(boat, {y: [0, -4, 0]},
                {duration: 4.6, repeat: Infinity, easing: "ease-in-out"});
      }
      const net = scene.querySelector(".net");
      if (net) {
        net.style.transformBox = "view-box";
        net.style.transformOrigin = "452px 58px";
        animate(net, {rotate: [-.4, .4, -.4]},
                {duration: 14, repeat: Infinity, easing: "ease-in-out"});
      }
      const birds = scene.querySelector(".birds");
      if (birds)
        animate(birds, {x: [0, -36, 0]},
                {duration: 22, repeat: Infinity, easing: "ease-in-out"});
    });
  }
} catch (e) { /* decoration only — page is complete without it */ }
</script>
"""


def page(title: str, body: str, description: str = "",
         nav: str = "", footer: str = "",
         canonical_url: str = "", head_extra: str = "",
         og_image: str = "", body_class: str = "") -> str:
    """Full HTML page shell. Caller must escape dynamic content via esc().

    `nav` renders before <main>, `footer` after it — both are trusted HTML
    built by the caller (e.g. site.py's shared chrome). `canonical_url` emits
    canonical + hreflang (en/x-default) link tags + og: meta; `head_extra` is
    trusted HTML appended to <head> (e.g. JSON-LD)."""
    desc = f'<meta name="description" content="{html.escape(description)}">' if description else ""
    canon = ""
    if canonical_url:
        u = html.escape(canonical_url)
        t = html.escape(title)
        d = html.escape(description)
        img = f'<meta property="og:image" content="{html.escape(og_image)}">' if og_image else ""
        desc_og = f'<meta property="og:description" content="{d}">' if description else ""
        canon = (
            f'<link rel="canonical" href="{u}">'
            f'<link rel="alternate" hreflang="en" href="{u}">'
            f'<link rel="alternate" hreflang="x-default" href="{u}">'
            '<meta property="og:type" content="website">'
            f'<meta property="og:title" content="{t}">'
            f'<meta property="og:url" content="{u}">'
            f"{img}{desc_og}"
        )
    body_attr = f' class="{html.escape(body_class)}"' if body_class else ""
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f'<meta name="theme-color" content="{IVORY}">{desc}{canon}'
        f"<title>{html.escape(title)}</title>{_FAVICON}{_FONT_LINKS}{head_extra}"
        f"<style>{CSS}</style></head>"
        f"<body{body_attr}>"
        '<a class="skip" href="#main">Skip to content</a>'
        f'{nav}<main id="main" tabindex="-1">{body}</main>{footer}{_MOTION}</body></html>'
    )


def esc(s) -> str:
    return html.escape(str(s) if s is not None else "")


def status_badge(status: str) -> str:
    cls = {
        "pending": "wait",
        "confirmed": "ok",
        "verified": "ok",
        "converted": "ok",
        "available": "ok",
        "reachable": "ok",
        "approved": "ok",
        "queued": "wait",
        "calling": "wait",
        "unverified": "wait",
        "unavailable": "wait",
        "pending verification": "wait",
        "pending approval": "wait",
        "pending_approval": "wait",
        "blocked": "bad",
        "declined": "bad",
        "cancelled": "bad",
        "expired": "bad",
        "opted_out": "bad",
        "not_interested": "bad",
        "no_answer": "bad",
        "unreachable": "bad",
        "inactive": "bad",
    }.get(status, "wait")
    return f'<span class="badge {cls}">{esc(status)}</span>'
