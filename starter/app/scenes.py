"""Backwater scenes for the public site — layered, tonal SVG illustrations.

Built procedurally (seeded, so the markup is identical on every request) from
the Kaayal palette only. Realism comes from atmospheric depth — far shores pale
and hazy, near forms dark and detailed — plus rippled reflections and water
shimmer that thins toward the viewer, not from gradients or photo effects.

Each scene is split into depth layers (`<g data-depth>`); the motion script
moves the layers at different speeds on scroll, so the parallax is real depth.
All ids are prefixed per scene so three scenes can share one document.
"""

import math
import random

LAGOON = "#123F3C"
TEAL = "#267A73"
MIST = "#D9E6DE"
SAND = "#C68E55"
IVORY = "#F7F5EE"
WOOD = "#6B4A26"      # derived: deep sand, used for hulls
WOOD_LIGHT = "#8A5F33"
HAZE = "#9DB3AC"      # derived: far-shore tone
MID = "#4A6B66"       # derived: mid-shore tone


def _f(v: float) -> str:
    # Whole units: the viewBox is ~1:1 with rendered pixels, so decimals only
    # add bytes (they tripled the markup size).
    return str(round(v))


# --- palms -------------------------------------------------------------------

def _w(v: float) -> str:
    """Stroke widths keep one decimal — rounding 0.6 to 1 (or 0.4 to 0) is visible."""
    return f"{v:.1f}"


def _palm(rng: random.Random, x: float, base: float, h: float, lean: float,
          color: str, detail: float = 1.0) -> str:
    """A coconut palm as it actually grows on a Kerala canal bank.

    - Trunk: slender, flared at the base, bending in a gentle S toward the
      light, with growth rings on near palms.
    - Fronds: arch up out of the crown, then fall under their own weight
      (a gravity curve, not a fan). Leaflets hang below the midrib in
      irregular lengths and sweep toward the frond tip.
    - Depth inside one crown: back fronds are drawn a shade lighter, front
      fronds in full colour, so the crown has volume instead of a flat star.
    - Near palms also get a dead brown frond hanging down and a coconut
      cluster under the crown.
    """
    # Trunk spine: a cubic with an S-bend, top displaced by `lean`.
    tx, ty = x + lean * h, base - h
    c1x, c1y = x - lean * h * .15, base - h * .35
    c2x, c2y = x + lean * h * 1.15, base - h * .72

    def spine(t):
        u = 1 - t
        px = u ** 3 * x + 3 * u * u * t * c1x + 3 * u * t * t * c2x + t ** 3 * tx
        py = u ** 3 * base + 3 * u * u * t * c1y + 3 * u * t * t * c2y + t ** 3 * ty
        return px, py

    w_top = max(.7, h * .012)
    w_mid = max(1, h * .017)
    left, right = [], []
    for k in range(13):
        t = k / 12
        px, py = spine(t)
        flare = 1 + 1.1 * max(0, .12 - t) / .12           # bulb at the base
        hw = (w_mid + (w_top - w_mid) * t) * flare
        left.append((px - hw, py))
        right.append((px + hw, py))
    trunk = ("M" + " L".join(f"{_f(px)},{_f(py)}" for px, py in left)
             + " L" + " L".join(f"{_f(px)},{_f(py)}" for px, py in reversed(right)) + " Z")
    rings = ""
    if detail >= .9:
        rr = []
        for k in range(1, 22):
            t = k / 22 + rng.uniform(-.01, .01)
            px, py = spine(t)
            hw = w_mid + (w_top - w_mid) * t
            rr.append(f"M{_f(px - hw)},{_f(py)}q{_f(hw)},{_f(hw * .5)} {_f(hw * 2)},0")
        rings = (f'<path d="{"".join(rr)}" fill="none" stroke="{IVORY}" '
                 f'stroke-width="{_w(max(.5, h * .003))}" opacity=".25"/>')

    teeth = 16 if detail >= .9 else 10 if detail >= .5 else 5
    back, front = [], []
    n = rng.randint(11, 15) if detail >= .5 else rng.randint(7, 9)
    for i in range(n):
        # angle above horizontal: young fronds stand up, old ones sag below
        rise = rng.uniform(-.35, 1.2)
        side = 1 if i % 2 == 0 else -1
        side *= rng.uniform(.35, 1)                      # foreshortening
        length = h * rng.uniform(.3, .42) * (.7 if rise > .95 else 1)
        gravity = rng.uniform(.35, .7)
        pts = []
        for k in range(teeth + 1):
            t = k / teeth
            px = tx + side * length * t * math.cos(rise * .75)
            py = ty - length * t * math.sin(rise) + gravity * length * t * t * (1 + max(0, -rise))
            pts.append((px, py))
        under = []
        for k in range(teeth + 1):
            t = k / teeth
            px, py = pts[k]
            if t < .1:
                under.append((px, py + h * .004))
                continue
            hang = length * .12 * math.sin(math.pi * min(1, t * 1.05)) ** .7
            hang *= rng.uniform(.6, 1.25)                # irregular leaflets
            under.append((px + side * hang * .55, py + hang))
        d = [f"M{_f(pts[0][0])},{_f(pts[0][1])}"]
        d += [f"L{_f(px)},{_f(py)}" for px, py in pts[1:]]
        for k in range(teeth, 0, -1):
            ux, uy = under[k]
            mx_, my_ = pts[k - 1]
            notch = rng.uniform(.25, .5)
            d.append(f"L{_f(ux)},{_f(uy)}L{_f(mx_ + (ux - mx_) * notch)},{_f(my_ + (uy - my_) * notch)}")
        d.append("Z")
        (back if rise > .45 else front).append("".join(d))
    extras = ""
    if detail >= .5:
        # one dead frond hanging straight down, browned
        dl = h * rng.uniform(.2, .28)
        dx = rng.choice((-1, 1)) * h * .02
        extras += (f'<path d="M{_f(tx)},{_f(ty + 2)} q{_f(dx * 2)},{_f(dl * .5)} {_f(dx * 3)},{_f(dl)} '
                   f'l{_f(-dx * 1.5 - h * .012)},{_f(-dl * .55)} Z" fill="{WOOD_LIGHT}" opacity=".85"/>')
    if detail >= .9:
        nuts = "".join(f'<circle cx="{_f(tx + rng.uniform(-1, 1) * h * .022)}" cy="{_f(ty + h * rng.uniform(.012, .04))}" '
                       f'r="{_w(h * .013)}"/>' for _ in range(rng.randint(4, 6)))
        extras += f'<g fill="{WOOD}">{nuts}</g>'
    sw = _w(max(.4, h * .004))
    crown = (f'<path d="{"".join(back)}" fill="{color}" opacity=".72" stroke="{color}" stroke-width="{sw}" stroke-linejoin="round"/>'
             f'{extras}'
             f'<path d="{"".join(front)}" fill="{color}" stroke="{color}" stroke-width="{sw}" stroke-linejoin="round"/>')
    if detail >= .5:
        # Each crown sways on its own clock: pivot at the crown, varied
        # period and phase so the bank never moves in lockstep.
        crown = (f'<g class="sway" style="transform-origin:{_f(tx)}px {_f(ty)}px;'
                 f'animation-duration:{rng.uniform(5.5, 9):.1f}s;animation-delay:-{rng.uniform(0, 9):.1f}s">{crown}</g>')
    return f'<path d="{trunk}" fill="{color}"/>{rings}{crown}'


def _shore(rng: random.Random, x0: float, x1: float, y: float, height: float,
           color: str, palms: int, palm_h: tuple[float, float], detail: float,
           opacity: float) -> str:
    """A low bank of vegetation with palms rising out of it."""
    pts = [f"M{_f(x0)},{_f(y)}"]
    x = x0
    while x < x1:
        step = rng.uniform(14, 34)
        x = min(x1, x + step)
        pts.append(f"Q{_f(x - step / 2)},{_f(y - height * rng.uniform(.6, 1.4))} {_f(x)},{_f(y - height * rng.uniform(.2, .6))}")
    pts.append(f"L{_f(x1)},{_f(y)} Z")
    out = [f'<g opacity="{opacity}"><path d="{"".join(pts)}" fill="{color}"/>']
    for _ in range(palms):
        px = rng.uniform(x0 + 10, x1 - 10)
        out.append(_palm(rng, px, y - height * .3, rng.uniform(*palm_h),
                         rng.uniform(-.28, .28), color, detail))
    out.append("</g>")
    return "".join(out)


def _shimmer(rng: random.Random, x0: float, x1: float, y0: float, y1: float,
             rows: int, color: str, base_opacity: float, glow_x: float | None = None) -> str:
    """Horizontal water glints, dense at the horizon and sparse up close."""
    segs = []
    for i in range(rows):
        t = (i / rows) ** 1.7                   # perspective spacing
        y = y0 + (y1 - y0) * t
        for _ in range(rng.randint(2, 5)):
            cx = rng.uniform(x0, x1)
            ln = rng.uniform(12, 60) * (1 + t * 2.2)
            if glow_x is not None and abs(cx - glow_x) < 90:
                continue
            segs.append(f"M{_f(cx - ln / 2)},{_f(y)}h{_f(ln)}")
    path = f'<path d="{"".join(segs)}" stroke="{color}" stroke-width="1.1" stroke-linecap="round" opacity="{base_opacity}"/>'
    glow = ""
    if glow_x is not None:  # the sun's broken column on the water
        g = []
        for i in range(rows):
            t = (i / rows) ** 1.5
            y = y0 + (y1 - y0) * t
            ln = rng.uniform(10, 34) * (1 + t * 1.6)
            g.append(f"M{_f(glow_x - ln / 2 + rng.uniform(-14, 14) * (1 + t))},{_f(y)}h{_f(ln)}")
        glow = f'<path d="{"".join(g)}" stroke="{SAND}" stroke-width="1.6" stroke-linecap="round" opacity=".55"/>'
    return f'<g class="drift">{path}</g>' + (f'<g class="glint">{glow}</g>' if glow else "")


def _sun(cx: float, cy: float, r: float) -> str:
    return (f'<g class="halo" style="transform-origin:{cx}px {cy}px">'
            f'<circle cx="{cx}" cy="{cy}" r="{r * 2.6}" fill="{SAND}" opacity=".06"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r * 1.7}" fill="{SAND}" opacity=".1"/></g>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{SAND}" opacity=".42"/>')


def _birds(points: list[tuple[float, float, float]]) -> str:
    d = "".join(f"M{_f(x - s)},{_f(y)} q{_f(s / 2)},{_f(-s * .55)} {_f(s)},0 q{_f(s / 2)},{_f(-s * .55)} {_f(s)},0"
                for x, y, s in points)
    return f'<g class="glide"><path d="{d}" fill="none" stroke="{LAGOON}" stroke-width="1.3" stroke-linecap="round" opacity=".55"/></g>'


def _reflection(pid: str, href: str, axis_y: float, height: float, opacity: float) -> str:
    """Mirror `href` about the waterline, broken up by a ripple filter."""
    return (f'<g clip-path="url(#{pid}-below)" filter="url(#{pid}-ripple)" opacity="{opacity}">'
            f'<g class="ripple" style="transform-origin:600px {_f(axis_y)}px">'
            f'<use href="#{href}" transform="translate(0 {_f(axis_y * 2)}) scale(1 -1)"/></g></g>')


def _defs(pid: str, water_y: float, width: float, height: float) -> str:
    return (f'<defs><clipPath id="{pid}-below"><rect x="0" y="{_f(water_y)}" width="{width}" height="{height}"/></clipPath>'
            f'<filter id="{pid}-ripple" x="-5%" y="-5%" width="110%" height="110%">'
            f'<feTurbulence type="fractalNoise" baseFrequency=".006 .09" numOctaves="2" seed="7" result="n"/>'
            f'<feDisplacementMap in="SourceGraphic" in2="n" scale="14" xChannelSelector="R" yChannelSelector="G"/>'
            f'</filter></defs>')


def _open(cls_extra: str, vb_w: int, vb_h: int, label: str) -> str:
    # Decorative: the page text carries the meaning, so hide from assistive tech.
    return (f'<svg class="scene{cls_extra}" aria-hidden="true" focusable="false" '
            f'viewBox="0 0 {vb_w} {vb_h}" width="100%" preserveAspectRatio="xMidYMax slice" '
            f'data-scene="{label}">')


# --- 1. Kettuvallam on Vembanad (hero) -----------------------------------------

def _houseboat(pid: str) -> str:
    """A kettuvallam: upturned wooden hull, arched woven-thatch canopy with a
    raised rear section, open bow deck. Drawn around a waterline at y=338."""
    ribs = "".join(f"M{x},226 L{x},320" for x in range(366, 772, 11))
    weave = "".join(f"M352,{y} Q563,{y - 6} 776,{y}" for y in range(244, 320, 9))
    windows = "".join(
        f'<rect x="{x}" y="286" width="34" height="24" rx="2" fill="{LAGOON}" opacity=".88"/>'
        f'<rect x="{x}" y="286" width="34" height="5" fill="{WOOD_LIGHT}" opacity=".7"/>'
        for x in range(392, 742, 46))
    rail = "".join(f"M{x},300 L{x},318" for x in range(316, 360, 7))
    return f"""
<g id="{pid}-hb" class="bob" style="transform-origin:563px 338px">
  <path d="M286,276 C300,298 316,313 342,318 L792,318 C814,313 830,302 842,290
           C838,312 820,333 784,339 L362,339 C328,337 300,312 286,276 Z" fill="{WOOD}"/>
  <path d="M300,300 C340,326 380,330 420,330 L760,330 C800,328 822,318 836,302" fill="none"
        stroke="{WOOD_LIGHT}" stroke-width="1.4" opacity=".75"/>
  <path d="M318,322 L800,322 M330,334 L790,334" stroke="{LAGOON}" stroke-width="1" opacity=".35"/>
  <path d="M352,318 C352,262 380,232 444,226 L690,226 C752,232 778,262 778,318 Z" fill="{SAND}"/>
  <clipPath id="{pid}-roof"><path d="M352,318 C352,262 380,232 444,226 L690,226 C752,232 778,262 778,318 Z"/></clipPath>
  <g clip-path="url(#{pid}-roof)">
    <path d="{ribs}" stroke="{WOOD_LIGHT}" stroke-width="1" opacity=".35"/>
    <path d="{weave}" fill="none" stroke="{WOOD_LIGHT}" stroke-width=".7" opacity=".22"/>
    <rect x="340" y="226" width="450" height="14" fill="{IVORY}" opacity=".18"/>
    <rect x="340" y="296" width="450" height="24" fill="{WOOD}" opacity=".35"/>
  </g>
  {windows}
  <path d="M600,226 C602,206 618,196 640,194 L712,194 C732,196 744,208 746,226 Z" fill="{SAND}"/>
  <path d="M612,226 L612,200 M634,226 L634,195 M656,226 L656,194 M678,226 L678,194 M700,226 L700,195 M722,226 L722,199"
        stroke="{WOOD_LIGHT}" stroke-width="1.1" opacity=".55"/>
  <path d="M600,226 L746,226" stroke="{WOOD}" stroke-width="2"/>
  <path d="{rail}" stroke="{WOOD}" stroke-width="1.6"/>
  <path d="M312,300 L356,300" stroke="{WOOD}" stroke-width="2"/>
  <path d="M286,276 C282,268 284,262 290,258" fill="none" stroke="{WOOD}" stroke-width="3" stroke-linecap="round"/>
  <path d="M842,290 C848,282 848,276 844,270" fill="none" stroke="{WOOD}" stroke-width="2.6" stroke-linecap="round"/>
  <path d="M848,300 L878,262" stroke="{WOOD}" stroke-width="2.2" stroke-linecap="round"/>
</g>"""


def scene_houseboat() -> str:
    rng = random.Random(11)
    pid, W, H, water = "sh", 1200, 420, 262
    far = _shore(rng, -20, 1220, water, 10, HAZE, 34, (26, 46), .45, .55)
    mid_l = _shore(rng, -20, 300, water + 6, 18, MID, 9, (60, 104), .75, .85)
    mid_r = _shore(rng, 980, 1220, water + 4, 14, MID, 6, (54, 92), .75, .8)
    near = []
    for x in (1040, 1090, 1150):
        near.append(_palm(rng, x, 430, rng.uniform(250, 320), rng.uniform(-.32, -.16), LAGOON, 1))
    reeds = "".join(
        f"M{_f(x)},420 Q{_f(x + rng.uniform(-6, 6))},{_f(400 - rng.uniform(10, 30))} {_f(x + rng.uniform(-14, 14))},{_f(372 - rng.uniform(0, 34))}"
        for x in [rng.uniform(0, 210) for _ in range(46)])
    return (
        _open("", W, H, "houseboat") + _defs(pid, 338, W, H)
        + f'<g data-depth="0.1">{_sun(905, 118, 44)}{_birds([(820, 96, 9), (848, 112, 7), (972, 82, 8)])}</g>'
        + f'<g data-depth="0.2">{far}</g>'
        + f'<g data-depth="0.35">{mid_l}{mid_r}'
        + f'<rect x="0" y="{water}" width="{W}" height="2" fill="{IVORY}" opacity=".7"/></g>'
        + f'<g data-depth="0.5">{_shimmer(rng, 0, W, water + 6, H, 26, TEAL, .32, glow_x=905)}</g>'
        + f'<g data-depth="0.7">{_houseboat(pid)}{_reflection(pid, pid + "-hb", 339, 120, .28)}'
        + f'<path d="M260,343 Q560,352 880,343" fill="none" stroke="{IVORY}" stroke-width="1.6" opacity=".7"/></g>'
        + f'<g data-depth="1">{"".join(near)}<g class="reeds" style="transform-origin:100px 420px"><path d="{reeds}" fill="none" stroke="{LAGOON}" stroke-width="1.6" stroke-linecap="round" opacity=".85"/></g></g>'
        + "</svg>"
    )


# --- 2. Chinese fishing net at evening ---------------------------------------

def _net(pid: str, s: float = 1.0, ox: float = 0, oy: float = 0) -> str:
    """Cheena vala: shore platform, A-frame pivot, long boom with four curved
    spars holding a mesh bowl over the water, counterweight stones behind."""
    def p(x, y):
        return f"{_f(ox + x * s)},{_f(oy + y * s)}"
    corners = [(612, 236), (690, 254), (858, 254), (932, 236)]
    tip = (772, 96)
    spars = "".join(f"M{p(*tip)} Q{p((tip[0] + cx) / 2 + (cx - tip[0]) * .25, (tip[1] + cy) / 2 - 22)} {p(cx, cy)}"
                    for cx, cy in corners)
    # mesh: rows between rim (straight-ish) and bowl (sagging), columns across
    mesh = []
    for r in range(0, 8):
        t = r / 7
        y_l, y_r = 236 + 18 * t, 236 + 18 * t
        sag = 44 * math.sin(math.pi * (0.25 + t * .5))
        mesh.append(f"M{p(612 + 78 * t, y_l)} Q{p(772, 262 + sag)} {p(932 - 74 * t, y_r)}")
    for c in range(0, 13):
        u = c / 12
        x0 = 612 + (932 - 612) * u
        mesh.append(f"M{p(x0, 236 + 6 * math.sin(math.pi * u))} Q{p(x0 + (772 - x0) * .2, 286)} {p(690 + (858 - 690) * u, 254)}")
    stones = "".join(f'<circle cx="{_f(ox + x * s)}" cy="{_f(oy + y * s)}" r="{_f(r * s)}" fill="{LAGOON}"/>'
                     f'<path d="M{p(x, 150 + (x - 150) * .05)} L{p(x, y - r)}" stroke="{LAGOON}" stroke-width="{_w(1 * s)}"/>'
                     for x, y, r in [(150, 214, 7), (166, 226, 6), (182, 210, 6.5), (198, 222, 5.5)])
    people = ""
    if s >= 1:
        people = (f'<g fill="{LAGOON}"><circle cx="{p(236, 214).split(",")[0]}" cy="{p(236, 214).split(",")[1]}" r="{_f(5.5 * s)}"/>'
                  f'<path d="M{p(232, 220)} L{p(240, 220)} L{p(244, 246)} L{p(230, 246)} Z"/>'
                  f'<circle cx="{p(268, 210).split(",")[0]}" cy="{p(268, 210).split(",")[1]}" r="{_f(5.5 * s)}"/>'
                  f'<path d="M{p(264, 216)} L{p(272, 216)} L{p(278, 246)} L{p(262, 246)} Z"/></g>'
                  f'<path d="M{p(244, 226)} L{p(170, 156)} M{p(276, 222)} L{p(196, 152)}" stroke="{LAGOON}" stroke-width="{_w(1.2 * s)}"/>')
    sw = lambda w: _w(w * s)  # noqa: E731
    return f"""
<g id="{pid}-net{int(s * 10)}" fill="none" stroke="{LAGOON}" stroke-linecap="round">
  <path d="M{p(120, 248)} L{p(330, 248)} M{p(128, 248)} L{p(128, 272)} M{p(200, 248)} L{p(200, 274)} M{p(300, 248)} L{p(300, 272)}" stroke-width="{sw(3)}"/>
  <path d="M{p(276, 248)} L{p(318, 128)} L{p(352, 248)}" stroke-width="{sw(3.4)}"/>
  <g class="lever" style="transform-origin:{_f(ox + 318 * s)}px {_f(oy + 128 * s)}px;animation-delay:-{_f(s * 7)}s">
  <path d="M{p(150, 150)} L{p(318, 128)} L{p(772, 96)}" stroke-width="{sw(3.6)}"/>
  <path d="M{p(318, 128)} L{p(330, 70)} M{p(330, 70)} Q{p(560, 64)} {p(772, 96)} M{p(330, 70)} Q{p(230, 96)} {p(150, 150)}" stroke-width="{sw(1.1)}" opacity=".8"/>
  <path d="{spars}" stroke-width="{sw(2)}"/>
  <path d="{''.join(mesh)}" stroke-width="{sw(.7)}" opacity=".7"/>
  {stones}
  </g>{people}
</g>"""


def scene_net() -> str:
    rng = random.Random(23)
    pid, W, H, water = "sn", 1200, 380, 250
    far = _shore(rng, -20, 1220, water, 9, HAZE, 30, (22, 40), .45, .5)
    distant_net = _net(pid, .42, 760, 120)
    return (
        _open("", W, H, "fishing-net") + _defs(pid, 252, W, H)
        + f'<g data-depth="0.1">{_sun(1010, 176, 54)}{_birds([(940, 120, 8), (962, 134, 6)])}</g>'
        + f'<g data-depth="0.2">{far}<g opacity=".45">{distant_net}</g></g>'
        + f'<g data-depth="0.45">{_shimmer(rng, 0, W, water + 4, H, 22, TEAL, .3, glow_x=1010)}</g>'
        + f'<g data-depth="0.65"><path d="M60,250 L360,250 L372,262 L50,262 Z" fill="{MID}" opacity=".9"/>'
        + _shore(rng, 40, 140, 252, 14, LAGOON, 2, (110, 150), 1, 1)
        + f'{_net(pid)}{_reflection(pid, pid + "-net10", 252, 130, .25)}</g>'
        + "</svg>"
    )


# --- 3. Punted canoe past the paddy bund -------------------------------------

def _canoe(pid: str) -> str:
    return f"""
<g id="{pid}-cn" class="paddle" style="transform-origin:525px 330px">
  <path d="M330,300 C360,316 420,322 520,322 C620,322 690,316 720,296 C712,312 690,326 640,330
           L410,330 C370,328 344,318 330,300 Z" fill="{WOOD}"/>
  <path d="M344,304 C400,316 640,318 708,300" fill="none" stroke="{WOOD_LIGHT}" stroke-width="1.3" opacity=".8"/>
  <path d="M330,300 C324,294 324,288 328,284 M720,296 C726,290 726,284 722,280" fill="none" stroke="{WOOD}" stroke-width="2.4" stroke-linecap="round"/>
  <g fill="{LAGOON}">
    <circle cx="452" cy="262" r="8"/>
    <path d="M440,272 C440,268 464,268 464,272 L470,306 L434,306 Z"/>
    <path d="M430,300 L478,300 L476,312 L432,312 Z" opacity=".85"/>
    <path d="M426,258 C434,246 470,246 478,258 Z" fill="{SAND}"/>
    <circle cx="612" cy="196" r="8.5"/>
    <path d="M603,206 L621,206 L626,262 L598,262 Z"/>
    <path d="M600,262 L594,306 L604,306 L612,268 L618,306 L628,306 L624,262 Z"/>
    <path d="M598,192 C604,184 620,184 626,192 Z" fill="{IVORY}" opacity=".9"/>
  </g>
  <path d="M664,140 L568,366" stroke="{LAGOON}" stroke-width="3" stroke-linecap="round"/>
  <path d="M606,222 L640,202 M618,226 L650,214" stroke="{LAGOON}" stroke-width="5" stroke-linecap="round"/>
</g>"""


def scene_canoe() -> str:
    rng = random.Random(37)
    pid, W, H, water = "sc", 1200, 380, 232
    far = _shore(rng, -20, 1220, water - 2, 8, HAZE, 26, (20, 36), .45, .5)
    bund = (f'<path d="M-10,236 C200,226 420,230 640,224 S1000,222 1210,228 L1210,246 L-10,246 Z" fill="{MID}" opacity=".85"/>'
            + "".join(_palm(rng, x, 232, rng.uniform(70, 120), rng.uniform(-.25, .25), MID, .7)
                      for x in [rng.uniform(30, 1170) for _ in range(11)]))
    paddy = "".join(
        f"M{_f(x)},{_f(y)} l{_f(rng.uniform(-3, 3))},{_f(-rng.uniform(5, 11))}"
        for x, y in [(rng.uniform(0, W), rng.uniform(238, 246)) for _ in range(260)])
    reeds_r = "".join(
        f"M{_f(x)},380 Q{_f(x + rng.uniform(-8, 8))},{_f(350 - rng.uniform(0, 30))} {_f(x + rng.uniform(-22, 22))},{_f(300 - rng.uniform(0, 60))}"
        for x in [rng.uniform(930, 1200) for _ in range(60)])
    lilies = "".join(
        f'<ellipse cx="{_f(x)}" cy="{_f(y)}" rx="{_f(r)}" ry="{_f(r * .28)}" fill="{LAGOON}" opacity=".7"/>'
        for x, y, r in [(rng.uniform(60, 300), rng.uniform(330, 370), rng.uniform(7, 15)) for _ in range(9)])
    return (
        _open("", W, H, "canoe") + _defs(pid, 330, W, H)
        + f'<g data-depth="0.15">{far}</g>'
        + f'<g data-depth="0.3">{bund}<path d="{paddy}" stroke="{TEAL}" stroke-width="1" opacity=".6"/></g>'
        + f'<g data-depth="0.5">{_shimmer(rng, 0, W, 250, H, 20, TEAL, .3)}</g>'
        + f'<g data-depth="0.7">{_canoe(pid)}{_reflection(pid, pid + "-cn", 330, 120, .25)}</g>'
        + f'<g data-depth="1">{lilies}<g class="reeds" style="transform-origin:1065px 380px"><path d="{reeds_r}" fill="none" stroke="{LAGOON}" stroke-width="1.7" stroke-linecap="round" opacity=".9"/></g></g>'
        + "</svg>"
    )


# Rendered once at import — deterministic, so safe to cache as module constants.
HOUSEBOAT = scene_houseboat()
NET = scene_net()
CANOE = scene_canoe()
