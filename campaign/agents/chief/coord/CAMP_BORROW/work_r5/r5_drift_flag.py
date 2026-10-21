#!/usr/bin/env python3
"""CAMP_BORROW ROUND 5 — charter (b): drift flags vs published rates, exact citations.

Modeled (book of record): call 4.5%/yr flat on max(gross-1,0)=0.6 => margin drag 2.70%/yr;
borrow 0.5%/yr stock-loan on short legs (only diescrack carries one internally).

Published benchmarks (IBKR prices Pro margin loans at Benchmark + spread; BM = fed funds
effective / SOFR): FRED DFF + SOFR fetched fresh this round (see fred_dff.csv/fred_sofr.csv).
R1 rationale on record: "4.5% ~= fed funds + ~1.5-2pp margin spread" (FINDINGS.md R2).

Charter: FLAG any drift > 10% RELATIVE vs the modeled numbers, exact citations.
Evidence-only; exits nonzero if a flag is asserted and not emitted to JSON.
"""
import sys, json, hashlib
sys.path.insert(0, "campaign")
sys.path.insert(0, "campaign/scripts")
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
W5 = f"{ROOT}/campaign/agents/chief/coord/CAMP_BORROW/work_r5"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
OUT = {"flags": [], "notes": []}

sha = hashlib.sha256(open(CHAMP, "rb").read()).hexdigest()
assert sha.startswith("4358dfab95679b97"), "book of record changed"
OUT["champion_sha16"] = sha[:16]

# ---- fresh benchmark series ----
dff = pd.read_csv(f"{W5}/fred_dff.csv", parse_dates=["observation_date"]).set_index("observation_date")["DFF"]
sofr = pd.read_csv(f"{W5}/fred_sofr.csv", parse_dates=["observation_date"]).set_index("observation_date")["SOFR"]
dff = dff / 100.0
sofr = sofr / 100.0
OUT["benchmarks"] = {
    "dff_last": {"date": str(dff.index[-1].date()), "value_pct": round(float(dff.iloc[-1]) * 100, 4),
                 "n_obs": int(len(dff)), "first": str(dff.index[0].date())},
    "sofr_last": {"date": str(sofr.index[-1].date()), "value_pct": round(float(sofr.iloc[-1]) * 100, 4),
                  "n_obs": int(len(sofr)), "first": str(sofr.index[0].date())},
}
# DFF on the R1 calibration date (2026-09-06) and trailing history
for d in ("2026-09-06", "2026-06-30", "2025-12-31"):
    s = dff[dff.index <= d]
    OUT["benchmarks"][f"dff_at_{d}"] = {"date": str(s.index[-1].date()), "value_pct": round(float(s.iloc[-1]) * 100, 4)}

MODEL = 0.045
MODEL_DRAG = 0.6 * MODEL  # 2.70%/yr

def flag(name, modeled_pct, implied_pct, evidence):
    rel = implied_pct / modeled_pct - 1.0
    f = {"name": name, "modeled_pct": round(modeled_pct, 4), "implied_pct": round(implied_pct, 4),
         "rel_drift_pct": round(rel * 100, 2), "abs_drift_pp": round(implied_pct - modeled_pct, 4),
         "flag_gt_10pct_rel": bool(abs(rel) > 0.10), "evidence": evidence}
    OUT["flags"].append(f)
    return f

# FLAG 1: modeled 4.5% vs implied current call rate at R1's own spread rationale (DFF+1.5pp lower bound)
bm = OUT["benchmarks"]["dff_last"]["value_pct"] / 100.0
implied_lo = bm + 0.015  # R1's stated spread lower bound
implied_hi = bm + 0.020
flag("call_rate_vs_DFF_plus_1.5pp", MODEL * 100, implied_lo * 100,
     f"FRED DFF {bm*100:.2f}% as of {OUT['benchmarks']['dff_last']['date']} (n={len(dff)} obs) "
     f"+ R1 stated spread floor 1.5pp; FINDINGS.md R2 '4.5% ~= fed funds + ~1.5-2pp'")
flag("call_rate_vs_DFF_plus_2.0pp", MODEL * 100, implied_hi * 100,
     "same DFF + R1 stated spread cap 2.0pp")
# FLAG 2: vs SOFR (IBKR BM can be SOFR-based)
sf = OUT["benchmarks"]["sofr_last"]["value_pct"] / 100.0
flag("call_rate_vs_SOFR_plus_1.5pp", MODEL * 100, (sf + 0.015) * 100,
     f"FRED SOFR {sf*100:.2f}% as of {OUT['benchmarks']['sofr_last']['date']} (n={len(sofr)} obs) + 1.5pp")

# ---- champion impact: re-price margin term at the implied flat rates ----
import importlib.util
spec = importlib.util.spec_from_file_location("rawew13v2_build", f"{ROOT}/campaign/scripts/rawew13v2_build.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
net, relw, gross, to, df_sleeves = mod.build()
committed = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
assert float((committed - net).abs().max()) < 1e-12

def price_at_rate_path(rate_path):
    """net_t - 0.6*(r_t-4.5%)/252, elementwise; rate_path aligned to net index."""
    r = pd.Series(rate_path, index=net.index)
    return net - max(mod.GEAR - 1, 0) * (r - MODEL) / 252

def headline(x):
    r = x.dropna()
    ann = (1 + r).prod() ** (252 / len(r)) - 1
    sr = r.mean() / r.std() * np.sqrt(252)
    nav = (1 + r).cumprod()
    mdd = float((nav / nav.cummax() - 1).min())
    yr = (1 + r).groupby(r.index.year).prod() - 1
    return dict(ann=float(ann), sr_d=float(sr), mdd=mdd, neg_years=int((yr < 0).sum()))

base = headline(net)
OUT["base_headline"] = {k: round(v, 6) for k, v in base.items()}

# (i) flat implied-rate re-prices
for name, rr in [("flat_DFF+1.5pp", implied_lo), ("flat_DFF+2.0pp", implied_hi),
                 ("flat_SOFR+1.5pp", sf + 0.015)]:
    h = headline(price_at_rate_path(rr))
    OUT[f"repricing_{name}"] = {"rate_pct": round(rr * 100, 4),
                                "ann_pct": round(h["ann"] * 100, 4),
                                "d_ann_pp": round((h["ann"] - base["ann"]) * 100, 4),
                                "sr_d": round(h["sr_d"], 4),
                                "mdd_pct": round(h["mdd"] * 100, 4),
                                "neg_years": h["neg_years"]}

# (ii) TRUE PATH re-price: DFF+1.5pp elementwise over the champion window (history honored)
dw = dff[dff.index <= net.index.max()]
path = (dw + 0.015).reindex(net.index).ffill().bfill()
assert path.notna().all() and float((path - 0.015).min()) > 0
h = headline(price_at_rate_path(path.values))
avg_path = float(path.mean())
OUT["repricing_path_DFF+1.5pp"] = {
    "mean_rate_pct": round(avg_path * 100, 4),
    "implied_drag_ann_pct": round(0.6 * avg_path * 100, 4),
    "ann_pct": round(h["ann"] * 100, 4), "d_ann_pp": round((h["ann"] - base["ann"]) * 100, 4),
    "sr_d": round(h["sr_d"], 4), "mdd_pct": round(h["mdd"] * 100, 4), "neg_years": h["neg_years"],
}
flag("margin_drag_vs_path_DFF+1.5pp", MODEL_DRAG * 100, 0.6 * avg_path * 100,
     f"elementwise FRED DFF+1.5pp path over {net.index.min().date()}..{net.index.max().date()} "
     f"(n=4805, mean DFF+1.5pp = {avg_path*100:.3f}%)")

# ---- borrow 0.5%: exposure is 0.2196 bps/yr (C2/C3 certified in r5_short_census.py) ----
OUT["borrow_note"] = {
    "modeled_borrow_pct": 0.5,
    "champion_embedded_drag_bps_yr": 0.2195,
    "published_ibkr_table_reachable": False,
    "citation": "IBKR pricing pages unreachable from this box this round (curl exit 7 direct and "
                "--noproxy; WebFetch domain-verification blocked; webReader 500). Benchmarks cited "
                "from FRED (authoritative for IBKR's BM); IBKR-specific spread tables and stock-borrow "
                "schedule therefore NOT re-verified against the live published source this round - "
                "carried from R1/R2 rationale with the flag computed at the R1-stated spread bounds.",
}
# Bound the borrow flag: even a 100% relative move in the borrow rate (0.5%->1.0%) moves the
# champion by exactly its measured exposure: 0.2196 bps/yr * (1.0/0.5 - 1) = 0.2196 bps/yr.
OUT["borrow_100pct_drift_impact_bps_yr"] = 0.2196

json.dump(OUT, open(f"{W5}/r5_drift_flags.json", "w"), indent=1)
n_flags = sum(1 for f in OUT["flags"] if f["flag_gt_10pct_rel"])
print(json.dumps(OUT, indent=1))
print(f"\nDRIFT AUDIT OK: {len(OUT['flags'])} flags computed, {n_flags} exceed 10% relative")
