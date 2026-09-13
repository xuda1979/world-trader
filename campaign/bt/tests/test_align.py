"""TDD tests for bt.align — PIT-safe weekly-signal -> daily-session mapping.

Background (DATA_COTMORE r2 charter item c): every COT hunt agent re-implements the
weekly->daily join (HUNT_COT2 r1 found 4 bugs there, the searchsorted duplicate-index
crash chief among them; HUNT_CIT_AG hand-rolls reindex+ffill with a naive +3d shift that
lands positions on non-sessions and holds them over weekends). One audited helper, used
everywhere:

    align.py — as-of joins that are NEVER early.

Semantics locked by these tests:
- A signal known on date D becomes tradable at the FIRST SESSION STRICTLY AFTER D when
  after=True (release-session close not yet public => next-session entry; PIT-correct for
  CFTC Tue report + 3d publication lag: first P&L is the session after that).
- after=False: first session on/after D (release-session close itself).
- Sessions the price calendar lacks (holidays) snap LATER, never earlier.
- Several signals landing on the same first session: the LATEST signal wins (newest info).
- Signal dates BEFORE the first price session: dropped (not snapped onto session 0 in a
  way that duplicates the index) — the first tradable session carries the newest signal.
- Output index == prices index exactly (no duplicates, no extras), values ffill between
  signal dates, 0.0 before the first tradable session.
"""
import numpy as np
import pandas as pd
import pytest

from bt import align


def _px(dates):
    s = pd.Series(np.arange(len(dates), dtype=float) + 100.0,
                  index=pd.DatetimeIndex(dates))
    return s


WED = pd.Timestamp("2024-01-03")   # Wed
THU = pd.Timestamp("2024-01-04")
FRI = pd.Timestamp("2024-01-05")
SAT = pd.Timestamp("2024-01-06")
MON = pd.Timestamp("2024-01-08")
TUE = pd.Timestamp("2024-01-09")


def test_basic_next_session_entry():
    """after=True: Friday-release signal -> first tradable close is Monday."""
    px = _px([THU, FRI, MON, TUE])
    sig = pd.Series({"2024-01-05": 1.0})          # released Friday
    pos = align.signal_to_sessions(sig, px, after=True)
    assert list(pos.index) == list(px.index)      # output index == price index exactly
    assert pos.loc[FRI] == 0.0                    # release close: not yet tradable
    assert pos.loc[MON] == 1.0                    # next session: tradable
    assert pos.loc[TUE] == 1.0                    # ffill holds


def test_same_session_entry_when_after_false():
    px = _px([THU, FRI, MON, TUE])
    sig = pd.Series({"2024-01-05": 1.0})
    pos = align.signal_to_sessions(sig, px, after=False)
    assert pos.loc[FRI] == 1.0                    # release-session close itself
    assert pos.loc[MON] == 1.0


def test_holiday_snaps_later_never_earlier():
    """Friday release, Monday holiday -> next AVAILABLE session is Tuesday (no early snap)."""
    px = _px([THU, FRI, TUE])                     # Mon missing = holiday
    sig = pd.Series({"2024-01-05": 1.0})
    pos = align.signal_to_sessions(sig, px, after=True)
    assert pos.loc[TUE] == 1.0
    assert (pos.loc[:FRI] == 0.0).all()


def test_keep_last_on_same_session_collision():
    """Two weekend knowledge-dates (Sat+Sun releases) snap to the same next session: newest
    wins. (Original fixture used Mon/Tue sessions — they don't collide; a TUE-dated signal
    live at the TUE close also contradicts after=True semantics, i.e. lookahead. The real
    collision case is holiday/weekend pairs snapping together, per the module docstring.)"""
    px = _px([THU, FRI, MON, TUE])
    sig = pd.Series([0.1, 0.2], index=[SAT, pd.Timestamp("2024-01-07")])  # Sat then Sun release
    pos = align.signal_to_sessions(sig, px, after=True)
    assert pos.loc[MON] == 0.2                    # the later signal is live at that session


def test_signals_before_price_history_dropped_not_duplicated():
    """THE r1 bug: signal dates before the first price session all searchsorted to index
    position 0 -> duplicate index labels -> 'cannot reindex on duplicate labels' crash.
    Here: newest pre-history signal is live at the FIRST session; earlier ones discarded."""
    px = _px([MON, TUE])
    sig = pd.Series([0.1, 0.2, 0.3],
                    index=[pd.Timestamp("2023-12-01"), pd.Timestamp("2023-12-08"),
                           pd.Timestamp("2023-12-15")])       # all before 2024-01-08
    pos = align.signal_to_sessions(sig, px, after=True)
    assert list(pos.index) == list(px.index)      # would crash under the r1 bug
    assert pos.iloc[0] == 0.3                     # newest pre-history signal live at session 0
    assert (pos == 0.3).all()                     # and held forward


def test_zero_before_first_tradable_session():
    px = _px([THU, FRI, MON, TUE])
    sig = pd.Series([1.0], index=[MON])
    pos = align.signal_to_sessions(sig, px, after=True)
    assert (pos.loc[[THU, FRI]] == 0.0).all()
    assert pos.loc[TUE] == 1.0
    assert pos.loc[MON] == 0.0                    # after=True: Tue is first STRICTLY-after
