#!/usr/bin/env python3
"""STATS_REVIEW independent stats on GOAL100_HONEST11FIX (committed CSVs, own code)."""
import numpy as np, pandas as pd
from scipy import stats as st
rng = np.random.default_rng(20260902)
ROOT = "/Users/daxu/software/world-trader"
FILES = {"BAL": "GOAL100_HONEST11FIX_BALANCED_daily.csv",
         "SAFE": "GOAL100_HONEST11FIX_SAFE_daily.csv",
         "AGGR": "GOAL100_HONEST11FIX_AGGRESSIVE_daily.csv"}

def load(fn):
    df = pd.read_csv(f"{ROOT}/campaign/results/{fn}", index_col=0, parse_dates=True)
    return df.iloc[:, 0].astype(float)

def mdd(r):
    eq = (1+r).cumprod(); return float((eq/eq.cummax()-1).min())

def worst_window_mdd(r, w=1260):
    v = r.values; n = len(v); best = 0.0; arg = None
    for i in range(0, n-w):
        x = v[i:i+w+1]; eq = np.cumprod(1+x); d = (eq/np.maximum.accumulate(eq)-1).min()
        if d < best: best = d; arg = (r.index[i].date(), r.index[i+w].date())
    return best, arg

def worst_window_ret(r, w=252):
    v = r.values; n = len(v); best = 0.0; arg = None
    for i in range(0, n-w):
        x = v[i:i+w]; ret = np.prod(1+x)-1
        if ret < best: best = ret; arg = (r.index[i].date(), r.index[i+w-1].date())
    return best, arg

def sr_d(r): return float(r.mean()/r.std(ddof=1)*np.sqrt(252))
def sr_m(r):
    m = (1+r).resample('ME').prod()-1
    return float(m.mean()/m.std(ddof=1)*np.sqrt(12)), m

def block_boot_sr_ci(r, nboot=2000, blk=10):
    v = r.values; n = len(v); nb = int(np.ceil(n/blk)); out = np.empty(nboot)
    for b in range(nboot):
        starts = rng.integers(0, n, nb); idx = ((starts[:,None] + np.arange(blk)[None,:]) % n).ravel()[:n]
        x = v[idx]; out[b] = x.mean()/x.std(ddof=1)*np.sqrt(252)
    return np.percentile(out, [2.5, 97.5]), out

def iid_boot_sr_m_ci(m, nboot=2000):
    v = m.values; n = len(v); out = np.empty(nboot)
    for b in range(nboot):
        x = v[rng.integers(0, n, n)]
        out[b] = x.mean()/x.std(ddof=1)*np.sqrt(12)
    return np.percentile(out, [2.5, 97.5]), out

def ann_geo(r): return float((1+r).prod()**(252/len(r))-1)

res = {}
for tag, fn in FILES.items():
    r_full = load(fn)
    r = r_full[r_full.index >= "2008-03-31"]
    d = {}
    d["n_full"] = len(r_full); d["n"] = len(r)
    d["start_full"] = str(r_full.index[0].date()); d["end"] = str(r_full.index[-1].date())
    d["start"] = str(r.index[0].date())
    d["ann"] = ann_geo(r); d["sr_d"] = sr_d(r)
    d["sr_m"], m = sr_m(r); d["m_ret"] = m
    (d["sr_d_lo"], d["sr_d_hi"]), _ = block_boot_sr_ci(r)
    (d["sr_m_lo"], d["sr_m_hi"]), _ = iid_boot_sr_m_ci(m)
    d["mdd"] = mdd(r)
    d["mdd3y"], d["mdd3y_arg"] = worst_window_mdd(r, 1260)
    d["ret1y"], d["ret1y_arg"] = worst_window_ret(r, 252)
    yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    d["yrs"] = yr; d["neg"] = int((yr < 0).sum()); d["nyr"] = int(yr.size)
    d["worst_yr"] = float(yr.min()); d["worst_yr_name"] = yr.idxmin(); d["best_yr"] = float(yr.max())
    for lab, start in [("oos17","2017-01-01"), ("oos20","2020-01-01"), ("oos23","2023-01-01")]:
        o = r[r.index >= start]
        d[lab+"_ann"] = ann_geo(o); d[lab+"_sr"] = sr_d(o); d[lab+"_mdd"] = mdd(o); d[lab+"_n"] = len(o)
    # tail stats
    d["skew"] = float(st.skew(r.values)); d["xkurt"] = float(st.kurtosis(r.values, fisher=True))
    d["kurt_raw"] = float(st.kurtosis(r.values, fisher=False))
    worst5 = r.nsmallest(5); best1 = r.max()
    d["worst5"] = [(str(k.date()), float(v)) for k, v in worst5.items()]
    d["best_day"] = (str(r.idxmax().date()), float(best1))
    var5 = float(np.percentile(r.values, 5)); d["var5"] = var5
    d["cvar5"] = float(r.values[r.values <= var5].mean())
    d["sigma"] = float(r.std(ddof=1)); d["mu"] = float(r.mean())
    # the 14.40% day
    zday = abs(best1)/d["sigma"]; d["z_best"] = float(zday)
    # fitted Student-t df (MLE on standardized returns)
    x = (r.values - r.mean())/r.std(ddof=1)
    df_hat, loc, scale = st.t.fit(x)
    d["t_df"] = float(df_hat)
    d["p_t"] = float(st.t.cdf(-zday, df_hat, loc=0, scale=1))  # approx: t on standardized scale
    d["p_norm"] = float(st.norm.cdf(-zday))
    # empirical Hill tail index (top 1% absolute)
    ax = np.sort(np.abs(x))[::-1]; k = max(10, int(0.01*len(ax)))
    d["hill"] = float(np.mean(np.log(ax[:k]/ax[k])))
    d["n_gt_half"] = int((np.abs(x) > zday/2).sum())
    res[tag] = d

# print BAL in full detail
d = res["BAL"]
print(f"=== BALANCED (comparable span {d['start']}..{d['end']}, n={d['n']}; full span {d['start_full']}, n_full={d['n_full']}) ===")
print(f"ann(geo) {d['ann']*100:.2f}%  | SR_d {d['sr_d']:.3f} CI95[{d['sr_d_lo']:.3f},{d['sr_d_hi']:.3f}] (block10 2000x)")
print(f"SR_m {d['sr_m']:.3f} CI95[{d['sr_m_lo']:.3f},{d['sr_m_hi']:.3f}] (iid 2000x, nm={len(d['m_ret'])})")
print(f"MaxDD {d['mdd']*100:.2f}% | worst 3y(1260d) subwindow MDD {d['mdd3y']*100:.2f}% in {d['mdd3y_arg']}")
print(f"worst 1y(252d) subwindow return {d['ret1y']*100:.2f}% in {d['ret1y_arg']}")
print(f"neg years {d['neg']}/{d['nyr']} worst {d['worst_yr_name']} {d['worst_yr']*100:.2f}% best {d['best_yr']*100:.2f}%")
for lab in ["oos17","oos20","oos23"]:
    print(f"{lab}: ann {d[lab+'_ann']*100:.2f}% SR_d {d[lab+'_sr']:.3f} MDD {d[lab+'_mdd']*100:.2f}% (n={d[lab+'_n']})")
print(f"full-span(2006-10+) ann {ann_geo(load(FILES['BAL']))*100:.2f}%")
print(f"skew {d['skew']:.3f} excess kurt {d['xkurt']:.2f} raw kurt {d['kurt_raw']:.2f}")
print("worst5 days:", [(a, round(b*100,2)) for a,b in d["worst5"]])
print(f"best day {d['best_day'][0]} {d['best_day'][1]*100:.3f}% = {d['z_best']:.1f} sigma (sigma_d={d['sigma']*1e4:.1f}bp, mu={d['mu']*1e4:.2f}bp)")
print(f"VaR5% {d['var5']*100:.3f}%  CVaR5% {d['cvar5']*100:.3f}%")
print(f"t-fit df {d['t_df']:.2f}; P(day<=-{d['z_best']:.1f}sig): t {d['p_t']:.3e}, normal {d['p_norm']:.3e}; Hill tail alpha {d['hill']:.3f}")
print(f"days with |z|>z_best/2: {d['n_gt_half']} of {d['n']}")
print()
for tag in ["SAFE","AGGR"]:
    d = res[tag]
    print(f"=== {tag}: n={d['n']} ann {d['ann']*100:.2f}% SR_d {d['sr_d']:.3f} CI[{d['sr_d_lo']:.3f},{d['sr_d_hi']:.3f}] SR_m {d['sr_m']:.3f} CI[{d['sr_m_lo']:.3f},{d['sr_m_hi']:.3f}] MDD {d['mdd']*100:.2f}% 3yMDD {d['mdd3y']*100:.2f}% 1y {d['ret1y']*100:.2f}% neg {d['neg']}/{d['nyr']} worst {d['worst_yr']*100:.2f}%({d['worst_yr_name']}) OOS17 {d['oos17_ann']*100:.1f}%/{d['oos17_sr']:.2f} OOS20 {d['oos20_ann']*100:.1f}%/{d['oos20_sr']:.2f} OOS23 {d['oos23_ann']*100:.1f}%/{d['oos23_sr']:.2f} skew {d['skew']:.2f} xkurt {d['xkurt']:.1f} VaR5 {d['var5']*100:.2f}% CVaR5 {d['cvar5']*100:.2f}% maxday {d['best_day'][1]*100:.2f}%({d['z_best']:.1f}sig) t_df {d['t_df']:.1f}")

# yearly table BAL
print("\nBAL yearly:"); print({int(k): round(v*100,2) for k,v in res["BAL"]["yrs"].items()})

# Ljung-Box
from statsmodels.stats.diagnostic import acorr_ljungbox
rb = load(FILES["BAL"]); rb = rb[rb.index >= "2008-03-31"]
lb = acorr_ljungbox(rb.values, lags=[10], return_df=True)
print("\nLjung-Box(10) BAL 2008+: stat", float(lb['lb_stat'].iloc[0]), "p", float(lb['lb_pvalue'].iloc[0]))
ac = rb.autocorr(lag=1)
print("ac1", float(ac))
sq = (rb.values - rb.mean())**2
from statsmodels.stats.diagnostic import acorr_ljungbox as alb
lbsq = alb(sq, lags=[10], return_df=True)
print("Ljung-Box(10) on sq returns: stat", float(lbsq['lb_stat'].iloc[0]), "p", float(lbsq['lb_pvalue'].iloc[0]))

# distinct values / flatten gate on FIX
print("distinct returns:", rb.nunique(), "of", len(rb), "uniqR", rb.nunique()/len(rb))

# DSR (Bailey/Lopez de Prado), N=500 effective trials
def dsr(sr_hat_ann, T, skew_, kurt_raw, var_sr_trials, N=500):
    g = 0.5772156649015329
    z1 = st.norm.ppf(1 - 1.0/N); z2 = st.norm.ppf(1 - 1.0/(N*np.e))
    sr_star = np.sqrt(var_sr_trials) * ((1-g)*z1 + g*z2)   # expected max SR under H0, annualized-daily units
    denom = np.sqrt(1 - skew_*sr_hat_ann + (kurt_raw-1)/4.0*sr_hat_ann**2)
    stat = (sr_hat_ann - sr_star) * np.sqrt(T-1) / denom
    return sr_star, float(st.norm.cdf(stat)), float(stat)
# empirical cross-trial variance anchor: daily SRs of the 11 sleeves + blend variants
import sys; sys.path.insert(0,'scripts'); sys.path.insert(0, ROOT)
import honest11_build as hb
srlist = []
for n, p in hb.POOL.items():
    rr = hb.sn(p); rr = rr[rr.index >= '2008-03-31']
    rr = rr[rr != 0.0]  # active days only? no - keep all
    srlist.append(sr_d(rr))
sleeve_sr = np.array(srlist)
print("\nsleeve daily SRs (2008+, all days):", np.round(sleeve_sr,2), "sd", round(float(sleeve_sr.std(ddof=1)),3))
for sd in [0.25, 0.5, 1.0, float(sleeve_sr.std(ddof=1))]:
    var_sr = sd**2
    sstar, p, stat = dsr(d["sr_d"], d["n"], d["skew"], d["kurt_raw"], var_sr)
    print(f"DSR N=500, sd(SR trials)={sd:.3f}: SR* (expected max under H0) {sstar:.3f}, haircut {sstar:.3f}, DSR={p:.6f} (z={stat:.2f})")
# PSR(0) too
_, p_psr, z_psr = dsr(d['sr_d'], d['n'], d['skew'], d['kurt_raw'], 0.0)
print(f"PSR(benchmark SR*=0): {p_psr:.6f} (z={z_psr:.2f})")

# breach math for -14.4% day
zday = d['z_best']; day = d['best_day'][1]
breach_gain = 0.93/(1-abs(day)) - 1
print(f"\na -{abs(day)*100:.2f}% day: breaches DD<=7% unless prior equity > running peak by more than +{breach_gain*100:.2f}%")
# from current-level scenarios
for x0 in [0.0, -0.0485, -0.0673]:
    print(f"  from DD {x0*100:.2f}% -> new DD {((1+x0)*(1-abs(day))-1)*100:.2f}%")
