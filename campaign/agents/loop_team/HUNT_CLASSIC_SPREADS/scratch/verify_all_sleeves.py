"""Final consolidated gate verification of all saved sleeves.
Rebuilds each sleeve from raw data via the same engine, recomputes ALL honest gates
(SR, H1/H2, neg-yr, proper position-rotation scramble, corr to champion, ac1, uniqR).
Prints a clean summary table.
"""
import sys, numpy as np, pandas as pd, glob, os
sys.path.insert(0,'.')
import engine as E
DATA=f'{E.DATA}'; champ=E.champ_ref()

def load_ohlc(path, col='close'):
    df=pd.read_csv(path); df['date']=pd.to_datetime(df['date'])
    return df.drop_duplicates('date').set_index('date').sort_index()[col]

# ---- rebuild sources
wti=E.eia('wti_spot_daily'); gas_nyh=E.eia('gasoline_nyh_spot_daily')*42.0; ulsd_nyh=E.eia('ulsd_nyh_spot_daily')*42.0
gas_gulf=E.eia('gasoline_gulf_spot_daily')*42.0; ulsd_gulf=E.eia('ulsd_gulf_spot_daily')*42.0; jet=E.eia('jet_gulf_spot_daily')*42.0
v9=load_ohlc(f'{DATA}/more_vol/VIX9D.csv'); v3m=load_ohlc(f'{DATA}/more_vol/VIX3M.csv'); v6m=load_ohlc(f'{DATA}/more_vol/VIX6M.csv')

def proper_p(pos,ret,nv,n=150):
    rng=np.random.default_rng(0); T=len(pos); pv=pos.values; realv=nv.mean()/nv.std()*np.sqrt(252); cnt=0
    def roll(p,r):
        g=(p*r).dropna(); t=p.diff().abs().reindex(g.index).fillna(0); nn=g-t*6.4/1e4
        nn,_=E.vol_target(nn); return nn.dropna()
    for _ in range(n):
        lag=int(rng.integers(21,max(T-21,22))); nb=roll(pd.Series(np.roll(pv,lag),index=pos.index),ret.rename('r'))
        if len(nb) and nb.std()>0 and nb.mean()/nb.std()*np.sqrt(252)>=realv: cnt+=1
    return cnt/n

def zrev(margin,lb,gate):
    net,gr,pos,tup=E.zrev_margin(margin,lookback=lb,gate=gate); nv,_=E.vol_target(net)
    return nv,pos,margin
def term(sp,lb,gate):
    m=sp.rolling(lb).mean(); sd=sp.rolling(lb).std().replace(0,np.nan); z=(sp-m)/sd
    pos=pd.Series(0.0,index=sp.index); pos[z<-gate]=1.0; pos[z>gate]=-1.0
    ret=sp.diff().shift(-1); gr=(pos*ret).dropna(); tup=pos.diff().abs().reindex(gr.index).fillna(0)
    return (gr-tup*6.4/1e4),pos,ret

builders={
 'crack_crack321_nyh_L60Z1.5': ('z',E.build_crack321(wti,gas_nyh,ulsd_nyh),60,1.5),
 'crack_crack321_nyh_L15Z1.5': ('z',E.build_crack321(wti,gas_nyh,ulsd_nyh),15,1.5),
 'crack_crack321_nyh_L60Z1.0': ('z',E.build_crack321(wti,gas_nyh,ulsd_nyh),60,1.0),
 'crack_crack211_nyh_L15Z1.5': ('z',E.build_crack211(wti,gas_nyh,ulsd_nyh),15,1.5),
 'crack_crack211_nyh_L60Z1.5': ('z',E.build_crack211(wti,gas_nyh,ulsd_nyh),60,1.5),
 'crack_gas_crack_nyh_L30Z1.5': ('z',gas_nyh-wti,30,1.5),
 'crack_gas_crack_nyh_L30Z2.0': ('z',gas_nyh-wti,30,2.0),
 'crack_gas_crack_nyh_L40Z1.0': ('z',gas_nyh-wti,40,1.0),
 'inter_gasreg_nyh_gulf_L30Z1.0': ('z',np.log(gas_nyh)-np.log(gas_gulf),30,1.0),
 'inter_gasreg_nyh_gulf_L40Z1.0': ('z',np.log(gas_nyh)-np.log(gas_gulf),40,1.0),
 'inter_gasreg_nyh_gulf_L60Z1.0': ('z',np.log(gas_nyh)-np.log(gas_gulf),60,1.0),
 'inter_dieseljet_L60Z1.5': ('z',np.log(ulsd_nyh)-np.log(jet),60,1.5),
 'inter_dieseljet_L60Z1.0': ('z',np.log(ulsd_nyh)-np.log(jet),60,1.0),
 'calendar_vixterm_9_3_L20Z1.0': ('t',v3m-v9,20,1.0),
 'calendar_vixterm_9_3_L40Z1.5': ('t',v3m-v9,40,1.5),
 'calendar_vixterm_9_3_L60Z2.0': ('t',v3m-v9,60,2.0),
 'calendar_vixterm_3_6_L20Z1.5': ('t',v6m-v3m,20,1.5),
}
print(f"{'sleeve':38s} {'SR':>5s} {'ann%':>6s} {'MDD%':>7s} {'negy':>4s} {'H1':>5s} {'H2':>5s} {'scram':>6s} {'corr':>6s} {'uniq':>5s} {'PASS':>4s}")
rows=[]
for name,(kind,margin,lb,gate) in builders.items():
    if kind=='z':
        nv,pos,m=zrev(margin,lb,gate)
        ret=m.diff().shift(-1)
    else:
        net,pos,ret=term(margin,lb,gate); nv,_=E.vol_target(net.dropna())
    st=E.evaluate(nv,champ,name)
    p=proper_p(pos,ret,nv)
    ok=st['SR_pass'] and st['H_pass'] and st['negyr_pass'] and p<0.05 and st['corr_pass'] and st['flatten_pass']
    rows.append((name,st,p,ok))
    print(f"{name:38s} {st['SR']:5.2f} {st['ann_geo']*100:6.1f} {st['MDD']*100:7.1f} {st['negyr']:4d} {st['H1_H2'][0]:5.2f} {st['H1_H2'][1]:5.2f} {p:6.3f} {st['corr_champ']:6.3f} {st['uniqR']:5.2f} {'Y' if ok else 'n'}")
