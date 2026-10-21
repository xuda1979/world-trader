import os, sys, hashlib, ast
import numpy as np, pandas as pd
from scipy.optimize import minimize
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign/scripts")
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r6")
import rawew13v2_build as B

OUT = ROOT + "/campaign/agents/chief/coord/ITER53_DUR_READJ"
LOG = []
def log(s=""):
    LOG.append(str(s)); print(s)

W_MAX, SHRINK, BRWT_CAP = 2.0, 0.70, 0.30
BRWT_BLOCK = ("brwt10", "brwt7", "brwt5")
PRECOMMIT_SHA = "710a1e7de776dbbd"
K_COVERED = 11
BAR = 4.218504
FS_BAR = 3.820357
ARMS = (1.90, 1.40, 1.65, 2.15, 2.40)
ANCHOR_DUR = 1.90
CHAMP = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
WGT = ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv"
A6R7_CSV = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv"
DGS2 = ROOT + "/tools/quant/hedge_fund_strats/data_fred_new/DGS2.csv"
K, CAD, VT, CAP = 378, 42, 0.12, 5.0

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
    b = extract(__file__)
    for src_name, blk in (("driver_iter41", a), ("driver_iter36", c)):
        miss = [n for n in WANT4 if n not in blk]
        assert not miss, "frozen-block extract failed vs " + src_name + ": " + str(miss)
        diff = [n for n in WANT4 if blk[n] != b[n]]
        assert not diff, "frozen block diverged from " + src_name + ": " + str(diff)
    log("FROZEN-BLOCK check: fit_relw/apply_cap/project_wmax/build_book text-identical to driver_iter41.py AND driver_iter36.py")

def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

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

log(9 * chr(45) + " ITER53 A6R7-DUR STALENESS RE-ADJUDICATION driver (2026-09-20 session 33). FINDINGS_PRECOMMIT.md sha16 " + PRECOMMIT_SHA + " sealed BEFORE this run.")
_frozen_check()
assert sha16(OUT + "/FINDINGS_PRECOMMIT.md") == PRECOMMIT_SHA, "precommit mutated - fail closed"
champ_sha_pre, wgt_sha_pre = sha16(CHAMP), sha16(WGT)
log("Champion sha16 pre-run: " + champ_sha_pre + " / weights " + wgt_sha_pre + " / precommit " + PRECOMMIT_SHA)
assert (champ_sha_pre, wgt_sha_pre) == ("cfa9ec4d38158691", "a384d6b92e258fd5"), "driver must run against the ADOPTED pair untouched"

log("D17 SCOPE NOTE: the ITER53 chain is r6lib-FREE - legacy_a6r7 needs only pandas + DGS2 and rawew13v2_build loads the committed sleeve CSVs directly (no data.panel call); the PARENT-driver DUAL-identity D17 patch (iter52 form) is NOT-APPLICABLE here (the documented non-r6lib case) and is substituted OUT. The D17 runtime-patch law remains LOAD-BEARING for every r6lib-resolving chain and is untouched by this note.")

def legacy_a6r7(dur):
    y = pd.read_csv(DGS2, index_col=0, parse_dates=True)["value"].astype(float) / 100.0
    y = y[~y.index.duplicated(keep="last")].sort_index()
    tr = (-dur * y.diff() + y / 252.0).dropna()
    sig = (tr.rolling(K).mean() > 0).astype(float)
    W = sig.iloc[::CAD].reindex(tr.index).ffill().fillna(0.0)
    gross_g = W.shift(1) * tr
    turn = (W.shift(1) - W.shift(2)).abs().fillna(0.0)
    net_g = (gross_g - turn * 6.0 / 1e4).dropna()
    lev = (VT / np.sqrt(252) / net_g.expanding(60).std().shift(1)).clip(0, CAP).fillna(0.0)
    return (net_g * lev).dropna()

def recon(regen, path):
    c = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
    c = pd.to_numeric(c, errors="coerce")
    j = pd.concat([c.dropna().rename("c"), regen.rename("g")], axis=1, join="inner").dropna()
    dev = float((j.c - j.g).abs().max())
    ok = (len(j) == int(c.notna().sum())) and dev < 1e-12
    return ok, dev, len(j), int(c.notna().sum())

names12 = list(B.NAMES)
df12 = pd.DataFrame(dict((n, B.load(B.PATHS[n]).dropna()) for n in names12))
df12 = df12[df12.index >= "2008-03-31"]

sT = legacy_a6r7(ANCHOR_DUR)
okT, devT, niT, ncT = recon(sT, A6R7_CSV)
log("A1 regen-dur1.90-vs-committed a6r7 ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (okT, devT, niT, ncT))
assert okT, "A1 failed - fail closed"

streams = dict()
results = dict()
for dur in ARMS:
    s1 = legacy_a6r7(dur)
    streams[dur] = s1
    assert s1.index.equals(streams[ANCHOR_DUR].index), "calendar moved with DUR - coverage law violated"
    dfa = df12.copy()
    dfa["a6r7"] = s1.reindex(df12.index)
    assert int(dfa["a6r7"].notna().sum()) == int(df12["a6r7"].notna().sum()), "frame coverage changed - fail closed"
    fit, nrows, kcov = fit_relw(dfa[dfa.index < B.IS_END], names12)
    relw_raw = apply_cap(fit)
    relw = project_wmax(relw_raw, k=kcov, block=B.BRWT_BLOCK)
    netA, WgA, toA = build_book(dfa, relw, gear=1.0)
    i_net = netA[netA.index < B.IS_END]
    rec = dict(nrows=nrows, kcov=kcov, relw=relw, relw_raw=relw_raw, net=netA, Wg=WgA, to=toA,
               is_sr=sr(i_net), is_mdd=mdd(i_net), ny=len(neg_years(i_net)),
               wmax_sf=float(relw.max()) * kcov, gmax=float(WgA.abs().sum(axis=1).max()),
               proj_id=float((relw - relw_raw).abs().max()))
    results[dur] = rec
    log("ARM DUR=%.2f: rows=%d k=%d projid=%.3e IS-SR=%.6f IS-MDD=%.4f pct negyrs=%d Wmax_sf=%.4fx grossmax=%.9f" % (dur, nrows, kcov, rec["proj_id"], rec["is_sr"], rec["is_mdd"] * 100, rec["ny"], rec["wmax_sf"], rec["gmax"]))
    assert nrows == 1809 and kcov == K_COVERED, "arm window/coverage drift - fail closed"
    s1.to_frame("ret").to_csv(OUT + "/arm_dur" + ("%.2f" % dur) + "_stream_a6r7.csv")
    rec["relw"].to_frame("relw").to_csv(OUT + "/arm_dur" + ("%.2f" % dur) + "_weights.csv")

_fitC, nrowsC, kC = fit_relw(df12[df12.index < B.IS_END], names12)
relwC_raw = apply_cap(_fitC)
relwC = project_wmax(relwC_raw, k=kC, block=B.BRWT_BLOCK)
netC, WgC, _ = build_book(df12, relwC, gear=1.0)
identC = float((relwC - relwC_raw).abs().max())
committed = pd.read_csv(WGT, index_col=0).iloc[:, 0]
wdev = float((relwC - committed.reindex(relwC.index)).abs().max())
champ = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
jj = pd.concat([champ.rename("csv"), netC.rename("reb")], axis=1, join="inner")
bdev = float((jj["csv"] - jj["reb"]).abs().max())
iC = netC[netC.index < B.IS_END]
log("A2 committed-frame continuity: projid=%.3e weights maxdev=%.3e bytes maxdev=%.3e n=%d rows=%d k=%d IS-SR=%.6f (bar %.6f)" % (identC, wdev, bdev, len(jj), nrowsC, kC, sr(iC), BAR))
assert identC == 0.0 and wdev < 1e-12 and bdev < 1e-12 and nrowsC == 1809 and kC == K_COVERED, "A2 committed-frame continuity failed - fail closed"
assert abs(sr(iC) - BAR) < 5e-6, "committed IS-SR drifted - fail closed"
ra = results[ANCHOR_DUR]
jit_w = float((ra["relw"] - relwC).abs().max())
jit_sr = abs(ra["is_sr"] - sr(iC))
log("A2b regen-vs-committed fit-landing jitter: weights %.3e  IS-SR %.3e" % (jit_w, jit_sr))

adm = [dur for dur in ARMS if dur != ANCHOR_DUR
       and results[dur]["is_sr"] > BAR + 1e-4
       and results[dur]["is_mdd"] >= -0.06
       and results[dur]["ny"] == 0
       and results[dur]["wmax_sf"] <= 2.0 + 1e-9]
log("")
log("IS admission: " + str(adm) + " (bar %.6f, anchor arm ineligible by construction)" % BAR)
verdict = "NO-ADMISSION (IS level) -> honest negative, no reveal (per precommit stop rule)"
if not adm:
    log("NO non-anchor arm IS-admitted -> HONEST NEGATIVE, no reveal (sealed stop rule).")
else:
    best = max(adm, key=lambda dur: results[dur]["is_sr"])
    r = results[best]
    relw, net, Wg, to = r["relw"], r["net"], r["Wg"], r["to"]
    f_sr, f_mdd = sr(net), mdd(net)
    f_ann_a, f_ann_c = ann_arith(net) * 100, ann_cagr(net) * 100
    nyf = neg_years(net)
    toyr = float(to.mean() * 252 * B.BPS)
    margin_yr = float((np.maximum(Wg.abs().sum(axis=1) - 1.0, 0.0) * B.RATE).mean() * 100)
    cfx = float(relw["CFX4"])
    wmax_sf = r["wmax_sf"]
    gmax = r["gmax"]
    log("")
    log("REVEAL arm DUR=%.2f (IS-argmax of admitted), gear 1.0, n=%d (%s..%s)" % (best, len(net), str(net.index[0].date()), str(net.index[-1].date())))
    log("  FS SR=%.6f (incumbent %.6f)  ann arith=%.4f pct  cagr=%.4f pct  MDD=%.4f pct  negyrs=%d" % (f_sr, FS_BAR, f_ann_a, f_ann_c, f_mdd * 100, len(nyf)))
    log("  grossmax=%.9f  turnover=%.4f bp/yr  margin=%.4f pct/yr  Wmax_sf=%.4fx (k=11)  CFX4=%.1e" % (gmax, toyr, margin_yr, wmax_sf, cfx))
    bins = (("2017-18", "2017", "2018"), ("2019-20", "2019", "2020"), ("2021-22", "2021", "2022"),
            ("2023-24", "2023", "2024"), ("2025-26", "2025", "2026"))
    dsrc = []
    for lbl2, a, b in bins:
        m_c = net[(net.index >= a + "-01-01") & (net.index <= b + "-12-31")]
        m_i = champ[(champ.index >= a + "-01-01") & (champ.index <= b + "-12-31")]
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
    g8 = (1809 - r["nrows"]) / 1809.0 <= 0.02
    gates = [g1, g2, g3, g4, g5, g6, g7, g8]
    labels = ["1 FS ann>=20pct", "2 gross<=1.6", "3 FS MDD>=-7pct", "4 0 FS neg yrs",
              "5 CFX4=0", "6 Wmax_sf<=2.0x (k=11)", "7 OOS police", "8 fit-window shrink<=2pct"]
    for l, g in zip(labels, gates):
        log("  GATE %-30s %s" % (l, "PASS" if g else "FAIL"))
    if all(gates):
        verdict = "ADOPTABLE (8/8) -> proceed to full battery per precommit"
    else:
        fails = [l for l, g in zip(labels, gates) if not g]
        verdict = "REJECT - failed gates: " + ", ".join(fails) + " (no second reveal per precommit)"
    pd.DataFrame(dict(ret=net.values), index=net.index).to_csv(OUT + "/candidate_dur" + ("%.2f" % best) + "_daily.csv")

log("")
log("VERDICT: " + verdict)
champ_sha_post, wgt_sha_post = sha16(CHAMP), sha16(WGT)
log("Champion sha16 post-run: " + champ_sha_post + " / weights " + wgt_sha_post + " (pre==post: " + str((champ_sha_pre == champ_sha_post) and (wgt_sha_pre == wgt_sha_post)) + ")")
assert champ_sha_pre == champ_sha_post and wgt_sha_pre == wgt_sha_post
with open(OUT + "/driver_iter53.log", "w") as fh:
    fh.write(chr(10).join(LOG) + chr(10))
print("LOG WRITTEN: " + OUT + "/driver_iter53.log")
