#!/usr/bin/env python3
import hashlib, importlib.util, itertools, json, os
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = ROOT + "/campaign/agents/chief/coord/ITER30_RECIPE_SWEEP"
CHAMP = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
JITTER = 1e-4

spec = importlib.util.spec_from_file_location("d24", ROOT + "/campaign/agents/chief/coord/ITER24_DATA_AXIS/driver_iter24.py")
d24 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d24)

K_SET = [252, 315, 378, 441, 504]
CAD_SET = [21, 42, 63]
VT_SET = [0.08, 0.12, 0.16]
CAP_SET = [3.0, 5.0]
INC_CELL = (378, 42, 0.12, 5.0)
DUR, BPS = 1.9, 6.0

y = pd.read_csv(ROOT + "/tools/quant/hedge_fund_strats/data_fred_new/DGS2.csv", index_col=0, parse_dates=True)["value"].astype(float) / 100.0
y = y[~y.index.duplicated(keep="last")].sort_index()
TR = (-DUR * y.diff() + y / 252.0).dropna()

def gen_stream(tr, K, CAD, VT, CAP):
    sig = (tr.rolling(K).mean() > 0).astype(float)
    W = sig.iloc[::CAD].reindex(tr.index).ffill().fillna(0.0)
    gross = W.shift(1) * tr
    turn = (W.shift(1) - W.shift(2)).abs().fillna(0.0)
    net = (gross - turn * BPS / 1e4).dropna()
    lev = (VT / np.sqrt(252) / net.expanding(60).std().shift(1)).clip(0, CAP).fillna(0.0)
    out = (net * lev).dropna()
    if len(out) == 0 or not np.isfinite(out.values).all():
        raise RuntimeError("cell stream empty or non-finite - fail-closed")
    return out

def causality_probe(K, CAD, VT, CAP, fracs=(0.25, 0.5, 0.75)):
    base = gen_stream(TR, K, CAD, VT, CAP)
    worst = 0.0
    for f in fracs:
        t = int(len(TR) * f)
        TRz = TR.copy()
        TRz.iloc[t:] = 0.0
        z = gen_stream(TRz, K, CAD, VT, CAP)
        j = pd.concat([base.rename("b"), z.rename("z")], axis=1, join="inner")
        pre = j[j.index < TR.index[t]]
        if len(pre):
            worst = max(worst, float((pre["b"] - pre["z"]).abs().max()))
    return worst
frames = dict((n, d24.load_ret(p).dropna()) for n, p in d24.INCUMBENT.items())
idx12 = sorted(set().union(*[set(frames[n].index) for n in d24.INCUMBENT]))
idx12 = [t for t in idx12 if t >= d24.START]
df12 = pd.DataFrame(frames)[list(d24.INCUMBENT)].reindex(idx12)
champ_r = d24.load_ret(CHAMP)
FS_BAR = float(champ_r.mean() / champ_r.std(ddof=1) * np.sqrt(252))
isr0 = df12[df12.index < d24.IS_END]
have0 = [n for n in df12.columns if isr0[n].notna().sum() > 0]
ROWS_FIT_INC = int(isr0[have0].dropna().shape[0])
wcmt = pd.read_csv(ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv", index_col=0)["relw"]
KC = 11

def is_stats(net):
    pre = net[net.index < d24.IS_END]
    nav = (1.0 + pre).cumprod()
    yr = pre.groupby(pre.index.year).apply(lambda x: (1.0 + x).prod() - 1.0)
    return dict(is_sr=float(pre.mean() / pre.std(ddof=1) * np.sqrt(252)),
                is_mdd=float((nav / nav.cummax() - 1.0).min() * 100.0),
                is_negy=int((yr < 0).sum()))

def l1_norm(cell):
    K, CAD, VT, CAP = cell
    return (abs(K - 378) / 63.0 + abs(CAD - 42) / 21.0
            + abs(VT - 0.12) / 0.04 + abs(CAP - 5.0) / 2.0)

rows = []
cells = [(K, CAD, VT, CAP) for K in K_SET for CAD in CAD_SET for VT in VT_SET for CAP in CAP_SET]
assert len(cells) == 90 and INC_CELL in cells
inc_row = None
for cell in cells:
    K, CAD, VT, CAP = cell
    if cell == INC_CELL:
        s = frames["a6r7"]
    else:
        s = gen_stream(TR, K, CAD, VT, CAP)
    dfc = df12.copy()
    dfc["a6r7"] = s.reindex(idx12)
    isr_c = dfc[dfc.index < d24.IS_END]
    have_c = [n for n in dfc.columns if isr_c[n].notna().sum() > 0]
    covers = bool(int(isr_c[have_c].dropna().shape[0]) == ROWS_FIT_INC)
    net_t, relw_t, gross_t, to_t = d24.build_from_frame(dfc)
    st = d24.stats(net_t, "cell")
    iss = is_stats(net_t)
    wmax_sf = float(relw_t.max()) * KC
    g = dict(A=bool(wmax_sf <= 2.0 + 1e-9), B=bool(iss["is_sr"] > 0.0),
             C=bool(iss["is_mdd"] >= -6.0 and iss["is_negy"] == 0),
             D=bool(float(gross_t.max()) <= 1.6 + 1e-9), E=covers)
    row = dict(cell=list(cell), is_sr=iss["is_sr"], is_mdd=iss["is_mdd"],
               is_negy=iss["is_negy"], fs_sr=st["sr"], cagr=st["cagr"],
               arith=st["arith"], mdd=st["mdd"], worst_yr=st["worst_yr"],
               neg_years=st["neg_years"], gross_max=float(gross_t.max()),
               wmax_sf=wmax_sf, a6r7_relw=float(relw_t["a6r7"]),
               to_bp_yr=float(to_t.mean() * 252.0 * 6.4), n_rows=int(len(net_t)),
               gates=g, l1=l1_norm(cell))
    rows.append(row)
    if cell == INC_CELL:
        inc_row = row
        dev_saved = float((s - d24.load_ret(d24.INCUMBENT["a6r7"])).abs().max())
        wdev = float((wcmt.reindex(relw_t.index) - relw_t).abs().max())
        print("INCUMBENT CELL: gen-vs-saved dev %.3e  weights-vs-committed dev %.3e" % (dev_saved, wdev))
        print("INCUMBENT CELL: is_sr %.6f  fs_sr %.6f  wmax_sf %.4f" % (iss["is_sr"], st["sr"], wmax_sf))
        if dev_saved >= 1e-12 or wdev >= 1e-9:
            raise SystemExit("incumbent cell anchor FAILED; STOP")
IS_BAR = inc_row["is_sr"]
print("BAR: incumbent is_sr %.6f  fs bar %.6f" % (IS_BAR, FS_BAR))
admitted = []
for r in rows:
    cell = tuple(r["cell"])
    if cell == INC_CELL:
        r["gates"]["B"] = True
        r["admitted"] = False
        continue
    r["gates"]["B"] = bool(r["is_sr"] > IS_BAR + JITTER)
    r["admitted"] = all(r["gates"].values())
    if r["admitted"]:
        admitted.append(r)
print("ADMITTED %d/89" % len(admitted))
for r in sorted(rows, key=lambda x: -x["is_sr"])[:12]:
    print("ROW cell=%s is_sr=%.4f fs_sr=%.4f wmax=%.3f a6r7w=%.4f mdd=%.2f gates=%s adm=%s"
          % (tuple(r["cell"]), r["is_sr"], r["fs_sr"], r["wmax_sf"], r["a6r7_relw"],
             r["is_mdd"], "".join("1" if v else "0" for v in r["gates"].values()), r["admitted"]))
verdict = dict(precommit_sha16="93ecd55beb7fa4f5", n_cells=len(cells), is_bar=IS_BAR,
               fs_bar=FS_BAR, n_admitted=len(admitted), admitted_cells=[r["cell"] for r in admitted])
if not admitted:
    verdict.update(outcome="NO_ADMIT", adopted=False)
    print("VERDICT: NO ADMITTED CELL - honest negative, no reveal (sealed stop rule)")
else:
    best = sorted(admitted, key=lambda r: (-r["is_sr"], r["l1"], tuple(r["cell"])))[0]
    cell = tuple(best["cell"])
    print("ARGMAX cell=%s is_sr=%.6f (bar+%.6f)" % (cell, best["is_sr"], best["is_sr"] - IS_BAR))
    verdict.update(argmax_cell=list(cell), argmax_is_sr=best["is_sr"])
    K, CAD, VT, CAP = cell
    caus = causality_probe(K, CAD, VT, CAP)
    print("causality probe max pre-probe dev: %.3e" % caus)
    verdict["causality_max_dev"] = caus
    if caus >= 1e-12:
        verdict.update(outcome="CAUSALITY_FAIL", adopted=False)
        raise SystemExit("causality probe FAILED - STOP")
    s = gen_stream(TR, K, CAD, VT, CAP)
    dfc = df12.copy()
    dfc["a6r7"] = s.reindex(idx12)
    net_t, relw_t, gross_t, to_t = d24.build_from_frame(dfc)
    st = d24.stats(net_t, "reveal")
    bins = d24.oos_bins(net_t, champ_r)
    pre_t = net_t[net_t.index >= d24.IS_END]
    pre_c = champ_r[champ_r.index >= d24.IS_END]
    dsr_full = float(pre_t.mean() / pre_t.std(ddof=1) - pre_c.mean() / pre_c.std(ddof=1))
    npos = int(sum(1 for v in bins if v > 0))
    fs_gates = dict(fs_sr_gt=bool(st["sr"] > FS_BAR), bins=bool(npos >= 4 and dsr_full > 0),
                    cagr=bool(st["cagr"] >= 20.0), arith=bool(st["arith"] >= 20.0),
                    mdd=bool(st["mdd"] >= -7.0), negy=bool(st["neg_years"] == 0),
                    worst=bool(st["worst_yr"] > -5.0), gross=bool(float(gross_t.max()) <= 1.6 + 1e-9))
    relw_t.to_csv(OUT + "/argmax_weights.csv")
    net_t.to_frame("ret").to_csv(OUT + "/argmax_book_daily.csv")
    verdict.update(reveal=dict(cell=list(cell), stats=st, bins=bins, n_pos_bins=npos,
                               dsr_full_oos_per_day=dsr_full, fs_gates=fs_gates,
                               wmax_sf=float(relw_t.max()) * KC,
                               a6r7_relw=float(relw_t["a6r7"])))
    print("REVEAL fs_sr %.6f vs %.6f | bins %s (%d/5) | dsr_full %.5f" % (st["sr"], FS_BAR, [round(b, 4) for b in bins], npos, dsr_full))
    print("REVEAL cagr %.4f arith %.4f mdd %.4f worst %.4f negy %d gross %.6f" % (st["cagr"], st["arith"], st["mdd"], st["worst_yr"], st["neg_years"], float(gross_t.max())))
    if all(fs_gates.values()):
        verdict.update(outcome="ADOPT", adopted=True)
        print("VERDICT: ADOPT - all reveal gates pass; champion candidate emitted (landing protocol next)")
    else:
        verdict.update(outcome="REJECT", adopted=False)
        print("VERDICT: REJECT - failed gates %s (sealed stop rule; no second reveal)" % [k for k, v in fs_gates.items() if not v])
with open(OUT + "/cells.json", "w") as fh:
    json.dump(rows, fh, indent=1, default=str)
with open(OUT + "/verdict.json", "w") as fh:
    json.dump(verdict, fh, indent=1, default=str)
print("ITER30 DRIVER COMPLETE:", verdict["outcome"])
