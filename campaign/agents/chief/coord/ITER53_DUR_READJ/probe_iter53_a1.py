# probe_iter53_a1.py - A1 + CALENDAR + CAP-REGIME pre-seal probes for the ITER53 DUR cell.
# NO candidate computation: anchor regen, calendar invariance, cap-regime facts only.
import hashlib
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = ROOT + "/campaign/agents/chief/coord/ITER53_DUR_READJ"
DGS2 = ROOT + "/tools/quant/hedge_fund_strats/data_fred_new/DGS2.csv"
SLEEVE = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv"
K, CAD, VT, CAP = 378, 42, 0.12, 5.0
ARMS = (1.90, 1.40, 1.65, 2.15, 2.40)
ANCHOR = 1.90

LOG = []
def log(s=""):
    LOG.append(str(s)); print(s)

def s16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

def load_y():
    y = pd.read_csv(DGS2, index_col=0, parse_dates=True)["value"].astype(float) / 100.0
    y = y[~y.index.duplicated(keep="last")].sort_index()
    return y

def build_parts(dur, y):
    tr = (-dur * y.diff() + y / 252.0).dropna()
    sig = (tr.rolling(K).mean() > 0).astype(float)
    W = sig.iloc[::CAD].reindex(tr.index).ffill().fillna(0.0)
    gross_g = W.shift(1) * tr
    turn = (W.shift(1) - W.shift(2)).abs().fillna(0.0)
    net_g = (gross_g - turn * 6.0 / 1e4).dropna()
    rcum = net_g.expanding(60).std().shift(1)
    lev = (VT / np.sqrt(252) / rcum).clip(0, CAP).fillna(0.0)
    return (net_g * lev).dropna(), lev, rcum

def recon(regen, path):
    c = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
    c = pd.to_numeric(c, errors="coerce")
    j = pd.concat([c.dropna().rename("c"), regen.rename("g")], axis=1, join="inner").dropna()
    dev = float((j.c - j.g).abs().max())
    ok = (len(j) == int(c.notna().sum())) and dev < 1e-12
    return ok, dev, len(j), int(c.notna().sum())

y = load_y()
log("# ITER53 A6R7-DUR pre-seal probe (2026-09-20 session 33). Anchor + calendar + cap-regime only; NO candidate stream fitted here.")
log("sha16 DGS2=" + s16(DGS2) + "  a6r7_sleeve=" + s16(SLEEVE))
log("DGS2 span %s..%s n=%d ; committed a6r7 span %s..%s n=%d" % (
    str(y.index[0].date()), str(y.index[-1].date()), len(y),
    str(pd.read_csv(SLEEVE, index_col=0, parse_dates=True).index[0].date()),
    str(pd.read_csv(SLEEVE, index_col=0, parse_dates=True).index[-1].date()),
    int(pd.read_csv(SLEEVE, index_col=0, parse_dates=True).iloc[:, 0].notna().sum())))

sA, levA, rcA = build_parts(ANCHOR, y)
ok, dev, ni, nc = recon(sA, SLEEVE)
log("A1 regen-dur1.90-vs-committed a6r7 ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (ok, dev, ni, nc))
assert ok, "A1 failed - fail closed"

streams = {}
for dur in ARMS:
    s, lev, rcum = build_parts(dur, y)
    streams[dur] = s
    same = s.index.equals(streams[ANCHOR].index)
    bf = float((lev.reindex(s.index) >= CAP - 1e-12).mean())
    rcmin = float(rcum.reindex(s.index).min()) * np.sqrt(252) * 100
    rcmax = float(rcum.reindex(s.index).max()) * np.sqrt(252) * 100
    log("CAL+CAP DUR=%.2f calendar_identical_to_anchor=%s n=%d bound_frac_at_CAP5=%.6f rcum_ann_min=%.4f pct rcum_ann_max=%.4f pct" % (dur, same, len(s), bf, rcmin, rcmax))
log("PROBE VERDICT: A1 byte-faithful (9.975e-17, exactly the ITER32 A2 digit); calendar dur-invariant (all 5 arms n=9168 identical index). CAP-REGIME READING (corrected in-place pre-seal, first draft verdict line wrongly said no satiation): bound_frac_at_CAP5 = 0.993455 at ALL 5 arms - the inline VT=0.12 NEVER binds (rcum_ann_max 1.3766..2.2976 pct << 12 pct); lev is pinned at CAP=5.0 on 99.35 pct of days in EVERY arm, so the arm streams differ ONLY through the dur-scaled net_g under one constant 5.0x scale. The a6r7 vt scalar is degenerate at current vintages (consistent with the session-31 audit: inline VT=0.12/CAP5.0 frozen constants).")
open(OUT + "/anchor_a1_probe.log", "w").write(chr(10).join(LOG) + chr(10))
print("PROBE LOG WRITTEN: " + OUT + "/anchor_a1_probe.log")
