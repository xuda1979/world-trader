"""RECON 7: dual-gate refinement on MOM/MKT (rv63-z AND VIX-z), hysteresis, slow+fast combo,
MKT+MOM jointly. Then the best-SR single cell gets refined with exit threshold."""
import sys; sys.path.insert(0,'.')
import lib, numpy as np, pandas as pd

champ=lib.load_champion()
def build(pos,r):
    net,_=lib.net_of(pos,r)
    rv=net.expanding(60).std()*np.sqrt(252)
    net=net*((0.10/rv).clip(upper=3.0).shift(1).fillna(1.0))
    return net[net.index>=pd.Timestamp('2008-01-01')].dropna()
def stats(tag,net,quiet=False):
    st=lib.full_stats(net); h1,h2=lib.halves_sr(net)
    okn,ny=lib.negyr_tol(net); corr,_=lib.corr_to(net,champ); fg=lib.flatten_gates(net)
    if not quiet:
        print(f"{tag}: SR {st['sr']:.2f} ann {st['ann_geo']:.1%} MDD {st['mdd']:.1%} negy {st['negy']} worst {st['worst']:+.1%} "
              f"H1 {h1:.2f} H2 {h2:.2f} corr {corr:+.3f} ac1 {fg['ac1']:.2f} uniqR {fg['uniqR']:.2f}")
    return st['sr']

ff=lib.load_ff3(); mom=lib.load_mom(); vix=lib.load_vix()

def rz(s, win=63):
    rv=s.rolling(win,min_periods=40).std()
    return (rv-rv.expanding(252).mean())/rv.expanding(252).std()

# dual gate: in when BOTH rv-z<th1 AND vix-z<th2 (each own ma)
MOM=mom['MOM'][mom['MOM'].index>='2005-01-01']
MKT=ff['Mkt-RF'][ff['Mkt-RF'].index>='2005-01-01']
V=vix.reindex(MOM.index).ffill()
zv=(V-V.rolling(252).mean())/V.rolling(252).std()
rows=[]
for th_r in (0.0,0.25,0.5):
    for ma_v in (126,252):
        for th_v in (0.0,0.5):
            zg=(rz(MOM)<th_r)&(zv.shift(1)<th_v)
            pos=pd.Series(np.where(zg,1.0,0.0),index=MOM.index)
            rows.append((f'MOM dual th_r{th_r} ma{ma_v} th_v{th_v}',build(pos,MOM)))
for th_r in (0.25,0.5,0.75):
    for ma_v in (126,252):
        for th_v in (0.0,0.5):
            zg=(rz(MKT)<th_r)&(zv.shift(1)<th_v)
            pos=pd.Series(np.where(zg,1.0,0.0),index=MKT.index)
            rows.append((f'MKT dual th_r{th_r} ma{ma_v} th_v{th_v}',build(pos,MKT)))
# hysteresis on MOM rv-gate alone: enter z<th0, exit z>th1
for th0,th1 in ((-0.5,0.5),(0.0,0.5),(0.0,1.0),(-0.5,1.0),(0.0,0.75)):
    zr=rz(MOM).shift(1)
    pos=np.zeros(len(MOM)); in_=False
    zr_v=zr.values
    for i,x in enumerate(zr_v):
        if np.isnan(x): pos[i]=0; continue
        if not in_ and x<th0: in_=True
        elif in_ and x>th1: in_=False
        pos[i]=1.0 if in_ else 0.0
    rows.append((f'MOM hyst {th0}/{th1}',build(pd.Series(pos,index=MOM.index),MOM)))
sc=sorted(rows,key=lambda kv:-stats(kv[0],kv[1],quiet=True))
for k,v_ in sc[:10]: stats(k,v_)
