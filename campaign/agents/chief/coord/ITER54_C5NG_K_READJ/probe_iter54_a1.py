# probe_iter54_a1.py - PRE-SEAL probes for ITER54 C5NG-K staleness re-adjudication.
# Runs A1 anchors (regen k=2.5 vs committed vintages) + arm calendar identity + clip-regime
# probe at every arm k (vt FROZEN 0.10) + fresh family-share recompute from the committed
# weights file. Property probes only - NO pool fit, NO arm IS-SR, NO candidate computation
# (precommit law).
import os, sys, hashlib
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign/scripts")
sys.path.insert(0, ROOT)
import rawew13v2_build as B
from campaign.agents.B2_highfreq.gates import vol_target

OUT = ROOT + "/campaign/agents/chief/coord/ITER54_C5NG_K_READJ"
CNG_CSV = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv"
SUM_CSV = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv"
WGT = ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv"
DHH = ROOT + "/tools/quant/data/newdata/DHHNGSP.csv"
COST_SLEEVE = 6e-4
MONTHS = list(range(4, 11))
ARMS = (2.5, 1.5, 2.0, 3.0, 3.5)
ANCHOR_K = 2.5
VT_FROZEN = 0.10

def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

def build_c5ng(summer, k):
    s = pd.read_csv(DHH, index_col=0, parse_dates=True).iloc[:, 0]
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
    net = (gr - turn * COST_SLEEVE).dropna()
    scaled, _ = vol_target(net, vt_ann=VT_FROZEN)
    return scaled.dropna()

def recon(regen, path):
    c = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
    c = pd.to_numeric(c, errors="coerce")
    j = pd.concat([c.dropna().rename("c"), regen.rename("g")], axis=1, join="inner").dropna()
    dev = float((j.c - j.g).abs().max())
    ok = (len(j) == int(c.notna().sum())) and dev < 1e-12
    return ok, dev, len(j), int(c.notna().sum())

def rcum_of(summer, k):
    s = pd.read_csv(DHH, index_col=0, parse_dates=True).iloc[:, 0]
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
    net = (gr - turn * COST_SLEEVE).dropna()
    rc = net.expanding(60).std() * np.sqrt(252) * 100
    return rc[rc.index >= "2008-03-31"]

lines = []
def log(s=""):
    lines.append(str(s)); print(s)

log("ITER54 A1/calendar/clip probe (pre-seal, property probes only) " + str(pd.Timestamp("now")))
log("committed vintages: C5ng " + sha16(CNG_CSV) + " / C5ngsum " + sha16(SUM_CSV))
log("live champion pair: " + sha16(ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv") + " / " + sha16(WGT))
sC = build_c5ng(False, ANCHOR_K)
sS = build_c5ng(True, ANCHOR_K)
okC, devC, niC, ncC = recon(sC, CNG_CSV)
okS, devS, niS, ncS = recon(sS, SUM_CSV)
log("A1a regen-k250-vs-committed C5ng ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (okC, devC, niC, ncC))
log("A1b regen-k250-vs-committed C5ngsum ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (okS, devS, niS, ncS))
assert okC and okS, "A1 failed - probe fail-closed"
streams = dict()
for k in ARMS:
    streams[k] = (build_c5ng(False, k), build_c5ng(True, k))
a0, b0 = streams[ANCHOR_K]
for k in ARMS:
    a, b = streams[k]
    assert a.index.equals(a0.index), "calendar moved with K - coverage law violated"
    assert b.index.equals(b0.index), "sum calendar moved with K - coverage law violated"
log("calendar identical ALL %d arms: C5ng n=%d  C5ngsum n=%d" % (len(ARMS), len(a0), len(b0)))
# clip regime: scale=(VT/rcum).clip(upper=3.0); rcum is a property of the PRE-scale stream,
# which DEPENDS on k (the calm filter reshapes net) - so rcum is recomputed per arm.
for nm, summer in (("C5ng", False), ("C5ngsum", True)):
    for k in ARMS:
        rc = rcum_of(summer, k)
        rmin = float(rc.min())
        frac = float((VT_FROZEN / rc > 3.0).mean())
        log("clip %s k=%.2f: rcum_min=%.4f pct ann, bound_frac_onframe=%.6f" % (nm, k, rmin, frac))
# fresh family-share recompute from the COMMITTED post-projection weights (no fit re-run).
w = pd.read_csv(WGT, index_col=0).iloc[:, 0]
sh = w / w.sum() * 100.0
fam = float(sh["C5ng"] + sh["C5ngsum"])
log("family share (committed relw, post cap+projection): C5ng %.4f + C5ngsum %.4f = %.4f pct" % (float(sh["C5ng"]), float(sh["C5ngsum"]), fam))
rank = sh.sort_values(ascending=False)
log("per-sleeve shares: " + "; ".join("%s=%.2f" % (n, v) for n, v in rank.items()))
open(OUT + "/anchor_a1_probe.log", "w").write(chr(10).join(lines) + chr(10))
print("probe log written:", OUT + "/anchor_a1_probe.log")
