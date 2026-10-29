import numpy as np
import pandas as pd
import pytest

import h002


def day(session="2024-07-02", signal=100.0, entry=100.0, exit=100.0, close=None,
        roll=False, drop=()):
    """Build a full RTH session of flat bars at 100, with the rule bars set."""
    index = pd.date_range(f"{session} 09:30", f"{session} 15:59", freq="min",
                          tz="America/New_York")
    df = pd.DataFrame({"open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0}, index=index)
    df.loc[index.time == h002.SIGNAL_BAR, "close"] = signal
    df.loc[index.time == h002.ENTRY_BAR, "open"] = entry
    df.loc[index.time == h002.EXIT_BAR, "close"] = exit if close is None else close
    df["volume"] = 10
    df["session"] = pd.Timestamp(session).date()
    df["rth"] = True
    df["roll_window"] = roll
    for t in drop:
        df = df[df.index.time != t]
    return df


def trades(*days):
    return h002.make_trades(pd.DataFrame([h002.summarize_session(d) for d in days]))


def prev(**kw):
    return day(session="2024-07-01", **kw)


def test_up_first_half_hour_goes_long_and_exits_at_1559_close():
    t = trades(prev(), day(signal=101, entry=102, exit=104))
    assert len(t) == 1
    row = t.iloc[0]
    assert (row.side, row.entry, row.exit) == (1, 102, 104)
    assert row.r1 == pytest.approx(0.01)        # 10:00 price 101 vs previous close 100
    assert row.bp == pytest.approx((2 - h002.COST) / 102 * 1e4)


def test_down_first_half_hour_goes_short():
    row = trades(prev(), day(signal=99, entry=98, exit=97)).iloc[0]
    assert row.side == -1
    assert row.gross_points == 1
    assert row.long_bp == pytest.approx((-1 - h002.COST) / 98 * 1e4)


def test_previous_close_is_last_rth_bar():
    row = trades(prev(close=200), day(signal=202, entry=100, exit=100)).iloc[0]
    assert row.prev_close == 200 and row.r1 == pytest.approx(0.01)


def test_flat_first_half_hour_means_no_trade():
    assert trades(prev(), day(signal=100)).empty


def test_missing_rule_bars_skip_the_day():
    for bar in (h002.SIGNAL_BAR, h002.ENTRY_BAR, h002.EXIT_BAR):
        assert trades(prev(), day(signal=101, drop=[bar])).empty


def test_early_close_day_is_skipped():
    early = day(signal=101)
    early = early[early.index.time < pd.Timestamp("13:00").time()]
    assert trades(prev(), early).empty


def test_previous_session_too_far_back_skips_the_day():
    old = day(session="2024-06-26")                       # 6 days earlier
    assert trades(old, day(signal=101)).empty
    weekend_holiday = day(session="2024-06-28")           # Friday to Tuesday, 4 days
    assert len(trades(weekend_holiday, day(signal=101))) == 1


def test_roll_window_today_or_yesterday_skips_the_day():
    assert trades(prev(), day(signal=101, roll=True)).empty
    assert trades(prev(roll=True), day(signal=101)).empty


def test_first_session_has_no_previous_close():
    assert trades(day(signal=101)).empty


def test_one_trade_per_day_and_no_other_exit():
    swing = day(signal=101, entry=100, exit=100)
    swing.loc[swing.index.time == pd.Timestamp("15:45").time(), ["high", "low"]] = [150, 50]
    t = trades(prev(), swing)
    assert len(t) == 1 and t.iloc[0].exit == 100        # no stop or target fired
    assert np.isclose(t.iloc[0].gross_points, 0)
