#!/usr/bin/env python3
"""HUNT_FXCARRY2 round 5 — pre-registered corner: Frankfurter FX daily (keyless, ECB
euro reference rates 1999+, fetched this round to work_r5/frankfurter/, manifest + sha256
in fetch_meta.json). Families per charter: carry / trend.

EXPRESSIBILITY (disclosed up front, pinned by tests): Frankfurter is SPOT-ONLY — it
publishes no forward points, deposits or short rates. A carry book therefore cannot be
built from Frankfurter alone; the carry variants here use the FRED IRSTCI01 monthly
immediate rates (same PIT month-end +1-month convention as R2, whose negative is the
documented family context — this is a DIFFERENT corner: the 10-currency Frankfurter
panel vs R2's 8 DEX pairs, and trend run on the new panel too). Trend needs no rates
and is judged on the Frankfurter panel directly.

Construction: EUR-base quotes -> cross rates vs USD; equal-weight baskets formed at
month-end (PIT), T+1 shift(1), 6.4bps FULL |dW| + 0.5%/yr borrow + 4.5%*max(gross-1,0)
margin, trailing-expanding VT10 cap3. Full V2 battery: gates.run(r=per-unit, sig=held
positions, leak_check=True, beats_passive trio, ref=champion of record
sha 4358dfab95679b97), scramble 200x, plateau grid, halves, yearly.

Span discipline (V2 s9): panel is 1999+ => span_class 2007plus at best (1999 start);
every number carries its span. If IS-SR <= 0 that IS the result (charter instruction).
"""
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/campaign")

from bt import engine, metrics as M  # noqa: E402
import bt.gates as bgates  # noqa: E402

HERE = f"{ROOT}/campaign/agents/chief/coord/HUNT_FXCARRY2/work_r5"
FF_DIR = f"{HERE}/frankfurter"
SLEEVES = f"{ROOT}/campaign/agents/chief/coord/HUNT_FXCARRY2/sleeves"
CHAMP_CSV = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
CHAMP_SHA = hashlib.sha256(open(CHAMP_CSV, "rb").read()).hexdigest()[:16]

ANN = 252
COST = 6.4 / 1e4
BORROW = 0.005
MARGIN = 0.045
GEAR_CAP = 1.6

# FRED IRSTCI01 immediate rates: country-code -> series id (R2-verified live ids).
RATE_IDS = {"US": "IRSTCI01USM156N", "EU": "IRSTCI01DEM156N", "JP": "IRSTCI01JPM156N",
            "GB": "IRSTCI01GBM156N", "CA": "IRSTCI01CAM156N", "CH": "IRSTCI01CHM156N",
            "AU": "IRSTCI01AUM156N", "NZ": "IRSTCI01NZM156N", "NO": "IRSTCI01NOM156N",
            "KR": "IRSTCI01KRM156N"}
# currency -> (frankfurter column, EUR-or-USD pricing leg). EUR itself uses the DEM/EZ
# rate with the USD cross from the panel's USD column.
CCY = {"AUD": "AUD", "CAD": "CAD", "CHF": "CHF", "GBP": "GBP", "JPY": "JPY",
       "KRW": "KRW", "NOK": "NOK", "NZD": "NZD"}
RATE2CCY = {"US": "USD", "EU": "EUR", "JP": "JPY", "GB": "GBP", "CA": "CAD",
            "CH": "CHF", "AU": "AUD", "NZ": "NZD", "NO": "NOK", "KR": "KRW"}


# ------------------------------------------------------------------ data
def load_frankfurter():
    df = pd.read_csv(f"{FF_DIR}/FRANKFURTER_EUR_wide.csv", index_col=0, parse_dates=True)
    return df.sort_index().astype(float)


def load_rates():
    out = {}
    for cc, sid in RATE_IDS.items():
        df = pd.read_csv(f"{ROOT}/tools/quant/data/more_fx/{sid}.csv", parse_dates=["date"])
        s = pd.Series(df["value"].astype(float).values / 100.0, index=pd.to_datetime(df["date"]))
        out[cc] = s.sort_index()
    return out


def usd_crosses(px):
    """USD per 1 EUR (col USD) and USD per 1 ccy for each CCY col: USDperCCY =
    USDperEUR / ccyPerEUR."""
    usdper_eur = px["USD"]
    out = {"EUR": usdper_eur}
    for c in CCY:
        out[c] = usdper_eur / px[c]
    return pd.DataFrame(out)


def month_ends(idx):
    s = idx.to_series()
    return pd.DatetimeIndex(s.groupby([s.index.year, s.index.month]).apply(lambda g: g.index[-1]))


# ------------------------------------------------------------------ books
def carry_book_weights(px, rates, top=3, k=252):
    """Monthly carry basket on the Frankfurter 10-currency universe (9 non-USD + USD as
    pricing leg): rank by trailing-k-day (≈12m) mean of (r_ccy - r_usd) monthly rate
    differential PIT at month-end; long `top` high-carry vs short `top` low-carry vs USD.
    Returns W (decision-time weights, per-ccy USD cross), daily grid."""
    cross = usd_crosses(px)
    mes = month_ends(cross.index)
    r_us = rates["US"]
    diffs = {}
    for cc, ccy in RATE2CCY.items():
        if cc == "US":
            continue
        r_c = rates[cc]
        # monthly-rate differential sampled at each month-end, PIT (rate series dated m
        # is usable from m+1 per R2's FRED release-lag convention)
        d = (r_c.reindex(mes, method="ffill", limit=45)
             - r_us.reindex(mes, method="ffill", limit=45))
        d = d.shift(1, freq="MS")  # +1-month PIT convention: month-m value usable at m+1
        diffs[ccy] = d
    D = pd.DataFrame(diffs)
    signal = D.rolling(k // 21, min_periods=6).mean()  # ~12m mean carry (monthly obs)
    signal = signal.reindex(cross.index, method="ffill", limit=45)

    W = pd.DataFrame(0.0, index=cross.index, columns=list(cross.columns))
    for dt, row in signal.iterrows():
        r_ = row.dropna()
        if len(r_) < 2 * top:
            continue
        hi = r_.nlargest(top).index
        lo = r_.nsmallest(top).index
        for c in hi:
            W.loc[dt, c] = 1.0 / top
        for c in lo:
            W.loc[dt, c] = -1.0 / top
        W.loc[dt, "USD"] = -(W.loc[dt, list(hi) + list(lo)].sum())
    # hold month-end decision daily until next month-end
    W = W.reindex(cross.index).ffill().fillna(0.0)
    return W[list(cross.columns)]


def trend_book_weights(px, lb=252, mode="LS", top=3):
    """Monthly time-series/cross-sectional trend: at month-end rank |trailing-lb| move;
    TS mode: long positive-momentum ccy vs USD, short negative (LS) or flat (LF).
    EW across qualifying names, capped at `top` each side."""
    cross = usd_crosses(px)
    mes = month_ends(cross.index)
    mom12 = cross.loc[mes].pct_change(lb // 21)
    W = pd.DataFrame(0.0, index=cross.index, columns=list(cross.columns))
    for dt, row in mom12.iterrows():
        r_ = row.dropna()
        if len(r_) < 4:
            continue
        up = r_[r_ > 0].nlargest(top).index if mode in ("LS", "LF") else []
        dn = (-r_[r_ < 0]).nlargest(top).index if mode == "LS" else []
        n = max(len(up), len(dn), 1)
        for c in up:
            W.loc[dt, c] = 1.0 / n
        for c in dn:
            W.loc[dt, c] = -1.0 / n
    W = W.reindex(cross.index).ffill().fillna(0.0)
    return W[list(cross.columns)]


# ------------------------------------------------------------------ engine
def returns_from_px(px):
    cross = usd_crosses(px)
    return cross.pct_change()


def fx_total_returns(px, rates):
    """TOTAL returns per funding leg of the basket: spot return + interest-rate-parity
    accrual (r_ccy - r_usd)/252 credited daily on each non-USD leg (long 1 unit of ccy c
    funded at USD rate earns spot + (r_c - r_usd)); the USD leg is the numéraire residual
    and earns exactly 0 — the book is self-funding per leg, never a hidden EUR/USD spot."""
    spot = returns_from_px(px)
    out = {}
    mes = month_ends(spot.index)
    r_us_m = rates["US"].reindex(mes, method="ffill", limit=45)
    r_us_m = r_us_m.shift(1, freq="MS")  # PIT: month-m rate usable from m+1 (R2 convention)
    r_us_daily = r_us_m.reindex(spot.index, method="ffill", limit=45)
    for c in spot.columns:
        cc = {v: k for k, v in RATE2CCY.items()}[c]
        r_c_m = rates[cc].reindex(mes, method="ffill", limit=45).shift(1, freq="MS")
        r_c_daily = r_c_m.reindex(spot.index, method="ffill", limit=45)
        out[c] = spot[c] + (r_c_daily - r_us_daily) / ANN
    out["USD"] = pd.Series(0.0, index=spot.index)  # funding/numéraire leg: earns exactly 0
    return pd.DataFrame(out)


def net_of(W, R, vt=True, target=0.10, cap=3.0):
    """T+1 effective weights, trailing-expanding VT on the PORTFOLIO RETURN series,
    6.4bps FULL |dW| + borrow + margin. R = per-ccy USD-cross daily returns.

    Returns (net, We, sig, r_pu): sig = HELD GROSS UNITS (sum|We| > 0 on live days) and
    r_pu the per-unit costed return with sig*r_pu == net exactly on live days — the
    gates.run contract. The R5 v1 scalarization (sig = signed net exposure) is 0 for a
    dollar-neutral basket and made gates.run judge a zero book (corr nan, negyr 0)."""
    W = W.reindex(columns=R.columns).fillna(0.0)
    We = W.shift(1).fillna(0.0)
    gross_leg_pre = We.abs().sum(axis=1)
    # VT scale input = the PORTFOLIO GROSS RETURN series (campaign convention: INTL2/CMDT2
    # net_of feed (We*R).sum(axis=1), NOT the weight gross — a constant-2.0 weight series
    # has std 0 and slams the scale to its 0.2 floor). vol_target_scale is trailing-only.
    port_pre = (We * R.fillna(0.0)).sum(axis=1)
    if vt:
        s = engine.vol_target_scale(port_pre.to_frame("g"), target=target, cap=cap)["g"]
        We = We.mul(s, axis=0)
    gross_leg = We.abs().sum(axis=1)
    port = (We * R.fillna(0.0)).sum(axis=1)
    cost = engine.cost_turnover(We, cost_bps=6.4)
    borr = engine.borrow_cost(We)
    marg = np.maximum(gross_leg - 1.0, 0.0) * MARGIN / ANN
    net = port - cost - borr - marg
    live = gross_leg > 0
    sig = gross_leg.where(live, 0.0)  # positive held units: |We| sums, never the signed sum
    r_pu = (net / sig.replace(0.0, np.nan)).fillna(0.0)
    book = sig * r_pu
    assert ((book - net)[live].abs() < 1e-15).all(), "sig*r_pu != net on live days"
    return net.rename("ret"), We, sig.rename("sig"), r_pu.rename("r_pu")


def trim_warmup(net, sig):
    live = sig.fillna(0.0) > 0
    if not live.any():
        raise AssertionError("never-live book: weights all zero — broken build")
    return net[net.index >= live.idxmax()]


def matrix_scramble_p(W, R, n=200, seed=7):
    """GATE e at book level for a multi-leg basket: roll the whole position MATRIX by one
    common random lag (preserves cross-sectional structure), rebuild T+1+VT+costs
    identically, p = P(SR_scrambled >= SR_real)."""
    from numpy.random import default_rng
    rng = default_rng(seed)
    W = W.reindex(columns=R.columns).fillna(0.0)
    R = R.fillna(0.0)
    net, We, sig, r_pu = net_of(W, R)
    real = M.sharpe_d(trim_warmup(net, sig))
    idx = W.index
    cnt = 0
    lag_lo, lag_hi = 120, max(121, len(idx) // 3)
    for _ in range(n):
        lag = int(rng.integers(lag_lo, lag_hi))
        Wp = W.copy()
        Wp.iloc[lag:] = W.iloc[:len(W) - lag].values  # roll forward by `lag`
        nets, _, s, _ = net_of(Wp, R)
        if M.sharpe_d(trim_warmup(nets, s)) >= real:
            cnt += 1
    return cnt / n


# ------------------------------------------------------------------ battery
def _benchmarks():
    spy = pd.read_csv(f"{ROOT}/tools/quant/data/twelvedata/SPY.csv", parse_dates=["date"]
                      ).set_index("date")["close"].sort_index().pct_change()
    ief = pd.read_csv(f"{ROOT}/tools/quant/data/more_etf/IEF.csv", parse_dates=["date"]
                      ).set_index("date")["close"].sort_index().pct_change()
    cta = pd.read_csv(f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv",
                      parse_dates=["date"]).set_index("date")["ret"]
    return spy.rename("ret"), ief.rename("ret"), cta.rename("ret")


BENCH = {"spy": None, "ief": None, "cta": None}


def v2_battery(name, r_pu, sig, We, net, ref, use_trio=True, scramble_n=200):
    """Full V2 battery per GATES_CONTRACT_V2 §0/§6 Step-1/§7: gates.run with EXPLICIT
    sig=, leak_check=True, ref=champion (never None on an acceptance call), beats_passive
    trio. Fail-closed on anything missing."""
    kw = dict(leak_check=True, scramble_n=scramble_n)
    if use_trio:
        kw.update(beats_passive=True, spy=BENCH["spy"], ief=BENCH["ief"], cta=BENCH["cta"])
    g = bgates.run(r_pu, ref=ref, sig=sig, **kw)
    span_start = net.index[0]
    span_class = ("pre2007" if span_start <= pd.Timestamp("2007-01-01") else
                  "2007plus" if span_start <= pd.Timestamp("2013-01-01") else "inception_fail")
    # era split (the R4 TimesFM bar: >=8y of effect, not one episode)
    eras = {}
    for a, b, tag in [("2000-01-01", "2008-01-01", "2000s"), ("2008-01-01", "2015-01-01", "GFC"),
                      ("2015-01-01", "2021-01-01", "2015-21"), ("2021-01-01", None, "2021+")]:
        m = net[net.index >= pd.Timestamp(a)]
        if b:
            m = m[m.index < pd.Timestamp(b)]
        eras[tag] = round(M.sharpe_d(m), 3) if len(m) > 120 else None
    leak = g.get("leak") or {}
    bp = g.get("beats_passive") or {}
    res = dict(name=name, gates=g, span_class=span_class,
               n=len(net), start=str(span_start.date()), end=str(net.index[-1].date()),
               sr=M.sharpe_d(net), ann=M.ann_geo(net), mdd=M.max_dd(net),
               h1=g["h1"], h2=g["h2"], neg=int(g["neg_years"]), worst=g["worst"],
               corr=g["corr"], scr_p=g["scr_p"], ac1=g["ac1"],
               leak_corr=leak.get("same_period_corr"), leak_flag=leak.get("leak"),
               leak_ok=g.get("leak_ok"),
               bp_ok=g.get("beats_passive_ok"), bp_best=bp.get("best_passive_sr"),
               bp_name=bp.get("best_passive_name"), bp_reason=bp.get("reason"),
               eras=eras, v2_pass=bool(g["pass"]))
    return res


# ------------------------------------------------------------------ grid + main
def plateau_checks(fn, center_params, neighbors):
    out = {}
    for tag, p in [(str(p), p) for p in [center_params] + neighbors]:
        res = fn(p)
        out[tag] = None if res is None else round(res, 4)
    return out


def run_all(save=True, verbose=True):
    px = load_frankfurter()
    rates = load_rates()
    R_total = fx_total_returns(px, rates)   # carry family: spot + accrual, USD leg = 0
    R_spot = returns_from_px(px)            # trend family: spot only
    champ = pd.read_csv(CHAMP_CSV, index_col=0, parse_dates=True).iloc[:, 0]
    BENCH.update(zip(("spy", "ief", "cta"), _benchmarks()))
    grid = []
    # carry family (charter 'carry'): Frankfurter panel + FRED rates, PIT month-end
    for top in (2, 3, 4):
        grid.append((f"CARRY_EWtop{top}_12m", "carry", dict(top=top, k=252)))
    # trend family (charter 'trend')
    for lb in (63, 126, 252):
        for mode in ("LS", "LF"):
            grid.append((f"TREND_mom{lb}_{mode}", "trend", dict(lb=lb, mode=mode)))
    rows = []
    for name, fam, params in grid:
        R = R_total if fam == "carry" else R_spot
        if fam == "carry":
            W = carry_book_weights(px, rates, **params)
        else:
            W = trend_book_weights(px, **params)
        net, We, sig, r_pu = net_of(W, R)
        net = trim_warmup(net, sig)
        idx = net.index
        res = v2_battery(name, r_pu.reindex(idx).fillna(0.0),
                         sig.reindex(idx).fillna(0.0), We, net,
                         ref=champ.reindex(idx).dropna())
        res["matrix_scramble_p"] = matrix_scramble_p(W, R, n=200)
        rows.append(res)
        if verbose:
            print(f"[{name}] n={res['n']} {res['start']}->{res['end']} ({res['span_class']})")
            print(f"    SR {res['sr']:+.3f} ann {res['ann']*100:+.2f}% MDD {res['mdd']*100:.1f}% "
                  f"H1 {res['h1']:+.2f} H2 {res['h2']:+.2f} negyr {res['neg']} "
                  f"worst {res['worst']*100:.1f}%")
            print(f"    corrChamp {res['corr']:+.3f} scr_p {res['scr_p']} "
                  f"mtrx_scr_p {res['matrix_scramble_p']:.3f} "
                  f"leak {res['leak_flag']} (corr {res['leak_corr']:+.4f}) bp_ok {res['bp_ok']} "
                  f"({res['bp_name']} {res['bp_best']}) v2.pass={res['v2_pass']}")
            print(f"    eras {res['eras']}")
        if save:
            os.makedirs(SLEEVES, exist_ok=True)
            pd.DataFrame({"ret": net.values},
                         index=[t.strftime("%Y-%m-%d") for t in net.index]
                         ).to_csv(f"{SLEEVES}/FXCARRY2_R5_{name}.csv", index_label="date")
    if save:
        with open(f"{HERE}/r5_results.json", "w") as f:
            json.dump(rows, f, indent=1, default=str)
        print("saved", f"{HERE}/r5_results.json", "and", len(rows), "sleeves")
    return rows


if __name__ == "__main__":
    run_all()
