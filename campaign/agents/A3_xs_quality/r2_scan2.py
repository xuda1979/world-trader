"""r2 refinements: dual-momentum gating, risk-adj momentum, TS momentum, combos."""
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
vol252 = rets.rolling(252, min_periods=200).std()
sig_ramom = sig121 / vol252                      # risk-adjusted momentum
sighw = px / px.rolling(252, min_periods=200).max()

def gated_long_only(scores, g, frac=1/3):
    idx = rets.index; W = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    for t in [d for d in MES if d in scores.index]:
        row = scores.loc[t].dropna()
        if len(row) < 10: continue
        row = row.sort_values(); nl = max(int(np.floor(len(row)*frac)),1)
        gi = g.loc[t] if t in g.index else 0.0
        if gi > 0:
            for s in row.index[-nl:]: W.loc[t, s] = 1.0/nl
        # flat when gate off (absolute momentum)
    return W

def ts_mom(sig, frac=0.34):
    """sign of own past return among names with |sig| big enough; L/S neutral"""
    idx = rets.index; W = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    for t in [d for d in MES if d in sig.index]:
        row = sig.loc[t].dropna()
        if len(row) < 10: continue
        n = len(row); k = max(int(np.floor(n*frac)),1)
        top = row.nlargest(k).index; bot = row.nsmallest(k).index
        for s in top: W.loc[t, s] = 1.0/k
        for s in bot: W.loc[t, s] -= 1.0/k
    return W

def blend(scores_list, frac=1/3, longs_only=False):
    """avg of cross-sectional ranks"""
    rk = sum(s.rank(axis=1, pct=True) for s in scores_list) / len(scores_list)
    idx = rets.index; W = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    for t in [d for d in MES if d in rk.index]:
        row = rk.loc[t].dropna()
        if len(row) < 10: continue
        row = row.sort_values(); nl = max(int(np.floor(len(row)*frac)),1)
        if longs_only:
            for s in row.index[-nl:]: W.loc[t, s] = 1.0/nl
        else:
            ns = max(int(np.floor(len(row)*frac)),1)
            for s in row.index[-nl:]: W.loc[t, s] = 1.0/nl
            for s in row.index[:ns]: W.loc[t, s] -= 1.0/ns
    return W

# feat for low-iv filter
feat = pd.read_parquet("/Users/daxu/software/world-trader/alphaportfolio_replication/data/daily_features.parquet")
feat["date"] = pd.to_datetime(feat["date"])
ivf = feat.pivot_table(index="date", columns="symbol", values="idio_vol")
posf = ivf.index.searchsorted(px.index, side="right") - 1
okf = posf >= 0
iv_p = pd.DataFrame(np.nan, index=px.index, columns=px.columns)
iv_p.loc[okf, :] = ivf.iloc[posf[okf]].reindex(columns=px.columns).values

sig121_lv = sig121.where(iv_p.le(iv_p.quantile(0.5, axis=1), axis=0))

CASES = [
 ("R1_dualmom121_gate",   gated_long_only(sig121, gate_d),  None),
 ("R2_dualmom_RA_gate",   gated_long_only(sig_ramom, gate_d), None),
 ("R3_dualmom_HW_gate",   gated_long_only(sighw, gate_d),   None),
 ("R4_dualmom_blend_gate",gated_long_only((sig121.rank(axis=1,pct=True)+sighw.rank(axis=1,pct=True)+sig_ramom.rank(axis=1,pct=True))/3, gate_d), None),
 ("R5_tsmom121",          ts_mom(sig121),                   None),
 ("R6_tsmom121_gateL",    None,                             None),  # filled below
 ("R7_blend_LS",          blend([sig121, sighw, sig_ramom]), None),
 ("R8_blend_longonly_gate",gated_long_only((sig121.rank(axis=1,pct=True)+sighw.rank(axis=1,pct=True))/2, gate_d), None),
 ("R9_lowiv_dualmom",     gated_long_only(sig121_lv.where(sig121_lv>0), gate_d), None),
]
# R6: TS mom longs only when gate on (crash-avoid on longs)
Wts = ts_mom(sig121)
CASES[5] = ("R6_tsmom121_gateL", Wts.clip(lower=0).mul(gate_d, axis=0).add(Wts.clip(upper=0), axis=0), None)

out = {}
for name, W, st in CASES:
    ok, g, r, net = run_gates(W, rets, name, verbose=False)
    out[name] = (ok, g, r)
    print(f"{name:26s} SR={g['SR']:.2f} H1={g['H1']:.2f} H2={g['H2']:.2f} "
          f"negYr={g['neg_years']} worst={g['worst_year']:.1f}% ann={g['ann']:.1f}% corrMKT~{np.corrcoef(r, mkt.reindex(r.index).ffill())[0,1]:.2f} "
          f"{'PASS' if ok else 'fail'}")
