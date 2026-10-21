"""A6 r2 mission 3: PAIR sleeve = 0.5*residmom_gated + 0.5*X (2022-positive library sleeve)."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from lib6 import stats, halves_sr, vol_target, scramble_pvalue
from idea234_engine import resid_momentum, weights_long, rets, px

_, resid_mom, _ = resid_momentum()
ok = rets.notna() & (px.notna().cumsum() >= 120)
W = weights_long(resid_mom, ok, frac=1/3, cadence=21)
mkt = px.mean(axis=1)

def gate_dual(dd_entry=20, dd_thresh=-0.15):
    ma_s = mkt.rolling(150, min_periods=75).mean()
    dd = (mkt / mkt.rolling(252, min_periods=126).max() - 1.0)
    above = (mkt > ma_s).values; below = (mkt < ma_s*0.98).values
    n = len(mkt); state = np.zeros(n); s = 0; cnt = 0
    for i in range(n):
        if np.isnan(ma_s.iloc[i]): continue
        need = dd_entry if (not np.isnan(dd.iloc[i]) and dd.iloc[i] < dd_thresh) else 10
        if s == 1 and below[i]: s = 0; cnt = 0
        elif s == 0:
            cnt = cnt + 1 if above[i] else 0
            if cnt >= need: s = 1
        state[i] = s
    return pd.Series(state, index=mkt.index)

G = gate_dual()
Wg = W.mul(G, axis=0)
gross = (Wg.shift(1)*rets).sum(axis=1)["2007-01-01":]
turn = (Wg.shift(1)-Wg.shift(2)).abs().sum(axis=1)["2007-01-01":].fillna(0.0)
rm_raw = (gross - turn*6/1e4).dropna()
rm_vt, _ = vol_target(rm_raw, 0.10)

LIB = "/Users/daxu/software/world-trader/campaign/results/sleeve_library"
def load_lib(name):
    df = pd.read_csv(f"{LIB}/{name}.csv", index_col=0)
    df.index = pd.to_datetime(df.index)
    s = pd.Series(df.iloc[:, 0].astype(float).values, index=df.index)
    return s[~s.index.duplicated(keep="last")].sort_index()

CANDS = ["CTA_Futures_15vol", "FactorMom_1926", "FactorMom_2008", "Factor_Momentum_FF",
         "ls_n10r14_2018", "Multi_Strategy_EW", "Multi_Strategy_SharpeW", "L_S_130_30",
         "Credit_z120_1986", "CTA_Futures_tsmom_10d", "CTA_Futures_multi_10d"]

def pair_gates(r, tag):
    s = stats(r); h = halves_sr(r); p = scramble_pvalue(r)
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    neg = {int(y): round(v*100,1) for y,v in yr.items() if v < 0}
    g = {"full": s['sr']>=0.6, "H1": h['H1']>=0.3, "H2": h['H2']>=0.3,
         "negYr": s['neg_years']<=2, "worst": s['worst_year']>-5.0, "scr": p<0.05}
    print(f"{tag:38s} SR={s['sr']:.2f} H1={h['H1']:.2f} H2={h['H2']:.2f} negYr={s['neg_years']}{neg} worst={s['worst_year']:6.1f}% scr={p:.3f} {'*** ALL GATES PASS ***' if all(g.values()) else 'fail:'+str([k for k,v in g.items() if not v])}")
    return all(g.values()), r

print("=== legs ===")
_, _ = pair_gates(rm_vt, "residmom_gated_vt (leg1)")
for c in CANDS:
    try:
        x = load_lib(c)
        xv, _ = vol_target(x, 0.10)  # vol-target X leg to 10% too (trailing only)
        pair_gates(xv["2007-01-01":], f"leg2 {c}")
    except Exception as e:
        print(c, "ERR", e)
print("=== pairs 50/50 (both legs vol-tgt 10%, then pair vol-tgt 10%) ===")
for c in CANDS:
    try:
        x = load_lib(c)
        xv, _ = vol_target(x, 0.10)
        pair = (0.5*rm_vt + 0.5*xv).dropna()
        pair_vt, _ = vol_target(pair, 0.10)
        pair_gates(pair_vt, f"PAIR rm+{c}")
    except Exception as e:
        print(c, "ERR", e)
