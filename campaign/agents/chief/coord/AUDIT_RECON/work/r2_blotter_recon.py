#!/usr/bin/env python3
"""R2(a) AUDIT_RECON: full blotter reconciliation of the RE-EMITTED champion
(GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv, causal nav.shift(1) re-emit 2026-09-07 00:45).

Checks, all against the actual construction path in scripts/rawew13v2_build.py:
  A1 cost charge per day == FULL |dW| row-sum x 6.4bp (exact, per-day)
  A2 margin charge per day == 4.5%/yr x (1.6-1) / 252 (exact constant)
  A3 algebra: CSV ret == port - cost - margin (max abs dev, expect ~1e-16)
  A4 no-lookahead: corr(|dW|_t, r_t) and corr(|dW|_t, r_{t+1}) on NEW vs ARCHIVED leak file
     (expect new ~0.2 / near-0, NOT the 0.34/0.78 leak signature)
  A5 gross exposure == 1.6 every day; day-1 entry-cost treatment quantified
  A6 per-day ledger table head/tail printed for the record
"""
import sys
sys.path.insert(0, 'campaign'); sys.path.insert(0, 'campaign/scripts')
import numpy as np, pandas as pd
import rawew13v2_build as B

ROOT = B.ROOT
champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0]
arch = pd.read_csv(f"{ROOT}/campaign/results/archive_GOAL100_RAWEW13v2_WEIGHTED_GEAR16_SAMEDAYLEAK_ann40.84.csv",
                   index_col=0, parse_dates=True).iloc[:, 0]

# Rebuild the full internal path (identical calls as build(), but keep intermediates)
df = pd.DataFrame({n: B.load(B.PATHS[n]).dropna() for n in B.NAMES})
df = df[df.index >= '2008-03-31']
isr = df[df.index < B.IS_END]
SR = pd.Series({n: B.is_sr(isr[n]) for n in B.NAMES})
relw = np.maximum(SR, 0.0) ** B.P
nav_c = (1 + df.fillna(0)).cumprod()
nav = nav_c.shift(1).fillna(1.0)                    # T+1 CAUSAL (re-emit)
d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
d2 = d2.div(d2.sum(axis=1), axis=0) * len(B.NAMES)
Wg = d2 * (B.GEAR / len(B.NAMES))
port = (df.fillna(0).values * Wg.values).sum(axis=1)
port = pd.Series(port, index=df.index)
to = Wg.diff().abs().sum(axis=1).fillna(0.0)
cost = to * B.BPS / 1e4
margin_daily = np.maximum(B.GEAR - 1, 0) * B.RATE / 252
net = port - cost - margin_daily

fails = []
def check(name, cond, detail):
    tag = "PASS" if cond else "FAIL"
    print(f"[{tag}] {name}: {detail}")
    if not cond: fails.append(name)

print("=" * 78)
print("A1 COST: per-day charge vs FULL |dW| x 6.4bp")
ret = champ.reindex(net.index)
csv_cost = (port - margin_daily) - ret            # implied cost inside committed CSV
dev_cost = float((csv_cost - cost).abs().max())
check("A1", dev_cost < 1e-15, f"max|csv_implied_cost - |dW|*6.4bp| = {dev_cost:.3e}")
print(f"      charged cost total {cost.sum()*1e4:.4f} bp-sum over {len(cost)} days; "
      f"mean {cost.mean()*1e4:.6f} bp/day -> annualized {to.mean()*252*B.BPS:.4f} bp/yr (charter expects ~4.94)")

print("A2 MARGIN: per-day charge vs 4.5%*(1.6-1)/252")
csv_margin = (port - cost) - ret
dev_mgn = float((csv_margin - margin_daily).abs().max())
check("A2", dev_mgn < 1e-15, f"max|csv_implied_margin - {margin_daily:.8e}| = {dev_mgn:.3e}; "
      f"unique csv-implied daily margins n={csv_margin.round(15).nunique()}")

print("A3 ALGEBRA: CSV ret == port - cost - margin")
dev_alg = float((net - ret).abs().max())
check("A3", dev_alg < 1e-14, f"max|net - csv| = {dev_alg:.3e}")

print("A4 NO-LOOKAHEAD perturbation (leak signature was corr(dW,r_t)=0.78 / to-vs-ret 0.34)")
r_t = df.fillna(0).sum(axis=1)  # NOT the portfolio ret; use portfolio gross return below
gross_ret_c = port / Wg.abs().sum(axis=1)         # per-unit-gross portfolio return day t
def xc(a, b):
    j = pd.concat([a, b], axis=1, join='inner').dropna()
    return float(j.iloc[:, 0].corr(j.iloc[:, 1]))
# NEW champion
dw_new = Wg.diff().abs().sum(axis=1)
c_same_new = xc(dw_new, port)                     # turnover vs SAME-day port ret
c_next_new = xc(dw_new, port.shift(-1))           # turnover vs NEXT-day port ret
dwvec_new = Wg.diff().abs().mul(relw, axis=1).sum(axis=1)  # proxy per-sleeve |dW|
c_dw_same_new = xc(dw_new, gross_ret_c)
# ARCHIVED leak champion: rebuild with nav_t (no shift) to expose its dW path
nav_l = nav_c
d2l = nav_l.div(nav_l.mean(axis=1), axis=0).mul(relw, axis=1)
d2l = d2l.div(d2l.sum(axis=1), axis=0) * len(B.NAMES)
Wg_l = d2l * (B.GEAR / len(B.NAMES))
port_l = pd.Series((df.fillna(0).values * Wg_l.values).sum(axis=1), index=df.index)
dw_l = Wg_l.diff().abs().sum(axis=1)
gross_ret_l = port_l / Wg_l.abs().sum(axis=1)
c_same_l = xc(dw_l, port_l)
c_next_l = xc(dw_l, port_l.shift(-1))
c_dw_same_l = xc(dw_l, gross_ret_l)
check("A4a", abs(c_dw_same_new) < 0.5 and c_dw_same_new < c_dw_same_l,
      f"corr(|dW_t|, r_t) NEW={c_dw_same_new:.4f} vs ARCHIVED-leak={c_dw_same_l:.4f} (R1 leak signature 0.78)")
check("A4b", abs(c_same_new) < 0.5,
      f"corr(|dW_t|, portret_t) NEW={c_same_new:.4f} (archived {c_same_l:.4f}); next-day corr NEW={c_next_new:.4f} (arch {c_next_l:.4f})")
# direct same-day causality: FUTURE-TRUNCATION perturbation. Zero every sleeve return from day
# t onward; rebuild the ENTIRE pipeline; Wg_t must be byte-identical (it may only depend on
# returns <= t-1 via nav.shift(1), and on same-row cross-sectional means of those shifted navs).
# (Note: an extra nav.shift(1) is NOT invariance-preserving here because it also shifts the
# nav.mean(axis=1) row denominator — first A4c attempt failed on that test-construction error.)
def wg_from(df_in):
    nv = (1 + df_in.fillna(0)).cumprod().shift(1).fillna(1.0)
    dd = nv.div(nv.mean(axis=1), axis=0).mul(relw, axis=1)
    dd = dd.div(dd.sum(axis=1), axis=0) * len(B.NAMES)
    return dd * (B.GEAR / len(B.NAMES))
max_dev_trunc = 0.0
for t in [0, 1, 2, 100, 1200, 2400, 3600, 4804]:
    dtr = df.copy()
    dtr.iloc[t:] = 0.0
    devt = float((Wg.iloc[t] - wg_from(dtr).iloc[t]).abs().max())
    max_dev_trunc = max(max_dev_trunc, devt)
check("A4c", max_dev_trunc < 1e-18,
      f"Wg_t invariant to zeroing all returns >= t at 8 probe days (max dev {max_dev_trunc:.3e}) "
      f"=> Wg_t uses returns <= t-1 only")

print("A4d charter-statistic apples-to-apples (R1 quoted corr(dW_i,r_i)=0.78 xsec / 0.34 to-ret)")
Rz = df.fillna(0)
def xsec_mean_corr(Wg):
    dW = Wg.diff(); cs = []
    for i in range(1, len(Rz)):
        a, b = dW.iloc[i].values, Rz.iloc[i].values
        if a.std() > 0 and b.std() > 0:
            cs.append(np.corrcoef(a, b)[0, 1])
    return float(np.nanmean(cs))
cs_new, cs_leak = xsec_mean_corr(Wg), xsec_mean_corr(Wg_l)
check("A4d", abs(cs_new) < 0.10 and cs_leak > 0.7,
      f"mean per-day xsec corr(dW_i, r_i): NEW={cs_new:+.4f} (want ~0) vs LEAK-construction={cs_leak:+.4f} "
      f"(reproduces R1's 0.78 signature on the archived mechanism); "
      f"corr(sum|dW|_t, portret_t) NEW={c_same_new:+.4f} ~ charter's '0.2 legitimate responsiveness'")

print("A5 GROSS + day-1 entry")
g = Wg.abs().sum(axis=1)
check("A5a", abs(g.mean() - 1.6) < 1e-12 and int((g > 1.6 + 1e-9).sum()) == 0,
      f"gross mean {g.mean():.9f} max {g.max():.12f} days>1.6+eps = {int((g>1.6+1e-9).sum())}")
entry_cost_bp = g.iloc[0] * B.BPS
to0 = float(to.iloc[0])
check("A5b", to0 == 0.0,
      f"day-1 turnover charged = {to0} (builder charges NO day-1 entry cost; "
      f"uncharged entry leg = {entry_cost_bp:.2f} bp one-time = {entry_cost_bp/252/19:.5f} bp/yr-equiv)")

print("A6 ledger head/tail (date, ret_csv, port, cost_bp, margin_bp)")
led = pd.DataFrame({"ret_csv": ret, "port": port, "cost_bp": cost * 1e4,
                    "margin_bp": margin_daily * 1e4, "to_bp": to * 1e4})
print(led.head(3).to_string(float_format=lambda v: f"{v:.8f}"))
print(led.tail(3).to_string(float_format=lambda v: f"{v:.8f}"))

# Honest metrics of the committed champion (verify headline 39.85%)
r = ret.dropna()
ann = (1 + r).prod() ** (252 / len(r)) - 1
sr = r.mean() / r.std(ddof=1) * np.sqrt(252)
navp = (1 + r).cumprod(); mdd = float((navp / navp.cummax() - 1).min())
ny = int((r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1) < 0).sum())
print("=" * 78)
print(f"COMMITTED champion honest metrics: n={len(r)} ann={ann*100:.2f}% SR={sr:.3f} MDD={mdd*100:.2f}% neg_years={ny}")
print(f"archived (leak) headline for contrast: ann from file name = 40.84%; "
      f"recomputed from archived csv: ", end="")
ra = arch.dropna(); print(f"ann={((1+ra).prod()**(252/len(ra))-1)*100:.2f}% "
      f"SR={ra.mean()/ra.std(ddof=1)*np.sqrt(252):.3f}")

print("=" * 78)
print("FAILS:", fails if fails else "none — ALL CHECKS PASS")
sys.exit(1 if fails else 0)
