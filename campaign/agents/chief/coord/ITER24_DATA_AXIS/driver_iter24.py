
#!/usr/bin/env python3
"""ITER24 DATA-AXIS driver. Deterministic, random-free. Parts:
  1 = raw-data hygiene screens (fail-closed, CFX4 lesson)
  2 = candidate sleeve construction (frozen a6r7 recipe) + standalone stats + correlations
  3 = greedy pool refit + gates per FINDINGS_PRECOMMIT.md
Usage: python3 driver_iter24.py --part N [--keep LOG]
All paths absolute; cwd-independent. No parameter search anywhere.
"""
import argparse, json, sys
import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROOT = "/Users/daxu/software/world-trader"
OUT = ROOT + "/campaign/agents/chief/coord/ITER24_DATA_AXIS"
DATA = ROOT + "/tools/quant/data"
IS_END = pd.Timestamp("2017-01-01")
START = pd.Timestamp("2008-03-31")
K, CAD, VT, CAP, BPS = 378, 42, 0.12, 5.0, 6.4

RAW = dict(
    bund2y   = DATA + "/bund_daily/bund_02y.csv",
    bund10y  = DATA + "/bund_daily/bund_10y.csv",
    cad2y    = DATA + "/dm_rates/cad_govt_2y.csv",
    cad10y   = DATA + "/dm_rates/cad_govt_10y.csv",
    selic    = DATA + "/em_rates/brazil_selic.csv",
    usdbrl   = DATA + "/em_rates/brazil_usdbrl.csv",
)

def load_val(path):
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    s = df["value"].astype(float)
    s = s[~s.index.duplicated(keep="last")].sort_index()
    return s

def max_run(vals):
    # longest run of identical consecutive values
    if len(vals) == 0:
        return 0
    grp = (vals != vals.shift()).cumsum()
    return int(vals.groupby(grp).size().max())

def screen(name, s, spike_lim):
    r = dict(name=name, n=int(len(s)), first=str(s.index[0].date()),
             last=str(s.index[-1].date()), nan=int(s.isna().sum()))
    r["max_flat_run"] = max_run(s)
    dy = s.diff().abs()
    spikes = dy[dy > spike_lim]
    r["n_spike_gt_lim"] = int(len(spikes))
    r["spike_dates"] = [str(pd.Timestamp(t).date()) for t in spikes.index[:12]]
    r["spike_vals"] = [float(v) for v in spikes.values[:12]]
    # recent level sample for unit eyeball
    r["tail3"] = [float(v) for v in s.tail(3)]
    r["head3"] = [float(v) for v in s.head(3)]
    return r

def part1():
    print("=== PART 1: RAW-DATA HYGIENE (fail-closed) ===")
    rep = []
    for nm, path in RAW.items():
        s = load_val(path)
        lim = 1.0 if "usdbrl" not in nm else 0.10   # yields: 100bp/day; FX: 10%/day
        rep.append(screen(nm, s, lim))
    for r in rep:
        print(json.dumps(r))
    # selic unit inference: compare recent level vs known selic target ~15%/yr (2025-26)
    s = load_val(RAW["selic"])
    last = float(s.tail(60).mean())
    print("selic last-60d mean raw value: %.6f" % last)
    for k, unit in ((0.01, "pct/yr"), (1.0, "decimal/yr"), (252.0, "decimal/DAY")):
        print("  if unit=%s -> %.2f%%/yr" % (unit, last * k * 100))
    with open(OUT + "/part1_hygiene.json", "w") as fh:
        json.dump(rep, fh, indent=2, default=str)

def trend_sleeve(tr):
    """FROZEN a6r7 recipe transplant (E1_20yspan/work/e1_idea2_a6r7_brwt_detrunc.py):
    sig = rolling K mean of tr > 0; 42-obs cadence freeze; T+1; cost FULL |dWsig| at
    6.4bp (TRADE_RECORD_STANDARD; a6r7 legacy used 6.0); causal expanding vol overlay
    VT12 CAP5 OUTSIDE the cost (pool convention)."""
    tr = tr.dropna()
    sig = (tr.rolling(K).mean() > 0).astype(float)
    W = sig.iloc[::CAD].reindex(tr.index).ffill().fillna(0.0)
    gross = W.shift(1) * tr
    turn = (W.shift(1) - W.shift(2)).abs().fillna(0.0)
    net = gross - turn * BPS / 1e4
    lev = (VT / np.sqrt(252) / net.expanding(60).std().shift(1)).clip(0, CAP).fillna(0.0)
    out = (net * lev).dropna()
    return out[~out.index.duplicated(keep="last")]

def causality_probe(tr, fracs=(0.25, 0.5, 0.75)):
    """G9: zero raw TR from probe day onward -> position path up to probe-1 unchanged."""
    base = trend_sleeve(tr)
    worst = 0.0
    for f in fracs:
        t = int(len(tr) * f)
        trz = tr.copy()
        trz.iloc[t:] = 0.0
        z = trend_sleeve(trz)
        j = pd.concat([base.rename("b"), z.rename("z")], axis=1, join="inner")
        pre = j[j.index < tr.index[t]]
        if len(pre):
            worst = max(worst, float((pre["b"] - pre["z"]).abs().max()))
    return worst

def stats(r, label):
    r = r.dropna()
    e_full = r[r.index >= START]
    pre = e_full[e_full.index < IS_END]
    post = e_full[e_full.index >= IS_END]
    def sr(x):
        x = x.dropna()
        return float(x.mean() / x.std(ddof=1) * np.sqrt(252)) if len(x) > 20 and x.std(ddof=1) > 1e-12 else 0.0
    nav = (1 + e_full).cumprod()
    yr = e_full.groupby(e_full.index.year).apply(lambda x: (1 + x).prod() - 1)
    return dict(label=label, n=int(len(e_full)), sr=sr(e_full), is_sr=sr(pre), oos_sr=sr(post),
                cagr=float((nav.iloc[-1]) ** (252 / len(e_full)) - 1) * 100,
                arith=float(e_full.mean() * 252) * 100,
                mdd=float((nav / nav.cummax() - 1).min()) * 100,
                worst_yr=float(yr.min()) * 100, neg_years=int((yr < 0).sum()))

INCUMBENT = dict(
    brwt10  = ROOT + "/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv",
    brwt7   = ROOT + "/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv",
    brwt5   = ROOT + "/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv",
    C5ng    = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
    C5ngsum = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
    A5r2    = ROOT + "/campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
    a6r7    = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
    QAxasts = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
    carryv2 = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
    dualmom = ROOT + "/campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
    diescrack = ROOT + "/campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
    CFX4    = ROOT + "/campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
)

def load_ret(path):
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    col = "ret" if "ret" in df.columns else df.columns[0]
    return df[col].astype(float)

def part2():
    print("=== PART 2: CANDIDATE SLEEVES (frozen recipe) + STANDALONE ===")
    y2 = load_val(RAW["bund2y"]) / 100.0
    y10 = load_val(RAW["bund10y"]) / 100.0
    c2 = load_val(RAW["cad2y"]) / 100.0
    c10 = load_val(RAW["cad10y"]) / 100.0
    sl = load_val(RAW["selic"])
    fx = load_val(RAW["usdbrl"])
    trs = dict(
        bund2y  = (-1.9 * y2.diff() + y2 / 252.0),
        bund10y = (-8.5 * y10.diff() + y10 / 252.0),
        cad2y   = (-1.9 * c2.diff() + c2 / 252.0),
        cad10y  = (-8.5 * c10.diff() + c10 / 252.0),
    )
    cands = dict()
    # selic units VERIFIED in part1/eyeball: raw value is a DAILY rate in PERCENT.
    # (1.000522)^252-1 = 14.0%/yr matches the 2025-26 selic target; (1.00154)^252-1 =
    # 47.6%/yr matches post-Real 1995. Simple daily carry = value/100 (a6r7-consistent).
    recent_ann = (1.0 + float(sl.tail(60).mean()) / 100.0) ** 252 - 1
    head_ann = (1.0 + float(sl.head(60).mean()) / 100.0) ** 252 - 1
    if not (0.08 <= recent_ann <= 0.30 and 0.30 <= head_ann <= 0.80):
        raise SystemExit("selic unit check FAILED: recent %.3f head %.3f" % (recent_ann, head_ann))
    y_sl = sl / 100.0   # daily decimal carry
    j = pd.concat([y_sl.rename("y"), fx.rename("fx")], axis=1, join="inner").dropna()
    tr_carry = j["y"] - j["fx"].diff() / j["fx"]
    trs["seliccary"] = tr_carry
    stats_all, probes = dict(), dict()
    for nm in trs:
        s = trend_sleeve(trs[nm])
        cands[nm] = s
        s.to_frame("ret").to_csv(OUT + "/sleeve_" + nm + ".csv")
        stats_all[nm] = stats(s, nm)
        probes[nm] = causality_probe(trs[nm])
    print("causality probes (max pre-probe dev):", json.dumps(probes))
    print(json.dumps(stats_all, indent=2, default=str))
    inc = pd.DataFrame(dict((n, load_ret(p)) for n, p in INCUMBENT.items()))
    print("=== correlations vs incumbent sleeves (common idx >= 2008-03-31) ===")
    for nm, s in cands.items():
        e = s[s.index >= START]
        row = []
        for n2 in inc.columns:
            jj = pd.concat([e.rename("a"), inc[n2].rename("b")], axis=1, join="inner").dropna()
            row.append("%.2f" % jj["a"].corr(jj["b"]) if len(jj) > 100 else "na")
        print(nm.ljust(10), " ".join(("%s=%s" % (n2, v)) for n2, v in zip(inc.columns, row)))
    with open(OUT + "/part2_candidates.json", "w") as fh:
        json.dump(dict(stats=stats_all), fh, indent=2, default=str)




BUILDER_NAMES = ["brwt10", "brwt7", "brwt5", "C5ng", "C5ngsum", "A5r2", "a6r7",
                 "QAxasts", "carryv2", "dualmom", "diescrack", "CFX4"]
SHRINK_D, W_BRWT_CAP, GEAR, RATE = 0.70, 0.30, 1.0, 0.045

def fit_relw_mirror(isr, names):
    """Exact mirror of rawew13v2_build.fit_relw (two-stage cap, 3 SLSQP starts)."""
    have = [n for n in names if isr[n].notna().sum() > 0]
    X = isr[have].dropna()
    mu = (X.mean() * 252).values
    Sig = X.cov().values * 252
    Sig = (1.0 - SHRINK_D) * Sig + SHRINK_D * np.diag(np.diag(Sig))
    k, sd = len(have), np.sqrt(np.diag(Sig))
    def neg_sharpe(w):
        v = float(np.sqrt(w @ Sig @ w))
        return -(float(w @ mu)) / v if v > 1e-14 else 0.0
    cons = [dict(type="eq", fun=lambda w: w.sum() - 1.0)]
    cap = 2.0 / k
    def solve(bounds):
        best = None
        for w0 in (np.full(k, 1.0 / k),
                   np.maximum(mu, 0.0) / max(float(np.maximum(mu, 0.0).sum()), 1e-12),
                   (1.0 / sd) / (1.0 / sd).sum()):
            r = minimize(neg_sharpe, w0, method="SLSQP", bounds=bounds, constraints=cons,
                         options=dict(maxiter=800, ftol=1e-12))
            if r.success and (best is None or r.fun < best.fun):
                best = r
        return best
    best = solve([(0.0, 2.0)] * k)
    if best is not None and float(best.x.max()) > cap + 1e-9:
        best = solve([(0.0, cap)] * k)
    if best is None:
        raise RuntimeError("fit failed")
    relw = pd.Series(0.0, index=names)
    relw[have] = best.x
    return relw

def apply_brwt_cap_mirror(relw):
    share = relw / relw.sum()
    blk = [n for n in ("brwt10", "brwt7", "brwt5") if n in share.index]
    bs = float(share[blk].sum())
    out = share.copy()
    if bs > W_BRWT_CAP:
        excess = bs - W_BRWT_CAP
        out[blk] = out[blk] * (W_BRWT_CAP / bs)
        nonblk = [n for n in out.index if n not in blk]
        nb = float(out[nonblk].sum())
        out[nonblk] = out[nonblk] + excess * out[nonblk] / nb
    if "CFX4" in out.index:
        out["CFX4"] = 0.0
    return out

def build_from_frame(df, gear=GEAR):
    """Mirror of rawew13v2_build.build mechanics on a given frame (fit inside)."""
    names = list(df.columns)
    isr = df[df.index < IS_END]
    relw = apply_brwt_cap_mirror(fit_relw_mirror(isr, names))
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(names)
    Wg = d2 * (gear / len(names))
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    net = (pd.Series(port, index=df.index) - to * 6.4 / 1e4
           - np.maximum(gear - 1, 0) * RATE / 252)
    gross = Wg.abs().sum(axis=1)
    return net, relw, gross, to


def book_stats(r):
    return stats(r, "book")

def oos_bins(a, b):
    edges = ["2017-01-01", "2019-01-01", "2021-01-01", "2023-01-01", "2025-01-01", "2099-01-01"]
    out = []
    for i in range(5):
        wa = a[(a.index >= pd.Timestamp(edges[i])) & (a.index < pd.Timestamp(edges[i + 1]))]
        wb = b[(b.index >= pd.Timestamp(edges[i])) & (b.index < pd.Timestamp(edges[i + 1]))]
        j = pd.concat([wa.rename("a"), wb.rename("b")], axis=1, join="inner").dropna()
        if len(j) < 60 or j["a"].std(ddof=1) <= 1e-12 or j["b"].std(ddof=1) <= 1e-12:
            out.append(float("nan"))
            continue
        sa = j["a"].mean() / j["a"].std(ddof=1) * np.sqrt(252)
        sb = j["b"].mean() / j["b"].std(ddof=1) * np.sqrt(252)
        out.append(float(sa - sb))
    return out

def part3():
    print("=== PART 3: GREEDY POOL REFIT + GATES ===")
    frames = dict((n, load_ret(p2).dropna()) for n, p2 in INCUMBENT.items())
    cand_order = ["bund2y", "bund10y", "cad2y", "cad10y", "seliccary"]
    for nm in cand_order:
        frames[nm] = pd.read_csv(OUT + "/sleeve_" + nm + ".csv", index_col=0,
                                 parse_dates=True).iloc[:, 0]
    all_names = BUILDER_NAMES + cand_order
    df13 = pd.DataFrame(frames)[all_names]
    df13 = df13[df13.index >= START]
    results = dict()
    # B0 = the 12 committed slots on the TRUE 12-sleeve union (exactly the builder's frame)
    idx12 = sorted(set().union(*[set(frames[n].index) for n in BUILDER_NAMES]))
    idx12 = [d for d in idx12 if d >= START]
    df12 = df13[BUILDER_NAMES].reindex(idx12)
    isr12 = df12[df12.index < IS_END]
    have12 = [n for n in BUILDER_NAMES if isr12[n].notna().sum() > 0]
    isr12_rows = int(isr12[have12].dropna().shape[0])
    net12, relw12, gross12, to12 = build_from_frame(df12)
    champ = load_ret(ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")
    wcmt = load_ret(ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv")
    if len(net12) != len(champ):
        raise SystemExit("B0 length %d != champion %d - union mismatch" % (len(net12), len(champ)))
    j = pd.concat([champ.rename("old"), net12.rename("new")], axis=1, join="inner").dropna()
    byte_dev = float((j.old - j.new).abs().max())
    w_aligned = float((wcmt.reindex(relw12.index) - relw12).abs().max())
    print("ANCHOR 12-pool: byte dev %.3e  weights dev %.3e" % (byte_dev, w_aligned))
    results["anchor_byte_dev"] = byte_dev
    if byte_dev >= 1e-12 or w_aligned >= 1e-9:
        raise SystemExit("ANCHOR FAILED - mirror not byte-identical; STOP")
    b0 = book_stats(net12)
    results["B0"] = b0
    print("B0:", json.dumps(b0, default=str))
    kept, log = [], []
    for nm in cand_order:
        trial_names = BUILDER_NAMES + kept + [nm]
        dft = df13[trial_names]
        net_t, relw_t, gross_t, to_t = build_from_frame(dft)
        isr_t = dft[dft.index < IS_END]
        have_t = [n for n in trial_names if isr_t[n].notna().sum() > 0]
        isr_joint = int(isr_t[have_t].dropna().shape[0])
        win_shrink = (isr12_rows - isr_joint) / isr12_rows
        dfb = df13[BUILDER_NAMES].reindex(dft.index)
        net_b, relw_b, gross_b, to_b = build_from_frame(dfb)
        bwm = book_stats(net_b)
        st = book_stats(net_t)
        bar_sr = max(b0["sr"], bwm["sr"])
        bins_b0 = oos_bins(net_t, net12)
        bins_bwm = oos_bins(net_t, net_b)
        pre = lambda x: x[x.index >= IS_END]
        ao, bo, wo = pre(net_t), pre(net12), pre(net_b)
        dsr_b0 = float(ao.mean() / ao.std(ddof=1) - bo.mean() / bo.std(ddof=1))
        dsr_bwm = float(ao.mean() / ao.std(ddof=1) - wo.mean() / wo.std(ddof=1))
        npos = sum(1 for v in bins_bwm if v > 0)
        wmax_ratio = float((relw_t / (1.0 / len(relw_t))).max())
        g = dict(
            G1=bool(st["sr"] > bar_sr),
            G2=bool(st["arith"] >= 20.0 and st["cagr"] >= 20.0),
            G3=bool(float(gross_t.max()) <= 1.6 + 1e-9),
            G4=bool(st["neg_years"] == 0 and st["worst_yr"] > -5.0 and st["mdd"] >= -7.0),
            G5=bool(dsr_b0 > 0 and dsr_bwm > 0 and npos >= 4),
            G7=bool(wmax_ratio <= 2.0 + 1e-9),
            G8=bool(win_shrink < 0.02),
        )
        adopted = all(g.values())
        rec = dict(slot=nm, kept_pool=list(kept), stats=st, bwm=bwm, bar_sr=bar_sr,
                   is_rows_trial=isr_joint, is_rows_incumbent=isr12_rows,
                   window_shrink_pct=win_shrink * 100,
                   d_cagr_vs_B0=st["cagr"] - b0["cagr"],
                   d_arith_vs_B0=st["arith"] - b0["arith"],
                   d_cagr_vs_Bwm=st["cagr"] - bwm["cagr"],
                   dsr_oos_vs_B0_per_day=dsr_b0, dsr_oos_vs_Bwm_per_day=dsr_bwm,
                   bins_vs_B0=bins_b0, bins_vs_Bwm=bins_bwm, n_pos_bins_vs_Bwm=npos,
                   relw=dict(relw_t), gross_max=float(gross_t.max()),
                   wmax_ratio=wmax_ratio, to_bp_yr=float(to_t.mean() * 252 * 6.4),
                   gates=g, adopted=adopted)
        log.append(rec)
        if adopted:
            kept.append(nm)
        print(json.dumps(dict(slot=nm, SR=round(st["sr"], 4), bar=round(bar_sr, 4),
                              BwmSR=round(bwm["sr"], 4), cagr=round(st["cagr"], 4),
                              arith=round(st["arith"], 4), mdd=round(st["mdd"], 4),
                              worst=round(st["worst_yr"], 4), neg=st["neg_years"],
                              dCAGR_B0=round(rec["d_cagr_vs_B0"], 4),
                              dsrOOS_B0=round(dsr_b0, 5), dsrOOS_Bwm=round(dsr_bwm, 5),
                              pos_bins=npos, winshrink_pct=round(win_shrink * 100, 3),
                              wmax=round(wmax_ratio, 4), gates=g, adopted=adopted),
                         default=str))
    results["trials"] = log
    results["kept"] = kept
    with open(OUT + "/part3_trials.json", "w") as fh:
        json.dump(results, fh, indent=2, default=str)
    print("KEPT:", kept)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int, required=True)
    a = ap.parse_args()
    if a.part == 1:
        part1()
    elif a.part == 2:
        part2()
    elif a.part == 3:
        part3()
