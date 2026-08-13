"""Refined multi-strategy blend test (2026-08-13).

Tests the MULTI-STRATEGY category more rigorously: blend ONLY the
positive-edge, low/negative-correlation streams (hedge-fund suite + the
two validated cross-suite legs) instead of including negative stat-arb.

Streams (all 6 bps costs built in where applicable):
  hedge_ms_ew  : existing multi-strategy EW (L/S+CTA+macro+statarb) on full 18y
  ls_volman    : L/S 130/30 vol-managed (hedge suite, positive, β0)
  riskparity   : Risk Parity Bridgewater-style (hedge suite)
  cta_fut      : CTA Futures (macro 21d) (hedge suite, small positive)
  fx_carry     : FX Carry (hedge suite, small positive)
  ls_champ     : polygon LS champion @3x (DIVERSIFIER, 2024-07+)
  ap_gold      : AP gold composite (validated, full 18y daily)

Two windows:
  FULL (2008-2026): hedge suite streams + ap_gold
  RECENT (2024-07+): add ls_champ (only ~2y history)
"""
import sys, os
from pathlib import Path
import pandas as pd, numpy as np

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
ROOT = HERE.parent.parent.parent

def load(path, col=0):
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    s = df.iloc[:, col]
    return s.astype(float)

def perf(r):
    r = r.dropna()
    eq = (1 + r).cumprod()
    n = len(r); ret = (eq.iloc[-1])**(252/n)-1
    vol = r.std()*np.sqrt(252)
    sharpe = r.mean()/r.std()*np.sqrt(252) if r.std()>0 else np.nan
    dd = (eq/eq.cummax()-1).min()
    return dict(n=n, ret=ret, vol=vol, sharpe=sharpe, maxdd=dd)

streams = {
    "hedge_ms_ew": load(RES/"equity_Multi_Strategy_EW.csv").pct_change(),
    "ls_volman":   load(RES/"equity_L_S_130_30_volmanaged.csv").pct_change(),
    "riskparity":  load(RES/"equity_Risk_Parity_Bridgewater.csv").pct_change(),
    "cta_fut":     load(RES/"equity_CTA_Futures_macro_21d.csv").pct_change(),
    "fx_carry":    load(RES/"equity_FX_Carry.csv").pct_change(),
}
# cross-suite validated legs
ap = load(ROOT/"alphaportfolio_replication/data/wf_champion_gold_opt_daily.csv")
ap = ap[ap.index!=0] if 0 in ap.index else ap
streams["ap_gold"] = ap
ls = load(ROOT/"alphaportfolio_replication/data/ls_polygon_daily.csv", col=0)
streams["ls_champ"] = ls[ls!=0]

def blend(sts, names, window):
    df = pd.concat([sts[n] for n in names], axis=1)
    if window=="full":
        df = df[df.index>="2008-02-01"]
    else:
        df = df[df.index>="2024-07-24"]
    df = df.ffill()
    # require every stream to have real (non-ffilled-leading) data over window
    df = df.dropna()
    ew = df.mean(axis=1)
    c = df.corr()
    return ew, c, perf(ew)

print("="*72)
print("REFINED MULTI-STRATEGY BLENDS (6 bps, free data)")
print("="*72)

cases = [
    ("FULL 18y: hedge EW + AP gold", ["hedge_ms_ew","ap_gold"], "full"),
    ("FULL 18y: LSvolman+RP+CTA+FX + AP gold", ["ls_volman","riskparity","cta_fut","fx_carry","ap_gold"], "full"),
    ("FULL 18y: LSvolman+RP+CTA+FX (no AP)", ["ls_volman","riskparity","cta_fut","fx_carry"], "full"),
    ("RECENT: hedge EW + AP gold + LS champ", ["hedge_ms_ew","ap_gold","ls_champ"], "recent"),
    ("RECENT: LSvolman+RP+CTA+FX+AP+LSchamp", ["ls_volman","riskparity","cta_fut","fx_carry","ap_gold","ls_champ"], "recent"),
]

for label, names, win in cases:
    ew, c, p = blend(streams, names, win)
    print(f"\n## {label}")
    print(f"   Sharpe {p['sharpe']:.3f} | ret {p['ret']*100:.1f}% | vol {p['vol']*100:.1f}% | MaxDD {p['maxdd']*100:.1f}% | n={p['n']}")
    # avg pairwise |corr| excluding diagonal
    tri = c.where(np.triu(np.ones(c.shape),1).astype(bool))
    print(f"   mean |pairwise corr|: {np.nanmean(np.abs(tri.values)):.3f}")
