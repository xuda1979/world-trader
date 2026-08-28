"""r2: gate variants to fix 2022; then full gates + plateau on the best."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
from r2lib import *
from engine import load_rets
import pandas as pd, numpy as np

px, rets = load_rets()
MES = [d for d in month_ends(rets) if d in px.index]
ff = D.ff_factors()
mkt = (1 + ff["Mkt-RF"] + ff["RF"]).cumprod()

gates = {
 "ma200":      (mkt > mkt.rolling(200).mean()).astype(float),
 "ma250":      (mkt > mkt.rolling(250).mean()).astype(float),
 "abs12m":     (mkt.pct_change(252) > 0).astype(float),
 "abs12m_126": (mkt.pct_change(126) > 0).astype(float),
 "ma200_band": np.where(mkt > mkt.rolling(200).mean()*1.03, 1.0,
                np.where(mkt < mkt.rolling(200).mean()*0.97, 0.0, np.nan)),
 "ma200_rise": ((mkt > mkt.rolling(200).mean()) & (mkt.rolling(200).mean() > mkt.rolling(200).mean().shift(21))).astype(float),
 "combo":      ((mkt.pct_change(252) > 0) & (mkt > mkt.rolling(200).mean())).astype(float),
}
sig121 = px.shift(21)/px.shift(252) - 1.0

def gated_lo(scores, gser, frac=1/3):
    g = gser.reindex(px.index).ffill()
    # band hysteresis: forward-fill nan in band gate to last state
    g = g.ffill().fillna(0.0)
    idx = rets.index; W = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    for t in [d for d in MES if d in scores.index]:
        row = scores.loc[t].dropna()
        if len(row) < 10: continue
        if g.loc[t] > 0:
            row = row.sort_values(); nl = max(int(np.floor(len(row)*frac)),1)
            for s in row.index[-nl:]: W.loc[t, s] = 1.0/nl
    return W

res = {}
for gname, gser in gates.items():
    gser = pd.Series(gser, index=mkt.index) if not isinstance(gser, pd.Series) else gser
    ok, g, r, net = run_gates(gated_lo(sig121, gser), rets, f"dualmom {gname}", verbose=False)
    yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    res[gname] = (ok, g)
    print(f"{gname:12s} SR={g['SR']:.2f} H1={g['H1']:.2f} H2={g['H2']:.2f} negYr={g['neg_years']} worst={g['worst_year']:.1f}% ann={g['ann']:.1f}%  neg={[ (int(k), round(v*100,1)) for k,v in yr.items() if v<0 ]}")
import pickle; pickle.dump(res, open("/tmp/r2gates.pkl","wb"))
