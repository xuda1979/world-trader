"""A6 r2 mission-3 PAIR sleeve #2 (PASSES ALL GATES r2):
0.5 * residmom_gated(MA150 c10, ddEntry 20d/-15%) + 0.5 * Multi_Strategy_EW, vol-tgt 10% each + pair.
Gates (r2): SR 0.88 | H1 0.70 / H2 1.11 | neg years 2 (2015 -0.3%, 2022 -3.7%) | worst -3.7% |
signal-scramble p=0.000 | plateau neighborhood min 0.80 (peak 0.92 for this X)."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from lib6 import closes, stats, halves_sr, vol_target
from idea234_engine import resid_momentum, weights_long, rets, px

OUT = "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/sleeves/a6_r2_pair_residmom_msew.csv"

_, resid_mom, _ = resid_momentum()
ok = rets.notna() & (px.notna().cumsum() >= 120)
W = weights_long(resid_mom, ok, frac=1/3, cadence=21)
mkt = px.mean(axis=1)
ma = mkt.rolling(150, min_periods=75).mean()
dd = mkt / mkt.rolling(252, min_periods=126).max() - 1.0
state = np.zeros(len(mkt)); s = 0; cnt = 0
for i in range(len(mkt)):
    if np.isnan(ma.iloc[i]): continue
    need = 20 if (not np.isnan(dd.iloc[i]) and dd.iloc[i] < -0.15) else 10
    if s == 1 and mkt.iloc[i] < ma.iloc[i]*0.98: s = 0; cnt = 0
    elif s == 0:
        cnt = cnt + 1 if mkt.iloc[i] > ma.iloc[i] else 0
        if cnt >= need: s = 1
    state[i] = s
gate = pd.Series(state, index=mkt.index)
Wg = W.mul(gate, axis=0)
gross = (Wg.shift(1) * rets).sum(axis=1)["2007-01-01":]
turn = (Wg.shift(1) - Wg.shift(2)).abs().sum(axis=1)["2007-01-01":].fillna(0.0)
rm_net = (gross - turn*6/1e4).dropna()
rm_vt, _ = vol_target(rm_net, 0.10)

lib = pd.read_csv("/Users/daxu/software/world-trader/campaign/results/sleeve_library/Multi_Strategy_EW.csv", index_col=0)
lib.index = pd.to_datetime(lib.index)
x = pd.Series(lib.iloc[:, 0].astype(float).values, index=lib.index)
x = x[~x.index.duplicated(keep="last")].sort_index()
x_vt, _ = vol_target(x, 0.10)

pair = (0.5*rm_vt + 0.5*x_vt).dropna()
pair, _ = vol_target(pair, 0.10)
pair.to_csv(OUT, header=["ret"], index_label="date")
st = stats(pair); h = halves_sr(pair)
print(f"saved {OUT}: SR={st['sr']:.2f} H1={h['H1']:.2f} H2={h['H2']:.2f} negYr={st['neg_years']} worst={st['worst_year']:.1f}%")
