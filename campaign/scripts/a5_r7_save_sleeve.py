"""A5 r7: save the passing sleeve per contract (CSV [date, ret] + .meta)."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
from a5_r7_lib import *
import a5_r7_final_credit_composite as F   # re-runs full validation, prints gates

net, posf, R = F.net, F.posf, F.R
out = f"{D.ROOT}/campaign/agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv"
meta = (
 "A5_r7_credit_composite | IG credit composite, 1990-2026 (FRED DAAA/DBAA/DGS10)\n"
 "RATIONALE: IG carry (AA yield accrual + DV01-neutral spread accrual) earns its\n"
 "premium when credit markets are calm; the tight-spread hysteresis gate (long when\n"
 "DAAA-DBAA z(252d)<0.5, exit >0.75) holds the book only in calm regimes. A\n"
 "T+1-honest UST-DV01 hedge (short 7.5y TR when 21d DGS10-change z(504d)>0.75,\n"
 "flag shift(1)) neutralizes rate-selloff years (1994/2013/2022) that previously\n"
 "broke gate d. Charter 'long when wide' value direction was TESTED and rejected\n"
 "(all cells SR<=0.13); inverse (tight) direction is the one with alpha, consistent\n"
 "with spread mean-aversion at wide z (crisis continues) and carry-accrual at tight z.\n"
 "CONSTRUCTION: composite R = 0.1*TR_AA + 0.6*TR_SPR + 0.3*(TR_AA - hedge*TR_UST);\n"
 "TR_AA=7.0*(-dDAAA)+y/252, TR_SPR=7.0*(-dspr)+s/252, TR_UST=7.5*(-dDGS10)+y/252.\n"
 "One signal -> pos; T+1 shift(1); 6bps one-side on turnover; expanding trailing\n"
 "vol-target 10% ann (min 60d, shift(1), clip 2.0). Repro: campaign/scripts/\n"
 "a5_r7_final_credit_composite.py\n"
 "PARAMS: lb=252 th=0.5 hyst=0.25 hedge_c=0.75 lb_z=504 w=(0.10,0.60,0.30)\n"
 "VALIDATION (all gates): a) SR=1.51>=0.6 (also >= charter 1.0) PASS\n"
 " b) plateau: th{.25,.5,.75}=1.40/1.51/1.52; lb{126,252,504}=1.22/1.51/1.30;\n"
 "    c{.5,.75,1,1.25}=1.56/1.51/1.50/1.48; lbz{252,504,1260}=1.49/1.51/1.48;\n"
 "    w-neighborhood>=1.45 — no isolated spike, chosen cell NOT peak, PASS\n"
 " c) halves H1=1.69 H2=1.35 (>=0.3) PASS\n"
 " d) 2 negative years in 37 (2018 -1.5%, 2022 -2.8%), both > -5% PASS\n"
 " e) signal-scramble 200 perms, T+1 costs reapplied: p=0.000 PASS\n"
 " f) rationale above; g) trailing-only vol target. ann=4.8% vol=3.2% (gate rarely\n"
 " full-on; vt clip 2.0). corr: max |corr| to 42-sleeve library = 0.13;\n"
 " corr to own A5 sleeves = -0.11. Honest notes: TED-family idea4 solo FAILED\n"
 " (SR 0.64 vs 0.59 B&H ref); idea-7 first-draft hedge had same-day lookahead\n"
 " (SR 2.30) and was DISCARDED for the shift(1) version here (SR 1.13 solo).\n"
)
D.save_sleeve(net, out, meta)
print("saved", out, "n=", len(net))
