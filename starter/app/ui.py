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
    '<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;1,9..144,400;1,9..144,500'
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
.skip:hover, .skip:focus {{ color: var(--ivory); }}
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
  font-size: .78rem; font-weight: 500; border: 1px solid transparent; white-space: nowrap;
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
input::placeholder {{ color: #4A6B66; }}
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
a.btn {{ text-decoration: none; }}
a.btn:hover {{ text-decoration: none; }}
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
  font-family: {DISPLAY_FONT}; font-style: italic; font-weight: 500;
  font-size: 1.05rem; color: #8A5F33; margin: 0 0 .2rem;
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
section > p, section > ul {{ max-width: 38rem; }}
section > p.small {{ max-width: 52ch; }}
p.dropcap {{ max-width: 64ch; }}
.paayal-fig > div > p {{ max-width: 38rem; }}
p, li {{ text-wrap: pretty; }}
a.ask {{ display: block; text-decoration: none; }}
a.ask:hover {{ color: var(--teal); border-left-color: var(--teal); }}
.band a:not(.btn) {{ color: color-mix(in srgb, var(--teal) 60%, var(--lagoon)); }}
.duo {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0 2.5rem; }}
@media (max-width: 700px) {{ .duo {{ grid-template-columns: 1fr; }} }}
@media (max-width: 700px) {{
  /* Scroll the table sideways rather than crushing columns to one word. */
  .tablewrap table {{ min-width: 42rem; }}
  .tablewrap th.actions, .tablewrap td.actions {{
    position: sticky; right: 0; background: var(--ivory);
    box-shadow: -6px 0 6px -3px rgba(18, 63, 60, .18);
  }}
}}
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
.band-dark .kick {{ color: color-mix(in srgb, var(--sand) 60%, var(--ivory)); }}
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
html {{ scroll-behavior: smooth; }}
section[id] {{ scroll-margin-top: 5.5rem; margin-top: 3.25rem; }}
h2[id] {{ scroll-margin-top: 4.5rem; }}
td.actions, th.actions {{ white-space: nowrap; text-align: right; }}
.tablewrap td {{ vertical-align: middle; }}
td.actions form.inline button {{ min-height: 2.5rem; padding: .35rem .8rem; font-size: .85rem; margin: .1rem .3rem .1rem 0; }}
.rip {{ transform-box: fill-box; transform-origin: center; opacity: .3; }}
.rip2 {{ opacity: .15; }}
.ml {{ font-family: 'Noto Sans Malayalam', {BODY_FONT}; }}
.topnav {{
  display: flex; align-items: baseline; gap: 1.15rem; flex-wrap: nowrap;
  overflow-x: auto; scrollbar-width: none;
  border-bottom: 1px solid var(--line); padding-bottom: .85rem; margin-bottom: 2.25rem;
  position: sticky; top: 0; z-index: 5; background: var(--ivory); padding-top: .9rem;
  /* Paint the ivory bar edge to edge so full-bleed bands never peek out
     beside the sticky nav; shadows don't add scrollable overflow. */
  box-shadow: 0 0 0 100vmax var(--ivory); clip-path: inset(0 -100vmax);
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
/* Phones: the nav wraps onto rows instead of hiding links off-screen, and
   stops sticking — three sticky rows would eat the viewport; the floating
   call button stays as the persistent action. Must follow the base rules. */
@media (max-width: 640px) {{
  .topnav {{ flex-wrap: wrap; overflow-x: clip; gap: .15rem .95rem; position: static; }}
  .topnav .wordmark {{ font-size: 1.2rem; flex-basis: 100%; margin-bottom: .2rem; }}
  .topnav a.navlink {{ padding: .5rem 0; }}
  section[id], h2[id] {{ scroll-margin-top: 1rem; }}
}}
/* Phones, all pages: just the wordmark up top. The wrapped row of links
   read as clutter; on the public site the call buttons carry the action. */
@media (max-width: 640px) {{
  /* Every page (site, privacy, admin, portal): small wordmark in the
     top-left corner at its desktop size, padded from the top by the same
     gutter as from the left and centred in the header strip. Section links
     are hidden; a page's role label (admin / operator) stays on the right. */
  .topnav a.navlink {{ display: none; }}
  .topnav {{ flex-wrap: nowrap; padding: var(--gutter, 1.25rem) 0; align-items: center; }}
  .topnav .wordmark {{ font-size: 1.35rem; line-height: 1; margin: 0 auto 0 0; flex-basis: auto; }}
}}
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
/* Hidden while an inline call button (or the footer) is on screen: the action
   is already visible there, and the floating copy would only cover text.
   visibility flips after the fade so a hidden button can't take focus. */
.fab-call {{ transition: opacity .2s ease, transform .2s ease, visibility 0s linear 0s, background-color .15s ease; }}
.fab-call.is-hidden {{
  opacity: 0; transform: translateY(.75rem); visibility: hidden; pointer-events: none;
  transition: opacity .2s ease, transform .2s ease, visibility 0s linear .2s;
}}
.fab-call .voicewave rect {{ transform-origin: bottom; }}
.site-footer {{
  border-top: 1px solid var(--line); margin-top: 3rem; padding-top: 1.1rem;
  font-size: .95rem; color: #4A6B66; padding-bottom: 4.5rem;
}}
.site-footer p {{ max-width: 33rem; }}
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
/* --- Coastal Utility: admin + operator portal ------------------------------- */
.topnav .role {{ font-size: .85rem; color: #4A6B66; white-space: nowrap; }}
.sectionnav {{
  display: flex; flex-wrap: wrap; gap: .35rem .5rem; margin: 1.25rem 0 .5rem;
  padding: 0; list-style: none;
}}
.sectionnav a {{
  display: inline-flex; align-items: baseline; gap: .4rem; text-decoration: none;
  color: var(--ink); font-size: .9rem; padding: .35rem .75rem; min-height: 2.25rem;
  border: 1px solid var(--line); border-radius: .375rem; background: #FDFCF9;
}}
.sectionnav a:hover {{ border-color: var(--teal); color: var(--lagoon); }}
.sectionnav .n {{ font-variant-numeric: tabular-nums; color: #4A6B66; font-size: .8rem; }}
.sectionnav .n.hot {{ color: #6B4A26; font-weight: 700; }}
h2 .n {{ font-family: {BODY_FONT}; font-size: .85rem; font-weight: 500; color: #4A6B66; margin-left: .35rem; }}
td.num, th.num {{ font-variant-numeric: tabular-nums; }}
.ledger {{ list-style: none; padding: 0; margin: .35rem 0 0; display: grid; gap: .15rem; }}
.ledger a {{ font-weight: 500; }}
.req {{ display: grid; gap: .35rem; }}
.req-head {{ display: flex; flex-wrap: wrap; align-items: center; gap: .35rem .6rem; margin: 0; }}
.req-head b {{ font-variant-numeric: tabular-nums; }}
.req p {{ margin: 0; }}
.req-actions {{ display: flex; flex-wrap: wrap; align-items: center; gap: .5rem; margin-top: .5rem; }}
.req-actions input {{ max-width: 16rem; flex: 1 1 12rem; }}
.req-actions button {{ margin: 0; }}
.card.quiet {{ border-left-color: var(--line); background: transparent; }}
details.disclose {{ border: 1px solid var(--line); border-left: 3px solid var(--sand); border-radius: .25rem; background: #FDFCF9; margin: 1rem 0; }}
details.disclose > summary {{
  cursor: pointer; list-style: none; padding: .8rem 1.25rem; font-weight: 500; color: var(--lagoon);
}}
details.disclose > summary::-webkit-details-marker {{ display: none; }}
details.disclose > summary::before {{ content: "+"; color: var(--teal); margin-right: .55rem; display: inline-block; transition: transform .15s ease; }}
details.disclose[open] > summary::before {{ transform: rotate(45deg); }}
details.disclose > div {{ padding: 0 1.25rem 1.1rem; }}
.sr-only {{ position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0; }}
.copyrow {{ display: flex; flex-wrap: wrap; gap: .5rem; align-items: center; }}
.copyrow code {{ flex: 1 1 18rem; padding: .55rem .7rem; }}
/* --- privacy facts: label column + answer column ------------------------------ */
.facts {{ display: grid; grid-template-columns: 11rem minmax(0, 38rem); gap: 0 2rem; margin: 1.5rem 0 0; }}
.facts dt {{ font-family: {DISPLAY_FONT}; font-size: 1.05rem; color: var(--lagoon); padding: 1rem 0 0; border-top: 1px solid var(--line); }}
.facts dd {{ margin: 0; padding: 1rem 0 0; border-top: 1px solid var(--line); }}
.facts dd p {{ margin: 0 0 1rem; }}
@media (max-width: 700px) {{
  .facts {{ grid-template-columns: 1fr; }}
  .facts dd {{ border-top: 0; padding-top: .3rem; }}
}}
/* --- Public site: Backwater Editorial at full strength ------------------------
   One spacing scale drives every section (--section-y), bands bleed edge to edge,
   headings sit in a sticky left column while the content scrolls past them. */
body.site {{
  --section-y: clamp(4.5rem, 9vw, 7.5rem);
  --gutter: clamp(1.25rem, 4vw, 3rem);
  max-width: 76rem; padding: 0 var(--gutter) 0;
}}
body.site .topnav {{ margin-bottom: 0; }}
body.site main > section {{ margin: 0; padding: var(--section-y) 0; }}
body.site h2 {{
  font-size: clamp(2.1rem, 3.9vw, 3.25rem); line-height: 1.04; letter-spacing: -.02em;
  font-weight: 400; margin: 0 0 1rem;
}}
body.site h3 {{ font-family: {DISPLAY_FONT}; font-size: 1.3rem; font-weight: 500; margin: 2.25rem 0 .6rem; letter-spacing: -.005em; }}
body.site main p, body.site main li {{ max-width: 62ch; }}
body.site main p.small {{ max-width: 32rem; }}
body.site main p.dropcap {{ max-width: 36rem; }}
body.site ::selection {{ background: color-mix(in srgb, var(--sand) 40%, var(--ivory)); color: var(--lagoon); }}
/* Bands: the colour runs to the window edge, the content keeps the column. */
body.site .band, body.site .band-dark {{
  margin: 0 calc(-1 * var(--gutter)); padding: var(--section-y) var(--gutter); background-image: none;
  box-shadow: 0 0 0 100vmax var(--band-bg); clip-path: inset(0 -100vmax);
}}
body.site .band {{ --band-bg: color-mix(in srgb, var(--mist) 45%, var(--ivory)); background: var(--band-bg); }}
body.site .band-dark {{ --band-bg: var(--lagoon); background: var(--band-bg); }}
/* Editorial split: heading column left (sticky), reading column right. */
.ed {{ display: grid; grid-template-columns: minmax(0, 5fr) minmax(0, 7fr); gap: 2.5rem clamp(2.5rem, 6vw, 6rem); align-items: start; }}
.ed-head {{ position: sticky; top: 6.5rem; }}
.ed-head > p:last-child {{ margin-bottom: 0; }}
.ed > div > h3:first-child, .ed .duo h3 {{ margin-top: 0; }}
.ed > .duo, .ed > .asks-block {{ grid-column: 2; }}
#paayal.ed {{ grid-template-rows: auto auto; }}
#paayal .asks-block {{ grid-column: 1 / -1; margin-top: 1rem; }}
/* A sticky head would slide over the full-width questions row below it. */
#paayal .ed-head {{ position: static; }}
/* Hero: the promise at display size, Paayal's greeting as the proof. */
body.site .hero {{
  grid-template-columns: minmax(0, 7fr) minmax(0, 4fr); gap: 2rem clamp(2rem, 6vw, 5rem);
  padding: clamp(3.5rem, 9vw, 7rem) 0 0; align-items: end;
}}
body.site .hero h1 {{
  font-size: clamp(3rem, 7.4vw, 6rem); line-height: .98; letter-spacing: -.03em;
  font-weight: 400; margin: 0 0 1.75rem; max-width: 13ch;
}}
body.site .lead {{ font-size: clamp(1.1rem, 1.5vw, 1.3rem); line-height: 1.55; max-width: 34rem; }}
body.site .call_line .btn {{ font-size: 1.1rem; padding: .85rem 1.6rem; min-height: 3.25rem; }}
body.site .hero-art {{ text-align: left; padding-bottom: .5rem; }}
body.site .hero-art img {{ width: clamp(10rem, 18vw, 15.5rem); height: auto; }}
body.site .hero-art figcaption {{ margin-top: 1.5rem; display: grid; gap: .35rem; }}
body.site .greeting {{ font-size: clamp(1.35rem, 2vw, 1.7rem); color: var(--lagoon); line-height: 1.35; }}
body.site main > svg.scene, body.site main > svg.contours {{ margin: clamp(2rem, 5vw, 3.5rem) 0 !important; }}
/* Languages: the autonyms themselves, set as a wrapped line of type. */
.tongues {{ list-style: none; padding: 0; margin: 1.5rem 0 0; display: flex; flex-wrap: wrap; gap: .35rem 1.1rem;
  font-size: 1.15rem; color: var(--lagoon); line-height: 1.6; }}
body.site .tongues li {{ max-width: none; }}
.tongues .first {{ font-weight: 700; }}
@media (max-width: 640px) {{ svg.scene {{ min-height: 11rem; }} }}
/* Steps: a horizontal sequence — the numerals carry the order. */
ol.steps {{ list-style: none; padding: 0; margin: 0; counter-reset: s; display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 2.25rem 2.5rem; }}
ol.steps li {{ counter-increment: s; border-top: 1px solid var(--lagoon); padding-top: 1rem; max-width: none; }}
ol.steps li::before {{
  content: counter(s); display: block; font-family: {DISPLAY_FONT}; font-style: italic;
  font-size: 2.75rem; line-height: 1; color: var(--teal); margin-bottom: .75rem;
}}
ol.steps li b {{ display: block; font-family: {DISPLAY_FONT}; font-weight: 500; font-size: 1.2rem; color: var(--lagoon); margin-bottom: .3rem; }}
body.site ol.flow {{ max-width: none; margin: 0 0 1rem; }}
body.site ol.flow li {{ border-left: 0; margin-left: 0; padding: 1rem 0 1rem 3.25rem; border-top: 1px solid var(--line); }}
body.site ol.flow li:first-child {{ border-top: 0; padding-top: 0; }}
body.site ol.flow li::before {{
  content: counter(step); background: none; border: 0; border-radius: 0; width: auto; height: auto;
  left: 0; top: .85rem; font-family: {DISPLAY_FONT}; font-style: italic; font-weight: 400;
  font-size: 1.9rem; line-height: 1; color: var(--teal);
}}
body.site ol.flow li:first-child::before {{ top: -.15rem; }}
/* Paayal: two plain lists, then the questions set as pull lines. */
ul.ticks {{ list-style: none; padding: 0; margin: 0; }}
ul.ticks li {{ padding: .6rem 0; border-top: 1px solid var(--line); }}
body.site .asks {{ display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 0 clamp(2rem, 5vw, 4rem); margin: .5rem 0 1.5rem; }}
body.site .ask, body.site a.ask {{
  background: none; border: 0; border-top: 1px solid color-mix(in srgb, var(--lagoon) 30%, transparent); border-radius: 0;
  padding: 1rem 0 1.1rem; font-style: italic; font-weight: 400;
  font-size: clamp(1.35rem, 2.3vw, 1.85rem); line-height: 1.25; color: var(--lagoon); max-width: none;
}}
body.site a.ask:hover {{ color: var(--teal); text-decoration: underline; text-decoration-thickness: 1px; }}
/* Boats: a ruled listing, not a card grid. */
.listing {{ border-bottom: 1px solid var(--lagoon); }}
.boat {{ display: grid; grid-template-columns: minmax(0, 3fr) minmax(0, 2fr); gap: 1rem 2rem; padding: 1.5rem 0; border-top: 1px solid var(--lagoon); }}
.boat h3 {{ margin: 0 0 .2rem !important; font-size: 1.6rem !important; font-weight: 400 !important; }}
.boat p {{ margin: 0 0 .45rem; }}
.boat h3 .badge {{ font-family: {BODY_FONT}; vertical-align: middle; margin-left: .35rem; }}
.boat-facts {{ list-style: none; padding: 0; margin: .6rem 0 0; font-size: .95rem; }}
.boat-price b {{ font-family: {DISPLAY_FONT}; font-weight: 500; font-size: 1.25rem; color: var(--lagoon); display: block; }}
.listing > .card {{ border: 0; background: none; padding: 1.5rem 0; margin: 0; border-top: 1px solid var(--lagoon); }}
/* FAQ + privacy inside the reading column. */
body.site details.faq-item {{ max-width: none; padding: .35rem 0; }}
body.site details.faq-item:first-child {{ border-top: 1px solid var(--line); }}
body.site details.faq-item summary {{ font-family: {DISPLAY_FONT}; font-size: 1.2rem; font-weight: 400; color: var(--lagoon); padding: .8rem 0 .8rem 1.75rem; }}
body.site details.faq-item summary::before {{ top: .8rem; font-family: {BODY_FONT}; }}
body.site details.faq-item p {{ margin-left: 1.75rem; }}
body.site .facts {{ grid-template-columns: 10rem minmax(0, 1fr); margin-top: 0; }}
body.site .facts dt:first-of-type, body.site .facts dd:first-of-type {{ border-top: 0; padding-top: 0; }}
body.site .privacy-page h1 {{ font-size: clamp(2.4rem, 4.6vw, 3.75rem); line-height: 1.02; letter-spacing: -.025em; font-weight: 400; margin: 0 0 1rem; }}
/* Closing: the loudest moment on the page. */
.closing {{ display: grid; grid-template-columns: minmax(0, 7fr) minmax(0, 4fr); gap: 2.5rem clamp(2.5rem, 6vw, 6rem); align-items: end; }}
body.site #closing h2 {{ font-size: clamp(2.75rem, 6.4vw, 5.25rem); line-height: 1; letter-spacing: -.03em; margin-bottom: 1.25rem; }}
body.site #closing .lead {{ color: var(--mist); }}
.ops-copy {{ border-top: 1px solid color-mix(in srgb, var(--ivory) 30%, transparent); padding-top: 1.25rem; }}
/* A lone houseboat floats above the operators block on the dark band. */
.closing-ops svg.scene-mini {{ display: block; width: 100%; max-width: 26rem; height: auto; min-height: 0; margin: 0 0 1rem; }}
.closing-ops h3 {{ margin-top: 0 !important; }}
.closing-ops p {{ color: var(--mist); }}
/* Secondary to the caller CTA: an outline, so the page keeps one loud button. */
body.site .closing-ops .btn {{ background: transparent; color: var(--ivory); border-color: color-mix(in srgb, var(--ivory) 55%, transparent); }}
body.site .closing-ops .btn:hover {{ background: var(--ivory); color: var(--lagoon); border-color: var(--ivory); }}
body.site .site-footer {{ margin-top: 0; padding-top: 2rem; }}
@media (max-width: 860px) {{
  .ed, .closing, body.site .hero {{ grid-template-columns: 1fr; }}
  .ed > .duo, .ed > .asks-block, #paayal .asks-block {{ grid-column: auto; }}
  .ed-head {{ position: static; }}
  body.site .hero {{ align-items: start; }}
}}
ol.steps li span {{ display: block; }}
@media (max-width: 640px) {{
  /* Phones: numeral in a gutter beside the title instead of its own row. */
  ol.steps {{ gap: 0; }}
  ol.steps li {{ display: grid; grid-template-columns: 2.4rem minmax(0, 1fr); column-gap: .6rem;
    padding: .9rem 0 1rem; border-top-color: var(--line); }}
  ol.steps li:first-child {{ border-top-color: var(--lagoon); }}
  ol.steps li::before {{ grid-row: 1 / span 2; font-size: 2.1rem; margin: -.15rem 0 0; }}
  ol.steps li b {{ font-size: 1.1rem; margin-bottom: .15rem; }}
  body.site .ed-head > p.muted {{ margin-bottom: 0; }}
  .ed {{ row-gap: 1.5rem; }}
  ol.steps, body.site .asks, .boat {{ grid-template-columns: 1fr; }}
  body.site .facts {{ grid-template-columns: 1fr; }}
  body.site .facts dd:first-of-type {{ padding-top: .3rem; }}
}}
/* --- Coastal Utility at full strength: admin + operator portal ----------------
   Same type voice as the public site (Fraunces display, Satoshi UI), no scenery,
   no motion. A tinted header band holds the title and the section jump bar;
   sections breathe on one rhythm; tables are quiet but legible. */
body.util {{ --gutter: clamp(1.25rem, 4vw, 3rem); --band-bg: color-mix(in srgb, var(--mist) 45%, var(--ivory));
  max-width: 76rem; padding: 0 var(--gutter) 4rem; }}
body.util .topnav {{ margin-bottom: 0; }}
.util-head {{
  margin: 0 calc(-1 * var(--gutter)); padding: clamp(2rem, 4vw, 3rem) var(--gutter) 1.5rem;
  background: var(--band-bg); box-shadow: 0 0 0 100vmax var(--band-bg); clip-path: inset(0 -100vmax);
}}
.util-head h1 {{ font-size: clamp(2.2rem, 4.2vw, 3.25rem); font-weight: 400; letter-spacing: -.025em; line-height: 1.02; margin: 0 0 .5rem; }}
.util-head > p {{ margin: 0; max-width: 46rem; }}
.util-head .sectionnav {{ margin: 1.5rem 0 0; }}
.util-head .sectionnav a {{ background: var(--ivory); }}
body.util h2 {{ font-size: clamp(1.5rem, 2.2vw, 1.9rem); font-weight: 400; letter-spacing: -.01em;
  margin: clamp(2.75rem, 5vw, 4rem) 0 1rem; padding-top: 1.25rem; border-top: 1px solid var(--lagoon); }}
body.util h2 .n {{ font-size: .9rem; }}
body.util h3 {{ font-family: {DISPLAY_FONT}; font-weight: 500; font-size: 1.15rem; }}
body.util table {{ font-size: .93rem; font-variant-numeric: tabular-nums; }}
body.util th {{ color: #4A6B66; font-size: .78rem; font-weight: 500; letter-spacing: .01em; border-bottom: 1px solid var(--line); padding: .5rem .75rem .5rem 0; }}
body.util td {{ padding: .8rem .75rem .8rem 0; }}
body.util tbody tr:hover td {{ background: color-mix(in srgb, var(--mist) 30%, transparent); }}
body.util td.num:first-child {{ color: #4A6B66; }}
body.util .card {{ padding: 1.15rem 1.35rem; }}
body.util .card.req:not(.quiet) {{ border-color: color-mix(in srgb, var(--sand) 45%, var(--line)); background: color-mix(in srgb, var(--sand) 6%, #FDFCF9); }}
body.util .req-head b {{ font-family: {DISPLAY_FONT}; font-weight: 500; font-size: 1.15rem; color: var(--lagoon); }}
body.util details.disclose > summary {{ font-family: {DISPLAY_FONT}; font-size: 1.1rem; }}
body.util .notice {{ margin-top: 0; }}
/* Scene life: slow, low-amplitude ambient motion — noticed only on a second
   look. Everything pivots at a physical point (crown, root, waterline, the
   net's fulcrum). Paused off-screen; reduced-motion zeroes it all. */
svg.scene .sway   {{ animation: k-sway 7s ease-in-out infinite alternate; }}
svg.scene .bob    {{ animation: k-bob 6.5s ease-in-out infinite alternate; }}
svg.scene .paddle {{ animation: k-paddle 11s ease-in-out infinite alternate; }}
svg.scene .lever  {{ animation: k-lever 12s ease-in-out infinite alternate; }}
svg.scene .reeds  {{ animation: k-reeds 5.5s ease-in-out infinite alternate; }}
svg.scene .drift  {{ animation: k-drift 14s ease-in-out infinite alternate; }}
svg.scene .glint  {{ animation: k-glint 3.8s ease-in-out infinite alternate; }}
svg.scene .ripple {{ animation: k-ripple 5s ease-in-out infinite alternate; }}
svg.scene .halo   {{ animation: k-halo 9s ease-in-out infinite alternate; }}
svg.scene .glide  {{ animation: k-glide 18s ease-in-out infinite alternate; }}
svg.scene[data-offscreen] * {{ animation-play-state: paused !important; }}
@keyframes k-sway   {{ from {{ transform: rotate(-1.4deg); }} to {{ transform: rotate(1.6deg); }} }}
@keyframes k-bob    {{ from {{ transform: translateY(0) rotate(-.25deg); }} to {{ transform: translateY(2px) rotate(.3deg); }} }}
@keyframes k-paddle {{ from {{ transform: translate(-6px, 0); }} to {{ transform: translate(8px, 1px); }} }}
@keyframes k-lever  {{ from {{ transform: rotate(-.8deg); }} to {{ transform: rotate(1.4deg); }} }}
@keyframes k-reeds  {{ from {{ transform: skewX(-1.6deg); }} to {{ transform: skewX(2deg); }} }}
@keyframes k-drift  {{ from {{ transform: translateX(-10px); }} to {{ transform: translateX(10px); }} }}
@keyframes k-glint  {{ from {{ opacity: .6; }} to {{ opacity: 1; }} }}
@keyframes k-ripple {{ from {{ transform: scaleY(1) translateX(0); }} to {{ transform: scaleY(1.035) translateX(3px); }} }}
@keyframes k-halo   {{ from {{ transform: scale(1); opacity: .85; }} to {{ transform: scale(1.06); opacity: 1; }} }}
@keyframes k-glide  {{ from {{ transform: translate(0, 0); }} to {{ transform: translate(-28px, -6px); }} }}
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ transition: none !important; animation: none !important; }}
  html {{ scroll-behavior: auto; }}
}}
"""


# Progressive-enhancement motion (motion.dev, pinned CDN build). If the CDN or
# the module fails, everything still renders statically — animations only ever
# run FROM hidden states, never TO them. prefers-reduced-motion skips all of it.
_MOTION = """
<script>
// Pause ambient scene motion while a scene is off-screen (no CPU for
// animations nobody can see). Plain script: works even if motion.dev fails.
if ("IntersectionObserver" in window) {
  const io = new IntersectionObserver((entries) => entries.forEach((e) =>
    e.target.toggleAttribute("data-offscreen", !e.isIntersecting)), {rootMargin: "80px"});
  document.querySelectorAll("svg.scene").forEach((s) => io.observe(s));
  // Floating call button: step aside whenever a full call button or the
  // footer (which lists the number) is in view.
  const fab = document.querySelector(".fab-call");
  if (fab) {
    const shown = new Set();
    const fio = new IntersectionObserver((entries) => {
      entries.forEach((e) => e.isIntersecting ? shown.add(e.target) : shown.delete(e.target));
      fab.classList.toggle("is-hidden", shown.size > 0);
    });
    document.querySelectorAll(".call_line, .site-footer").forEach((el) => fio.observe(el));
  }
}
</script>
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
    // Scroll-linked parallax on tagged elements — transform only, damped on mobile.
    document.querySelectorAll("[data-plx]").forEach((el) => {
      const d = parseFloat(el.dataset.plx || "0") * (narrow ? .35 : 1);
      if (d) scroll(animate(el, {y: [d * 55, -d * 55]}),
                    {target: el, offset: ["start end", "end start"]});
    });
    document.querySelectorAll("svg.contours").forEach((svg) => {
      const paths = svg.querySelectorAll("path");
      inView(svg, () => paths.forEach((p, i) => {
        const len = p.getTotalLength();
        p.style.strokeDasharray = len;
        animate(p, {strokeDashoffset: [len, 0]},
                {duration: 1.8, delay: i * .12, easing: "ease-in-out"});
      }), {amount: .4});
    });
    // Scenes: each depth layer drifts at its own speed — near layers move
    // more than the far shore, so scrolling reads as real depth.
    document.querySelectorAll("svg.scene").forEach((scene) => {
      scene.querySelectorAll("g[data-depth]").forEach((g) => {
        const d = parseFloat(g.dataset.depth) * (narrow ? .4 : 1);
        scroll(animate(g, {y: [d * 34, -d * 34]}),
               {target: scene, offset: ["start end", "end start"]});
      });
    });
  }
} catch (e) { /* decoration only — page is complete without it */ }
</script>
"""


def page(title: str, body: str, description: str = "",
         nav: str = "", footer: str = "",
         canonical_url: str = "", head_extra: str = "",
         og_image: str = "", body_class: str = "", motion: bool = True) -> str:
    """Full HTML page shell. Caller must escape dynamic content via esc().

    `nav` renders before <main>, `footer` after it — both are trusted HTML
    built by the caller (e.g. site.py's shared chrome). `canonical_url` emits
    canonical + hreflang (en/x-default) link tags + og: meta; `head_extra` is
    trusted HTML appended to <head> (e.g. JSON-LD). `motion=False` for
    Coastal Utility screens (admin, portal): work surfaces get no entrance
    animation, so state is readable the instant the page loads."""
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
        f'{nav}<main id="main" tabindex="-1">{body}</main>{footer}{_MOTION if motion else ""}</body></html>'
    )


def esc(s) -> str:
    return html.escape(str(s) if s is not None else "")


def status_badge(status: str) -> str:
    cls = {
        "pending": "wait",
        "confirmed": "ok",
        "verified": "ok",
        "converted": "ok",
        "notified": "ok",
        "interested": "ok",
        "active": "ok",
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
    # Machine codes (no_answer, opted_out) read as plain words on screen.
    return f'<span class="badge {cls}">{esc(status.replace("_", " "))}</span>'
