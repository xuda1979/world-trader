"""HUNT_TIMESFM ROUND 5 library — weekly forecast-direction on new 2026-09-08 spans.

Pre-registered contract (FINDINGS.md R5, before any result): last-trading-day-of-ISO-week
decisions on the asset's own calendar; TimesFM 2.5-200m sign(m) at h in {1,5}; VT frozen
at the decision date (trailing-only); held weights w_t = pos_j * v_j over (D_j, D_{j+1}];
strict T+1; 6.4bps one-side FULL |dW| + borrow 0.5%/yr + margin 4.5%/yr; per-unit net with
sig * r_pu == net exactly for gates.run (V2 6d contract: r must be per-unit so sig*r IS
the held book).
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")

COST = 6.4e-4
BORROW = 0.005
MARGIN = 0.045
ANN = 252.0

WEEK = pd.Timestamp("1970-01-05")  # a Monday; ISO arithmetic via isocalendar instead


def load_index_csv(path: str, value_col: str = None) -> pd.Series:
    """Load a dated CSV as a clean close series: drop NaN rows (NEVER fill — holidays are
    closures, ffill would fabricate prices and corrupt log-price context), dedupe keeping
    last, drop nonpositive, sort. Fail-closed on empty."""
    import pandas as pd
    df = pd.read_csv(path)
    dcol = df.columns[0]
    vcol = value_col or df.columns[1]
    dt = pd.to_datetime(df[dcol])
    v = pd.to_numeric(df[vcol], errors="coerce")
    ok = v.notna() & (v > 0)
    s = pd.Series(v[ok].values, index=dt[ok])
    s = s[~s.index.duplicated(keep="last")].sort_index()
    if not len(s):
        raise ValueError(f"empty after clean: {path}")
    return s.astype(float)


def weekly_decisions(idx: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Last trading day of each ISO week present in the calendar (asset's own calendar)."""
    iso = idx.isocalendar()
    df = pd.DataFrame({"d": idx, "yw": iso.year * 100 + iso.week})
    last = df.groupby("yw")["d"].max()
    return pd.DatetimeIndex(last.sort_values().values)


def vt_frozen(r: pd.Series, dec: pd.DatetimeIndex, target=0.10, minlen=60, cap=3.0) -> pd.Series:
    """Trailing-only VT evaluated ONCE per decision date: scale_j uses returns up to and
    including D_j (the position is decided at close D_j, so <=D_j info is PIT-legal),
    frozen through the holding week. 10% ann target, clip<=3, min 60 obs, else 0."""
    rx = r.dropna()
    vol = rx.expanding(min_periods=minlen).std(ddof=1) * np.sqrt(ANN)
    s = (target / vol.replace(0.0, np.nan)).clip(upper=cap)
    s = s.shift(0)  # includes D_j's own return: decided at close D_j after observing it
    v = s.reindex(dec)
    return v.fillna(0.0) if v.isna().any() else v


def held_weights(cal: pd.DatetimeIndex, pos: pd.Series, v: pd.Series) -> pd.Series:
    """w_t = pos_j * v_j for t in (D_j, D_{j+1}]; strict T+1: the first held day is the
    first trading day AFTER D_j (decision day itself holds the PRIOR decision)."""
    pv = (pos * v).dropna().sort_index()
    w = pd.Series(0.0, index=cal)
    if len(pv) == 0:
        return w
    dec = pv.index
    # decision day D_j itself holds the prior decision value; T+1 start for its own.
    # Build via reindex on calendar: last decision strictly before t.
    keys = pd.Series(np.arange(len(cal)), index=cal)
    di = pd.Series(keys.reindex(dec).values, index=dec)
    # for each calendar day, index of last decision strictly before it
    j = np.searchsorted(dec.values, cal.values, side="left") - 1
    w_vals = np.where(j >= 0, pv.values[j.clip(0)], 0.0)
    w = pd.Series(w_vals, index=cal)
    # enforce strict T+1: a day t equal to a decision date D_k holds decision j<k.
    on_dec = keys.reindex(dec)
    for d, k in on_dec.items():
        prev = [x for x in dec if x < d]
        w.loc[d] = float(pv.loc[prev[-1]]) if prev else 0.0
    return w


def book_net(w: pd.Series, r: pd.Series):
    """Costed book from held weights. Returns (net, r_pu, sig):
      net_t = w_t*r_t - |dw|*6.4bps - borrow - margin   (per 1.0 NAV)
      r_pu_t = net_t / |w_t| (per-unit, 1.0 when flat)  so sig=sign-ish weight path gives
      sig * r_pu == net EXACTLY (gates.run V2 contract: r must be PER-UNIT).
    sig here is the held weight path itself (units of exposure), matching CMDT2-R5's
    corrected convention: gates.run internal book sig*r_pu == held book."""
    r = r.reindex(w.index)
    act = w.abs() > 0
    if (act & r.isna()).any():
        d = (act & r.isna()).idxmax()
        raise ValueError(f"silent zero-fill: active weight without return at {d}")
    r = r.fillna(0.0)
    dw = w.diff().abs()
    if len(dw):
        dw.iloc[0] = abs(w.iloc[0])          # entry turnover charged
    # Fold EXIT turnover (dw on a day where w becomes 0) into the LAST ACTIVE day. The
    # total cost is identical; the timing moves one day earlier. Without this, the cost
    # would land on a flat day where sig=0 and the gates.run contract (sig * r_pu == net
    # on every day) would silently MISS the exit cost — fail-open book distortion.
    flat_day_cost = dw.where((w == 0) & (dw > 0))
    if flat_day_cost.notna().any():
        # attribute each flat-day cost to the most recent active day
        last_active = (w != 0).cummax() * (w != 0)
        idx_last = pd.Series(np.where(last_active > 0, np.arange(len(w)), -1), index=w.index)
        carry = idx_last.replace(-1, np.nan).ffill().fillna(-1).astype(int)
        for gi, c in flat_day_cost.dropna().items():
            li = carry.loc[gi]
            if li >= 0:
                dw.iloc[li] += c
        dw.loc[flat_day_cost.dropna().index] = 0.0
    gross = w * r
    cost = dw * COST
    borrow = (-w.clip(upper=0.0)) * BORROW / ANN
    margin = (w.abs() - 1.0).clip(lower=0.0) * MARGIN / ANN
    net = gross - cost - borrow - margin
    r_pu = net / w.replace(0.0, np.nan)   # SIGNED division: sig*r_pu == net for w<0 too
    r_pu = r_pu.fillna(1.0)  # flat days: per-unit undefined; set 1.0 (sig=0 kills it in book)
    sig = w.copy()
    return net, r_pu, sig


def run_battery(net, rpu, sig, ref=None, spy=None, ief=None, cta=None, scramble_n=200) -> dict:
    """Full V2 battery, EXPLICIT per charter: leak_check=True, beats_passive=True trio,
    sig=, ref=champion. r = per-unit so gates' internal book sig*r_pu == held net."""
    from bt import gates as G
    return G.run(rpu.dropna(), ref=ref, sig=sig.reindex(rpu.dropna().index),
                 leak_check=True, beats_passive=True,
                 spy=spy, ief=ief, cta=cta, scramble_n=scramble_note(scramble_n))


def scramble_note(n):
    return n
