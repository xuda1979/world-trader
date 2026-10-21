import os, sys, hashlib
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign/scripts")
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r6")
sys.path.insert(0, ROOT + "/campaign/agents/A3_xs_quality")
import rawew13v2_build as B
import campaign.harness.data as _D
def _panel_skip_manifest(extended=False):
    d = _D.EXT if extended else _D.PANEL
    out = dict()
    for f in os.listdir(d):
        if f.endswith(".csv") and f != "manifest.csv":
            df = pd.read_csv(os.path.join(d, f), parse_dates=["date"], index_col="date")
            out[f[:-4]] = df
    return out
_D.panel = _panel_skip_manifest
from r7_idea5_breadth import panel, RET_PAN
from r6lib import wback_rb
from r7lib import wed_rbd
from campaign.agents.B2_highfreq.gates import vol_target

OUT = ROOT + "/campaign/agents/chief/coord/ITER49_TSMOM_VT"
LOG = []
def log(s=""):
    LOG.append(str(s)); print(s)
def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

TSM = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv"
MAW_FROZEN = 189
ARMS = (0.10, 0.06, 0.09, 0.12, 0.15)

log(9 * chr(61) + " ITER49 TSMOM-VT PRE-SEAL PROBE (A1 + clip regime) " + 9 * chr(61))
log("committed sleeve sha16 = " + sha16(TSM))

def tsmom_build(vt):
    R5 = RET_PAN.drop(columns=["CASH"])
    s = np.sign(panel - panel.rolling(MAW_FROZEN, min_periods=MAW_FROZEN // 2).mean()).fillna(0) * 0.2
    net, _ = wback_rb(s, R5, wed_rbd(panel.index))
    rfull, sc = vol_target(net.dropna(), vt_ann=vt)
    return rfull.dropna(), sc, net.dropna()

scaled, scale, pre = tsmom_build(0.10)
saved = pd.read_csv(TSM, index_col=0, parse_dates=True).iloc[:, 0]
saved = pd.to_numeric(saved, errors="coerce")
j = pd.concat([scaled.rename("g"), saved.rename("c")], axis=1, join="inner").dropna()
dev = float((j.g - j.c).abs().max())
ok = (len(j) == int(saved.notna().sum())) and dev < 1e-12
log("A1 regen-vt010 vs committed: ok=%s maxdev=%.6e inner=%d committed_nonnan=%d"
    % (ok, dev, len(j), int(saved.notna().sum())))
log("regen span %s .. %s ; committed span %s .. %s"
    % (scaled.index[0].date(), scaled.index[-1].date(), saved.index[0].date(), saved.index[-1].date()))

pre_frame = pre[pre.index >= "2008-03-31"]
rcum = pre_frame.expanding(60).std() * np.sqrt(252)
rcum_on = rcum.dropna()
rmin = float(rcum_on.min())
rmax = float(rcum_on.max())
log("PRE-SCALE rcum on-frame (n=%d): min=%.4f max=%.4f pct ann" % (len(rcum_on), rmin * 100, rmax * 100))
warm = int((pre.index < "2008-03-31").sum())
log("pre-frame rows (unreachable by the fit): %d ; regen head %s" % (warm, str(scaled.dropna().index[0].date())))
for vt in ARMS:
    bound = vt / 3.0
    nbind = int((rcum_on < bound).sum())
    log("arm vt=%.2f: clip binds iff rcum < %.4f ; on-frame rows under bound = %d -> %s"
        % (vt, bound, nbind, "CLIP REGIME" if nbind > 0 else "PURE-SCALE on-frame"))
log("PROBE VERDICT: " + ("CLIP REGIME present at some arm - genuine shape axis, adoption EV honest"
    if any(float(rcum_on.min()) < vt / 3.0 for vt in ARMS if vt != 0.10) else
    "PURE-SCALE at every arm - #48 shrink-distortion law applies, anchor certified, EV LOW"))
with open(OUT + "/anchor_a1_probe.log", "w") as fh:
    fh.write(chr(10).join(LOG) + chr(10))
print("LOG WRITTEN: " + OUT + "/anchor_a1_probe.log")
