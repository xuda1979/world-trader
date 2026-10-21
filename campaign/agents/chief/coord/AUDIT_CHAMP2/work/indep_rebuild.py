#!/usr/bin/env python3
"""AUDIT_CHAMP2 — INDEPENDENT rebuild of RAWEW13v2 champion.
NO import of the builder. Every step re-derived from raw sleeve CSVs only.
Then byte-compare to the committed champion CSV."""
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
SLEEVES = {
 "brwt15":"campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 "brwt10":"campaign/agents/COORD/sleeves/brwt10_2000.csv",
 "brwt7" :"campaign/agents/COORD/sleeves/brwt7.csv",
 "brwt5" :"campaign/agents/COORD/sleeves/brwt5.csv",
 "C5ng"  :"campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsum":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 "A5r2"  :"campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 "a6r7"  :"campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "QAxasts":"campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 "carryv2":"campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
 "diescrack":"campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
 "CFX4"  :"campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
}
GEAR, RATE, BPS, P, IS_END = 1.6, 0.045, 6.4, 0.55, pd.Timestamp('2017-01-01')

def load(name, path):
    df = pd.read_csv(f"{ROOT}/{path}")
    df['date'] = pd.to_datetime(df['date'])
    s = pd.to_numeric(df['ret'], errors='coerce')
    s.index = df['date']
    return s.rename(name)

sers = [load(n,p) for n,p in SLEEVES.items()]
df = pd.concat(sers, axis=1).sort_index()
df = df[df.index >= '2008-03-31']
print("panel:", df.shape, df.index.min().date(), "->", df.index.max().date())
print("per-sleeve non-NaN counts inside panel:")
print(df.notna().sum().to_string())
print("total NaN cells:", int(df.isna().sum().sum()))

# --- independent IS SR (sample std ddof=1, >=200 obs rule) ---
isr = df[df.index < IS_END]
SR = {}
for n in df.columns:
    r = isr[n].dropna()
    SR[n] = float(r.mean()/r.std(ddof=1)*np.sqrt(252)) if (len(r)>=200 and r.std(ddof=1)>1e-12) else 0.0
SR = pd.Series(SR)
relw = np.maximum(SR,0.0)**P
print("\nIS SR and relw:")
print(pd.concat([SR.rename('IS_SR'), relw.rename('relw')], axis=1).round(4).to_string())

# --- NAV-drift weights, row-normalized, scaled to GEAR/K ---
filled = df.fillna(0.0)
nav = (1+filled).cumprod()
K = len(df.columns)
d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
d2 = d2.div(d2.sum(axis=1), axis=0)*K
Wg = d2*(GEAR/K)
port = (filled.values*Wg.values).sum(axis=1)
to = Wg.diff().abs().sum(axis=1).fillna(0.0)
net = pd.Series(port, index=df.index) - to*BPS/1e4 - np.maximum(GEAR-1,0)*RATE/252
gross = Wg.abs().sum(axis=1)

# --- metrics (independent) ---
r = net.dropna()
yrs = (1+r).groupby(r.index.year).prod()-1
ann_geo = (1+r).prod()**(252/len(r))-1
sr_d = r.mean()/r.std(ddof=1)*np.sqrt(252)
cs = r.cumsum(); mdd = (cs-cs.cummax()).min()
print(f"\nINDEP REBUILD: ann_geo={ann_geo:.4%} SR_d={sr_d:.3f} MDD={mdd:.4%} "
      f"neg={int((yrs<0).sum())}/{len(yrs)} worst={yrs.min():.4%} n={len(r)}")
print(f"gross: mean={gross.mean():.10f} max={gross.max():.12f} days>1.6+1e-9={int((gross>1.6+1e-9).sum())}")
print(f"turnover: mean_daily={to.mean():.3e} ann_cost={to.mean()*252*BPS:.2f}bps/yr")

# --- byte compare to committed champion + weights ---
old = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                  index_col=0, parse_dates=True).iloc[:,0]
j = pd.concat([old.rename('c'), net.rename('i')], axis=1, join='inner').dropna()
md = float((j.c-j.i).abs().max())
print(f"\nBYTE-REPRO vs committed champion: n_committed={len(old)} n_indep={len(net)} inner={len(j)} maxdev={md:.3e}")
oldw = pd.read_csv(f"{ROOT}/campaign/results/RAWEW13v2_IS_SR_weights.csv", index_col=0).iloc[:,0]
ow = pd.concat([oldw.rename('c'), relw.rename('i')], axis=1, join='inner').dropna()
print(f"weights: maxdev={float((ow.c-ow.i).abs().max()):.3e}")
