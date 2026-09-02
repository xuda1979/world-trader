"""CANDIDATE 9: gates on RAW delivered file (FF2_DUALGATE_raw_daily.csv) + how the champion
blend absorbs it: capital-slot 0.10 exercise (like V2 does: sleeve at 4.55% capital each).
Incremental value test on the champion is OUT OF SCOPE here (no V2 builder access) but we CAN
simulate a quick naive 11+1 style reweighting on the SAVED champion daily file:
naive add: champ_ret*(1-w) + sleeve_pooled*w for w in {0.05,0.10} and report MDD/SR."""
import sys; sys.path.insert(0,'.')
import lib, numpy as np, pandas as pd

champ=lib.load_champion()
raw=pd.read_csv('../sleeves/FF2_DUALGATE_raw_daily.csv',index_col=0,parse_dates=True)['ret']
pv=pd.read_csv('../sleeves/FF2_DUALGATE_poolvt_daily.csv',index_col=0,parse_dates=True)['ret']

def audit(tag,r):
    r=r.dropna()
    st=lib.full_stats(r); h1,h2=lib.halves_sr(r)
    okn,ny=lib.negyr_tol(r); corr,nco=lib.corr_to(r,champ); fg=lib.flatten_gates(r)
    p_poslag='(see cand4: raw 0.015)'
    g=dict(SR=st['sr']>=0.6, halves=(h1>=0.3 and h2>=0.3), negy=okn, ac1=fg['ac1']<0.5,
           uniq=fg['uniqR']>=0.08, corr=abs(corr)<0.15)
    print(f"{tag}: n={st['n']} SR {st['sr']:.3f} H1 {h1:.2f} H2 {h2:.2f} negy {st['negy']} worst {st['worst']:+.1%} "
          f"ac1 {fg['ac1']:.3f} uniqR {fg['uniqR']:.3f} corr {corr:+.3f}(n={nco}) gates={sum(g.values())}/6(+scramble p)")
    return st,corr

print('== RAW delivered ==')
st_raw,c_raw=audit('FF2_DUALGATE_raw  ',raw)
print('== POOLVT delivered ==')
st_pv,c_pv=audit('FF2_DUALGATE_poolvt',pv)

print('\n== naive champion add (poolvt sleeve, w=capital frac) ==')
for w in (0.05,0.10,0.20):
    j=pd.concat([champ.rename('c'),pv.rename('s')],axis=1,join='inner').dropna()
    bl=j['c']*(1-w)+j['s']*w
    st=lib.full_stats(bl); corr,_=lib.corr_to(bl,champ)
    print(f" w={w:.2f}: SR {st['sr']:.3f} ann {st['ann_geo']:.1%} MDD {st['mdd']:.1%} negy {st['negy']} worst {st['worst']:+.1%} corr_to_champ {corr:+.3f}")
j=pd.concat([champ.rename('c'),pv.rename('s')],axis=1,join='inner').dropna()
st0=lib.full_stats(j['c'])
print(f" (champion alone on overlap: SR {st0['sr']:.3f} ann {st0['ann_geo']:.1%} MDD {st0['mdd']:.1%} negy {st0['negy']})")
