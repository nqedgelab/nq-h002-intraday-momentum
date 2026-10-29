"""Draw this repo's README artwork. Run from the repo root after a backtest:
python assets/make_assets.py
"""

import csv
import re
from pathlib import Path

from nqlab import art

OUT = Path(__file__).resolve().parent
TRADES = OUT.parent / "backtest" / "trades_in_sample.csv"
SCALE = 10   # art.equity draws in R with a tick every 20; plot tens of bp, relabel as bp

SECTIONS = [
    ("claim", "The idea", "What was claimed, and the exact rules"),
    ("result", "The result", "In sample, 2015–2021, after costs"),
    ("lessons", "What it taught", "Why a rejection is still useful"),
    ("data", "Reproduce it", "Same data, same code, same answer"),
]


def in_bp(svg: str) -> str:
    """Turn the chart's R labels back into basis points."""
    def relabel(m):
        value = float(m.group(1)) * SCALE
        return f">{value:+,.0f} bp<"
    return re.sub(r">([+-]?\d+(?:\.\d+)?)R<", relabel, svg)


def main():
    with TRADES.open(newline="") as f:
        rows = [(r["session"], float(r["bp"]) / SCALE) for r in csv.DictReader(f)]
    for name, t in art.THEMES.items():
        status = (f'Verdict: <tspan fill="{t["bad"]}" font-weight="700">rejected</tspan>'
                  f'<tspan dx="14" fill="{t["sub"]}">·</tspan><tspan dx="14">−0.80 bp per trade after costs</tspan>')
        art.write(OUT, "banner", name, art.banner(
            t, "H-002", "Intraday momentum: first half hour to last half hour", status,
            "nq-h002-intraday-momentum"))
        for num, (slug, title, sub) in enumerate(SECTIONS, 1):
            art.write(OUT, f"section-{slug}", name, art.section(t, num, slug, title, sub))
        art.write(OUT, "equity", name, in_bp(art.equity(
            t, rows, "Cumulative result, in sample",
            f"{len(rows):,} trades, 2015–2021, after costs, measured in basis points of entry price",
            "rejected")))
    print("ok")


if __name__ == "__main__":
    main()
