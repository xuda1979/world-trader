import os, sys, hashlib, ast
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign/scripts")
sys.path.insert(0, ROOT)
import rawew13v2_build as B

sys.path.insert(0, ROOT + "/campaign/agents/A3_xs_quality")
import campaign.harness.data as _D

def _panel_skip_manifest(extended=False):
    # D17 mitigation (FINDINGS_PRECOMMIT.md): twelve_big/manifest.csv (untracked,
    # landed 2026-09-08) breaks panel(); skipping it restores the original 298-CSV
    # panel byte-faithfully (sleeve predates the manifest; A1 regen-vs-saved 1e-16).
    d = _D.EXT if extended else _D.PANEL
    out = {}
    for f in os.listdir(d):
        if f.endswith(".csv") and f != "manifest.csv":
            df = pd.read_csv(os.path.join(d, f), parse_dates=["date"], index_col="date")
            out[f[:-4]] = df
    return out

_D.panel = _panel_skip_manifest

import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("a3_engine", ROOT + "/campaign/agents/A3_xs_quality/engine.py")
_a3 = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_a3)
assert _a3.__file__.endswith("A3_xs_quality/engine.py")
month_ends, strategy_ret = _a3.month_ends, _a3.strategy_ret

OUT = ROOT + "/campaign/agents/chief/coord/ITER38_DUALMOM_BAND"
LOG = []
def log(s=""):
    LOG.append(str(s)); print(s)

W_MAX, SHRINK, BRWT_CAP = 2.0, 0.70, 0.30
BRWT_BLOCK = ("brwt10", "brwt7", "brwt5")
PRECOMMIT_SHA = "8a1c571db36f9770"
K_COVERED = 11
BAR = 4.198632
FS_BAR = 3.751429
GRID = [0.01, 0.02, 0.03, 0.04, 0.05]
ANCHOR_BAND = 0.03
FRED = ROOT + "/tools/quant/hedge_fund_strats/data_fred"
NEW = ROOT + "/tools/quant/data/newdata"
EIA = ROOT + "/tools/quant/data/eia_weekly"
CHAMP = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
WGT = ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv"
QA_REL = "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv"

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
def dload(pstr):
    df = pd.read_csv(pstr, index_col=0, parse_dates=True)
    v = df.iloc[:, 0]
    return pd.to_numeric(v, errors="coerce").dropna()
def fred(name, src=FRED):
    s = dload(src + "/" + name + ".csv")
    return s[~s.index.duplicated(keep="last")].sort_index()

_CTX = None
WIN_F, FRAC_F = 200, 1.0 / 3.0
def dm_ctx():
    # Band-independent precomputation, numerically identical to the QA script module
    # setup (px, rets, MES, sig 21/252, FF market cumprod, MA200 WIN=200 min_periods=WIN).
    global _CTX
    if _CTX is None:
        px = _D.closes()
        rets = px.pct_change()
        MES = [d for d in month_ends(rets) if d in px.index]
        sig = px.shift(21) / px.shift(252) - 1.0
        ff = _D.ff_factors()
        mkt = (1 + ff["Mkt-RF"] + ff["RF"]).cumprod()
        ma = mkt.rolling(WIN_F, min_periods=WIN_F).mean()
        _CTX = (px, rets, MES, sig, mkt, ma)
    return _CTX

def dualmom_build(band):
    # Re-typed verbatim from campaign/scripts/QA_dualmom_band121.py (importing it would
    # fire module-level save_sleeve onto live sleeves). Only `band` varies; WIN/FRAC and
    # the vol-target (engine defaults 0.10/expanding60/cap5) are frozen. Costs 6.4bps
    # FULL |dW| one-side (CAMP_COST R2 costfix convention = the committed CSV vintage).
    px, rets, MES, sig, mkt, ma = dm_ctx()
    g = pd.Series(np.where(mkt > ma * (1 + band), 1.0,
                  np.where(mkt < ma * (1 - band), 0.0, np.nan)), index=mkt.index)
    g = g.reindex(px.index).ffill().fillna(0.0)
    W = pd.DataFrame(0.0, index=rets.index, columns=rets.columns)
    for t in MES:
        if t not in sig.index or g.loc[t] <= 0:
            continue
        row = sig.loc[t].dropna()
        if len(row) < 10:
            continue
        row = row.sort_values()
        nl = max(int(np.floor(len(row) * FRAC_F)), 1)
        for s in row.index[-nl:]:
            W.loc[t, s] = 1.0 / nl
    COST_STD = 6.4
    idx = rets.index
    w = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    prev = pd.Series(0.0, index=rets.columns)
    turn = pd.Series(0.0, index=idx)
    pos_of = {d: idx.get_loc(d) for d in MES}
    for i, t in enumerate(MES):
        neww = W.loc[t]
        p = pos_of[t]
        if p + 1 < len(idx):
            turn.iloc[p + 1] = (neww - prev).abs().sum()
            nxt_p = pos_of[MES[i + 1]] + 1 if i + 1 < len(MES) else len(idx)
            w.iloc[p + 1: nxt_p] = neww.values
            prev = neww
    net = (w * rets.fillna(0.0)).sum(axis=1) - turn * COST_STD / 1e4
    nz = w.abs().sum(axis=1)
    start = nz[nz > 0].index[0]
    return strategy_ret(net, start)

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

def _frozen_check():
    WANT = ("fit_relw", "apply_cap", "project_wmax", "build_book")
    def extract(path):
        src = open(path).read()
        tree = ast.parse(src)
        out = {}
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in WANT:
                out[node.name] = ast.get_source_segment(src, node)
        return out
    for ref in ("ITER36_DIESCRACK_Z/driver_iter36.py", "ITER37_TSMOM_MAW/driver_iter37.py"):
        a = extract(ROOT + "/campaign/agents/chief/coord/" + ref)
        b = extract(__file__)
        missing = [n for n in WANT if n not in a or n not in b]
        assert not missing, "frozen-block extract failed vs " + ref + ": " + str(missing)
        bad = [n for n in WANT if a[n] != b[n]]
        assert not bad, "frozen block diverged from " + ref + ": " + str(bad)
    log("FROZEN-BLOCK check vs driver_iter36.py + driver_iter37.py: fit_relw/apply_cap/project_wmax/build_book text-identical")
from scipy.optimize import minimize

log(9 * chr(45) + " ITER38 dualmom-band driver (2026-09-19 session 19). FINDINGS_PRECOMMIT.md sha16 " + PRECOMMIT_SHA + " sealed BEFORE this run.")
_frozen_check()
assert sha16(OUT + "/FINDINGS_PRECOMMIT.md") == PRECOMMIT_SHA, "precommit mutated - fail closed"
champ_sha_pre, wgt_sha_pre = sha16(CHAMP), sha16(WGT)
log("Champion sha16 pre-run: " + champ_sha_pre + " / weights " + wgt_sha_pre + " / precommit " + PRECOMMIT_SHA)

names12 = list(B.NAMES)
df12 = pd.DataFrame(dict((n, B.load(B.PATHS[n]).dropna()) for n in names12))
df12 = df12[df12.index >= "2008-03-31"]

saved = dload(ROOT + "/" + QA_REL)
gen0 = dualmom_build(ANCHOR_BAND)
j0 = pd.concat([gen0.rename("gen"), saved.rename("saved")], axis=1, join="inner").dropna()
a1dev = float((j0["gen"] - j0["saved"]).abs().max())
log("ANCHOR A1 regen BAND=0.03 vs saved: maxdev=%.6e (inner n=%d)" % (a1dev, len(j0)))
assert a1dev < 1e-12, "re-typed generator is not the saved stream source - STOP"
anchor_idx = gen0.index

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
dc_share = float((relw12 / relw12.sum())["dualmom"])
log("ANCHOR A2 projection-identity on incumbent: maxdev=" + repr(ident) + " (need exactly 0)")
log("ANCHOR A2 weights maxdev=%.3e (need <1e-12)" % wdev)
log("ANCHOR A2 bytes   maxdev=%.3e (need <1e-12) n=%d" % (bdev, len(jj)))
log("ANCHOR A2 grossmax=%.9f  fit rows=%d  k_covered=%d" % (gmax, nrows12, k12))
log("ANCHOR A2 incumbent Wmax_sf(x11)=%.4fx  IS-SR=%.6f (continuity 4.198632)  dualmom share=%.4f pct" % (inc_wmax_sf, is_sr_inc, dc_share * 100))
assert ident == 0.0, "projection is NOT identity on the feasible incumbent - fail closed"
assert wdev < 1e-12 and bdev < 1e-12 and gmax <= 1.0 + 1e-9
assert nrows12 == 1809, "fit row drift - fail closed"
assert abs(is_sr_inc - 4.198632) < 5e-6, "IS-SR anchor drifted - fail closed"

log("")
log("CELL SWEEP: BAND grid on the A3 dual-momentum hysteresis gate (WIN=200/FRAC=1/3/xs 12-1/VT0.10 frozen), every other slot frozen per precommit; one sleeve (dualmom), one scalar")
log("BAND   regen-dev   is_sr     IS-ann pct  IS-MDD pct  negy  Wmax_sf   adm")
rows = []
for BAND in GRID:
    s = dualmom_build(BAND)
    assert s.index.equals(anchor_idx), "calendar moved with BAND - coverage law violated"
    cc = saved.index.intersection(s.index)
    gdev = float((s.reindex(cc) - saved.reindex(cc)).abs().max())
    dfc = df12.copy()
    dfc["dualmom"] = s.reindex(dfc.index)
    assert dfc.index.equals(df12.index), "frame index changed - fail closed"
    assert int(dfc["dualmom"].notna().sum()) == int(df12["dualmom"].notna().sum()), "coverage law violated - fail closed"
    isr_c = dfc[dfc.index < B.IS_END]
    relw_c, nrows_c, k_c = fit_relw(isr_c, names12)
    assert nrows_c == nrows12 and k_c == K_COVERED, "coverage law violated - fail closed"
    relw_c = apply_cap(relw_c)
    relw_p = project_wmax(relw_c, k=K_COVERED)
    wmax_sf = float(relw_p.max()) * K_COVERED
    net_p, Wg_p, _ = build_book(dfc, relw_p, gear=1.0)
    i_net = net_p[net_p.index < B.IS_END]
    i_sr, i_mdd = sr(i_net), mdd(i_net)
    i_ann = ann_arith(i_net) * 100
    ny = len(neg_years(i_net))
    cfx = float(relw_p["CFX4"])
    blk = float((relw_p[list(BRWT_BLOCK)]).sum())
    adm = (wmax_sf <= 2.0 + 1e-9) and (i_mdd >= -0.06) and (ny == 0) and (i_sr > BAR + 1e-4)
    label = "%0.2f" % BAND
    extra = ""
    if BAND == ANCHOR_BAND:
        wdev10 = float((relw_p - committed.reindex(relw_p.index)).abs().max())
        jb = pd.concat([champ.rename("csv"), net_p.rename("reb")], axis=1, join="inner")
        bdev10 = float((jb["csv"] - jb["reb"]).abs().max())
        log("ANCHOR CELL BAND=0.03: weights dev vs committed %.3e (need <1e-6); book dev vs champ %.3e (need <1e-9); block share=%.6f" % (wdev10, bdev10, blk))
        assert wdev10 < 1e-6 and bdev10 < 1e-9, "anchor cell does not reproduce the incumbent - STOP"
        extra = " (anchor)"
    relw_p.to_frame("relw").to_csv(OUT + "/arm_BAND" + label + "_weights.csv")
    rows.append(dict(label=label, BAND=BAND, isr=i_sr, iann=i_ann, imdd=i_mdd, ny=ny,
                     wmax=wmax_sf, cfx=cfx, blk=blk, adm=adm, relw=relw_p, net=net_p, dfc=dfc))
    log("%-6s %.3e  %8.6f  %8.3f    %8.2f    %d/9  %6.4fx  %s%s  blk=%.4f" % (label, gdev, i_sr, i_ann, i_mdd * 100, ny, wmax_sf, "YES" if adm else "no", extra, blk))

adm_rows = [r for r in rows if r["adm"]]
log("")
log("ADMITTED: %d / %d (jitter tolerance 1e-4 on the IS bar)" % (len(adm_rows), len(rows)))
verdict = "NO-ADMISSION (IS level) -> honest negative, no reveal (per precommit stop rule)"

if not adm_rows:
    log("NO cell admitted -> HONEST NEGATIVE, no reveal (per precommit STOP RULE).")
else:
    win = sorted(adm_rows, key=lambda r: (-r["isr"], abs(r["BAND"] - ANCHOR_BAND), r["BAND"]))[0]
    log("GLOBAL ARGMAX (IS-only): BAND=%s IS-SR=%.6f Wmax_sf=%.4fx block=%.6f" % (win["label"], win["isr"], win["wmax"], win["blk"]))
    fs = win["net"]; relw13 = win["relw"]; dfw = win["dfc"]
    f_sr, f_mdd = sr(fs), mdd(fs)
    f_ann_a, f_ann_c = ann_arith(fs) * 100, ann_cagr(fs) * 100
    nyf = neg_years(fs)
    _, Wg_win, _ = build_book(dfw, relw13, gear=1.0)
    grossmax = float(Wg_win.abs().sum(axis=1).max())
    log("")
    log("REVEAL book: 12-pool refit at BAND=%s, gear 1.0, n=%d (%s..%s)" % (win["label"], len(fs), str(fs.index[0].date()), str(fs.index[-1].date())))
    log("  FS SR=%.6f (incumbent 3.751429)  ann arith=%.4f pct  cagr=%.4f pct  MDD=%.4f pct  negyrs=%d" % (f_sr, f_ann_a, f_ann_c, f_mdd * 100, len(nyf)))
    log("  grossmax=%.9f  Wmax_sf=%.4fx  CFX4 relw=%.1e  brwt-block share=%.6f" % (grossmax, win["wmax"], win["cfx"], win["blk"]))
    isr_w = dfw[dfw.index < B.IS_END]
    have12 = [n for n in names12 if isr_w[n].notna().sum() > 0]
    n12a = len(isr_w[have12].dropna()); n12b = n12a
    shrink_g8 = 1.0 - n12b / float(n12a)
    log("  G8 fit-window complete rows: %d -> %d (same pool), shrink=%.4f pct (bar <= 2 pct)" % (n12a, n12b, shrink_g8 * 100))
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
    g5 = win["cfx"] == 0.0
    g6 = win["wmax"] <= 2.0 + 1e-9
    g7 = (pos >= 4) and (min(dsrc) >= -0.10) and (f_sr > FS_BAR)
    g8 = shrink_g8 <= 0.02
    gates = [g1, g2, g3, g4, g5, g6, g7, g8]
    labels = ["1 FS ann>=20pct", "2 gross<=1.6", "3 FS MDD>=-7pct", "4 0 FS neg yrs",
              "5 CFX4=0", "6 Wmax_sf<=2.0x (k=11)", "7 OOS police", "8 fit-window shrink<=2pct"]
    for l, g in zip(labels, gates):
        log("  GATE %-24s %s" % (l, "PASS" if g else "FAIL"))
    if all(gates):
        verdict = "ADOPTABLE (8/8) -> proceed to full battery per precommit"
    else:
        fails = [l for l, g in zip(labels, gates) if not g]
        verdict = "REJECT - failed gates: " + ", ".join(fails) + " (no second reveal per precommit)"
    pd.DataFrame(dict(ret=fs.values), index=fs.index).to_csv(OUT + "/candidate_BAND" + win["label"] + "_daily.csv")
    win["relw"].to_frame("relw").to_csv(OUT + "/candidate_BAND" + win["label"] + "_weights.csv")

log("")
log("VERDICT: " + verdict)
champ_sha_post, wgt_sha_post = sha16(CHAMP), sha16(WGT)
log("Champion sha16 post-run: " + champ_sha_post + " / weights " + wgt_sha_post + " (pre==post: " + str((champ_sha_pre == champ_sha_post) and (wgt_sha_pre == wgt_sha_post)) + ")")
assert champ_sha_pre == champ_sha_post and wgt_sha_pre == wgt_sha_post
with open(OUT + "/driver_iter38.log", "w") as fh:
    fh.write(chr(10).join(LOG) + chr(10))
print("LOG WRITTEN: " + OUT + "/driver_iter38.log")
