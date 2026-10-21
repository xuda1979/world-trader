#!/usr/bin/env python3
import hashlib, importlib.util, json, os
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = ROOT + "/campaign/agents/chief/coord/ITER30_RECIPE_SWEEP"
CHAMP = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
WF = ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv"
SLEEVE = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv"

def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

shas = dict(champion=sha_file(CHAMP), weights=sha_file(WF), a6r7_sleeve=sha_file(SLEEVE))
print("A1 shas:", json.dumps(shas, indent=1))

spec = importlib.util.spec_from_file_location("d24", ROOT + "/campaign/agents/chief/coord/ITER24_DATA_AXIS/driver_iter24.py")
d24 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d24)

DUR, K, CAD, VT, CAP = 1.9, 378, 42, 0.12, 5.0
y = pd.read_csv(ROOT + "/tools/quant/hedge_fund_strats/data_fred_new/DGS2.csv",
                index_col=0, parse_dates=True)["value"].astype(float) / 100.0
y = y[~y.index.duplicated(keep="last")].sort_index()
tr = (-DUR * y.diff() + y / 252.0).dropna()
sig = (tr.rolling(K).mean() > 0).astype(float)
W = sig.iloc[::CAD].reindex(tr.index).ffill().fillna(0.0)
gross_g = W.shift(1) * tr
turn = (W.shift(1) - W.shift(2)).abs().fillna(0.0)
net_g = (gross_g - turn * 6.0 / 1e4).dropna()
lev = (VT / np.sqrt(252) / net_g.expanding(60).std().shift(1)).clip(0, CAP).fillna(0.0)
a6 = (net_g * lev).dropna()
saved = d24.load_ret(SLEEVE)
j = pd.concat([a6.rename("gen"), saved.rename("saved")], axis=1, join="inner").dropna()
gen_dev = float((j["gen"] - j["saved"]).abs().max())
cov = dict(gen_n=int(len(a6)), saved_n=int(len(saved)), inner_n=int(len(j)),
           gen_first=str(a6.index[0].date()), saved_first=str(saved.index[0].date()),
           gen_last=str(a6.index[-1].date()), saved_last=str(saved.index[-1].date()))
print("A2 generator max dev vs saved: %.3e" % gen_dev, json.dumps(cov))
if gen_dev >= 1e-12:
    raise SystemExit("A2 FAILED - legacy generator is not the saved stream source; STOP")

frames = dict((n, d24.load_ret(p).dropna()) for n, p in d24.INCUMBENT.items())
idx12 = sorted(set().union(*[set(frames[n].index) for n in d24.INCUMBENT]))
idx12 = [t for t in idx12 if t >= d24.START]
df12 = pd.DataFrame(frames)[list(d24.INCUMBENT)].reindex(idx12)
net12, relw12, gross12, to12 = d24.build_from_frame(df12)
champ_r = d24.load_ret(CHAMP)
wcmt = pd.read_csv(WF, index_col=0)["relw"]
if len(net12) != len(champ_r):
    raise SystemExit("A3 length %d != champion %d - union mismatch" % (len(net12), len(champ_r)))
jj = pd.concat([champ_r.rename("old"), net12.rename("new")], axis=1, join="inner").dropna()
byte_dev = float((jj["old"] - jj["new"]).abs().max())
w_dev = float((wcmt.reindex(relw12.index) - relw12).abs().max())
isr12 = df12[df12.index < d24.IS_END]
have12 = [n for n in d24.INCUMBENT if isr12[n].notna().sum() > 0]
pre = net12[net12.index < d24.IS_END]
is_sr = float(pre.mean() / pre.std(ddof=1) * np.sqrt(252))
fs_sr = float(net12.mean() / net12.std(ddof=1) * np.sqrt(252))
print("A3 byte dev %.3e  weights dev %.3e  n %d" % (byte_dev, w_dev, len(net12)))
print("A3 IS-SR %.6f  FS-SR %.6f  k_covered %d" % (is_sr, fs_sr, len(have12)))
if byte_dev >= 1e-12 or w_dev >= 1e-9:
    raise SystemExit("A3 FAILED - mirror not byte-identical; STOP")
res = dict(shas=shas, gen_max_dev=gen_dev, gen_coverage=cov, pool_byte_dev=byte_dev,
           weights_dev=w_dev, is_sr=is_sr, fs_sr=fs_sr, k_covered=len(have12),
           n_rows=int(len(net12)), relw12=dict((n, float(v)) for n, v in relw12.items()))
with open(OUT + "/anchors.json", "w") as fh:
    json.dump(res, fh, indent=2, default=str)
print("ANCHORS OK - all three exact")
