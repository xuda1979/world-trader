#!/usr/bin/env python3
"""HUNT_CBOE_IV R8 engine - build + gate the three PRE-REGISTERED CBOE corners.

Pre-registration: work_r8/PRE_REGISTRATION.md (written before any result was seen).
Data: tools/quant/data/cboe_hist/ (coverage: work_r8/r8_coverage.{json,csv}).

Conventions (all T+1, campaign-standard costs):
  * signal s_t uses data ONLY through close t; the POSITION held on day t is s_{t-1}
    (sig = s.shift(1)); it earns the day-t return r_t. This is bt.engine.lag_signal.
  * costs: 6.4 bps ONE-SIDE on FULL |dW| (no 0.5 half-turn), day-1 establishment charged.
  * long/flat only -> no borrow. gross (sum |w|) clipped at 1.0 (unlevered), which is the
    gross_s=1.0 assumption of the ratified V2 section-8 blend machinery (conservative).
  * vol target 10% ann, TRAILING-ONLY (bt.engine.vol_target_scale), clip <=3.

Run: python3 campaign/agents/chief/coord/HUNT_CBOE_IV/work_r8/r8_engine.py
Writes: r8_results.json, r8_candidate_<name>_daily.csv
"""
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore", message=".*Sorting by default.*")
warnings.filterwarnings("ignore", category=FutureWarning)

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")

import numpy as np
import pandas as pd

import bt.gates as gates
from bt.metrics import ann_geo, half_split, max_dd, neg_years, sharpe_d

ROOT = "/Users/daxu/software/world-trader"
CBOE = os.path.join(ROOT, "tools/quant/data/cboe_hist")
WORK = os.path.join(ROOT, "campaign/agents/chief/coord/HUNT_CBOE_IV/work_r8")
CHAMP_PATH = os.path.join(ROOT, "campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")
A5R2_PATH = os.path.join(ROOT, "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv")
SPY_PATH = os.path.join(ROOT, "tools/quant/data/twelvedata/SPY.csv")
IEF_PATH = os.path.join(ROOT, "tools/quant/data/more_etf/IEF.csv")
CTA_PATH = os.path.join(ROOT, "campaign/results/sleeve_library/CTA_15vol.csv")

BPS, RATE, GEAR, ANN = 6.4, 0.045, 1.6, 252.0
TARGET_VOL = 0.10
IS_END = pd.Timestamp("2017-01-01")
PRE2010 = pd.Timestamp("2010-01-01")


# ------------------------------------------------------------------ loaders
def load_close(name):
    """cboe_hist/<name>.csv -> close Series on a DatetimeIndex (dupes: last wins)."""
    df = pd.read_csv(os.path.join(CBOE, name + ".csv"))
    df.columns = [str(c).strip().lower() for c in df.columns]
    idx = pd.to_datetime(df["date"], errors="coerce")
    s = pd.Series(pd.to_numeric(df["close"], errors="coerce").to_numpy(dtype=float),
                  index=pd.DatetimeIndex(idx))
    s = s[s.index.notna()].sort_index()
    s = s[~s.index.duplicated(keep="last")]
    return s.dropna()


def load_ohlc(name):
    """cboe_hist/<name>.csv -> DataFrame[open,high,low,close,volume] on a DatetimeIndex."""
    df = pd.read_csv(os.path.join(CBOE, name + ".csv"))
    df.columns = [str(c).strip().lower() for c in df.columns]
    idx = pd.to_datetime(df["date"], errors="coerce")
    df = df.loc[idx.notna()].copy()
    df.index = pd.DatetimeIndex(idx[idx.notna()])
    for c in ("open", "high", "low", "close", "volume"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df[~df.index.duplicated(keep="last")].sort_index()


def load_ret(path):
    """A [date,ret] (or [date,close]) sleeve/benchmark file -> return Series."""
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float).dropna()


def zscore(s, win):
    m = s.rolling(win, min_periods=win).mean()
    sd = s.rolling(win, min_periods=win).std(ddof=1)
    return (s - m) / sd.replace(0.0, np.nan)


def build_panel():
    """The vol/price panel used by the three pre-registered corners."""
    cols = {}
    for k in ("VIX", "VIX3M", "VIX6M", "GVZ", "OVX", "VVIX"):
        cols[k] = load_close(k)
    spx = load_ohlc("SPX")
    cols["SPX"] = spx["close"]
    cols["SPX_high"] = spx["high"]
    cols["SPX_low"] = spx["low"]
    return pd.DataFrame(cols)


# ------------------------------------------------------------------ signals
def _to_pos(score, thr, sign, mode):
    """sign: +1 as-written in the pre-registration; -1 the disclosed sign-flip.
    mode: 'gate' = binary >thr (PRE-REGISTERED); 'lin' = clip(score,0,1) disclosed extension."""
    sc = (sign * score).dropna()
    if mode == "gate":
        return (sc > thr).astype(float)
    return sc.clip(lower=0.0, upper=1.0)


def sig_c1(lookback, thr, kind, px, sign=1, mode="gate"):
    """C1_VOLBACK: back-end vol-curve slope + curvature. PRE-REGISTERED corner.

    back  = VIX3M/VIX6M - 1        (back-end slope; NEGATIVE in normal upward-sloping curves)
    curv  = VIX6M - 2*VIX3M + VIX  (curve convexity)
    DISCLOSED ECONOMIC AMBIGUITY: the pre-registration says "risk on when the back end is in
    contango". Back-end contango means VIX6M > VIX3M, i.e. the slope is LOW (z<0), so the
    economically correct sign is sign=-1 on z(back). The as-written phrasing reads the other
    way. BOTH are reported in full; neither is claimed as skill.
    """
    back = px["VIX3M"] / px["VIX6M"] - 1.0
    curv = px["VIX6M"] - 2.0 * px["VIX3M"] + px["VIX"]
    if kind == "slope":
        score = zscore(back, lookback)
    elif kind == "curv":
        score = zscore(curv, lookback)
    else:
        score = zscore(back, lookback) + zscore(curv, lookback)
    return _to_pos(score, thr, sign, mode)


def sig_c2(rv_win, z_win, thr, px, sign=1, mode="gate"):
    """C2_VRP: variance risk premium = VIX minus Parkinson realized vol from official SPX OHLC.

    Parkinson RV (annualized) over rv_win: sqrt(mean(ln(H/L)^2)/(4 ln2)) * sqrt(252).
    vrp = VIX - RV. High vrp = variance insurance rich = risk-on. sign=+1 is unambiguous."""
    hl = np.log(px["SPX_high"] / px["SPX_low"]) ** 2
    rv = np.sqrt(hl.rolling(rv_win, min_periods=rv_win).mean() / (4.0 * np.log(2.0))) * np.sqrt(ANN)
    vrp = px["VIX"] - rv
    return _to_pos(zscore(vrp, z_win), thr, sign, mode)


def sig_c3(z_win, thr, px, sign=1, mode="gate"):
    """C3_VOLDISP: cross-asset implied-vol DISPERSION across VIX/GVZ/OVX z-scores.

    disp = cross-sectional std of the three trailing z-scores.
    Low dispersion = one common vol factor = risk-on -> long while disp <= thr.
    Implemented as score = -disp with threshold -thr (identical condition)."""
    z = pd.DataFrame({k: zscore(px[k], z_win) for k in ("VIX", "GVZ", "OVX")})
    disp = z.std(axis=1, ddof=1).dropna()
    return _to_pos((-disp).reindex(px.index), -thr, sign, mode)


# ------------------------------------------------------------------ backtest
def backtest(pos_raw, px, gross_cap=1.0):
    """pos_raw: desired exposure known at close t. Returns aligned series dict.

    sig_t = pos_raw_{t-1} * scale_{t-1} (vol target, trailing-only) -> earns r_t.
    """
    from bt.engine import vol_target_scale
    r = px["SPX"].pct_change()
    scale = vol_target_scale(r.to_frame("r").dropna(), target=TARGET_VOL,
                            window=60, cap=3.0)["r"].reindex(r.index).fillna(1.0)
    w = (pos_raw.reindex(r.index).fillna(0.0) * scale).clip(lower=0.0, upper=gross_cap)
    sig = w.shift(1).fillna(0.0)
    gross = sig.abs()
    prev = sig.shift(1)
    prev.iloc[0] = 0.0
    to = (sig - prev).abs()
    cost = to * BPS / 1e4
    book = sig * r
    port = book - cost
    margin = np.maximum(gross - 1.0, 0.0) * RATE / 252.0
    net = port - margin
    return dict(r=r, sig=sig, w=w, gross=gross, to=to, cost=cost, book=book,
                port=port, margin=margin, net=net)


# ------------------------------------------------------------------ metrics
def metrics(net, gross=None, cost=None):
    n = net.dropna()
    neg, worst = neg_years(n)
    out = dict(n=int(len(n)), sr=round(sharpe_d(n), 4),
               ann_geo=round(ann_geo(n), 6),
               ann_arith=round(float(n.mean() * ANN), 6),
               vol=round(float(n.std(ddof=1) * np.sqrt(ANN)), 6),
               mdd=round(max_dd(n), 6), neg_years=neg,
               worst_year=round(worst, 6) if np.isfinite(worst) else None)
    if gross is not None:
        out["gross_mean"] = round(float(gross.mean()), 6)
        out["gross_max"] = round(float(gross.max()), 6)
        out["exposure_frac"] = round(float((gross > 0).mean()), 6)
    if cost is not None:
        out["cost_bp_yr"] = round(float(cost.mean() * ANN * 1e4), 4)
    return out


def _slice(net, mask, label):
    s = net[mask].dropna()
    if len(s) < 60:
        return {label: dict(n=int(len(s)), note="too short to judge")}
    neg, worst = neg_years(s)
    return {label: dict(n=int(len(s)), sr=round(sharpe_d(s), 4),
                        ann_geo=round(ann_geo(s), 6), mdd=round(max_dd(s), 6),
                        neg_years=neg)}


def stability(net):
    """MANDATORY pre/post-2010 + IS/OOS stability table."""
    ix = net.index
    out = {}
    out.update(_slice(net, ix < PRE2010, "pre2010"))
    out.update(_slice(net, ix >= PRE2010, "post2010"))
    out.update(_slice(net, ix < IS_END, "IS_lt2017"))
    out.update(_slice(net, ix >= IS_END, "OOS_ge2017"))
    return out


def corr_to(a, b):
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1, sort=True).dropna()
    return round(float(j.a.corr(j.b)), 4) if len(j) > 2 else None


# ------------------------------------------------------------------ orchestration
def load_benchmarks():
    """Pinned V2 section 7c benchmarks: twelvedata SPY, more_etf IEF, sleeve_library CTA_15vol."""
    spy = (pd.read_csv(SPY_PATH, index_col="date", parse_dates=True)["close"]
           .astype(float).pct_change().dropna())
    ief = (pd.read_csv(IEF_PATH, index_col="date", parse_dates=True)["close"]
           .astype(float).pct_change().dropna())
    cta = (pd.read_csv(CTA_PATH, index_col="date", parse_dates=True)["ret"]
           .astype(float).dropna())
    return spy, ief, cta


def span_class_of(first):
    if first < pd.Timestamp("2007-01-01"):
        return "pre2007"
    if first < pd.Timestamp("2013-01-01"):
        return "2007plus"
    return "inception_fail"


def ser(o):
    """numpy/pandas -> plain python for json."""
    if isinstance(o, dict):
        return {str(k): ser(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [ser(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        f = float(o)
        return f if np.isfinite(f) else None
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, float) and not np.isfinite(o):
        return None
    if isinstance(o, pd.Timestamp):
        return str(o.date())
    return o


def eval_candidate(pos_raw, px, champ, a5, spy, ief, cta, do_gates=True):
    """Build the sleeve on its own admissible span and run the full battery."""
    fv = pos_raw.first_valid_index()
    if fv is None:
        return dict(error="signal never defined")
    idx = champ.index[champ.index >= fv]
    if len(idx) < 300:
        return dict(error="span too short", n=int(len(idx)), first_valid=str(fv.date()))
    bt = backtest(pos_raw, px.reindex(idx), gross_cap=1.0)
    ok = bt["r"].notna() & bt["sig"].notna()
    S = {k: v[ok] for k, v in bt.items()}
    net = S["net"]
    rec = dict(n=int(len(net)),
               span=[str(net.index[0].date()), str(net.index[-1].date())],
               span_class=span_class_of(net.index[0]),
               metrics=metrics(net, S["gross"], S["cost"]),
               stability=stability(net),
               corr_champ=corr_to(net, champ),
               corr_A5r2=corr_to(net, a5))
    if do_gates:
        g = gates.run(S["r"], ref=champ.reindex(net.index), sig=S["sig"], leak_check=True,
                      beats_passive=True, spy=spy, ief=ief, cta=cta, scramble_n=200)
        rec["gates"] = ser(g)
        rec["gate_pass"] = bool(g["pass"])
    rec["_net"] = net
    rec["_pos"] = S["sig"]
    return rec


PARAM_BUILDERS = {
    "C1": lambda px, p, sign, mode: sig_c1(p[0], p[1], p[2], px, sign, mode),
    "C2": lambda px, p, sign, mode: sig_c2(p[0], p[1], p[2], px, sign, mode),
    "C3": lambda px, p, sign, mode: sig_c3(p[0], p[1], px, sign, mode),
}
# PREREG = the pre-registered reading (as-written). The other three are DISCLOSED
# extensions forced by the sign ambiguity documented in sig_c1; all are reported IN FULL
# and are NOT a search for a winning cell (see the multiple-testing note in FINDINGS).
VARIANTS = [("PREREG", 1, "gate"), ("FLIP", -1, "gate"),
            ("LIN_ASWRITTEN", 1, "lin"), ("LIN_FLIP", -1, "lin")]
RUNGS = (0.025, 0.05, 0.075, 0.10, 0.15)


def grid_c1():
    return {"C1_L%d_t%s_%s" % (L, str(t).replace(".", ""), k): (L, t, k)
            for L in (21, 63, 126, 252) for t in (0.5, 1.0, 1.5)
            for k in ("both", "slope", "curv")}


def grid_c2():
    return {"C2_rv%d_z%d_t%s" % (rv, zw, str(t).replace(".", "")): (rv, zw, t)
            for rv in (10, 21, 63) for zw in (63, 252) for t in (0.0, 0.5, 1.0)}


def grid_c3():
    return {"C3_z%d_t%s" % (zw, str(t).replace(".", "")): (zw, t)
            for zw in (63, 126, 252) for t in (0.5, 1.0, 1.5)}


GRIDS = {"C1": grid_c1, "C2": grid_c2, "C3": grid_c3}
PRIMARY = {"C1": "C1_L63_t10_both", "C2": "C2_rv21_z63_t00", "C3": "C3_z126_t10"}


def run_grid(prefix, grid, px, champ, a5, spy, ief, cta):
    """Evaluate the pre-registered grid x the 4 disclosed sign/mode variants."""
    table = {}
    for vname, sign, mode in VARIANTS:
        for key, params in grid.items():
            r = eval_candidate(PARAM_BUILDERS[prefix](px, params, sign, mode),
                               px, champ, a5, spy, ief, cta, do_gates=False)
            k = "%s|%s" % (key, vname)
            if "error" in r:
                table[k] = {"error": r["error"]}
            else:
                table[k] = {"params": str(params), "variant": vname, "n": r["n"],
                            "span": r["span"], "span_class": r["span_class"],
                            "sr": r["metrics"]["sr"], "ann": r["metrics"]["ann_geo"],
                            "mdd": r["metrics"]["mdd"],
                            "neg_years": r["metrics"]["neg_years"],
                            "cost_bp_yr": r["metrics"]["cost_bp_yr"],
                            "exposure": r["metrics"]["exposure_frac"],
                            "corr_champ": r["corr_champ"], "corr_A5r2": r["corr_A5r2"]}
    return table


def ladder_via_ref(net_s, champ, name):
    """V2 section 8 ladder using the RATIFIED reference impl (HUNT_VOL2/work_r3/blend_r3_lib).

    CHARTER WEIGHT CONVENTION: w is the SLEEVE slice; the champion gets (1-w).
    blend_metrics charges the constant-mix rebalance-drift turnover at 6.4bps FULL |dW| and
    re-prices margin on blended gross-1. gross_s is pinned at 1.0 there; our sleeve is
    unlevered by construction (gross<=1.0), so that pin is an UPPER bound on our true gross
    -> conservative (slightly over-charges margin).
    """
    _d = os.path.join(ROOT, "campaign/agents/chief/coord/HUNT_VOL2/work_r3")
    if _d not in sys.path:
        sys.path.insert(0, _d)
    import blend_r3_lib as B
    idx = champ.index.intersection(net_s.dropna().index)
    nc = champ.reindex(idx)
    ns = net_s.reindex(idx)
    if ns.isna().any():
        raise ValueError("ladder: sleeve net missing champion days")
    ann_c, sr_c, mdd_c = float(ann_geo(nc)), float(sharpe_d(nc)), float(max_dd(nc))
    h1_c, h2_c = B._halves(nc)
    rows = []
    for w in RUNGS:
        m = B.blend_metrics(nc, ns, w)
        rows.append(dict(candidate=name, w=float(w),
                         d_ann_pp=(m["ann"] - ann_c) * 100.0,
                         d_sr=m["sr"] - sr_c,
                         d_mdd_pp=(m["mdd"] - mdd_c) * 100.0,
                         d_h1=m["h1"] - h1_c, d_h2=m["h2"] - h2_c,
                         neg_years=int(m["neg_years"]), gross=m["gross"],
                         ann=m["ann"] * 100.0, sr=m["sr"], mdd=m["mdd"] * 100.0,
                         h1=m["h1"], h2=m["h2"], worst_year=m["worst_year"] * 100.0,
                         drift_cost_bp_yr=m["drift_cost_bp_yr"], n=m["n"],
                         window="OVERLAP[%s..%s]" % (idx[0].date(), idx[-1].date())))
    tbl = pd.DataFrame(rows)
    verdict = B.gates_for(tbl, name)
    base = dict(window=[str(idx[0].date()), str(idx[-1].date())], n=int(len(idx)),
                champ_ann=ann_c, champ_sr=sr_c, champ_mdd=mdd_c,
                champ_h1=h1_c, champ_h2=h2_c)
    return base, rows, verdict


def main():
    px = build_panel()
    champ = load_ret(CHAMP_PATH)
    a5 = load_ret(A5R2_PATH)
    spy, ief, cta = load_benchmarks()
    j = pd.concat([champ.rename("c"), a5.rename("a")], axis=1, sort=True).dropna()
    out = {"champion": dict(path=CHAMP_PATH, n=int(len(champ)),
                            sr=round(float(sharpe_d(champ)), 4),
                            ann=round(float(ann_geo(champ)), 6),
                            mdd=round(float(max_dd(champ)), 6)),
           "a5r2": dict(path=A5R2_PATH, n=int(len(a5.dropna())),
                        sr=round(float(sharpe_d(a5.dropna())), 4),
                        ann=round(float(ann_geo(a5.dropna())), 6),
                        mdd=round(float(max_dd(a5.dropna())), 6),
                        corr_champ=round(float(j.c.corr(j.a)), 4)),
           "grids": {}, "primaries": {}, "ladder": {}, "leak": {}, "best_cell": {}}
    for prefix in ("C1", "C2", "C3"):
        grid = GRIDS[prefix]()
        table = run_grid(prefix, grid, px, champ, a5, spy, ief, cta)
        out["grids"][prefix] = ser(table)
        pp = grid[PRIMARY[prefix]]
        prim = eval_candidate(PARAM_BUILDERS[prefix](px, pp, 1, "gate"),
                              px, champ, a5, spy, ief, cta, do_gates=True)
        net = prim.pop("_net")
        pos_s = prim.pop("_pos")
        out["primaries"][prefix] = ser(dict(primary_key=PRIMARY[prefix],
                                            params=str(pp), **prim))
        net.to_frame("ret").to_csv(os.path.join(WORK, "r8_candidate_%s_PRIMARY_daily.csv" % prefix))
        fb, rows, verdict = ladder_via_ref(net, champ, prefix + "_PRIMARY")
        out["ladder"][prefix + "_PRIMARY"] = ser(dict(base=fb, rows=rows, verdict=verdict))
        from bt.leakcheck import leak_probe
        ss = px["SPX"].pct_change().reindex(pos_s.index)
        out["leak"][prefix] = ser(leak_probe(pos_s, ss))
        cand = {k: v for k, v in table.items() if "sr" in v}
        bk = max(cand, key=lambda k: cand[k]["sr"])
        bkey, bvar = bk.split("|")
        bsign = 1 if bvar in ("PREREG", "LIN_ASWRITTEN") else -1
        bmode = "gate" if bvar in ("PREREG", "FLIP") else "lin"
        brec = eval_candidate(PARAM_BUILDERS[prefix](px, grid[bkey], bsign, bmode),
                              px, champ, a5, spy, ief, cta, do_gates=True)
        bnet = brec.pop("_net")
        brec.pop("_pos")
        out["best_cell"][prefix] = ser(dict(cell=bk, **brec))
        bb, br, bv = ladder_via_ref(bnet, champ, prefix + "_BESTCELL")
        out["ladder"][prefix + "_BESTCELL"] = ser(dict(base=bb, rows=br, verdict=bv))
        print("[%s] PREREG %s n=%d SR=%s ann=%s mdd=%s corrChamp=%s corrA5r2=%s costbp=%.0f"
              % (prefix, PRIMARY[prefix], prim["n"], prim["metrics"]["sr"],
                 prim["metrics"]["ann_geo"], prim["metrics"]["mdd"],
                 prim["corr_champ"], prim["corr_A5r2"], prim["metrics"]["cost_bp_yr"]))
        print("      BESTCELL %s SR=%s ann=%s mdd=%s corrChamp=%s corrA5r2=%s"
              % (bk, brec["metrics"]["sr"], brec["metrics"]["ann_geo"],
                 brec["metrics"]["mdd"], brec["corr_champ"], brec["corr_A5r2"]))
        print("      ladder best dAnn: PREREG=%.3f BESTCELL=%.3f"
              % (max(r["d_ann_pp"] for r in rows), max(r["d_ann_pp"] for r in br)))
    with open(os.path.join(WORK, "r8_results.json"), "w") as fh:
        json.dump(ser(out), fh, indent=1)
    print("wrote r8_results.json")


if __name__ == "__main__":
    main()
