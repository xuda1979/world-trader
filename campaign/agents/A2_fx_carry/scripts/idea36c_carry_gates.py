"""Charter 1 candidate: carry W top1/bot1 + accrual (2018+). Full gate battery + save if pass."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from r7_lib import *
import numpy as np, pandas as pd

R = load_pair_rets(); yd = load_ydiff(); acc = yd/100.0/252.0
Rf = R.fillna(0)
pos = carry_ls_pos(yd, top=1, bot=1, rule="W")
net, to = backtest(pos, Rf)
net = net + (pos*acc).sum(axis=1, min_count=1)
nv = U.vol_target(net, 0.10)

print("avg daily turnover:", round(to,4))
h1,h2 = U.halves_ok(nv.dropna()); print(f"halves H1={h1:.2f} H2={h2:.2f}")
real, p = scramble_df(pos, Rf, n=200); print(f"scramble (pre-vt): real={real:.2f} p={p:.3f}")
s, mx = corr_to_library(nv); print(f"corr to library: max|{mx:.2f}| mean|{s.abs().mean():.2f}|")
print(s.reindex(s.abs().sort_values().index[-5:]).round(2).to_string())

# how much of return is accrual vs spot?
spot_only,_ = backtest(pos, Rf)
print("spot-only SR:", round(U.vol_target(spot_only,0.10).dropna().mean()/U.vol_target(spot_only,0.10).dropna().std()*np.sqrt(252),2))
g = U.gates(nv); print("gates:", g)
import json
if g["pass_"] and p<0.05 and mx<0.3:
    meta = (f"A2 r7 idea36: FX carry L/S weekly, top1/bot1 by (foreign10y - US2y) pct, monthly foreign yields lag1m + daily US2y (FRED data_fred_new/old), "
            f"+ daily interest accrual ydiff/100/252; pairs JPY,EUR,GBP,CAD 2018-02..2026-08; T+1, 6bps/side, vt10 trailing. "
            f"Rationale: high-yield currency (positive rate diff) appreciates on average vs low-yield (uncovered interest parity violation); "
            f"accrual is the true carry. Gates: SR {g['sr']:.2f}, H1 {h1:.2f}/H2 {h2:.2f}, negyr {g['neg_years']} worst {g['worst']*100:.1f}%, "
            f"scramble p={p:.3f}, maxcorr {mx:.2f}. Window caveat: foreign yields only on disk 2018+ -> 8.5y live window, no 2008 carry-crash test.")
    save_sleeve(nv.rename("ret"), "sleeves/A2_fx_carry_W11_accrual.csv", meta)
    print("SAVED A2_fx_carry_W11_accrual.csv")
else:
    print("NOT SAVED")
