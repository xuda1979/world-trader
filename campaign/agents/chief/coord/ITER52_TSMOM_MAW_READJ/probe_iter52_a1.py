# probe_iter52_a1.py - PRE-SEAL probes for ITER52 TSMOM-MAW staleness re-adjudication.
# Runs A1 anchor (regen MAW=189 at vt0.15 vs committed vt015 vintage) + per-arm calendar
# invariance + clip-regime probe at every grid MAW. Property probes only - NO pool fit,
# NO arm IS-SR, NO candidate computation (precommit law).
import os, sys, hashlib
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
OUT = ROOT + "/campaign/agents/chief/coord/ITER52_TSMOM_MAW_READJ"
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, ROOT + "/campaign/scripts")
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/campaign/harness")
import data as DH
# D17 Amendment-1 DUAL patch: manifest.csv sits in twelve_big at probe time and harness
# data.panel() has no skip logic; r6lib resolves the FULL-PATH identity, so BOTH module
# objects must be patched BEFORE the r7/r6lib import chain (driver_iter49 form).
def _panel_d17(extended=False):
    d = DH.EXT if extended else DH.PANEL
    out = dict()
    for f in os.listdir(d):
        if f.endswith(".csv") and f != "manifest.csv":
            out[f[:-4]] = pd.read_csv(os.path.join(d, f), parse_dates=["date"], index_col="date")
    return out
DH.panel = _panel_d17
import campaign.harness.data as DHF
def _panel_d17_full(extended=False):
    d = DHF.EXT if extended else DHF.PANEL
    out = dict()
    for f in os.listdir(d):
        if f.endswith(".csv") and f != "manifest.csv":
            out[f[:-4]] = pd.read_csv(os.path.join(d, f), parse_dates=["date"], index_col="date")
    return out
DHF.panel = _panel_d17_full
sys.path.insert(0, ROOT + "/campaign/agents/A3_xs_quality")
from r7_idea5_breadth import panel, RET_PAN
from r6lib import wback_rb
from r7lib import wed_rbd
from campaign.agents.B2_highfreq.gates import vol_target

TSM_CSV = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189__vt015.csv"
VT_FROZEN = 0.15
ANCHOR_MAW = 189
ARMS = (189, 126, 157, 220, 252)

def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

def build_prescale(maw):
    R5 = RET_PAN.drop(columns=["CASH"])
    s = np.sign(panel - panel.rolling(maw, min_periods=maw // 2).mean()).fillna(0) * 0.2
    net, _ = wback_rb(s, R5, wed_rbd(panel.index))
    return net.dropna()

def build_tsmom(maw):
    net = build_prescale(maw)
    rfull, _ = vol_target(net, vt_ann=VT_FROZEN)
    return rfull.dropna()

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

log("ITER52 A1/clip probe (pre-seal, property probes only) " + str(pd.Timestamp("now")))
log("committed vintage: QAxasts vt015 " + sha16(TSM_CSV))
log("live champion pair: " + sha16(ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv") + " / " + sha16(ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv"))
sA = build_tsmom(ANCHOR_MAW)
okT, devT, niT, ncT = recon(sA, TSM_CSV)
log("A1 regen-maw189-vt015-vs-committed QAxasts ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (okT, devT, niT, ncT))
assert okT, "A1 failed - probe fail-closed"
idx_anchor = sA.index
for maw in ARMS:
    net = build_prescale(maw)
    rfull, _ = vol_target(net, vt_ann=VT_FROZEN)
    s1 = rfull.dropna()
    cal_ok = bool(s1.index.equals(idx_anchor))
    log("cal MAW=%d: index_equals_anchor=%s n=%d" % (maw, cal_ok, len(s1)))
    assert cal_ok, "calendar moved with MAW - coverage law violated (probe fail-closed)"
    rc = net.expanding(60).std() * np.sqrt(252) * 100
    rc = rc[rc.index >= "2008-03-31"]
    rmin = float(rc.min())
    frac = float((VT_FROZEN / rc > 3.0).mean())
    log("clip MAW=%d: rcum_min=%.4f pct ann, bound_frac_onframe=%.6f" % (maw, rmin, frac))
open(OUT + "/anchor_a1_probe.log", "w").write(chr(10).join(lines) + chr(10))
print("probe log written:", OUT + "/anchor_a1_probe.log")
