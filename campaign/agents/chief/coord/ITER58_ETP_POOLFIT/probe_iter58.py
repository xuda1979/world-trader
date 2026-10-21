import os, sys, hashlib, io
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
OUT = ROOT + "/campaign/agents/chief/coord/ITER58_ETP_POOLFIT"
LOG = []
def log(s=""):
    LOG.append(str(s)); print(s)

MAW_FROZEN = 189
CANDS = ["DBC","GSG","DBA","DBE","DBP","UNG","USO","UUP","BNO","CORN","SOYB","WEAT","USCI"]

sys.path.insert(0, ROOT + "/campaign/scripts")
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r6")
import rawew13v2_build as B

sys.path.insert(0, ROOT + "/campaign/harness")
import data as DH
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
log("D17 pre-patch applied to BOTH identities before the r6lib-resolving import")

sys.path.insert(0, ROOT + "/campaign/agents/A3_xs_quality")
from r7_idea5_breadth import panel, RET_PAN
from r6lib import wback_rb
from r7lib import wed_rbd
from campaign.agents.B2_highfreq.gates import vol_target

def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

def sha16_bytes(b):
    return hashlib.sha256(b).hexdigest()[:16]

def sr(x): return float(x.mean() / x.std(ddof=1) * np.sqrt(252))

TSM_CSV = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189__vt015.csv"

def build_tsmom(vt):
    R5 = RET_PAN.drop(columns=["CASH"])
    s = np.sign(panel - panel.rolling(MAW_FROZEN, min_periods=MAW_FROZEN // 2).mean()).fillna(0) * 0.2
    net, _ = wback_rb(s, R5, wed_rbd(panel.index))
    rfull, _ = vol_target(net.dropna(), vt_ann=vt)
    return rfull.dropna()

def recon(regen, path):
    c = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
    c = pd.to_numeric(c, errors="coerce")
    j = pd.concat([c.dropna().rename("c"), regen.rename("g")], axis=1, join="inner").dropna()
    dev = float((j.c - j.g).abs().max())
    ok = (len(j) == int(c.notna().sum())) and dev < 1e-12
    return ok, dev, len(j), int(c.notna().sum())

def load_etp(sym):
    df = pd.read_csv(ROOT + "/tools/quant/data/more_etf/" + sym + ".csv", index_col=0, parse_dates=True)
    s = df["close"].astype(float)
    return s[~s.index.duplicated(keep="last")].sort_index()

def build_tsmom_etp(px, vt):
    r = px.pct_change().to_frame("px")
    s = np.sign(px - px.rolling(MAW_FROZEN, min_periods=MAW_FROZEN // 2).mean()).fillna(0).to_frame("px")
    net, _ = wback_rb(s, r, wed_rbd(px.index))
    rfull, _ = vol_target(net.dropna(), vt_ann=vt)
    return rfull.dropna()

log("ITER58 PROBE (pre-seal, disclosed inside FINDINGS_PRECOMMIT): more_etf futures-ETP universe, tsmom-189 vt015 single-stream transplant.")
sT = build_tsmom(0.15)
okT, devT, niT, ncT = recon(sT, TSM_CSV)
log("A1a canonical vt015 regen ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (okT, devT, niT, ncT))
assert okT, "A1a recipe fidelity failed - fail closed"

rows = []
for sym in CANDS:
    px = load_etp(sym)
    src_sha = sha16(ROOT + "/tools/quant/data/more_etf/" + sym + ".csv")
    assert px.notna().all(), "NaN in " + sym
    gaps = px.index.to_series().diff().dt.days.dropna()
    assert int(gaps.max()) <= 5, "calendar gap > 5d in " + sym
    same = px.diff() == 0
    stale = int((same.groupby((~same).cumsum()).sum()).max())
    assert stale <= 5, "stale close run > 5 (vendor freeze?) in " + sym
    rr = px.pct_change().dropna()
    mx = float(rr.abs().max())
    assert mx < 0.35, "impossible move (split artifact?) in " + sym + ": %.4f" % mx
    is_rows = int(((px.index >= "2008-03-31") & (px.index < B.IS_END)).sum())
    assert is_rows > 500, "census criterion fail (IS rows) in " + sym
    live = str(px.index[-1].date()) >= "2024-01-01"
    assert live, "not live >=2024 in " + sym
    st = build_tsmom_etp(px, 0.15)
    buf = io.StringIO()
    pd.DataFrame(dict(ret=st.values), index=st.index).to_csv(buf)
    st_sha = sha16_bytes(buf.getvalue().encode())
    rows.append((sym, str(px.index[0].date()), str(px.index[-1].date()), len(px), is_rows, stale, mx, src_sha, st_sha))
    log("%-5s start=%s end=%s n=%d ISrows=%d stale=%d maxr=%.4f src_sha16=%s stream_sha16=%s" % rows[-1])

log("PROBE COMPLETE - 13/13 candidates pass hygiene + census screen; stream shas recorded for the seal.")
with open(OUT + "/probe_iter58.log", "w") as fh:
    fh.write(chr(10).join(LOG) + chr(10))
print("PROBE LOG WRITTEN")
