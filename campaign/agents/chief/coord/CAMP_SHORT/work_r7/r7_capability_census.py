#!/usr/bin/env python3
"""CAMP_SHORT ROUND 7 charter (b) - capability-lane refresh on the CURRENT tree.

Re-runs the two R5/R6 capability invariants with OWN code (no CAMP_BORROW imports):
  B1. net-short census: 62,465 slot-days (4,805 days x 13 slots), ZERO net-short.
      Slot tree = rebuilt from the 13 sleeve CSVs via the committed builder recipe
      (relw = max(IS_SR,0)^0.55, IS_END 2017-01-01, gear 1.6); additionally pinned
      against the current ON-DISK sleeve files (mtimes+shas) so "current tree" is
      a measured statement, not an assumption.
  B2. 8% HTB tier arithmetic: 3.2931 bps/yr, re-derived from the committed diescrack
      CSV short-leg days x champion weights (NOT copied from anyone's JSON).
  B3. CAMP_BORROW's 4 open drift flags re-computed vs the fetched FRED benchmarks
      in their r5 artifacts (>10 pct rel each) + champion re-price at those rates.
  B4. tree-freshness: champion sha + 13 sleeve-file shas today vs R6 close.
"""
import hashlib
import json
import os
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = f"{ROOT}/campaign/agents/chief/coord/CAMP_SHORT/work_r7/r7_capability.json"
IS_END = pd.Timestamp("2017-01-01")
GEAR, RATE, BPS, P = 1.6, 0.045, 6.4, 0.55

R = {"tool": "CAMP_SHORT R7 capability refresh (own code)"}


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def sharpe_d(r):
    s = r.std(ddof=1)
    return 0.0 if (not s or not np.isfinite(s) or s < 1e-12) else float(r.mean() / s * np.sqrt(252))


def ann_geo(r):
    return float((1 + r).prod(min_count=1) ** (252.0 / len(r)) - 1)


def load_ret(p):
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)


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

# ---- B4 tree freshness ------------------------------------------------------
R["tree"] = {"champ_sha16": sha16(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"),
             "sleeve_shas": {n: sha16(p) for n, p in PATHS.items()},
             "sleeve_mtimes": {n: os.path.getmtime(p) for n, p in PATHS.items()},
             "git_dirty_results": subprocess.run(
                 ["git", "status", "--short", "campaign/results/"],
                 capture_output=True, text=True, cwd=ROOT).stdout.strip()}

# ---- B1 census --------------------------------------------------------------
df = pd.DataFrame({n: load_ret(PATHS[n]).dropna() for n in NAMES})
df = df[df.index >= "2008-03-31"]
isr = df[df.index < IS_END]
SR = pd.Series({n: sharpe_d(isr[n]) for n in NAMES})
relw = np.maximum(SR, 0.0) ** P
nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
d2 = d2.div(d2.sum(axis=1), axis=0) * len(NAMES)
Wg = d2 * (GEAR / len(NAMES))

slot_days = int(Wg.size)
n_neg = int((Wg < -1e-12).sum().sum())
per_slot = {c: int((Wg[c] < -1e-12).sum()) for c in Wg.columns}
R["B1_census"] = dict(slot_days=slot_days, expected=62465, n_negative_slot_days=n_neg,
                      pass_=slot_days == 62465 and n_neg == 0,
                      wmin=float(Wg.min().min()),
                      days=int(len(Wg)), slots=int(Wg.shape[1]),
                      span=(str(Wg.index[0].date()), str(Wg.index[-1].date())),
                      per_slot_negative_counts=per_slot)
# single-name equity check (the only single-name panel) still long-only
dm = Wg["dualmom"]
R["B1_census"]["dualmom_min_w"] = float(dm.min())

# ---- B2 8% HTB tier arithmetic (own derivation from committed files) --------
# (R6-proven own-algebra: borrow LINE = committed diescrack file minus borrow-free
# reconstruction; champion drag = slot-weighted line, annualized; tier uplift scales
# the line by (tier/0.005 - 1). Same block that reproduced 0.2195/0.6586/3.2931 to 5e-4.)
sys.path.insert(0, f"{ROOT}/campaign")
sys.path.insert(0, f"{ROOT}/campaign/scripts")
sys.path.insert(0, f"{ROOT}/campaign/agents/loop_team/HUNT_BASIS2/scratch")
import lib as L  # noqa: E402

dj = L.fred("DJFUELUSGULF", L.NEW)
wti = L.fred("wti_full", L.FRED)
spread = np.log(dj * 42) - np.log(wti)
n_, g_, pos, tup = L.zrev(spread, lookback=40, gate=2.0, min_start="2008-01-01")
netv, _ = L.vol_target(n_, vt_ann=0.08, min_days=60, cap=3.0)
dc = load_ret(PATHS["diescrack"])
j2 = pd.concat([netv.rename("recon"), dc.rename("committed")], axis=1, join="inner").dropna()
line = j2.committed - j2.recon
w_dc = Wg["diescrack"].reindex(line.index)
drag = float((w_dc * line).dropna().sum() / (len(w_dc) / 252))
bps_embed = -drag * 1e4
tiers = {}
for tier in (0.02, 0.08):
    extra = float((w_dc * (line * (tier / 0.005 - 1))).dropna().sum() / (len(w_dc) / 252))
    tiers[tier] = round(-extra * 1e4, 4)
R["B2_htb"] = dict(embedded_bps_yr=round(bps_embed, 4), htb2_bps_yr=tiers[0.02],
                   htb8_bps_yr=tiers[0.08],
                   claims_to_pin=dict(baseline=0.2195, htb2=0.6586, htb8=3.2931),
                   ok=bool(abs(bps_embed - 0.2195) < 5e-4 and abs(tiers[0.08] - 3.2931) < 5e-4
                           and abs(tiers[0.02] - 0.6586) < 5e-4))

# ---- B3 drift flags re-computed --------------------------------------------
fl = json.load(open(f"{ROOT}/campaign/agents/chief/coord/CAMP_BORROW/work_r5/r5_drift_flags.json"))
dff_last, sofr_last = fl["benchmarks"]["dff_last"], fl["benchmarks"]["sofr_last"]
flags = []
# their convention: rel_drift = (implied - modeled)/modeled (positive = modeled is LOW)
for name, modeled, bench_pct, sprd in [
        ("call_rate_vs_DFF_plus_1.5pp", 4.5, dff_last["value_pct"], 1.5),
        ("call_rate_vs_DFF_plus_2.0pp", 4.5, dff_last["value_pct"], 2.0),
        ("call_rate_vs_SOFR_plus_1.5pp", 4.5, sofr_last["value_pct"], 1.5)]:
    implied = bench_pct + sprd
    flags.append(dict(name=name, modeled_pct=modeled, implied_pct=round(implied, 2),
                      rel_drift_pct=round((implied - modeled) / modeled * 100, 2),
                      gt_10pct=bool(abs((implied - modeled) / modeled) > 0.10)))
# margin-drag path flag: elementwise DFF+1.5pp over the champion span
dser = pd.read_csv(f"{ROOT}/campaign/agents/chief/coord/CAMP_BORROW/work_r5/fred_dff.csv",
                   index_col=0, parse_dates=True).iloc[:, 0]
dser = dser / 100.0  # CSV stores percent
dff_path = dser.reindex(Wg.index).ffill().bfill()
mean_rate = float(dff_path.mean()) + 0.015  # fraction
modeled_drag = max(GEAR - 1, 0) * RATE  # 0.027
flags.append(dict(name="margin_drag_vs_path_DFF+1.5pp", modeled_pct=round(modeled_drag * 100, 2),
                  implied_pct=round(0.6 * mean_rate * 100, 4),
                  rel_drift_pct=round((0.6 * mean_rate - modeled_drag) / modeled_drag * 100, 2),
                  gt_10pct=bool(abs((0.6 * mean_rate - modeled_drag) / modeled_drag) > 0.10)))
R["B3_drift_flags_own"] = flags
R["B3_published"] = [{k: f[k] for k in ("name", "modeled_pct", "implied_pct", "rel_drift_pct")}
                     for f in fl["flags"]]

# champion re-price at the four implied rates (own margin line: 0.6 x rate/252 on (gross-1))
champ = load_ret(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")


def ann_of(r):
    return float((1 + r).prod(min_count=1) ** (252.0 / len(r)) - 1)


def negy(r):
    yr = (1 + r).groupby(r.index.year).prod(min_count=1) - 1
    return int((yr.where(np.isfinite(yr), -1.0) < 0).sum())


reprices = {}
for label, rate in [("flat_DFF+1.5pp", dff_last["value_pct"] / 100 + 0.015),
                    ("flat_DFF+2.0pp", dff_last["value_pct"] / 100 + 0.020),
                    ("flat_SOFR+1.5pp", sofr_last["value_pct"] / 100 + 0.015),
                    ("path_DFF+1.5pp", None)]:
    r_t = dff_path + 0.015 if rate is None else pd.Series(rate, index=champ.index)
    net_r = champ - max(GEAR - 1, 0) * (r_t.reindex(champ.index).fillna(RATE) - RATE) / 252
    reprices[label] = dict(ann_pct=round(ann_of(net_r) * 100, 4),
                           d_ann_pp=round((ann_of(net_r) - ann_of(champ)) * 100, 2),
                           neg_years=negy(net_r))
R["B3_reprices_own"] = reprices
R["B3_reprices_published"] = {"flat_DFF+1.5pp": 36.6784, "flat_DFF+2.0pp": 36.2695,
                              "flat_SOFR+1.5pp": 36.6538, "path_DFF+1.5pp": 38.4910}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(R, open(OUT, "w"), indent=1, default=str)
print(json.dumps(R, indent=1, default=str))
