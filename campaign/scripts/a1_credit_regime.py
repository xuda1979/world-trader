"""A1_credit_regime_mom (r7) — credit-spread momentum regime book on FRED DBAA (1990+).
Long BAA-index synth TR (dur 7) when BAA yield fell over trailing 252d (spread tightening
regime), flat (cash at rf) else. T+1, 6bps one-side x |dsize|, trailing expanding vt10 cap2,
honest funding rf + size*(leg-rf). Window 1990-01-03+. Repro: python3 a1_credit_regime.py"""
import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
import numpy as np, pandas as pd
NEW = "/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred_new"
COST = 0.0006
dbaa = pd.read_csv(f"{NEW}/DBAA.csv")
y = pd.to_numeric(dbaa["value"], errors="coerce"); y.index = pd.to_datetime(dbaa["date"])
y = y.dropna(); y = y[~y.index.duplicated(keep="last")].sort_index()
y = y.reindex(pd.bdate_range(y.index[0], pd.Timestamp("2026-08-28"))).ffill()/100.0
tb = pd.read_csv(f"{NEW}/DTB3.csv")
tb3 = pd.to_numeric(tb["value"], errors="coerce"); tb3.index = pd.to_datetime(tb["date"])
tb3 = tb3.dropna(); tb3 = tb3[~tb3.index.duplicated(keep="last")].sort_index()
tb3 = tb3.reindex(y.index).ffill()/100.0
rf = tb3/252.0
ex = (y/252.0 - 7.0*y.diff()) - rf          # synth TR excess (carry - D*dy), dur 7
sig = (y.diff(252) < 0).astype(float)       # 252d spread-tightening momentum
pos = sig.shift(1).fillna(0)                # T+1
v = ex.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
size = (pos*(0.10/v)).clip(0, 1.0).fillna(0)
c = size*ex - size.diff().abs().fillna(0)*COST
net = (rf + c)
v2 = net.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
net = (net*(0.10/v2).clip(0, 2.0)).dropna()
out = net[net.index >= "1990-01-03"]
out.name = "ret"
out.to_frame().to_csv("/Users/daxu/software/world-trader/campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv", index_label="date")
print("saved", len(out), "obs; SR(90+)=", round(out.mean()/out.std()*252**0.5, 3))
