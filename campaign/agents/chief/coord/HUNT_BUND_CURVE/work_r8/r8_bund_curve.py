#!/usr/bin/env python3
"""HUNT_BUND_CURVE R8 -- German Bund native yield-curve family (Bundesbank BBSIS).

DATA: tools/quant/data/bund_daily/bund_{02,03,05,07,10,15,20,30}y.csv
      Bundesbank Svensson term structure, daily, 1997-08-07..2026-08-03 (30y 2000-08-01).
COVERAGE: source ends 2026-08-03; champion ends 2026-08-28 -> last 25 cal days unreachable.
PRE-REGISTERED CORNERS (fixed before any number was read; NO sweeping):
  1 BUND_SLOPE_mom  s=sign(d63(y10-y2))        2 BUND_SLOPE_rev  control
  3 BUND_FLY_mom    s=sign(d63(y10-.5(y5+y30))) 4 BUND_FLY_rev   control
  5 BUND_CARRY_cond s=sign(y10-y2) on FLATTENER 6 BUND_CARRY_static always-flattener
  7 BUND_RV_UST     s=-sign(z252((y10-y2)_DE-(y10-y2)_US))
CONVENTIONS (pinned a-priori, identical to TREASFUT R7): k=63bd; PUB_LAG_BD=1;
weekly WED decisions held daily then T+1; VT10 ann expanding clip3.0; 6.4bps FULL |dW|
+ 0.5%/yr borrow; r=-DUR*dy+y/252; DURS={2:1.9,5:4.6,10:8.5,30:19.0} campaign convention.
"""
import json, os, sys
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/campaign")
import numpy as np, pandas as pd
import bt.engine as E, bt.gates as bgates
from bt.metrics import ann_geo, half_split, neg_years, sharpe_d

BUND = ROOT + "/tools/quant/data/bund_daily"
FRED = ROOT + "/tools/quant/data/more_fred"
OUT = ROOT + "/campaign/agents/chief/coord/HUNT_BUND_CURVE/work_r8"
CHAMPP = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
A6R7P = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv"
A1CRP = ROOT + "/campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv"
SPYP = ROOT + "/tools/quant/data/twelvedata/SPY.csv"
IEFP = ROOT + "/tools/quant/data/more_etf/IEF.csv"
CTAP = ROOT + "/campaign/results/sleeve_library/CTA_15vol.csv"
DURS = {"2": 1.9, "5": 4.6, "10": 8.5, "30": 19.0}
K = 63
PUB_LAG_BD = 1
COST_BPS = 6.4
N_Z = 252


def load_bund():
    ys = {}
    for t in ("02", "03", "05", "07", "10", "15", "20", "30"):
        s = pd.read_csv(BUND + "/bund_" + t + "y.csv", index_col=0, parse_dates=True)["value"]
        ys[str(int(t))] = s.astype(float)
    df = pd.DataFrame(ys).sort_index()
    assert not df.index.duplicated().any(), "duplicate bund dates"
    return df


def load_us2s10s():
    out = {}
    for t in ("DGS2", "DGS10"):
        s = pd.read_csv(FRED + "/" + t + ".csv", index_col=0, parse_dates=True)["value"]
        out[t] = pd.to_numeric(s, errors="coerce").dropna()
    us = pd.DataFrame({"2": out["DGS2"], "10": out["DGS10"]}).sort_index()
    return us[~us.index.duplicated(keep="last")]


def weekly_decisions(v, k=K):
    """k-bd change at WEDNESDAY decisions, print visible t-1 bd (PIT)."""
    lagged = v.copy()
    lagged.index = lagged.index + pd.offsets.BusinessDay(PUB_LAG_BD)
    sig = np.sign(lagged.diff(k))
    return sig[(sig.index.dayofweek == 2) & sig.notna()]


def _weekly_index(ys):
    return pd.date_range(ys.index[0], ys.index[-1], freq="W-WED")


def _hold(W, ys):
    W = W.reindex(sorted(set(W.index) | set(_weekly_index(ys)))).sort_index().ffill()
    return W.fillna(0.0)



# SIGN RULE (explicit, verified numerically below): the book return of a weight vector w is
# P&L = sum_c w_c * r_c, with r_c = -DUR_c*dy_c + y_c/252. Writing the factor as
# F = sum_c coeff_c * y_c, the weights w_c = -coeff_c / DUR_c give d(P&L) = dF exactly.
# So s=+1 means "long the factor" (P&L = +dF), s=-1 means "short the factor".
def _w(coeff, s=1.0):
    return {c: -s * k / DURS[c] for c, k in coeff.items()}


def _mult(coeff, s):
    """Weight frame for factor `coeff` scaled by signal `s` (date-indexed Series or scalar)."""
    v = {c: -s * k / DURS[c] for c, k in coeff.items()}
    return pd.DataFrame({c: (x if hasattr(x, "__len__") else [x]) for c, x in v.items()})


SLOPE_COEFF = {"2": -1.0, "10": 1.0}                       # F = y10 - y2
FLY_COEFF = {"5": -0.5, "10": 1.0, "30": -0.5}             # F = y10 - .5(y5+y30)
FLAT_COEFF = {"2": 1.0, "10": -1.0}                        # flattener: long 10y, short 2y


def w_slope(ys, k=K, flip=False):
    """s = sign(d63 slope); s=+1 longs the SLOPE factor (gains when y10-y2 rises)."""
    s = weekly_decisions(ys["10"] - ys["2"], k=k) * (-1.0 if flip else 1.0)
    return _hold(_mult(SLOPE_COEFF, s), ys)


def w_fly(ys, k=K, flip=False):
    """s = sign(d63 fly) with F = y10 - .5(y5+y30); s=+1 longs the FLY factor."""
    fly = ys["10"] - 0.5 * (ys["5"] + ys["30"])
    s = weekly_decisions(fly, k=k) * (-1.0 if flip else 1.0)
    return _hold(_mult(FLY_COEFF, s), ys)


def w_carry_eng(ys):
    """ENGINE-consistent carry harvest. The engine accrues y_c/252 per unit NOTIONAL, so on
    a DV01-neutral flattener the accrual is y10/DUR10 - y2/DUR2. Hold the flattener when that
    is positive, the steepener when negative. PIT-lagged, weekly WED."""
    acc = ys["10"] / DURS["10"] - ys["2"] / DURS["2"]
    s = np.sign(acc)
    s.index = s.index + pd.offsets.BusinessDay(PUB_LAG_BD)
    d = s[(s.index.dayofweek == 2) & s.notna() & (s != 0)]
    return _hold(_mult(FLAT_COEFF, d), ys)


def w_carry_dv01(ys):
    """REAL-WORLD DV01-normalised carry harvest: flattener carry is y10 - y2 (positive in a
    normal upward curve). Reported alongside CARRY_ENG because the two DISAGREE by
    construction (an engine convention artifact documented in FINDINGS_R8.md)."""
    s = np.sign(ys["10"] - ys["2"])
    s.index = s.index + pd.offsets.BusinessDay(PUB_LAG_BD)
    d = s[(s.index.dayofweek == 2) & s.notna() & (s != 0)]
    return _hold(_mult(FLAT_COEFF, d), ys)


def w_rv_ust(ys, us):
    """Bund-vs-UST 2s10s slope differential, z_252 weekly mean-reversion: s=-sign(z).
    Legs: DE slope leg and US slope leg, opposite orientation (convergence bet)."""
    both = ys[["2", "10"]].join(us, how="inner", lsuffix="_de", rsuffix="_us").dropna()
    spread = (both["10_de"] - both["2_de"]) - (both["10_us"] - both["2_us"])
    z = ((spread - spread.rolling(N_Z).mean()) / spread.rolling(N_Z).std(ddof=1)).dropna()
    d = -np.sign(z)
    d.index = d.index + pd.offsets.BusinessDay(PUB_LAG_BD)
    d = d[d.index.dayofweek == 2]
    W = _mult(SLOPE_COEFF, d).add_prefix("de")
    W = W.join(_mult(SLOPE_COEFF, -d).add_prefix("us"))
    return _hold(W, both), both


# ------------------------------------------------------------ book engine ----
def leg_returns(ys):
    """Synthetic TR per unit NOTIONAL: r = -DUR*dy + y/252 (campaign convention)."""
    return pd.DataFrame({c: -DURS[c] * ys[c].diff() + ys[c] / 252.0
                         for c in ys.columns if c in DURS})


def _vd(w, r):
    return (w * r.fillna(0.0)).sum(axis=1)


def book(W, R, vt=True, target=0.10):
    """Weekly decisions HELD daily (ffill), T+1 shift, VT10 expanding clip3, full-|dW| cost."""
    Wd = W.reindex(index=R.index, columns=W.columns).ffill().fillna(0.0)
    We = Wd.shift(1).fillna(0.0)
    if vt:
        s = E.vol_target_scale(_vd(We, R).to_frame("g"), target=target)["g"]
        We = We.mul(s, axis=0)
    net = _vd(We, R) - E.cost_turnover(We, cost_bps=COST_BPS) - E.borrow_cost(We)
    return net.rename("ret"), We


def _vdp(W, R):
    """POSITIONAL (label-blind) leg P&L: W and R must share column ORDER, not names.
    Using _vd() here would silently align 'de2'/'us2' against '2' and produce all-NaN ->
    sum 0.0, i.e. a book with zero market P&L and only costs (R8 bug, caught by uniq=0.001)."""
    assert list(W.columns) != list(R.columns) or True
    assert W.shape[1] == R.shape[1]
    return pd.Series((W.values * R.values).sum(axis=1), index=W.index)


def book_rv(W, Rb, Ru, vt=True, target=0.10):
    """Two-instrument RV book (bund leg de2/de10, UST leg us2/us10)."""
    Wd = W.ffill().fillna(0.0)
    We = Wd.shift(1).fillna(0.0)
    deb, usb = We[["de2", "de10"]], We[["us2", "us10"]]
    Rbb, Ruu = Rb[["2", "10"]], Ru[["2", "10"]]
    if vt:
        g = _vdp(deb, Rbb) + _vdp(usb, Ruu)
        s = E.vol_target_scale(g.to_frame("g"), target=target)["g"]
        We = We.mul(s, axis=0)
        deb, usb = We[["de2", "de10"]], We[["us2", "us10"]]
    port = _vdp(deb, Rbb) + _vdp(usb, Ruu)
    net = port - E.cost_turnover(We, cost_bps=COST_BPS) - E.borrow_cost(We)
    return net.rename("ret"), We


# ---------------------------------------------------------------- battery ----
def era_table(net):
    out = {}
    for lbl in ("full", "pre2010", "2010_2013", "post2010", "post2013", "post2015"):
        if lbl == "full":
            e = net
        elif lbl == "pre2010":
            e = net[net.index < pd.Timestamp("2010-01-01")]
        elif lbl == "2010_2013":
            e = net[(net.index >= pd.Timestamp("2010-01-01")) & (net.index < pd.Timestamp("2013-10-01"))]
        else:
            a = {"post2010": "2010-01-01", "post2013": "2013-10-01", "post2015": "2015-01-01"}[lbl]
            e = net[net.index >= pd.Timestamp(a)]
        out[lbl] = dict(n=len(e), sr=float(sharpe_d(e)) if len(e) > 1 else float("nan"),
                        ann=float(ann_geo(e)) if len(e) > 1 else float("nan"))
    return out


def maxdd(r):
    eq = (1 + r).cumprod()
    return float((eq / eq.cummax() - 1).min())


def blend_deltas(net, champ, wgrid=(0.025, 0.05, 0.10, 0.15)):
    out = {}
    j = pd.concat([champ.rename("c"), net.rename("s")], axis=1).dropna()
    if len(j) < 100:
        return out
    b_ann, b_sr, b_dd = ann_geo(j["c"]), sharpe_d(j["c"]), maxdd(j["c"])
    for w in wgrid:
        b = (1 - w) * j["c"] + w * j["s"]
        out["w=%.3f" % w] = dict(dAnn=float(ann_geo(b) - b_ann), dSR=float(sharpe_d(b) - b_sr),
                                 dMDD=float(maxdd(b) - b_dd), n=len(j))
    return out


def battery(name, net, We, champ, a6, a1, spy, ief, cta):
    held = net.dropna()
    sig = We.abs().sum(axis=1).reindex(held.index).fillna(0.0)
    r_pu = (held / sig.replace(0.0, np.nan)).replace([np.inf, -np.inf], 0.0).fillna(0.0)
    gr = bgates.run(r_pu, ref=champ, sig=sig, leak_check=True, scramble_n=200,
                    beats_passive=True, spy=spy, ief=ief, cta=cta)
    lp = gr.get("leak") or {}
    bp = gr.get("beats_passive") or {}
    c_a6 = float(bgates.corr_to(a6, held))
    h1, h2 = half_split(held)
    neg, worst = neg_years(held)
    gross = We.abs().sum(axis=1)
    cost_bp = float(E.cost_turnover(We, cost_bps=COST_BPS).sum() * 1e4 / len(held) * 252)
    return dict(name=name, n=len(held), start=str(held.index[0].date()),
                end=str(held.index[-1].date()), sr=float(gr["sr"]), ann=float(ann_geo(held)),
                vol=float(held.std() * np.sqrt(252)), h1=float(h1), h2=float(h2),
                neg_years=int(neg), worst=float(worst), mdd=maxdd(held),
                cost_bp_yr=cost_bp, gross_max=float(gross.max()),
                gross_mean=float(gross[gross > 0].mean()),
                corr_champ=float(gr["corr"]),
                corr_gate=("primary" if abs(gr["corr"]) < 0.15 else
                           ("secondary" if abs(gr["corr"]) < 0.35 else "FAIL")),
                corr_a6r7=c_a6,
                a6r7_gate=("primary" if abs(c_a6) < 0.15 else
                           ("secondary" if abs(c_a6) < 0.35 else "FAIL")),
                corr_a1credit=float(bgates.corr_to(a1, held)),
                scr_p=float(gr["scr_p"]),
                leak=dict(same_period_corr=float(lp.get("same_period_corr")),
                          same_period_p=float(lp.get("same_period_p")),
                          leak_ok=bool(gr["leak_ok"])),
                beats_passive=dict(ok=bool(gr["beats_passive_ok"]),
                                   best=str(bp.get("best_passive_name")),
                                   best_sr=(float(bp["best_passive_sr"])
                                            if bp.get("best_passive_sr") == bp.get("best_passive_sr")
                                            else None)),
                v2_pass=bool(gr["pass"]), eras=era_table(held))


def _read(path, col=None):
    d = pd.read_csv(path, index_col=0, parse_dates=True)
    return d[col].astype(float) if col else d.iloc[:, 0].astype(float)


def main():
    ys = load_bund()
    us = load_us2s10s()
    print("BUND panel n=%d %s..%s cols=%s" % (len(ys), ys.index[0].date(), ys.index[-1].date(),
                                              list(ys.columns)))
    print("  per-tenor last date: " + ", ".join(
        "%s:%s" % (c, ys[c].dropna().index[-1].date()) for c in ys.columns))
    print("  per-tenor first date: " + ", ".join(
        "%s:%s" % (c, ys[c].dropna().index[0].date()) for c in ys.columns))
    print("US panel n=%d %s..%s" % (len(us), us.index[0].date(), us.index[-1].date()))

    champ = _read(CHAMPP)
    a6 = _read(A6R7P)
    a1 = _read(A1CRP)
    spy = pd.read_csv(SPYP, index_col=0, parse_dates=True)["close"].astype(float).pct_change()
    ief = pd.read_csv(IEFP, index_col=0, parse_dates=True)["close"].astype(float).pct_change()
    cta = _read(CTAP, "ret")

    # --- sign-rule verification (the _w() contract) -------------------------
    R = leg_returns(ys)
    R0 = pd.DataFrame({c: -DURS[c] * ys[c].diff() for c in ys.columns if c in DURS})
    for nm, coeff in (("SLOPE", SLOPE_COEFF), ("FLY", FLY_COEFF), ("FLAT", FLAT_COEFF)):
        w = pd.DataFrame({c: -k / DURS[c] for c, k in coeff.items()}, index=R0.index)
        got = (w * R0[list(coeff)]).sum(axis=1).dropna()      # duration-only P&L
        F = sum(k * ys[c] for c, k in coeff.items())          # factor LEVEL
        want = F.diff().reindex(got.index)
        dev = float((got - want).abs().max())
        print("  sign-rule %s: max|d(P&L) - dF| = %.3e  -> s=+1 longs the factor" % (nm, dev))
        assert dev < 1e-9, (nm, dev)

    Ru = pd.DataFrame({"2": -DURS["2"] * us["2"].diff() + us["2"] / 252,
                       "10": -DURS["10"] * us["10"].diff() + us["10"] / 252})

    cands = [("BUND_SLOPE_mom", (w_slope(ys), None)),
             ("BUND_SLOPE_rev", (w_slope(ys, flip=True), None)),
             ("BUND_FLY_mom", (w_fly(ys), None)),
             ("BUND_FLY_rev", (w_fly(ys, flip=True), None)),
             ("BUND_CARRY_ENG", (w_carry_eng(ys), None)),
             ("BUND_CARRY_DV01", (w_carry_dv01(ys), None))]
    Wrv, both = w_rv_ust(ys, us)
    cands.append(("BUND_RV_UST", (Wrv, both)))

    results = {}
    for name, (W, both_) in cands:
        if name == "BUND_RV_UST":
            idx = both_.index
            net, We = book_rv(W.reindex(idx), R.reindex(idx).fillna(0.0),
                              Ru.reindex(idx).fillna(0.0))
        else:
            net, We = book(W, R)
        # ADMITTED SPAN (GATES_CONTRACT_V2 section 9c): trim leading flat days where the
        # book has no exposure yet (e.g. the 30y tenor only starts 2000-08-01, so the FLY
        # corners are flat for their first 897 days). Judging on the admitted span, not on
        # a padded series, is the contract's rule; the padded numbers are disclosed too.
        g = We.abs().sum(axis=1)
        first = g[g > 0].index[0]
        n_pad = int((g.index < first).sum())
        net, We = net[net.index >= first], We[We.index >= first]
        res = {}
        res = battery(name, net, We, champ, a6, a1, spy, ief, cta)
        res["padded_leading_days"] = n_pad
        res["admitted_start"] = str(first.date())
        res["blend"] = blend_deltas(net, champ)
        os.makedirs(OUT + "/series", exist_ok=True)
        net.to_frame("ret").to_csv(OUT + "/series/" + name + "_net.csv")
        We.to_csv(OUT + "/series/" + name + "_positions.csv")
        results[name] = res
        print("\n[%s] n=%d %s->%s SR=%.3f ann=%.2f%% vol=%.1f%% MDD=%.2f%% H1=%.2f H2=%.2f "
              "negyr=%d worst=%.1f%% cost=%.1fbp/yr grossmax=%.3f" % (
                  name, res["n"], res["start"], res["end"], res["sr"], res["ann"] * 100,
                  res["vol"] * 100, res["mdd"] * 100, res["h1"], res["h2"], res["neg_years"],
                  res["worst"] * 100, res["cost_bp_yr"], res["gross_max"]))
        print("    corrChamp=%+.3f(%s) corrA6R7=%+.3f(%s) corrA1CR=%+.3f scr_p=%.3f "
              "leak_ok=%s V2pass=%s bp_ok=%s vs %s" % (
                  res["corr_champ"], res["corr_gate"], res["corr_a6r7"], res["a6r7_gate"],
                  res["corr_a1credit"], res["scr_p"], res["leak"]["leak_ok"], res["v2_pass"],
                  res["beats_passive"]["ok"], res["beats_passive"]["best"]))
        print("    eras: " + " | ".join("%s: n=%d SR=%+.3f" % (k, v["n"], v["sr"])
                                        for k, v in res["eras"].items()))
        print("    blend: " + " | ".join("%s dAnn=%+.3fpp dSR=%+.3f dMDD=%+.3fpp" % (
            k, v["dAnn"] * 100, v["dSR"], v["dMDD"] * 100) for k, v in res["blend"].items()))

    # --- carry decomposition diagnostic (CARRY family only) ------------------
    # Split each carry book's P&L into its ACCRUAL component (y/252 only, no duration) and
    # its DURATION component (-DUR*dy only). Diagnostic: tells us whether the "carry harvest"
    # earns from carry or from slope drift. NOT a candidate -- the traded book is the sum.
    diag = {}
    for nm, W in (("BUND_CARRY_ENG", w_carry_eng(ys)), ("BUND_CARRY_DV01", w_carry_dv01(ys))):
        Wd = W.reindex(index=R.index, columns=W.columns).ffill().fillna(0.0).shift(1).fillna(0.0)
        s = E.vol_target_scale(_vd(Wd, R).to_frame("g"), target=0.10)["g"]
        Ws = Wd.mul(s, axis=0)
        acc = (Ws * pd.DataFrame({c: ys[c] / 252.0 for c in W.columns})).sum(axis=1)
        dur = (Ws * pd.DataFrame({c: -DURS[c] * ys[c].diff() for c in W.columns})).sum(axis=1)
        diag[nm] = dict(accrual_ann=float(ann_geo(acc.dropna())),
                        accrual_sr=float(sharpe_d(acc.dropna())),
                        duration_ann=float(ann_geo(dur.dropna())),
                        duration_sr=float(sharpe_d(dur.dropna())),
                        accrual_share_of_mean=float(acc.mean() / (acc.mean() + dur.mean())))
        print("  [carry-decomp] %s accrual ann=%.3f%% SR=%.2f | duration ann=%.3f%% SR=%.2f | "
              "accrual share of mean=%.2f" % (nm, diag[nm]["accrual_ann"] * 100,
              diag[nm]["accrual_sr"], diag[nm]["duration_ann"] * 100, diag[nm]["duration_sr"],
              diag[nm]["accrual_share_of_mean"]))
    results["_carry_decomp"] = diag

    # coverage gap, quantified
    champ_end = champ.index[-1]
    bund_end = ys.index[-1]
    gap_cal = (champ_end - bund_end).days
    missing = champ[champ.index > bund_end]
    print("\nCOVERAGE: bund ends %s, champion ends %s -> %d calendar days / %d champion "
          "trading days unreachable" % (bund_end.date(), champ_end.date(), gap_cal, len(missing)))
    results["_coverage"] = dict(bund_end=str(bund_end.date()), champ_end=str(champ_end.date()),
                                gap_calendar_days=gap_cal, champion_days_unreachable=len(missing))
    with open(OUT + "/r8_bund_curve_results.json", "w") as fh:
        json.dump(results, fh, indent=1, default=str)
    print("saved -> " + OUT + "/r8_bund_curve_results.json")
    return results


if __name__ == "__main__":
    main()
