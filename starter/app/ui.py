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
_FONT_LINKS = (
    '<link rel="preconnect" href="https://api.fontshare.com">'
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
  --line: color-mix(in srgb, var(--lagoon) 18%, transparent);
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
a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible {{
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
  background: #FDFCF9; border: 1px solid var(--mist); border-radius: .375rem;
  padding: .55rem .7rem; width: 100%; max-width: 26rem;
  touch-action: manipulation;
}}
input::placeholder {{ color: #9DB3AC; }}
button, .btn {{
  font: inherit; font-weight: 500; font-size: .95rem; cursor: pointer;
  background: var(--teal); color: var(--ivory);
  border: 1px solid var(--teal); border-radius: .375rem;
  padding: .55rem 1.1rem; touch-action: manipulation;
  transition: background-color .15s ease, border-color .15s ease;
}}
button:hover, .btn:hover {{ background: var(--lagoon); border-color: var(--lagoon); color: var(--ivory); }}
button.secondary {{ background: transparent; color: var(--teal); border-color: var(--mist); }}
button.secondary:hover {{ border-color: var(--teal); color: var(--lagoon); background: transparent; }}
button.danger {{ background: transparent; color: #7A2E2E; border-color: #D9AFAF; }}
button.danger:hover {{ background: #F3E3E1; color: #7A2E2E; border-color: #7A2E2E; }}
.card {{
  border: 1px solid var(--line); border-left: 3px solid var(--sand);
  border-radius: .25rem; padding: 1rem 1.25rem; margin: 1rem 0;
  background: #FDFCF9;
}}
.card h3 {{ margin: 0 0 .25rem; font-family: {DISPLAY_FONT}; font-size: 1.2rem; color: var(--lagoon); }}
.muted {{ color: #5E7A74; }}
.small {{ font-size: .85rem; }}
.rule {{ border: 0; border-top: 1px solid var(--line); margin: 2.5rem 0; }}
.ml {{ font-family: 'Noto Sans Malayalam', {BODY_FONT}; }}
.topnav {{
  display: flex; align-items: baseline; gap: 1.15rem; flex-wrap: wrap;
  border-bottom: 1px solid var(--line); padding-bottom: .85rem; margin-bottom: 2.25rem;
}}
.topnav .wordmark {{
  font-family: {DISPLAY_FONT}; font-size: 1.35rem; color: var(--lagoon);
  text-decoration: none; margin-right: auto;
}}
.topnav .wordmark:hover {{ color: var(--teal); }}
.topnav a.navlink {{ color: var(--ink); text-decoration: none; font-size: .95rem; }}
.topnav a.navlink:hover {{ color: var(--teal); text-decoration: underline; }}
.topnav .navcall {{ font-size: .85rem; padding: .35rem .8rem; text-decoration: none; }}
.site-footer {{
  border-top: 1px solid var(--line); margin-top: 3rem; padding-top: 1.1rem;
  font-size: .85rem; color: #5E7A74;
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
}}
"""


def page(title: str, body: str, description: str = "",
         nav: str = "", footer: str = "") -> str:
    """Full HTML page shell. Caller must escape dynamic content via esc().

    `nav` renders before <main>, `footer` after it — both are trusted HTML
    built by the caller (e.g. site.py's shared chrome)."""
    desc = f'<meta name="description" content="{html.escape(description)}">' if description else ""
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f'<meta name="theme-color" content="{IVORY}">{desc}'
        f"<title>{html.escape(title)}</title>{_FONT_LINKS}"
        f"<style>{CSS}</style></head><body>"
        '<a class="skip" href="#main">Skip to content</a>'
        f'{nav}<main id="main">{body}</main>{footer}</body></html>'
    )


def esc(s) -> str:
    return html.escape(str(s) if s is not None else "")


def status_badge(status: str) -> str:
    cls = {
        "pending": "wait",
        "confirmed": "ok",
        "verified": "ok",
        "blocked": "bad",
        "cancelled": "bad",
        "unverified": "wait",
        "pending verification": "wait",
    }.get(status, "wait")
    return f'<span class="badge {cls}">{esc(status)}</span>'


def brand_header(tagline: str = "") -> str:
    tag = f'<p class="muted" style="margin:.25rem 0 0">{esc(tagline)}</p>' if tagline else ""
    return (
        '<header style="margin-bottom:2rem">'
        '<p style="font-family:' + DISPLAY_FONT + ';font-size:1.6rem;color:var(--lagoon);margin:0">'
        'Kaayal <span class="ml" lang="ml">(കായൽ)</span></p>' + tag + "</header><hr class=rule style='margin:0 0 2rem'>"
    )
