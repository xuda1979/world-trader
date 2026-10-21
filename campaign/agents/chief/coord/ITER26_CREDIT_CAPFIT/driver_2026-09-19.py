
# ITER26 driver (2026-09-19, session #9). Per FINDINGS_PRECOMMIT.md sealed THIS session
# (sha16 4d3373c65598a1cb, written before this driver was invoked).
# Repair-of-record: #118 documented order-of-operations defect (apply_brwt_cap pro-rata
# redistribution runs AFTER fit_relw's 2/k bounded solve with NO post-clamp). Machinery
# copied verbatim from ITER25_CREDIT_READJ/driver_2026-09-19.py + ONE declared repair
# step (project_wmax_invariant), per pre-commit section 3.
import os, sys, hashlib
import numpy as np, pandas as pd
from scipy.optimize import minimize

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign/scripts")
import rawew13v2_build as B

OUT = ROOT + "/campaign/agents/chief/coord/ITER26_CREDIT_CAPFIT"
LOG = []
def log(s=""):
    LOG.append(str(s)); print(s)

W_MAX, SHRINK, BRWT_CAP = 2.0, 0.70, 0.30
BRWT_BLOCK = ("brwt10", "brwt7", "brwt5")
PRECOMMIT_SHA = "4d3373c65598a1cb"

def sr(x): return float(x.mean() / x.std(ddof=1) * np.sqrt(252))
def mdd(x):
    nav = (1 + x).cumprod(); return float((nav / nav.cummax() - 1).min())
def ann_arith(x): return float(x.mean() * 252)
def ann_cagr(x): return float((1 + x).prod() ** (252 / len(x)) - 1)
def neg_years(x):
    yr = x.groupby(x.index.year).apply(lambda v: (1 + v).prod() - 1)
    return yr[yr < 0]
def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

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
    return relw

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
    # Pre-commit section 3 REPAIR STEP: deterministic parameter-free water-filling into
    # the invariant set share <= 2/k. Receivers: non-block, non-CFX4, strictly below
    # cap. Identity on any already-feasible vector (loop body never fires).
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

CHAMP = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
WGT   = ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv"
CRED  = ROOT + "/campaign/agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv"
ITER25_W = ROOT + "/campaign/agents/chief/coord/ITER25_CREDIT_READJ/candidate_A5r7credit_weights.csv"
log("# ITER26 reveal driver (2026-09-19 session #9). FINDINGS_PRECOMMIT.md sha16 %s sealed BEFORE this run." % PRECOMMIT_SHA)
assert sha16(OUT + "/FINDINGS_PRECOMMIT.md") == PRECOMMIT_SHA, "precommit mutated - fail closed"
champ_sha_pre, wgt_sha_pre = sha16(CHAMP), sha16(WGT)
log("# Champion sha16 pre-run: %s / weights %s / precommit %s" % (champ_sha_pre, wgt_sha_pre, PRECOMMIT_SHA))

names12 = list(B.NAMES)
df12 = pd.DataFrame({n: B.load(B.PATHS[n]).dropna() for n in names12})
df12 = df12[df12.index >= "2008-03-31"]

# ---- ANCHORS (pre-commit section 3) ------------------------------------------
relw12_raw = apply_cap(fit_relw(df12[df12.index < B.IS_END], names12))
relw12 = project_wmax(relw12_raw, k=12)
ident = float((relw12 - relw12_raw).abs().max())
committed = pd.read_csv(WGT, index_col=0).iloc[:, 0]
wdev = float((relw12 - committed.reindex(relw12.index)).abs().max())
net12, Wg12, _ = build_book(df12, relw12, gear=1.0)
champ = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
j = pd.concat([champ.rename("csv"), net12.rename("reb")], axis=1, join="inner")
bdev = float((j["csv"] - j["reb"]).abs().max())
gmax = float(Wg12.abs().sum(axis=1).max())
isr_net12 = net12[net12.index < B.IS_END]
is_sr_inc = sr(isr_net12)
log("ANCHOR projection-identity on incumbent: maxdev=%.3e (need exactly 0)" % ident)
log("ANCHOR weights maxdev=%.3e (need <1e-12)" % wdev)
log("ANCHOR bytes   maxdev=%.3e (need <1e-12) n=%d" % (bdev, len(j)))
log("ANCHOR grossmax=%.9f  days>1.6: %d" % (gmax, int((Wg12.abs().sum(axis=1) > 1.6 + 1e-9).sum())))
log("ANCHOR incumbent IS-SR=%.6f (ITER22/23/24/25 continuity 4.198632)" % is_sr_inc)
log("ANCHOR champ ann arith=%.4f%% cagr=%.4f%% SR=%.6f MDD=%.4f%%" %
    (ann_arith(champ) * 100, ann_cagr(champ) * 100, sr(champ), mdd(champ) * 100))
assert ident == 0.0, "projection is NOT identity on the feasible incumbent - fail closed"
assert wdev < 1e-12 and bdev < 1e-12 and gmax <= 1.0 + 1e-9
assert abs(is_sr_inc - 4.198632) < 5e-6, "IS-SR anchor drifted - fail closed"

# ---- frozen candidate (pre-commit section 2) ----------------------------------
cred = pd.read_csv(CRED, index_col=0, parse_dates=True).iloc[:, 0]
cred.index.name = "date"
log("candidate A5_r7_credit n=%d %s..%s" % (len(cred), str(cred.index[0].date()), str(cred.index[-1].date())))

frame = pd.concat([df12, cred.rename("A5r7credit")], axis=1).sort_index()
frame = frame[frame.index >= "2008-03-31"]
names13 = names12 + ["A5r7credit"]
isr = frame[frame.index < B.IS_END]

# G8 fit-window shrink (pre-commit section 3): complete-row shrink of the fit window.
# DRIVER FIX (disclosed in FINDINGS; definition unchanged, made computable): CFX4 has
# ZERO coverage >= 2008-03-31 (dead feed), so a naive all-12-column dropna counts 0 rows
# (ZeroDivisionError caught fail-closed on first run). fit_relw itself defines the fit
# frame via coverage (have = notna>0 names), so the inner-join row counts are
# coverage-restricted identically: 12-pool over have12 (11 names), 13-pool over have13
# (11 + credit). Bar (<= 2%) untouched.
have12 = [n for n in names12 if isr[n].notna().sum() > 0]
have13 = [n for n in names13 if isr[n].notna().sum() > 0]
log("G8 coverage sets: have12=%d names (CFX4 out: %s), have13=%d names" %
    (len(have12), "CFX4" not in have12, len(have13)))
n12 = len(isr[have12].dropna()); n13 = len(isr[have13].dropna())
assert n12 > 0, "empty 12-pool fit window - fail closed"
shrink_g8 = 1.0 - n13 / float(n12)
log("G8 fit-window complete rows: 12-pool %d -> 13-pool %d, shrink=%.4f%% (bar <= 2%%)" %
    (n12, n13, shrink_g8 * 100))

# REPRODUCTION anchor: unprojected house order must reproduce ITER25's vector
relw13_pre = apply_cap(fit_relw(isr, names13))
r25 = pd.read_csv(ITER25_W, index_col=0).iloc[:, 0]
rdev = float((relw13_pre - r25.reindex(relw13_pre.index)).abs().max())
net13_pre, _, _ = build_book(frame, relw13_pre, gear=1.0)
is_sr_pre = sr(net13_pre[net13_pre.index < B.IS_END])
log("REPRO unprojected 13-pool maxdev vs ITER25=%.3e (need <1e-9); IS-SR=%.4f (ITER25 4.2575); Wmax=%.4fx (ITER25 2.4745x)" %
    (rdev, is_sr_pre, float(relw13_pre.max()) * 13.0))
assert rdev < 1e-9, "machinery does not reproduce ITER25 - fail closed"

# THE candidate: house order + the one declared repair step
relw13 = project_wmax(relw13_pre, k=13)
viol = [n for n in relw13.index if float(relw13_pre[n]) > 2.0 / 13 + 1e-12]
moved = (relw13 - relw13_pre).abs()
det = ", ".join("%s %+.6f" % (n, float(relw13[n] - relw13_pre[n]))
                for n in relw13.index[abs(relw13 - relw13_pre) > 1e-12])
log("REPAIR clamped violators: %s ; total moved mass %.6f" % (",".join(viol) or "none", float(moved.sum())))
log("REPAIR relw deltas: %s" % (det or "none"))
assert float(relw13.max()) * 13.0 <= 2.0 + 1e-9, "repair failed its own invariant"
net13, Wg13, _ = build_book(frame, relw13, gear=1.0)
i_net = net13[net13.index < B.IS_END]
i_sr, i_mdd = sr(i_net), mdd(i_net)
i_ann = ann_arith(i_net) * 100
ny = len(neg_years(i_net))
wmax = float(relw13.max()) * 13.0
ws = float(relw13["A5r7credit"])
sum_ = float(relw13.sum()); cfx = float(relw13["CFX4"])
wmax_eff = float((relw13 / (sum_ - cfx)).max()) * 13.0
log("")
log("cand          relw[S]     IS-SR    IS-ann%%  IS-MDD%%  negy  Wmax(raw) Wmax(eff)")
log("%-13s %8.5f  %8.4f  %7.3f  %7.2f   %d/9  %6.4fx   %6.4fx" %
    ("A5r7credit", ws, i_sr, i_ann, i_mdd * 100, ny, wmax, wmax_eff))
filt = (wmax <= 2.0 + 1e-9) and (i_mdd >= -0.06) and (ny == 0)
adm = filt and (i_sr > 4.198632)
log("ADMITTED: %s (filters %s, IS-SR bar %s)" % ("YES" if adm else "NO", filt, i_sr > 4.198632))
relw13.to_frame("relw").to_csv(OUT + "/candidate_credit_at_cap_weights.csv")

verdict = "NO-ADMISSION (IS level) -> honest negative, no reveal (per pre-commit)"
if adm:
    fs = net13
    f_sr, f_mdd = sr(fs), mdd(fs)
    f_ann_a, f_ann_c = ann_arith(fs) * 100, ann_cagr(fs) * 100
    nyf = neg_years(fs)
    grossmax = float(Wg13.abs().sum(axis=1).max())
    log("")
    log("REVEAL book: 13-pool + A5r7credit at invariant cap, gear 1.0, n=%d (%s..%s)" %
        (len(fs), str(fs.index[0].date()), str(fs.index[-1].date())))
    log("  FS SR=%.6f (incumbent 3.751429)  ann arith=%.4f%%  cagr=%.4f%%  MDD=%.4f%%  negyrs=%d" %
        (f_sr, f_ann_a, f_ann_c, f_mdd * 100, len(nyf)))
    log("  grossmax=%.9f  Wmax=%.4fx  CFX4 relw=%.1e  G8 shrink=%.4f%%" % (grossmax, wmax, cfx, shrink_g8 * 100))
    bins = [("2017-18", "2017", "2018"), ("2019-20", "2019", "2020"), ("2021-22", "2021", "2022"),
            ("2023-24", "2023", "2024"), ("2025-26", "2025", "2026")]
    dsrc = []
    for lbl, a, b in bins:
        m_c = fs[(fs.index >= a + "-01-01") & (fs.index <= b + "-12-31")]
        m_i = champ[(champ.index >= a + "-01-01") & (champ.index <= b + "-12-31")]
        dsr = sr(m_c) - sr(m_i)
        dsrc.append(dsr)
        log("  bin %s dSR=%+.4f (cand %.4f vs inc %.4f)" % (lbl, dsr, sr(m_c), sr(m_i)))
    pos = sum(1 for d_ in dsrc if d_ > 0)
    g1 = (f_ann_c >= 0.20) or (f_ann_a >= 0.20)
    g2 = grossmax <= 1.6 + 1e-9
    g3 = f_mdd >= -0.07
    g4 = len(nyf) == 0
    g5 = cfx == 0.0
    g6 = wmax <= 2.0 + 1e-9
    g7 = (pos >= 4) and (min(dsrc) >= -0.10) and (f_sr > 3.751429)
    g8 = shrink_g8 <= 0.02
    gates = [g1, g2, g3, g4, g5, g6, g7, g8]
    labels = ["1 FS ann>=20%", "2 gross<=1.6", "3 FS MDD>=-7%", "4 0 FS neg yrs",
              "5 CFX4=0", "6 Wmax<=2.0x", "7 OOS police", "8 fit-window shrink<=2%"]
    for l, g in zip(labels, gates):
        log("  GATE %-24s %s" % (l, "PASS" if g else "FAIL"))
    if all(gates):
        verdict = "ADOPTABLE (8/8) -> proceed to full battery per pre-commit section 6"
    elif (not g1) and all([g2, g3, g4, g5, g6, g7, g8]) and f_ann_c >= 0.18:
        done = False
        for step in range(1, 7):
            g_ = 1.0 + 0.05 * step
            netg, Wgg, _ = build_book(frame, relw13, gear=g_)
            c_ = ann_cagr(netg); s_ = sr(netg); m_ = mdd(netg)
            ny_g = len(neg_years(netg)); gmx = float(Wgg.abs().sum(axis=1).max())
            log("  AMEND gear=%.2f cagr=%.4f%% SR=%.6f MDD=%.4f%% negy=%d grossmax=%.6f" %
                (g_, c_ * 100, s_, m_ * 100, ny_g, gmx))
            if c_ >= 0.20:
                done = True
                gates_g = [c_ >= 0.20, gmx <= 1.6 + 1e-9, m_ >= -0.07, ny_g == 0,
                           cfx == 0.0, wmax <= 2.0 + 1e-9, g7, g8]
                if all(gates_g) and s_ > 3.751429:
                    verdict = "ADOPTABLE at restored gear %.2f (8/8) -> full battery" % g_
                else:
                    verdict = "REJECT at restored gear %.2f" % g_
                break
        if not done:
            verdict = "REJECT - no gear <=1.30 restores ann>=20pct"
    else:
        fails = [l for l, g in zip(labels, gates) if not g]
        verdict = "REJECT - failed gates: " + ", ".join(fails) + " (no second reveal per pre-commit)"
    pd.DataFrame(dict(ret=fs.values), index=fs.index).to_csv(OUT + "/candidate_credit_at_cap_daily.csv")

log("")
log("VERDICT: " + verdict)
champ_sha_post, wgt_sha_post = sha16(CHAMP), sha16(WGT)
log("# Champion sha16 post-run: %s / weights %s (pre==post: %s)" %
    (champ_sha_post, wgt_sha_post, (champ_sha_pre == champ_sha_post) and (wgt_sha_pre == wgt_sha_post)))
assert champ_sha_pre == champ_sha_post and wgt_sha_pre == wgt_sha_post
with open(OUT + "/driver_2026-09-19.log", "w") as fh:
    fh.write("\n".join(LOG) + "\n")
print("LOG WRITTEN:", OUT + "/driver_2026-09-19.log")
