"""Reproducible build of sleeve a6_r7_bond2y_trend (A6_reversal, round r7).
PROTOCOL (canonical, mirrors scripts/r7_idea1_save.py): FRED DGS2 quote dates only (no synthetic
calendar; H.15 publication dates are the data). Synthetic 2y Treasury total return
TR = -1.9 * d(y) + y/252  (y in DECIMAL, par-bond approx incl carry). LONG when trailing 378-obs
mean TR > 0 else FLAT; decisions frozen every 42 obs; T+1 (W.shift(1)*TR); 6bps/side on |dW|;
vol-target 12% ann trailing expanding min-60d, cap 5x. Eval 2007+.
Validated r7: SR 1.43 | H1 1.14 / H2 1.81 | negYr 2/20 (2014 -0.5, 2021 -4.1) | scramble p=0.005
| SR plateau k315..441 x cad 21/42/63 all 1.38-1.43, gate-d holds at all 9 interior points
(k252 and k504 disclosed as softer/failing) | corr to champion6 = -0.00.
Run: python3 campaign/scripts/a6_r7_bond2y_trend.py"""
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
DGS2 = f"{ROOT}/tools/quant/hedge_fund_strats/data_fred_new/DGS2.csv"
OUT = f"{ROOT}/campaign/agents/A6_reversal/sleeves/a6_r7_bond2y_trend.csv"
START, VT, CAP, COST_BPS, DUR, K, CAD = "2007-01-01", 0.12, 5.0, 6.0, 1.9, 378, 42

y = pd.read_csv(DGS2, index_col=0, parse_dates=True)["value"].astype(float) / 100.0
y = y[~y.index.duplicated(keep="last")].sort_index()
tr = (-DUR * y.diff() + y / 252.0).dropna()          # excess-return stream incl carry

sig = (tr.rolling(K).mean() > 0).astype(float)        # long/flat on policy-path trend
W = sig.iloc[::CAD].reindex(tr.index).ffill().fillna(0.0)   # cadence freeze

gross = (W.shift(1) * tr)[START:]                     # T+1 execution
turn = (W.shift(1) - W.shift(2)).abs()[START:].fillna(0.0)
net = (gross - turn * COST_BPS / 1e4).dropna()
lev = (VT / np.sqrt(252) / net.expanding(60).std().shift(1)).clip(0, CAP).fillna(0.0)
r = (net * lev).dropna()

df = pd.DataFrame({"ret": r.values}, index=r.index)
df.index.name = "date"
df.to_csv(OUT)
sr = r.mean() / r.std() * np.sqrt(252)
yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
neg = {int(k): round(v * 100, 1) for k, v in yr.items() if v < 0}
print(f"saved {OUT}\nSR={sr:.2f} ann={r.mean()*252*100:.1f}% vol={r.std()*np.sqrt(252)*100:.1f}% "
      f"negYr={len(neg)}{neg}")
