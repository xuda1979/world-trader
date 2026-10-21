import os, sys, hashlib, ast, io
import numpy as np, pandas as pd
from scipy.optimize import minimize
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign/scripts")
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r6")
import rawew13v2_build as B

OUT = ROOT + "/campaign/agents/chief/coord/ITER57_FXHIST_TSMOM"
LOG = []
def log(s=""):
    LOG.append(str(s)); print(s)

W_MAX, SHRINK, BRWT_CAP = 2.0, 0.70, 0.30
BRWT_BLOCK = ("brwt10", "brwt7", "brwt5")
PRECOMMIT_SHA = "3ab2baad6966b10b"
BAR = 4.218504
FS_BAR = 3.820357
MAW_FROZEN = 189
PAIRS = ["EUR_USD","GBP_USD","AUD_USD","NZD_USD","USD_CAD","USD_CHF","USD_JPY","USD_SEK","USD_NOK"]
STREAM_SHA = "9f61a03317a535ef"
CHAMP = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
WGT   = ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv"
TSM_CSV = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189__vt015.csv"

def _frozen_check():
    WANT4 = ("fit_relw", "apply_cap", "project_wmax", "build_book")
    def extract(path):
        src = open(path).read()
        tree = ast.parse(src)
        out = dict()
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in WANT4:
                out[node.name] = ast.get_source_segment(src, node)
        return out
    a = extract(ROOT + "/campaign/agents/chief/coord/ITER41_VTOVERLAY/driver_iter41.py")
    c = extract(ROOT + "/campaign/agents/chief/coord/ITER36_DIESCRACK_Z/driver_iter36.py")
    e = extract(ROOT + "/campaign/agents/chief/coord/ITER49_TSMOM_VT/driver_iter49.py")
    b = extract(__file__)
    for src_name, blk in (("driver_iter41", a), ("driver_iter36", c), ("driver_iter49", e)):
        miss = [n for n in WANT4 if n not in blk]
        assert not miss, "frozen-block extract failed vs " + src_name + ": " + str(miss)
        diff = [n for n in WANT4 if blk[n] != b[n]]
        assert not diff, "frozen block diverged from " + src_name + ": " + str(diff)
    log("FROZEN-BLOCK check: fit_relw/apply_cap/project_wmax/build_book text-identical to driver_iter41.py, driver_iter36.py AND driver_iter49.py")

def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

def sha16_bytes(b):
    return hashlib.sha256(b).hexdigest()[:16]

def sr(x): return float(x.mean() / x.std(ddof=1) * np.sqrt(252))

def mdd(x):
    nav = (1 + x).cumprod(); return float((nav / nav.cummax() - 1).min())

def ann_arith(x): return float(x.mean() * 252)

def ann_cagr(x): return float((1 + x).prod() ** (252 / len(x)) - 1)

def neg_years(x):
    yr = x.groupby(x.index.year).apply(lambda v: (1 + v).prod() - 1)
    return yr[yr < 0]
def fit_relw(df_isr, names, shrink=SHRINK):
    have = [n for n in names if df_isr[n].notna().sum() > 0]
    X = df_isr[have].dropna()
    mu = (X.mean() * 252).values
    Sig = X.cov().values * 252
    Sig = (1.0 - shrink) * Sig + shrink * np.diag(np.diag(Sig))
    k, sd = len(have), np.sqrt(np.diag(Sig))
    def neg_sharpe(w):
        v = float(np.sqrt(w @ Sig @ w))
        return -(float(w @ mu)) / v if v > 1e-14 else 0.0
    cons = [dict(type="eq", fun=lambda w: w.sum() - 1.0)]
    cap = W_MAX / k
    def solve(bounds):
        best = None
        for w0 in (np.full(k, 1.0 / k),
                   np.maximum(mu, 0.0) / max(float(np.maximum(mu, 0.0).sum()), 1e-12),
                   (1.0 / sd) / (1.0 / sd).sum()):
            r = minimize(neg_sharpe, w0, method="SLSQP", bounds=bounds, constraints=cons,
                         options=dict(maxiter=800, ftol=1e-12))
            if r.success and (best is None or r.fun < best.fun):
                best = r
        return best
    best = solve([(0.0, W_MAX)] * k)
    if best is not None and float(best.x.max()) > cap + 1e-9:
        best = solve([(0.0, cap)] * k)
    if best is None:
        raise RuntimeError("IS max-Sharpe fit failed to converge - fail closed")
    relw = pd.Series(0.0, index=names)
    relw[have] = best.x
    return relw, int(X.shape[0]), int(k)

def apply_cap(relw, cap=BRWT_CAP):
    share = relw / relw.sum(); out = share.copy()
    if cap is not None:
        blk = [n for n in BRWT_BLOCK if n in share.index]
        bs = float(share[blk].sum())
        if bs > cap:
            excess = bs - cap
            out[blk] = share[blk] * (cap / bs)
            nonblk = [n for n in share.index if n not in blk]
            nb = float(share[nonblk].sum())
            out[nonblk] = share[nonblk] + excess * share[nonblk] / nb
    if "CFX4" in out.index: out["CFX4"] = 0.0
    return out

def project_wmax(relw, k, block=BRWT_BLOCK, tol=1e-12, iters=200):
    cap = 2.0 / k
    out = relw.copy()
    s0 = float(out.sum())
    for _ in range(iters):
        over = out > cap + tol
        if not over.any():
            break
        if bool(out[list(block)].max() > cap + tol):
            raise RuntimeError("block name violates invariant - fail closed")
        excess = float((out[over] - cap).sum())
        out[over] = cap
        recv = [n for n in out.index
                if (n not in block) and (n != "CFX4") and (float(out[n]) < cap - tol)]
        if not recv:
            raise RuntimeError("water-filling has no receivers - fail closed")
        w = out[recv].astype(float); s = float(w.sum())
        if s <= 1e-15:
            raise RuntimeError("water-filling receiver mass zero - fail closed")
        out[recv] = w + excess * w / s
    else:
        raise RuntimeError("water-filling did not converge - fail closed")
    assert abs(float(out.sum()) - s0) < 1e-12, "sum not preserved"
    if "CFX4" in out.index: assert float(out["CFX4"]) == 0.0
    assert float(out[list(block)].sum()) <= BRWT_CAP + 1e-9, "block mass grew"
    return out

def build_book(frame, relw, gear=1.0):
    nav = (1 + frame.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(relw)
    Wg = d2 * (gear / len(relw))
    port = (frame.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    net = pd.Series(port, index=frame.index) - to * B.BPS / 1e4 - max(gear - 1, 0) * B.RATE / 252
    return net, Wg, to

def recon(regen, path):
    c = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
    c = pd.to_numeric(c, errors="coerce")
    j = pd.concat([c.dropna().rename("c"), regen.rename("g")], axis=1, join="inner").dropna()
    dev = float((j.c - j.g).abs().max())
    ok = (len(j) == int(c.notna().sum())) and dev < 1e-12
    return ok, dev, len(j), int(c.notna().sum())
log(9 * chr(45) + " ITER57 FXHIST-TSMOM transplant driver (2026-09-20 session 37). FINDINGS_PRECOMMIT.md sha16 " + PRECOMMIT_SHA + " sealed BEFORE this run.")
_frozen_check()
assert sha16(OUT + "/FINDINGS_PRECOMMIT.md") == PRECOMMIT_SHA, "precommit mutated - fail closed"
champ_sha_pre, wgt_sha_pre = sha16(CHAMP), sha16(WGT)
log("Champion sha16 pre-run: " + champ_sha_pre + " / weights " + wgt_sha_pre + " / precommit " + PRECOMMIT_SHA)
assert (champ_sha_pre, wgt_sha_pre) == ("cfa9ec4d38158691", "a384d6b92e258fd5"), "driver must run against the ADOPTED pair untouched"

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
log("FX panel: %d cols n=%d %s..%s" % (fxp.shape[1], len(fxp), str(fxp.index[0].date()), str(fxp.index[-1].date())))
r9 = fxp.pct_change()
for p in PAIRS:
    rr = r9[p].dropna()
    s1 = fxp[p].diff() == 0
    stale = int((s1.groupby((~s1).cumsum()).sum()).max())
    gaps = fxp.index.to_series().diff().dt.days.dropna()
    assert fxp[p].notna().all(), "NaN in " + p
    assert int(gaps.max()) <= 5, "calendar gap > 5d in " + p
    assert stale <= 1, "stale close run > 1 in " + p
    assert float(rr.abs().max()) < 0.20, "impossible FX move in " + p
cre = float(r9["EUR_USD"].corr(r9["USD_CHF"]))
snb = float(r9.loc["2015-01-15", "USD_CHF"])
log("FX hygiene gates: 9/9 no-NaN/maxgap<=5/stale<=1/|r|<20pct; corr(longEUR,longCHF)=%.3f (>+0.30); SNB-day longCHF=%+.4f (>+0.10)" % (cre, snb))
assert cre > 0.30 and snb > 0.10, "direction gates failed - fail closed"

def build_tsmom_fx(vt):
    R9 = fxp.pct_change()
    s9 = np.sign(fxp - fxp.rolling(MAW_FROZEN, min_periods=MAW_FROZEN // 2).mean()).fillna(0) / 9.0
    net, _ = wback_rb(s9, R9, wed_rbd(fxp.index))
    rfull, _ = vol_target(net.dropna(), vt_ann=vt)
    return rfull.dropna()

sT = build_tsmom(0.15)
okT, devT, niT, ncT = recon(sT, TSM_CSV)
log("A1a canonical vt015 regen ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (okT, devT, niT, ncT))
assert okT, "A1a recipe fidelity failed - fail closed"

cand = build_tsmom_fx(0.15)
buf = io.StringIO()
pd.DataFrame(dict(ret=cand.values), index=cand.index).to_csv(buf)
got = sha16_bytes(buf.getvalue().encode())
log("stream re-derive sha16=%s (probe artifact %s)" % (got, STREAM_SHA))
assert got == STREAM_SHA, "candidate stream not byte-equal to probe artifact - fail closed"

names12 = list(B.NAMES)
df12 = pd.DataFrame(dict((n, B.load(B.PATHS[n]).dropna()) for n in names12))
df12 = df12[df12.index >= "2008-03-31"]

_fitC, nrowsC, kC = fit_relw(df12[df12.index < B.IS_END], names12)
relwC_raw = apply_cap(_fitC)
relwC = project_wmax(relwC_raw, k=kC, block=B.BRWT_BLOCK)
netC, WgC, _ = build_book(df12, relwC, gear=1.0)
committed = pd.read_csv(WGT, index_col=0).iloc[:, 0]
wdev = float((relwC - committed.reindex(relwC.index)).abs().max())
champ = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
jj = pd.concat([champ.rename("csv"), netC.rename("reb")], axis=1, join="inner")
bdev = float((jj["csv"] - jj["reb"]).abs().max())
iC = netC[netC.index < B.IS_END]
log("A2 committed-frame continuity: weights maxdev=%.3e bytes maxdev=%.3e n=%d rows=%d k=%d IS-SR=%.6f (bar %.6f)" % (wdev, bdev, len(jj), nrowsC, kC, sr(iC), BAR))
assert wdev < 1e-12 and bdev < 1e-12 and nrowsC == 1809 and kC == 11, "A2 committed-frame continuity failed - fail closed"
assert abs(sr(iC) - BAR) < 5e-6, "committed IS-SR drifted - fail closed"

cand_r = cand.reindex(df12.index)
dfa = df12.copy()
dfa["FXH9"] = cand_r
assert dfa.index.equals(df12.index), "frame index changed - fail closed"
fit13, nrows13, k13 = fit_relw(dfa[dfa.index < B.IS_END], names12 + ["FXH9"])
relw13_raw = apply_cap(fit13)
relw13 = project_wmax(relw13_raw, k=k13, block=B.BRWT_BLOCK)
proj_id = float((relw13 - relw13_raw).abs().max())
net13, Wg13, _ = build_book(dfa, relw13, gear=1.0)
i_net = net13[net13.index < B.IS_END]
i_sr, i_mdd = sr(i_net), mdd(i_net)
i_ann = ann_arith(i_net) * 100
ny = len(neg_years(i_net))
wmax_sf = float(relw13.max()) * k13
gmax = float(Wg13.abs().sum(axis=1).max())
g8 = (1809 - nrows13) / 1809.0
wfx = float(relw13["FXH9"])
log("CANDIDATE FXH9: relw=%.5f projid=%.3e rows=%d k=%d IS-SR=%.6f IS-ann=%.3f%% IS-MDD=%.4f%% negyrs=%d Wmax_sf=%.4fx (k=%d) g8=%.3f%% grossmax=%.9f" %
    (wfx, proj_id, nrows13, k13, i_sr, i_ann, i_mdd * 100, ny, wmax_sf, k13, g8 * 100, gmax))
filt = (i_sr > BAR + 1e-4) and (i_mdd >= -0.06) and (ny == 0) and (wmax_sf <= 2.0 + 1e-9) and (g8 <= 0.02)
relw13.to_frame("relw").to_csv(OUT + "/candidate_FXH9_weights.csv")

verdict = "NO-ADMISSION (IS level) -> honest negative, no reveal (per precommit stop rule)"
if not filt:
    log("FXH9 NOT admitted at the IS bar (%.6f + 1e-4) -> HONEST NEGATIVE, no reveal." % BAR)
else:
    f_sr, f_mdd = sr(net13), mdd(net13)
    f_ann_a, f_ann_c = ann_arith(net13) * 100, ann_cagr(net13) * 100
    nyf = neg_years(net13)
    toyr = float(Wg13.diff().abs().sum(axis=1).fillna(0.0).mean() * 252 * B.BPS)
    cfx = float(relw13["CFX4"])
    log("")
    log("REVEAL: 13-pool + FXH9 at gear 1.0, n=%d (%s..%s)" % (len(net13), str(net13.index[0].date()), str(net13.index[-1].date())))
    log("  FS SR=%.6f (incumbent %.6f)  ann arith=%.4f%%  cagr=%.4f%%  MDD=%.4f%%  negyrs=%d" %
        (f_sr, FS_BAR, f_ann_a, f_ann_c, f_mdd * 100, len(nyf)))
    log("  grossmax=%.9f  turnover=%.4f bp/yr  Wmax_sf=%.4fx (k=%d)  CFX4=%.1e  FXH9 relw=%.5f" %
        (gmax, toyr, wmax_sf, k13, cfx, wfx))
    bins = (("2017-18", "2017", "2018"), ("2019-20", "2019", "2020"), ("2021-22", "2021", "2022"),
            ("2023-24", "2023", "2024"), ("2025-26", "2025", "2026"))
    dsrc = []
    for lbl2, a2, b2 in bins:
        m_c = net13[(net13.index >= a2 + "-01-01") & (net13.index <= b2 + "-12-31")]
        m_i = champ[(champ.index >= a2 + "-01-01") & (champ.index <= b2 + "-12-31")]
        dsr = sr(m_c) - sr(m_i)
        dsrc.append(dsr)
        log("  bin %s dSR=%+.4f (cand %.4f vs inc %.4f)" % (lbl2, dsr, sr(m_c), sr(m_i)))
    pos = sum(1 for d_ in dsrc if d_ > 0)
    g1 = (f_ann_c >= 20.0) or (f_ann_a >= 20.0)
    g2 = gmax <= 1.6 + 1e-9
    g3 = f_mdd >= -0.07
    g4 = len(nyf) == 0
    g5 = cfx == 0.0
    g6 = wmax_sf <= 2.0 + 1e-9
    g7 = (pos >= 4) and (min(dsrc) >= -0.10) and (f_sr > FS_BAR)
    gates = [g1, g2, g3, g4, g5, g6, g7, g8 <= 0.02]
    labels = ["1 FS ann>=20pct", "2 gross<=1.6", "3 FS MDD>=-7pct", "4 0 FS neg yrs",
              "5 CFX4=0", "6 Wmax_sf<=2.0x (have-set)", "7 OOS police", "8 fit-row shrink<=2pct"]
    for l, g in zip(labels, gates):
        log("  GATE %-30s %s" % (l, "PASS" if g else "FAIL"))
    if all(gates):
        verdict = "ADOPTABLE (8/8) -> proceed to full battery per precommit"
        pd.DataFrame(dict(ret=net13.values), index=net13.index).to_csv(OUT + "/candidate_FXH9_daily.csv")
    else:
        fails = [l for l, g in zip(labels, gates) if not g]
        verdict = "REJECT - failed gates: " + ", ".join(fails) + " (no second reveal per precommit)"
log("")
log("VERDICT: " + verdict)
champ_sha_post, wgt_sha_post = sha16(CHAMP), sha16(WGT)
log("Champion sha16 post-run: " + champ_sha_post + " / weights " + wgt_sha_post + " (pre==post: " + str((champ_sha_pre == champ_sha_post) and (wgt_sha_pre == wgt_sha_post)) + ")")
assert champ_sha_pre == champ_sha_post and wgt_sha_pre == wgt_sha_post
with open(OUT + "/driver_iter57.log", "w") as fh:
    fh.write(chr(10).join(LOG) + chr(10))
print("LOG WRITTEN: " + OUT + "/driver_iter57.log")
