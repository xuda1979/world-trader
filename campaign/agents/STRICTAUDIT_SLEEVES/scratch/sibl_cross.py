import pandas as pd, numpy as np
# Cross-check my reconstruction against the CONSTRUCTION agent's BAL_exact (they recovered a session-log builder)
bal = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/STRICTAUDIT_CONSTRUCTION/scratch/BAL_exact.csv',index_col=0,parse_dates=True).iloc[:,0]
ch = pd.read_csv('../../../results/GOAL100_STRICTTRADE_BALANCED_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
j = pd.concat([bal.rename('sibl'), ch.rename('comm')],axis=1,join='inner').dropna()
print(f"construction-agent BAL vs committed: n={len(j)} corr={j.corr().iloc[0,1]:.4f} max|d|={(j['sibl']-j['comm']).abs().max():.4f} mean|d|={(j['sibl']-j['comm']).abs().mean():.5f}")
print(f"sibl ann={j['sibl'].mean()*252*100:.1f}% SR={j['sibl'].mean()/j['sibl'].std()*np.sqrt(252):.2f}")
