#!/usr/bin/env python3
"""HUNT_FXCARRY2 round-2: monthly carry basket on linted FRED FX + IRSTCI01 rates.

Data: tools/quant/data/more_fx (29 linted FRED series, manifest in that dir;
     daily DEX FX 1971-1999+, monthly immediate rates 1954+).
Window: 2004+ per charter (fixes R1's 2019+ flaw); pre-2004 DEX coverage is
     fine but IRSTCI01 immediate rates only start making the 6-10 pair basket
     viable around 1990s, and the champion overlap window needs 2004+.
Engine (GATES_CONTRACT.md): honest T+1 (signal at t uses data <= t; position
     taken t+1), 6.4bps one-side on FULL |dW| incl. day-1 entry, borrow
     0.5%/yr on short notional, margin 4.5%/yr on (gross-1), vol-target 10%
     ann trailing-only clip <=3.0, gross cap 1.6.
Carry: IRSTCI01 immediate-rate differential foreign-USD, sampled at month-end,
     held one month (holding period == rebalance frequency).
Pairs (8 with rates on FRED): AUD, EUR, GBP, JPY, CAD, CHF, NOK, KRW vs USD.
Variants: (b) nominal carry EW; real carry (CPI-deflated); (c) carry+momentum;
     (d) vol-scaled carry (inverse realized-vol cross-sectional weights).
"""
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")
from bt import metrics as M

FXD = f"{ROOT}/tools/quant/data/more_fx"
COST, BORROW, MARGIN, ANN = 6.4e-4, 0.005, 0.045, 252.0
CHAMP_CSV = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"

# name -> (DEX series, foreign ccy, sign converting "long foreign" to pair quote)
# DEXUSAL/DEXUSEU/DEXUSUK quote USD-per-foreign => +1: px up = foreign up.
# DEXJPUS/DEXCAUS/DEXSZUS/DEXNOUS/DEXKOUS quote foreign-per-USD => long pair =
# long USD, so the foreign-carry signal enters with sign -1.
PAIRS = {
    "AUDUSD": ("DEXUSAL", "AUD", +1),
    "EURUSD": ("DEXUSEU", "EUR", +1),
    "GBPUSD": ("DEXUSUK", "GBP", +1),
    "USDJPY": ("DEXJPUS", "JPY", -1),
    "USDCAD": ("DEXCAUS", "CAD", -1),
    "USDCHF": ("DEXSZUS", "CHF", -1),
    "USDNOK": ("DEXNOUS", "NOK", -1),
    "USDKRW": ("DEXKOUS", "KRW", -1),
}
RATE = {
    "USD": "IRSTCI01USM156N", "AUD": "IRSTCI01AUM156N", "EUR": "IRSTCI01EZM156N",
    "GBP": "IRSTCI01GBM156N", "JPY": "IRSTCI01JPM156N", "CAD": "IRSTCI01CAM156N",
    "CHF": "IRSTCI01CHM156N", "NOK": "IRSTCI01NOM156N", "KRW": "IRSTCI01KRM156N",
}
CPI = {
    "USD": "CPALTT01USM657N", "EUR": "CPALTT01DEM657N", "JPY": "CPALTT01JPM657N",
    "GBP": "CPALTT01GBM657N", "CAD": "CPALTT01CAM657N", "CHF": "CPALTT01CHM657N",
    "KRW": None,  # no KRW CPI on FRED under CPALTT01 (probed 2026-09-07)
    "NOK": None,  # no NOK CPI on FRED under CPALTT01
}


def load_col(sid):
    df = pd.read_csv(f"{FXD}/{sid}.csv")
    return pd.Series(df["value"].astype(float).values,
                     index=pd.to_datetime(df["date"])).sort_index()


def load_px(sid):
    s = load_col(sid)
    return s[s > 0]


def load_rate(sid):
    return load_col(sid) / 100.0  # percent -> decimal p.a.


def month_ends(px, start):
    sub = px[px.index >= start]
    return pd.DatetimeIndex(sub.groupby([sub.index.year, sub.index.month]).apply(
        lambda g: g.index[-1]))


def vt_scale(r, target=0.10, window=60, cap=3.0):
    vol = r.expanding(min_periods=window).std(ddof=1) * np.sqrt(ANN)
    sc = (target / vol.replace(0.0, np.nan)).clip(upper=cap).clip(lower=0.2)
    return sc.shift(1).fillna(1.0)


def evaluate(pos, r, vt=True, lag=True, lev_cap=1.6, yield_r=None):
    """pos: daily-grid signal series. yield_r: extra daily return per unit of
    position (the carry accrual, sign-adjusted to pair-quote convention).
    Returns (net daily series, positions used)."""
    p = pos.reindex(r.index)
    p = p.where(p.notna(), 0.0)
    if lag:
        p = p.shift(1).fillna(0.0)
    if vt:
        p = p * vt_scale(r)
    gross = p.abs()
    over = gross > lev_cap
    if over.any():
        p = p.where(~over, p * (lev_cap / gross))
    w = p.fillna(0.0)
    prev = w.shift(1)
    prev.iloc[0] = 0.0
    to = (w - prev).abs()
    short = (-w.clip(upper=0.0))
    tot_r = r if yield_r is None else (r + yield_r.reindex(r.index).fillna(0.0))
    net = (w * tot_r - to * COST - short * BORROW / ANN
           - np.maximum(w.abs() - 1.0, 0.0) * MARGIN / ANN)
    return net.dropna(), w


def stat(net):
    if len(net) < 200:
        return dict(n=len(net), sr=np.nan, ann=np.nan)
    neg, worst = M.neg_years(net)
    h1, h2 = M.half_split(net)
    return dict(n=len(net), sr=round(M.sharpe_d(net), 3),
                ann=round(M.ann_geo(net), 4), mdd=round(M.max_dd(net), 4),
                neg_years=int(neg), worst_year=round(float(worst), 4),
                h1=round(h1, 3), h2=round(h2, 3),
                vol=round(float(net.std(ddof=1) * np.sqrt(ANN)), 4))


def yearly(net):
    yr = net.groupby(net.index.year).apply(lambda x: (1 + x).prod() - 1)
    return {int(k): round(float(v), 4) for k, v in yr.items()}


def yearly_ok(net):
    yr = net.groupby(net.index.year).apply(lambda x: (1 + x).prod() - 1)
    neg = yr[yr < 0]
    return (len(neg) <= 2 and (len(neg) == 0 or neg.min() > -0.05))


def champ_corr(net):
    ch = pd.read_csv(CHAMP_CSV, index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([ch.rename("c"), net.rename("s")], axis=1).dropna()
    return float(j["c"].corr(j["s"]))


def book_scramble(pos_map, rets_map, ylds=None, n=200, seed=0, index=None):
    """GATE e at book level: roll every pair's position by the same random lag,
    recompute the EW gross book SR on TOTAL return (spot + carry accrual).
    p = frac(scrambled >= real). All series aligned on `index`."""
    rng = np.random.default_rng(seed)
    ks = list(pos_map)
    idx = index if index is not None else pos_map[ks[0]].index
    P = np.column_stack([
        np.asarray(pos_map[k].reindex(idx).fillna(0.0), float) for k in ks])
    R = np.column_stack([
        np.asarray(rets_map[k].reindex(idx).fillna(0.0), float) for k in ks])
    if ylds:
        Y = np.column_stack([
            np.asarray(ylds[k].reindex(idx).fillna(0.0), float) for k in ks])
        R = R + Y
    gross = pd.Series((P * R).mean(axis=1))
    real = M.sharpe_d(gross.dropna())
    T = len(gross)
    cnt = 0
    for _ in range(n):
        lag = int(rng.integers(10, T - 10 + 1))
        sc = M.sharpe_d(pd.Series((np.roll(P, lag, axis=0) * R).mean(axis=1)).dropna())
        if sc >= real:
            cnt += 1
    return cnt / n, float(real)


def build_signals(start="2004-01-01", mode="nominal", mom=None):
    """Per-pair daily carry signal (long high-yield leg). mode: nominal|real.
    mom: if set, zero out months where sign(carry) != sign(mom-day momentum).
    Returns (signals, yields, rets): yields = per-pair daily carry accrual per
    unit pair-position. A pair position w (pair-quote units) earns the spot
    return PLUS sign*(r_fgn - r_usd)/252 per day held (interest-rate parity:
    the high-yield leg pays the rate differential forward)."""
    rates = {c: load_rate(s) for c, s in RATE.items() if s}
    cpis = {c: load_px(s) for c, s in CPI.items() if s}
    out, yld, pxs, rets = {}, {}, {}, {}
    for name, (sid, fgn, sign) in PAIRS.items():
        px = load_px(sid)
        if mode == "real" and CPI.get(fgn) is None:
            continue  # honest: drop pair rather than fake its CPI
        idx = month_ends(px, start)
        carry_m = (rates[fgn].reindex(idx, method="ffill")
                   - rates["USD"].reindex(idx, method="ffill"))
        if mode == "real":
            ia = cpis[fgn].pct_change(12).reindex(idx, method="ffill")
            iu = cpis["USD"].pct_change(12).reindex(idx, method="ffill")
            carry_m = carry_m - (ia - iu)
        sig_m = np.sign(carry_m) * sign
        if mom is not None:
            m = px.pct_change(mom).reindex(idx, method="ffill")
            sig_m = sig_m.where(np.sign(sig_m) == np.sign(m), 0.0)
        sig_d = pd.Series(np.nan, index=px.index)
        for d, v in sig_m.items():
            sig_d.loc[d:] = v
        # daily accrual per unit position: sign * (r_fgn - r_usd) / 252
        rate_diff_d = (rates[fgn] - rates["USD"]).reindex(px.index).ffill()
        yld[name] = rate_diff_d * sign / ANN
        out[name] = sig_d.dropna()
        pxs[name] = px
        rets[name] = px.pct_change()
    return out, yld, rets


def book(sigs, rets, ylds=None, w_map=None, start=None):
    """EW (or weighted) book of per-pair T+1 net series; returns (net, positions).
    ylds: per-pair daily carry accrual (credited on position, after T+1 shift).
    start: slice the book to the evaluation window (positions are 0-filler before
    a pair's signal starts; those filler days must not enter the stats)."""
    nets, poss = [], []
    for k in sigs:
        net, w = evaluate(sigs[k], rets[k], yield_r=(ylds[k] if ylds else None))
        nets.append(net.rename(k))
        poss.append((k, w))
    df = pd.concat(nets, axis=1).fillna(0.0)
    if start is not None:
        df = df[df.index >= start]
    n = len(nets)
    if w_map is None:
        wts = pd.Series({k: 1.0 / n for k, _ in poss})
    else:
        s = pd.Series(w_map, dtype=float)
        wts = s / s.sum()
    net = df.mul(wts, axis=1).sum(axis=1)
    pos = {k: w * float(wts[k]) for k, w in poss}
    if start is not None:
        pos = {k: v[v.index >= start] for k, v in pos.items()}
    return net, pos


def vol_weights(rets, sigs, window=63):
    """Cross-sectional inverse realized-vol weights, trailing-only at each
    month-end (uses returns <= t)."""
    names = list(sigs)
    idx = sigs[names[0]].index
    me = month_ends(pd.Series(1.0, index=idx), idx[0])
    vols = {k: rets[k].rolling(window).std() * np.sqrt(ANN) for k in names}
    rows = {}
    for d in me:
        row = {k: 1.0 / vols[k].asof(d) if np.isfinite(vols[k].asof(d)) else np.nan
               for k in names}
        s = pd.Series(row, dtype=float)
        rows[d] = s / s.sum(min_count=1) * len(names)  # gross-neutral multiplier
    W = pd.DataFrame(rows).T
    out = {}
    for k in names:
        out[k] = sigs[k] * W[k].reindex(sigs[k].index).ffill().fillna(1.0)
    return out


def gates(net, pos_map, rets_map, label):
    st = stat(net)
    h1, h2 = M.half_split(net)
    p_sc, real = book_scramble(pos_map, rets_map)
    corr = champ_corr(net)
    g = dict(label=label, n=st["n"], sr=st["sr"], ann=st["ann"],
             mdd=st["mdd"], neg_years=st["neg_years"],
             worst_year=st["worst_year"], h1=st["h1"], h2=st["h2"],
             halves_ok=bool(h1 >= 0.5 and h2 >= 0.5),
             yearly_ok=bool(yearly_ok(net)), years=yearly(net),
             corr=round(corr, 4), corr_ok=bool(abs(corr) < 0.15),
             scramble_p=round(p_sc, 4), scramble_real=round(real, 3),
             sr_ok=bool(st["sr"] >= 1.0))
    g["verdict"] = ("PASS" if (g["sr_ok"] and g["halves_ok"] and g["yearly_ok"]
                              and g["corr_ok"] and p_sc < 0.05) else "FAIL")
    return g


def show(g):
    print("%-22s n=%-5d SR=%6.3f ann=%7.4f mdd=%6.3f negyr=%d worst=%7.4f "
          "H=(%5.2f,%5.2f) corr=%6.3f scr_p=%5.3f => %s" % (
              g["label"], g["n"], g["sr"], g["ann"], g["mdd"], g["neg_years"],
              g["worst_year"], g["h1"], g["h2"], g["corr"], g["scramble_p"],
              g["verdict"]))
    print("   years:", g["years"])


if __name__ == "__main__":
    start = sys.argv[1] if len(sys.argv) > 1 else "2004-01-01"
    print(f"=== HUNT_FXCARRY2 round-2 | window {start}+ | 8 pairs, monthly carry ===")

    sigs, ylds, rets = build_signals(start=start, mode="nominal")
    # R1-style (spot-only) reproduction: shows the framework-flaw delta honestly
    net0, pos0 = book(sigs, rets, start=start)
    show(gates(net0, pos0, rets, "carry-spotonly-EW (R1 flaw)"))

    net, pos = book(sigs, rets, ylds=ylds, start=start)
    show(gates(net, pos, rets, "carry-nominal-EW"))

    sigs_r, ylds_r, rets_r = build_signals(start=start, mode="real")
    net, pos = book(sigs_r, rets_r, ylds=ylds_r, start=start)
    show(gates(net, pos, rets_r, "carry-real-EW"))

    sigs_c, ylds_c, rets_c = build_signals(start=start, mode="nominal", mom=63)
    net, pos = book(sigs_c, rets_c, ylds=ylds_c, start=start)
    show(gates(net, pos, rets_c, "carry+mom63-EW"))

    sigs_v = vol_weights(rets, sigs)
    net, pos = book(sigs_v, rets, ylds=ylds, start=start)
    show(gates(net, pos, rets, "carry-volscaled-EW"))
