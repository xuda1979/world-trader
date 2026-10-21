import sys, numpy as np, pandas as pd
sys.path.insert(0,'.')
import engine as E
DATA=f'{E.DATA}'; champ=E.champ_ref(); OUT='/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves'
def load_ohlc(path, col='close'):
    df=pd.read_csv(path); df['date']=pd.to_datetime(df['date'])
    return df.drop_duplicates('date').set_index('date').sort_index()[col]
v9=load_ohlc(f'{DATA}/more_vol/VIX9D.csv'); v3m=load_ohlc(f'{DATA}/more_vol/VIX3M.csv'); v6m=load_ohlc(f'{DATA}/more_vol/VIX6M.csv')
curves={'vixterm_9_3': v3m-v9, 'vixterm_3_6': v6m-v3m, 'vixterm_9_6': v6m-v9}
def term_book(slope, lb, gate):
    m=slope.rolling(lb).mean(); sd=slope.rolling(lb).std().replace(0,np.nan); z=(slope-m)/sd
    pos=pd.Series(0.0,index=slope.index); pos[z<-gate]=1.0; pos[z>gate]=-1.0
    ret=slope.diff().shift(-1); gr=(pos*ret).dropna(); tup=pos.diff().abs().reindex(gr.index).fillna(0)
    return (gr-tup*6.4/1e4),pos,ret
def roll(p,r):
    g=(p*r).dropna(); t=p.diff().abs().reindex(g.index).fillna(0); n=g-t*6.4/1e4
    n,_=E.vol_target(n); return n.dropna()
def proper_p(pos,ret,nv,n=200):
    rng=np.random.default_rng(0); T=len(pos); pv=pos.values; realv=nv.mean()/nv.std()*np.sqrt(252); cnt=0
    for _ in range(n):
        lag=int(rng.integers(21,max(T-21,22))); nb=roll(pd.Series(np.roll(pv,lag),index=pos.index),ret.rename('r'))
        if len(nb) and nb.std()>0 and nb.mean()/nb.std()*np.sqrt(252)>=realv: cnt+=1
    return cnt/200
cfgs={'vixterm_9_3':[(20,1.0),(40,1.5),(60,2.0)],
      'vixterm_9_6':[(40,1.5),(60,2.0)],
      'vixterm_3_6':[(20,1.5),(60,2.0)]}
for cname,slope in curves.items():
    for lb,gate in cfgs.get(cname,[]):
        net,pos,ret=term_book(slope,lb,gate)
        nv,_=E.vol_target(net.dropna())
        st=E.evaluate(nv,champ,cname)
        p=proper_p(pos,ret,nv)
        fn=f"{OUT}/calendar_{cname}_L{lb}Z{gate}.csv"
        E.save_sleeve(nv,fn)
        ok = st['SR_pass'] and st['H_pass'] and st['negyr_pass'] and p<0.05 and st['corr_pass'] and st['flatten_pass']
        print(f"SAVED {fn} SR={st['SR']:.3f} ann={st['ann_geo']*100:.1f}% MDD={st['MDD']*100:.1f}% negy={st['negyr']} corr={st['corr_champ']:+.3f} scram={p:.3f} PASS={'Y' if ok else 'n'}")
