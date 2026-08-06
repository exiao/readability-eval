"""Generate results/chart.svg from results/*.json.

    python3 -m readability_eval.chart
"""
import glob
import json
import os
from statistics import mean

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


def load(condition="default", limit=None):
    """Summary rows per model.

    With `limit`, every model is re-scored over just its first `limit` prompts
    instead of using the stored summary. The full run is 30 prompts for some
    models and 5 for others, and plotting both on one axis compares different
    tests: a model that answered 5 easy prompts sits next to one that answered
    30, and the bar chart says nothing about the difference. Pass limit=5 for a
    like-for-like chart across every model.
    """
    out = []
    for f in glob.glob(os.path.join(ROOT, "results", "*.json")):
        d = json.load(open(f))
        s = d["summary"]
        if s.get("condition", "default") != condition:
            continue
        if limit is None:
            out.append({"model": s["model"], "score": s["score"],
                        "words": s["avg_words"],
                        "economy": s["per_rule"]["rule2_economy"],
                        "slop": s["slop_per_1k"], "n": s["n"]})
            continue
        runs = [r for r in d["runs"] if r.get("response") and r["id"] <= limit]
        if len(runs) < limit:
            continue                      # cannot compare on a short run
        out.append({
            "model": s["model"],
            "score": round(mean(r["score"] for r in runs), 1),
            "words": round(mean(len(r["response"].split()) for r in runs)),
            "economy": round(mean(r["rules"]["rule2_economy"] for r in runs), 1),
            "slop": round(mean(r["slop_per_1k"] for r in runs), 1),
            "n": len(runs),
        })
    return sorted(out, key=lambda r: -r["score"])


def axis_floor(rows):
    """Lowest multiple of 5 that clears the worst score, capped at 80."""
    return min(80, int(min(r["score"] for r in rows) // 5 * 5) - 5)


def bars(rows, x0, y0, w, row_h):
    """Score bars. Zero-baseline would compress the field into nothing, so the
    axis starts below the lowest score and the label says where.

    The floor was hardcoded to 80, which broke the moment a model scored under
    it: rule 7 dropped grok to 77.0 and it rendered as a 2px sliver. Derive it.
    """
    lo, hi = axis_floor(rows), 100
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
<text x="40" y="72" fill="{MUTED}" font-size="14">clarity x (1 - slop tax) · axis starts at {axis_floor(rows)}</text>
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
    import sys
    # --limit N re-scores every model over its first N prompts, so models with
    # different run lengths are comparable on one axis.
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    rows = load(limit=limit)
    name = "chart.svg" if limit is None else f"chart-n{limit}.svg"
    out = os.path.join(ROOT, "results", name)
    with open(out, "w") as f:
        f.write(build(rows))
    ns = sorted({r["n"] for r in rows})
    note = f"n={ns[0]}" if len(ns) == 1 else f"MIXED n={ns} (use --limit)"
    print(f"-> {out}  ({len(rows)} models, {note})")
