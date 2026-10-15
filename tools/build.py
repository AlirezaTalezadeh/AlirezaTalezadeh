#!/usr/bin/env python3
"""Builds the animated SVGs in ../assets/ for the GitHub profile README.

Account4All look (light only): white rounded cards, electric blue #1f1eff,
the cyan-to-blue A4 logo, homepage sparkles, and pixel-art sprites.

Needs fontTools + brotli (a Vazirmatn subset is embedded in every SVG):
    python3 -m venv /dev/shm/ftvenv && /dev/shm/ftvenv/bin/pip install fonttools brotli
    /dev/shm/ftvenv/bin/python tools/build.py

GitHub keeps <style> and SMIL inside SVG images, so CSS keyframes and
<animateMotion> both play on github.com.
"""
import base64
import io
import math
import os
import re
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets")

# ---------------------------------------------------------------- CONTENT
NAME_FIRST, NAME_LAST = "Alireza", "Talezadeh"
ROLE = "Founder & CEO"
SITE = "account4all.ir"
TAG_EN = ("Building account4all.ir", " — a story that never ends!")
TAG_FA = ("در حال ساختن اکانت فور آل؛ ", "داستانی که تمومی نداره!")

DESK_EYEBROW = "LIVE FROM THE FOUNDER'S DESK"
DESK_TITLE = "A day at account4all.ir"
FEED = [  # (icon, tint, title, subtitle, time) - illustrative events
    ("cart", "blue", "New order", "ChatGPT Plus · 1 month", "now"),
    ("bolt", "amber", "Delivered", "Spotify Premium · in minutes", "1m"),
    ("heart", "red", "New 5-star review", "“Fast and friendly, thank you!”", "3m"),
    ("mug12", "green", "Coffee break", "Cup number three today", "5m"),
]

DO_TITLE = "What I do"
DO_SUB = "Running an online store, every single day"
DO = [  # (icon, title, line)
    ("cart", "E-commerce, daily", "Orders, delivery and support"),
    ("chart", "Growth", "SEO, marketing, getting found"),
    ("heart", "Customers first", "Fast answers and fair prices"),
    ("bolt", "Fast delivery", "Premium accounts, delivered quickly"),
    ("card", "Smooth payments", "Checkout and wallet that just work"),
    ("mug12", "Founder & CEO", "Vision, team and lots of coffee"),
]
FOOTER = "made with coffee and love"

# ---------------------------------------------------------------- TOKENS (Account4All kit v1.0.0)
C = {
    "surface": "#ffffff", "border": "#e5e5e9", "border2": "#d0d0d8",
    "text": "#23242b", "text2": "#61616e", "muted": "#73737f",
    "primary": "#1f1eff", "blue500": "#5a59fe", "blue50": "#f0f0ff", "blue100": "#e3e3ff", "blue200": "#d2d2ff",
    "cyan": "#00c8ff", "logo2": "#0d6dff",
    "green": "#06a731", "green50": "#e9f8ee", "red": "#ff4d6d", "red50": "#fff0f3",
    "amber": "#f29d00", "amber50": "#fff7e0", "sun": "#ffc83d",
}
FONT = "A4V, Vazirmatn, Tahoma, sans-serif"
EASE = "cubic-bezier(0.2, 0, 0, 1)"          # the kit's motion curve
EXPO = "cubic-bezier(0.16, 1, 0.3, 1)"
POP = "cubic-bezier(0.34, 1.56, 0.64, 1)"

# ---------------------------------------------------------------- PIXEL SPRITES
PAL = {
    "k": "#23242b", "h": "#3b2a22", "s": "#f8cfb0", "b": "#ffa3b5", "w": "#ffffff",
    "B": "#1f1eff", "g": "#c4c4d0", "C": "#6b3e26", "r": "#ff4d6d", "R": "#ff9fb2",
    "y": "#ffc83d", "Y": "#f29d00", "n": "#06a731", "p": "#3cb35a", "P": "#d98b5f",
}
SPR = {
    "ceo": [
        "....kkkkkkkkkk....",
        "..kkhhhhhhhhhhkk..",
        ".khhhhhhhhhhhhhhk.",
        "khhhhhhhhhhhhhhhhk",
        "khhhhhhhhhhhhhhhhk",
        "khhhsshhhhhhsshhhk",
        "khhsssssssssssshhk",
        "khsssssssssssssshk",
        "kssswksssssswksssk",
        "ksssKKssssssKKsssk",
        "ksbbssssssssssbbsk",
        "kssssskssssksssssk",
        "kssssssskksssssssk",
        ".kssssssssssssssk.",
        "..kkssssssssssskk.",
        "....kkkssssskkk...",
        "..kkBBBBwwBBBBkk..",
        ".kBBBBBBwwBBBBBBk.",
        "kBBBBBBBBBBBBBBBBk",
        "kBBBBBBBBBBBBBBBBk",
        "kBBBBBBBBBBBBBBBBk",
    ],
    "mug": [
        "kkkkkkk..",
        "kCCCCCk..",
        "kwwwwwkkk",
        "kBBBBBk.k",
        "kwwwwwk.k",
        "kwwwwwkkk",
        "kwwwwwk..",
        ".kkkkk...",
    ],
    "plant": [
        "..p.p..",
        ".ppppp.",
        "ppp.ppp",
        ".ppppp.",
        "..ppp..",
        ".PPPPP.",
        ".PPPPP.",
        "..PPP..",
    ],
    "heart_s": [
        ".rr.rr.",
        "rRrrrrr",
        "rrrrrrr",
        ".rrrrr.",
        "..rrr..",
        "...r...",
    ],
    "cart": [
        "kk..........",
        ".k..........",
        ".kBBBBBBBBBk",
        ".kBBBBBBBBk.",
        "..kBBBBBBBk.",
        "..kBBBBBBk..",
        "...kkkkkkk..",
        "...k........",
        "...kkkkkkkk.",
        "....kk...kk.",
        "....kk...kk.",
        "............",
    ],
    "chart": [
        "........nnnn",
        "..........nn",
        ".........n.n",
        "........n...",
        "...n...n....",
        "..n.n.n.....",
        ".n...n...BB.",
        "n........BB.",
        "......BB.BB.",
        "...BB.BB.BB.",
        "...BB.BB.BB.",
        "kkkkkkkkkkkk",
    ],
    "heart": [
        "............",
        "..rrr..rrr..",
        ".rRRrrrrrrr.",
        "rRRrrrrrrrrr",
        "rRrrrrrrrrrr",
        "rrrrrrrrrrrr",
        ".rrrrrrrrrr.",
        "..rrrrrrrr..",
        "...rrrrrr...",
        "....rrrr....",
        ".....rr.....",
        "............",
    ],
    "bolt": [
        ".......YYYY.",
        "......YyyY..",
        ".....YyyY...",
        "....YyyY....",
        "...YyyyyyyY.",
        "..YYYYyyyY..",
        "......YyY...",
        ".....YyY....",
        "....YyY.....",
        "...YY.......",
        "..Y.........",
        "............",
    ],
    "card": [
        "............",
        "............",
        "kkkkkkkkkkkk",
        "kBBBBBBBBBBk",
        "kkkkkkkkkkkk",
        "kBBBBBBBBBBk",
        "kByyBBBBBBBk",
        "kByyBBBBBBBk",
        "kBBBBBwwwwBk",
        "kkkkkkkkkkkk",
        "............",
        "............",
    ],
    "mug12": [
        "...g..g.....",
        "..g..g......",
        "...g..g.....",
        "............",
        "kkkkkkkkk...",
        "kCCCCCCCk...",
        "kwwwwwwwkkk.",
        "kBBBBBBBk.k.",
        "kwwwwwwwk.k.",
        "kwwwwwwwkkk.",
        "kwwwwwwwk...",
        ".kkkkkkk....",
    ],
}
PAL["K"] = PAL["k"]


def sprite(key, P, x=0, y=0):
    rows = SPR[key]
    width = max(len(r) for r in rows)
    out = []
    for j, row in enumerate(rows):
        row = row.ljust(width, ".")
        i = 0
        while i < width:
            ch, k = row[i], i
            while k < width and row[k] == ch:
                k += 1
            if ch != ".":
                out.append(f'<rect x="{x + i * P:g}" y="{y + j * P:g}" width="{(k - i) * P:g}" height="{P:g}" fill="{PAL[ch]}"/>')
            i = k
    return '<g shape-rendering="crispEdges">' + "".join(out) + "</g>"


def sprite_size(key, P):
    rows = SPR[key]
    return max(len(r) for r in rows) * P, len(rows) * P


# ---------------------------------------------------------------- HELPERS
_TEXTS = []


def T(s):
    """Escape text for SVG and remember it for the font subset."""
    _TEXTS.append(s)
    return escape(s)


def font_css():
    chars = "".join(_TEXTS) + " +="
    _TEXTS.clear()
    css = []
    for weight, fname in ((400, "Vazirmatn-Regular.woff2"), (800, "Vazirmatn-Bold.woff2")):
        f = TTFont(os.path.join(HERE, fname))
        opts = subset.Options()
        opts.layout_features = ["*"]
        opts.flavor = "woff2"
        sub = subset.Subsetter(opts)
        sub.populate(text=chars)
        sub.subset(f)
        buf = io.BytesIO()
        f.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        css.append(f"@font-face{{font-family:A4V;font-weight:{weight};src:url(data:font/woff2;base64,{b64}) format('woff2')}}")
    return "\n".join(css)


def svg(w, h, title, body, css):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(title)}">\n<title>{escape(title)}</title>\n'
            f'<style>\n{font_css()}\ntext{{font-family:{FONT}}}\n{css}\n'
            f'@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}\n</style>\n{body}\n</svg>\n')


def write(name, content):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"{name:12} {len(content.encode()) / 1024:6.1f} KB")


def card(W, H, rx=28):
    return (f'<defs><filter id="sh" x="-10%" y="-20%" width="120%" height="160%">'
            f'<feDropShadow dx="0" dy="6" stdDeviation="9" flood-color="#191846" flood-opacity=".08"/></filter>'
            f'<linearGradient id="lg" x1="1" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{C["cyan"]}"/>'
            f'<stop offset="1" stop-color="{C["logo2"]}"/></linearGradient></defs>'
            f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="{rx}" fill="{C["surface"]}" stroke="{C["border"]}" stroke-width="1.5"/>')


def logo(fill="url(#lg)"):
    s = open(os.path.join(HERE, "a4-logo.svg"), encoding="utf-8").read()
    return "".join(f'<path d="{d}" fill="{fill}"/>' for d in re.findall(r'<path d="([^"]+)"', s))


def sparkle(x, y, r, colour, delay):
    d = (f"M0 {-r} C{r * .12:.2f} {-r * .2:.2f} {r * .2:.2f} {-r * .12:.2f} {r} 0 "
         f"C{r * .2:.2f} {r * .12:.2f} {r * .12:.2f} {r * .2:.2f} 0 {r} "
         f"C{-r * .12:.2f} {r * .2:.2f} {-r * .2:.2f} {r * .12:.2f} {-r} 0 "
         f"C{-r * .2:.2f} {-r * .12:.2f} {-r * .12:.2f} {-r * .2:.2f} 0 {-r}Z")
    return f'<g transform="translate({x} {y})"><path class="tw" d="{d}" fill="{colour}" style="animation-delay:{delay}s"/></g>'


SPARKLE_CSS = (".tw{transform-box:fill-box;transform-origin:center;animation:tw 2.6s ease-in-out infinite}"
               "@keyframes tw{0%,100%{transform:scale(.45) rotate(0);opacity:.35}50%{transform:scale(1) rotate(45deg);opacity:1}}")


def lemniscate(cx, cy, a, sy, n=160):
    pts = []
    for k in range(n):
        t = 2 * math.pi * k / n
        d = 1 + math.sin(t) ** 2
        pts.append((cx + a * math.cos(t) / d, cy + sy * a * math.sin(t) * math.cos(t) / d))
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"


# ---------------------------------------------------------------- HERO
def hero():
    W, H = 1200, 400
    cx, cy = 905, 214
    inf = lemniscate(cx, cy, 225, 1.55)
    css = f"""
.lockup{{transform-box:fill-box;transform-origin:center;animation:pop .8s {POP} .1s both}}
@keyframes pop{{from{{transform:scale(.6);opacity:0}}}}
.shine{{animation:shine 5s {EASE} 1.2s infinite both}}
@keyframes shine{{0%{{transform:translateX(-40px)}}30%,100%{{transform:translateX(80px)}}}}
.site{{font-weight:800;font-size:22px;fill:{C['text']};animation:fade .6s ease-out .3s both}}
.chip{{animation:up .7s {EXPO} .35s both}}
.chipt{{font-weight:800;font-size:14px;fill:{C['primary']}}}
.live{{transform-box:fill-box;transform-origin:center;animation:live 1.8s ease-out infinite}}
@keyframes live{{0%{{transform:scale(1);opacity:.6}}100%{{transform:scale(2.6);opacity:0}}}}
.name{{font-weight:800;font-size:58px;animation:rise .9s {EXPO} .45s both}}
@keyframes rise{{from{{transform:translateY(80px)}}}}
@keyframes up{{from{{transform:translateY(14px);opacity:0}}}}
@keyframes fade{{from{{opacity:0}}}}
.tag{{font-size:21px}}
.en,.fa{{animation:swap 12s {EXPO} infinite both}}
.en{{animation-delay:1.1s}} .fa{{animation-delay:-4.9s}}
@keyframes swap{{0%{{transform:translateY(34px);opacity:0}}6%,44%{{transform:none;opacity:1}}50%,100%{{transform:translateY(-34px);opacity:0}}}}
.track{{fill:none;stroke:{C['blue50']};stroke-width:24;stroke-linejoin:round}}
.flow{{fill:none;stroke:url(#lgf);stroke-width:5;stroke-linecap:round;stroke-dasharray:70 50;animation:flow 6s linear infinite}}
@keyframes flow{{to{{stroke-dashoffset:-1200}}}}
.inf{{animation:fade 1s ease-out .6s both}}
@media (prefers-reduced-motion: reduce){{.fa{{opacity:0}}}}
{SPARKLE_CSS}
"""
    body = f"""{card(W, H)}
<defs>
<linearGradient id="lgf" gradientUnits="userSpaceOnUse" x1="{cx - 230}" y1="0" x2="{cx + 230}" y2="0"><stop offset="0" stop-color="{C['cyan']}"/><stop offset=".5" stop-color="{C['primary']}"/><stop offset="1" stop-color="{C['blue500']}"/></linearGradient>
<linearGradient id="sw" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".8"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<clipPath id="lc">{logo()}</clipPath>
<clipPath id="nm"><rect x="40" y="170" width="660" height="84"/></clipPath>
<clipPath id="tg"><rect x="40" y="272" width="660" height="42"/></clipPath>
<clipPath id="cardc"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="28"/></clipPath>
<radialGradient id="blob"><stop offset="0" stop-color="{C['blue100']}" stop-opacity=".9"/><stop offset="1" stop-color="{C['blue50']}" stop-opacity="0"/></radialGradient>
<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.3" fill="{C['border2']}" opacity=".6"/></pattern>
<linearGradient id="dfade" x1="0" x2="1"><stop offset="0" stop-color="#fff"/><stop offset=".25" stop-color="#fff" stop-opacity="0"/></linearGradient>
</defs>
<g clip-path="url(#cardc)">
<rect x="620" y="0" width="580" height="{H}" fill="url(#dots)"/>
<rect x="620" y="0" width="580" height="{H}" fill="url(#dfade)"/>
<circle cx="{cx}" cy="{cy}" r="300" fill="url(#blob)"/>
</g>
<g transform="translate(64 44) scale(1.12)"><g class="lockup">{logo()}
<g clip-path="url(#lc)"><rect class="shine" x="-20" y="-10" width="30" height="80" fill="url(#sw)" transform="skewX(-20)"/></g></g></g>
<text class="site" x="130" y="83">{T(SITE)}</text>
<g class="chip"><rect x="64" y="122" width="160" height="34" rx="17" fill="{C['blue50']}" stroke="{C['blue200']}"/>
<circle class="live" cx="84" cy="139" r="5" fill="{C['green']}"/><circle cx="84" cy="139" r="5" fill="{C['green']}"/>
<text class="chipt" x="98" y="144">{T(ROLE)}</text></g>
<g clip-path="url(#nm)"><text class="name" x="62" y="236"><tspan fill="{C['text']}">{T(NAME_FIRST)} </tspan><tspan fill="{C['primary']}">{T(NAME_LAST)}</tspan></text></g>
<g clip-path="url(#tg)">
<text class="tag en" x="64" y="301"><tspan fill="{C['text']}" font-weight="800">{T(TAG_EN[0])}</tspan><tspan fill="{C['text2']}">{T(TAG_EN[1])}</tspan></text>
<text class="tag fa" x="64" y="301" direction="rtl" text-anchor="end"><tspan fill="{C['text']}">{T(TAG_FA[0])}</tspan><tspan fill="{C['primary']}" font-weight="800">{T(TAG_FA[1])}</tspan></text>
</g>
<g class="inf"><path class="track" d="{inf}"/><path class="flow" pathLength="1200" d="{inf}"/></g>
{sparkle(1120, 66, 16, C['sun'], 0)}
{sparkle(682, 336, 11, C['primary'], .9)}
{sparkle(1136, 340, 9, C['blue500'], 1.7)}
{sparkle(600, 96, 10, C['sun'], 1.3)}
"""
    # travellers on the never-ending loop
    for k, icon in enumerate(("cart", "heart", "mug12", "bolt")):
        w, h = sprite_size(icon, 3)
        body += (f'<g><circle r="27" fill="{C["surface"]}" stroke="{C["border"]}" stroke-width="1.5" filter="url(#sh)"/>'
                 f'{sprite(icon, 3, -w / 2, -h / 2)}'
                 f'<animateMotion dur="16s" repeatCount="indefinite" begin="{-k * 4}s" path="{inf}"/></g>\n')
    write("hero.svg", svg(W, H, f"{NAME_FIRST} {NAME_LAST}, {ROLE} of {SITE}. {''.join(TAG_EN)}", body, css))


# ---------------------------------------------------------------- DESK (pixel scene + live feed)
def desk():
    W, H = 1200, 440
    P = 8
    rx0, ry0, rw, rh = 40, 40, 520, 360
    cw_, ch_ = sprite_size("ceo", P)
    ceo_x = rx0 + (rw - cw_) / 2 - 24
    desk_y = 300
    ceo_y = desk_y - ch_ - 6
    css = f"""
.bob{{animation:bob 1.1s steps(1,end) infinite}}
@keyframes bob{{50%{{transform:translateY(4px)}}}}
.blink{{opacity:0;animation:blink 4.2s steps(1,end) infinite}}
@keyframes blink{{0%,93%{{opacity:0}}94%,98%{{opacity:1}}99%{{opacity:0}}}}
.steam{{animation:steam 2.4s ease-out infinite both}}
@keyframes steam{{0%{{transform:translateY(0);opacity:0}}25%{{opacity:.9}}100%{{transform:translateY(-34px);opacity:0}}}}
.luv{{animation:luv 4.2s ease-out infinite both}}
@keyframes luv{{0%{{transform:translate(0,0);opacity:0}}12%{{opacity:1;transform:translate(0,-14px)}}70%{{opacity:1}}100%{{transform:translate(16px,-96px);opacity:0}}}}
.cloud{{animation:cloud 14s linear infinite}}
@keyframes cloud{{from{{transform:translateX(-80px)}}to{{transform:translateX(160px)}}}}
.glow{{animation:glow 2.4s ease-in-out infinite alternate}}
@keyframes glow{{from{{opacity:.45}}to{{opacity:1}}}}
.eyebrow{{font-weight:800;font-size:13px;letter-spacing:.12em;fill:{C['primary']}}}
.h{{font-weight:800;font-size:28px;fill:{C['text']}}}
.ft{{font-weight:800;font-size:16px;fill:{C['text']}}}
.fs{{font-size:14px;fill:{C['text2']}}}
.fm{{font-size:13px;fill:{C['muted']}}}
.toast{{animation:toast 14s {EXPO} infinite both}}
@keyframes toast{{0%{{transform:translateX(46px);opacity:0}}5%,84%{{transform:none;opacity:1}}90%,100%{{transform:none;opacity:0}}}}
.ring{{transform-box:fill-box;transform-origin:center;animation:ring 14s ease-out infinite both}}
@keyframes ring{{0%{{transform:scale(1);opacity:0}}3%{{opacity:.7}}12%,100%{{transform:scale(1.6);opacity:0}}}}
.dot{{animation:dot 1s steps(1,end) infinite}}
@keyframes dot{{50%{{opacity:.25}}}}
{SPARKLE_CSS}
"""
    tints = {"blue": (C["blue50"], C["primary"]), "amber": (C["amber50"], C["amber"]),
             "red": (C["red50"], C["red"]), "green": (C["green50"], C["green"])}
    crisp = 'shape-rendering="crispEdges"'
    b = [card(W, H),
         f'<defs><clipPath id="room"><rect x="{rx0}" y="{ry0}" width="{rw}" height="{rh}" rx="20"/></clipPath>'
         f'<clipPath id="win"><rect x="364" y="76" width="152" height="104"/></clipPath></defs>',
         f'<g clip-path="url(#room)"><rect x="{rx0}" y="{ry0}" width="{rw}" height="{rh}" fill="{C["blue50"]}"/>']
    # window with a drifting cloud
    b.append(f'<g {crisp}><rect x="356" y="68" width="168" height="120" fill="{C["border2"]}"/>'
             f'<rect x="364" y="76" width="152" height="104" fill="#c6f0ff"/></g>'
             f'<g clip-path="url(#win)"><g class="cloud" {crisp}>'
             f'<rect x="384" y="108" width="48" height="16" fill="#fff"/><rect x="396" y="96" width="24" height="12" fill="#fff"/>'
             f'<rect x="446" y="142" width="32" height="12" fill="#fff"/><rect x="454" y="134" width="16" height="8" fill="#fff"/></g></g>'
             f'<rect x="436" y="76" width="8" height="104" fill="{C["border2"]}" {crisp}/>')
    # framed A4 poster
    b.append(f'<rect x="80" y="72" width="120" height="120" fill="{C["surface"]}" stroke="{C["border2"]}" stroke-width="8" {crisp}/>'
             f'<g transform="translate(110 102) scale(1.2)">{logo()}</g>')
    # floor
    b.append(f'<rect x="{rx0}" y="{desk_y + 40}" width="{rw}" height="80" fill="{C["blue100"]}"/>')
    # character, bobbing while typing, blinking
    ey = ceo_y + 8 * P
    blink = (f'<g class="blink" {crisp}>'
             + "".join(f'<rect x="{ceo_x + cx_ * P}" y="{ey}" width="{2 * P}" height="{2 * P}" fill="{PAL["s"]}"/>'
                       f'<rect x="{ceo_x + cx_ * P}" y="{ey + P}" width="{2 * P}" height="{P / 2}" fill="{PAL["k"]}"/>'
                       for cx_ in (4, 12)) + "</g>")
    b.append(f'<g class="bob">{sprite("ceo", P, ceo_x, ceo_y)}{blink}</g>')
    for dx, delay in ((-34, 0), (44, 1.4), (6, 2.8)):
        b.append(f'<g class="luv" style="animation-delay:{delay}s">{sprite("heart_s", 4, ceo_x + cw_ / 2 + dx, ceo_y + 6)}</g>')
    # desk + laptop (we see the back of the lid)
    b.append(f'<g {crisp}><rect x="{rx0}" y="{desk_y}" width="{rw}" height="14" fill="{C["border2"]}"/>'
             f'<rect x="{rx0}" y="{desk_y + 14}" width="{rw}" height="26" fill="{C["border"]}"/></g>')
    lx, lw, lh = ceo_x + 4, cw_ - 8, 64
    b.append(f'<g {crisp}><rect x="{lx}" y="{desk_y - lh}" width="{lw}" height="{lh}" fill="#8f8fa3"/>'
             f'<rect x="{lx + 6}" y="{desk_y - lh + 6}" width="{lw - 12}" height="{lh - 6}" fill="#b4b4c4"/></g>'
             f'<g class="glow" transform="translate({lx + lw / 2 - 14} {desk_y - lh + 16}) scale(.58)">{logo("#ffffff")}</g>'
             f'<rect x="{lx - 18}" y="{desk_y - 6}" width="{lw + 36}" height="6" fill="#73738a" {crisp}/>')
    # mug with steam, plant
    mx, my = lx + lw + 40, desk_y - 64
    b.append(sprite("mug", 8, mx, my))
    for k, sx in enumerate((mx + 8, mx + 24, mx + 40)):
        b.append(f'<g class="steam" style="animation-delay:{k * .8}s" {crisp}>'
                 f'<rect x="{sx}" y="{my - 12}" width="6" height="6" fill="#c4c4d0"/>'
                 f'<rect x="{sx + 6}" y="{my - 18}" width="6" height="6" fill="#c4c4d0"/></g>')
    b.append(sprite("plant", 8, rx0 + 30, desk_y - 64))
    b.append("</g>")
    # live feed
    fx = 610
    b.append(f'<circle class="dot" cx="{fx + 5}" cy="66" r="5" fill="{C["green"]}"/>'
             f'<text class="eyebrow" x="{fx + 18}" y="71">{T(DESK_EYEBROW)}</text>'
             f'<text class="h" x="{fx}" y="112">{T(DESK_TITLE)}</text>')
    for k, (icon, tint, title, sub, t) in enumerate(FEED):
        y = 140 + k * 70
        soft, strong = tints[tint]
        delay = 0.6 + k * 1.3
        iw, ih = sprite_size(icon, 3)
        b.append(
            f'<g class="toast" style="animation-delay:{delay}s">'
            f'<rect x="{fx}" y="{y}" width="550" height="58" rx="16" fill="{C["surface"]}" stroke="{C["border"]}" stroke-width="1.5" filter="url(#sh)"/>'
            f'<rect class="ring" x="{fx + 10}" y="{y + 9}" width="40" height="40" rx="12" fill="none" stroke="{strong}" stroke-width="2" style="animation-delay:{delay}s"/>'
            f'<rect x="{fx + 10}" y="{y + 9}" width="40" height="40" rx="12" fill="{soft}"/>'
            f'{sprite(icon, 3, fx + 30 - iw / 2, y + 29 - ih / 2)}'
            f'<text class="ft" x="{fx + 64}" y="{y + 25}">{T(title)}</text>'
            f'<text class="fs" x="{fx + 64}" y="{y + 45}">{T(sub)}</text>'
            f'<text class="fm" x="{fx + 532}" y="{y + 25}" text-anchor="end">{T(t)}</text></g>')
    b.append(sparkle(1150, 58, 12, C["sun"], .4))
    write("desk.svg", svg(W, H, f"{DESK_TITLE}: new orders, fast delivery, happy customers and coffee",
                          "\n".join(b), css))


# ---------------------------------------------------------------- WHAT I DO
def what():
    cols, cw_, chh, gap, px, top = 3, 360, 116, 20, 40, 116
    rows = math.ceil(len(DO) / cols)
    W = 1200
    H = top + rows * chh + (rows - 1) * gap + 40
    css = f"""
.h{{font-weight:800;font-size:28px;fill:{C['text']}}}
.sub{{font-size:16px;fill:{C['text2']}}}
.ct{{font-weight:800;font-size:18px;fill:{C['text']}}}
.cs{{font-size:14px;fill:{C['text2']}}}
.in{{animation:in .8s {EXPO} both}}
@keyframes in{{from{{transform:translateY(18px);opacity:0}}}}
.hop{{animation:hop 7.2s steps(1,end) infinite}}
@keyframes hop{{0%,8%,100%{{transform:none}}2%{{transform:translateY(-5px)}}4%{{transform:translateY(-10px)}}6%{{transform:translateY(-4px)}}}}
.edge{{animation:edge 7.2s ease-in-out infinite}}
@keyframes edge{{0%,12%,100%{{stroke:{C['border']}}}4%{{stroke:{C['primary']}}}}}
{SPARKLE_CSS}
"""
    b = [card(W, H),
         f'<text class="h" x="{px}" y="66">{T(DO_TITLE)}</text>'
         f'<text class="sub" x="{px}" y="94">{T(DO_SUB)}</text>',
         sparkle(px + 152, 52, 10, C["sun"], 0)]
    for k, (icon, title, line) in enumerate(DO):
        r, c = divmod(k, cols)
        x, y = px + c * (cw_ + gap), top + r * (chh + gap)
        iw, ih = sprite_size(icon, 5)
        d_in, d_hop = 0.15 + k * 0.08, 1.2 + k * 1.2
        b.append(
            f'<g class="in" style="animation-delay:{d_in:.2f}s">'
            f'<rect class="edge" x="{x}" y="{y}" width="{cw_}" height="{chh}" rx="20" fill="{C["surface"]}" stroke="{C["border"]}" stroke-width="1.5" style="animation-delay:{d_hop:.1f}s"/>'
            f'<rect x="{x + 18}" y="{y + 18}" width="80" height="80" rx="16" fill="{C["blue50"]}"/>'
            f'<g class="hop" style="animation-delay:{d_hop:.1f}s">{sprite(icon, 5, x + 58 - iw / 2, y + 58 - ih / 2)}</g>'
            f'<text class="ct" x="{x + 118}" y="{y + 52}">{T(title)}</text>'
            f'<text class="cs" x="{x + 118}" y="{y + 78}">{T(line)}</text></g>')
    write("what.svg", svg(W, H, f"{DO_TITLE}: " + "; ".join(f"{t}, {l}" for _, t, l in DO), "\n".join(b), css))


# ---------------------------------------------------------------- FOOTER
def footer():
    W, H = 1200, 128
    cx = W / 2 + 24  # centres the coffee + love = ∞ row over the caption
    inf = lemniscate(cx + 70, 46, 36, 1.6, 80)
    css = f"""
.op{{font-weight:800;font-size:22px;fill:{C['muted']}}}
.t{{font-size:16px;fill:{C['text2']}}}
.s{{font-weight:800;fill:{C['primary']}}}
.beat{{transform-box:fill-box;transform-origin:center;animation:beat 1.4s ease-in-out infinite}}
@keyframes beat{{0%,40%,100%{{transform:scale(1)}}20%{{transform:scale(1.25)}}}}
.steam{{animation:steam 2.4s ease-out infinite both}}
@keyframes steam{{0%{{transform:translateY(0);opacity:0}}25%{{opacity:.9}}100%{{transform:translateY(-14px);opacity:0}}}}
.flow{{fill:none;stroke:url(#lgf);stroke-width:4;stroke-linecap:round;stroke-dasharray:40 26;animation:flow 4s linear infinite}}
@keyframes flow{{to{{stroke-dashoffset:-660}}}}
"""
    b = [card(W, H, 24),
         f'<defs><linearGradient id="lgf" x1="0" x2="1"><stop offset="0" stop-color="{C["cyan"]}"/><stop offset="1" stop-color="{C["primary"]}"/></linearGradient></defs>',
         sprite("mug", 4, cx - 152, 30),
         f'<g class="steam" shape-rendering="crispEdges"><rect x="{cx - 146}" y="20" width="4" height="4" fill="#c4c4d0"/>'
         f'<rect x="{cx - 138}" y="16" width="4" height="4" fill="#c4c4d0"/><rect x="{cx - 130}" y="20" width="4" height="4" fill="#c4c4d0"/></g>',
         f'<text class="op" x="{cx - 98}" y="54" text-anchor="middle">+</text>',
         f'<g class="beat">{sprite("heart_s", 4, cx - 78, 34)}</g>',
         f'<text class="op" x="{cx - 20}" y="54" text-anchor="middle">=</text>',
         f'<path d="{inf}" fill="none" stroke="{C["blue50"]}" stroke-width="10"/><path class="flow" pathLength="660" d="{inf}"/>',
         f'<text class="t" x="{W / 2}" y="104" text-anchor="middle">{T(FOOTER)} · <tspan class="s">{T(SITE)}</tspan></text>']
    write("footer.svg", svg(W, H, f"{FOOTER} · {SITE}", "\n".join(b), css))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name in os.listdir(OUT):
        if name.endswith(".svg"):
            os.remove(os.path.join(OUT, name))
    hero()
    desk()
    what()
    footer()
