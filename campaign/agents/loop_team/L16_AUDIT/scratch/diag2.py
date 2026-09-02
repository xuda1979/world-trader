import sys; sys.path.insert(0,'campaign/scripts')
import numpy as np, pandas as pd
from champion_build import load, vt
from pandas.tseries.holiday import USFederalHolidayCalendar
ROOT="/Users/daxu/software/world-trader"
exec(open('campaign/agents/loop_team/L16_AUDIT/scratch/audit_b_build.py').read().split("A,ma=build")[0])

old=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv",index_col=0,parse_dates=True).iloc[:,0]

# hypothesis: A and B each correct but BAL built as (A+B)/2 reindexed on A only, or dropna differently
A,ma=build(0.07,0.04); B,mb=build(0.091,0.03)
for name,cand in [("A",A),("B",B),("avgA",0.5*A+0.5*B)]:
    j=pd.concat([old.rename('o'),cand.rename('n')],axis=1,join='inner').dropna()
    print(name,len(j),f"max|d|={float((j.o-j.n).abs().max()):.3e}  corr={j.o.corr(j.n):.6f}")
BAL=((A+B)/2).dropna()
j=pd.concat([old.rename('o'),BAL.rename('n')],axis=1,join='inner').dropna()
# is the diff proportional to a constant factor on r? test scale k minimizes |o - k*n|
n=j.n.values; o=j.o.values
k=(n@o)/(n@n)
resid=o-k*n
print("best constant scale k:",k,"resid max:",abs(resid).max())
# is diff correlated with |n| or turnover-like?
d=o-n
print("corr(d, n):",np.corrcoef(d,n)[0,1], " corr(d,|n|):",np.corrcoef(d,abs(n))[0,1])
# regression o = a + b*n
X=np.vstack([np.ones(len(n)),n]).T
beta,res_,rank,sv=np.linalg.lstsq(X,o,rcond=None)
r_=o-X@beta
print("lstsq a,b:",beta,"resid max:",abs(r_).max(),"resid std:",r_.std())
