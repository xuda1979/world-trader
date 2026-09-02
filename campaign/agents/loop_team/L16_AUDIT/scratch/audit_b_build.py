import sys; sys.path.insert(0,'campaign/scripts')
import numpy as np, pandas as pd
from champion_build import load, vt
from pandas.tseries.holiday import USFederalHolidayCalendar
ROOT="/Users/daxu/software/world-trader"

POOL = {
 "brwt15": "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 "brwt10": "campaign/agents/COORD/sleeves/brwt10_2000.csv",
 "brwt7" : "campaign/agents/COORD/sleeves/brwt7.csv",
 "brwt5" : "campaign/agents/COORD/sleeves/brwt5.csv",
 "C5ng"  : "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsum":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 "A5r2"  : "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 "a6r7"  : "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "QAxasts":"campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 "carryv2":"campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
}
EXEC = {'brwt15':1.5,'brwt10':1.5,'brwt7':1.5,'brwt5':1.5,'C5ng':5,'C5ngsum':5,'A5r2':6,'a6r7':5,'QAxasts':8,'carryv2':8,'dualmom':15}
SHORTF = {'dualmom':0.5,'QAxasts':0.4,'carryv2':0.3,'C5ng':0.5,'C5ngsum':0.5,'brwt15':0.5,'brwt10':0.5,'brwt7':0.5,'brwt5':0.5,'A5r2':0,'a6r7':0}
cal = USFederalHolidayCalendar(); hol=set(cal.holidays(start='2006-01-01',end='2026-12-31').date)
def sn(p):
    r=load(p).dropna()
    keep=np.array([(d.dayofweek<5 and d.date() not in hol) for d in r.index])
    out=pd.Series(0.0,index=r.index[keep]); cu=0.0; ki=0; v=r.values
    for i in range(len(r)):
        cu+=v[i]
        if keep[i]: out.iloc[ki]=cu; cu=0.0; ki+=1
    return out.iloc[:ki]

N=len(POOL)
Sn=pd.DataFrame({n:vt(sn(p),0.10)[1] for n,p in POOL.items()}).dropna(how='all')
capW=Sn/N

def build(TGT,THR,PERSLEEVE=0.08):
    V={}
    Scales={}
    for n in POOL:
        r=sn(POOL[n])
        v,s=vt(r,PERSLEEVE)          # L16 change: 0.08 per-sleeve target
        cap=capW[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4)
        V[n]=v-cap; Scales[n]=s
    Vn=pd.DataFrame(V)
    W=Sn.div(Sn.sum(axis=1),axis=0).fillna(0)
    blend=Vn.mean(axis=1); blend=blend[blend.index>='2006-10-01']
    tw=((W-W.shift(1)).abs()*0.5).sum(axis=1)
    b,sb=vt(blend,TGT)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=b.index); b=b*sc; dsc=sc.diff().abs()*0.5
    r_out=b-(tw.reindex(b.index).fillna(0)+dsc.fillna(0))*6e-4
    htb=pd.Series(0.0,index=Sn.index)
    for n in POOL:
        sf=SHORTF[n]
        if sf>0:
            gn=Sn[n]/N*sc*sf
            htb=htb+gn*(0.005+(0.03 if n=='dualmom' else 0.0)*0.2)
    out=(r_out-htb/252).dropna()
    meta={"global_scale":sb,"throttle":sc,"sleeve_scales":pd.DataFrame(Scales),"turnover":tw}
    return out,meta

A,ma=build(0.07,0.04); B,mb=build(0.091,0.03); BAL=((A+B)/2).dropna()
print("BAL n",len(BAL),BAL.index.min(),BAL.index.max())
eq=(1+BAL).cumprod(); mdd=(eq/eq.cummax()-1).min()*100
m=(1+BAL).resample('ME').prod()-1
print(f"repro BAL: ann {(eq.iloc[-1]**(252/len(BAL))-1)*100:.2f}% SR_d {BAL.mean()/BAL.std()*np.sqrt(252):.3f} SR_m {m.mean()/m.std()*np.sqrt(12):.3f} MDD {mdd:.2f}%")
yr=BAL.groupby(BAL.index.year).apply(lambda x:(1+x).prod()-1)
print("neg yrs",int((yr<0).sum()),"worst yr",f"{yr.min()*100:.2f}%")

for fn,r in [("GOAL100_HONEST11L16_BALANCED_daily.csv",BAL),("GOAL100_HONEST11L16_SAFE_daily.csv",A),("GOAL100_HONEST11L16_AGGRESSIVE_daily.csv",B)]:
    old=pd.read_csv(f"{ROOT}/campaign/results/{fn}",index_col=0,parse_dates=True).iloc[:,0]
    j=pd.concat([old.rename('old'),r.rename('new')],axis=1,join='inner').dropna()
    md=float((j.old-j.new).abs().max()); rel=float((j.old-j.new).abs().max()/old.abs().max())
    print(f"{fn}: n_join={len(j)} max|new-old|={md:.3e} rel={rel:.3e} {'MATCH' if md<1e-12 else 'DIFF'}")

BAL.to_frame('ret').to_csv(f"{ROOT}/campaign/agents/loop_team/L16_AUDIT/scratch/repro_BAL.csv")
ma['global_scale'].to_frame('gs').to_csv(f"{ROOT}/campaign/agents/loop_team/L16_AUDIT/scratch/scale_A.csv")
mb['global_scale'].to_frame('gs').to_csv(f"{ROOT}/campaign/agents/loop_team/L16_AUDIT/scratch/scale_B.csv")
ma['sleeve_scales'].to_csv(f"{ROOT}/campaign/agents/loop_team/L16_AUDIT/scratch/sleeve_scales_A.csv")
mb['sleeve_scales'].to_csv(f"{ROOT}/campaign/agents/loop_team/L16_AUDIT/scratch/sleeve_scales_B.csv")
