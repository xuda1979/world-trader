#!/usr/bin/env python3
"""AUDIT_CHAMP2 ROUND 2 — fresh independent audit of the RE-EMITTED causal champion.

Everything recomputed from the 13 RAW sleeve files, not from the builder module (no import
of rawew13v2_build). Construction re-implemented from the builder DOCSTRING spec:
  relw_i = max(IS_SR_i,0)^0.55 on IS window (< 2017-01-01), row-normalized NAV-drift
  (CAUSAL: nav.shift(1)), gross exactly 1.6, cost FULL |dW| x 6.4bps one-side,
  margin (1.6-1)*4.5%/252 daily.

Gates C1..C7 + metrics + the R2(d) new-vs-archive mechanism pin.
"""
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
POOL = {
 "brwt15": "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 "brwt10": "campaign/agents/COORD/sleeves/brwt10_2000.csv",
 "brwt7":  "campaign/agents/COORD/sleeves/brwt7.csv",
 "brwt5":  "campaign/agents/COORD/sleeves/brwt5.csv",
 "C5ng":   "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsum":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 "A5r2":   "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 "a6r7":   "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "QAxasts":"campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 "carryv2":"campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
}
NEW = {
 "diescrack":"campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
 "CFX4":     "campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
}
NAMES = list(POOL) + list(NEW)
PATHS = {**POOL, **NEW}
GEAR, RATE, BPS, P = 1.6, 0.045, 6.4, 0.55
IS_END = pd.Timestamp('2017-01-01')
CHAMP  = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
WGT    = f"{ROOT}/campaign/results/RAWEW13v2_IS_SR_weights.csv"
ARCH   = f"{ROOT}/campaign/results/archive_GOAL100_RAWEW13v2_WEIGHTED_GEAR16_SAMEDAYLEAK_ann40.84.csv"

def load(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)

def wg_causal(df, relw, lag=1):
    k = len(NAMES)
    nav = (1 + df.fillna(0)).cumprod()
    if lag:
        nav = nav.shift(lag).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * k
    return d2 * (GEAR / k)

def is_sr(r):
    r = r.dropna()
    if len(r) < 200 or r.std(ddof=1) <= 1e-12:
        return 0.0
    return float(r.mean() / r.std(ddof=1) * np.sqrt(252))

# ---------------- independent rebuild ----------------
df = pd.DataFrame({n: load(PATHS[n]).dropna() for n in NAMES})
df = df[df.index >= '2008-03-31']
isr = df[df.index < IS_END]
SR = pd.Series({n: is_sr(isr[n]) for n in NAMES})
relw = np.maximum(SR, 0.0) ** P

Wg = wg_causal(df, relw, 1)
port = pd.Series((df.fillna(0).values * Wg.values).sum(axis=1), index=df.index)
to = Wg.diff().abs().sum(axis=1).fillna(0.0)
net = port - to * BPS / 1e4 - np.maximum(GEAR - 1, 0) * RATE / 252
gross = Wg.abs().sum(axis=1)

# committed files
com = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
comw = pd.read_csv(WGT, index_col=0).iloc[:, 0]
arc = pd.read_csv(ARCH, index_col=0, parse_dates=True).iloc[:, 0]

print("=== R2 INDEPENDENT REBUILD (no builder import) ===")
print(f"panel: {df.shape[0]} days x {df.shape[1]} sleeves, {df.index[0].date()}..{df.index[-1].date()}, "
      f"NaN cells={int(df.isna().sum().sum())}")

# --- C7 byte repro vs committed ---
j = pd.concat([com.rename('c'), net.rename('n')], axis=1, join='inner').dropna()
md7 = float((j.c - j.n).abs().max())
rows_ok = len(j) == len(com) == len(net)
print(f"\n[C7] byte-repro: rows committed={len(com)} built={len(net)} inner={len(j)} equal={rows_ok} "
      f"maxdev={md7:.3e} -> {'PASS' if rows_ok and md7 < 1e-12 else 'FAIL'}")
mdw = float((comw.reindex(NAMES) - relw).abs().max())
print(f"[C7] weights: max|committed-built|={mdw:.3e} -> {'PASS' if mdw < 1e-12 else 'FAIL'}")

# --- metrics ---
def metrics(r, label):
    r = r.dropna()
    ann = (1 + r).prod() ** (252 / len(r)) - 1
    srd = r.mean() / r.std(ddof=1) * np.sqrt(252)
    cum = (1 + r).cumprod()
    mdd = float((cum / cum.cummax() - 1).min())
    yrs = (1 + r).resample('YE').prod() - 1
    neg = int((yrs < 0).sum())
    print(f"  {label}: n={len(r)} ann_geo={ann:.4%} SR_d={srd:.4f} MaxDD={mdd:.2%} "
          f"neg_years={neg}/{len(yrs)} worst_year={yrs.min():.2%} vol={r.std(ddof=1)*np.sqrt(252):.2%}")
    return ann, srd, mdd, neg

print("\n[METRICS]")
m_b = metrics(net, "rebuild")
m_c = metrics(com, "committed")
m_a = metrics(arc, "archive(leak)")

# --- C1 cost decomposition ---
print("\n[C1] cost decomposition:")
cum_cost = float((to * BPS / 1e4).sum())
print(f"  cum cost = {cum_cost*1e4:.2f}bp over {len(to)} days = {cum_cost*1e4/(len(to)/252):.3f}bp/yr")
resid = float((net - (port - to * BPS / 1e4 - (GEAR - 1) * RATE / 252)).abs().max())
print(f"  net == port - |dW|*6.4bp - (1.6-1)*4.5%/252 residual = {resid:.2e}")
half = float(((to / 2 * BPS / 1e4).sum() - cum_cost) * 1e4 / (len(to) / 252))
print(f"  half-turn variant would differ by {half:.3f}bp/yr (absent => FULL |dW| confirmed)")
print(f"  first-row entry turnover charged = {to.iloc[0]*1e4:.2f}bp "
      f"(Wg.diff() row0 NaN->0, disclosed R1)")
gross_ = Wg.abs().sum(axis=1)
print(f"\n[C3] gross mean={gross_.mean():.12f} min={gross_.min():.12f} "
      f"max={gross_.max():.12f} days>1.6+1e-9 = {int((gross_ > 1.6 + 1e-9).sum())}")
print(f"[C3] min slot weight = {Wg.min().min():.6f} (>=0 required)")

# --- C4 ---
yrs = (1 + net.dropna()).resample('YE').prod() - 1
print(f"[C4] neg calendar years = {int((yrs < 0).sum())}/{len(yrs)}; "
      f"min {yrs.min():.2%}; max {yrs.max():.2%}")

# --- C6 real T+1 perturbation, 5 probes ---
print("\n[C6] T+1 same-day perturbation (own implementation, 5 probes):")
worst = 0.0
k = len(NAMES)
ti_list = [len(df) // 4, len(df) // 2, 3 * len(df) // 4]
for si, delta in [(0, 0.010), (k - 1, -0.020), (k // 2, 0.050), (1, -0.015), (k - 2, 0.030)]:
    for ti in ti_list:
        df2 = df.copy(); df2.iat[ti, si] += delta
        Wg2 = wg_causal(df2, relw, 1)
        p1 = pd.Series((df2.fillna(0).values * Wg2.values).sum(axis=1), index=df2.index)
        t = df.index[ti]
        obs = float(p1.loc[t] - port.loc[t])
        exp = float(Wg.iloc[ti, si] * delta)
        ex = abs(obs - exp) / (abs(delta) * GEAR / k)
        worst = max(worst, ex)
print(f"  max excess response = {worst:.3e} weight-units (T+1 requires <1e-6) "
      f"-> {'PASS' if worst < 1e-6 else 'FAIL'}")
dW = Wg.diff()
cors = [np.corrcoef(dW.iloc[i].values, df.fillna(0).iloc[i].values)[0, 1] for i in range(1, len(df))]
mc = float(np.nanmean(cors))
print(f"  corr(dW_t, r_t) = {mc:+.4f} (0 under T+1)")

# --- R2(d) causal-vs-leak mechanism ---
print("\n[R2d] new champion vs archived SAME-DAY-LEAK champion:")
jj = pd.concat([arc.rename('a'), com.rename('c')], axis=1, join='inner').dropna()
dev = (jj.a - jj.c)
print(f"  rows both={len(jj)}  max|leak-causal|={dev.abs().max():.3e}  "
      f"mean dev={dev.mean():+.3e}  corr={jj.a.corr(jj.c):.5f}")
# mechanism: rebuild the LEAKED variant with same weights, lag=0
Wg_leak = wg_causal(df, relw, 0)
port_l = pd.Series((df.fillna(0).values * Wg_leak.values).sum(axis=1), index=df.index)
to_l = Wg_leak.diff().abs().sum(axis=1).fillna(0.0)
net_l = port_l - to_l * BPS / 1e4 - (GEAR - 1) * RATE / 252
jk = pd.concat([arc.rename('a'), net_l.rename('l')], axis=1, join='inner').dropna()
mdm = float((jk.a - jk.l).abs().max())
print(f"  archive vs my lag=0 rebuild: maxdev={mdm:.3e} -> "
      f"{'MATCH: archive IS the leaked construction' if mdm < 1e-12 else 'DIFFERS'}")
jc = pd.concat([com.rename('c'), net.rename('n')], axis=1, join='inner').dropna()
mdc = float((jc.c - jc.n).abs().max())
print(f"  committed vs my lag=1 rebuild: maxdev={mdc:.3e} -> "
      f"{'MATCH: committed IS the causal construction' if mdc < 1e-12 else 'DIFFERS'}")
d_same = float((net_l - net).abs().max())
print(f"  same-day PnL term size |leak-causal| max daily = {d_same:.3e}")
ann_leak = (1 + net_l.dropna()).prod() ** (252 / len(net_l.dropna())) - 1
print(f"  leak ann={ann_leak:.4%} vs causal ann={m_b[0]:.4%}  delta={100*(ann_leak-m_b[0]):.2f}pp")
same_day_pnl = float((port_l - port - to_l * BPS / 1e4 + to * BPS / 1e4).mean() * 252)
print(f"  annualized same-day-weight PnL advantage of leak = {same_day_pnl:.4%}")

# --- IS/OOS split ---
print("\n[SPLIT] IS/OOS:")
for label, m in (("committed", com), ("archive", arc)):
    r = m.dropna()
    isr_ = r[r.index < IS_END]; oos = r[r.index >= IS_END]
    f = lambda x: ((1 + x).prod() ** (252 / len(x)) - 1) if len(x) else float('nan')
    print(f"  {label}: IS ann={f(isr_):.4%} (n={len(isr_)})  OOS ann={f(oos):.4%} (n={len(oos)})")
