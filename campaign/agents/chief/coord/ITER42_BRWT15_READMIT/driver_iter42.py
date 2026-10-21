import os, sys, hashlib, ast
import numpy as np, pandas as pd
from scipy.optimize import minimize
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign/scripts")
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r6")
import rawew13v2_build as B
import refresh_sleeves as RS

OUT = ROOT + "/campaign/agents/chief/coord/ITER42_BRWT15_READMIT"
LOG = []
def log(s=""):
    LOG.append(str(s)); print(s)

W_MAX, SHRINK, BRWT_CAP = 2.0, 0.70, 0.30
BRWT_BLOCK = ("brwt10", "brwt7", "brwt5", "brwt15")
PRECOMMIT_SHA = "2b204b1a5f3f4e0c"
K_COVERED_INC = 11
K_COVERED_CAND = 12
BAR = 4.198632
FS_BAR = 3.751429
CHAMP = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
WGT = ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv"
SL = ROOT + "/campaign/agents/chief/coord/CAMP_COST/sleeves/"

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

log(9 * chr(45) + " ITER42 brwt15 RE-ADMISSION driver (2026-09-19 session 22). FINDINGS_PRECOMMIT.md sha16 " + PRECOMMIT_SHA + " (with Amendment 1) sealed BEFORE this run.")
_frozen_check()
assert sha16(OUT + "/FINDINGS_PRECOMMIT.md") == PRECOMMIT_SHA, "precommit mutated - fail closed"
champ_sha_pre, wgt_sha_pre = sha16(CHAMP), sha16(WGT)
log("Champion sha16 pre-run: " + champ_sha_pre + " / weights " + wgt_sha_pre + " / precommit " + PRECOMMIT_SHA)

def recon(regen, path):
    c = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
    c = pd.to_numeric(c, errors="coerce")
    j = pd.concat([c.dropna().rename("c"), regen.rename("g")], axis=1, join="inner").dropna()
    dev = float((j.c - j.g).abs().max())
    ok = (len(j) == int(c.notna().sum())) and dev < 1e-12
    return ok, dev, len(j), int(c.notna().sum())

A1 = []
for nm, args, p in (("brwt10", (10, 1.0, "2000-01-01"), SL + "brwt10_2000__costfix.csv"),
                    ("brwt7", (7, 1.0, "2008-01-01"), SL + "brwt7__costfix.csv"),
                    ("brwt5", (5, 1.0, "2008-01-01"), SL + "brwt5__costfix.csv")):
    ok, dev, ni, nc = recon(RS.brwt_build(*args), p)
    A1.append((nm, ok, dev, ni, nc))
    log("A1 sibling recon %s ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (nm, ok, dev, ni, nc))
assert all(t[1] for t in A1), "A1 sibling recon failed - fail closed"
r15 = RS.brwt_build(15, 1.0, "2000-01-01")
p15 = pd.read_csv(SL + "brwt15__prefix.csv", index_col=0, parse_dates=True).iloc[:, 0]
p15 = pd.to_numeric(p15, errors="coerce")
ok_ii = bool(p15.dropna().index.isin(r15.dropna().index).all())
tail_end = str(r15.dropna().index[-1].date())
log("A1 ii-prime overlap-calendar identical=%s  regen n=%d tail end=%s (siblings 2026-08-28)" % (ok_ii, len(r15.dropna()), tail_end))
assert ok_ii and tail_end == "2026-08-28", "A1 ii-prime failed - fail closed"

names12 = list(B.NAMES)
df12 = pd.DataFrame(dict((n, B.load(B.PATHS[n]).dropna()) for n in names12))
df12 = df12[df12.index >= "2008-03-31"]

_fit12, nrows12, k12 = fit_relw(df12[df12.index < B.IS_END], names12)
relw12_raw = apply_cap(_fit12)
assert k12 == K_COVERED_INC, "k_covered drift - fail closed"
relw12 = project_wmax(relw12_raw, k=K_COVERED_INC, block=B.BRWT_BLOCK)
ident = float((relw12 - relw12_raw).abs().max())
committed = pd.read_csv(WGT, index_col=0).iloc[:, 0]
wdev = float((relw12 - committed.reindex(relw12.index)).abs().max())
net12, Wg12, _ = build_book(df12, relw12, gear=1.0)
champ = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
jj = pd.concat([champ.rename("csv"), net12.rename("reb")], axis=1, join="inner")
bdev = float((jj["csv"] - jj["reb"]).abs().max())
gmax = float(Wg12.abs().sum(axis=1).max())
isr_net12 = net12[net12.index < B.IS_END]
is_sr_inc = sr(isr_net12)
inc_wmax_sf = float(relw12.max()) * K_COVERED_INC
log("ANCHOR A2 projection-identity on incumbent: maxdev=" + repr(ident) + " (need exactly 0)")
log("ANCHOR A2 weights maxdev=%.3e  bytes maxdev=%.3e n=%d  grossmax=%.9f" % (wdev, bdev, len(jj), gmax))
log("ANCHOR A2 rows=%d k=%d Wmax_sf(x11)=%.4fx IS-SR=%.6f (continuity 4.198632)" % (nrows12, k12, inc_wmax_sf, is_sr_inc))
assert ident == 0.0, "projection is NOT identity on the feasible incumbent - fail closed"
assert wdev < 1e-12 and bdev < 1e-12 and gmax <= 1.0 + 1e-9
assert nrows12 == 1809, "fit row drift - fail closed"
assert abs(is_sr_inc - 4.198632) < 5e-6, "IS-SR anchor drifted - fail closed"

names13 = names12 + ["brwt15"]
df13 = df12.copy()
df13["brwt15"] = r15.reindex(df12.index)
_fit13, nrows13, k13 = fit_relw(df13[df13.index < B.IS_END], names13)
relw13_raw = apply_cap(_fit13)
assert k13 == K_COVERED_CAND, "candidate k_covered mismatch - fail closed"
assert nrows13 == 1809, "candidate fit-row drift (brwt15 in-frame gaps) - fail closed"
relw13 = project_wmax(relw13_raw, k=K_COVERED_CAND, block=BRWT_BLOCK)
proj_id = float((relw13 - relw13_raw).abs().max())
net13, Wg13, to13 = build_book(df13, relw13, gear=1.0)
i_net13 = net13[net13.index < B.IS_END]
is_sr13, is_mdd13 = sr(i_net13), mdd(i_net13)
ny13 = len(neg_years(i_net13))
relw15_raw = float(relw13_raw["brwt15"])
relw15 = float(relw13["brwt15"])
cfx = float(relw13["CFX4"])
wmax13_sf = float(relw13.max()) * K_COVERED_CAND
gmax13 = float(Wg13.abs().sum(axis=1).max())
log("")
log("CELL: 13-pool (committed 12 + brwt15 R6-convention regen), house rule, gear 1.0")
log("  fit rows=%d k=%d  proj identity=%.3e" % (nrows13, k13, proj_id))
log("  relw15 raw=%.6f projected=%.6f  CFX4=%.1e  Wmax_sf(x12)=%.4fx  grossmax=%.9f" % (relw15_raw, relw15, cfx, wmax13_sf, gmax13))
log("  IS-SR=%.6f (bar 4.198632)  IS-MDD=%.4f pct  IS negyrs=%d" % (is_sr13, is_mdd13 * 100, ny13))
relw13.to_frame("relw").to_csv(OUT + "/arm_13pool_weights.csv")
live = (relw15_raw > 1e-4) or (is_sr13 > BAR + 1e-4)
adm = live and (is_sr13 > BAR) and (is_mdd13 >= -0.06) and (ny13 == 0) and (wmax13_sf <= 2.0 + 1e-9)
verdict = "NO-ADMISSION (IS level) -> honest negative, no reveal (per precommit stop rule)"
if not adm:
    log("NOT ADMITTED (live=%s) -> HONEST NEGATIVE, no reveal (per precommit STOP RULE)." % live)
else:
    f_sr, f_mdd = sr(net13), mdd(net13)
    f_ann_a, f_ann_c = ann_arith(net13) * 100, ann_cagr(net13) * 100
    nyf = neg_years(net13)
    toyr = float(to13.mean() * 252 * B.BPS)
    margin_yr = float((np.maximum(Wg13.abs().sum(axis=1) - 1.0, 0.0) * B.RATE).mean() * 100)
    log("")
    log("REVEAL book: 13-pool at projected fit weights, gear 1.0, n=%d (%s..%s)" % (len(net13), str(net13.index[0].date()), str(net13.index[-1].date())))
    log("  FS SR=%.6f (incumbent 3.751429)  ann arith=%.4f pct  cagr=%.4f pct  MDD=%.4f pct  negyrs=%d" % (f_sr, f_ann_a, f_ann_c, f_mdd * 100, len(nyf)))
    log("  grossmax=%.9f  turnover=%.4f bp/yr  margin=%.4f pct/yr  Wmax_sf=%.4fx (k=12)  CFX4=%.1e" % (gmax13, toyr, margin_yr, wmax13_sf, cfx))
    bins = (("2017-18", "2017", "2018"), ("2019-20", "2019", "2020"), ("2021-22", "2021", "2022"),
            ("2023-24", "2023", "2024"), ("2025-26", "2025", "2026"))
    dsrc = []
    for lbl2, a, b in bins:
        m_c = net13[(net13.index >= a + "-01-01") & (net13.index <= b + "-12-31")]
        m_i = champ[(champ.index >= a + "-01-01") & (champ.index <= b + "-12-31")]
        dsr = sr(m_c) - sr(m_i)
        dsrc.append(dsr)
        log("  bin %s dSR=%+.4f (cand %.4f vs inc %.4f)" % (lbl2, dsr, sr(m_c), sr(m_i)))
    pos = sum(1 for d_ in dsrc if d_ > 0)
    g1 = (f_ann_c >= 20.0) or (f_ann_a >= 20.0)
    g2 = gmax13 <= 1.6 + 1e-9
    g3 = f_mdd >= -0.07
    g4 = len(nyf) == 0
    g5 = cfx == 0.0
    g6 = wmax13_sf <= 2.0 + 1e-9
    g7 = (pos >= 4) and (min(dsrc) >= -0.10) and (f_sr > FS_BAR)
    g8 = (1809 - nrows13) / 1809.0 <= 0.02
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
    pd.DataFrame(dict(ret=net13.values), index=net13.index).to_csv(OUT + "/candidate_13pool_daily.csv")
    relw13.to_frame("relw").to_csv(OUT + "/candidate_13pool_weights.csv")

log("")
log("VERDICT: " + verdict)
champ_sha_post, wgt_sha_post = sha16(CHAMP), sha16(WGT)
log("Champion sha16 post-run: " + champ_sha_post + " / weights " + wgt_sha_post + " (pre==post: " + str((champ_sha_pre == champ_sha_post) and (wgt_sha_pre == wgt_sha_post)) + ")")
assert champ_sha_pre == champ_sha_post and wgt_sha_pre == wgt_sha_post
with open(OUT + "/driver_iter42.log", "w") as fh:
    fh.write(chr(10).join(LOG) + chr(10))
print("LOG WRITTEN: " + OUT + "/driver_iter42.log")
