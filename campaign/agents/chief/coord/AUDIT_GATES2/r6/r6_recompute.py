#!/usr/bin/env python3
"""AUDIT_GATES2 ROUND 6 — V2 conformance sweep: recompute cited R5 gate numbers from
published artifacts. One lane per charter item, docs-only, no bt/ or contract edits.

Lane A HUNT_CMDT2   : 28 prop_*.csv vs meta headline rows + v2_corrected lines
Lane B HUNT_VOL2    : pcr_overlay_scan.csv grid rules + cited extremes + gates.run re-run
Lane C HUNT_TIMESFM : TIMESFM_R5_*_daily.csv vs eval_r5_results.json vs FINDINGS numbers
Lane D CAMP_BORROW  : r5_drift_flag.py re-run (champion impact table) + margin arithmetic
Lane E RES_BASIS    : emit_sleeve.py re-run -> byte-identical CSV/meta, battery re-run
"""
import hashlib
import json
import re
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
CAMP = f"{ROOT}/campaign"
sys.path.insert(0, CAMP)

R = {"lanes": {}}


def sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def note(lane, k, v):
    R["lanes"].setdefault(lane, {})[k] = v


def sharpe_d(r):
    s = r.std(ddof=1)
    return 0.0 if (not s or not np.isfinite(s) or s < 1e-12) else float(r.mean() / s * np.sqrt(252))


def neg_years(r):
    yr = (1 + r).groupby(r.index.year).prod(min_count=1) - 1
    yr = yr.where(np.isfinite(yr), -1.0)
    return int((yr < 0).sum()), float(yr.min())


def half_split(r):
    k = len(r) // 2
    return sharpe_d(r.iloc[:k]), sharpe_d(r.iloc[k:])


def ann_geo(r):
    return float((1 + r).prod(min_count=1) ** (252.0 / len(r)) - 1)


def max_dd(r):
    eq = (1 + r).cumprod()
    return float((eq / eq.cummax() - 1).min())


# ============================================================ Lane A: HUNT_CMDT2
lane = "A_HUNT_CMDT2"
import glob
import os

meta_re = re.compile(
    r"^SR=(?P<sr>-?[\d.]+) ann=(?P<ann>-?[\d.]+)% vol=(?P<vol>-?[\d.]+)% "
    r"H1=(?P<h1>-?[\d.]+) H2=(?P<h2>-?[\d.]+) negyrs=(?P<neg>\d+) worstyr=(?P<worst>-?[\d.]+)% "
    r"corr_champ=(?P<corr>-?[\d.]+) n=(?P<n>\d+) (?P<start>[\d-]+)->(?P<end>[\d-]+)\n"
    r"gates: (?P<gates>.+)\n"
    r"v2: leak_corr=(?P<leakc>-?[\d.e-]+) leak_p=(?P<leakp>-?[\d.e-]+) leak_ok=(?P<leakok>\w+) "
    r"bp_ok=(?P<bpok>\w+) best_passive=(?P<bpname>[^:]+):(?P<bpsr>-?[\d.]+) sr=(?P<v2sr>-?[\d.]+) pass=(?P<v2pass>\w+)",
    re.M)

v2c_re = re.compile(
    r"v2_corrected: r=per-unit \(sig\*r==held book\) leak_corr=(?P<leakc>-?[\d.e-]+) "
    r"leak_p=(?P<leakp>-?[\d.e-]+) leak_ok=(?P<leakok>\w+) bp_ok=(?P<bpok>\w+) "
    r"best_passive=(?P<bpname>[^:]+):(?P<bpsr>-?[\d.]+) v2sr=(?P<v2sr>-?[\d.]+) "
    r"corr=(?P<corr>-?[\d.e-]+) pass=(?P<pass>\w+)")

rows, mism = [], []
for mp in sorted(glob.glob(f"{ROOT}/campaign/agents/chief/coord/HUNT_CMDT2/sleeves/prop_*.csv.meta")):
    name = os.path.basename(mp)[:-5]
    txt = open(mp).read()
    m = meta_re.search(txt)
    c = v2c_re.search(txt)
    if not m:
        mism.append((name, "META HEADLINE PARSE FAIL"))
        continue
    csv_p = mp[:-5]
    net = pd.read_csv(csv_p, index_col=0, parse_dates=True).iloc[:, 0]
    sr = sharpe_d(net)
    h1, h2 = half_split(net)
    neg, worst = neg_years(net)
    ann = ann_geo(net)
    row = dict(name=name, n_csv=len(net), sr_csv=round(sr, 4), ann_csv=round(ann * 100, 1),
               h1_csv=round(h1, 2), h2_csv=round(h2, 2), neg_csv=neg,
               worst_csv=round(worst * 100, 1),
               sr_meta=float(m["sr"]), ann_meta=float(m["ann"]), h1_meta=float(m["h1"]),
               h2_meta=float(m["h2"]), neg_meta=int(m["neg"]), worst_meta=float(m["worst"]),
               n_meta=int(m["n"]), start_meta=m["start"], end_meta=m["end"],
               v2sr_meta_distorted=float(m["v2sr"]),
               v2c_sr=float(c["v2sr"]) if c else np.nan,
               v2c_leak_corr=float(c["leakc"]) if c else np.nan,
               v2c_bp_ok=c["bpok"] if c else None,
               v2c_bpsr=float(c["bpsr"]) if c else np.nan,
               v2c_pass=c["pass"] if c else None)
    # tolerance: meta rounds (SR 2dp/4dp, ann 1dp, halves 2dp, worst 1dp)
    checks = dict(sr=abs(row["sr_csv"] - row["sr_meta"]) < 0.051,
                  ann=abs(row["ann_csv"] - row["ann_meta"]) < 0.35,
                  h1=abs(row["h1_csv"] - row["h1_meta"]) < 0.051,
                  h2=abs(row["h2_csv"] - row["h2_meta"]) < 0.051,
                  neg=row["neg_csv"] == row["neg_meta"],
                  worst=abs(row["worst_csv"] - row["worst_meta"]) < 0.35,
                  n=row["n_csv"] == row["n_meta"],
                  span=(str(net.index[0].date()) == row["start_meta"]
                        and str(net.index[-1].date()) == row["end_meta"]),
                  # corrected battery must still report FAIL and bp_ok False
                  v2c_fail=(row["v2c_pass"] == "false"),
                  v2c_bp=(row["v2c_bp_ok"] == "False"),
                  v2c_bpsr_reach=(abs(row["v2c_bpsr"] - 0.566) < 0.02))
    row["checks_pass"] = all(checks.values())
    if not all(checks.values()):
        mism.append((name, {k: v for k, v in checks.items() if not v}))
    rows.append(row)

dfA = pd.DataFrame(rows)
note(lane, "n_metas_checked", len(dfA))
note(lane, "n_mismatch", len(mism))
note(lane, "mismatches", [str(x) for x in mism])
note(lane, "v2c_bpsr_range", [float(dfA.v2c_bpsr.min()), float(dfA.v2c_bpsr.max())])
note(lane, "n_v2c_fail", int((dfA.v2c_pass == "false").sum()))
note(lane, "max_abs_sr_dev_csv_vs_meta", float((dfA.sr_csv - dfA.sr_meta).abs().max()))

# FINDINGS headline claims: family bests
fam_best_seas = dfA[dfA.name.str.startswith("prop_seas")].sr_csv.max()
fam_best_trend = dfA[dfA.name.str.startswith("prop_trend")].sr_csv.max()
fam_best_sprd = dfA[dfA.name.str.startswith("prop_spreadmr")].sr_csv.max()
note(lane, "family_best_sr", dict(seasonality=round(fam_best_seas, 3),
                                  trend=round(fam_best_trend, 3),
                                  spreadmr=round(fam_best_sprd, 3)))
# FINDINGS quotes: "TREND family best 0.47 w21 long-only vt SR 0.465 ann 3.8%"
w21 = dfA[dfA.name == "prop_trend_w21_lo_vt.csv"].iloc[0]
note(lane, "w21_lo_vt_csv_sr", round(w21.sr_csv, 3))
note(lane, "w21_lo_vt_csv_ann", float(w21.ann_csv))
note(lane, "w21_lo_vt_meta_sr", float(w21.sr_meta))
note(lane, "w21_lo_vt_meta_ann", float(w21.ann_meta))
# "12-02 novt SR 0.205"
s2 = dfA[dfA.name == "prop_seas_12-02_novt.csv"].iloc[0]
note(lane, "seas12-02_novt_sr_csv", round(s2.sr_csv, 3), )
note(lane, "seas12-02_novt_meta_sr", float(s2.sr_meta))
# "decorrelation |corr|<=0.052 all 28"
note(lane, "max_abs_corr_champ_meta", float(dfA.sr_meta.max() * 0 + 0))  # placeholder
corrs = []
for mp in sorted(glob.glob(f"{ROOT}/campaign/agents/chief/coord/HUNT_CMDT2/sleeves/prop_*.csv.meta")):
    txt = open(mp).read()
    mm = re.search(r"corr_champ=(-?[\d.]+)", txt)
    corrs.append(abs(float(mm.group(1))))
note(lane, "max_abs_corr_champ_meta", max(corrs))

# ============================================================ Lane B: HUNT_VOL2
lane = "B_HUNT_VOL2"
scan = pd.read_csv(f"{ROOT}/campaign/agents/chief/coord/HUNT_VOL2/work_r5/pcr_overlay_scan.csv")
unf = pd.read_csv(f"{ROOT}/campaign/agents/chief/coord/HUNT_VOL2/work_r5/pcr_overlay_scan_UNFILTERED_disclosure.csv")
note(lane, "scan_rows", len(scan))
note(lane, "unfiltered_rows", len(unf))
note(lane, "scan_8c_pass_dAnn_gt0", int((scan.d_ann > 0).sum()))
note(lane, "unf_8c_pass_dAnn_gt0", int((unf.d_ann > 0).sum()))
note(lane, "scan_best_dAnn", float(scan.d_ann.max()))
note(lane, "unf_best_dAnn", float(unf.d_ann.max()))
b8 = scan.loc[scan.d_ann.idxmax()]
note(lane, "scan_best_dAnn_variant", f"{b8.series} {b8.kind} {b8.op}{b8.thr} to={b8.to}")
bu = unf.loc[unf.d_ann.idxmax()]
note(lane, "unf_best_dAnn_variant", f"{bu.series} {bu.kind} {bu.op}{bu.thr} to={bu.to}")
note(lane, "scan_best_dSR", float(scan.d_sr.max()))
bd = scan.loc[scan.d_sr.idxmax()]
note(lane, "scan_best_dSR_variant_dH2", float(bd.d_h2))
note(lane, "scan_8d_pass", int(((scan.d_sr >= 0) & (scan.d_h2 >= 0)).sum()))
note(lane, "scan_8a_count_nety0", int((scan.neg_yrs_net == 0).sum()))
note(lane, "scan_8b_count_mdd_gt_-7", int((scan.net_mdd > -7).sum()))
note(lane, "leak_ok_all", bool(scan.leak_ok.all()))
note(lane, "max_abs_leak_corr", float(scan.leak_corr.abs().max()))
# era claim: best variants positive in 1/3 and 1/5
for tag, rowx in [("pcr_vix_z2_to0.5", scan[(scan.series == "pcr_vix") & (scan.kind == "z") & (scan.thr == 2.0) & (scan.to == 0.5)]),
                  ("pcr_equity_level0.9_to0.5", scan[(scan.series == "pcr_equity") & (scan.kind == "level") & (scan.thr == 0.9) & (scan.to == 0.5)])]:
    e3 = [rowx.iloc[0][f"era{i}of3"] for i in (1, 2, 3)]
    e5 = [rowx.iloc[0][f"era{i}of5"] for i in (1, 2, 3, 4, 5)]
    note(lane, f"era_pos_{tag}", dict(of3=int(sum(1 for x in e3 if x > 0)), of5=int(sum(1 for x in e5 if x > 0)),
                                      e3=[float(x) for x in e3], e5=[float(x) for x in e5]))

# independent rebuild of ONE variant end-to-end (pcr_vix z>2.0 to=0.5) from raw inputs
sys.path.insert(0, f"{ROOT}/campaign/agents/chief/coord/HUNT_VOL2/work_r5")
import pcr5_lib as L  # noqa: E402

champ_full = L.champion()
w, champ_w = L.window_frame("pcr_vix")
g = L.pcr_gate(w["pcr_vix"], kind="z", op="gt", thr=2.0, to=0.5, minp=502)
net = L.overlay_net(g, champ_w)
d = L.delta_stats(net, champ_w)
note(lane, "rebuild_pcr_vix_z2_to0.5", dict(d_ann_pp=round(d["d_ann"] * 100, 3),
                                            d_sr=round(d["d_sr"], 4), d_mdd_pp=round(d["d_mdd"] * 100, 3),
                                            freq=round(L.trim_frequency(g, 0.5), 4),
                                            n=int(d["net"]["n"])))
sc = scan[(scan.series == "pcr_vix") & (scan.kind == "z") & (scan.thr == 2.0) & (scan.to == 0.5)].iloc[0]
note(lane, "scan_row_same_variant", dict(d_ann=round(float(sc.d_ann), 3), d_sr=float(sc.d_sr),
                                         d_mdd=float(sc.d_mdd), freq=float(sc.freq)))
# gates.run re-run on the rebuilt overlay
sig = g.reindex(champ_w.index).fillna(1.0).shift(1).fillna(1.0).values
res = L.gate_run(net, champ_full, sig=sig)
note(lane, "gates_run_rebuild", dict(leak_ok=bool(res["leak_ok"]), scr_p=float(res["scr_p"]),
                                     leak_corr=float(res["leak"]["same_period_corr"]),
                                     pass_=bool(res["pass"])))

# ============================================================ Lane C: HUNT_TIMESFM
lane = "C_HUNT_TIMESFM"
ev = json.load(open(f"{ROOT}/campaign/agents/chief/coord/HUNT_TIMESFM/work_r5/eval_r5_results.json"))
tfm_rows = []
for key, metafile in [("NKY_f1", "TIMESFM_R5_NKY_f1_daily.csv"),
                      ("NKY_f5", "TIMESFM_R5_NKY_f5_daily.csv"),
                      ("PROP_f1", "TIMESFM_R5_PROP_f1_daily.csv"),
                      ("PROP_f5", "TIMESFM_R5_PROP_f5_daily.csv")]:
    p = f"{ROOT}/campaign/agents/chief/coord/HUNT_TIMESFM/sleeves/{metafile}"
    dcol = "observation_date" if "NKY" in metafile else "date"
    df = pd.read_csv(p, parse_dates=[dcol]).set_index(dcol)
    net = df["net"]
    rpu = df["rpu"]
    wgt = df["w"]
    sr = sharpe_d(net)
    h1, h2 = half_split(net)
    neg, worst = neg_years(net)
    ann = ann_geo(net)
    # book identity: w*rpu == net exactly? (their TDD locks this)
    ident = float((wgt * rpu - net).abs().max())
    tfm_rows.append(dict(key=key, n_csv=len(net), n_json=ev[f"{key} [full]"]["n"],
                         sr_csv=round(sr, 4), sr_json=ev[f"{key} [full]"]["sr"],
                         h1_csv=round(h1, 4), h1_json=ev[f"{key} [full]"]["h1"],
                         h2_csv=round(h2, 4), h2_json=ev[f"{key} [full]"]["h2"],
                         neg_csv=neg, neg_json=ev[f"{key} [full]"]["neg_years"],
                         worst_csv=round(worst, 4), worst_json=ev[f]["worst"] if False else ev[f"{key} [full]"]["worst"],
                         ann_csv=round(ann * 100, 2), ann_json=round(ev[f"{key} [full]"]["ann"] * 100, 2),
                         ident_max_dev=ident,
                         span_csv=(str(net.index[0].date()), str(net.index[-1].date())),
                         span_json=(ev[f"{key} [full]"]["span_start"], ev[f"{key} [full]"]["span_end"])))
tfmA = pd.DataFrame(tfm_rows)
note(lane, "table", tfmA.to_dict("records"))
note(lane, "all_identity_max_dev", float(tfmA.ident_max_dev.max()))
note(lane, "all_pass_json", all(json.load(open(f"{ROOT}/campaign/agents/chief/coord/HUNT_TIMESFM/work_r5/eval_r5_results.json"))[f"{k} [full]"]["PASS"] is False for k in ["NKY_f1", "NKY_f5", "PROP_f1", "PROP_f5"]))

# PROP_f1 beats-passive independent check on the champion window (their claim: bp_best spy_bh 0.5643)
sys.path.insert(0, f"{ROOT}/campaign")
from bt.beats_passive import best_passive_sr  # noqa: E402

PROP = f"{ROOT}/campaign/agents/chief/coord/HUNT_TIMESFM/sleeves/TIMESFM_R5_PROP_f1_daily.csv"
pnet = pd.read_csv(PROP, parse_dates=["date"]).set_index("date")["net"]
pw = pnet[(pnet.index >= "2007-04-02")]
spy = pd.read_csv(f"{ROOT}/tools/quant/data/twelvedata/SPY.csv", index_col=0, parse_dates=True)["close"].pct_change()
ief = pd.read_csv(f"{ROOT}/tools/quant/data/more_etf/IEF.csv", index_col=0, parse_dates=True)["close"].pct_change()
cta = pd.read_csv(f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv", index_col=0, parse_dates=True)["ret"]
bp_best_sr, bp_info = best_passive_sr(pw, spy=spy, ief=ief, cta=cta)
note(lane, "PROP_f1_champwin_best_passive_sr", round(float(bp_best_sr), 4))
note(lane, "PROP_f1_champwin_bp_detail", {k: (round(v, 4) if isinstance(v, float) else v)
                                          for k, v in bp_info.items()})

# ============================================================ Lane D: CAMP_BORROW
lane = "D_CAMP_BORROW"
fl = json.load(open(f"{ROOT}/campaign/agents/chief/coord/CAMP_BORROW/work_r5/r5_drift_flags.json"))
note(lane, "n_flags", len(fl["flags"]))
note(lane, "flags_gt_10pct", [f["name"] for f in fl["flags"] if f["flag_gt_10pct_rel"]])
note(lane, "benchmarks", fl["benchmarks"]["dff_last"], )
note(lane, "sofr_last", fl["benchmarks"]["sofr_last"])
note(lane, "base_headline", fl["base_headline"])
for k in ["repricing_flat_DFF+1.5pp", "repricing_flat_DFF+2.0pp", "repricing_flat_SOFR+1.5pp",
          "repricing_path_DFF+1.5pp"]:
    note(lane, k, fl.get(k))
# margin arithmetic: 0.6*4.5%/252 in bps/day
note(lane, "margin_bps_day", 0.6 * 0.045 / 252 * 1e4)
# re-run their drift script fresh (it asserts champion sha + rebuild < 1e-12)
p = subprocess.run([sys.executable, f"{ROOT}/campaign/agents/chief/coord/CAMP_BORROW/work_r5/r5_drift_flag.py"],
                   capture_output=True, text=True, timeout=1200)
note(lane, "rerun_exit", p.returncode)
note(lane, "rerun_tail", p.stdout.strip().splitlines()[-1] if p.stdout.strip() else p.stderr[-300:])
fl2 = json.load(open(f"{ROOT}/campaign/agents/chief/coord/CAMP_BORROW/work_r5/r5_drift_flags.json"))
note(lane, "rerun_flags_match_saved", fl2 == fl)

# ============================================================ Lane E: RES_BASIS
lane = "E_RES_BASIS"
S = f"{ROOT}/campaign/team/agents/RES_BASIS/sleeves"
cand_csv = f"{S}/RB_hobr_crack_hyst_w63_z10_zo10.csv"
note(lane, "sleeve_sha16_now", sha16(cand_csv))
note(lane, "sleeve_sha_meta", "da0285b9a7a5e6a2")
cand = pd.read_csv(cand_csv, index_col=0, parse_dates=True)["ret"]
sr = sharpe_d(cand)
h1, h2 = half_split(cand)
neg, worst = neg_years(cand)
note(lane, "net_stats_from_csv", dict(n=len(cand), sr=round(sr, 4), ann=round(ann_geo(cand) * 100, 2),
                                      mdd=round(max_dd(cand) * 100, 2), h1=round(h1, 3), h2=round(h2, 3),
                                      neg=neg, worst=round(worst * 100, 2),
                                      span=(str(cand.index[0].date()), str(cand.index[-1].date()))))
note(lane, "meta_claims", dict(sr=1.3498, ann=13.25, mdd=-22.29, h1=2.182, h2=0.753, neg=1,
                               worst=-0.69, n=4604, span=("2008-02-19", "2026-08-25")))

# battery re-run from published code path (emit_sleeve imports run_hunt + hunt_r1)
import importlib.util


def run_module(path):
    spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path)
    mod = json_mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True)["ret"]
import bt.gates as G6  # noqa: E402

hb = run_module(f"{ROOT}/campaign/team/agents/RES_BASIS/hunt_r1.py")
rh = run_module(f"{ROOT}/campaign/team/agents/RES_BASIS/run_hunt.py")
d6 = rh.spreads()["ho_br"]
net6, We6, gross6, rpu6 = hb.pair_book(d6["r_a"], d6["r_b"], d6["spread"], win=63, z_in=1.0,
                                       z_out=1.0, side="meanrev", return_rpu=True)
live6 = (We6.fillna(0) != 0).any(axis=1)
net6 = net6[net6.index >= live6.idxmax()]
We6 = We6[We6.index >= net6.index[0]]
note(lane, "rebuild_matches_csv", float((net6 - cand.reindex(net6.index)).abs().max()))
note(lane, "rebuild_n", len(net6))
spy6, ief6, cta6 = rh.benchmark_series()
v26 = rh.v2_battery(rpu6.reindex(We6.index).fillna(0.0), sig=We6["a"].fillna(0.0), ref=champ,
                    spy=spy6, ief=ief6, cta=cta6)
note(lane, "v2_battery_rerun", dict(sr=round(v26["sr"], 4), corr=round(v26["corr"], 4),
                                    leak_corr=round(v26["leak"]["same_period_corr"], 4),
                                    leak_p=v26["leak"]["same_period_p"],
                                    leak_lag={k: round(v, 4) for k, v in v26["leak"]["lag_scan"].items()},
                                    leak_ok=bool(v26["leak_ok"]), scr_p=float(v26["scr_p"]),
                                    bp_best=v26["beats_passive"]["best_passive_name"],
                                    bp_best_sr=round(v26["beats_passive"]["best_passive_sr"], 4),
                                    bp_cand=round(v26["beats_passive"]["candidate_sr"], 4),
                                    bp_ok=bool(v26["beats_passive_ok"]),
                                    PASS=bool(v26["pass"])))
# blend arithmetic w=0.25 (fill-0 convention per coordinator's 11:4x check)
from bt.metrics import neg_years as ny6  # noqa: E402

c_al = champ.reindex(net6.index).fillna(0.0)
for w6 in (0.10, 0.25, 0.50):
    bl = c_al + w6 * net6
    blsr = sharpe_d(bl)
    note(lane, f"blend_w{w6}", dict(dSR=round(blsr - sharpe_d(c_al), 3),
                                    dAnn_pp=round((ann_geo(bl) - ann_geo(c_al)) * 100, 2),
                                    blendMDD_pct=round(max_dd(bl) * 100, 2),
                                    neg=int(ny6(bl)[0]),
                                    dH2=round(half_split(bl)[1] - half_split(c_al)[1], 3)))

json.dump(R, open(f"{ROOT}/campaign/agents/chief/coord/AUDIT_GATES2/r6/r6_recompute.json", "w"),
          indent=1, default=str)
print(json.dumps(R, indent=1, default=str))
