# H-002 results: intraday momentum, first half hour to last half hour

**Verdict: rejected at step 1 (in sample).** Validation and holdout data were not used, so they stay unseen for future hypotheses.

Run on 2026-10-29 with `python backtest/h002.py in_sample`. The rules are exactly those committed in [`hypothesis.md`](hypothesis.md) before this run, and the rule logic is unit-tested in [`backtest/test_h002.py`](backtest/test_h002.py).

## In sample, 2015–2021, after costs

| Measure | Value |
|:---|---:|
| Sessions | 1,807 |
| Trades | 1,520 |
| Long / short | 55% / 45% |
| Win rate | 47.3% |
| Average win | 19.3 bp |
| Average loss | 18.8 bp |
| **Expectancy** | **−0.80 bp** |
| 95% bootstrap CI | −2.36 bp to +0.83 bp |
| Expectancy in points | −0.94 points ($−19 per contract) |
| Expectancy without the 10 best trades | −2.01 bp |
| Expectancy before costs | +0.34 bp |
| Always-long benchmark, after costs | −1.98 bp |
| Median cost per trade | 1.09 bp |
| Max drawdown | 1,611 bp |
| Total | −1,217 bp |

Step 1 needed expectancy > 0 bp with the lower confidence bound > 0 bp. Neither holds, so the hypothesis is rejected. Step 2, beating always-long, would have passed (−0.80 bp vs −1.98 bp), but it only matters if step 1 passes.

The signal was checked before writing this up. The largest first-half-hour moves are real market days (2020-03-09, 2015-08-24, 2020-03-24), not contract-roll jumps.

## What the numbers say

- **The signal barely predicts anything.** The 10:00 return and the 15:30–16:00 return have a correlation of 0.02, and the direction was right on 50.5% of days. Before costs that's +0.34 bp a trade, well inside noise.
- **Costs are the same size as the effect.** A round trip costs about 1.1 bp. Even if the +0.34 bp were real, costs would take three times that.
- **The last half hour drifted down, not up.** Always-long lost 1.98 bp a trade after costs, about −0.9 bp before them. Beating that benchmark here meant only "losing less than buying". This is the opposite of the full-day drift H-001 ran into.
- **No sign of the published effect on NQ in these years.** The paper found it on SPY with a different close. Before publication (2015–2018) the result was −1.06 bp, so this isn't a story of an edge that decayed once it was known. It wasn't there to begin with on this instrument and window.

## Breakdown (reported, not used to rescue the result)

| Group | Trades | Win rate | Avg win bp | Avg loss bp | Expectancy bp | 95% CI | Always long bp |
|:---|---:|---:|---:|---:|---:|:---:|---:|
| All | 1520 | 47.3% | 19.3 | 18.8 | −0.80 | [−2.36, +0.83] | −1.98 |
| Long | 833 | 48.5% | 16.7 | 18.8 | −1.56 | [−3.44, +0.38] | −1.56 |
| Short | 687 | 45.9% | 22.6 | 18.9 | +0.12 | [−2.47, +2.82] | −2.48 |
| 2015 | 217 | 43.3% | 17.7 | 16.5 | −1.69 | [−5.39, +1.90] | −1.74 |
| 2016 | 218 | 45.9% | 12.8 | 15.7 | −2.64 | [−5.43, +0.05] | −0.90 |
| 2017 | 214 | 43.0% | 9.2 | 10.0 | −1.72 | [−3.40, −0.06] | −1.57 |
| 2018 | 217 | 50.7% | 25.4 | 22.4 | +1.82 | [−3.21, +6.99] | −4.58 |
| 2019 | 217 | 52.1% | 13.4 | 15.8 | −0.61 | [−3.33, +1.98] | −0.41 |
| 2020 | 218 | 51.8% | 38.4 | 33.2 | +3.94 | [−3.32, +11.34] | −1.69 |
| 2021 | 219 | 44.3% | 14.7 | 20.1 | −4.69 | [−7.89, −1.42] | −2.94 |
| Before publication (to 2018) | 866 | 45.7% | 16.6 | 16.0 | −1.06 | [−2.82, +0.73] | −2.20 |
| After publication (2019 on) | 654 | 49.4% | 22.6 | 22.9 | −0.46 | [−3.26, +2.39] | −1.69 |
| Small first move | 500 | 52.8% | 16.1 | 15.7 | +1.09 | [−1.08, +3.37] | −2.28 |
| Middle first move | 500 | 46.2% | 19.1 | 15.1 | +0.71 | [−1.68, +3.26] | −0.51 |
| Large first move | 501 | 43.3% | 22.9 | 24.9 | −4.21 | [−7.66, −0.84] | −2.73 |
| Low volatility | 501 | 45.9% | 11.1 | 12.3 | −1.55 | [−3.06, +0.10] | −1.35 |
| Middle volatility | 500 | 44.6% | 13.5 | 15.6 | −2.61 | [−4.43, −0.76] | −1.87 |
| High volatility | 501 | 51.7% | 31.2 | 30.0 | +1.65 | [−2.38, +5.71] | −2.39 |

**No group has a confidence interval entirely above zero.** Four groups sit entirely below it (2017, 2021, large first moves, middle volatility). With 18 groups, a few should cross zero by chance.

**The large-first-move result points the wrong way for the paper.** The idea says a strong first half hour should carry into the close. Here the biggest first moves did worst, at −4.21 bp. That hints at reversal, not momentum. It's suggested by this very data, so it isn't evidence of anything yet.

**Don't mine this table.** "High volatility only", "2020-style years" or "fade large first moves" are ideas suggested by this data. Testing any of them on the same in-sample period would be circular. If one becomes a new hypothesis, its first honest test is the validation period, and it must be written down before that test.
