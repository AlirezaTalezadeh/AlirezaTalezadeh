#!/usr/bin/env python3
"""Builds the animated SVGs in ../assets/ for the GitHub profile README.

Edit the CONTENT section, then run:  python3 tools/build.py
Every animation is plain CSS inside the SVG (GitHub strips scripts from
SVG images but keeps <style>), so the files animate on github.com as-is.
"""
import json
import math
import os
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets")

# ---------------------------------------------------------------- CONTENT
FIRST, LAST = "Alireza", "Talezadeh"
ROLES = [
    "WordPress & WooCommerce engineer",
    "building account4all.ir",
    "Persian / RTL interfaces",
    "MQL5 trading systems",
]
TERMINAL_TITLE = "alireza@account4all: ~"
# ("cmd", text) is typed after the prompt; ("out", [(text, colour-token), ...]) fades in.
TERMINAL = [
    ("cmd", "whoami"),
    ("out", [("alireza talezadeh", "text"), (" - building ", "muted"), ("account4all.ir", "sun")]),
    ("cmd", "cat focus.txt"),
    ("out", [("woocommerce themes & plugins", "text"), ("  ·  ", "muted"), ("persian / rtl ux", "text"),
             ("  ·  ", "muted"), ("checkout & order flows", "text")]),
    ("out", [("sms + email automation", "text"), ("  ·  ", "muted"), ("seo & structured data", "text"),
             ("  ·  ", "muted"), ("web performance", "text")]),
    ("cmd", "ls side-quests/"),
    ("out", [("mql5-expert-advisors/", "teal"), ("   ", "muted"), ("crypto-research/", "teal"),
             ("   ", "muted"), ("3d-interiors/", "teal")]),
    ("cmd", "echo $STATUS"),
    ("out", [("● ", "teal"), ("shipping, one verified release at a time", "text")]),
]
STACK = [  # (label, simple-icons key or a custom key below)
    ("WordPress", "wordpress"), ("WooCommerce", "woocommerce"), ("PHP", "php"),
    ("JavaScript", "javascript"), ("MySQL", "mysql"), ("Python", "python"), ("MQL5", "_candles"),
    ("Docker", "docker"), ("Linux", "linux"), ("Git", "git"), ("Cloudflare", "cloudflare"),
    ("Blender", "blender"), ("SketchUp", "sketchup"), ("Persian RTL", "_farsi"),
]
FOOTER_EN = "thanks for stopping by"
FOOTER_FA = "ممنون که سر زدی"

# ---------------------------------------------------------------- TOKENS
C = {
    "ink": "#0A0F1F", "ink2": "#111833", "line": "#1E2A4A",
    "text": "#E8ECF5", "muted": "#8A94B0",
    "teal": "#30C5B5",   # Persian turquoise
    "sun": "#F5B841",    # saffron
    "rose": "#F0717B",
}
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
MONO = "ui-monospace, 'SF Mono', SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
EXPO = "cubic-bezier(0.16, 1, 0.3, 1)"


def pct(t, total):
    return f"{max(0.0, min(100.0, t / total * 100)):.3f}%"


def svg(w, h, title, body, css):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(title)}">\n<title>{escape(title)}</title>\n'
            f'<style>\n{css}\n</style>\n{body}\n</svg>\n')


def write(name, content):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"{name:14} {len(content.encode()) / 1024:6.1f} KB")


def khatam(cx, cy, r, rot=0.0):
    """Eight-point star from two overlapping squares (khatam, Persian girih)."""
    inner = r * math.cos(math.pi / 4) / math.cos(math.pi / 8)
    pts = []
    for k in range(16):
        a = math.radians(rot) + k * math.pi / 8 - math.pi / 2
        rr = r if k % 2 == 0 else inner
        pts.append(f"{cx + rr * math.cos(a):.2f},{cy + rr * math.sin(a):.2f}")
    return "M" + " L".join(pts) + " Z"


def star_8_3(cx, cy, r, rot=0.0):
    """{8/3} star polygon - the long-armed girih star."""
    pts = []
    for k in range(8):
        a = math.radians(rot) + (k * 3 % 8) * math.pi / 4 - math.pi / 2
        pts.append(f"{cx + r * math.cos(a):.2f},{cy + r * math.sin(a):.2f}")
    return "M" + " L".join(pts) + " Z"


def typed_chars(prefix, phrases, x0, y, cw, size, colour, t0, type_ms, hold_ms, del_ms, gap_ms):
    """Per-character typing/backspacing that loops forever. Returns (body, css, caret events, cycle)."""
    events, t = [], t0
    for p, s in enumerate(phrases):
        n = len(s)
        start = t
        on = [start + i * type_ms for i in range(n)]
        end_type = start + n * type_ms
        off = [end_type + hold_ms + (n - 1 - i) * del_ms for i in range(n)]
        events.append((p, s, on, off))
        t = end_type + hold_ms + n * del_ms + gap_ms
    total = t
    body, css, caret = [], [], []
    for p, s, on, off in events:
        for i, ch in enumerate(s):
            if ch == " ":
                continue
            name = f"{prefix}{p}_{i}"
            css.append(f"@keyframes {name}{{0%,{pct(on[i] - 1, total)}{{opacity:0}}"
                       f"{pct(on[i], total)},{pct(off[i], total)}{{opacity:1}}"
                       f"{pct(off[i] + 1, total)},100%{{opacity:0}}}}"
                       f".{name}{{animation:{name} {total}ms linear infinite}}")
            body.append(f'<text class="{prefix} {prefix}p{p} {name}" x="{x0 + i * cw:.1f}" y="{y}">{escape(ch)}</text>')
        for i in range(len(s)):
            caret.append((on[i], x0 + (i + 1) * cw))
            caret.append((off[i], x0 + i * cw))
    caret.sort()
    return "\n".join(body), "\n".join(css), caret, total


def caret_keyframes(name, events, total, x0, y_of=None):
    stops = [f"0%{{transform:translate({x0:.1f}px,{(y_of or 0):.1f}px)}}"]
    for t, x, *rest in events:
        y = rest[0] if rest else (y_of or 0)
        stops.append(f"{pct(t, total)}{{transform:translate({x:.1f}px,{y:.1f}px)}}")
    return (f"@keyframes {name}{{{''.join(stops)}}}"
            f".{name}{{animation:{name} {total}ms steps(1,end) infinite}}")


# ---------------------------------------------------------------- HERO
def hero():
    W, H = 1200, 420
    mx, my = 935, 210  # medallion centre
    css = [f"""
.bg{{fill:{C['ink']}}}
.drift{{animation:drift 30s linear infinite}}
@keyframes drift{{to{{transform:translate(80px,80px)}}}}
.glow{{animation:glow 7s ease-in-out infinite alternate}}
.glow2{{animation:glow 9s ease-in-out -3s infinite alternate}}
@keyframes glow{{from{{opacity:.55}}to{{opacity:1}}}}
.eyebrow{{font:600 15px {MONO};letter-spacing:.22em;fill:{C['teal']};animation:fade .8s ease-out .1s both}}
.name{{font:800 78px {SANS};letter-spacing:-.025em}}
.n1{{fill:{C['text']};animation:rise .9s {EXPO} .25s both}}
.n2{{fill:url(#ink);animation:rise .9s {EXPO} .35s both}}
@keyframes rise{{from{{transform:translateY(96px)}}to{{transform:none}}}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
.rule{{stroke:{C['sun']};stroke-width:4;stroke-linecap:round;fill:none;stroke-dasharray:1;stroke-dashoffset:1;
      animation:draw 1s {EXPO} .9s forwards}}
.prompt{{font:600 22px {MONO};fill:{C['teal']};animation:fade .6s ease-out 1.1s both}}
.ty{{font:500 22px {MONO};fill:{C['text']};opacity:0}}
.caret rect{{fill:{C['sun']};animation:blink 1s steps(1,end) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
.spin{{transform-origin:{mx}px {my}px;animation:spin 90s linear infinite}}
.spinr{{transform-origin:{mx}px {my}px;animation:spin 40s linear infinite reverse}}
.orbit{{transform-origin:{mx}px {my}px;animation:spin 11s linear infinite}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.d{{fill:none;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1}}
.d1{{stroke:{C['teal']};stroke-width:1.6;animation:draw 2.4s {EXPO} .3s forwards}}
.d2{{stroke:{C['sun']};stroke-width:2.2;animation:draw 2.2s {EXPO} .8s forwards}}
.d3{{stroke:{C['teal']};stroke-width:2;animation:draw 2s {EXPO} 1.2s forwards}}
.d4{{stroke:{C['line']};stroke-width:1.2;animation:draw 3s ease-out .1s forwards}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
.core{{fill:{C['sun']};transform-origin:{mx}px {my}px;animation:pop .7s {EXPO} 1.8s both,breathe 3.2s ease-in-out 2.5s infinite alternate}}
@keyframes pop{{from{{transform:scale(0)}}}}
@keyframes breathe{{to{{transform:scale(1.35)}}}}
.dot{{fill:{C['sun']};animation:fade .6s ease-out 2s both}}
.fill8{{fill:{C['teal']};fill-opacity:.07;animation:fade 2s ease-out 1.6s both}}
"""]
    # background girih tile
    tile = (f'<pattern id="tile" width="80" height="80" patternUnits="userSpaceOnUse">'
            f'<path d="{khatam(40, 40, 22)}" fill="none" stroke="{C["teal"]}" stroke-width="1" opacity=".09"/>'
            f'<circle cx="0" cy="0" r="2" fill="{C["muted"]}" opacity=".18"/></pattern>')
    defs = f"""<defs>
<clipPath id="card"><rect width="{W}" height="{H}" rx="22"/></clipPath>
<clipPath id="m1"><rect x="40" y="120" width="640" height="94"/></clipPath>
<clipPath id="m2"><rect x="40" y="204" width="640" height="94"/></clipPath>
<linearGradient id="ink" x1="0" x2="1"><stop offset="0" stop-color="{C['teal']}"/><stop offset="1" stop-color="{C['sun']}"/></linearGradient>
<radialGradient id="g1"><stop offset="0" stop-color="{C['teal']}" stop-opacity=".32"/><stop offset="1" stop-color="{C['teal']}" stop-opacity="0"/></radialGradient>
<radialGradient id="g2"><stop offset="0" stop-color="{C['sun']}" stop-opacity=".16"/><stop offset="1" stop-color="{C['sun']}" stop-opacity="0"/></radialGradient>
<linearGradient id="fadeL" x1="0" x2="1"><stop offset="0" stop-color="{C['ink']}"/><stop offset=".55" stop-color="{C['ink']}" stop-opacity=".2"/><stop offset="1" stop-color="{C['ink']}" stop-opacity="0"/></linearGradient>
{tile}
</defs>"""
    ring_ticks = "".join(
        f'<line x1="{mx + 176 * math.cos(a):.1f}" y1="{my + 176 * math.sin(a):.1f}" '
        f'x2="{mx + (186 if k % 4 == 0 else 181) * math.cos(a):.1f}" y2="{my + (186 if k % 4 == 0 else 181) * math.sin(a):.1f}" '
        f'stroke="{C["muted"] if k % 4 else C["sun"]}" stroke-width="1.4" opacity=".55"/>'
        for k in range(48) for a in [k * 2 * math.pi / 48])
    medallion = f"""
<circle class="glow" cx="{mx}" cy="{my}" r="300" fill="url(#g1)"/>
<g class="spinr">{ring_ticks}</g>
<g class="spin">
  <circle class="d d4" pathLength="1" cx="{mx}" cy="{my}" r="168"/>
  <path class="fill8" d="{khatam(mx, my, 128)}"/>
  <path class="d d1" pathLength="1" d="{star_8_3(mx, my, 160, 22.5)}"/>
  <path class="d d2" pathLength="1" d="{khatam(mx, my, 128)}"/>
  <path class="d d3" pathLength="1" d="{khatam(mx, my, 70, 22.5)}"/>
  <circle class="d d4" pathLength="1" cx="{mx}" cy="{my}" r="44"/>
</g>
<circle class="core" cx="{mx}" cy="{my}" r="9"/>
<g class="orbit"><circle class="dot" cx="{mx + 168}" cy="{my}" r="5"/></g>"""

    roles_body, roles_css, caret, total = typed_chars(
        "ty", ROLES, x0=72 + 2 * 13.2, y=360, cw=13.2, size=22, colour=C["text"],
        t0=1400, type_ms=55, hold_ms=2000, del_ms=24, gap_ms=380)
    css.append(roles_css)
    css.append(caret_keyframes("cmove", caret, total, 72 + 2 * 13.2))
    # reduced motion: final frame, first role printed
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important;stroke-dashoffset:0!important}"
               f".typ0{{opacity:1}}.cmove{{transform:translate({72 + (2 + len(ROLES[0])) * 13.2:.1f}px,0)}}}}")

    text = f"""
<text class="eyebrow" x="74" y="112">HI, I'M</text>
<g clip-path="url(#m1)"><text class="name n1" x="68" y="196">{escape(FIRST)}</text></g>
<g clip-path="url(#m2)"><text class="name n2" x="68" y="280">{escape(LAST)}</text></g>
<path class="rule" pathLength="1" d="M74 312 H 292"/>
<text class="prompt" x="72" y="360">&gt;</text>
{roles_body}
<g class="cmove caret"><rect x="2" y="341" width="12" height="24" rx="2"/></g>"""
    body = (f'{defs}\n<g clip-path="url(#card)">\n<rect class="bg" width="{W}" height="{H}"/>\n'
            f'<g class="drift"><rect x="-80" y="-80" width="{W + 160}" height="{H + 160}" fill="url(#tile)"/></g>\n'
            f'<circle class="glow2" cx="150" cy="420" r="320" fill="url(#g2)"/>\n'
            f'<rect width="760" height="{H}" fill="url(#fadeL)"/>\n{medallion}\n{text}\n</g>')
    write("hero.svg", svg(W, H, f"{FIRST} {LAST} - {ROLES[0]}", body, "\n".join(css)))


# ---------------------------------------------------------------- TERMINAL
def terminal():
    W, LH, X0, Y0, FS = 1200, 36, 40, 104, 19
    cw = FS * 0.6
    H = Y0 + LH * (len(TERMINAL) - 1) + 52
    type_ms, after_cmd, after_out, hold, fade = 62, 380, 260, 6500, 500
    items, caret, t, y = [], [], 900, Y0
    for kind, val in TERMINAL:
        if kind == "cmd":
            px = X0 + 2 * cw
            items.append(("prompt", t, y, None))
            caret.append((t, px, y))
            for i, ch in enumerate(val):
                items.append(("ch", t + 150 + i * type_ms, y, (px + i * cw, ch)))
                caret.append((t + 150 + i * type_ms, px + (i + 1) * cw, y))
            t += 150 + len(val) * type_ms + after_cmd
        else:
            items.append(("out", t, y, val))
            t += after_out
        y += LH
    caret.append((t, X0 + 2 * cw, y))
    items.append(("prompt", t, y, None))  # idle prompt at the end
    off = t + hold
    total = off + fade + 300

    css = [f"""
.win{{fill:{C['ink']};stroke:{C['line']};stroke-width:1.5}}
.bar{{fill:{C['ink2']}}}
.ttl{{font:500 14px {MONO};fill:{C['muted']}}}
.t{{font:500 {FS}px {MONO};white-space:pre}}
.ps{{fill:{C['teal']}}} .pt{{fill:{C['sun']}}}
.c{{fill:{C['text']}}}
.caret rect{{fill:{C['sun']};animation:blink 1s steps(1,end) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
"""]
    body = [f'<rect class="win" x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16"/>',
            f'<path class="bar" d="M17 1.75 H{W - 17} a15.25 15.25 0 0 1 15.25 15.25 V48 H1.75 V17 A15.25 15.25 0 0 1 17 1.75 Z"/>',
            f'<line x1="1.5" y1="48" x2="{W - 1.5}" y2="48" stroke="{C["line"]}"/>']
    for i, col in enumerate(("rose", "sun", "teal")):
        body.append(f'<circle cx="{28 + i * 22}" cy="25" r="6.5" fill="{C[col]}"/>')
    body.append(f'<text class="ttl" x="{W / 2}" y="30" text-anchor="middle">{escape(TERMINAL_TITLE)}</text>')

    for n, (kind, t_on, y, val) in enumerate(items):
        name = f"e{n}"
        rise = kind == "out"
        a_on = pct(t_on, total)
        a_full = pct(t_on + (280 if rise else 1), total)
        a_off, a_end = pct(off, total), pct(off + fade, total)
        frm = "opacity:0;transform:translateY(6px)" if rise else "opacity:0"
        css.append(f"@keyframes {name}{{0%,{a_on}{{{frm}}}{a_full},{a_off}{{opacity:1;transform:none}}"
                   f"{a_end},100%{{opacity:0}}}}.{name}{{animation:{name} {total}ms {'ease-out' if rise else 'linear'} infinite}}")
        if kind == "prompt":
            body.append(f'<text class="t {name}" x="{X0}" y="{y}"><tspan class="ps">$</tspan></text>')
        elif kind == "ch":
            x, ch = val
            body.append(f'<text class="t c {name}" x="{x:.1f}" y="{y}">{escape(ch)}</text>')
        else:
            spans = "".join(f'<tspan fill="{C[col]}">{escape(s)}</tspan>' for s, col in val)
            body.append(f'<text class="t {name}" x="{X0 + 2 * cw:.1f}" y="{y}" xml:space="preserve">{spans}</text>')
    # caret: hidden after the fade, back at the first prompt
    stops = [f"0%{{transform:translate({X0 + 2 * cw:.1f}px,{Y0}px)}}"]
    stops += [f"{pct(tt, total)}{{transform:translate({x:.1f}px,{yy}px)}}" for tt, x, yy in caret]
    stops.append(f"{pct(off + fade, total)}{{transform:translate({X0 + 2 * cw:.1f}px,{Y0}px)}}")
    css.append(f"@keyframes tc{{{''.join(stops)}}}.tc{{animation:tc {total}ms steps(1,end) infinite}}")
    body.append(f'<g class="tc caret"><rect x="1" y="-17" width="10" height="22" rx="1.5"/></g>')
    last_y = items[-1][2]
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}"
               f".tc{{transform:translate({X0 + 2 * cw:.1f}px,{last_y}px)}}}}")
    write("terminal.svg", svg(W, H, "whoami - " + " / ".join(v for k, v in TERMINAL if k == "cmd"),
                              "\n".join(body), "\n".join(css)))


# ---------------------------------------------------------------- STACK
CUSTOM_ICONS = {
    # three candlesticks, 24x24
    "_candles": "M5 3h1.5v4H8v9H6.5v5H5v-5H3.5V7H5zM11.25 6h1.5v3h1.5v7h-1.5v3h-1.5v-3h-1.5V9h1.5zM17.5 2H19v6h1.5v6H19v8h-1.5v-8H16V8h1.5z",
}


ICON_SCALE = {"woocommerce": 3.0, "mysql": 1.9}  # wide wordmark logos need more room


def stack():
    icons = json.load(open(os.path.join(HERE, "icons.json")))
    icons.update(CUSTOM_ICONS)
    cols, tw, th, gap, pad = 7, 152, 116, 16, 20
    rows = math.ceil(len(STACK) / cols)
    W = cols * tw + (cols - 1) * gap + 2 * pad
    H = rows * th + (rows - 1) * gap + 2 * pad
    wave = 8000
    css = [f"""
.tile{{fill:{C['ink2']};stroke:{C['line']};stroke-width:1.2}}
.lbl{{font:500 13px {MONO};fill:{C['muted']}}}
.ic{{fill:{C['text']}}}
.fa{{font:800 30px {SANS};fill:{C['text']}}}
.in{{transform-box:fill-box;transform-origin:center;animation:in .7s {EXPO} both}}
@keyframes in{{from{{opacity:0;transform:translateY(14px) scale(.94)}}}}
@keyframes hi{{0%,9%,100%{{stroke:{C['line']}}}4%{{stroke:{C['teal']}}}}}
@keyframes hiS{{0%,9%,100%{{stroke:{C['line']}}}4%{{stroke:{C['sun']}}}}}
@keyframes ico{{0%,9%,100%{{fill:{C['text']}}}4%{{fill:{C['teal']}}}}}
@keyframes icoS{{0%,9%,100%{{fill:{C['text']}}}4%{{fill:{C['sun']}}}}}
@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}
"""]
    body = []
    for k, (label, key) in enumerate(STACK):
        r, c = divmod(k, cols)
        x, y = pad + c * (tw + gap), pad + r * (th + gap)
        d_in = 0.15 + (r + c) * 0.06
        d_wave = 1.6 + (r + c) * 0.18
        sun = (r + c) % 3 == 2
        css.append(f".k{k}{{animation-delay:{d_in:.2f}s}}"
                   f".k{k} .tile{{animation:{'hiS' if sun else 'hi'} {wave}ms ease-in-out {d_wave:.2f}s infinite}}"
                   f".k{k} .ic,.k{k} .fa{{animation:{'icoS' if sun else 'ico'} {wave}ms ease-in-out {d_wave:.2f}s infinite}}")
        if key == "_farsi":
            icon = f'<text class="fa" x="{tw / 2}" y="60" text-anchor="middle" direction="rtl">فا</text>'
        else:
            sc = ICON_SCALE.get(key, 1.5)
            icon = f'<path class="ic" transform="translate({tw / 2 - 12 * sc:.1f} {40 - 12 * sc:.1f}) scale({sc})" d="{icons[key]}"/>'
        body.append(
            f'<g transform="translate({x} {y})"><g class="in k{k}">'
            f'<rect class="tile" width="{tw}" height="{th}" rx="14"/>{icon}'
            f'<text class="lbl" x="{tw / 2}" y="92" text-anchor="middle">{escape(label)}</text></g></g>')
    write("stack.svg", svg(W, H, "Tech stack: " + ", ".join(l for l, _ in STACK), "\n".join(body), "\n".join(css)))


# ---------------------------------------------------------------- FOOTER
def footer():
    W, H, wl = 1200, 150, 300

    def wave(amp, base, phase):
        d = f"M{-wl} {base}"
        for i in range(-wl, W + 2 * wl + 1, 10):
            d += f" L{i} {base + amp * math.sin((i / wl) * 2 * math.pi + phase):.1f}"
        return d + f" L{W + 2 * wl} {H} L{-wl} {H} Z"

    css = f"""
.w1{{fill:{C['teal']};opacity:.22;animation:slide 9s linear infinite}}
.w2{{fill:{C['sun']};opacity:.16;animation:slide 13s linear infinite reverse}}
.w3{{fill:{C['ink2']};animation:slide 17s linear infinite}}
@keyframes slide{{to{{transform:translateX({wl}px)}}}}
.en{{font:500 15px {MONO};fill:{C['text']};letter-spacing:.08em}}
.fa{{font:600 17px {SANS};fill:{C['teal']}}}
@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}"""
    body = (f'<defs><clipPath id="card"><rect width="{W}" height="{H}" rx="22"/></clipPath></defs>\n'
            f'<g clip-path="url(#card)"><rect width="{W}" height="{H}" fill="{C['ink']}"/>\n'
            f'<path class="w1" d="{wave(12, 92, 0)}"/>\n<path class="w2" d="{wave(9, 104, 1.6)}"/>\n'
            f'<path class="w3" d="{wave(7, 118, 3.1)}"/>\n'
            f'<text class="en" x="{W / 2}" y="40" text-anchor="middle">{escape(FOOTER_EN)}</text>\n'
            f'<text class="fa" x="{W / 2}" y="68" text-anchor="middle" direction="rtl">{escape(FOOTER_FA)}</text></g>')
    write("footer.svg", svg(W, H, FOOTER_EN, body, css))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    hero()
    terminal()
    stack()
    footer()
