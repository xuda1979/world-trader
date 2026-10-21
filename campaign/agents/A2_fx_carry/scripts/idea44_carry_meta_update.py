import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from r7_lib import *
import numpy as pd, pandas as pd, numpy as np
R=load_pair_rets(); yd=load_ydiff(); acc=yd/100/252; Rf=R.fillna(0)
pos=carry_ls_pos(yd,top=1,bot=1,rule="W")
net,to=backtest(pos,Rf); net=net+(pos*acc).sum(axis=1,min_count=1)
# trim to live window: signal data (foreign yields) starts 2018 -> strategy did not exist before
net=net.loc["2018-02-01":]
nv=U.vol_target(net,0.10)
r=nv.dropna(); sr=r.mean()/r.std()*np.sqrt(252)
h1,h2=U.halves_ok(r)
yr=U.yearly(nv); neg=yr[yr<0]
real,p=scramble_df(pos,Rf,n=1000,seed=7)
s,mx=corr_to_library(nv)
ch=pd.read_csv("/Users/daxu/software/world-trader/campaign/results/CHAMPION_FINAL_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
j=pd.concat([nv.rename("a"),ch.rename("b")],axis=1).dropna(); cch=j["a"].corr(j["b"])
sub1=nv.loc[:"2021-12-31"].dropna(); sub2=nv.loc["2022-01-01":].dropna()
s1=sub1.mean()/sub1.std()*np.sqrt(252); s2=sub2.mean()/sub2.std()*np.sqrt(252)
meta=(f"A2 r7 idea36: FX carry L/S weekly top1/bot1 by (foreign10y - US2y) pct rank; pairs JPY,EUR,GBP,CAD "
      f"2018-02..2026-08 (foreign yields monthly FRED, lag 1mo PIT; US rate daily data_fred_new/DGS2). "
      f"Accrual ydiff/100/252 added daily (true carry); T+1, 6bps/side, vt10 trailing expanding min60 lag1. "
      f"Rationale: uncovered-interest-parity violation - high-yield vs low-yield currency appreciates on average; "
      f"accrual is the actual carry (spot-only SR 0.25). Book = short JPY (SR .74) + long GBP (.45), EUR .30, CAD -.16. "
      f"GATES: full SR {sr:.2f}>=0.6; plateau: W/M/Q rebal 0.61-0.88, top/bot 1/2 variants 0.56-0.88, 5 US-rate proxies all 0.85; "
      f"halves H1 {h1:.2f}/H2 {h2:.2f}; negyr {len(neg)} worst {neg.min()*100:.1f}%; scramble(n=1000,seed7,pre-vt) p={p:.4f}; "
      f"subperiod SR 18-21 {s1:.2f} / 22-26 {s2:.2f}; corr champion {cch:.2f}, max|corr| library {mx:.2f}. "
      f"CAVEATS (disclosed): (1) charter r7 mission bar SR>=1.0 NOT met (0.85) - saved as campaign-brief passer (all brief gates pass); "
      f"(2) window 8.5y only - foreign yields on disk start 2018; NO 2008 carry-crash test (book shorts JPY, 2008-style unwind would hurt); "
      f"(3) scramble marginal: 500x3 seeds p=0.030-0.054; (4) costs trivial ({to:.5f}/d turnover = {to*6:.3f}bp/d) - result is not cost-tested. "
      f"Coordinator: treat as conditional diversifier pending longer-window foreign-rate data (OECD/BIS daily or 2000s monthly policy rates).")
save_sleeve(nv.rename("ret"), "sleeves/A2_fx_carry_W11_accrual.csv", meta)
print(f"saved live-window: SR {sr:.2f} H1 {h1:.2f} H2 {h2:.2f} negyr {len(neg)} worst {neg.min()*100:.1f}% p {p:.4f} cch {cch:.3f} mx {mx:.2f} n={len(r)}")
