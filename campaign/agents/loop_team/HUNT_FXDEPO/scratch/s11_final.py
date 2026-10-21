"""FINAL CANDIDATE BUILD: FXD1_KRWTRI (KRW3 lb(21,63) z-rev, cap2) — battery + delivery.
Fix: dedupe DEXKO column in joint pos frame by renaming books B1,B2,B3."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *

px=pd.DataFrame({n:dex(n) for n in ['DEXKOUS','DEXSDUS','DEXSFUS','DEXNOUS']})
lp=np.log(px); rets=px.pct_change()
champ=load_champion()
books=[('DEXKOUS','DEXSDUS'),('DEXKOUS','DEXSFUS'),('DEXKOUS','DEXNOUS')]

def build(lbs=(21,63), cap=2.0, vt=None):
    rs=[]; PALL=[]; RALL=[]
    for i,(a,b) in enumerate(books):
        sp=lp[a]-lp[b]
        pos=sum(zpos(sp,lb,cap) for lb in lbs)/len(lbs)
        P=pd.DataFrame({f'B{i}_long_{a[-4:]}':pos, f'B{i}_short_{b[-4:]}':-pos})
        R=pd.DataFrame({f'B{i}_long_{a[-4:]}':rets[a], f'B{i}_short_{b[-4:]}':rets[b]})
        rs.append(net_of_book(P,R)); PALL.append(P); RALL.append(R)
    r=pd.concat([x.fillna(0) for x in rs],axis=1).sum(axis=1)/len(books)
    if vt:
        rv=r.expanding(60).std()*np.sqrt(252)
        sc=(vt/rv).clip(upper=8.0).shift(1).fillna(1.0)
        r=r*sc
    return r.dropna(), PALL, RALL

print('cap plateau KRW3 lb(21,63):')
for cap in [1.0,1.5,2.0,2.5]:
    r,_,_=build(cap=cap); r8=r[r.index>='2008-01-01']
    print(f'  cap{cap}: SR {full_stats(r8)["sr"]:.3f}')
print('lb plateau (cap2):')
for lbs in [(21,),(63,),(21,63),(21,42,63)]:
    r,_,_=build(lbs=lbs); r8=r[r.index>='2008-01-01']
    print(f'  lb{lbs}: SR {full_stats(r8)["sr"]:.3f}')

r_raw, PALL, RALL = build()
r_vt, _, _ = build(vt=0.08)
common=r_raw.index
POSa=pd.concat([p.reindex(common).fillna(0.0) for p in PALL],axis=1).shift(1).fillna(0.0)
RETa=pd.concat([rr.reindex(common).fillna(0.0) for rr in RALL],axis=1)[POSa.columns]

for tag,rr in [('FXD1_KRWTRI_raw',r_raw),('FXD1_KRWTRI_poolvt',r_vt)]:
    r8=rr[rr.index>='2008-01-01']
    g=gate_battery(tag, r8, POSa, RETa, champ)
    print('  yearly:', g['stats']['yearly'])
    from campaign.harness.data import save_sleeve
    out=f'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/sleeves/{tag}_daily.csv'
    meta=(f"FXD1_KRWTRI: 3-book DEX z-reversion (KRW/SEK, KRW/CHF, KRW/NOK), log-spread z "
          f"lb(21,63) averaged, w=clip(-z,+-2)/2 per leg, EW books, T+1 (pos.shift(1)), "
          f"6bps/side on |dpos|/2 per leg, borrow 0.5%/yr on shorts. "
          f"variant={tag.split('_',1)[1] if 'vt' in tag else 'raw'}"
          + (", trailing expanding vol-target 0.08 cap 8 shift(1)" if 'vt' in tag else ""))
    save_sleeve(r8.round(12), out, meta)
    print('  saved',out)
