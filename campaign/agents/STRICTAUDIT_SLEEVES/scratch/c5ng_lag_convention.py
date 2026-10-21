import pandas as pd, numpy as np
# C5ng T+1 audit: pos(t) decided USING |lr(t)| (same-day print) earns lr.shift(-1)=log s_{t+1}/s_t.
# FRED DHHNGSP daily spot: is the t print known before you trade at close t? For FRED spot prices,
# publication is same-day (EIA daytime print) — the calm filter uses the print itself, so this is
# same-CLOSE info for a NEXT-close P&L: acceptable IF print published intraday. Publication-lag risk documented.
# Also check: lr.shift(-1) at pos row t = return from close t to close t+1. Correct T+1. Verify no same-day PnL:
D='/Users/daxu/software/world-trader/tools/quant/data/newdata/DHHNGSP.csv'
s=pd.read_csv(D,index_col=0,parse_dates=True).iloc[:,0]
s=pd.to_numeric(s,errors='coerce'); s=s[s>0].dropna().sort_index()
lr=np.log(s).diff(); idx=s.index
pos=pd.Series(0.0,index=idx)
pos[idx.dayofweek==2]=-1.0; pos[idx.dayofweek==3]=-1.0; pos[idx.dayofweek==4]=1.0
# weekday structure sanity: count pos days
print("pos counts:", pos.value_counts().to_dict())
# does pos ever depend on future? mask uses lr (t), thr uses shift(1). => info <= t. OK.
