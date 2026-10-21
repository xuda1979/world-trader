
# ITER25 driver (2026-09-19, session #7). Per FINDINGS_PRECOMMIT.md sealed 02:44 THIS session.
# Re-adjudication of A5_r7_credit_composite under the CURRENT champion + operator floor.
# Machinery copied verbatim from ITER24_DA/driver_2026-09-19.py (anchor-validated).
import os, sys, hashlib
import numpy as np, pandas as pd
from scipy.optimize import minimize

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign/scripts")
import rawew13v2_build as B

OUT = ROOT + "/campaign/agents/chief/coord/ITER25_CREDIT_READJ"
LOG = []
def log(s=""):
    LOG.append(str(s)); print(s)

W_MAX, SHRINK, BRWT_CAP = 2.0, 0.70, 0.30
BRWT_BLOCK = ("brwt10", "brwt7", "brwt5")

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
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}]
    cap = W_MAX / k
    def solve(bounds):
        best = None
        for w0 in (np.full(k, 1.0 / k),
                   np.maximum(mu, 0.0) / max(float(np.maximum(mu, 0.0).sum()), 1e-12),
                   (1.0 / sd) / (1.0 / sd).sum()):
            r = minimize(neg_sharpe, w0, method="SLSQP", bounds=bounds, constraints=cons,
                         options={"maxiter": 800, "ftol": 1e-12})
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
log("# ITER25 reveal driver (2026-09-19 session #7). Pre-commit FINDINGS_PRECOMMIT.md sealed 02:44 BEFORE this run.")
champ_sha_pre, wgt_sha_pre = sha16(CHAMP), sha16(WGT)
log("# Champion sha16 pre-run: %s / weights %s / precommit d176f7cb8f2f11f5" % (champ_sha_pre, wgt_sha_pre))

names12 = list(B.NAMES)
df12 = pd.DataFrame({n: B.load(B.PATHS[n]).dropna() for n in names12})
df12 = df12[df12.index >= "2008-03-31"]

# ---- ANCHORS (must pass before any candidate) --------------------------------
relw12 = apply_cap(fit_relw(df12[df12.index < B.IS_END], names12))
committed = pd.read_csv(WGT, index_col=0).iloc[:, 0]
wdev = float((relw12 - committed.reindex(relw12.index)).abs().max())
net12, Wg12, _ = build_book(df12, relw12, gear=1.0)
champ = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
j = pd.concat([champ.rename("csv"), net12.rename("reb")], axis=1, join="inner")
bdev = float((j["csv"] - j["reb"]).abs().max())
gmax = float(Wg12.abs().sum(axis=1).max())
isr_net = net12[net12.index < B.IS_END]
is_sr_inc = sr(isr_net)
log("ANCHOR weights maxdev=%.3e (need <1e-12)" % wdev)
log("ANCHOR bytes   maxdev=%.3e (need <1e-12) n=%d" % (bdev, len(j)))
log("ANCHOR grossmax=%.9f  days>1.6: %d" % (gmax, int((Wg12.abs().sum(axis=1) > 1.6 + 1e-9).sum())))
log("ANCHOR incumbent IS-SR=%.6f (ITER22/23/24 continuity 4.198632)" % is_sr_inc)
log("ANCHOR champ ann arith=%.4f%% cagr=%.4f%% SR=%.6f MDD=%.4f%%" %
    (ann_arith(champ) * 100, ann_cagr(champ) * 100, sr(champ), mdd(champ) * 100))
assert wdev < 1e-12 and bdev < 1e-12 and gmax <= 1.0 + 1e-9
assert abs(is_sr_inc - 4.198632) < 5e-6, "IS-SR anchor drifted - fail closed"

# ---- frozen single candidate (pre-commit section 2) ---------------------------
cred = pd.read_csv(CRED, index_col=0, parse_dates=True).iloc[:, 0]
cred.index.name = "date"
log("candidate A5_r7_credit n=%d %s..%s" % (len(cred), str(cred.index[0].date()), str(cred.index[-1].date())))

frame = pd.concat([df12, cred.rename("A5r7credit")], axis=1).sort_index()
frame = frame[frame.index >= "2008-03-31"]
names13 = names12 + ["A5r7credit"]
isr = frame[frame.index < B.IS_END]
relw13 = apply_cap(fit_relw(isr, names13))
net13, Wg13, _ = build_book(frame, relw13, gear=1.0)
i_net = net13[net13.index < B.IS_END]
i_sr, i_mdd = sr(i_net), mdd(i_net)
i_ann = ann_arith(i_net) * 100
ny = len(neg_years(i_net))
wmax = float(relw13.max()) * 13.0
ws = float(relw13["A5r7credit"])
log("")
log("cand          relw[S]     IS-SR    IS-ann%%  IS-MDD%%  negy  Wmax")
log("%-13s %8.5f  %8.4f  %7.3f  %7.2f   %d/9  %6.4fx" %
    ("A5r7credit", ws, i_sr, i_ann, i_mdd * 100, ny, wmax))
filt = (wmax <= 2.0 + 1e-9) and (i_mdd >= -0.06) and (ny == 0)
adm = filt and (i_sr > 4.198632)
log("ADMITTED: %s (filters %s, IS-SR bar %s)" % ("YES" if adm else "NO", filt, i_sr > 4.198632))
relw13.to_frame("relw").to_csv(OUT + "/candidate_A5r7credit_weights.csv")

verdict = "NO-ADMISSION (IS level) -> honest negative, no reveal (per pre-commit)"
if adm:
    fs = net13
    f_sr, f_mdd = sr(fs), mdd(fs)
    f_ann_a, f_ann_c = ann_arith(fs) * 100, ann_cagr(fs) * 100
    nyf = neg_years(fs)
    grossmax = float(Wg13.abs().sum(axis=1).max())
    cfx = float(relw13["CFX4"])
    log("")
    log("REVEAL book: 13-pool + A5r7credit at gear 1.0, n=%d (%s..%s)" %
        (len(fs), str(fs.index[0].date()), str(fs.index[-1].date())))
    log("  FS SR=%.6f (incumbent 3.751429)  ann arith=%.4f%%  cagr=%.4f%%  MDD=%.4f%%  negyrs=%d" %
        (f_sr, f_ann_a, f_ann_c, f_mdd * 100, len(nyf)))
    log("  grossmax=%.9f  Wmax=%.4fx  CFX4 relw=%.1e" % (grossmax, wmax, cfx))
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
    gates = [g1, g2, g3, g4, g5, g6, g7]
    labels = ["1 FS ann>=20%", "2 gross<=1.6", "3 FS MDD>=-7%", "4 0 FS neg yrs",
              "5 CFX4=0", "6 Wmax<=2.0x", "7 OOS police"]
    for l, g in zip(labels, gates):
        log("  GATE %-16s %s" % (l, "PASS" if g else "FAIL"))
    if all(gates):
        verdict = "ADOPTABLE (7/7) -> proceed to full battery per pre-commit section 6"
    elif (not g1) and all([g2, g3, g4, g5, g6, g7]) and f_ann_c >= 0.18:
        # pre-declared deterministic amendment: smallest restoring gear, one pass
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
                           cfx == 0.0, wmax <= 2.0 + 1e-9, g7]
                if all(gates_g) and s_ > 3.751429:
                    verdict = "ADOPTABLE at restored gear %.2f (7/7) -> full battery" % g_
                else:
                    verdict = "REJECT at restored gear %.2f" % g_
                break
        if not done:
            verdict = "REJECT - no gear <=1.30 restores ann>=20pct"
    else:
        fails = [l for l, g in zip(labels, gates) if not g]
        verdict = "REJECT - failed gates: " + ", ".join(fails) + " (no second reveal per pre-commit)"
    pd.DataFrame({"ret": fs.values}, index=fs.index).to_csv(OUT + "/candidate_A5r7credit_daily.csv")

log("")
log("VERDICT: " + verdict)
champ_sha_post, wgt_sha_post = sha16(CHAMP), sha16(WGT)
log("# Champion sha16 post-run: %s / weights %s (pre==post: %s)" %
    (champ_sha_post, wgt_sha_post, (champ_sha_pre == champ_sha_post) and (wgt_sha_pre == wgt_sha_post)))
assert champ_sha_pre == champ_sha_post and wgt_sha_pre == wgt_sha_post
with open(OUT + "/driver_2026-09-19.log", "w") as fh:
    fh.write("\n".join(LOG) + "\n")
print("LOG WRITTEN:", OUT + "/driver_2026-09-19.log")
