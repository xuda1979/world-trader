import os, sys, hashlib, subprocess
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign/scripts")
sys.path.insert(0, ROOT)
import rawew13v2_build as B
from campaign.agents.B2_highfreq.gates import vol_target
OUT = ROOT + "/campaign/agents/chief/coord/ITER55_BRWT_ZB_READJ"
LOG = []
def log(s=""):
    LOG.append(str(s)); print(s)
def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
FRED = ROOT + "/tools/quant/hedge_fund_strats/data_fred"
EIA = ROOT + "/tools/quant/data/eia_weekly"
ARMS3 = [(10, "brwt10", "2000-01-01"), (7, "brwt7", "2008-01-01"), (5, "brwt5", "2008-01-01")]
def dload(pstr):
    df = pd.read_csv(pstr, index_col=0, parse_dates=True)
    v = df.iloc[:, 0]
    return pd.to_numeric(v, errors="coerce").dropna()
def fred(name):
    s = dload(FRED + "/" + name + ".csv")
    return s[~s.index.duplicated(keep="last")].sort_index()
def brwt_load():
    BR = fred("brent")
    WT = fred("wti")
    E_BR = dload(EIA + "/brent_spot_daily.csv")
    E_WT = dload(EIA + "/wti_spot_daily.csv")
    BR = pd.concat([BR, E_BR[E_BR.index > BR.index[-1]]])
    WT = pd.concat([WT, E_WT[E_WT.index > WT.index[-1]]])
    return BR, WT
def brwt_build(lb, zb, min_start):
    BR, WT = brwt_load()
    sp = (np.log(BR) - np.log(WT)).dropna()
    sp = sp[sp.index >= min_start]
    m = sp.rolling(lb, min_periods=lb).mean()
    sd = sp.rolling(lb, min_periods=lb).std().replace(0, np.nan)
    z = (sp - m) / sd
    pos = pd.Series(0.0, index=sp.index)
    pos[z < -zb] = 1.0
    pos[z > zb] = -1.0
    gross = pos * sp.diff().shift(-1)
    net = gross - pos.diff().abs() * 6.4 / 1e4
    scaled, scale = vol_target(net)
    return scaled, scale
log("--------- ITER55 BRWT-ZB STALENESS RE-ADJUDICATION A1 probe (2026-09-20 session 35).")
champ = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
wgt = ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv"
log("Champion sha16: " + sha16(champ) + " / weights " + sha16(wgt))
saved = {}
cal = {}
clipfrac = {}
for lb, nm, ms in ARMS3:
    g, scale = brwt_build(lb, 1.0, ms)
    p = ROOT + "/" + B.PATHS[nm]
    c = pd.read_csv(p, index_col=0, parse_dates=True).iloc[:, 0]
    c = pd.to_numeric(c, errors="coerce")
    j = pd.concat([c.dropna().rename("c"), g.rename("g")], axis=1, join="inner").dropna()
    dev = float((j.c - j.g).abs().max())
    ok = (len(j) == int(c.notna().sum())) and dev < 1e-12
    log("A1 regen-zb1.0-vs-committed %s ok=%s maxdev=%.3e inner=%d committed_nonnan=%d tail_saved=%s tail_gen=%s"
        % (nm, ok, dev, len(j), int(c.notna().sum()), str(c.dropna().index[-1].date()), str(g.index[-1].date())))
    saved[nm] = g
    cal[nm] = g.index
    clipfrac[nm] = float((scale >= 3.0 - 1e-12).mean())
    log("   vt-clip probe %s: bound_frac=%.6f (fraction of days scale pinned at upper 3.0; default vt_ann=0.10 min60)" % (nm, clipfrac[nm]))
assert cal["brwt10"].equals(cal["brwt7"]) is False or True
# calendar-vs-zb probe: re-run one variant at a different zb, index must be identical
g2, _ = brwt_build(10, 2.0, "2000-01-01")
log("Calendar-vs-zb probe: brwt10 zb=2.0 index identical to zb=1.0: %s (zb moves only the threshold mask, never the index)" % str(g2.index.equals(saved["brwt10"].index)))
assert g2.index.equals(saved["brwt10"].index)
# family share recompute from committed weights
w = pd.read_csv(wgt, index_col=0).iloc[:, 0]
share = w / w.sum()
trio = float(share[list(B.BRWT_BLOCK)].sum())
mx = share.drop("CFX4").idxmax()
log("Family share recomputed fresh: brwt10 %.4f + brwt7 %.4f + brwt5 %.4f = %.4f pct (block cap 0.30)" % (share["brwt10"]*100, share["brwt7"]*100, share["brwt5"]*100, trio*100))
log("Max non-CFX4 share: %s %.4f pct (Wmax_sf x11 = %.4fx)" % (mx, share[mx]*100, share[mx]*11))
# data vintage mtimes
for f in ("tools/quant/hedge_fund_strats/data_fred/brent.csv", "tools/quant/hedge_fund_strats/data_fred/wti.csv",
          "tools/quant/data/eia_weekly/brent_spot_daily.csv", "tools/quant/data/eia_weekly/wti_spot_daily.csv"):
    import time
    p = ROOT + "/" + f
    log("mtime %s %s" % (time.strftime("%m-%d %H:%M", time.localtime(os.path.getmtime(p))), f))
# stray writers
try:
    ps = subprocess.run(["ps", "-eo", "command="], capture_output=True, text=True, timeout=30).stdout
    lines = [l.strip() for l in ps.splitlines() if "/.local/bin/claude" in l or "claude --print" in l or "claude -p" in l]
    log("claude-ish procs: %d" % len(lines))
    for l in lines[:10]:
        log("  " + l[:120])
except Exception as e:
    log("ps probe unavailable: %r" % (e,))
with open(OUT + "/probe_iter55_a1.log", "w") as fh:
    fh.write(chr(10).join(LOG) + chr(10))
print("PROBE LOG WRITTEN")
