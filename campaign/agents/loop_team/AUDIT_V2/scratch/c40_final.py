#!/usr/bin/env python3
"""Final: stat-arbitrage between claimed slot-accounting and reconstruction; contribution shares
of the two new sleeves in V2; borrow+cost sums; verify SAFEs differ; numbers for FINDINGS."""
import numpy as np, pandas as pd, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
from v2lib import NEW, load
ROOT = "/Users/daxu/software/world-trader"
v2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
dies = load(NEW['diescrack']); cfx = load(NEW['CFX4'])
w_d, w_c = 0.023347, 0.024722
common = v2.index
contrib_d = (w_d*dies.reindex(common).fillna(0)).sum()
contrib_c = (w_c*cfx.reindex(common).fillna(0)).sum()
print(f"implied slot contributions (4989 common rows): dies {contrib_d*100:+.2f}% cum, CFX4 {contrib_c*100:+.2f}% cum")
# per-year contribution share of V2 total
tot08 = v2[(v2.index>='2008-03-31')].sum()
print(f"V2 BAL 2008+ total simple return: {tot08*100:.1f}%")
print(f"new-sleeve share of 2008+ sum: {(w_d*dies[(dies.index>='2008-03-31')&(dies.index<=v2.index[-1])].fillna(0).sum() + w_c*cfx[(cfx.index>='2008-03-31')].fillna(0).sum())/tot08*100:.2f}%")
# slot-share implied: ann contribution of each slot vs 11-pool
print(f"\nimplied capital share check: w_dies=0.0233 vs slot 0.10/12.2=0.0082 vs 1/22=0.0455 — NEITHER matches")
print(f"w_cfx/w_dies = {w_c/w_d:.3f} (should be 1.0 if symmetric slots)")
