# probe_iter51_a1.py - PRE-SEAL probes for ITER51 C5NG-VT staleness re-adjudication.
# Runs A1 anchors (regen vs committed vintages) + clip-regime probe at every arm vt.
# Property probes only - NO pool fit, NO arm IS-SR, NO candidate computation (precommit law).
import os, sys, hashlib
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign/scripts")
sys.path.insert(0, ROOT)
import rawew13v2_build as B
from campaign.agents.B2_highfreq.gates import vol_target

OUT = ROOT + "/campaign/agents/chief/coord/ITER51_C5NG_VT_READJ"
CNG_CSV = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv"
SUM_CSV = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv"
DHH = ROOT + "/tools/quant/data/newdata/DHHNGSP.csv"
COST_SLEEVE = 6e-4
MONTHS = list(range(4, 11))
ARMS = (0.10, 0.06, 0.09, 0.12, 0.15)

def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

def build_c5ng(summer, vt):
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
    thr = lr.rolling(90).std().shift(1) * 2.5
    pos = pos.mask(lr.abs() > thr, 0.0)
    gr = pos * lr.shift(-1)
    turn = pos.diff().abs()
    turn.iloc[0] = abs(pos.iloc[0])
    net = (gr - turn * COST_SLEEVE).dropna()
    scaled, _ = vol_target(net, vt_ann=vt)
    return scaled.dropna()

def recon(regen, path):
    c = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
    c = pd.to_numeric(c, errors="coerce")
    j = pd.concat([c.dropna().rename("c"), regen.rename("g")], axis=1, join="inner").dropna()
    dev = float((j.c - j.g).abs().max())
    ok = (len(j) == int(c.notna().sum())) and dev < 1e-12
    return ok, dev, len(j), int(c.notna().sum())

lines = []
def log(s=""):
    lines.append(str(s)); print(s)

log("ITER51 A1/clip probe (pre-seal, property probes only) " + str(pd.Timestamp("now")))
log("committed vintages: C5ng " + sha16(CNG_CSV) + " / C5ngsum " + sha16(SUM_CSV))
log("live champion pair: " + sha16(ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv") + " / " + sha16(ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv"))
sC = build_c5ng(False, 0.10)
sS = build_c5ng(True, 0.10)
okC, devC, niC, ncC = recon(sC, CNG_CSV)
okS, devS, niS, ncS = recon(sS, SUM_CSV)
log("A1a regen-vt010-vs-committed C5ng ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (okC, devC, niC, ncC))
log("A1b regen-vt010-vs-committed C5ngsum ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (okS, devS, niS, ncS))
assert okC and okS, "A1 failed - probe fail-closed"

# clip regime: scale=(vt/rcum).clip(upper=3.0), rcum=expanding(60) ann vol of PRE-SCALE stream.
# rcum is a property of the pre-scale net stream (vt-invariant); compute once per variant.
def rcum_of(summer):
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
    thr = lr.rolling(90).std().shift(1) * 2.5
    pos = pos.mask(lr.abs() > thr, 0.0)
    gr = pos * lr.shift(-1)
    turn = pos.diff().abs()
    turn.iloc[0] = abs(pos.iloc[0])
    net = (gr - turn * COST_SLEEVE).dropna()
    rc = net.expanding(60).std() * np.sqrt(252) * 100
    return rc[rc.index >= "2008-03-31"]

for nm, rc in (("C5ng", rcum_of(False)), ("C5ngsum", rcum_of(True))):
    rmin = float(rc.min())
    for vt in ARMS:
        frac = float((vt / rc > 3.0).mean())
        log("clip %s vt=%.2f: rcum_min=%.4f pct ann, bound_frac_onframe=%.6f" % (nm, vt, rmin, frac))
open(OUT + "/anchor_a1_probe.log", "w").write("\n".join(lines) + "\n")
print("probe log written:", OUT + "/anchor_a1_probe.log")
