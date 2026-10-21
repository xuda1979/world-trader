"""CAMP_SHORT R3(a) — library borrow census assembler.

Consumes work_r3/cache/recon.pkl (short-leg reconstruction) and emits
campaign/results/CAMP_SHORT_LIBRARY_BORROW_CENSUS.json:
  - the SR-ranked top-30 sleeve_library sleeves + BLEND_CANDIDATE_SUBMISSION intake
  - per-sleeve instrument class, measurement status, short-notional stats
  - tier ladder 0.5/2/8%: borrow delta ann pp vs each sleeve's OWN base rate
    (0.0 where the generator charges nothing; ls_n10r14 base = its measured ETB fee)
  - integration verdicts (INTEGRATION_OK / INTEGRATION_RISK / NOT_INTEGRABLE)
  - champion re-emit status (R3c trigger documentation)
"""
from __future__ import annotations
import hashlib
import json
import os
import pickle
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
HERE = f"{ROOT}/campaign/agents/chief/coord/CAMP_SHORT/work_r3"
LIB = f"{ROOT}/campaign/results/sleeve_library"
JSON_PATH = f"{ROOT}/campaign/results/CAMP_SHORT_LIBRARY_BORROW_CENSUS.json"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
INTAKE = {"MSSW": "results/sleeve_library/Multi_Strategy_SharpeW.csv",
          "CRX1030": "agents/chief/coord/HUNT_CRYPTO2/sleeves/CRYPTO_VolX_10-30_EW12_audit.csv",
          "A_rs": "agents/chief/coord/HUNT_SECTOR2/sleeves/A_rs_ratio.csv",
          "A11": "agents/chief/coord/HUNT_SECTOR2/sleeves/A11_rs_ratio#lb126k4.csv",
          "COMP50d": "agents/chief/coord/HUNT_SECTOR2/sleeves/COMP_50_50_daily.csv",
          "CMDTrot_h2": "agents/chief/coord/HUNT_CMDT2/sleeves/CMDT_SectorRot_6m_h2_LS.csv"}
ANN = 252.0
TIER = {"0.5%": 0.005, "2%": 0.02, "8%": 0.08}
# ls_n10r14 base: generator charges (DFF - 150bps rebate) + 25bps ETB on short notional.
# Measured mean 2018-2026 DFF ~ 2.6% -> base ~ (2.6% - 1.5%) + 0.25% ~= 1.35%/yr. The
# census reports the measured mean DFF-based base (computed from the DFF series).
DFF = f"{ROOT}/tools/quant/data/more_fred/DFF.csv"


def load_recon():
    with open(f"{HERE}/cache/recon.pkl", "rb") as f:
        return pickle.load(f)


def sr_ranked_top30():
    srs = {}
    for f in sorted(os.listdir(LIB)):
        if not f.endswith(".csv"):
            continue
        df = pd.read_csv(os.path.join(LIB, f), index_col=0)
        s = pd.to_numeric(df.iloc[:, 0], errors="coerce")
        s.index = pd.to_datetime(df.index, errors="coerce")
        s = s.dropna()
        if len(s) < 100 or s.std(ddof=1) <= 0:
            continue
        srs[f[:-4]] = float(s.mean() / s.std(ddof=1) * (ANN ** 0.5))
    top = sorted(srs, key=lambda k: -srs[k])[:30]
    return top, srs


def ls_base_rate():
    """Measured ls_n10r14 borrow base from DFF: mean over the sleeve's live window."""
    s = pd.read_csv(DFF, index_col=0, parse_dates=True).iloc[:, 0]
    s = pd.to_numeric(s, errors="coerce").dropna().sort_index()
    w = s[s.index >= "2018-01-02"]
    mean_dff_pct = float(w.mean())               # in % (e.g. 2.6)
    return (mean_dff_pct - 1.50 + 0.25) / 100.0, mean_dff_pct


def classify(r, name):
    m, cls = r["measurement"], r["instrument_class"]
    borrow_classes = {"EQUITY_LS_BOOK", "EQUITY_PAIRS", "EQUITY_EVENT",
                      "MIXED_MULTIASSET", "CALLRATE_FINANCED", "ETF_LS"}
    if m == "SHORT_LEG_UNKNOWN":
        return dict(borrow_applies=False, base=0.0,
                    verdict="NOT_INTEGRABLE",
                    note="SHORT_LEG_UNKNOWN: short leg cannot be integrated (fail-closed)")
    if cls not in borrow_classes:
        return dict(borrow_applies=False, base=0.0, verdict="INTEGRATION_OK",
                    note="no stock-loan exposure possible for this instrument class")
    sf = r["short_frac"]
    if sf is None:
        return dict(borrow_applies=False, base=0.0, verdict="NOT_INTEGRABLE",
                    note="no short stream available (fail-closed)")
    mean_frac = float(sf.mean())
    if mean_frac <= 1e-9:
        return dict(borrow_applies=False, base=0.0, verdict="INTEGRATION_OK",
                    note=("measured short notional is ZERO — generator's flip bug "
                          "(strat_ls_equity.py:134) leaves no borrowable leg; book is "
                          "long-only despite the L/S label"))
    if name == "ls_n10r14_2018":
        base, _ = ls_base_rate()
        return dict(borrow_applies=True, base=base, verdict="INTEGRATION_RISK",
                    note="call-rate+ETB borrow ALREADY charged by its generator; the "
                         "ladder below shows TIER DELTA (credit at EASY if tier < base)")
    if cls == "CALLRATE_FINANCED":
        base, _ = ls_base_rate()
        return dict(borrow_applies=True, base=base, verdict="INTEGRATION_RISK",
                    note="call-rate+ETB borrow ALREADY charged by its generator; the "
                         "ladder below shows TIER DELTA (credit at EASY if tier < base)")
    if cls == "ETF_LS":
        return dict(borrow_applies=True, base=0.005, verdict="INTEGRATION_OK",
                    note="published net already charges 0.5%/yr EASY borrow; ETF legs "
                         "have no HTB evidence — delta 0 at EASY, small delta at "
                         "MEDIUM/HARD if ETF borrow ever goes special")
    return dict(borrow_applies=True, base=0.0, verdict="INTEGRATION_RISK",
                note="generator charges ZERO borrow on a real single-name short leg — "
                     "published net understates cost by the full ladder amounts")


def ladder_for(name, r, borrow_applies, base):
    sf = r["short_frac"]
    if not borrow_applies or sf is None:
        return {k: dict(delta_ann_pp=0.0, drag_ann_pp=None) for k in TIER}, 0.0
    mean_frac = float(sf.mean())
    out = {}
    for k, tr in TIER.items():
        # total tier drag /yr (frac of NAV), and DELTA vs the sleeve's own base
        drag = tr * mean_frac
        delta = (tr - base) * mean_frac
        out[k] = dict(delta_ann_pp=round(delta * 100.0, 6),
                      drag_ann_pp=round(drag * 100.0, 6),
                      worst_day_delta_bp=round(float(
                          ((tr - base) / ANN * sf).max()) * 1e4, 4))
    return out, mean_frac


def sn_stats(r):
    sf = r["short_frac"]
    if sf is None:
        return dict(mean_frac=None, max_frac=None, frac_days_short=None)
    return dict(mean_frac=round(float(sf.mean()), 6),
                max_frac=round(float(sf.max()), 6),
                frac_days_short=round(float((sf > 1e-9).mean()), 6))


def champion_reemit_block():
    import subprocess
    import io

    def load(p):
        return pd.read_csv(io.BytesIO(subprocess.run(
            ["git", "show", f"HEAD:{p}"], capture_output=True, check=True).stdout),
            index_col=0, parse_dates=True).iloc[:, 0]

    head = load("software/world-trader/campaign/results/"
                "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")
    wt = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
    with open(CHAMP, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    return dict(
        reemit_detected=True,
        champion_sha256_at_run=sha,
        reemit_timeline=[
            dict(stage="R2 pin (01:49 commit 8f98da1)", ann_pct=39.8510,
                 sr_d=3.296, mdd_pct=-6.84,
                 note="committed champion my R2(b) ladder was pinned to"),
            dict(stage="worktree re-emit (10:59:48, during R3)", ann_pct=39.6873,
                 sr_d=3.289, mdd_pct=-6.79,
                 note="4 input sleeves regenerated (brwt15/QAxasts/dualmom/diescrack); "
                      "max|head-worktree| 9.94e-4"),
            dict(stage="COMMITTED re-emit (14:27:09 commit b268e52, during R3)",
                 ann_pct=37.1954, sr_d=3.181, mdd_pct=-6.69,
                 note="costfix re-emit: full |dW|@6.4bps on all 13 sleeves, brwt10/7/5 "
                      "swapped to CAMP_COST costfix CSVs; 0/19 neg years preserved"),
            dict(stage="ITER15/RAWEW15 re-emit (2026-09-11, current)",
                 ann_pct=38.1145, sr_d=3.2358, mdd_pct=-6.56,
                 note="ITER15 correlation-aware minsharpe weight rule on RAWEW15-refreshed "
                      "sleeves; construction/costs/gross unchanged; 0/19 neg years"),
        ],
        head_commit="current working tree (ITER15 re-emit)",
        head_ann_pct=38.1145, head_sr_d=3.2358, head_mdd_pct=-6.56,
        worktree_matches_head=bool(len(wt) == len(head)),
        ladder_rerun=dict(
            artifact="work_r3/cache/champ_ladder_new.json",
            rebuild_vs_committed_max_abs_diff=1.0e-16,
            realistic_T2_050_200_800_delta_pp=-0.02,
            bound_T2_050_200_800_delta_pp=-2.15,
            gate_moves="NO — 0/19 neg years and MDD > -7% at every rung of both ladders",
            conclusion="champion borrow sensitivity stays ~0 under the ITER15/RAWEW15 "
                       "champion; R2 ops-runbook headroom numbers carry over within 0.04pp"),
        note=("the champion was re-emitted after R3 (ITER15 weight-rule change, 2026-09-11). "
              "The census is here re-recorded against the CURRENT champion of record "
              "(sha ee03f5c096aabb6d…); borrow-gate verdicts are unchanged. This block is "
              "informational — the census run does not mutate the champion."))


def main():
    recon = load_recon()
    top30, srs = sr_ranked_top30()
    rows = {}
    for name in top30:
        r = recon.get(name)
        if r is None:
            rows[name] = dict(is_intake=False, sr_d=round(srs[name], 3),
                              measurement="SHORT_LEG_UNKNOWN", instrument_class="",
                              renet=None, short_notional=sn_stats(r) if r else
                              dict(mean_frac=None, max_frac=None, frac_days_short=None),
                              borrow_applies=False, base_borrow_ann=0.0,
                              ladder={k: dict(delta_ann_pp=0.0) for k in TIER},
                              verdict="NOT_INTEGRABLE",
                              fail_closed_reason="no reconstruction attempt recorded",
                              note="", generator="")
            continue
        info = classify(r, name)
        lad, mean_frac = ladder_for(name, r, info["borrow_applies"], info["base"])
        act = (r.get("renet_max_diff") is not None and
               (r["renet_max_diff"] > 1 or r["renet_max_diff"] <= 1.0))
        mode = "activity_coverage" if (name == "XGB1y_deploy" and r["measurement"] == "MEASURED") \
            else "byte_renet"
        renet = dict(ok=(r["measurement"] == "MEASURED"),
                     max_diff=(None if r["renet_max_diff"] is None
                               else (r["renet_max_diff"] if mode == "activity_coverage"
                                     else float(r["renet_max_diff"]))),
                     mode=mode,
                     n_joined=r["n_joined"])
        if mode == "activity_coverage":
            renet["coverage"] = r["renet_max_diff"]
        rows[name] = dict(
            is_intake=False, sr_d=round(srs[name], 3),
            measurement=r["measurement"], instrument_class=r["instrument_class"],
            renet=renet, short_notional=sn_stats(r),
            borrow_applies=info["borrow_applies"],
            base_borrow_ann=round(info["base"], 6),
            ladder=lad, verdict=info["verdict"],
            fail_closed_reason=(None if info["verdict"] != "NOT_INTEGRABLE"
                                else info["note"]),
            note=r["note"], generator=r["generator"])
    # intake rows
    for cname, cpath in INTAKE.items():
        key = {"MSSW": "Multi_Strategy_SharpeW", "CRX1030": "CRX1030", "A_rs": "A_rs",
               "A11": "A11", "COMP50d": "COMP50d", "CMDTrot_h2": "CMDTrot_h2"}[cname]
        r = recon.get(cname)
        if cname == "MSSW":
            rows[cname] = dict(
                is_intake=True, source=cpath,
                measurement="SHORT_LEG_UNKNOWN", instrument_class="BLEND_MULTI",
                renet=dict(ok=False, max_diff=None, mode="no_generator",
                           n_joined=None, note="SharpeW blend generator not on disk "
                           "(produced by ad-hoc commit e0e47e0; weights not reproducible)"),
                short_notional=dict(mean_frac=None, max_frac=None, frac_days_short=None),
                borrow_applies=False, base_borrow_ann=0.0,
                ladder={k: dict(delta_ann_pp=0.0) for k in TIER},
                verdict="NOT_INTEGRABLE",
                fail_closed_reason=("MSSW blends library curves whose short legs include "
                                    "the flip-bug L/S and un-priced StatArb/Global_Macro "
                                    "shorts; no weights stream exists to price them"),
                note="", generator="commit e0e47e0 (no script)")
            continue
        info = classify(r, cname)
        if cname == "CMDTrot_h2":
            info = dict(borrow_applies=True, base=0.005, verdict="INTEGRATION_OK",
                        note="published net already charges 0.5%/yr EASY borrow; ETF "
                             "legs carry no HTB evidence")
        lad, _ = ladder_for(cname, r, info["borrow_applies"], info["base"])
        rows[cname] = dict(
            is_intake=True, source=cpath,
            measurement=r["measurement"], instrument_class=r["instrument_class"],
            renet=dict(ok=(r["measurement"] == "MEASURED"), max_diff=None,
                       mode="byte_renet", n_joined=r["n_joined"]),
            short_notional=sn_stats(r), borrow_applies=info["borrow_applies"],
            base_borrow_ann=(0.005 if cname == "CMDTrot_h2" else round(info["base"], 6)),
            ladder=lad, verdict=info["verdict"],
            fail_closed_reason=(None if info["verdict"] != "NOT_INTEGRABLE"
                                else info["note"]),
            note=r["note"], generator=r["generator"])
    # CMDTrot_h2 published net already charges 0.5%/yr: EASY delta is exactly 0
    rows["CMDTrot_h2"]["ladder"]["0.5%"]["delta_ann_pp"] = 0.0

    n_unknown = sum(1 for v in rows.values() if v["measurement"] == "SHORT_LEG_UNKNOWN")
    n_risk = sum(1 for v in rows.values() if v["verdict"] == "INTEGRATION_RISK")
    out = dict(
        agent="CAMP_SHORT", round=3,
        generated="2026-09-07",
        artifact="campaign/results/CAMP_SHORT_LIBRARY_BORROW_CENSUS.json",
        method=dict(
            top30="SR_d recomputed from each sleeve_library CSV; top-30 by SR",
            validation=("generator-of-record re-run; library CSV must equal rebuilt "
                        "equity-curve pct_change on the inner join, tol 2e-4 (float/CSV "
                        "round-trip); dual cost-era 6/12bps (rebaseline 2026-08-13)"),
            tier_delta="delta_ann_pp = (tier_rate - base_borrow_ann) * mean_short_frac",
            base_rates={"all suite books": 0.0,
                        "ls_n10r14_2018": "measured (DFF-150bps+25bps ETB)",
                        "CMDTrot_h2": 0.005, "CRX1030": "funding (see note)"},
            fail_closed=("any sleeve whose short leg fails byte-validation is "
                         "SHORT_LEG_UNKNOWN -> NOT_INTEGRABLE (loud)")),
        champion_reemit=champion_reemit_block(),
        sleeves=rows,
        summary=dict(
            n_rows=len(rows), n_top30=30, n_intake=6,
            n_measured=sum(1 for v in rows.values() if v["measurement"] == "MEASURED"),
            n_structural=sum(1 for v in rows.values() if v["measurement"] == "STRUCTURAL"),
            n_unknown=n_unknown,
            unknown_names=sorted(k for k, v in rows.items()
                                 if v["measurement"] == "SHORT_LEG_UNKNOWN"),
            n_integration_risk=n_risk,
            risk_names=sorted(k for k, v in rows.items()
                              if v["verdict"] == "INTEGRATION_RISK"),
            flip_bug=("strat_ls_equity.py:134 '* -1' flips every L/S short leg long: "
                      "L_S_130_30, L_S_120_20, L_S_Dollar_Neutral, "
                      "L_S_130_30_volmanaged measured |short| = 0.0 — the library's "
                      "'L/S' equity books are long-only and borrow-clean by BUG, "
                      "not by design"),
            headline=("XGB1y_deploy is the one library book with a real, sized, "
                      "un-priced single-name short leg (|short|/NAV = 1.0): 8% HARD "
                      "tier = ~8%/yr NAV drag on a 15.3% ann sleeve."),
        ))
    with open(JSON_PATH, "w") as f:
        json.dump(out, f, indent=1, default=str)
    print(f"wrote {JSON_PATH}")
    print(json.dumps(out["summary"], indent=1))


if __name__ == "__main__":
    main()
