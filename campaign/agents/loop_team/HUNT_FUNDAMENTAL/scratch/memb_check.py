"""Membership in/audit: does dynamic membership (delist-aware) fix fundamentals factors?
Build entry/exit dates from price availability itself, run value Q-LS with survivorship-honest masks."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
from hf_engine import *
from run_ideas2_lib import (px, rets, F, sigv, sigp, rebalance_q, rebalance_m, mom, report, COST_BPS)
import numpy as np, pandas as pd

# idea: long cheap names that are ALREADY in the panel at t (all are, trivially), but
# measure whether the LOSS comes from the short side (appreciation of survivors).
net, w, turn = rebalance_q(sigv, "ls", 1/3, 1/3, 2.0)
long_r = (w.clip(lower=0) * rets.fillna(0)).sum(axis=1) / w.clip(lower=0).sum(axis=1).replace(0, np.nan)
short_r = (w.clip(upper=0) * rets.fillna(0)).sum(axis=1) / (-w.clip(upper=0)).sum(axis=1).replace(0, np.nan)
long_r = long_r.resample('YE').sum()*100
short_r = short_r.resample('YE').sum()*100
cmp = pd.DataFrame({"long_leg": long_r, "short_leg": short_r}).dropna()
print("value Q-LS leg attribution (ann % by year):")
print(cmp.round(1).to_string())
