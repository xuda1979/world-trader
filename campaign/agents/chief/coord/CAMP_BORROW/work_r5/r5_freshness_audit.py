#!/usr/bin/env python3
"""CAMP_BORROW ROUND 5 — freshness audit of the financing stack vs published IBKR rates.

Charter (a): re-derive call 4.5% on (gross-1) => margin drag 2.70%/yr on the champion of
record; borrow 0.5%/yr on shorts — verify which sleeves actually carry short legs + their
gross share.
Charter (b): flag any drift > 10% relative vs the modeled numbers, with exact citations.

Evidence-only script: fails closed (nonzero exit) on any check that regresses vs the
recorded model. No champion edits, no new signals.
"""
import sys, json
sys.path.insert(0, "campaign")
import numpy as np
import pandas as pd
from bt import borrow as B

ROOT = "/Users/daxu/software/world-trader"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
OUT = {}

# ---------- 0. book of record ----------
import hashlib
sha = hashlib.sha256(open(CHAMP, "rb").read()).hexdigest()
print(f"[0] champion sha256[:16] = {sha[:16]}  (expect 4358dfab95679b97)")
assert sha.startswith("4358dfab95679b97"), "champion of record changed — re-anchor first"

# ---------- 1. fresh rebuild (independent path: builder module) ----------
sys.path.insert(0, f"{ROOT}/campaign/scripts")
import importlib.util
spec = importlib.util.spec_from_file_location("rawew13v2_build", f"{ROOT}/campaign/scripts/rawew13v2_build.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
net_b, relw, gross_b, to_b, df_sleeves = mod.build()
committed = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
j = pd.concat([committed.rename("old"), net_b.rename("new")], axis=1, join="inner").dropna()
repro = float((j.old - j.new).abs().max())
print(f"[1] builder rebuild vs committed: n={len(j)} max|dev|={repro:.3e} "
      f"{'IDENTICAL' if repro < 1e-12 else 'DIFF'}")
assert repro < 1e-12
OUT["repro_max_dev"] = repro

# ---------- 2. margin re-derivation from the ACTUAL weight stream ----------
g = pd.Series(gross_b)
ok, maxdev, nbad = B.gross_exact(g, 1.6)
print(f"[2] gross_exact: ok={ok} max|gross-1.6|={maxdev:.3e} n_beyond_1e-9={nbad}")
margin_daily = B.margin_daily(g, 0.045)
margin_ann_f = float(margin_daily.mean() * 252)
uniq = np.unique(np.round(margin_daily.values, 12))
print(f"[2] margin_daily mean*252 = {margin_ann_f*100:.6f}%/yr  (model: 2.70%/yr)  "
      f"distinct daily values={len(uniq)}")
bps_day = float(margin_daily.mean() * 1e4)
print(f"[2] margin drag = {bps_day:.4f} bps/day  (= 0.6*4.5/252 = {0.6*0.045/252*1e4:.4f})")
assert abs(margin_ann_f - 0.027) < 1e-12, "margin drag deviates from the 2.70%/yr model"
assert ok and nbad == 0
OUT["margin_ann_pct"] = margin_ann_f * 100
OUT["margin_bps_day"] = bps_day
OUT["gross_max_dev"] = maxdev

# committed-file margin arithmetic: net = port - to*6.4bp - 0.6*rate/252. Verify the
# committed series is priced at EXACTLY 4.5% (residual zero) and not at a stale rate.
# Recompute port/turnover exactly as the builder does:
nav = (1 + df_sleeves.fillna(0)).cumprod().shift(1).fillna(1.0)
d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
d2 = d2.div(d2.sum(axis=1), axis=0) * len(relw)
Wg = d2 * (mod.GEAR / len(relw))
port = (df_sleeves.fillna(0).values * Wg.values).sum(axis=1)
to = pd.Series(Wg.diff().abs().sum(axis=1), index=df_sleeves.index).fillna(0.0)
resid = {}
for r in (0.045, 0.055, 0.065):
    rebuilt = pd.Series(port, index=df_sleeves.index) - to * 6.4 / 1e4 - max(mod.GEAR - 1, 0) * r / 252
    jj = pd.concat([committed.rename("old"), rebuilt.rename("new")], axis=1, join="inner").dropna()
    resid[r] = float((jj.old - jj.new).abs().max())
print(f"[2] committed priced-at-rate residuals: " +
      ", ".join(f"{r:.1%}:{v:.2e}" for r, v in resid.items()))
assert resid[0.045] < 1e-12, "committed file NOT priced at 4.5%"
assert resid[0.055] > 1e-6 and resid[0.065] > 1e-6
OUT["priced_at_4p5_residual"] = resid[0.045]

# ---------- 3. fresh slot gross-share census ----------
share = Wg.abs().mean().sort_values(ascending=False) / 1.6 * 100
print("[3] slot gross share (%) over 2008-03-31..2026-08-27:")
for k, v in share.items():
    print(f"    {k:9s} {v:6.2f}%")
OUT["slot_gross_share_pct"] = {k: round(float(v), 4) for k, v in share.items()}
assert abs(share.sum() - 100.0) < 1e-9

# ---------- 4. short-leg census on the 13 generators (borrow applies ONLY to stock loan) ----------
GEN = {
    "brwt15": "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
    "brwt10": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv",
    "brwt7":  "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv",
    "brwt5":  "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv",
    "C5ng":   "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
    "C5ngsum":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
    "A5r2":   "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
    "a6r7":   "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
    "QAxasts":"campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
    "carryv2":"campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
    "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
    "diescrack":"campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
    "CFX4":   "campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
}
# find each generator script by grepping the trees for the sleeve filename
import subprocess, os
print("[4] short-leg evidence grep (generator trees):")
grep_pat = "borrow|0.005|short|htb"
gen_hits = {}
for slot, path in GEN.items():
    fname = os.path.basename(path)
    r = subprocess.run(
        ["grep", "-rl", "--include=*.py", fname.split("_net")[0] if slot == "diescrack" else fname.split("__")[0] if "__" in fname else fname.split(".")[0],
         f"{ROOT}/campaign/agents", f"{ROOT}/campaign/scripts"],
        capture_output=True, text=True)
    cand = [c for c in r.stdout.strip().split("\n") if c and "__pycache__" not in c]
    gen_hits[slot] = cand[:4]
    print(f"    {slot:9s} generator candidates: {len(cand)} -> {[os.path.relpath(c, ROOT) for c in cand[:2]]}")
OUT["gen_candidates"] = {k: [os.path.relpath(c, ROOT) for c in v] for k, v in gen_hits.items()}

# explicit borrow-declaration grep over all generator trees (R2 method, re-run fresh)
r = subprocess.run(["grep", "-rln", "-E", "borrow|HTB|htb|stock.?loan", "--include=*.py",
                    f"{ROOT}/campaign/agents", f"{ROOT}/campaign/scripts"],
                   capture_output=True, text=True)
borrow_files = sorted(set(x for x in r.stdout.strip().split("\n") if x and "__pycache__" not in x))
print("[4] files declaring borrow/HTB/stock-loan in py generators:")
for f in borrow_files:
    print("    ", os.path.relpath(f, ROOT))
OUT["borrow_decl_files"] = [os.path.relpath(f, ROOT) for f in borrow_files]

# diescrack short-leg intensity on champion days (the only declared cash-borrow short book)
dc = pd.read_csv(GEN["diescrack"], index_col=0, parse_dates=True).iloc[:, 0]
dc = dc[dc.index >= "2008-03-31"]
OUT["diescrack_rows"] = int(len(dc))
print(f"[4] diescrack: rows in champion window={len(dc)}")

json.dump(OUT, open(f"{ROOT}/campaign/agents/chief/coord/CAMP_BORROW/work_r5/r5_audit_state.json", "w"), indent=1)
print("\nCORE RE-DERIVATION OK — margin 2.70%/yr re-derived exactly; committed priced at 4.5%.")
