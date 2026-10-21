#!/usr/bin/env python3
"""CAMP_SHORT ROUND 6 (a) — fraud-catch cross-verification of CAMP_BORROW's R5 verdict.

Reproduces, with OWN code (no import of rawew13v2_build / bt.borrow / bt.financing_stress /
CAMP_BORROW modules — only their published ARTIFACTS are read), every load-bearing R5 claim:

  B1. champion sha + headline (ann 37.1954 / SR 3.1810 / MDD -6.6922 / 0 neg / n=4805).
  B2. own-algebra builder rebuild byte-matches the committed CSV (their max_dev 9.996e-17).
  B3. margin = 2.70%/yr on max(gross-1,0)=0.6 at 4.5%/252 = 1.0714 bps/day, ONE distinct
      daily value; gross exactly 1.6 every day.
  B4. committed file priced at EXACTLY 4.5% (residual ~1e-16; 5.5%/6.5% residuals ~2-5e-05).
  B5. slot gross-share census (brwt10 22.95 / brwt7 19.96 / brwt5 16.97 / brwt15 13.23 /
      C5ng 8.80 / C5ngsum 6.81 / dualmom 2.67 / QAxasts 2.34 / A5r2 1.78 / diescrack 1.77 /
      a6r7 1.54 / carryv2 1.19 / CFX4 0.00).
  B6. C1: ZERO negative slot weights on all 4805 days x 13 slots (62,465 slot-days).
  B7. C4: CFX4 relw=0 => weight exactly 0 all days (relw = max(IS_SR,0)^0.55 arithmetic).
  B8. C2: diescrack embeds EXACTLY 0.005/252 on 733/4605 rows (331 short / 173 long /
      229 cost-only), from an OWN zrev+VT reconstruction.
  B9. C3: embedded drag 0.2195 bps/yr; HTB 2% -> 0.6586 bps/yr, 8% -> 3.2931 bps/yr.
  B10. drift flags: DFF 3.63 (2026-09-03, n=26363) / SOFR 3.66 (n=2198); implied 5.13/5.63/
      5.16 rel +14.00/+25.11/+14.67%; path mean 2.9315 -> drag 1.7589 rel -34.86%; reprice
      ann 36.6784 / 36.2695 / 36.6538 / 38.4910 (dAnn -0.517/-0.926/-0.542/+1.296), SR /
      MDD / 0-neg as published; ladder rung arithmetic slope -0.60pp per +1pp EXACT.
  B11. borrow 100%-drift impact 0.2196 bps/yr.

Exits nonzero on any mismatch. Writes work_r6/r6_borrow_repro.json.
"""
import hashlib
import json
import math
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
W5B = f"{ROOT}/campaign/agents/chief/coord/CAMP_BORROW/work_r5"
W6 = f"{ROOT}/campaign/agents/chief/coord/CAMP_SHORT/work_r6"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
WEIGHTS = f"{ROOT}/campaign/results/RAWEW13v2_IS_SR_weights.csv"

OUT = {"agent": "CAMP_SHORT-R6", "verdicts": {}, "mismatches": []}


def check(label, mine, theirs, tol=1e-6):
    """Record agreement of my number vs their published number."""
    dev = abs(mine - theirs)
    ok = dev <= tol
    OUT["verdicts"][label] = {"mine": mine, "theirs": theirs, "abs_dev": dev,
                              "tol": tol, "match": bool(ok)}
    if not ok:
        OUT["mismatches"].append(f"{label}: mine={mine!r} theirs={theirs!r} dev={dev:.3e}")
    print(f"  [{'OK ' if ok else 'FAIL'}] {label}: mine={mine:.10g} theirs={theirs:.10g} dev={dev:.3e}")
    return ok


def headline(r):
    r = r.dropna()
    ann = float((1 + r).prod() ** (252 / len(r)) - 1)
    sr = float(r.mean() / r.std(ddof=1) * np.sqrt(252))
    nav = (1 + r).cumprod()
    mdd = float((nav / nav.cummax() - 1).min())
    yr = (1 + r).groupby(r.index.year).prod() - 1
    return dict(ann=ann, sr=sr, mdd=mdd, neg=int((yr < 0).sum()),
                worst=float(yr.min()), n=len(r))


# ---------- B1. book of record ----------
sha = hashlib.sha256(open(CHAMP, "rb").read()).hexdigest()
print(f"[B1] champion sha256[:16] = {sha[:16]}")
assert sha.startswith("4358dfab95679b97"), "book of record changed since charter quote"
champ = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
h0 = headline(champ)
print(f"[B1] headline: ann {h0['ann']*100:.4f}% SR {h0['sr']:.4f} MDD {h0['mdd']*100:.4f}% "
      f"neg {h0['neg']} n={h0['n']} {champ.index.min().date()}..{champ.index.max().date()}")
check("B1.ann_pct", h0["ann"] * 100, 37.19539675684982, 1e-9)
check("B1.sr", h0["sr"], 3.180994199561701, 1e-9)
check("B1.mdd_pct", h0["mdd"] * 100, -6.692185534307193, 1e-9)
check("B1.n", h0["n"], 4805, 0)
check("B1.neg_years", h0["neg"], 0, 0)
check("B1.worst_year_pct", h0["worst"] * 100, 7.310363900638817, 1e-9)

# ---------- B2..B7. own-algebra rebuild ----------
NAMES = ["brwt15", "brwt10", "brwt7", "brwt5", "C5ng", "C5ngsum", "A5r2", "a6r7",
         "QAxasts", "carryv2", "dualmom", "diescrack", "CFX4"]
PATHS = {
    "brwt15": f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
    "brwt10": f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv",
    "brwt7": f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv",
    "brwt5": f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv",
    "C5ng": f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
    "C5ngsum": f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
    "A5r2": f"{ROOT}/campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
    "a6r7": f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
    "QAxasts": f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
    "carryv2": f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
    "dualmom": f"{ROOT}/campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
    "diescrack": f"{ROOT}/campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
    "CFX4": f"{ROOT}/campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
}
GEAR, RATE, BPS, P, IS_END = 1.6, 0.045, 6.4, 0.55, pd.Timestamp("2017-01-01")


def load_ret(p):
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)


def is_sr(r):
    r = r.dropna()
    if len(r) < 200 or r.std(ddof=1) <= 1e-12:
        return 0.0
    return float(r.mean() / r.std(ddof=1) * np.sqrt(252))


df = pd.DataFrame({n: load_ret(PATHS[n]).dropna() for n in NAMES})
df = df[df.index >= "2008-03-31"]
isr = df[df.index < IS_END]
SR = pd.Series({n: is_sr(isr[n]) for n in NAMES})
relw = np.maximum(SR, 0.0) ** P
nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
d2 = d2.div(d2.sum(axis=1), axis=0) * len(NAMES)
Wg = d2 * (GEAR / len(NAMES))
port = pd.Series((df.fillna(0).values * Wg.values).sum(axis=1), index=df.index)
to = Wg.diff().abs().sum(axis=1).fillna(0.0)
net = port - to * BPS / 1e4 - max(GEAR - 1, 0) * RATE / 252
gross = Wg.abs().sum(axis=1)

jj = pd.concat([champ.rename("old"), net.rename("new")], axis=1, join="inner").dropna()
repro = float((jj.old - jj.new).abs().max())
print(f"\n[B2] OWN rebuild vs committed: n={len(jj)} max|dev|={repro:.4e} (their 9.996e-17)")
check("B2.byte_repro_max_dev", repro, 9.996e-17, 1e-12)
assert repro < 1e-12

# committed relw table vs my own relw arithmetic
relw_csv = pd.read_csv(WEIGHTS, index_col=0).iloc[:, 0]
relw_dev = float((relw_csv.reindex(NAMES) - relw.reindex(NAMES)).abs().max())
print(f"[B2b] OWN relw=max(IS_SR,0)^0.55 vs committed table: max|dev|={relw_dev:.4e}")
check("B2b.weights_repro_max_dev", relw_dev, 2.220446049250313e-16, 1e-12)
assert relw_dev < 1e-12

# B3 margin
margin_daily = max(GEAR - 1, 0) * RATE / 252
margin_ann = float(gross.mean() * 0 + margin_daily * 252)
n_uniq = len(np.unique(np.round(gross.values, 12)))
print(f"\n[B3] gross: min={gross.min():.15f} max={gross.max():.15f} distinct={n_uniq}")
print(f"[B3] margin drag = {margin_daily*1e4:.4f} bps/day -> {margin_ann*100:.6f}%/yr")
check("B3.margin_ann_pct", margin_ann * 100, 2.7000000000000002, 1e-9)
check("B3.bps_day", margin_daily * 1e4, 0.6 * 0.045 / 252 * 1e4, 1e-12)
check("B3.gross_max", float(gross.max()), 1.6000000000006978, 1e-9)
check("B3.n_over", int((gross > 1.6 + 1e-9).sum()), 0, 0)

# B4 priced-at-rate residual
resid = {}
for r_ in (0.045, 0.055, 0.065):
    rebuilt = port - to * BPS / 1e4 - max(GEAR - 1, 0) * r_ / 252
    k = pd.concat([champ.rename("o"), rebuilt.rename("n")], axis=1, join="inner").dropna()
    resid[r_] = float((k.o - k.n).abs().max())
print(f"\n[B4] priced-at-rate residuals: " + ", ".join(f"{r:.1%}:{v:.2e}" for r, v in resid.items()))
check("B4.resid_4.5", resid[0.045], 1.00e-16, 1e-12)
assert resid[0.045] < 1e-12 and resid[0.055] > 1e-6 and resid[0.065] > 1e-6

# B5 slot gross shares
share = Wg.abs().mean().sort_values(ascending=False) / GEAR * 100
print("\n[B5] slot gross share (%):")
for k, v in share.items():
    print(f"    {k:9s} {v:6.2f}%")
check("B5.share_sum", float(share.sum()), 100.0, 1e-9)
for k, v in {"brwt10": 22.95, "brwt7": 19.96, "brwt5": 16.97, "brwt15": 13.23,
             "C5ng": 8.80, "C5ngsum": 6.81, "dualmom": 2.67, "QAxasts": 2.34,
             "A5r2": 1.78, "diescrack": 1.77, "a6r7": 1.54, "carryv2": 1.19,
             "CFX4": 0.00}.items():
    check(f"B5.{k}", float(share[k]), v, 5e-3)

# B6 zero shorts at slot level
n_neg_slots = int((Wg < -1e-12).sum().sum())
slot_days = Wg.size
print(f"\n[B6] C1: negative slot weights = {n_neg_slots} of {slot_days} slot-days")
check("B6.neg_slot_weights", n_neg_slots, 0, 0)
check("B6.slot_days", slot_days, 62465, 0)
assert n_neg_slots == 0

# B7 CFX4 relw arithmetic
cfx_sr = is_sr(isr["CFX4"])
cfx_relw_mine = max(cfx_sr, 0.0) ** P
print(f"\n[B7] CFX4 IS_SR={cfx_sr:.6f} -> relw mine={cfx_relw_mine:.6e} "
      f"committed={relw_csv['CFX4']:.6e}; nonzero-weight days="
      f"{int((Wg['CFX4'].abs() > 1e-12).sum())}")
check("B7.CFX4_relw", float(relw_csv["CFX4"]), 0.0, 0.0)
check("B7.CFX4_nonzero_days", int((Wg["CFX4"].abs() > 1e-12).sum()), 0, 0)
assert cfx_sr <= 0 and relw_csv["CFX4"] == 0.0

OUT["share_pct"] = {k: round(float(v), 4) for k, v in share.items()}

# ---------- B8. diescrack embedded borrow, OWN reconstruction ----------
print("\n[B8] diescrack OWN zrev+VT reconstruction:")
dj = pd.read_csv(f"{ROOT}/tools/quant/data/newdata/DJFUELUSGULF.csv", index_col=0, parse_dates=True)
dj = (dj["value"] if "value" in dj.columns else dj.iloc[:, 0])
dj = dj[~dj.index.duplicated(keep="last")].sort_index()
wti = pd.read_csv(f"{ROOT}/tools/quant/hedge_fund_strats/data_fred/wti_full.csv",
                  index_col=0, parse_dates=True)
wti = (wti["value"] if "value" in wti.columns else wti.iloc[:, 0])
wti = wti[~wti.index.duplicated(keep="last")].sort_index()
spread = np.log(dj * 42) - np.log(wti)
sp = spread.dropna()
sp = sp[sp.index >= "2008-01-01"]
m = sp.rolling(40, min_periods=40).mean()
sd = sp.rolling(40, min_periods=40).std().replace(0, np.nan)
z = (sp - m) / sd
pos = pd.Series(0.0, index=sp.index)
pos[z < -2.0] = 1.0
pos[z > 2.0] = -1.0
ret = sp.diff().shift(-1)
gr = (pos * ret).dropna()
tup = pos.diff().abs().reindex(gr.index).fillna(0.0)
netv = gr - tup * 6.4 / 1e4
rv = netv.expanding(60).std() * np.sqrt(252)
scale = (0.08 / rv).clip(upper=3.0)
netvt = (netv * scale).dropna()

dc = load_ret(PATHS["diescrack"])
j2 = pd.concat([netvt.rename("recon"), dc.rename("committed")], axis=1, join="inner").dropna()
line = j2.committed - j2.recon
nz = line.abs() > 1e-12
unit = 0.005 / 252
charged = line[nz]
n_charged = int(nz.sum())
max_line_dev = float((charged.abs() - unit).abs().max())
posj = pos.reindex(j2.index)
n_short = int(((posj < 0) & nz).sum())
n_long = int(((posj > 0) & nz).sum())
n_cost = n_charged - n_short - n_long
print(f"    n={len(j2)} charged={n_charged} max||line|-0.005/252|={max_line_dev:.3e}")
print(f"    split short={n_short} long={n_long} cost-only={n_cost}")
check("B8.n_charged", n_charged, 733, 0)
check("B8.n_short", n_short, 331, 0)
check("B8.n_long", n_long, 173, 0)
check("B8.n_cost_only", n_cost, 229, 0)
check("B8.line_unit_dev", max_line_dev, 0.0, 1e-9)
assert n_charged == 733 and n_short == 331 and n_long == 173 and max_line_dev < 1e-9

# ---------- B9 champion-level drag + HTB tiers ----------
w = Wg["diescrack"].reindex(line.index)
drag = float((w * line).dropna().sum() / (len(w) / 252))
bps_embed = -drag * 1e4
tiers = {}
for tier in (0.02, 0.08):
    extra = float((w * (line * (tier / 0.005 - 1))).dropna().sum() / (len(w) / 252))
    tiers[tier] = -extra * 1e4
print(f"\n[B9] embedded drag {bps_embed:.4f} bps/yr; 2% tier {tiers[0.02]:.4f}; "
      f"8% tier {tiers[0.08]:.4f}")
check("B9.embedded_bps_yr", bps_embed, 0.2195, 5e-4)
check("B9.tier2_bps_yr", tiers[0.02], 0.6586, 5e-4)
check("B9.tier8_bps_yr", tiers[0.08], 3.2931, 5e-4)

# ---------- B10 drift flags + repricing (from THEIR fetched FRED artifacts) ----------
dff = pd.read_csv(f"{W5B}/fred_dff.csv", parse_dates=["observation_date"])
dff = dff.set_index("observation_date")["DFF"] / 100.0
sofr = pd.read_csv(f"{W5B}/fred_sofr.csv", parse_dates=["observation_date"])
sofr = sofr.set_index("observation_date")["SOFR"] / 100.0
print(f"\n[B10] FRED artifacts: DFF n={len(dff)} last {dff.index[-1].date()} "
      f"{dff.iloc[-1]*100:.2f}%; SOFR n={len(sofr)} last {sofr.index[-1].date()} "
      f"{sofr.iloc[-1]*100:.2f}%")
check("B10.dff_n", len(dff), 26363, 0)
check("B10.dff_last_pct", float(dff.iloc[-1]) * 100, 3.63, 1e-9)
check("B10.sofr_n", len(sofr), 2198, 0)
check("B10.sofr_last_pct", float(sofr.iloc[-1]) * 100, 3.66, 1e-9)
bm, sf = float(dff.iloc[-1]), float(sofr.iloc[-1])
check("B10.implied_dff+1.5", (bm + 0.015) * 100, 5.13, 1e-9)
check("B10.implied_dff+2.0", (bm + 0.020) * 100, 5.63, 1e-9)
check("B10.implied_sofr+1.5", (sf + 0.015) * 100, 5.16, 1e-9)
check("B10.rel_dff+1.5_pct", ((bm + 0.015) / 0.045 - 1) * 100, 14.00, 5e-3)
check("B10.rel_dff+2.0_pct", ((bm + 0.020) / 0.045 - 1) * 100, 25.11, 5e-3)
check("B10.rel_sofr+1.5_pct", ((sf + 0.015) / 0.045 - 1) * 100, 14.67, 5e-3)


def reprice(rate_path):
    r = pd.Series(rate_path, index=net.index)
    return net - max(GEAR - 1, 0) * (r - RATE) / 252


def reprice_flat(rate):
    return reprice(pd.Series(rate, index=net.index))


for name, rr, pub in [("flat5.13", bm + 0.015, dict(ann=36.6784, sr=3.1436, mdd=-6.6979,
                                                    d=-0.5170)),
                      ("flat5.63", bm + 0.020, dict(ann=36.2695, sr=3.1139, mdd=-6.7024,
                                                    d=-0.9259)),
                      ("flat5.16", sf + 0.015, dict(ann=36.6538, sr=3.1418, mdd=-6.6982,
                                                    d=-0.5416))]:
    h = headline(reprice_flat(rr))
    print(f"[B10] {name}: ann {h['ann']*100:.4f}% dAnn {(h['ann']-h0['ann'])*100:+.4f}pp "
          f"SR {h['sr']:.4f} MDD {h['mdd']*100:.4f}% neg {h['neg']}")
    check(f"B10.{name}.ann", h["ann"] * 100, pub["ann"], 5e-4)
    check(f"B10.{name}.d_ann_pp", (h["ann"] - h0["ann"]) * 100, pub["d"], 5e-4)
    check(f"B10.{name}.sr", h["sr"], pub["sr"], 5e-4)
    check(f"B10.{name}.mdd", h["mdd"] * 100, pub["mdd"], 5e-4)
    check(f"B10.{name}.neg", h["neg"], 0, 0)

dw = dff[dff.index <= net.index.max()]
path = (dw + 0.015).reindex(net.index).ffill().bfill()
assert path.notna().all()
h = headline(reprice(path.values))
avg = float(path.mean())
print(f"[B10] PATH DFF+1.5pp: mean {avg*100:.4f}% drag {0.6*avg*100:.4f}% "
      f"ann {h['ann']*100:.4f}% dAnn {(h['ann']-h0['ann'])*100:+.4f}pp SR {h['sr']:.4f} "
      f"MDD {h['mdd']*100:.4f}% neg {h['neg']}")
check("B10.path_mean_pct", avg * 100, 2.9315, 5e-4)
check("B10.path_drag_pct", 0.6 * avg * 100, 1.7589, 5e-4)
check("B10.path_rel_pct", (0.6 * avg / (0.6 * 0.045) - 1) * 100, -34.86, 5e-3)
check("B10.path_ann", h["ann"] * 100, 38.4910, 5e-4)
check("B10.path_d_ann_pp", (h["ann"] - h0["ann"]) * 100, 1.2956, 5e-4)
check("B10.path_sr", h["sr"], 3.2741, 5e-4)
check("B10.path_mdd", h["mdd"] * 100, -6.6824, 5e-4)
check("B10.path_neg", h["neg"], 0, 0)

# ladder rung cross-check vs their r5_tier_ladder.json (incl. -0.60pp/+1pp arithmetic slope)
lad = json.load(open(f"{W5B}/r5_tier_ladder.json"))
worst_rung = 0.0
for rung in lad["rungs"]:
    h = headline(reprice_flat(rung["rate"]))
    d_arith = (float(np.mean(reprice_flat(rung["rate"]).dropna())) -
               float(np.mean(net.dropna()))) * 252 * 100
    worst_rung = max(worst_rung, abs(h["ann"] - rung["ann"]),
                     abs(h["sr"] - rung["sr_d"]), abs(h["mdd"] - rung["mdd"]),
                     abs(d_arith - rung["delta_ann_arith_pp"]))
print(f"[B10] ladder rungs x6 (ann/sr/mdd/arith-slope) worst dev = {worst_rung:.3e}")
check("B10.ladder_worst_dev", worst_rung, 0.0, 1e-9)
s513 = headline(reprice_flat(bm + 0.015))
slope = ((float(np.mean(reprice_flat(bm + 0.015))) - float(np.mean(net))) * 252 * 100) / ((bm + 0.015) - 0.045) * 0.01
print(f"[B10] arithmetic slope d(ann_arith)/d(rate) = {slope:.6f} pp per +1pp")
check("B10.arith_slope", slope, -0.60, 1e-9)

# ---------- B11 borrow 100% drift ----------
print(f"\n[B11] borrow 100% relative drift (0.5->1.0%) incremental drag = "
      f"{bps_embed * (1.0/0.5 - 1):.4f} bps/yr")
check("B11.borrow100_bps_yr", bps_embed * (1.0 / 0.5 - 1), 0.2196, 5e-4)

OUT["mismatches_count"] = len(OUT["mismatches"])
json.dump(OUT, open(f"{W6}/r6_borrow_repro.json", "w"), indent=1)
print(f"\n=== CAMP_BORROW R5 cross-verification: {len(OUT['mismatches'])} mismatches ===")
sys.exit(1 if OUT["mismatches"] else 0)
