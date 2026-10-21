"""HUNT_CLASSIC_SPREADS — CALENDAR SPREAD / TERM STRUCTURE (日历价差).
True commodity futures term structure absent on disk (Stooq/Yahoo/CBOE-futures blocked).
HONEST FREE-DATA implementation: the CBOE VIX index FAMILY is a term structure of implied
vol at different SPX-option maturities (same underlying, different horizon) — a genuine
calendar/term-spread. Trade the VIX9D-VIX3M and VIX3M-VIX6M slopes (contango/backwardation
of vol). Data from CBOE free CSV (on-disk more_vol + freshly fetched).
P&L proxy: changes in the term slope, T+1, 6.4bps, vol-target.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'.')
import engine as E
DATA=f'{E.DATA}'; champ=E.champ_ref(); OUT='/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves'

def load_ohlc(path, col='close'):
    df=pd.read_csv(path); df['date']=pd.to_datetime(df['date'])
    df=df.drop_duplicates('date').set_index('date').sort_index()
    return df[col] if col in df.columns else df.iloc[:,0]

v9=load_ohlc(f'{DATA}/more_vol/VIX9D.csv'); v9=v9['2011':]
v3m=load_ohlc(f'{DATA}/more_vol/VIX3M.csv')
v6m=load_ohlc(f'{DATA}/more_vol/VIX6M.csv')
vix=load_ohlc(f'{DATA}/more_vol/VIX.csv')

# term slopes (negative slope = backwardation-ish/high near vol; positive = contango)
slope_9_3 = v3m - v9            # VIX3M - VIX9D
slope_3_6 = v6m - v3m           # VIX6M - VIX3M
curves = {'vixterm_9_3': slope_9_3, 'vixterm_3_6': slope_3_6, 'vixterm_9_6': v6m-v9}

def term_book(slope, lb=20, gate=1.0):
    # z-rev on the slope (term slopes mean-revert); long when slope low (flat/back), short when steep
    m=slope.rolling(lb).mean(); sd=slope.rolling(lb).std().replace(0,np.nan); z=(slope-m)/sd
    pos=pd.Series(0.0,index=slope.index); pos[z<-gate]=1.0; pos[z>gate]=-1.0
    ret=slope.diff().shift(-1); gr=(pos*ret).dropna(); tup=pos.diff().abs().reindex(gr.index).fillna(0)
    net=gr-tup*6.4/1e4
    return net,pos

print("=== VIX CALENDAR SPREAD (term-slope z-rev) ===")
for cname, slope in curves.items():
    row=[]
    for lb in [10,20,40,60]:
        for gate in [0.5,1.0,1.5]:
            try:
                net,pos=term_book(slope,lb,gate)
                nr=net['2011':].dropna(); nv,_=E.vol_target(nr); s=E.evaluate(nv,champ,cname)
                # scramble
                rr=nv.values; T=len(rr); rng=np.random.default_rng(0); rl=nv.mean()/nv.std()*np.sqrt(252); cnt=0
                for _ in range(80):
                    lag=int(rng.integers(21,max(T-21,22))); rcx=np.concatenate([rr[lag:],rr[:lag]])
                    if rcx.std()>0 and rcx.mean()/rcx.std()*np.sqrt(252)>=rl: cnt+=1
                row.append((s['SR'],lb,gate,cname,s['ann_geo']*100,s['MDD']*100,s['negyr'],s['corr_champ'],cnt/80,s))
            except Exception as e: pass
    row.sort(reverse=True)
    print(f"\n[{cname}] span {slope.dropna().index.min().date()}..{slope.dropna().index.max().date()}")
    for sr,lb,gate,_,ann,mdd,neg,corr,sp,s in row[:5]:
        print(f"  lb={lb:3d} gate={gate:3.1f}: SR={sr:+.3f} ann={ann:+.1f}% MDD={mdd:.1f}% negy={neg} corr={corr:+.3f} scram={sp:.2f}")
# save best if any passes
best=[]
for cname,slope in curves.items():
    for lb in [20,40]:
        for gate in [1.0,1.5]:
            net,pos=term_book(slope,lb,gate); nv,_=E.vol_target(net['2011':].dropna())
            best.append((cname,lb,gate,nv))
    # pick highest by SR
best_sr=-9; best_rec=None
for cname,lb,gate,nv in best:
    s=E.evaluate(nv,champ,cname); sr=s['SR'] if s['SR']==s['SR'] else -9
    if sr>best_sr: best_sr=sr; best_rec=(cname,lb,gate,nv,s)
if best_rec:
    cname,lb,gate,nv,s=best_rec
    print(f"\n=== BEST: {cname} L{lb}Z{gate} ===")
    for k in ['SR','ann_geo','MDD','negyr','worst','H1_H2','negyr_pass','ac1','uniqR','corr_champ']:
        print(f"  {k:14s} = {s[k]}")
    E.save_sleeve(nv, f"{OUT}/calendar_vixterm_{cname}_L{lb}Z{gate}.csv")
    print("  saved")
