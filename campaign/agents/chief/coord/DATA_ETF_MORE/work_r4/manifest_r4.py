#!/usr/bin/env python3
"""Rebuild more_etf/manifest.csv after the R4 rotation (5 new PASS_WAIVER
files: EIS TUR EPHE COPX ENOR). Reuses the R3 builder + gates unchanged so
span_class/status semantics stay identical; the only delta is the 5 new rows.
Runs from any cwd (absolute sys.path to work_r3)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R3 = "/Users/daxu/software/world-trader/campaign/agents/chief/coord/DATA_ETF_MORE/work_r3"
sys.path.insert(0, R3)

from manifest_r3 import build

if __name__ == "__main__":
    mf = build()  # lints every csv fail-closed under the waiver, writes manifest
    bad = mf[mf["status"].astype(str).str.startswith("FAIL")]
    print(f"manifest rebuilt: {len(mf)} rows, {len(bad)} loud FAILs")
    if len(bad):
        print(bad[["symbol", "start", "status"]].to_string(index=False))
