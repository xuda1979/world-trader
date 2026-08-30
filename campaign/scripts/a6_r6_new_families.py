"""A6 r6 new-family directive — ALL 4 IDEAS FAIL gate a; nothing saved.
Reproduces the headline numbers of FINDINGS.md r6 (subset of the full sweeps).
Charter gates r6: SR>=0.7, halves>=0.35, <=3 negYr, worst>-8%, scramble<0.05, plateau, corr<0.35.
Run: python3 campaign/scripts/a6_r6_new_families.py
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
from r6_lib import gate_report
import r6_idea1_pairs as I1
import r6_idea2_lelag as I2
import r6_idea3_52whigh as I3
import r6_idea4_drift as I4

print("== IDEA 1: pair-trading lite (top-40 hi-corr pairs, z2 enter / 0 exit, VT10) ==")
for ze, zx in [(2.0, 0.0), (2.5, 0.0), (1.5, 0.5)]:
    r, _ = I1.run(topn=40, zentry=ze, zexit=zx, zwin=252)
    gate_report(r.dropna(), f"PAIRS z{ze}/exit{zx}")
r, _ = I1.run(topn=40, zwin=126); gate_report(r.dropna(), "PAIRS zwin126")

print("== IDEA 2: lead-lag mega->small ==")
for mode in ["longwin", "both"]:
    for h in [1, 5]:
        r, _ = I2.run(mode=mode, hold=h)
        gate_report(r, f"LEADLAG {mode} h{h}")

print("== IDEA 3: 52w-high momentum ==")
for wm in ["ew", "ivw"]:
    r, _ = I3.run(cad=21, wmode=wm)
    gate_report(r, f"52WH cad21 {wm}")

print("== IDEA 4: earnings-drift proxy (rev-growth x new 52w-high, PIT+6mo) ==")
for thr in [0.10, 0.20]:
    r, _ = I4.run(thr=thr)
    gate_report(r, f"DRIFT g>{int(thr*100)}% CR>0.95")
r, _ = I4.run(thr=0.10, use_fund=False)
gate_report(r, "CTRL CR-only (no fund)")
