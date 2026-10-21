# Independent re-run of the recovered-builder logic in MY OWN script to confirm byte-exactness claims:
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign')
from champion_build import load, vt
from pandas.tseries.holiday import USFederalHolidayCalendar

STRICT={
 "brwt15":"campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 "brwt10":"campaign/agents/COORD/sleeves/brwt10_2000.csv",
 "brwt7":"campaign/agents/COORD/sleeves/brwt7.csv",
 "brwt5":"campaign/agents/COORD/sleeves/brwt5.csv",
 "C5ng":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsum":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 "A5r2":"campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 "a6r7":"campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "QAxasts":"campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 "carryv2":"campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
 "XGB1y":"campaign/results/sleeve_library/XGB1y_deploy.csv",
}
EXEC={'brwt15':1.5,'brwt10':1.5,'brwt7':1.5,'brwt5':1.5,'C5ng':5,'C5ngsum':5,'A5r2':6,
      'a6r7':5,'QAxasts':8,'carryv2':8,'dualmom':15,'XGB1y':15}
SHORTF={'dualmom':0.5,'XGB1y':0.5,'QAxasts':0.4,'carryv2':0.3,'C5ng':0.5,'C5ngsum':0.5,
        'brwt15':0.5,'brwt10':0.5,'brwt7':0.5,'brwt5':0.5,'A5r2':0,'a6r7':0}
cal=USFederalHolidayCalendar(); hol=set(cal.holidays(start='2006-01-01',end='2026-12-31').date)
def sn(p):
    r=load(p).dropna()
    keep=np.array([(d.dayofweek<5 and d.date() not in hol) for d in r.index])
    out=pd.Series(0.0,index=r.index[keep]); cu=0.0; ki=0; v=r.values
    for i in range(len(r)):
        cu+=v[i]
        if keep[i]: out.iloc[ki]=cu; cu=0.0; ki+=1
    return out.iloc[:ki]
N=len(STRICT); RAW={};S={}
for n,p in STRICT.items():
    r=sn(p); RAW[n]=r
    v,s=vt(r,0.10); S[n]=s
Sn=pd.DataFrame(S).dropna(how='all'); capW=Sn/N
def build(TGT,THR):
    V={}
    for n in STRICT:
        r=RAW[n]
        v,s=vt(r,0.10)
        v=v-capW[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4)
        V[n]=v
    Vn=pd.DataFrame(V); Sn2=pd.DataFrame(Sn)
    W=Sn2.div(Sn2.sum(axis=1),axis=0).fillna(0)
    blend=Vn.mean(axis=1); blend=blend[blend.index>='2006-10-01']
    tw=((W-W.shift(1)).abs()*0.5).sum(axis=1)
    b,_=vt(blend,TGT)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=b.index); b=b*sc; dsc=sc.diff().abs()*0.5
    r_out=b-(tw.reindex(b.index).fillna(0)+dsc.fillna(0))*6e-4
    htb=pd.Series(0.0,index=Sn2.index)
    for n in STRICT:
        sf=SHORTF[n]
        if sf>0:
            gn=Sn2[n]/N*sc*sf
            htb=htb+gn*(0.005+(0.03 if n in('dualmom','XGB1y') else 0.0)*0.2)
    return (r_out-htb/252).dropna()
A=build(0.07,0.04); B=build(0.091,0.03); BAL=((A+B)/2).dropna()
tgt = pd.read_csv('/Users/daxu/software/world-trader/campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
j=pd.concat([BAL.rename('mine'), tgt.rename('comm')],axis=1,join='inner').dropna()
d=(j['mine']-j['comm']).abs()
print(f"INDEPENDENT re-run: n={len(j)} max|d|={d.max():.3e} exact={(d<1e-15).sum()} corr={j.corr().iloc[0,1]:.8f}")
print(f"my BAL ann={BAL.mean()*252*100:.2f}% SR={BAL.mean()/BAL.std()*np.sqrt(252):.3f}")
# honesty notes: does throttle use tdd with eq.shift(1) — yes (shifted) => trailing. vt uses shift(1) (champion_build.vt)
import inspect
print(inspect.getsource(vt))
