import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emfx_lib as L

ch = L.champion()
print("champion: sha", L.sha16(L.CHAMP_CSV), "n", len(ch), ch.index.min().date(), ch.index.max().date())
px = L.panel()
print("\npanel USDXXX (champion calendar):")
print(px.describe().T[["count","min","max"]])
print("last row:\n", px.tail(2))
print("NaN counts:\n", px.isna().sum())
# where does PLN die?
print("\nPLN last valid:", px["PLN"].dropna().index.max().date(), " -> NaN days after:",
      int(px["PLN"].isna().sum()))
c = L.carry_brl(ch.index)
print("\nBRL carry daily (dec): mean %.6f  ann %.4f%%  min %.6f  max %.6f  frac>0 %.3f" % (
      c.mean(), c.mean()*252*100, c.min(), c.max(), (c>0).mean()))
print("carry at anchors:", {d: round(float(c.asof(pd.Timestamp(d))),6) for d in
      ["2008-06-30","2015-06-30","2020-08-14","2023-08-15","2026-08-28"]})
pu = L.total_perunit(px, c)
print("\nper-unit total returns (long EM):")
print(pu.describe().T[["count","mean","std","min","max"]])
print("annualized mean:", {k: round(float(v.mean()*252*100),3) for k,v in pu.items()})
print("annualized vol :", {k: round(float(v.std()*np.sqrt(252)*100),3) for k,v in pu.items()})
