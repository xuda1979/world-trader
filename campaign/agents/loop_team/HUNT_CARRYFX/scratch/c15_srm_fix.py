import pandas as pd, numpy as np
def sr12(m): m=m.dropna(); return float(m.mean()/m.std()*np.sqrt(12))
def sr_d(r): return float(r.mean()/r.std()*np.sqrt(252))
for tag,p in [("CFX4_nocarry","sleeves/CFX4_DTF21_63_raw_daily.csv"),
              ("CFX4_carry","sleeves/CFX4_DTF21_63_carry_raw_daily.csv"),
              ("FXMR3_committed","/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXMICRO/sleeves/FXMR3_42z2_daily.csv"),
              ("L16_BAL","/Users/daxu/software/world-trader/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv")]:
    r=pd.read_csv(p,index_col=0,parse_dates=True).iloc[:,0].dropna()
    m=(1+r).resample('ME').prod()-1
    print(f"{tag}: SR_d={sr_d(r):.4f}  SR_m(sqrt12)={sr12(m):.4f}  (n_months={len(m.dropna())})")
# top50 for nocarry
r=pd.read_csv("sleeves/CFX4_DTF21_63_raw_daily.csv",index_col=0,parse_dates=True)["ret"]
x=r.values; o=np.argsort(x)[::-1]; tot=x.sum()
print(f"nocarry: top5={x[o[:5]].sum()/tot*100:.1f}% top20={x[o[:20]].sum()/tot*100:.1f}% top50={x[o[:50]].sum()/tot*100:.1f}%")
