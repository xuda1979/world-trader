import os, sys, hashlib, ast
import numpy as np, pandas as pd
from scipy.optimize import minimize
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign/scripts")
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r6")
import rawew13v2_build as B

OUT = ROOT + "/campaign/agents/chief/coord/ITER46_CADGOVTLONG"
LOG = []
def log(s=""):
    LOG.append(str(s)); print(s)

W_MAX, SHRINK, BRWT_CAP = 2.0, 0.70, 0.30
BRWT_BLOCK = ("brwt10", "brwt7", "brwt5")
PRECOMMIT_SHA = "7027fd6f05e3c1cb"
K_COVERED = 12
BAR = 4.203733
FS_BAR = 3.764764
CHAMP = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
WGT = ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv"
K24, CAD24, VT24, VCAP24, SBPS24, SSTART24 = 378, 42, 0.12, 5.0, 6.4, "2007-01-01"
DUR = 9.5

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
    a = extract(ROOT + "/campaign/agents/chief/coord/ITER43_A5R2_VT/driver_iter43.py")
    c = extract(ROOT + "/campaign/agents/chief/coord/ITER36_DIESCRACK_Z/driver_iter36.py")
    d = extract(ROOT + "/campaign/agents/chief/coord/ITER45_CARRYV2_ZWIN/driver_iter45.py")
    b = extract(__file__)
    for src_name, blk in (("driver_iter43", a), ("driver_iter36", c), ("driver_iter45", d)):
        miss = [n for n in WANT4 if n not in blk]
        assert not miss, "frozen-block extract failed vs " + src_name + ": " + str(miss)
        diff = [n for n in WANT4 if blk[n] != b[n]]
        assert not diff, "frozen block diverged from " + src_name + ": " + str(diff)
    log("FROZEN-BLOCK check: fit_relw/apply_cap/project_wmax/build_book text-identical to driver_iter43.py, driver_iter36.py AND driver_iter45.py")

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

def load_series(rel):
    df = pd.read_csv(ROOT + "/tools/quant/data/" + rel, index_col=0, parse_dates=True)
    col = "close" if "close" in df.columns else "value"
    s = df[col].astype(float)
    return s[~s.index.duplicated(keep="last")].sort_index()

def trend_sleeve(s, kind, dur=None):
    if kind == "rates":
        y = s / 100.0
        tr = (-dur * y.diff() + y / 252.0).dropna()
    else:
        tr = s.pct_change().dropna()
    sig = (tr.rolling(K24).mean() > 0).astype(float)
    W = sig.iloc[::CAD24].reindex(tr.index).ffill().fillna(0.0)
    gross = (W.shift(1) * tr)[SSTART24:]
    turn = (W.shift(1) - W.shift(2)).abs()[SSTART24:].fillna(0.0)
    net = (gross - turn * SBPS24 / 1e4).dropna()
    lev = (VT24 / np.sqrt(252) / net.expanding(60).std().shift(1)).clip(0, VCAP24).fillna(0.0)
    return (net * lev).dropna()

def recon(regen, path):
    c = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
    c = pd.to_numeric(c, errors="coerce")
    j = pd.concat([c.dropna().rename("c"), regen.rename("g")], axis=1, join="inner").dropna()
    dev = float((j.c - j.g).abs().max())
    ok = (len(j) == int(c.notna().sum())) and dev < 1e-12
    return ok, dev, len(j), int(c.notna().sum())

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

log(9 * chr(45) + " ITER46 cad_govt_long census-remainder driver (2026-09-19 session 26). FINDINGS_PRECOMMIT.md sha16 " + PRECOMMIT_SHA + " sealed BEFORE this run. Pool-composition cell (ITER42 class, 22nd measured axis): cadlong = the ITER24 frozen recipe at the pre-registered dur=9.5 (printed 0.95*10, no novel scalar); single cell, no grid; k_covered=12 Wmax law (ITER28 correction).")
_frozen_check()
assert sha16(OUT + "/FINDINGS_PRECOMMIT.md") == PRECOMMIT_SHA, "precommit mutated - fail closed"
champ_sha_pre, wgt_sha_pre = sha16(CHAMP), sha16(WGT)
log("Champion sha16 pre-run: " + champ_sha_pre + " / weights " + wgt_sha_pre + " / precommit " + PRECOMMIT_SHA)
assert champ_sha_pre == "e67446186e269b88" and wgt_sha_pre == "bde8612d0b295068", "champion is not the ITER43 pair - fail closed"

names12 = list(B.NAMES)
df12 = pd.DataFrame(dict((n, B.load(B.PATHS[n]).dropna()) for n in names12))
df12 = df12[df12.index >= "2008-03-31"]

for sib, dur in (("cad_govt_10y", 9.5), ("cad_govt_2y", 1.9)):
    r = trend_sleeve(load_series("dm_rates/" + sib + ".csv"), "rates", dur)
    r.index.name = "date"
    ok, dev, n, nc = recon(r, ROOT + "/campaign/agents/chief/coord/ITER24_DA/sleeves/" + sib + ".csv")
    log("A1 sibling %s (dur=%.1f) regen-vs-ITER24-saved: ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (sib, dur, ok, dev, n, nc))
    assert ok, "A1 sibling recon failed - fail closed: " + sib

s_cad = trend_sleeve(load_series("dm_rates/cad_govt_long.csv"), "rates", DUR)
s_cad.index.name = "date"
log("A1 candidate stream cadlong (dur=%.1f): n=%d span %s..%s" % (DUR, len(s_cad), str(s_cad.index[0].date()), str(s_cad.index[-1].date())))

dfa = df12.copy()
dfa["cadlong"] = s_cad.reindex(df12.index)
names13 = names12 + ["cadlong"]
fit, nrows, kcov = fit_relw(dfa[dfa.index < B.IS_END], names13)
relw13_raw = apply_cap(fit)
relw13 = project_wmax(relw13_raw, k=kcov, block=B.BRWT_BLOCK)
net13, Wg13, to13 = build_book(dfa, relw13, gear=1.0)
i_net = net13[net13.index < B.IS_END]
proj_id = float((relw13 - relw13_raw).abs().max())
rec = dict(nrows=nrows, kcov=kcov, relw=relw13, relw_raw=relw13_raw, net=net13, Wg=Wg13, to=to13,
           is_sr=sr(i_net), is_mdd=mdd(i_net), ny=len(neg_years(i_net)),
           wmax_sf=float(relw13.max()) * kcov, gmax=float(Wg13.abs().sum(axis=1).max()),
           proj_id=proj_id, ws=float(relw13["cadlong"]))
log("CELL cadlong: rows=%d k=%d projid=%.3e share=%.6f IS-SR=%.6f IS-MDD=%.4f pct negyrs=%d Wmax_sf=%.4fx grossmax=%.9f" % (rec["nrows"], rec["kcov"], rec["proj_id"], rec["ws"], rec["is_sr"], rec["is_mdd"] * 100, rec["ny"], rec["wmax_sf"], rec["gmax"]))
assert kcov == K_COVERED and (1809 - nrows) / 1809.0 <= 0.02, "cell window/coverage drift - fail closed (Amendment-1 law: k=12 + G8 shrink <= 2pct)"
s_cad.to_frame("ret").to_csv(OUT + "/arm_cadlong_stream.csv")
rec["relw"].to_frame("relw").to_csv(OUT + "/arm_cadlong_weights.csv")

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
assert identC == 0.0 and wdev < 1e-12 and bdev < 1e-12 and nrowsC == 1809 and kC == 11, "A2 committed-frame continuity failed - fail closed"
assert abs(sr(iC) - BAR) < 5e-6, "committed IS-SR drifted - fail closed"

jitter_ok = (rec["ws"] > 1e-4) or (rec["is_sr"] - BAR > 1e-4)
adm = bool(rec["is_sr"] > BAR and rec["is_mdd"] >= -0.06 and rec["ny"] == 0
           and rec["wmax_sf"] <= 2.0 + 1e-9 and jitter_ok)
log("")
log("IS admission: %s (bar %.6f, margin %+.6f, share %.6f, jitter law: weight>1e-4 or margin>1e-4 -> %s)" % (str(adm), BAR, rec["is_sr"] - BAR, rec["ws"], str(jitter_ok)))
verdict = "NO-ADMISSION (IS level) -> honest negative, no reveal (per precommit stop rule)"
if not adm:
    log("Cell NOT IS-admitted -> HONEST NEGATIVE, no reveal (sealed stop rule).")
else:
    relw, net, Wg, to = rec["relw"], rec["net"], rec["Wg"], rec["to"]
    f_sr, f_mdd = sr(net), mdd(net)
    f_ann_a, f_ann_c = ann_arith(net) * 100, ann_cagr(net) * 100
    nyf = neg_years(net)
    toyr = float(to.mean() * 252 * B.BPS)
    margin_yr = float((np.maximum(Wg.abs().sum(axis=1) - 1.0, 0.0) * B.RATE).mean() * 100)
    cfx = float(relw["CFX4"])
    wmax_sf = rec["wmax_sf"]
    gmax = rec["gmax"]
    log("")
    log("REVEAL cell cadlong (single pre-registered cell), gear 1.0, n=%d (%s..%s)" % (len(net), str(net.index[0].date()), str(net.index[-1].date())))
    log("  FS SR=%.6f (incumbent 3.764764)  ann arith=%.4f pct  cagr=%.4f pct  MDD=%.4f pct  negyrs=%d" % (f_sr, f_ann_a, f_ann_c, f_mdd * 100, len(nyf)))
    log("  grossmax=%.9f  turnover=%.4f bp/yr  margin=%.4f pct/yr  Wmax_sf=%.4fx (k=12)  CFX4=%.1e" % (gmax, toyr, margin_yr, wmax_sf, cfx))
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
    g8 = (1809 - rec["nrows"]) / 1809.0 <= 0.02
    gates = [g1, g2, g3, g4, g5, g6, g7, g8]
    labels = ["1 FS ann>=20pct", "2 gross<=1.6", "3 FS MDD>=-7pct", "4 0 FS neg yrs",
              "5 CFX4=0", "6 Wmax_sf<=2.0x (k=12)", "7 OOS police", "8 fit-window shrink<=2pct"]
    for l, g in zip(labels, gates):
        log("  GATE %-30s %s" % (l, "PASS" if g else "FAIL"))
    if all(gates):
        verdict = "ADOPTABLE (8/8) -> proceed to full battery per precommit"
    else:
        fails = [l for l, g in zip(labels, gates) if not g]
        verdict = "REJECT - failed gates: " + ", ".join(fails) + " (no second reveal per precommit)"
    pd.DataFrame(dict(ret=net.values), index=net.index).to_csv(OUT + "/candidate_cadlong_daily.csv")

log("")
log("VERDICT: " + verdict)
champ_sha_post, wgt_sha_post = sha16(CHAMP), sha16(WGT)
log("Champion sha16 post-run: " + champ_sha_post + " / weights " + wgt_sha_post + " (pre==post: " + str((champ_sha_pre == champ_sha_post) and (wgt_sha_pre == wgt_sha_post)) + ")")
assert champ_sha_pre == champ_sha_post and wgt_sha_pre == wgt_sha_post
with open(OUT + "/driver_iter46.log", "w") as fh:
    fh.write(chr(10).join(LOG) + chr(10))
print("LOG WRITTEN: " + OUT + "/driver_iter46.log")
