"""honest_gate.py — automatic 'PASS means honest' CI gate (item 3).

One command that runs the full honesty battery on a claimed champion triple BEFORE it can be
quoted: builder byte-repro + full-|dW| cost reconciliation + T+1 causality + flatten sweep
(ac1<0.5, uniqR>=0.08, distinct-value floor) + zero-runs + gross-leverage cap. Mirrors the
verified verify_champion_r3_cmd.sh map, then adds the flatten diagnostics on the sleeve inputs.
Returns non-zero (fail-closed) if ANY check fails, so a CI hook can block a bad "record".
"""
import os
import subprocess
import sys

import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
CMD = f"{ROOT}/campaign/bt/verify_champion_r3_cmd.sh"

# 13-sleeve map (mirrors verify_champion_r3_cmd.sh; keep in sync with rawew13v2_build.py PATHS)
SLEEVES = {
    "A5r2": "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
    "C5ng": "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
    "C5ngsum": "campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
    "CFX4": "campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
    "QAxasts": "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
    "a6r7": "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
    "brwt10": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv",
    "brwt15": "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
    "brwt5": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv",
    "brwt7": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv",
    "carryv2": "campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
    "diescrack": "campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
    "dualmom": "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
}


def _flatten_flags():
    """ac1/uniq/distinct per sleeve input (XGB1y-class artifact detection)."""
    out = {}
    for name, rel in SLEEVES.items():
        df = pd.read_csv(f"{ROOT}/{rel}")
        col = "ret" if "ret" in df.columns else df.columns[1]
        r = df[col].dropna().astype(float)
        ac1 = r.autocorr(1) if len(r) > 2 else 0.0
        uniq = r.nunique() / len(r) if len(r) else 0.0
        out[name] = {"ac1": round(float(ac1), 4), "uniqR": round(float(uniq), 4),
                     "ok": bool(ac1 < 0.5 and uniq >= 0.08)}
    return out


def honest_verify():
    """Run verify gauntlet + flatten sweep. Returns (all_ok, report)."""
    rep = {"verify_r3": False, "errors": "", "flatten": _flatten_flags()}
    if not os.path.isfile(CMD):
        rep["errors"] = f"missing {CMD} (fail-closed)"
        return False, rep
    res = subprocess.run(["bash", CMD], capture_output=True, text=True)
    rep["verify_r3"] = res.returncode == 0
    rep["errors"] = res.stderr[-1500:]
    flat_ok = all(v["ok"] for v in rep["flatten"].values())
    rep["flat_ok"] = flat_ok
    return bool(rep["verify_r3"] and flat_ok), rep


if __name__ == "__main__":
    ok, rep = honest_verify()
    print("VERIFY_R3:", "PASS" if rep["verify_r3"] else "FAIL", "| FLATTEN-SWEEP:", "PASS" if rep["flat_ok"] else "FAIL")
    bad = [n for n, v in rep["flatten"].items() if not v["ok"]]
    if bad:
        print("flatten offenders:", {n: rep["flatten"][n] for n in bad})
    sys.exit(0 if ok else 1)
