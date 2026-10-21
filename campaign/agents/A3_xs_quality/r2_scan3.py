"""r2: diagnose yearly of best dual-mom cases; try absolute-momentum name screen."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
from r2lib import *
from engine import load_rets
import pandas as pd, numpy as np

px, rets = load_rets()
MES = [d for d in month_ends(rets) if d in px.index]
ff = D.ff_factors()
mkt = (1 + ff["Mkt-RF"] + ff["RF"]).cumprod()
gate_d = (mkt > mkt.rolling(200).mean()).astype(float).reindex(px.index).ffill()

sig121 = px.shift(21)/px.shift(252) - 1.0
feat = pd.read_parquet("/Users/daxu/software/world-trader/alphaportfolio_replication/data/daily_features.parquet")
feat["date"] = pd.to_datetime(feat["date"])
ivf = feat.pivot_table(index="date", columns="symbol", values="idio_vol")
posf = ivf.index.searchsorted(px.index, side="right") - 1; okf = posf >= 0
iv_p = pd.DataFrame(np.nan, index=px.index, columns=px.columns)
iv_p.loc[okf, :] = ivf.iloc[posf[okf]].reindex(columns=px.columns).values

def gated_lo(scores, g, frac=1/3, absmin=None, ivfilter=False):
    idx = rets.index; W = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    for t in [d for d in MES if d in scores.index]:
        row = scores.loc[t].dropna()
        if absmin is not None:
            a = absmin.loc[t, row.index] if t in absmin.index else None
            row = row[(a > 0)]
        if ivfilter and t in iv_p.index:
            iv = iv_p.loc[t, row.index]
            row = row[iv <= iv_p.loc[t].quantile(0.6)]
        if len(row) < 10: continue
        gi = g.loc[t] if t in g.index else 0.0
        if gi > 0:
            row = row.sort_values(); nl = max(int(np.floor(len(row)*frac)),1)
            for s in row.index[-nl:]: W.loc[t, s] = 1.0/nl
    return W

for tag, kw in [("base", {}), ("abs>0", dict(absmin=sig121)), ("abs>0+ivlow", dict(absmin=sig121, ivfilter=True))]:
    ok, g, r, net = run_gates(gated_lo(sig121, gate_d, **kw), rets, f"dualmom {tag}", verbose=False)
    yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    print(f"{tag:12s} SR={g['SR']:.2f} H1={g['H1']:.2f} H2={g['H2']:.2f} negYr={g['neg_years']} worst={g['worst_year']:.1f}%  negyrs={[ (int(k), round(v*100,1)) for k,v in yr.items() if v<0 ]}")
