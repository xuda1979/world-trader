"""RECON 6: VIX-gated MOM/HML/MKT timing (native VIX source, not factor-rv); FF cross-family
combos; MOM timing with trend override; dual (rv + VIX) gates."""
import sys; sys.path.insert(0,'.')
import lib, numpy as np, pandas as pd, glob

champ=lib.load_champion()
def build(pos,r):
    net,_=lib.net_of(pos,r)
    rv=net.expanding(60).std()*np.sqrt(252)
    net=net*((0.10/rv).clip(upper=3.0).shift(1).fillna(1.0))
    return net[net.index>=pd.Timestamp('2008-01-01')].dropna()
def stats(tag,net):
    st=lib.full_stats(net); h1,h2=lib.halves_sr(net)
    okn,ny=lib.negyr_tol(net); corr,_=lib.corr_to(net,champ); fg=lib.flatten_gates(net)
    print(f"{tag}: SR {st['sr']:.2f} ann {st['ann_geo']:.1%} MDD {st['mdd']:.1%} negy {st['negy']} worst {st['worst']:+.1%} "
          f"H1 {h1:.2f} H2 {h2:.2f} corr {corr:+.3f} ac1 {fg['ac1']:.2f} uniqR {fg['uniqR']:.2f}")
    return net

ff=lib.load_ff3(); mom=lib.load_mom(); vix=lib.load_vix()
F={'MOM':mom['MOM'],'MKT':ff['Mkt-RF'],'HML':ff['HML'],'SMB':ff['SMB']}
res={}
for nm,s in F.items():
    s=s[s.index>='2005-01-01']
    v=vix.reindex(s.index).ffill()
    for ma in (63,126,252,504):
        z=(v-v.rolling(ma).mean())/v.rolling(ma).std()
        for th in (0.0,0.5,-0.5,1.0,-1.0):
            pos=pd.Series(np.where(z.shift(1)<th,1.0,0.0),index=s.index)
            res[f'vix_{nm}_ma{ma}_z{th:+.1f}']=build(pos,s)
top=sorted(res.items(),key=lambda kv:-(kv[1].mean()/kv[1].std()*np.sqrt(252)))[:12]
for k,v_ in top: stats(k,v_)
