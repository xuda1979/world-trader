#!/usr/bin/env python3
"""HUNT_WX_DEMAND — weather-demand (HDD/CDD) natgas-complex signals.

Pre-registered 16 configs (see ../CHARTER.md, sealed commit c0ca915e BEFORE
any result). Costs: 6.4bps one-side FULL |dW|; borrow 0.5%/yr on short.
Gates per coord/GATES_CONTRACT.md.
Publication convention: month-M signal knowable >= 12th of M+1 (conservative
NCEI posting), as-of joined to DHHNGSP daily calendar, trade t+1.
"""
import hashlib
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
COST = 0.00064
BORROW = 0.005
INPUT_SHA = {
    "hdd": "0be7aa2620a76e52",
    "cdd": "f658bcdcdda3dcaa",
    "hh": "b9329a850156bc79",
}


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def load_wx(kind):
    p = f"{ROOT}/tools/quant/data/noaa_hddcdd/{kind}_monthly.csv"
    assert _sha(p) == INPUT_SHA[kind], f"vintage drift {kind}"
    df = pd.read_csv(p, parse_dates=["date"]).set_index("date")
    return df.astype(float)


def load_hh():
    p = f"{ROOT}/tools/quant/data/newdata/DHHNGSP.csv"
    assert _sha(p) == INPUT_SHA["hh"], "vintage drift hh"
    df = pd.read_csv(p, parse_dates=["date"]).set_index("date")["DHHNGSP"]
    return df.astype(float).sort_index()


def month_signal_date(m_date):
    """Month-M signal knowable at 12th of M+1 (conservative NCEI posting)."""
    y, m = m_date.year, m_date.month
    y2, m2 = (y + 1, 1) if m == 12 else (y, m + 1)
    return pd.Timestamp(year=y2, month=m2, day=12)


def z_vs_trailing(series_m, years=10, min_years=5):
    """Monthly value z vs trailing `years` same-month history (min min_years).
    Uses ONLY data at least 1 year old (strictly before current season)."""
    out = pd.Series(index=series_m.index, dtype=float)
    vals = series_m.values
    idx = series_m.index
    for i, ts in enumerate(idx):
        hist = [vals[j] for j in range(i)
                if idx[j].month == ts.month and (ts - idx[j]).days >= 365]
        if len(hist) < min_years:
            continue
        h = np.array(hist[-years:])
        sd = h.std(ddof=1)
        if sd <= 1e-12:
            continue
        out.iloc[i] = (vals[i] - h.mean()) / sd
    return out


def season_to_date_cum(series_m, start_month=7, years=10, min_years=5):
    """Gas-year (Jul-Jun) season-to-date cumulative HDD vs trailing same-
    season-to-date normal, as % of normal. Output at each month in season."""
    out = pd.Series(index=series_m.index, dtype=float)
    vals = series_m.values
    idx = series_m.index
    # position within season: months since season start
    def pos_in_season(ts):
        return (ts.month - start_month) % 12  # 0..11
    for i, ts in enumerate(idx):
        p = pos_in_season(ts)
        if p < 2:
            continue  # need >= 3 months in season for meaningful cum
        # season start timestamps
        sy = ts.year if ts.month >= start_month else ts.year - 1
        season_start = pd.Timestamp(year=sy, month=start_month, day=1)
        cur_mask = (idx >= season_start) & (idx <= ts)
        cur = vals[cur_mask].sum()
        # historical same-window seasons
        devs = []
        for k in range(1, years + 1):
            ss = season_start - pd.DateOffset(years=k)
            se = ts - pd.DateOffset(years=k)
            m2 = (idx >= ss) & (idx <= se)
            if m2.sum() == cur_mask.sum():
                devs.append(vals[m2].sum())
        if len(devs) < min_years:
            continue
        norm = float(np.mean(devs))
        if norm <= 1e-9:
            continue
        out.iloc[i] = (cur - norm) / norm * 100.0
    return out


def net_returns(daily_ret, daily_w):
    """T+1 accounting: weight at t applies to return t+1 (caller shifts).
    Costs on FULL |dW|. Borrow on short notional."""
    dw = daily_w.diff().abs().fillna(daily_w.abs())
    gross_short = daily_w.clip(upper=0).abs()
    borrow_daily = gross_short * BORROW / 252.0
    return daily_ret * daily_w - dw * COST - borrow_daily


def sr(x):
    x = x.dropna()
    if len(x) < 200 or x.std(ddof=1) <= 1e-12:
        return 0.0
    return float(x.mean() / x.std(ddof=1) * np.sqrt(252))


def halves(x):
    x = x.dropna()
    h = len(x) // 2
    return sr(x.iloc[:h]), sr(x.iloc[h:])


def neg_years(x):
    x = x.dropna()
    yr = (1 + x).groupby(x.index.year).prod() - 1
    return int((yr < 0).sum()), float(yr.min()) if len(yr) else 0.0


def scramble_p(x, seed=17, n=200):
    x = np.array(x.dropna().values, copy=True)
    rng = np.random.default_rng(seed)
    real = abs(sr(pd.Series(x)))
    wins = 0
    for _ in range(n):
        rng.shuffle(x)
        if real > abs(sr(pd.Series(x))):
            wins += 1
    return wins / n


def vol_target(net, target=0.10, min_hist=252):
    """Trailing-only vol target ~10% ann, scale clip <= 3.0 (gate g)."""
    vol = net.shift(1).rolling(min_hist).std() * np.sqrt(252)
    scale = (target / vol).clip(upper=3.0)
    return (net * scale).dropna()


def run_tilt(hh, hh_ret, sig_m, thr, sign, label, fam, results):
    """Monthly boolean tilt -> daily HH position from conservative signal
    date, T+1, costs, gates. sig_m: monthly series (index=month start)."""
    # map each month to its conservative knowable date and signal state
    active = sig_m.abs() >= thr  # boolean monthly
    # build daily position: for each day, the latest knowable month's state
    sig_dates = pd.Series(
        [float(active.iloc[i]) for i in range(len(active))],
        index=pd.DatetimeIndex([month_signal_date(d) for d in active.index])
    ).sort_index()
    # as-of join (charter semantics): daily state = value of latest signal
    # with sig_date <= day; weekend 12ths switch on first trading day after.
    days = hh.index.values
    sds = sig_dates.index.values
    pos_idx = np.searchsorted(sds, days, side="right") - 1
    state_d = pd.Series(
        [sig_dates.iloc[i] if i >= 0 else 0.0 for i in pos_idx],
        index=hh.index)
    pos = sign * state_d  # +1 long when active (sign=+1 follow) or -1 fade
    w = pos.shift(1)  # T+1
    net = net_returns(hh_ret.fillna(0.0), w)
    net_vt = vol_target(net)
    results.append((fam, label, sr(net_vt), halves(net_vt),
                    neg_years(net_vt), scramble_p(net_vt)))


def main():
    hdd = load_wx("hdd")
    cdd = load_wx("cdd")
    hh = load_hh()
    hh_ret = hh.pct_change().clip(-0.25, 0.25)

    results = []

    # ------------------------------------------------------------- W1 HDD-dev
    hz = z_vs_trailing(hdd["US"]).clip(-4, 4)
    for thr in (1.0, 1.5, 2.0):
        for sign, sname in ((1, "follow"), (-1, "fade")):
            run_tilt(hh, hh_ret, hz, thr, sign,
                     f"W1_hddz{thr}_{sname}", "W1", results)

    # ------------------------------------------------- W2 cumulative surplus
    hs = season_to_date_cum(hdd["US"], start_month=7)
    for thr in (2.0, 5.0):
        for sign, sname in ((1, "follow"), (-1, "fade")):
            run_tilt(hh, hh_ret, hs, thr, sign,
                     f"W2_hddcum{thr}%_{sname}", "W2", results)

    # ------------------------------------------------- W3 CDD summer variant
    cz = z_vs_trailing(cdd["US"]).clip(-4, 4)
    # restrict to cooling season May-Sep
    cz = cz[cz.index.month.isin([5, 6, 7, 8, 9])]
    for thr in (1.0, 1.5):
        for sign, sname in ((1, "follow"), (-1, "fade")):
            run_tilt(hh, hh_ret, cz, thr, sign,
                     f"W3_cddz{thr}_{sname}", "W3", results)
    cs = season_to_date_cum(cdd["US"], start_month=5)
    cs = cs[cs.index.month.isin([6, 7, 8, 9])]
    for thr in (2.0, 5.0):
        for sign, sname in ((1, "follow"), (-1, "fade")):
            run_tilt(hh, hh_ret, cs, thr, sign,
                     f"W3_cddcum{thr}%_{sname}", "W3", results)

    # ------------------------------------ W4 regional composition (follow only)
    heat = hdd[["NE", "UP", "OH"]].sum(axis=1)
    nat = hdd["US"]
    # heating-region share of national deviation: corr-style conditioning
    hz_h = z_vs_trailing(heat).clip(-4, 4)
    # composition weight: |z_heat| > |z_national| -> amplification, else damp
    comp = (hz_h.abs() - hz.abs()) / 4.0  # -1..1
    sig = hz.where(hz.abs() >= 1.5) + comp.where(hz.abs() >= 1.5).fillna(0)
    sig = sig.fillna(0.0)
    # continuous tilt version: position = sign(hz)*1 when active
    pos_m = pd.Series(0.0, index=hdd.index)
    act = hz.abs() >= 1.5
    pos_m[act] = np.sign(hz[act]) * (1.0 + comp[act].clip(-0.5, 0.5))
    run_tilt(hh, hh_ret, pos_m, 0.5, 1, "W4_compfollow_1.5", "W4", results)
    # second config: threshold 1.5 on composition-amplified only (no damp)
    pos_m2 = pd.Series(0.0, index=hdd.index)
    act2 = (hz.abs() >= 1.5) & (comp > 0)
    pos_m2[act2] = np.sign(hz[act2]) * (1.0 + comp[act2].clip(0, 0.5))
    run_tilt(hh, hh_ret, pos_m2, 0.5, 1, "W4_compamp_1.5", "W4", results)

    # ------------------------------------------------------------------ report
    print(f"{'fam':4} {'config':24} {'SR':>7} {'H1':>6} {'H2':>6} "
          f"{'negY':>4} {'scram':>6}")
    for fam, name, s, (h1, h2), ny, sp in results:
        print(f"{fam:4} {name:24} {s:7.3f} {h1:6.3f} {h2:6.3f} "
              f"{ny[0]:4d} {sp:6.3f}")
    print("total configs:", len(results))


if __name__ == "__main__":
    sys.exit(main())
