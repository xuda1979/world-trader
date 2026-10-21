"""bt.align — PIT-safe signal->session mapping (DATA_COTMORE round 2 charter item c).

Every COT hunt agent re-implements the weekly->daily join. HUNT_COT2 r1 found 4 bugs in
those hand-rolled versions; HUNT_CIT_AG's `_apply_cot_lag` still lands positions on
non-sessions and ffills over weekends via a synthetic daily calendar. Use this instead.

The ONE function you need:

    pos = align.signal_to_sessions(sig, prices, after=True)

where `sig` is indexed by SIGNAL-KNOWLEDGE date (for COT: the release date, report+3d —
see bt.align.cot_release_shift) and `prices` is any price series whose DatetimeIndex IS
the trading calendar. Returns a float Series on EXACTLY the price index:

    pos[t] = signal live at close t, where a signal dated D is live from the FIRST
             SESSION STRICTLY AFTER D when after=True (default; the release-session
             close is not yet public knowledge at decision time), or from the first
             session on/after D when after=False. Sessions the calendar lacks (holidays)
             snap LATER, never earlier. Newest signal wins at any shared session.
             0.0 before the first live signal. NO lookahead by construction.

Why the conventions:
- after=True is the PIT-correct default: a signal published ON date D is not knowable at
  D's close (the print lands during/after the session). Combined with the framework's
  lag_signal/shift(1) (decide at t, earn t->t+1), the COT chain is: Tue report -> Fri
  release -> Mon close entry -> first P&L Tue — the c3-audited, charter-headline timing.
- after=False exists for genuinely same-day-close-known signals (e.g. a daily settle
  you treat as known at that close) — borderline, NOT the headline default.
- keep-last on session collisions: if two release dates snap to the same first session
  (holiday-week Mon/Tue report pairs), the newest report is the one live at that close.
- Signals dated before the first price session: the newest one is live at the first
  session, earlier ones discarded — never snapped onto session 0 en masse (the r1 bug).
"""
from __future__ import annotations

import pandas as pd

__all__ = ["signal_to_sessions", "cot_release_shift", "cot_release_shift_series"]


def signal_to_sessions(sig, prices, after=True):
    """Map a signal series to the price calendar, never early.

    sig: pd.Series indexed by signal-knowledge date (any daily/weekly dates).
    prices: pd.Series/DataFrame whose index is the trading calendar (the output index).
    after=True: live from the first session STRICTLY after each signal date (default).
    after=False: live from the first session on/after each signal date.

    Returns pd.Series of float, indexed exactly like prices.index, ffill between signal
    dates, 0.0 before the first live signal.
    """
    s = pd.Series(sig).dropna().sort_index()
    s.index = pd.DatetimeIndex(s.index)
    if len(s) > 1 and not s.index.is_monotonic_increasing:
        raise ValueError("signal index not sortable")   # unreachable after sort; guard typing
    pidx = prices.index
    if not isinstance(pidx, pd.DatetimeIndex):
        raise TypeError("prices.index must be a DatetimeIndex")
    if len(s) == 0:
        return pd.Series(0.0, index=pidx)
    # first session at which each signal is tradable
    side = "right" if after else "left"
    avail = pidx.searchsorted(s.index, side=side)       # LATER snap on missing sessions
    keep = avail < len(pidx)                            # signals with no session after them
    if not keep.all():
        s = s.iloc[keep]
        avail = avail[keep]
    live = pd.Series(s.values, index=pidx[avail])
    # collisions: several signals landing on the same first session -> newest wins
    live = live[~live.index.duplicated(keep="last")]
    out = live.reindex(pidx.union(live.index)).ffill().reindex(pidx).fillna(0.0)
    return out


def cot_release_shift(report_date):
    """CFTC report date (Tue) -> release date (report + 3 calendar days = Friday), the day
    the report is first public on cftc.gov. Pass release dates (not report dates) as the
    signal index into signal_to_sessions. If +3d lands on a non-session the join snaps
    LATER (never earlier) — never early."""
    return pd.to_datetime(report_date) + pd.Timedelta(days=3)


def cot_release_shift_series(sig):
    """Apply cot_release_shift to every index date of a signal series (index -> index+3d).
    Keeps values; sort first if needed."""
    s = pd.Series(sig)
    out = pd.Series(s.values, index=pd.DatetimeIndex([cot_release_shift(d) for d in s.index]))
    return out.sort_index()


def cot_release_shift_series_keep_last(sig):
    """As cot_release_shift_series, then collapse any duplicate release dates keeping the
    LATER report (holiday-week Mon/Tue report pairs can share a release date)."""
    s = cot_release_shift_series(sig)
    return s[~s.index.duplicated(keep="last")]
