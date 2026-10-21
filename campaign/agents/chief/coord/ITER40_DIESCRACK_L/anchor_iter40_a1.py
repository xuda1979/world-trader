import os, hashlib
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
OUT = ROOT + "/campaign/agents/chief/coord/ITER40_DIESCRACK_L"
os.makedirs(OUT, exist_ok=True)
FRED = ROOT + "/tools/quant/hedge_fund_strats/data_fred"
NEW = ROOT + "/tools/quant/data/newdata"
EIA = ROOT + "/tools/quant/data/eia_weekly"
DC_REL = ROOT + "/campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv"
CHAMP = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
GRID = [15, 27, 40, 53]
GATE = 2.0
LOG = []
def log(s=""):
    LOG.append(str(s)); print(s)
def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
def dload(p):
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    return pd.to_numeric(df.iloc[:, 0], errors="coerce").dropna()
def fred(name, src):
    s = dload(src + "/" + name + ".csv")
    return s[~s.index.duplicated(keep="last")].sort_index()
def diescrack_build(lb, gate):
    dj = fred("DJFUELUSGULF", NEW)
    wt = fred("wti_full", FRED)
    E_WT = dload(EIA + "/wti_spot_daily.csv")
    wt = pd.concat([wt, E_WT[E_WT.index > wt.index[-1]]])
    sp = (np.log(dj * 42.0) - np.log(wt)).dropna()
    sp = sp[sp.index >= "2008-01-01"]
    m = sp.rolling(lb, min_periods=lb).mean()
    sd = sp.rolling(lb, min_periods=lb).std().replace(0, np.nan)
    z = (sp - m) / sd
    pos = pd.Series(0.0, index=sp.index)
    pos[z < -gate] = 1.0
    pos[z > gate] = -1.0
    ret = sp.diff().shift(-1)
    gr = (pos * ret).dropna()
    tup = pos.diff().abs().reindex(gr.index).fillna(0.0)
    base = gr - tup * 6.4 / 1e4
    pi = pos.reindex(base.index).fillna(0.0)
    bmask = ((pi != 0) | (pi.shift(1).fillna(0) != 0)).astype(float)
    sc = (0.08 / (base.expanding(60).std() * np.sqrt(252))).clip(upper=3.0)
    return ((base * sc).fillna(0.0) - bmask * 0.005 / 252).dropna()

log("ITER40 A1 anchor pre-seal diagnostic (2026-09-19 session 20). No candidate computation here.")
log("saved diescrack_L40Z20_net.csv sha16: " + sha16(DC_REL))
saved = dload(DC_REL)
log("saved span: %s .. %s  n=%d" % (str(saved.index[0].date()), str(saved.index[-1].date()), len(saved)))
gen0 = diescrack_build(40, GATE)
j0 = pd.concat([gen0.rename("gen"), saved.rename("saved")], axis=1, join="inner").dropna()
a1dev = float((j0["gen"] - j0["saved"]).abs().max())
log("A1 regen L=40 Z=2.0 vs saved: maxdev=%.6e (inner n=%d)" % (a1dev, len(j0)))
log("A1 inner span: %s .. %s" % (str(j0.index[0].date()), str(j0.index[-1].date())))
frame = pd.read_csv(CHAMP, index_col=0, parse_dates=True).index
frame = frame[frame >= "2008-03-31"]
saved_inframe = int(saved.reindex(frame).notna().sum())
log("frame rows=%d  saved in-frame notna=%d" % (len(frame), saved_inframe))
sp_start = gen0.index[0]
log("regen stream start (all cells): %s" % str(sp_start.date()))
for L in GRID:
    g = diescrack_build(L, GATE)
    same_cal = g.index.equals(gen0.index)
    fv = g.index[L - 1]
    infc = int(g.reindex(frame).notna().sum())
    log("L=%d: calendar-identical=%s  first z-valid=%s (<= frame start %s: %s)  in-frame notna=%d" % (
        L, same_cal, str(fv.date()), "2008-03-31", str(fv <= pd.Timestamp("2008-03-31")), infc))
    assert same_cal, "calendar moved with L - generator not L-invariant in index"
    assert fv <= pd.Timestamp("2008-03-31"), "L=%d degenerate warmup cell - grid illegal" % L
    assert infc == saved_inframe, "in-frame notna count changed - coverage law violated"
log("ALL L-grid coverage diagnostics PASS - grid admissible under the coverage law.")
with open(OUT + "/anchor_iter40.log", "w") as fh:
    fh.write(chr(10).join(LOG) + chr(10))
print("LOG WRITTEN: " + OUT + "/anchor_iter40.log")
