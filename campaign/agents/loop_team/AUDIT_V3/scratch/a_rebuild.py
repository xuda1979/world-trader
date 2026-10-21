"""AUDIT_V3 target 1/3/4/5: OWN-loader independent rebuild of V3 (no committed builder import),
leverage recompute, yearly scoping, cost accounting, NEW2 (minus FF2) + pool-only deltas."""
import sys, numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
from pandas.tseries.holiday import USFederalHolidayCalendar
cal=USFederalHolidayCalendar(); HOL=set(cal.holidays(start='2006-01-01',end='2026-12-31').date)

def load(rel):
    df=pd.read_csv(f"{ROOT}/{rel}",index_col=0); df.index=pd.to_datetime(df.index)
    c="ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)

def rollup(r):  # my own re-implementation of weekend/holiday aggregation
    r=r.dropna(); v=r.values
    keep=np.array([(d.dayofweek<5 and d.date() not in HOL) for d in r.index])
    out=pd.Series(0.0,index=r.index[keep]); cu=0.0; ki=0
    for i in range(len(r)):
        cu+=v[i]
        if keep[i]: out.iloc[ki]=cu; cu=0.0; ki+=1
    return out.iloc[:ki]

def vt(r,tgt,min_win=60,cap=8.0):
    vol=r.rolling(min_win).std().shift(1)*np.sqrt(252)
    s=(tgt/vol).clip(upper=cap); s[vol.isna()]=0
    return r*s.fillna(0),s

POOL={
 "brwt15":"campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 "brwt10":"campaign/agents/COORD/sleeves/brwt10_2000.csv",
 "brwt7":"campaign/agents/COORD/sleeves/brwt7.csv","brwt5":"campaign/agents/COORD/sleeves/brwt5.csv",
 "C5ng":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsum":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 "A5r2":"campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 "a6r7":"campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "QAxasts":"campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 "carryv2":"campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv"}
EXEC={'brwt15':1.5,'brwt10':1.5,'brwt7':1.5,'brwt5':1.5,'C5ng':5,'C5ngsum':5,'A5r2':6,
      'a6r7':5,'QAxasts':8,'carryv2':8,'dualmom':15}
SHORTF={'dualmom':0.5,'QAxasts':0.4,'carryv2':0.3,'C5ng':0.5,'C5ngsum':0.5,
        'brwt15':0.5,'brwt10':0.5,'brwt7':0.5,'brwt5':0.5,'A5r2':0,'a6r7':0}
NEW2={"diescrack":"campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
      "CFX4":"campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv"}
NEW3=dict(NEW2); NEW3["FF2"]="campaign/agents/loop_team/HUNT_FF2/sleeves/FF2_DUALGATE_poolvt_daily.csv"

def make(NEW,SW=0.10,PS=0.08):
    RAW={n:rollup(load(p)) for n,p in POOL.items()}
    RAW.update({n:load(p).dropna() for n,p in NEW.items()})
    names=list(RAW)
    slots={n:(1.0 if n in POOL else SW) for n in names}
    tot=sum(slots.values()); wts=pd.Series({n:slots[n]/tot for n in names},dtype=float)
    S={};V={}
    for n,r in RAW.items(): V[n],S[n]=vt(r,PS)
    Sd=pd.DataFrame(S).dropna(how='all'); capW=Sd.mul(wts,axis=1)
    for n in POOL:
        V[n]=V[n]-capW[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4)
    Vn=pd.DataFrame(V)
    W=Sd.div(Sd.sum(axis=1),axis=0).fillna(0)
    blend=Vn.mul(wts,axis=1).sum(axis=1)
    blend=blend[blend.index>='2006-10-01']
    tw=((W-W.shift(1)).abs()*0.5).sum(axis=1)
    return Sd,capW,blend,tw,wts

def build(capW,blend,tw,TGT,THR):
    b,gb=vt(blend,TGT)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=b.index); b=b*sc; dsc=sc.diff().abs()*0.5
    full=capW.mul(gb,axis=0).mul(sc,axis=0)
    reb=full.diff().abs().sum(axis=1)
    r=b-(tw.reindex(b.index).fillna(0)+dsc.fillna(0))*6e-4-reb.reindex(b.index).fillna(0)*6e-4
    terms=[capW[n]*sc*SHORTF[n]*(0.005+(0.006 if n=='dualmom' else 0.0)) for n in POOL if SHORTF[n]>0]
    htb=pd.concat(terms,axis=1).sum(axis=1)
    return (r-htb.reindex(r.index).fillna(0)/252).dropna(how='all'), full, gb, sc, tw, dsc, reb

def stats(r,label,start='2008-03-31'):
    rr=r[r.index>=start]; eq=(1+rr).cumprod()
    m=(1+rr).resample('ME').prod()-1
    yr=rr.groupby(rr.index.year).apply(lambda x:(1+x).prod()-1)
    print(f"{label}: n={len(rr)} ann_arith {rr.mean()*252*100:.2f}% ann_geo {((eq.iloc[-1])**(252/len(rr))-1)*100:.2f}% "
          f"SR_d {rr.mean()/rr.std()*np.sqrt(252):.3f} SR_m {m.mean()/m.std()*np.sqrt(12):.3f} "
          f"MDD {((eq/eq.cummax())-1).min()*100:.2f}% vol {rr.std()*np.sqrt(252)*100:.2f}% "
          f"neg {int((yr<0).sum())}/{yr.size} worst_yr {yr.min()*100:.2f}%")
    return rr,yr

print("=== T1: OWN-loader independent rebuild vs committed CSVs ===")
outs={}
for tag,NEW in [("HONEST14V3",NEW3),("HONEST13V2",NEW2)]:
    Sd,capW,blend,tw,wts=make(NEW)
    A,fullA,_,_,_,_,_=build(capW,blend,tw,0.07,0.04)
    B,fullB,_,_,_,_,_=build(capW,blend,tw,0.091,0.03)
    BAL=((A+B)/2).dropna()
    for cfg,r in [("SAFE",A),("AGGRESSIVE",B),("BALANCED",BAL)]:
        fn=f"campaign/results/GOAL100_{tag}_{cfg}_daily.csv"
        old=load(fn); j=pd.concat([old.rename('o'),r.rename('n')],axis=1,join='inner').dropna()
        md=float((j.o-j.n).abs().max())
        idxok = len(j)==max(len(old),len(r))
        print(f"{fn}: max|mine-committed|={md:.3e} rows mine={len(r)} committed={len(old)} idxmatch={idxok} {'IDENTICAL' if md<1e-12 else 'DIFF'}")
        if tag=="HONEST14V3": outs[cfg]=(r,fullB if cfg=='AGGRESSIVE' else (fullA if cfg=='SAFE' else None))
    if tag=="HONEST14V3":
        BAL3=BAL; Sd3,capW3,tw3,wts3=Sd,capW,tw,wts
        full_bal=((fullA+fullB)/2)

print("\n=== T1b: headline stats (emit convention, 2008-03-31+) ===")
rr3,yr3=stats(BAL3,"V3 BALANCED (mine)")
rrA,_=stats(outs['SAFE'][0],"V3 SAFE (mine)")
rrB,_=stats(outs['AGGRESSIVE'][0],"V3 AGGR (mine)")

print("\n=== T4: yearly table V3 BALANCED ===")
yfull=BAL3.groupby(BAL3.index.year).apply(lambda x:(1+x).prod()-1)
print("FULL-window yearly (%):"); print({int(k):round(v*100,2) for k,v in yfull.items()})
print("2006 stub (from 2006-10-02): %.2f%%  2007: %.2f%%"%(yfull.get(2006,np.nan)*100,yfull.get(2007,np.nan)*100))
print("2008+ yearly (%):"); print({int(k):round(v*100,2) for k,v in yr3.items()})
print("min 2008+ year: %.3f%%"% (yr3.min()*100))

print("\n=== T3: capital-real gross leverage (V3 BALANCED, full-weight matrix mean(A,B) ) ===")
g=full_bal.fillna(0).abs().sum(axis=1); g=g.reindex(BAL3.index).fillna(0)
live=g[g.index>='2008-03-31']
print(f"gross leverage 2008-03-31+: mean {live.mean():.3f}x  p50 {live.median():.3f}x  p95 {np.percentile(live,95):.3f}x  max {live.max():.3f}x  frac>1.6x {(live>1.6).mean()*100:.1f}%  frac>1x {(live>1).mean()*100:.1f}%")
f=(1.6/live).clip(upper=1.0)
r16=BAL3*f
stats(r16,"V3 BAL @1.6x gross cap (no financing charge)")
for rate in [0.02,0.045]:
    fin=(live*f.reindex(live.index)-1).clip(lower=0)*rate/252
    r16f=(BAL3*f - fin.reindex(BAL3.index).fillna(0)).dropna()
    stats(r16f,f"V3 BAL @1.6x cap + margin {rate*100:.1f}%/yr on (gross-1)")

print("\n=== T5: cost accounting (V3 BALANCED, 2008-03-31+) ===")
Sd,capW,blend,tw,wts=make(NEW3)
A,fullA,gb,sc,tw_,dsc,reb=build(capW,blend,tw,0.07,0.04)
B,fullB,gb2,sc2,tw2,dsc2,reb2=build(capW,blend,tw,0.091,0.03)
idx=BAL3.index
turn=((tw_.reindex(idx).fillna(0)+dsc.fillna(0))+(tw2.reindex(idx).fillna(0)+dsc2.fillna(0)))/2 + (rebA:=reb.reindex(idx).fillna(0)+reb2.reindex(idx).fillna(0))/2
live_t=turn[turn.index>='2008-03-31']
ann_turn=live_t.mean()*252
print(f"one-side turnover/day: reb-blend {live_t.mean()*1e4:.2f}bps  annualized {ann_turn*100:.0f}% of NAV")
print(f"drag @6.0bps/side: {ann_turn*6e-4*100:.2f}%/yr   @6.4bps: {ann_turn*6.4e-4*100:.2f}%/yr   gap(0.4bps)={ann_turn*0.4e-4*100:.2f}%/yr")
htb_ann=None
terms=[capW[n]*sc*SHORTF[n]*(0.005+(0.006 if n=='dualmom' else 0.0)) for n in POOL if SHORTF[n]>0]
htb=pd.concat(terms,axis=1).sum(axis=1)
hlive=(htb.reindex(idx).fillna(0)/252); hlive=hlive[hlive.index>='2008-03-31']
print(f"borrow drag (short legs, 0.5%/yr + dualmom uplift to 1.1%): {hlive.mean()*252*100:.3f}%/yr")

print("\n=== T2-quant: FF2 contribution = V3(NEW3) minus NEW2(13 engines) minus pool-only(11) ===")
for tag,NEW in [("V3_14eng(NEW3)",NEW3),("NEW2_13eng(no FF2)",NEW2),("POOL11",{})]:
    Sd,capW,blend,tw,wts=make(NEW)
    A,_,_,_,_,_,_=build(capW,blend,tw,0.07,0.04)
    B,_,_,_,_,_,_=build(capW,blend,tw,0.091,0.03)
    BAL=((A+B)/2).dropna()
    stats(BAL,f"{tag} BALANCED")
