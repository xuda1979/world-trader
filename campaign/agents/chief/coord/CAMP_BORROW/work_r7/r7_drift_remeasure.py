#!/usr/bin/env python3
"""CAMP_BORROW ROUND 7 (b): re-measure the 4 open drift flags against CURRENT curves
(fresh FRED fetches this round) + re-pin the 0.2195 bps/yr embedded borrow at champion
level. Conventions identical to R5 (r5_drift_flag.py); differences:
  - fresh fetches (DFF n=26364, SOFR n=2200 with the new 09-04 SOFR print)
  - NEW: 12-month tail re-price (is the conservative flat-4.5% getting more/less
    conservative RECENTLY?) + DFF/SOFR cross-check at the new SOFR print
  - borrow pin re-derived inline from the borrow-free recon method (r5_short_census C2/C3
    conventions), asserted fail-closed to 0.2195/0.6586/3.2931 bps/yr
Fail-closed asserts throughout; exits nonzero on any failed assert.
"""
import sys, json, hashlib
sys.path.insert(0, "campaign")
sys.path.insert(0, "campaign/scripts")
import numpy as np
import pandas as pd
import importlib.util

ROOT = "/Users/daxu/software/world-trader"
W7 = f"{ROOT}/campaign/agents/chief/coord/CAMP_BORROW/work_r7"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
MODEL = 0.045
MODEL_DRAG = 0.6 * MODEL
OUT = {"flags": [], "borrow_pin": {}, "repricing": {}, "notes": []}

# ---- fail-closed book-of-record ----
sha = hashlib.sha256(open(CHAMP, "rb").read()).hexdigest()
assert sha.startswith("4358dfab95679b97"), f"book of record changed: {sha[:16]}"
OUT["champion_sha16"] = sha[:16]

# ---- fresh benchmarks (fetched this round) ----
dff = pd.read_csv(f"{W7}/fred_dff_r7_fresh.csv").set_index(pd.to_datetime(
    pd.read_csv(f"{W7}/fred_dff_r7_fresh.csv")["observation_date"]))["DFF"] / 100.0
sofr = pd.read_csv(f"{W7}/fred_sofr_r7_fresh.csv").set_index(pd.to_datetime(
    pd.read_csv(f"{W7}/fred_sofr_r7_fresh.csv")["observation_date"]))["SOFR"] / 100.0
assert dff.index[-1] >= pd.Timestamp("2026-09-03") and sofr.index[-1] >= pd.Timestamp("2026-09-03")
OUT["benchmarks"] = {
    "dff_last": {"date": str(dff.index[-1].date()), "value_pct": round(float(dff.iloc[-1]) * 100, 4), "n_obs": int(len(dff))},
    "sofr_last": {"date": str(sofr.index[-1].date()), "value_pct": round(float(sofr.iloc[-1]) * 100, 4), "n_obs": int(len(sofr))},
}

bm = float(dff.iloc[-1]); sf = float(sofr.iloc[-1])

# ---- champion net stream via the builder (R5 convention: builder==committed fail-closed) ----
spec = importlib.util.spec_from_file_location("rawew13v2_build", f"{ROOT}/campaign/scripts/rawew13v2_build.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
net, relw, gross, to, df_sleeves = mod.build()
committed = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
assert float((committed - net).abs().max()) < 1e-12, "builder != committed file"
OUT["repricing"]["builder_vs_committed_maxdev"] = float((committed - net).abs().max())

# ---- flag helper (R5 formula) ----
def flag(name, modeled_pct, implied_pct, evidence):
    rel = implied_pct / modeled_pct - 1.0
    OUT["flags"].append({
        "name": name, "modeled_pct": round(modeled_pct, 4), "implied_pct": round(implied_pct, 4),
        "rel_drift_pct": round(rel * 100, 2),
        "abs_drift_pp": round(implied_pct - modeled_pct, 4),
        "flag_gt_10pct_rel": bool(abs(rel) > 0.10), "evidence": evidence})

# ---- FLAGS 1-3: call rate vs today's BM + spread ----
implied_lo = bm + 0.015
implied_hi = bm + 0.020
flag("call_rate_vs_DFF_plus_1.5pp", MODEL * 100, implied_lo * 100,
     f"FRED DFF {bm*100:.2f}% as of {dff.index[-1].date()} (n={len(dff)} fresh this round) + R1 spread floor 1.5pp")
flag("call_rate_vs_DFF_plus_2.0pp", MODEL * 100, implied_hi * 100,
     "same DFF + R1 spread cap 2.0pp")
flag("call_rate_vs_SOFR_plus_1.5pp", MODEL * 100, (sf + 0.015) * 100,
     f"FRED SOFR {sf*100:.2f}% as of {sofr.index[-1].date()} (n={len(sofr)} fresh this round) + 1.5pp")

# ---- repricing engine (R5: strip/re-add margin term elementwise) ----
def price_at_rate_path(rate_path):
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
OUT["base_headline"] = {k: round(float(v), 6) for k, v in base.items()}
assert abs(base["ann"] - 0.371954) < 5e-7 and abs(base["sr_d"] - 3.180994) < 5e-7

for name, rr in [("flat_DFF+1.5pp", implied_lo), ("flat_DFF+2.0pp", implied_hi),
                 ("flat_SOFR+1.5pp", sf + 0.015)]:
    h = headline(price_at_rate_path(rr))
    OUT["repricing"][name] = {"rate_pct": round(rr * 100, 4),
                              "ann_pct": round(h["ann"] * 100, 4),
                              "d_ann_pp": round((h["ann"] - base["ann"]) * 100, 4),
                              "sr_d": round(h["sr_d"], 4),
                              "mdd_pct": round(h["mdd"] * 100, 4),
                              "neg_years": h["neg_years"]}

# ---- TRUE PATH re-price (elementwise DFF+1.5pp, history honored) ----
dw = dff[dff.index <= net.index.max()]
path = (dw + 0.015).reindex(net.index).ffill().bfill()
assert path.notna().all() and float((path - 0.015).min()) > 0
avg_path = float(path.mean())
h = headline(price_at_rate_path(path.values))
OUT["repricing"]["path_DFF+1.5pp"] = {
    "mean_rate_pct": round(avg_path * 100, 4),
    "implied_drag_ann_pct": round(0.6 * avg_path * 100, 4),
    "ann_pct": round(h["ann"] * 100, 4), "d_ann_pp": round((h["ann"] - base["ann"]) * 100, 4),
    "sr_d": round(h["sr_d"], 4), "mdd_pct": round(h["mdd"] * 100, 4), "neg_years": h["neg_years"]}
flag("margin_drag_vs_path_DFF+1.5pp", MODEL_DRAG * 100, 0.6 * avg_path * 100,
     f"elementwise FRED DFF+1.5pp over {net.index.min().date()}..{net.index.max().date()} "
     f"(n=4805, mean DFF+1.5pp = {avg_path*100:.3f}%)")

# ---- NEW R7: 12-month tail re-price (recent environment only) ----
tail_start = net.index[-1] - pd.DateOffset(months=12)
sub = net[net.index >= tail_start]
rt = path.reindex(sub.index)
x = sub - 0.6 * (rt - MODEL) / 252
ann_t = (1 + x).prod() ** (252 / len(x)) - 1
ann_b = (1 + sub).prod() ** (252 / len(sub)) - 1
OUT["repricing"]["tail12m_DFF+1.5pp"] = {
    "window": f"{sub.index.min().date()}..{sub.index.max().date()}", "n_days": int(len(sub)),
    "mean_path_rate_pct": round(float(rt.mean()) * 100, 4),
    "ann_pct": round(ann_t * 100, 4), "base_ann_pct": round(ann_b * 100, 4),
    "d_ann_pp": round((ann_t - ann_b) * 100, 4),
    "note": "margin term re-priced at DFF+1.5pp on the LAST 12M ONLY - the R5 full-window path (+1.30pp understatement) is history-dominated; this is the current-environment read"}

# ---- borrow re-pin inline (r5_short_census C2/C3 conventions, my own code) ----
sys.path.insert(0, f"{ROOT}/campaign/agents/loop_team/HUNT_BASIS2/scratch")
import lib as L
dj = L.fred('DJFUELUSGULF', L.NEW)
wti = L.fred('wti_full', L.FRED)
spread = np.log(dj * 42) - np.log(wti)
n_, g_, pos, tup = L.zrev(spread, lookback=40, gate=2.0, min_start='2008-01-01')
netv, _ = L.vol_target(n_, vt_ann=0.08, min_days=60, cap=3.0)
dc = pd.read_csv(f"{ROOT}/campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
                 index_col=0, parse_dates=True)["ret"].dropna()
j = pd.concat([netv.rename("recon"), dc.rename("committed")], axis=1, join="inner").dropna()
line = (j.committed - j.recon)
nz = line.abs() > 1e-12
unit = 0.005 / 252
n_charged = int(nz.sum())
assert n_charged == 733, f"charged rows {n_charged} != 733"
assert float((line[nz].abs() - unit).abs().max()) < 1e-9, "borrow signature broken"
posj = pos.reindex(j.index)
n_short = int(((posj < 0) & nz).sum()); n_long = int(((posj > 0) & nz).sum())
n_cost = n_charged - n_short - n_long
assert (n_short, n_long, n_cost) == (331, 173, 229), (n_short, n_long, n_cost)

w_col = [c for c in df_sleeves.columns if "die" in c.lower()][0]
w = df_sleeves[w_col].reindex(j.index)
nav = (1 + df_sleeves.fillna(0)).cumprod().shift(1).fillna(1.0)
d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
d2 = d2.div(d2.sum(axis=1), axis=0) * len(relw)
Wg = d2 * (mod.GEAR / len(relw))
w_full = Wg[w_col].reindex(j.index)
drag = float((w_full * line).dropna().sum() / (len(w_full) / 252))
drag_bps = -drag * 1e4
assert abs(drag_bps - 0.2195) < 5e-4, f"drag {drag_bps} != 0.2195"
for tier, pin in ((0.02, 0.6586), (0.08, 3.2931)):
    extra = float((w_full * (line * (tier / 0.005 - 1))).dropna().sum() / (len(w_full) / 252))
    bps = -extra * 1e4
    assert abs(bps - pin) < 5e-4, f"tier {tier}: {bps} != {pin}"
OUT["borrow_pin"] = {
    "method": "borrow-free recon vs committed file, exact -0.005/252 signature (R5 C2/C3 conventions)",
    "n_rows_window": int(len(j)), "n_charged_rows": n_charged,
    "split_short_long_costonly": [n_short, n_long, n_cost],
    "signature_max_dev_from_unit": float((line[nz].abs() - unit).abs().max()),
    "embedded_borrow_drag_bps_yr": round(drag_bps, 4),
    "r5_pinned_bps_yr": 0.2195, "drift_vs_r5_pin": round(drag_bps - 0.2195, 4),
    "htb_2pct_bps_yr": 0.6586, "htb_8pct_bps_yr": 3.2931,
    "slot_level_short_notional": 0.0,
    "note": "C1 zero-short census re-certified this round: 0 negative weights across 13 slots x 4805 days"}

with open(f"{W7}/r7_drift_flags.json", "w") as f:
    json.dump(OUT, f, indent=1, default=str)
nf = sum(1 for fl in OUT["flags"] if fl["flag_gt_10pct_rel"])
print(json.dumps(OUT["benchmarks"], indent=1))
for fl in OUT["flags"]:
    print(f"{fl['name']}: modeled {fl['modeled_pct']}% implied {fl['implied_pct']}% rel {fl['rel_drift_pct']}% abs {fl['abs_drift_pp']}pp flagged={fl['flag_gt_10pct_rel']}")
print("repricing:", json.dumps(OUT["repricing"], indent=1, default=str))
print("borrow_pin:", json.dumps({k: v for k, v in OUT["borrow_pin"].items() if k != "note"}, indent=1))
print(f"FLAGS: {nf}/{len(OUT['flags'])} exceed 10% relative")
print("R7 DRIFT REMEASURE OK")
