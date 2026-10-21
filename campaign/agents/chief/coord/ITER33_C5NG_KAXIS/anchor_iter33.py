
import sys
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)
from campaign.agents.B2_highfreq.gates import vol_target
D = ROOT + "/tools/quant/data/newdata/DHHNGSP.csv"
COST = 6e-4
MONTHS = list(range(4, 11))
def run(summer, k):
    s = pd.read_csv(D, index_col=0, parse_dates=True).iloc[:, 0]
    s = pd.to_numeric(s, errors="coerce")
    s = s[s > 0].dropna().sort_index()
    lr = np.log(s).diff()
    idx = lr.index
    pos = pd.Series(0.0, index=idx)
    pos[idx.dayofweek == 2] = -1.0
    pos[idx.dayofweek == 3] = -1.0
    pos[idx.dayofweek == 4] = 1.0
    if summer:
        pos[~idx.month.isin(MONTHS)] = 0.0
    thr = lr.rolling(90).std().shift(1) * k
    pos = pos.mask(lr.abs() > thr, 0.0)
    gr = pos * lr.shift(-1)
    turn = pos.diff().abs()
    turn.iloc[0] = abs(pos.iloc[0])
    net = (gr - turn * COST).dropna()
    scaled, _ = vol_target(net)
    return scaled.dropna()
SL = ROOT + "/campaign/agents/E1_20yspan/sleeves/"
ok = True
for summer, name in ((False, "E1_C5ng_weekday_prem.csv"), (True, "E1_C5ng_summer_weekday.csv")):
    saved = pd.read_csv(SL + name, index_col=0, parse_dates=True).iloc[:, 0]
    gen = run(summer, 2.5)
    j = pd.concat([gen.rename("gen"), saved.rename("saved")], axis=1, join="inner").dropna()
    dev = float((j["gen"] - j["saved"]).abs().max())
    print(name, "inner_n=%d gen_n=%d saved_n=%d dev=%.6e" % (len(j), len(gen), len(saved), dev))
    print("  gen_tail=%s saved_tail=%s" % (gen.index.max(), saved.index.max()))
    ok = ok and dev < 1e-12
print("A1 ANCHOR:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 2)
