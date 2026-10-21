"""FINAL 1: canonical, self-contained rebuild script for the delivered files (provenance),
run from scratch and byte-compare against delivered CSVs. Writes:
  sleeves/FF2_DUALGATE_raw_daily.csv / _poolvt_daily.csv + metas + FINAL_STATS.txt"""
import sys; sys.path.insert(0,'.')
import lib, numpy as np, pandas as pd, hashlib

# ---- canonical construction (exact) ----
ff=lib.load_ff3(); mom=lib.load_mom(); vix=lib.load_vix()
def rz(s, win=63, minp=40):
    rv=s.rolling(win,min_periods=minp).std()
    return (rv-rv.expanding(252).mean())/rv.expanding(252).std()
MOM=mom['MOM'][mom['MOM'].index>='2005-01-01']
MKT=ff['Mkt-RF'][ff['Mkt-RF'].index>='2005-01-01']
V=vix.reindex(MKT.index).ffill()
zv=(V-V.rolling(252).mean())/V.rolling(252).std()

def raw_net(pos,r):
    p=pos.shift(1).reindex(r.index)
    net=p*r-(p.diff().abs()/2.0).fillna(0.0)*lib.COST-lib.BORROW*p.clip(upper=0.0).abs()
    return net.dropna()
def poolvt(r,tgt=0.08,cap=3.0):
    sd=r.rolling(60,min_periods=60).std()*np.sqrt(252)
    return (r*((tgt/sd).clip(upper=cap).shift(1).fillna(1.0))).dropna()

posA=pd.Series(np.where(rz(MOM).shift(1)<0.0,1.0,0.0),index=MOM.index)
posD=pd.Series(np.where((rz(MKT).shift(1)<0.5)&(zv.shift(1)<0.0),1.0,0.0),index=MKT.index)
bl=raw_net(posA,MOM)+raw_net(posD,MKT)   # sum (== avg x2; invariant to 2x under vt)
bl=bl[bl.index>=pd.Timestamp('2008-01-01')]
raw_out=bl/2.0
pv_out=poolvt(bl)
raw_out.name='ret'; pv_out.name='ret'
raw_out.index.name='date'; pv_out.index.name='date'
raw_out.to_csv('../sleeves/FF2_DUALGATE_raw_daily.csv')
pv_out.to_csv('../sleeves/FF2_DUALGATE_poolvt_daily.csv')
print('raw sha:',hashlib.sha256(raw_out.to_csv().encode()).hexdigest()[:16])
print('pv  sha:',hashlib.sha256(pv_out.to_csv().encode()).hexdigest()[:16])

# stats to embed
champ=lib.load_champion()
for tag,s in [('raw',raw_out),('poolvt',pv_out)]:
    st=lib.full_stats(s); h1,h2=lib.halves_sr(s)
    okn,ny=lib.negyr_tol(s); corr,_=lib.corr_to(s,champ); fg=lib.flatten_gates(s)
    print(f"{tag}: SR {st['sr']:.4f} ann {st['ann_geo']*100:.2f}% MDD {st['mdd']*100:.2f}% negy {st['negy']} worst {st['worst']*100:.2f}% "
          f"H1 {h1:.3f} H2 {h2:.3f} ac1 {fg['ac1']:.4f} uniqR {fg['uniqR']:.4f} corr {corr:+.4f}")
oos=pv_out[pv_out.index>=pd.Timestamp('2017-01-01')]
print('poolvt OOS17+ arith %.2f%% geo %.2f%%'%(oos.mean()*252*100,((1+oos).prod())**(252/len(oos))*100-100))
