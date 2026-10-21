import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/B2_highfreq')
# gates.vol_target: rolling(60).std() NO shift (confirmed line 12-15: rcum=expanding, scale=r/rcum applied same row)
# Confirm: does scale at row t use return at row t? Yes: rcum=expanding includes t. So sleeves saved via gates.vol_target
# (brwt, C5ng family) include same-day return in their own vol scaler = small same-day effect (leverage slightly
# correlated with same-day return). Quantified: brwt15 SR 3.253 (no shift) vs 3.165 (shift) => +0.088 SR inflation.
# a6r7/QAxasts/A5r2/carryv2/dualmom use shift(1) vt - verified in code above.
# C5ng/C5ngsum:
D='/Users/daxu/software/world-trader/tools/quant/data/newdata/DHHNGSP.csv'
s=pd.read_csv(D,index_col=0,parse_dates=True).iloc[:,0]
s=pd.to_numeric(s,errors='coerce'); s=s[s>0].dropna().sort_index()
lr=np.log(s).diff(); idx=s.index
pos=pd.Series(0.0,index=idx)
pos[idx.dayofweek==2]=-1.0; pos[idx.dayofweek==3]=-1.0; pos[idx.dayofweek==4]=1.0
thr=lr.rolling(90).std().shift(1)*2.5
p=pos.mask(lr.abs()>thr,0.0)
gr=p*lr.shift(-1); turn=p.diff().abs().fillna(p.abs())
net=(gr-turn*6e-4).dropna()
def vt_shift(r, shift=True):
    v=r.expanding(60).std()
    if shift: v=v.shift(1)
    lev=(0.10/(v*np.sqrt(252))).clip(0,3)
    return (r*lev).dropna()
a=vt_shift(net,False); b=vt_shift(net,True)
print(f"C5ng vt NO-shift SR={a.mean()/a.std()*np.sqrt(252):.3f} vs WITH shift SR={b.mean()/b.std()*np.sqrt(252):.3f}")
