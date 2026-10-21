"""CANDIDATE 3: VT-convention robustness. For A+D and A+B, deliver the sleeve the campaign way:
UN-SCALED raw net (T+1, 6bps, borrow) delivered file; VT applied at POOL level in blend builders.
Report: raw single SRs, raw blend, and champion-pool-convention (60d trailing std incl zeros,
tgt .08, cap 8) scaled version. Compare MDD. Also test cap sensitivity (cap 3 / 5 / 8 / none)."""
import sys; sys.path.insert(0,'.')
import lib, numpy as np, pandas as pd

champ=lib.load_champion()
ff=lib.load_ff3(); mom=lib.load_mom(); vix=lib.load_vix()
def rz(s, win=63):
    rv=s.rolling(win,min_periods=40).std()
    return (rv-rv.expanding(252).mean())/rv.expanding(252).std()
MOM=mom['MOM'][mom['MOM'].index>='2005-01-01']
MKT=ff['Mkt-RF'][ff['Mkt-RF'].index>='2005-01-01']
V=vix.reindex(MKT.index).ffill()
zv=(V-V.rolling(252).mean())/V.rolling(252).std()

def raw_net(pos,r):
    p=pos.shift(1).reindex(r.index)
    net=p*r-(p.diff().abs()/2.0).fillna(0.0)*lib.COST-lib.BORROW*p.clip(upper=0.0).abs()
    return net.dropna()

posA=pd.Series(np.where(rz(MOM).shift(1)<0,1.0,0.0),index=MOM.index)
posD=pd.Series(np.where((rz(MKT)<0.5)&(zv.shift(1)<0.0),1.0,0.0),index=MKT.index)
posB=pd.Series(np.where(rz(MKT).shift(1)<0.5,1.0,0.0),index=MKT.index)
A=raw_net(posA,MOM); B=raw_net(posB,MKT); D=raw_net(posD,MKT)
print('RAW singles:',{k:round(s.mean()/s.std()*np.sqrt(252),3) for k,s in [('A',A),('B',B),('D',D)]})
print('RAW A+D:',round((A+D).mean()/(A+D).std()*np.sqrt(252),3),
      'RAW A+B:',round((A+B).mean()/(A+B).std()*np.sqrt(252),3))

def poolvt(r, tgt=0.08, cap=8.0):
    sd=r.rolling(60,min_periods=60).std()*np.sqrt(252)
    sc=(tgt/sd).clip(upper=cap).shift(1).fillna(1.0)
    return r*sc

for tag,bl in [('A+D',A+D),('A+B',A+B)]:
    bl=bl[bl.index>=pd.Timestamp('2008-01-01')]
    st=lib.full_stats(bl)
    print(f"\nRAW {tag} 2008+: SR {st['sr']:.3f} ann {st['ann_geo']:.1%} MDD {st['mdd']:.1%} negy {st['negy']} worst {st['worst']:+.1%} vol {bl.std()*np.sqrt(252)*100:.1f}%")
    for cap in (3.0,5.0,8.0):
        sv=poolvt(bl,cap=cap)
        st=lib.full_stats(sv)
        print(f"  pool-vt tgt.08 cap{cap:.0f}: SR {st['sr']:.3f} ann {st['ann_geo']:.1%} MDD {st['mdd']:.1%} negy {st['negy']} worst {st['worst']:+.1%} vol {sv.std()*np.sqrt(252)*100:.1f}%")
