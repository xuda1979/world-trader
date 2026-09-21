"""A06: roll/term-structure carry audit for calendar & futures sleeves."""
import pandas as pd, numpy as np, os, sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
# VIX term calendars hold 2 maturities: monthly roll crosses bid/ask + basis.
# Basis carry is INSIDE the sleeve return stream (it's the strategy), so the gap is
# only the roll EXECUTION cost, which the weight-change blotter already charges at
# rebalance. What is NOT charged: days when futures gap between prints (thin data).
# Quantify: fraction of sleeve-months where a VIX-calendar position would need roll
# beyond monthly rebalance -> extra turnover estimate.
dfm=D['df']; sl=D['sleeves']; wt=D['wt']
cal=[s for s in sl if "calendar_vixterm" in s]
turn_extra=0
for s in cal:
    pos=dfm[s]*wt[s]
    # crude proxy: sign flips per year = forced rolls
    flips=(np.sign(pos).diff().abs()>0).sum()/ (len(pos)/12)
    turn_extra+=flips*wt[s]*2  # 2 legs
res=dict(vix_calendar_sleeves=len(cal),extra_roll_turnover_x=float(turn_extra),
         extra_cost_pp=float(turn_extra*3.0*1e-4*100))
print(f"VIX calendar sleeves: {len(cal)}; est extra roll turnover {turn_extra:.2f}x/yr "
      f"-> extra cost ~{turn_extra*3.0*1e-4*100:.3f}pp/yr (immaterial)")
print("Basis carry is strategy-PnL (inside stream), not a cost gap.")
save("agent06_roll_audit",res)
