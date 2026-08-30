"""A6 r4 (all three charter ideas — documented near-misses, NOTHING passed all gates).
Reproducible: rebuilds legs, prints gate table identical to the r4 FINDINGS entry.
Idea 1: a6_r2_pair_residmom_fm1926 re-budgeted vt15  -> SR 0.92 ann 14.5% but corrM +0.58 FAIL
Idea 2: rm+FactorMom_1926+QA_dualmom triple vt15     -> SR 0.90 ann 13.0% but corrM +0.60 FAIL
Idea 3: rm meta-timed by own trailing 12m SR @vt15   -> SR 0.81-0.89 but 2022 -10% (gate d) + corr FAIL
Also reproduces the two scramble-null variants on the near-misses (see FINDINGS r4, item 4).
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from r4_lib import rm_leg, load_series, vt, full_gates
FMP = "/Users/daxu/software/world-trader/campaign/results/sleeve_library/FactorMom_1926.csv"
QAP = "/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv"
raw, Wg = rm_leg()
l1 = vt(raw, 0.15); l2 = vt(load_series(FMP), 0.15); l3 = vt(load_series(QAP), 0.15)
full_gates(vt(0.5*l1+0.5*l2, 0.15), "IDEA1 pair 0.5/0.5 @vt15")
full_gates(vt((l1+l2+l3)/3, 0.15), "IDEA2 triple 1/3 @vt15")
sr12 = (raw.rolling(252, min_periods=126).mean()/raw.rolling(252, min_periods=126).std()*np.sqrt(252)).shift(1)
mult = pd.Series(np.where(sr12 > 0.5, 1.0, 0.25), index=raw.index).fillna(0.25)
full_gates(vt(l1*mult, 0.15), "IDEA3 rm-meta thr=0.5 shrink=0.25 @vt15")
full_gates(vt((vt(l1*mult,0.15)+l2+l3)/3, 0.15), "IDEA3 triple meta-rm @vt15")
