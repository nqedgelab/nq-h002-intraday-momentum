"""H-002: intraday momentum, first half hour to last half hour. Rules are in
hypothesis.md and must not change here.

Usage: python backtest/h002.py in_sample
"""

import sys
from datetime import time
from pathlib import Path

import numpy as np
import pandas as pd

from nqlab import data

SIGNAL_BAR = time(9, 59)     # its close is the 10:00 price
ENTRY_BAR = time(15, 30)     # entry at its open
EXIT_BAR = time(15, 59)      # exit at its close
MAX_GAP_DAYS = 4             # previous session at most this many calendar days back

TICK = 0.25
COMMISSION = 0.25       # points per round trip ($2.50 per side at $20/point)
SLIP_ENTRY = 1 * TICK
SLIP_EXIT = 1 * TICK
COST = COMMISSION + SLIP_ENTRY + SLIP_EXIT

# Which years of files each split needs. The first session of a split needs the
# previous year's last close, so one extra year is loaded and then cut off.
SPLIT_YEARS = {
    "in_sample": range(2015, 2022),
    "validation": range(2021, 2024),
    "holdout": range(2023, 2026),
}


def bar_value(day: pd.DataFrame, at: time, column: str):
    hit = day[day.index.time == at]
    return hit[column].iloc[0] if len(hit) else np.nan


def summarize_session(day: pd.DataFrame) -> dict:
    """The prices one regular-hours session contributes, whether or not it trades."""
    return {
        "session": day["session"].iloc[0],
        "close": day["close"].iloc[-1],
        "signal_close": bar_value(day, SIGNAL_BAR, "close"),
        "entry": bar_value(day, ENTRY_BAR, "open"),
        "exit": bar_value(day, EXIT_BAR, "close"),
        "range_pct": (day["high"].max() - day["low"].min()) / day["close"].iloc[-1],
        "roll_window": bool(day["roll_window"].iloc[0]),
    }


def make_trades(sessions: pd.DataFrame) -> pd.DataFrame:
    """Apply the rules to one row per session, in date order."""
    s = sessions.sort_values("session").reset_index(drop=True)
    s["prev_close"] = s["close"].shift(1)
    s["prev_session"] = s["session"].shift(1)
    s["prev_roll"] = s["roll_window"].shift(1, fill_value=True)
    gap = (pd.to_datetime(s["session"]) - pd.to_datetime(s["prev_session"])).dt.days
    s["r1"] = s["signal_close"] / s["prev_close"] - 1

    # Context for the breakdowns, from the previous 20 sessions only.
    s["r1_ratio"] = s["r1"].abs() / s["r1"].abs().rolling(20, min_periods=20).median().shift(1)
    s["vol_prior"] = s["range_pct"].rolling(20, min_periods=20).mean().shift(1)

    ok = (
        s["prev_close"].notna() & (gap <= MAX_GAP_DAYS)
        & s["signal_close"].notna() & s["entry"].notna() & s["exit"].notna()
        & ~s["roll_window"] & ~s["prev_roll"].astype(bool)
        & (s["r1"] != 0)
    )
    t = s[ok].copy()
    t["side"] = np.sign(t["r1"]).astype(int)
    t["gross_points"] = (t["exit"] - t["entry"]) * t["side"]
    t["cost_points"] = COST
    t["bp"] = (t["gross_points"] - COST) / t["entry"] * 1e4
    t["gross_bp"] = t["gross_points"] / t["entry"] * 1e4
    t["long_bp"] = (t["exit"] - t["entry"] - COST) / t["entry"] * 1e4   # always-long benchmark
    return t.drop(columns=["prev_session", "prev_roll"]).reset_index(drop=True)


def run(bars: pd.DataFrame) -> pd.DataFrame:
    rth = bars[bars["rth"]]
    sessions = pd.DataFrame([summarize_session(day) for _, day in rth.groupby("session", sort=True)])
    return make_trades(sessions)


def summarize(x: np.ndarray, seed: int = 1) -> dict:
    rng = np.random.default_rng(seed)
    boots = rng.choice(x, size=(10_000, len(x)), replace=True).mean(axis=1)
    equity = np.cumsum(x)
    drawdown = np.max(np.maximum.accumulate(np.concatenate([[0], equity]))[1:] - equity)
    wins, losses = x[x > 0], x[x <= 0]
    return {
        "trades": len(x),
        "win_rate": len(wins) / len(x),
        "avg_win_bp": wins.mean() if len(wins) else 0.0,
        "avg_loss_bp": -losses.mean() if len(losses) else 0.0,
        "expectancy_bp": x.mean(),
        "ci_low": np.percentile(boots, 2.5),
        "ci_high": np.percentile(boots, 97.5),
        "max_drawdown_bp": drawdown,
        "expectancy_without_top10": np.sort(x)[:-10].mean() if len(x) > 10 else np.nan,
        "total_bp": x.sum(),
    }


def report(trades: pd.DataFrame) -> str:
    def row(name, sub):
        s = summarize(sub["bp"].to_numpy())
        return (f"| {name} | {s['trades']} | {s['win_rate']:.1%} | {s['avg_win_bp']:.1f} | "
                f"{s['avg_loss_bp']:.1f} | {s['expectancy_bp']:+.2f} | "
                f"[{s['ci_low']:+.2f}, {s['ci_high']:+.2f}] | {sub['long_bp'].mean():+.2f} |")

    def terciles(column, labels):
        w = trades.dropna(subset=[column])
        cuts = w[column].quantile([1 / 3, 2 / 3]).to_numpy()
        return [row(labels[0], w[w[column] <= cuts[0]]),
                row(labels[1], w[(w[column] > cuts[0]) & (w[column] <= cuts[1])]),
                row(labels[2], w[w[column] > cuts[1]])]

    lines = ["| Group | Trades | Win rate | Avg win bp | Avg loss bp | Expectancy bp | 95% CI | Always long bp |",
             "|:---|---:|---:|---:|---:|---:|:---:|---:|", row("All", trades),
             row("Long", trades[trades.side == 1]), row("Short", trades[trades.side == -1])]
    years = pd.to_datetime(trades["session"]).dt.year
    for y in sorted(years.unique()):
        lines.append(row(str(y), trades[years == y]))
    lines.append(row("Before publication (to 2018)", trades[years <= 2018]))
    lines.append(row("After publication (2019 on)", trades[years >= 2019]))
    lines += terciles("r1_ratio", ["Small first move", "Middle first move", "Large first move"])
    lines += terciles("vol_prior", ["Low volatility", "Middle volatility", "High volatility"])
    return "\n".join(lines)


def main(split_name: str) -> None:
    bars = data.load(years=SPLIT_YEARS[split_name])
    trades = run(bars)
    first, last = data.SPLITS[split_name]
    day = pd.to_datetime(trades["session"])
    trades = trades[(day >= pd.Timestamp(first)) & (day <= pd.Timestamp(last))].reset_index(drop=True)
    out = Path(__file__).resolve().parent / f"trades_{split_name}.csv"
    trades.to_csv(out, index=False)

    s = summarize(trades["bp"].to_numpy())
    print(f"split: {split_name}  trades: {len(trades)}")
    for k, v in s.items():
        print(f"{k:>26}: {v:.4f}" if isinstance(v, float) else f"{k:>26}: {v}")
    print(f"{'expectancy_before_costs':>26}: {trades['gross_bp'].mean():.4f}")
    print(f"{'always_long_bp':>26}: {trades['long_bp'].mean():.4f}")
    print(f"{'beats_always_long':>26}: {trades['bp'].mean() > trades['long_bp'].mean()}")
    print(f"{'expectancy_points':>26}: {(trades['gross_points'] - COST).mean():.4f}")
    print(f"{'median_cost_bp':>26}: {(COST / trades['entry'] * 1e4).median():.4f}")
    print(f"{'long_share':>26}: {(trades['side'] == 1).mean():.4f}")
    print()
    print(report(trades))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "in_sample")
