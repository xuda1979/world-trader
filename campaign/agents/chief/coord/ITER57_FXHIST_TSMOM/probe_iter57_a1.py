import os, sys, hashlib
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign/scripts")
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r6")
import rawew13v2_build as B

OUT = ROOT + "/campaign/agents/chief/coord/ITER57_FXHIST_TSMOM"
LOG = []
def log(s=""):
    LOG.append(str(s)); print(s)

def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

CHAMP = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
WGT   = ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv"
MAW_FROZEN = 189
PAIRS = ["EUR_USD","GBP_USD","AUD_USD","NZD_USD","USD_CAD","USD_CHF","USD_JPY","USD_SEK","USD_NOK"]

log("PROBE A1 for ITER57_FXHIST_TSMOM (pre-seal). Champion pair pre: %s / %s" % (sha16(CHAMP), sha16(WGT)))

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
log("D17 pre-patch applied to BOTH identities (Amendment 1) before the r6lib-resolving import")

sys.path.insert(0, ROOT + "/campaign/agents/A3_xs_quality")
from r7_idea5_breadth import panel, RET_PAN
from r6lib import wback_rb
from r7lib import wed_rbd
from campaign.agents.B2_highfreq.gates import vol_target

def build_tsmom(vt):
    R5 = RET_PAN.drop(columns=["CASH"])
    s = np.sign(panel - panel.rolling(MAW_FROZEN, min_periods=MAW_FROZEN // 2).mean()).fillna(0) * 0.2
    net, _ = wback_rb(s, R5, wed_rbd(panel.index))
    rfull, _ = vol_target(net.dropna(), vt_ann=vt)
    return rfull.dropna()

# ---- A1a: canonical-recipe fidelity (MUST reproduce the committed vt015 sleeve) ----
TSM_CSV = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189__vt015.csv"
sT = build_tsmom(0.15)
c = pd.read_csv(TSM_CSV, index_col=0, parse_dates=True).iloc[:, 0]
c = pd.to_numeric(c, errors="coerce")
j = pd.concat([c.dropna().rename("c"), sT.rename("g")], axis=1, join="inner").dropna()
dev = float((j.c - j.g).abs().max())
okA1 = (len(j) == int(c.notna().sum())) and dev < 1e-12
log("A1a canonical QAxasts vt015 regen vs committed: ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (okA1, dev, len(j), int(c.notna().sum())))
assert okA1, "A1a recipe fidelity FAILED - the transplant code path is not identical"

# ---- A1b: FX panel construction + hygiene gates (fail-closed) ----
def load_pair(name):
    df = pd.read_csv(ROOT + "/tools/quant/data/fx_hist/" + name + ".csv", index_col=0, parse_dates=True)
    s = df["close"].astype(float)
    return s[~s.index.duplicated(keep="last")].sort_index()

foreign_long = dict()
for p in PAIRS:
    s = load_pair(p)
    foreign_long[p] = 1.0 / s if p.startswith("USD_") else s
idx = foreign_long[PAIRS[0]].index
for p in PAIRS:
    assert foreign_long[p].index.equals(idx), "pair calendars differ: " + p
fxp = pd.DataFrame(foreign_long)[PAIRS]
log("A1b fxp panel: %d cols n=%d %s..%s (common calendar asserted identical)" %
    (fxp.shape[1], len(fxp), str(fxp.index[0].date()), str(fxp.index[-1].date())))

r = fxp.pct_change()
for p in PAIRS:
    rr = r[p].dropna()
    s1 = fxp[p].diff() == 0
    stale = int((s1.groupby((~s1).cumsum()).sum()).max())
    gaps = fxp.index.to_series().diff().dt.days.dropna()
    assert fxp[p].notna().all(), "NaN in " + p
    assert int(gaps.max()) <= 5, "calendar gap > 5d in " + p
    assert stale <= 1, "stale close run > 1 in " + p
    assert float(rr.abs().max()) < 0.20, "impossible FX move in " + p
    log("  %-9s first=%.4f last=%.4f |r|max=%.2f%% stale=%d" %
        (p, fxp[p].iloc[0], fxp[p].iloc[-1], rr.abs().max() * 100, stale))
# direction sanity v2 (v1 gate was mis-specified: two foreign-vs-USD longs are the SAME
# dollar-weak bet, so they must be strongly POSITIVELY correlated; the absolute sign proof
# is the 2015-01-15 SNB depeg, where long-CHF must be strongly POSITIVE)
cre = float(r["EUR_USD"].corr(r["USD_CHF"]))
log("  direction gate: corr(longEUR, longCHF)=%.3f (need > +0.30: dollar-block coherence)" % cre)
assert cre > 0.30, "quote-direction inversion wrong"
snb = r.loc["2015-01-15", "USD_CHF"]
log("  direction gate: long-CHF on 2015-01-15 (SNB depeg)=%+.4f (need > +0.10)" % snb)
assert snb > 0.10, "long-foreign sign wrong on the SNB day"

# ---- candidate stream (frozen construction, deterministic; stream artifact saved) ----
def build_tsmom_fx(vt):
    R9 = fxp.pct_change()
    s9 = np.sign(fxp - fxp.rolling(MAW_FROZEN, min_periods=MAW_FROZEN // 2).mean()).fillna(0) / 9.0
    net, _ = wback_rb(s9, R9, wed_rbd(fxp.index))
    rfull, _ = vol_target(net.dropna(), vt_ann=vt)
    return rfull.dropna()

cand = build_tsmom_fx(0.15)
names12 = list(B.NAMES)
df12 = pd.DataFrame(dict((n, B.load(B.PATHS[n]).dropna()) for n in names12))
df12 = df12[df12.index >= "2008-03-31"]
ins = cand.reindex(df12.index)
isr12 = df12[df12.index < B.IS_END]
have12 = [n for n in names12 if isr12[n].notna().sum() > 0]
isrows = int(isr12[have12].dropna().shape[0])
assert isrows == 1809, "12-pool IS fit rows moved: %d" % isrows
frame13 = pd.concat([df12, ins.rename("FXH9")], axis=1)
isr13 = frame13[frame13.index < B.IS_END]
have13 = [n for n in names12 + ["FXH9"] if isr13[n].notna().sum() > 0]
fitrows = int(isr13[have13].dropna().shape[0])
shr = (isrows - fitrows) / float(isrows)
iscov = int(ins[df12.index < B.IS_END].notna().sum())
log("A1c candidate stream: n=%d %s..%s  IS-cov-on-frame=%d/%d  fit-row-shrink=%.4f%%" %
    (len(cand), str(cand.index[0].date()), str(cand.index[-1].date()), iscov, isrows, shr * 100))
assert shr <= 0.02, "fit-row shrink > 2 pct at probe time - fail closed"
pd.DataFrame(dict(ret=cand.values), index=cand.index).to_csv(OUT + "/sleeve_FXH9_stream.csv")
log("stream artifact saved: sleeve_FXH9_stream.csv sha16=%s" % sha16(OUT + "/sleeve_FXH9_stream.csv"))
log("PROBE OK - candidate adjudication NOT computed here (post-seal)")
with open(OUT + "/probe_iter57_a1.log", "w") as fh:
    fh.write(chr(10).join(LOG) + chr(10))
print("LOG WRITTEN: " + OUT + "/probe_iter57_a1.log")
