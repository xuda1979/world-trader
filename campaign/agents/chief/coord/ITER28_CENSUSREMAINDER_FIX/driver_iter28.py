
# ITER28 census-remainder FILTER-REPAIR driver (2026-09-19, session #10).
# Repair of the ITER27 disclosed defect: Wmax filter x13 -> x k_covered (scale-free,
# campaign-recorded #117/#117b convention). ALL else verbatim ITER27.
# Pre-commit: FINDINGS_PRECOMMIT.md sha16 ccd882e6391f3742 sealed BEFORE this run.
# ITER24_DA driver_2026-09-19.py verbatim + two disclosed changes (see pre-commit):
#   change 1: kind "ret" for the nokcarry two-leg + fail-closed NOK unit gate
#   change 2: per-candidate G8 fit-row shrink < 2 pct (#117b landed hygiene);
#             fit_relw returns (relw, fit_rows) so both anchor and candidates measure rows
import os, sys, hashlib
import numpy as np, pandas as pd
from scipy.optimize import minimize

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign/scripts")
import rawew13v2_build as B

OUT = ROOT + "/campaign/agents/chief/coord/ITER28_CENSUSREMAINDER_FIX"
os.makedirs(OUT + "/sleeves", exist_ok=True)
LOG = []
def log(s=""):
    LOG.append(str(s)); print(s)

W_MAX, SHRINK, BRWT_CAP = 2.0, 0.70, 0.30
BRWT_BLOCK = ("brwt10", "brwt7", "brwt5")
K, CAD, VT, VCAP, SBPS, SSTART = 378, 42, 0.12, 5.0, 6.4, "2007-01-01"

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

def build_book(frame, relw, gear=1.0):
    nav = (1 + frame.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(relw)
    Wg = d2 * (gear / len(relw))
    port = (frame.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    net = pd.Series(port, index=frame.index) - to * B.BPS / 1e4 - max(gear - 1, 0) * B.RATE / 252
    return net, Wg, to

def load_series(rel):
    df = pd.read_csv(ROOT + "/tools/quant/data/" + rel, index_col=0, parse_dates=True)
    col = "close" if "close" in df.columns else "value"
    s = df[col].astype(float)
    return s[~s.index.duplicated(keep="last")].sort_index()

def trend_sleeve(s, kind, dur=None):
    if kind == "rates":
        y = s / 100.0
        tr = (-dur * y.diff() + y / 252.0).dropna()
    elif kind == "ret":
        tr = s.dropna()
    else:
        tr = s.pct_change().dropna()
    sig = (tr.rolling(K).mean() > 0).astype(float)
    W = sig.iloc[::CAD].reindex(tr.index).ffill().fillna(0.0)
    gross = (W.shift(1) * tr)[SSTART:]
    turn = (W.shift(1) - W.shift(2)).abs()[SSTART:].fillna(0.0)
    net = (gross - turn * SBPS / 1e4).dropna()
    lev = (VT / np.sqrt(252) / net.expanding(60).std().shift(1)).clip(0, VCAP).fillna(0.0)
    return (net * lev).dropna()

CHAMP = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
WGT   = ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv"
SHA_PRE = sha16(CHAMP); WSHA_PRE = sha16(WGT)
log("# ITER28 census-remainder FILTER-REPAIR reveal driver (2026-09-19). Pre-commit sha16 9c1f22cba582364a sealed BEFORE this run.")
log("# Champion sha16 pre-run: %s / weights %s" % (SHA_PRE, WSHA_PRE))

names12 = list(B.NAMES)
df12 = pd.DataFrame(dict((n, B.load(B.PATHS[n]).dropna()) for n in names12))
df12 = df12[df12.index >= "2008-03-31"]

# ---- ANCHORS (fail-closed, before any candidate) ------------------------------
relw12, nrows12, k12 = fit_relw(df12[df12.index < B.IS_END], names12)
relw12 = apply_cap(relw12)
committed = pd.read_csv(WGT, index_col=0).iloc[:, 0]
wdev = float((relw12 - committed.reindex(relw12.index)).abs().max())
net12, Wg12, _ = build_book(df12, relw12, gear=1.0)
champ = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
j = pd.concat([champ.rename("csv"), net12.rename("reb")], axis=1, join="inner")
bdev = float((j["csv"] - j["reb"]).abs().max())
gmax = float(Wg12.abs().sum(axis=1).max())
isr_net = net12[net12.index < B.IS_END]
is_sr_inc = sr(isr_net)
log("ANCHOR weights maxdev=%.3e (need <1e-12)  12-pool fit rows=%d k_covered=%d" % (wdev, nrows12, k12))
log("ANCHOR bytes   maxdev=%.3e (need <1e-12)  n=%d" % (bdev, len(j)))
log("ANCHOR grossmax=%.9f  days>1.6: %d" % (gmax, int((Wg12.abs().sum(axis=1) > 1.6 + 1e-9).sum())))
log("ANCHOR incumbent IS-SR=%.6f (continuity 4.198632)  IS-ann(arith)=%.4f%%" %
    (is_sr_inc, ann_arith(isr_net) * 100))
assert wdev < 1e-12 and bdev < 1e-12 and gmax <= 1.0 + 1e-9
assert abs(is_sr_inc - 4.198632) < 5e-6, "IS-SR continuity broken - STOP"

# ---- change 1: NOK unit gate (fail-closed BEFORE any candidate) ----------------
nok = load_series("dm_rates/nok_policy_rate.csv")   # ANNUAL percent
fxn = load_series("fx_hist/USD_NOK.csv")            # NOK per USD
tail_ann = (1.0 + float(nok.tail(60).mean()) / 100.0 / 252.0) ** 252 - 1
head_ann = (1.0 + float(nok.head(60).mean()) / 100.0 / 252.0) ** 252 - 1
log("NOK unit gate: tail60 ann=%.4f%% (need 2..8)  head60 ann=%.4f%% (need 3..15)" %
    (tail_ann * 100, head_ann * 100))
assert 0.02 <= tail_ann <= 0.08 and 0.03 <= head_ann <= 0.15, "NOK unit check FAILED - fail closed"
jn = pd.concat([(nok / 100.0 / 252.0).rename("y"), fxn.rename("fx")], axis=1, join="inner").dropna()
tr_nok = jn["y"] - jn["fx"].diff() / jn["fx"]
log("nokcarry joint tr: n=%d %s..%s" % (len(tr_nok), str(tr_nok.index[0].date()), str(tr_nok.index[-1].date())))

# ---- frozen candidate set (pre-commit; 30 = 29 ETF + 1 nokcarry) ---------------
CANDS = []
for n in ["DIA", "EEM", "EFA", "EMB", "EWT", "FXI", "GLD", "HYG", "IEF", "IWM", "JNK",
          "LQD", "QQQ", "SHY", "SLV", "SMH", "SPY", "TLT", "TSM", "VNQ",
          "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]:
    CANDS.append(("F1", n.lower() + "_etf", "cboe_hist/" + n + ".csv", "px", None))
CANDS.append(("F2", "nokcarry", None, "ret", None))
assert len(CANDS) == 30

log("")
log("cand                  fam  relw[S]     IS-SR    IS-ann%  IS-MDD%  negy  Wmax_sf  rows g8shr    adm")
rows = []
for fam, name, rel, kind, dur in CANDS:
    if kind == "ret":
        r = trend_sleeve(tr_nok, "ret")
    else:
        r = trend_sleeve(load_series(rel), kind, dur)
    r.index.name = "date"
    pd.DataFrame(dict(ret=r.values), index=r.index).to_csv(OUT + "/sleeves/" + name + ".csv")
    frame = pd.concat([df12, r.rename(name)], axis=1).sort_index()
    frame = frame[frame.index >= "2008-03-31"]
    names13 = names12 + [name]
    isr = frame[frame.index < B.IS_END]
    relw13, nrows13, k13 = fit_relw(isr, names13)
    relw13 = apply_cap(relw13)
    g8 = (nrows12 - nrows13) / float(nrows12)
    net13, Wg13, _ = build_book(frame, relw13, gear=1.0)
    i_net = net13[net13.index < B.IS_END]
    i_sr, i_mdd = sr(i_net), mdd(i_net)
    i_ann = ann_arith(i_net) * 100
    ny = len(neg_years(i_net))
    wmax = float(relw13.max()) * float(k13)
    ws = float(relw13[name])
    filt = (wmax <= 2.0 + 1e-9) and (i_mdd >= -0.06) and (ny == 0) and (g8 < 0.02)
    adm = filt and (i_sr > 4.198632)
    rows.append(dict(fam=fam, name=name, ws=ws, isr=i_sr, iann=i_ann, imdd=i_mdd * 100,
                     ny=ny, wmax=wmax, g8=g8, k=k13, adm=adm, relw=relw13, frame=frame, net=net13))
    log("%-20s %s  %8.5f  %8.4f  %7.3f  %7.2f   %d/9  %6.4fx  %4d %5.2f%%  %s" %
        (name, fam, ws, i_sr, i_ann, i_mdd * 100, ny, wmax, nrows13, g8 * 100,
         "YES" if adm else "no"))

adm_rows = [r for r in rows if r["adm"]]
log("")
log("ADMITTED: %d / 30" % len(adm_rows))

# ---- selection + SINGLE reveal -------------------------------------------------
if not adm_rows:
    log("NO candidate admitted -> HONEST NEGATIVE, no reveal (per pre-commit STOP RULE).")
else:
    adm_sorted = sorted(adm_rows, key=lambda r: (-r["isr"], -r["ws"], r["name"]))
    win = adm_sorted[0]
    log("GLOBAL ARGMAX (IS-only): %s  IS-SR=%.6f relw[S]=%.5f g8=%.3f%%" %
        (win["name"], win["isr"], win["ws"], win["g8"] * 100))
    net13 = win["net"]; relw13 = win["relw"]; frame = win["frame"]
    nav = (1 + frame.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw13, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(relw13)
    Wg13 = d2 * (1.0 / len(relw13))
    fs = net13
    f_sr, f_mdd = sr(fs), mdd(fs)
    f_ann_a, f_ann_c = ann_arith(fs) * 100, ann_cagr(fs) * 100
    ny = neg_years(fs)
    grossmax = float(Wg13.abs().sum(axis=1).max())
    wmax = float(relw13.max()) * float(win["k"])
    cfx = float(relw13["CFX4"])
    log("")
    log("REVEAL book: 13-pool + %s at gear 1.0, n=%d (%s..%s)" %
        (win["name"], len(fs), str(fs.index[0].date()), str(fs.index[-1].date())))
    log("  FS SR=%.6f (incumbent 3.751429)  ann arith=%.4f%%  cagr=%.4f%%  MDD=%.4f%%  negyrs=%d  worst=%s" %
        (f_sr, f_ann_a, f_ann_c, f_mdd * 100, len(ny), ("%.2f%%" % (float(ny.min()) * 100)) if len(ny) else "n/a"))
    log("  grossmax=%.9f  Wmax=%.4fx  CFX4 relw=%.1e" % (grossmax, wmax, cfx))
    g1 = (f_ann_c >= 0.20) or (f_ann_a >= 0.20)
    g2 = grossmax <= 1.6 + 1e-9
    g3 = f_mdd >= -0.07
    g4 = len(ny) == 0
    g5 = cfx == 0.0
    g6 = wmax <= 2.0 + 1e-9
    bins = [("2017-18", "2017", "2018"), ("2019-20", "2019", "2020"), ("2021-22", "2021", "2022"),
            ("2023-24", "2023", "2024"), ("2025-26", "2025", "2026")]
    dsrc, detail = [], []
    for lbl, a, b in bins:
        m_c = fs[(fs.index >= a + "-01-01") & (fs.index <= b + "-12-31")]
        m_i = champ[(champ.index >= a + "-01-01") & (champ.index <= b + "-12-31")]
        dsr = sr(m_c) - sr(m_i)
        dsrc.append(dsr)
        detail.append("  bin %s dSR=%+.4f (cand %.4f vs inc %.4f)" % (lbl, dsr, sr(m_c), sr(m_i)))
    pos = sum(1 for d in dsrc if d > 0)
    g7 = (pos >= 4) and (min(dsrc) >= -0.10) and (f_sr > 3.751429)
    for d in detail: log(d)
    gates = [g1, g2, g3, g4, g5, g6, g7]
    labels = ["1 FS ann>=20%", "2 gross<=1.6", "3 FS MDD>=-7%", "4 0 FS neg yrs",
              "5 CFX4=0", "6 Wmax<=2.0x", "7 OOS police"]
    for l, g in zip(labels, gates):
        log("  GATE %-16s %s" % (l, "PASS" if g else "FAIL"))
    ok = all(gates)
    log("")
    log("VERDICT: " + ("ADOPTABLE (7/7) -- proceed to archive+re-pin wave per pre-commit"
                       if ok else "REJECT -- honest negative, no second reveal (per pre-commit)"))
    pd.DataFrame(dict(ret=fs.values), index=fs.index).to_csv(OUT + "/candidate_" + win["name"] + "_daily.csv")
    relw13.to_frame("relw").to_csv(OUT + "/candidate_" + win["name"] + "_weights.csv")

SHA_POST = sha16(CHAMP); WSHA_POST = sha16(WGT)
log("")
log("# Champion sha16 post-run: %s / weights %s" % (SHA_POST, WSHA_POST))
assert SHA_POST == SHA_PRE and WSHA_POST == WSHA_PRE, "champion bytes changed - FAIL"
with open(OUT + "/driver_iter28.log", "w") as fh:
    fh.write("\n".join(LOG) + "\n")
print("LOG WRITTEN:", OUT + "/driver_iter28.log")
