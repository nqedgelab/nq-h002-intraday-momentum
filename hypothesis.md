# H-002: intraday momentum, first half hour to last half hour

- **Status:** untested <!-- untested | testing | supported | rejected | inconclusive -->
- **Written:** 2026-10-29 (before any testing)

No return from the 10:00 or 15:30–16:00 windows has been looked at. The in-sample years were already used once, for H-001's full-day trades, so their broad shape is known: it was mostly a rising market. Validation and holdout are still untouched.

## Claim
On NQ, the return from the previous session's 16:00 ET close to 10:00 ET today predicts the sign of the 15:30–16:00 ET return. Trading the last half hour in that direction has positive expectancy after costs, and it beats simply buying the last half hour every day.

## Why it might work
The idea comes from outside this project. Gao, Han, Li and Zhou ("Market Intraday Momentum", *Journal of Financial Economics*, 2018) reported it on SPY. That makes this an out-of-sample test of someone else's claim on a different instrument, not a pattern found in our own data.

Their proposed mechanisms:
- **Late-informed traders.** Some news is absorbed overnight and in the first half hour. Slower traders act on it near the close.
- **Hedging flows.** Option dealers who are short gamma hedge in the direction of the day's move, and much of that hedging happens late in the session.
- **Rebalancing.** Leveraged ETFs rebalance near the close in the direction of the day's return.

The other side is liquidity providers and anyone who needs to trade at the close regardless of price.

**The case against.**
- **Decay after publication.** Many published anomalies shrink once they're known. The paper came out in 2018, inside our in-sample period. A pass in sample followed by a fail in validation would fit that story.
- **A few big days.** The paper found the effect strongest on volatile days and in crises. If March 2020 carries the average, it won't survive the "without the top 10 trades" check.
- **Costs against a small move.** A 30-minute move is small next to a full-day trade. A round trip costs 0.75 points here, which could eat the whole effect.
- **A different close.** SPY closes at 16:00, when closing auctions concentrate flow. NQ keeps trading until 17:00, so its last half hour before 16:00 may behave differently.
- **Drift.** In a rising market, a rule that is long more often than short can look good just by being long. That's why it must also beat always-long.

**The most likely outcome is that it fails, either through costs or through decay.**

## Rules
All times New York (ET). Bars come from `nqlab.data.load()`, which drops sessions with broken data.

1. **Previous close.** The close of the last regular-hours bar of the most recent earlier session in the data. If that session is more than 4 calendar days earlier, skip the day; a dropped session would otherwise make r1 span two days. Four days covers a weekend plus a holiday.
2. **Signal return.** r1 = (close of the 09:59 bar) / (previous close) − 1. Skip the day if the 09:59 bar is missing. If r1 is exactly 0, there's no trade.
3. **Direction.** Long if r1 > 0, short if r1 < 0.
4. **Entry.** At the open of the 15:30 bar. Skip the day if the 15:30 bar is missing, which also skips early-close days.
5. **Exit.** At the close of the 15:59 bar. Skip the day if the 15:59 bar is missing. There's no stop and no target; the time exit is the only exit.
6. **Contract rolls.** Skip the day if today or the previous session is in `roll_window`. Prices aren't back-adjusted, so r1 could include the jump between contracts.
7. **Size.** 1 contract, fixed. At most one trade per day.
8. **No filters.** There's no volatility filter, threshold on r1, day-of-week rule or second signal window. The paper's variants, such as adding the 15:00–15:30 return as a second signal, are separate hypotheses.

## Measurement
- **Unit.** There's no stop, so R isn't defined. Each trade is measured in **basis points of the entry price**, after costs. A point is worth far more at 4,000 than at 16,000, so basis points keep the early and late years on equal terms.
- **Benchmark.** Always-long uses the same days, the same entry and exit, and the same costs. The strategy has to beat it, not just zero.

## Falsification
H-002 is **rejected** if any of these holds, checked in order:

1. In sample (2015–2021), expectancy after costs is ≤ 0 bp, or the lower bound of its 95% bootstrap confidence interval is ≤ 0 bp.
2. In sample, expectancy after costs is ≤ the always-long benchmark's expectancy after costs on the same days.
3. Validation (2022–2023, looked at once), expectancy after costs is ≤ 0 bp.
4. Holdout (2024 onward, looked at once, only if 1–3 pass), expectancy after costs is ≤ 0 bp.

It's **supported** only if all four pass. It's **inconclusive** if any period has fewer than the minimum number of trades below.

A result that depends on a handful of days is fragile even if it passes. The test reports expectancy with the 10 best trades removed. If that turns negative, the verdict says so.

## Test plan
- **Data period.** The fixed splits in `nqlab/data.py`: in sample 2015–2021, validation 2022–2023, holdout 2024 to Jul 2025. Rules are frozen at this commit and can't be changed after seeing any result.
- **Minimum sample size.** 300 trades in sample and 100 each in validation and holdout. Skipping roll windows leaves roughly 85% of sessions, so all three should be met easily.
- **Costs assumed.**
  - Commission and fees: $2.50 per side, or 0.25 points per round trip ($20 per point).
  - Slippage: 1 tick (0.25 points) on entry and 1 tick on exit.
  - That's 0.75 points per round trip, charged in points and converted to basis points of the entry price.
- **Regimes to check separately** (reported, not used to rescue a failed result):
  - longs vs shorts;
  - each calendar year;
  - before and after publication (2015–2018 vs 2019–2021);
  - |r1| tercile, measured against the previous 20 sessions;
  - volatility tercile, using the previous 20 sessions' average daily range.
- **Reported:** trade count, win rate, average win and loss in bp, expectancy in bp and in points, its bootstrap 95% CI, max drawdown in bp, expectancy without the top 10 trades, and the always-long benchmark.

## Result
Filled in after testing.
