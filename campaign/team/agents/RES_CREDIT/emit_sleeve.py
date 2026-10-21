"""Emit the best RES_CREDIT candidate sleeve (REJECT-labeled) — thin, reproducible."""
import sys

sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/team/agents/RES_CREDIT")

import pandas as pd
import credit_lib as C

OUT = "/Users/daxu/software/world-trader/campaign/team/agents/RES_CREDIT/sleeves/RC_t102_d5mr_w21_band50_vt5.csv"

t102 = C.load_series(f"{C.FRED}/t10y2y.csv")
d102 = t102.diff()
mom = t102.diff(5)
m = mom.rolling(21, min_periods=10).mean().shift(1)
s = mom.rolling(21, min_periods=10).std().shift(1)
z = (mom - m) / s.replace(0, float('nan'))
w = (-z / 2.0).clip(-0.5, 0.5).where(z.abs() > 0.5, 0.0)
idx = z.dropna().index
W = pd.DataFrame({'a': w.reindex(idx).fillna(0.0)}, index=idx)
R = pd.DataFrame({'a': d102.reindex(idx)})
net, We, gross = C.net_of(W, R, vt=True, target=0.05)
out = net.rename('ret').to_frame()
out.index.name = 'date'
out.to_csv(OUT)
print("wrote", OUT, "n=", len(out), "SR_d=", round(float(net.mean() / net.std(ddof=1) * 252 ** 0.5), 3))
