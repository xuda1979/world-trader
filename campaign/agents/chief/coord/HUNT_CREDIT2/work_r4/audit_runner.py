#!/usr/bin/env python3
"""HUNT_CREDIT2 ROUND 4 audit rotation — one-shot re-runner for all audited rows.
Each entry = (DEAD_IDEAS row, cited script). Run to reproduce the numbers in FINDINGS.md R4."""
import subprocess, sys

RUNS = [
    ("special duty: R2 gate2 generic-control (vol-mask >= credit gate)",
     "/Users/daxu/software/world-trader/campaign/scripts/HUNT_CREDIT2_round2_gate2.py", None),
    ("row 110 FF factor premia (byte-repro sha 1adcb4b7fbbdc079 / 55a9b3e5661bd871)",
     "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_CREDIT2/work_r4/audit_ff2/final1_auditcopy.py",
     "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FF2/scratch"),
    ("row 111 industry/decile L/S (fund_screen_all + run_ideas + ic_check3 + s_ta_backtest)", None, None),  # 4 scripts, see FINDINGS
    ("row 113 BAB (recon3 + recon5)",
     None, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FF2/scratch"),  # recon3.py, recon5.py
    ("row 114 FOMC x natgas/gold (d4_i1, d4_i1b, d4_i1c)",
     "/Users/daxu/software/world-trader/campaign/scripts/d4_i1.py", None),
    ("row 102 CMDT2-R3 commodity spread momentum + TDD 7/7",
     "/Users/daxu/software/world-trader/campaign/scripts/HUNT_CMDT2_round3.py", None),
    ("row 59 TREASFUT 2s10s steepener",
     "/Users/daxu/software/world-trader/campaign/scripts/HUNT_TREASFUT_round1.py", None),
]

def main():
    for label, script, cwd in RUNS:
        print("=" * 78)
        print("::", label)
        if script:
            r = subprocess.run([sys.executable, script], cwd=cwd or "/Users/daxu/software/world-trader")
            if r.returncode != 0:
                print(f"  !! exit {r.returncode}")
        else:
            print("  (multi-script row; run each listed script individually)")

if __name__ == "__main__":
    main()
