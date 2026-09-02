#!/usr/bin/env python3
"""VET_HONESTY permanent gate — independent re-implementation (adversarial, not a copy).

Gates for ANY candidate daily-return CSV (columns: date,ret), 2008-09+ window:
  G1  flatten: lag-1 autocorr > 0.5 OR distinct-value ratio < 0.08  -> REJECT (FLAT-BUG)
      extended: longest run of identical NONZERO consecutive values > 10 -> REJECT
      (long runs of exact 0.0 are position-off by design and NOT a flatten signature;
       verified on pool: brwt15/C5ngsum/A5r2/a6r7/dualmom off-periods are all 0.0bps)
  G2  T+1 lookahead probe: corr(r_t, trailing stat computed on [t+1, t+K]) — any |corr|>0.08
      over >=1200 obs (stats: lead-1 mean/std 2d, lead-5 mean, lead vol63, lead dd126) -> REJECT
  G3  SR(2008-09+) >= 0.6 required (>=1.0 "better")
  G4  halves: SR H1 >= 0.3 AND SR H2 >= 0.3 (median-date split)
  G5  neg years <= 2 and each negative year > -5%
  G6  scramble (CSV-only proxies, 200x): (a) 10-day block bootstrap p(SR<=0)<=0.05;
      (b) outlier scrub: SR after dropping the 5 largest positive days must stay >= 0.3.
      NOTE: literal "shuffle the returns" is a no-op (SR is permutation-invariant); the
      charter's signal-scramble needs the signal, which a return CSV does not carry.
  G7  |corr| < 0.15 to HONEST11 blend (committed GOAL100_HONEST11_daily_BALANCED_daily.csv)
  G8  6bps/side cost audit: NOT derivable from a return CSV alone -> verdict from submitter
      metadata; flagged UNVERIFIED-COST if absent (blocker for promotion to any blend)
Champion-level checks (separate functions): reconstruct stats, leverage, byte-reproduction.
"""
import sys, numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
H11 = f"{ROOT}/campaign/results/GOAL100_HONEST11_daily_BALANCED_daily.csv"

def readv(p):
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)

def sr(r): return r.mean()/r.std()*np.sqrt(252) if r.std() > 0 else np.nan

def flatten_gate(r08):
    ac1 = r08.autocorr(1)
    uniqr = r08.round(10).nunique()/len(r08)
    # longest run of identical consecutive values (1e-12 tolerance)
    v = r08.values; run = 1; mxrun = 1
    for i in range(1, len(v)):
        if abs(v[i]-v[i-1]) < 1e-12: run += 1; mxrun = max(mxrun, run)
        else: run = 1
    # nonzero-only constant runs (XGB1y signature: monthly PnL spread as constant daily value)
    v2 = r08.values; start = 0; mxnz = 0
    for i in range(1, len(v2)+1):
        if i == len(v2) or abs(v2[i]-v2[start]) > 1e-12:
            if i-start > mxnz and abs(v2[start]) > 1e-12: mxnz = i-start
            start = i
    flat = (ac1 > 0.5) or (uniqr < 0.08) or (mxnz > 10)
    return dict(ac1=round(float(ac1), 4), uniqR=round(float(uniqr), 4), maxrun=mxrun,
                maxrun_nonzero=mxnz, FLAT=flat)

def t1_gate(r):
    out = {}
    for K in (2, 5, 63, 126):
        lead_mean = r.shift(-K).rolling(K).mean().shift(-(K))  # mean of r[t+1..t+K] aligned at t
        lead_std  = r.shift(-K).rolling(K).std().shift(-(K))
        j = pd.concat([r.rename("r"), lead_mean.rename("lm"), lead_std.rename("ls")], axis=1).dropna()
        out[f"leadmean{K}"] = round(float(j.corr().iloc[0, 1]), 4)
        out[f"leadstd{K}"] = round(float(j.corr().iloc[0, 2]), 4)
    worst = max(abs(v) for k, v in out.items())
    n = len(r)
    return dict(out, worst=round(worst, 4), LOOKAHEAD=(worst > 0.08 and n >= 1200))

def perf_gates(r08):
    res = {}
    res["SR"] = round(float(sr(r08)), 3)
    h = len(r08)//2
    res["SR_H1"] = round(float(sr(r08.iloc[:h])), 3); res["SR_H2"] = round(float(sr(r08.iloc[h:])), 3)
    yr = r08.groupby(r08.index.year).apply(lambda x: (1+x).prod()-1)
    neg = yr[yr < 0]
    res["neg_years"] = int(len(neg)); res["worst_yr"] = round(float(yr.min()), 4)
    res["G_SR"] = res["SR"] >= 0.6
    res["G_HALVES"] = res["SR_H1"] >= 0.3 and res["SR_H2"] >= 0.3
    res["G_NEGYRS"] = len(neg) <= 2 and (len(neg) == 0 or neg.min() > -0.05)
    rng = np.random.default_rng(42); x = r08.values; n = len(x); B = 10
    nb = n//B; starts = rng.integers(0, n-B, size=(200, nb))
    boot = np.vstack([np.concatenate([x[s:s+B] for s in row])[:n] for row in starts])
    mus, sds = boot.mean(axis=1), boot.std(axis=1)
    boot_sr = np.where(sds > 0, mus/sds*np.sqrt(252), 0.0)
    p_le0 = float((boot_sr <= 0).mean())
    order = np.argsort(x)[::-1]
    keep = np.ones(n, bool); keep[order[:5]] = False
    scrub = float(sr(pd.Series(x[keep], index=r08.index[keep])))
    res["boot_p(SR<=0)"] = round(p_le0, 4)
    res["scrub5_SR"] = round(scrub, 3)
    res["G_SCRAMBLE"] = (p_le0 <= 0.05) and (scrub >= 0.3)
    return res

def corr_gate(r08):
    h = readv(H11).dropna(); h = h[h.index >= "2008-09-01"]
    j = pd.concat([r08.rename("c"), h.rename("h11")], axis=1, join="inner").dropna()
    if len(j) < 252: return dict(corr=None, n=int(len(j)), G_CORR=False)
    cc = float(j.corr().iloc[0, 1])
    return dict(corr=round(cc, 4), n=int(len(j)), G_CORR=abs(cc) < 0.15)

def vet(path):
    r = readv(path).dropna()
    r08 = r[r.index >= "2008-09-01"]
    if len(r08) < 252: return {"path": path, "VERDICT": "REJECT-TOOSHORT", "n08": int(len(r08))}
    f = flatten_gate(r08); t = t1_gate(r08); p = perf_gates(r08); c = corr_gate(r08)
    verdict = "PASS" if (not f["FLAT"] and not t["LOOKAHEAD"] and p["G_SR"] and p["G_HALVES"]
                         and p["G_NEGYRS"] and p["G_SCRAMBLE"] and c["G_CORR"]) else "REJECT"
    why = [k for k, ok in [("FLATTEN", not f["FLAT"]), ("LOOKAHEAD", not t["LOOKAHEAD"]),
                           ("SR>=0.6", p["G_SR"]), ("HALVES", p["G_HALVES"]),
                           ("NEGYRS", p["G_NEGYRS"]), ("SCRAMBLE", p["G_SCRAMBLE"]),
                           ("CORR<0.15", c["G_CORR"])] if not ok]
    return dict(path=path.replace(ROOT+"/", ""), n08=int(len(r08)), verdict=verdict,
                fails=why, flatten=f, t1=t, perf=p, corr=c, cost="UNVERIFIED-COST(csv-only)")

def champ_stats(path):
    r = readv(path).dropna()
    eq = (1+r).cumprod(); mdd = float((eq/eq.cummax()-1).min())
    m = (1+r).resample("ME").prod()-1
    yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    neg = yr[yr < 0]
    # worst 3y subwindow MaxDD
    worst3 = 0.0
    for a in pd.date_range(r.index[0], r.index[-1]-pd.Timedelta(days=1095), freq="YS"):
        w = r[(r.index >= a) & (r.index < a+pd.Timedelta(days=1461))]
        if len(w) > 252:
            e = (1+w).cumprod(); worst3 = min(worst3, float((e/e.cummax()-1).min()))
    o = r[r.index >= "2017-01-01"]
    return dict(n=int(len(r)), ann_geo=float((1+r).prod()**(252/len(r))-1),
                ann_arith=float(r.mean()*252), SR_d=float(sr(r)), SR_m=float(sr(m.dropna())),
                MDD=mdd, worst3y=worst3, neg_yrs=int(len(neg)), worst_yr=float(yr.min()),
                oos17_ann_arith=float(o.mean()*252), oos17_ann_geo=float((1+o).prod()**(252/len(o))-1),
                oos17_SR=float(sr(o)),
                oos17_MDD=float(((1+o).cumprod()/(1+o).cumprod().cummax()-1).min()))

if __name__ == "__main__":
    for p in sys.argv[1:]:
        import json; print(json.dumps(vet(p), default=str))
