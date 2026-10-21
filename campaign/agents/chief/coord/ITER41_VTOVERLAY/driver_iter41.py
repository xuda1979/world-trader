import os, sys, hashlib, ast
import numpy as np, pandas as pd
from scipy.optimize import minimize
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign/scripts")
sys.path.insert(0, ROOT)
import rawew13v2_build as B

OUT = ROOT + "/campaign/agents/chief/coord/ITER41_VTOVERLAY"
LOG = []
def log(s=""):
    LOG.append(str(s)); print(s)

W_MAX, SHRINK, BRWT_CAP = 2.0, 0.70, 0.30
BRWT_BLOCK = ("brwt10", "brwt7", "brwt5")
PRECOMMIT_SHA = "63b162ed42baf0c1"
K_COVERED = 11
BAR = 4.198632
FS_BAR = 3.751429
VT_GRID = [0.04, 0.05, 0.06, 0.07, 0.08]
CHAMP = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
WGT = ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv"

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
    a = extract(ROOT + "/campaign/agents/chief/coord/ITER40_DIESCRACK_L/driver_iter40.py")
    c = extract(ROOT + "/campaign/agents/chief/coord/ITER36_DIESCRACK_Z/driver_iter36.py")
    b = extract(__file__)
    for src_name, blk in (("driver_iter40", a), ("driver_iter36", c)):
        miss = [n for n in WANT4 if n not in blk]
        assert not miss, "frozen-block extract failed vs " + src_name + ": " + str(miss)
        diff = [n for n in WANT4 if blk[n] != b[n]]
        assert not diff, "frozen block diverged from " + src_name + ": " + str(diff)
    log("FROZEN-BLOCK check: fit_relw/apply_cap/project_wmax/build_book text-identical to driver_iter40.py AND driver_iter36.py")


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

log(9 * chr(45) + " ITER41 book-level vol-target overlay driver (2026-09-19 session 21). FINDINGS_PRECOMMIT.md sha16 " + PRECOMMIT_SHA + " sealed BEFORE this run.")
_frozen_check()
assert sha16(OUT + "/FINDINGS_PRECOMMIT.md") == PRECOMMIT_SHA, "precommit mutated - fail closed"
champ_sha_pre, wgt_sha_pre = sha16(CHAMP), sha16(WGT)
log("Champion sha16 pre-run: " + champ_sha_pre + " / weights " + wgt_sha_pre + " / precommit " + PRECOMMIT_SHA)

names12 = list(B.NAMES)
df12 = pd.DataFrame(dict((n, B.load(B.PATHS[n]).dropna()) for n in names12))
df12 = df12[df12.index >= "2008-03-31"]

_fit12, nrows12, k12 = fit_relw(df12[df12.index < B.IS_END], names12)
relw12_raw = apply_cap(_fit12)
assert k12 == K_COVERED, "k_covered drift - fail closed"
relw12 = project_wmax(relw12_raw, k=K_COVERED)
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
inc_wmax_sf = float(relw12.max()) * K_COVERED
rowsum_dev = float((Wg12.sum(axis=1) - 1.0).abs().max())
log("ANCHOR A2 projection-identity on incumbent: maxdev=" + repr(ident) + " (need exactly 0)")
log("ANCHOR A2 weights maxdev=%.3e (need <1e-12)" % wdev)
log("ANCHOR A2 bytes   maxdev=%.3e (need <1e-12) n=%d" % (bdev, len(jj)))
log("ANCHOR A2 grossmax=%.9f  fit rows=%d  k_covered=%d  weight-row-sum dev=%.3e" % (gmax, nrows12, k12, rowsum_dev))
log("ANCHOR A2 incumbent Wmax_sf(x11)=%.4fx  IS-SR=%.6f (continuity 4.198632)" % (inc_wmax_sf, is_sr_inc))
assert ident == 0.0, "projection is NOT identity on the feasible incumbent - fail closed"
assert wdev < 1e-12 and bdev < 1e-12 and gmax <= 1.0 + 1e-9
assert nrows12 == 1809, "fit row drift - fail closed"
assert abs(is_sr_inc - 4.198632) < 5e-6, "IS-SR anchor drifted - fail closed"
assert rowsum_dev < 1e-9, "weight rows do not sum to 1 - gross=g_t exactness broken"

def overlay_build(vt):
    if vt is None:
        g = pd.Series(1.0, index=df12.index)
    else:
        sig = net12.expanding(min_periods=60).std().shift(1).replace(0.0, np.nan)
        g = (vt / (sig * np.sqrt(252))).clip(lower=0.0, upper=1.6)
        g = g.fillna(1.0)
    Wp = Wg12.mul(g, axis=0)
    port = (df12.fillna(0).values * Wp.values).sum(axis=1)
    to = Wp.diff().abs().sum(axis=1).fillna(0.0)
    gross_t = Wp.abs().sum(axis=1)
    marg = np.maximum(gross_t - 1.0, 0.0) * B.RATE / 252.0
    net = pd.Series(port, index=df12.index) - to * B.BPS / 1e4 - marg
    return net, g, gross_t, to

netA, gA, grossA, toA = overlay_build(None)
jjA = pd.concat([champ.rename("csv"), netA.rename("reb")], axis=1, join="inner")
bdevA = float((jjA["csv"] - jjA["reb"]).abs().max())
log("ANCHOR A3 g=1.0 (no-overlay limit): bytes maxdev=%.3e (need <1e-12)  to=%.4f bp/yr" % (bdevA, float(toA.mean() * 252 * B.BPS)))
assert bdevA < 1e-12, "anchor does not reproduce committed bytes - STOP"

log("")
log("CELL SWEEP: vt grid, frozen committed weights, g_t=clip(vt/(sigma_{t-1}*sqrt(252)),0,1.6), sigma=expanding(60) std of incumbent net shift(1); cells EXACT (no optimizer)")
log("vt     is_sr     IS-ann pct  IS-MDD pct  negy  gmax     to bp/yr  adm")
rows = []
for vt in VT_GRID:
    net_p, g_p, gross_p, to_p = overlay_build(vt)
    i_net = net_p[net_p.index < B.IS_END]
    i_sr, i_mdd = sr(i_net), mdd(i_net)
    i_ann = ann_arith(i_net) * 100
    ny = len(neg_years(i_net))
    gmax_p = float(gross_p.max())
    toyr = float(to_p.mean() * 252 * B.BPS)
    adm = (gmax_p <= 1.6 + 1e-9) and (i_mdd >= -0.06) and (ny == 0) and (i_sr > BAR + 1e-4)
    lbl = "%.2f" % vt
    g_p.to_frame("g").to_csv(OUT + "/arm_vt" + lbl + "_gpath.csv")
    rows.append(dict(label=lbl, vt=vt, isr=i_sr, iann=i_ann, imdd=i_mdd, ny=ny,
                     gmax=gmax_p, toyr=toyr, adm=adm, net=net_p, g=g_p, gross=gross_p, to=to_p))
    log("%-6s %8.6f  %8.3f    %8.2f    %d/9  %.4f  %7.3f  %s" % (lbl, i_sr, i_ann, i_mdd * 100, ny, gmax_p, toyr, "YES" if adm else "no"))

adm_rows = [r for r in rows if r["adm"]]
log("")
log("ADMITTED: %d / %d (jitter tolerance 1e-4 on the IS bar)" % (len(adm_rows), len(rows)))
verdict = "NO-ADMISSION (IS level) -> honest negative, no reveal (per precommit stop rule)"

if not adm_rows:
    log("NO cell admitted -> HONEST NEGATIVE, no reveal (per precommit STOP RULE).")
else:
    win = sorted(adm_rows, key=lambda r: (-r["isr"], abs(r["vt"] - 0.06), r["vt"]))[0]
    fs = win["net"]
    f_sr, f_mdd = sr(fs), mdd(fs)
    f_ann_a, f_ann_c = ann_arith(fs) * 100, ann_cagr(fs) * 100
    nyf = neg_years(fs)
    grossmax = float(win["gross"].max())
    gmean = float(win["g"].mean())
    pct_over1 = float((win["g"] > 1.0 + 1e-12).mean() * 100)
    pct_cap = float((win["g"] > 1.6 - 1e-12).mean() * 100)
    toyr = float(win["to"].mean() * 252 * B.BPS)
    margin_yr = float((np.maximum(win["gross"] - 1.0, 0.0) * B.RATE).mean() * 100)
    log("")
    log("REVEAL book: vt=%s, committed weights, gear overlay, n=%d (%s..%s)" % (win["label"], len(fs), str(fs.index[0].date()), str(fs.index[-1].date())))
    log("  FS SR=%.6f (incumbent 3.751429)  ann arith=%.4f pct  cagr=%.4f pct  MDD=%.4f pct  negyrs=%d" % (f_sr, f_ann_a, f_ann_c, f_mdd * 100, len(nyf)))
    log("  grossmax=%.9f  g mean=%.4f  pct days g>1=%.2f  pct days at 1.6 cap=%.2f" % (grossmax, gmean, pct_over1, pct_cap))
    log("  turnover=%.4f bp/yr  margin=%.4f pct/yr  Wmax_sf=%.4fx  CFX4 relw=%.1e" % (toyr, margin_yr, inc_wmax_sf, float(relw12["CFX4"])))
    bins = [("2017-18", "2017", "2018"), ("2019-20", "2019", "2020"), ("2021-22", "2021", "2022"),
            ("2023-24", "2023", "2024"), ("2025-26", "2025", "2026")]
    dsrc = []
    for lbl2, a, b in bins:
        m_c = fs[(fs.index >= a + "-01-01") & (fs.index <= b + "-12-31")]
        m_i = champ[(champ.index >= a + "-01-01") & (champ.index <= b + "-12-31")]
        dsr = sr(m_c) - sr(m_i)
        dsrc.append(dsr)
        log("  bin %s dSR=%+.4f (cand %.4f vs inc %.4f)" % (lbl2, dsr, sr(m_c), sr(m_i)))
    pos = sum(1 for d_ in dsrc if d_ > 0)
    g1 = (f_ann_c >= 20.0) or (f_ann_a >= 20.0)
    g2 = grossmax <= 1.6 + 1e-9
    g3 = f_mdd >= -0.07
    g4 = len(nyf) == 0
    g5 = float(relw12["CFX4"]) == 0.0
    g6 = inc_wmax_sf <= 2.0 + 1e-9
    g7 = (pos >= 4) and (min(dsrc) >= -0.10) and (f_sr > FS_BAR)
    g8 = 0.0 <= 0.02
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
    pd.DataFrame(dict(ret=fs.values), index=fs.index).to_csv(OUT + "/candidate_vt" + win["label"] + "_daily.csv")
    win["g"].to_frame("g").to_csv(OUT + "/candidate_vt" + win["label"] + "_gpath.csv")
    log("  NOTE: no candidate WEIGHTS file emitted - the weights ARE the committed champion vector (d2d11c92a98683df); the candidate artifact is the g path.")

log("")
log("VERDICT: " + verdict)
champ_sha_post, wgt_sha_post = sha16(CHAMP), sha16(WGT)
log("Champion sha16 post-run: " + champ_sha_post + " / weights " + wgt_sha_post + " (pre==post: " + str((champ_sha_pre == champ_sha_post) and (wgt_sha_pre == wgt_sha_post)) + ")")
assert champ_sha_pre == champ_sha_post and wgt_sha_pre == wgt_sha_post
with open(OUT + "/driver_iter41.log", "w") as fh:
    fh.write(chr(10).join(LOG) + chr(10))
print("LOG WRITTEN: " + OUT + "/driver_iter41.log")
