"""Genera una batalla espacial animada (SVG) a partir del calendario de contribuciones.

Uso:
    python space_battle.py <usuario> <salida.svg>
    python space_battle.py --demo <salida.svg>      # datos de prueba, sin red
"""
import random
import re
import sys
import urllib.request

COLS, ROWS = 53, 7
CELL, GAP = 12, 3
STEP = CELL + GAP
PAD_X, TOP = 52, 58
W = PAD_X * 2 + COLS * STEP - GAP
SHIP_Y = TOP + ROWS * STEP + 52
H = SHIP_Y + 40
DUR = 22.0  # segundos por ciclo
START, END = 6.0, 84.0  # % del ciclo en que la nave recorre el calendario

LEVEL_FILL = ["#161b2e", "#3b2a6b", "#6d3fd1", "#a855f7", "#22d3ee"]
SANS = "'Segoe UI', -apple-system, Helvetica, Arial, sans-serif"
MONO = "Consolas, 'SFMono-Regular', Menlo, 'DejaVu Sans Mono', monospace"


def fetch(user):
    url = f"https://github.com/users/{user}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "space-battle"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    grid = [[0] * ROWS for _ in range(COLS)]
    cells = re.findall(r'<td[^>]*?id="contribution-day-component-(\d+)-(\d+)"[^>]*?data-level="(\d)"', html)
    if not cells:  # orden de atributos alterno
        cells = [(r, c, l) for l, r, c in re.findall(
            r'<td[^>]*?data-level="(\d)"[^>]*?id="contribution-day-component-(\d+)-(\d+)"', html)]
    for r, c, lvl in cells:
        r, c = int(r), int(c)
        if c < COLS and r < ROWS:
            grid[c][r] = int(lvl)
    m = re.search(r'([\d,]+)\s+contributions?\s+in the last year', html)
    total = m.group(1) if m else str(sum(1 for col in grid for v in col if v))
    return grid, total


def demo():
    rnd = random.Random(7)
    grid = [[(rnd.choice([0, 0, 0, 1, 1, 2, 3, 4]) if rnd.random() < 0.55 else 0) for _ in range(ROWS)] for _ in range(COLS)]
    return grid, "412"


def pct(x):
    return f"{x:.3f}%"


def ship(color_a="#ff3b5c", color_b="#22d3ee"):
    # Nave original: casco en flecha, alas en delta y doble motor.
    return f'''
    <g class="flame"><path d="M-9 13 L-6 26 L-3 13Z" fill="#ffb020"/><path d="M3 13 L6 26 L9 13Z" fill="#ffb020"/>
      <path d="M-8 13 L-6 20 L-4 13Z" fill="#fff6c2"/><path d="M4 13 L6 20 L8 13Z" fill="#fff6c2"/></g>
    <path d="M0 -20 L6 -4 L22 8 L22 13 L7 10 L5 14 L-5 14 L-7 10 L-22 13 L-22 8 L-6 -4Z" fill="#1f2937" stroke="{color_b}" stroke-width="1.6" stroke-linejoin="round"/>
    <path d="M0 -20 L4 -6 L0 2 L-4 -6Z" fill="{color_a}"/>
    <ellipse cx="0" cy="-4" rx="2.6" ry="5" fill="{color_b}" opacity=".9"/>
    <path d="M22 8 L26 2 L24 12Z M-22 8 L-26 2 L-24 12Z" fill="{color_a}"/>'''


def build(grid, total, user):
    rnd = random.Random(42)
    css, body = [], []
    css.append(f"""
  .star {{ fill: #fff; animation: tw 3s ease-in-out infinite; }}
  @keyframes tw {{ 0%,100% {{ opacity:.15 }} 50% {{ opacity:.9 }} }}
  .flame {{ animation: fl .12s linear infinite alternate; transform-origin: 0 13px; }}
  @keyframes fl {{ from {{ transform: scaleY(.7) }} to {{ transform: scaleY(1.15) }} }}
  .ship {{ animation: fly {DUR}s linear infinite; }}
  .cell {{ transform-box: fill-box; transform-origin: center; }}
  .t {{ font: 700 15px {SANS}; fill: #e6edf3; }}
  .s {{ font: 600 12px {MONO}; fill: #8b98ad; }}
""")
    x0 = PAD_X + CELL / 2
    x1 = PAD_X + (COLS - 1) * STEP + CELL / 2
    css.append(f"""  @keyframes fly {{
    0% {{ transform: translate({x0 - 80}px,{SHIP_Y + 60}px); opacity:0 }}
    3% {{ opacity:1 }}
    {pct(START)} {{ transform: translate({x0}px,{SHIP_Y}px) }}
    {pct(END)} {{ transform: translate({x1}px,{SHIP_Y}px) }}
    90% {{ transform: translate({x1 + 90}px,{SHIP_Y - 120}px); opacity:1 }}
    92%,100% {{ transform: translate({x1 + 90}px,{SHIP_Y - 120}px); opacity:0 }}
  }}""")

    # Estrellas
    for _ in range(90):
        x, y = rnd.uniform(4, W - 4), rnd.uniform(4, H - 4)
        body.append(f'<circle class="star" cx="{x:.1f}" cy="{y:.1f}" r="{rnd.choice([.6, .8, 1, 1.3]):.1f}" '
                    f'style="animation-delay:{rnd.uniform(0, 3):.2f}s;animation-duration:{rnd.uniform(2, 5):.1f}s"/>')
    # Planeta decorativo
    body.append(f'<circle cx="{W - 70}" cy="{H - 30}" r="46" fill="url(#planet)" opacity=".55"/>'
                f'<ellipse cx="{W - 70}" cy="{H - 30}" rx="72" ry="12" fill="none" stroke="#a855f7" stroke-opacity=".35" stroke-width="2" transform="rotate(-14 {W - 70} {H - 30})"/>')

    destroyed = 0
    for c in range(COLS):
        p = START + (END - START) * c / (COLS - 1)
        hit = [r for r in range(ROWS) if grid[c][r] > 0]
        cx = PAD_X + c * STEP
        for r in range(ROWS):
            lvl = grid[c][r]
            y = TOP + r * STEP
            if lvl == 0 or not hit:
                body.append(f'<rect x="{cx}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{LEVEL_FILL[0]}"/>')
                continue
            destroyed += 1
            body.append(f'<rect x="{cx}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{LEVEL_FILL[0]}"/>'
                        f'<rect class="cell h{c}" x="{cx}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{LEVEL_FILL[lvl]}"/>'
                        f'<rect class="cell h{c} f{c}" x="{cx}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="#ffffff"/>'
                        f'<circle class="b{c}" cx="{cx + CELL / 2}" cy="{y + CELL / 2}" r="10" fill="none" stroke="#ffd166" stroke-width="2"/>')
        if not hit:
            continue
        top_r = min(hit)
        ly = TOP + top_r * STEP
        a, b, d = p, p + 0.5, p + 1.2
        css.append(f"  .h{c} {{ animation: H{c} {DUR}s linear infinite; }}"
                   f" @keyframes H{c} {{ 0%,{pct(b)} {{ opacity:1; transform:scale(1) }}"
                   f" {pct(b + .25)} {{ opacity:1; transform:scale(1.5) }}"
                   f" {pct(d)},93% {{ opacity:0; transform:scale(.2) }} 98%,100% {{ opacity:1; transform:scale(1) }} }}")
        css.append(f"  .f{c} {{ animation: H{c} {DUR}s linear infinite, F{c} {DUR}s linear infinite; }}"
                   f" @keyframes F{c} {{ 0%,{pct(b)} {{ fill-opacity:0 }} {pct(b + .15)},{pct(b + .4)} {{ fill-opacity:1 }} {pct(d)},100% {{ fill-opacity:0 }} }}")
        css.append(f"  .b{c} {{ opacity:0; transform-box: fill-box; transform-origin:center; animation: B{c} {DUR}s linear infinite; }}"
                   f" @keyframes B{c} {{ 0%,{pct(b)} {{ opacity:0; transform:scale(.1) }} {pct(b + .1)} {{ opacity:1 }}"
                   f" {pct(d + .4)},100% {{ opacity:0; transform:scale(1) }} }}")
        css.append(f"  .l{c} {{ opacity:0; animation: L{c} {DUR}s linear infinite; }}"
                   f" @keyframes L{c} {{ 0%,{pct(a)} {{ opacity:0 }} {pct(a + .05)},{pct(b)} {{ opacity:1 }} {pct(b + .2)},100% {{ opacity:0 }} }}")
        lx = cx + CELL / 2
        body.append(f'<g class="l{c}"><rect x="{lx - 1.5}" y="{ly + CELL / 2}" width="3" height="{SHIP_Y - 20 - ly - CELL / 2}" rx="1.5" fill="url(#laser)"/>'
                    f'<rect x="{lx - 4}" y="{ly + CELL / 2}" width="8" height="{SHIP_Y - 20 - ly - CELL / 2}" rx="4" fill="#22d3ee" opacity=".25"/></g>')

    title = f'<text class="t" x="{PAD_X}" y="34">🚀 {total} contribuciones en el último año</text>'
    sub = f'<text class="s" x="{W - PAD_X}" y="34" text-anchor="end">@{user} · objetivos destruidos: {destroyed}</text>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Batalla espacial de contribuciones de {user}">
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b0f19"/><stop offset="1" stop-color="#140d2b"/></linearGradient>
  <linearGradient id="laser" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#22d3ee"/><stop offset="1" stop-color="#ffffff"/></linearGradient>
  <radialGradient id="planet" cx=".35" cy=".35"><stop offset="0" stop-color="#ff3b5c"/><stop offset="1" stop-color="#3b0a24"/></radialGradient>
  <clipPath id="r"><rect width="{W}" height="{H}" rx="14"/></clipPath>
</defs>
<style>{"".join(css)}
</style>
<g clip-path="url(#r)">
<rect width="{W}" height="{H}" fill="url(#sky)"/>
{"".join(body)}
{title}
{sub}
<g class="ship">{ship()}</g>
</g>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="13" fill="none" stroke="#243049"/>
</svg>'''


if __name__ == "__main__":
    if sys.argv[1] == "--demo":
        grid, total = demo()
        user = "AlexZuniga10"
    else:
        user = sys.argv[1]
        grid, total = fetch(user)
    out = sys.argv[2]
    with open(out, "w", encoding="utf-8") as f:
        f.write(build(grid, total, user))
    print(f"ok: {out} ({total} contribuciones)")
