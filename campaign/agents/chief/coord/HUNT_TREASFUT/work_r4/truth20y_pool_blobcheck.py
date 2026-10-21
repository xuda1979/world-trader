#!/usr/bin/env python3
"""R4 bounded TRUTH20Y re-check: are any of the 14 TRUTH20Y-pool files on disk
different from their git c745682 blobs BEYOND the known costfix trio?
If none differ, the worktree/git-blob technique that EXACTLY reproduced V2
cannot help TRUTH20Y (R3 variant-2 already tested those blobs -> 1.58e-2),
and the R3 quarantine stands with its evidence base strengthened."""
import subprocess, sys
import pandas as pd

GITROOT = subprocess.run(["git","rev-parse","--show-toplevel"],capture_output=True,text=True).stdout.strip()
# TRUTH20Y.json pool (14) -> on-disk candidates (E1 de-truncated = E-suffix files)
POOL = {
 "A5r7":    "campaign/agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv",
 "A5r2":    "campaign/agents/A5_vol_cond/sleeves/A5_r2_credit_regime.csv",
 "a6r7E":   "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "QAxastsE":"campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 "dualmom": "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
 "carryv2E":"campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "XGB1y":   "campaign/results/sleeve_library/XGB1y_deploy.csv",
 "A1credit":"campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv",
 "C5ngE":   "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsumE":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 "brwt15E": "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 "brwt10":  "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv",
 "brwt7":   "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv",
 "brwt5":   "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv",
}
TRIO = {"QAxastsE","dualmom","brwt15E"}
ndiff = 0
for key, rel in POOL.items():
    p = subprocess.run(["git","show",f"c745682:software/world-trader/{rel}"],
                       cwd=GITROOT, capture_output=True)
    if p.returncode != 0:
        print(f"{key:10s} NOT-IN-c745682  ({rel})"); continue
    disk = open(rel,'rb').read()
    same = (disk == p.stdout)
    tag = "SAME" if same else "DIFF"
    if not same:
        ndiff += 1
        note = "(costfix trio - already tested R3)" if key in TRIO else "<== OUTSIDE TRIO"
    else:
        note = ""
    print(f"{key:10s} {tag}  {note}")
print(f"\nfiles differing from c745682: {ndiff}; outside-costfix-trio differences: "
      f"{ndiff - sum(1 for k in TRIO if k in POOL)} expected==0 for 'blobs lost' story to be void")
