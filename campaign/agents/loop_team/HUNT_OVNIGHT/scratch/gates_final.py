"""FINAL gate battery for OVNCAP candidates with correctly-specified two-stream scramble
(position_lag_p2), vol-target tgt 0.10 cap 3 trailing expanding min60 (campaign convention).
Charter gates: SR>=0.6 2008+ | H1,H2>=0.3 | <=2 neg yrs each>-5% | poslag 200x p<0.05 |
|corr|<0.15 to HONEST14V3_BALANCED | ac1<0.5 | uniqR>=0.08."""
import sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd, hunt_lib as H

on,ic=H.onic()
champ=H.load_champion()

def run(lb,k,seed=0,nperm=200,minper=21):
    sig=on.rolling(lb,min_periods=max(2,lb//3)).mean()
    pos=H.xs_ls(sig,k=k)
    common=on.index
    p=pos.shift(1).reindex(common).fillna(0.0)
    r1=on.reindex(common).fillna(0.0); r2=ic.reindex(common).fillna(0.0)
    turn=(p.diff().abs().sum(axis=1)/2.0).fillna(0.0)
    bor=p.clip(upper=0).abs().sum(axis=1)*H.BORROW
    net=(p.mul(r1).sum(axis=1)-p.mul(r2).sum(axis=1)-turn*H.COST-bor).dropna()
    rv=net.expanding(60).std()*np.sqrt(252)
    sc=(0.10/rv).clip(upper=3.0).shift(1).fillna(1.0)
    netv=net*sc
    r=netv.dropna(); r=r[r.index>=pd.Timestamp('2008-01-01')]
    st=H.full_stats(r); h1,h2=H.halves_sr(r); okn,ny=H.negyr_tol(r)
    fg=H.flatten_gates(r); corr,nc=H.corr_to(r,champ)
    pl_p,pl_real=H.position_lag_p2(pos,on,ic,n=nperm,seed=seed,min_lag=minper)
    g=dict(SR=st['sr'],gate_SR=bool(st['sr']>=0.6),H1=h1,H2=h2,gate_halves=bool(h1>=0.3 and h2>=0.3),
           negy=st['negy'],worst=st['worst'],gate_negy=bool(okn),
           scramble_p=pl_p,scramble_real=pl_real,gate_scramble=bool(pl_p<0.05),
           ac1=fg['ac1'],gate_ac1=bool(fg['ac1']<0.5),uniqR=fg['uniqR'],gate_uniq=bool(fg['uniqR']>=0.08),
           corr=corr,gate_corr=bool(abs(corr)<0.15),n_corr=nc)
    npass=sum([g['gate_SR'],g['gate_halves'],g['gate_negy'],g['gate_scramble'],g['gate_ac1'],g['gate_uniq'],g['gate_corr']])
    print(f"OVNCAP lb{lb} k{k}: SR {st['sr']:.3f} | H1 {h1:.2f} H2 {h2:.2f} | negy {st['negy']}/{st['years']} worst {st['worst']*100:+.1f}% | poslag2_p {pl_p:.3f} | ac1 {fg['ac1']:.3f} uniqR {fg['uniqR']:.3f} | corr {corr:+.3f}(n={nc}) | ann_geo {st['ann_geo']*100:+.1f}% MDD {st['mdd']*100:.1f}% | GATES {npass}/7")
    return g,st,netv

res={}
for lb in [63,126,189,252]:
    for k in [15,25,50]:
        g,st,netv=run(lb,k)
        res[(lb,k)]=(g,st,netv)
import pickle
pickle.dump(res,open('scratch/gates_res.pkl','wb'))
