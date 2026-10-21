import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
# E1 C5ng files: same as C5_weekend_prem_ng.run() but full history
D='/Users/daxu/software/world-trader/tools/quant/data/newdata/DHHNGSP.csv'
s=pd.read_csv(D,index_col=0,parse_dates=True).iloc[:,0]
s=pd.to_numeric(s,errors='coerce'); s=s[s>0].dropna().sort_index()
lr=np.log(s).diff()
idx=s.index
pos=pd.Series(0.0,index=idx)
pos[idx.dayofweek==2]=-1.0; pos[idx.dayofweek==3]=-1.0; pos[idx.dayofweek==4]=1.0
def build(summer, k=2.5):
    thr=lr.rolling(90).std().shift(1)*k
    p=pos.mask(lr.abs()>thr,0.0)
    if summer:
        p=p.where((idx.month>=4)&(idx.month<=10),0.0)
    gr=p*lr.shift(-1)
    turn=p.diff().abs().fillna(p.abs())
    net=(gr-turn*6e-4).dropna()
    sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/B2_highfreq')
    from gates import vol_target
    scaled,_=vol_target(net)
    return scaled.dropna()
f1 = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv', parse_dates=['date']).set_index('date')['ret']
f2 = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv', parse_dates=['date']).set_index('date')['ret']
r1 = build(False); r2 = build(True)
for nm, r, f in [('C5ng', r1, f1), ('C5ngsum', r2, f2)]:
    j = pd.concat([r.rename('r'), f.rename('f')], axis=1, sort=True).dropna()
    d = (j['r']-j['f']).abs()
    print(f"{nm}: n={len(j)} corr={j['r'].corr(j['f']):.8f} max|d|={d.max():.3e} exact={(d<1e-12).sum()}")
