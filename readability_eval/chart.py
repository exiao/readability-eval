"""Generate results/chart.svg from results/*.json.

    python3 -m readability_eval.chart
"""
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG, FG, MUTED, GRID = "#0f1115", "#ffffff", "#8b93a1", "#2b3240"
BAR, BAR_TOP, DOT = "#3b82f6", "#4ade80", "#f87171"

W = 900
# Layout is derived, not hardcoded: an early version put tick labels at y=740
# on a 730px canvas and they silently vanished. Everything below flows from
# these constants.
BAR_TOP_Y, ROW_H = 100, 40
SCATTER_H = 240


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def load(condition="default"):
    out = []
    for f in glob.glob(os.path.join(ROOT, "results", "*.json")):
        s = json.load(open(f))["summary"]
        if s.get("condition", "default") != condition:
            continue
        out.append({"model": s["model"], "score": s["score"],
                    "words": s["avg_words"],
                    "economy": s["per_rule"]["rule2_economy"],
                    "slop": s["slop_per_1k"]})
    return sorted(out, key=lambda r: -r["score"])


def bars(rows, x0, y0, w, row_h):
    """Score bars. Zero-baseline would compress 87-95 into nothing, so the
    axis starts at 80 and the label says so."""
    lo, hi = 80, 100
    out = []
    for i, r in enumerate(rows):
        y = y0 + i * row_h
        frac = (r["score"] - lo) / (hi - lo)
        bw = max(2, frac * w)
        c = BAR_TOP if i == 0 else BAR
        out.append(f'<text x="{x0 - 12}" y="{y + 17}" fill="{FG}" font-size="14" '
                   f'text-anchor="end">{esc(r["model"])}</text>')
        out.append(f'<rect x="{x0}" y="{y}" width="{bw:.0f}" height="24" rx="3" fill="{c}"/>')
        out.append(f'<text x="{x0 + bw + 10:.0f}" y="{y + 17}" fill="{FG}" '
                   f'font-size="14" font-weight="700">{r["score"]}</text>')
    return "\n".join(out)


def scatter(rows, x0, y0, w, h):
    """Words vs economy. The whole story of the eval."""
    xs = [r["words"] for r in rows]
    ys = [r["economy"] for r in rows]
    xlo, xhi = 0, max(xs) * 1.15
    ylo, yhi = min(ys) - 1.8, max(ys) + 1.0
    out = []

    for t in range(0, int(xhi) + 1, 50):
        px = x0 + (t - xlo) / (xhi - xlo) * w
        out.append(f'<line x1="{px:.0f}" y1="{y0}" x2="{px:.0f}" y2="{y0 + h}" '
                   f'stroke="{GRID}" stroke-width="1"/>')
        out.append(f'<text x="{px:.0f}" y="{y0 + h + 20}" fill="{MUTED}" '
                   f'font-size="12" text-anchor="middle">{t}</text>')

    placed = []   # (px, py) of labels already drawn
    for r in rows:
        px = x0 + (r["words"] - xlo) / (xhi - xlo) * w
        py = y0 + h - (r["economy"] - ylo) / (yhi - ylo) * h
        short = r["model"].split("/")[-1]
        out.append(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="7" fill="{DOT}"/>')

        anchor, dx = ("end", -13) if r["words"] > 140 else ("start", 13)
        ly = py + 5
        # Nudge vertically when a previous label sits within one line height.
        # kimi-k3 and claude-fable-5 land 6px apart and overprint otherwise.
        for qx, qy in placed:
            if abs(px - qx) < 150 and abs(ly - qy) < 16:
                ly = qy + 18
        placed.append((px, ly))
        # A nudged label loses its dot; draw a faint leader so it stays readable.
        if abs(ly - (py + 5)) > 6:
            out.append(f'<line x1="{px:.0f}" y1="{py + 7:.0f}" x2="{px + dx * 0.5:.0f}" '
                       f'y2="{ly - 4:.0f}" stroke="{MUTED}" stroke-width="1" opacity="0.5"/>')
        out.append(f'<text x="{px + dx:.0f}" y="{ly:.0f}" fill="{FG}" '
                   f'font-size="13" text-anchor="{anchor}">{esc(short)}</text>')
    return "\n".join(out)


def build(rows):
    divider = BAR_TOP_Y + len(rows) * ROW_H + 40
    sc_y = divider + 100                 # top of scatter plot area
    tick_y = sc_y + SCATTER_H + 20       # tick numbers sit below the plot
    axis_y = tick_y + 26                 # axis title below the ticks
    h = axis_y + 24                      # canvas ends below everything
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="Helvetica,Arial,sans-serif">
<rect width="{W}" height="{h}" fill="{BG}"/>

<text x="40" y="48" fill="{FG}" font-size="22" font-weight="700">Readability score</text>
<text x="40" y="72" fill="{MUTED}" font-size="14">clarity x (1 - slop tax) · axis starts at 80</text>
{bars(rows, 210, BAR_TOP_Y, 560, ROW_H)}

<line x1="40" y1="{divider}" x2="{W - 40}" y2="{divider}" stroke="{GRID}"/>

<text x="40" y="{divider + 50}" fill="{FG}" font-size="22" font-weight="700">Shorter answers score better</text>
<text x="40" y="{divider + 74}" fill="{MUTED}" font-size="14">economy vs average answer length, in words</text>
{scatter(rows, 100, sc_y, 720, SCATTER_H)}
<text x="460" y="{axis_y}" fill="{MUTED}" font-size="13" text-anchor="middle">average words per answer</text>
<text x="34" y="{sc_y + SCATTER_H // 2}" fill="{MUTED}" font-size="13" text-anchor="middle" transform="rotate(-90 34 {sc_y + SCATTER_H // 2})">economy</text>
</svg>
'''


if __name__ == "__main__":
    rows = load()
    out = os.path.join(ROOT, "results", "chart.svg")
    with open(out, "w") as f:
        f.write(build(rows))
    print(f"-> {out}  ({len(rows)} models)")
