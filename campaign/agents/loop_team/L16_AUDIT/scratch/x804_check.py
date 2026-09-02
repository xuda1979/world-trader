import sys; sys.path.insert(0,'campaign/scripts')
import numpy as np, pandas as pd
from champion_build import load, vt
from pandas.tseries.holiday import USFederalHolidayCalendar
ROOT="/Users/daxu/software/world-trader"
exec(open('campaign/agents/loop_team/L16_AUDIT/scratch/audit_b_build.py').read().split("A,ma=build")[0])
# internal consistency of committed trio
S=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_SAFE_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
G=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_AGGRESSIVE_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
B=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
half=(S+G)/2
j=pd.concat([B.rename('b'),half.rename('h')],axis=1,join='inner').dropna()
print(f"BAL == (SAFE+AGGR)/2? max|d|={float((j.b-j.h).abs().max()):.3e}")

# X804 with its own convention (Sn at 0.10 per LOOP_SR_LEVERAGE table)
Sn10=pd.DataFrame({n:vt(sn(p),0.10)[1] for n,p in POOL.items()}).dropna(how='all')
capW10=Sn10/N
def build10(TGT,THR):
    V={};S={}
    for n in POOL:
        r=sn(POOL[n]); v,s=vt(r,0.10)
        V[n]=v-capW10[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4); S[n]=s
    Vn=pd.DataFrame(V)
    W=Sn10.div(Sn10.sum(axis=1),axis=0).fillna(0)
    blend=Vn.mean(axis=1); blend=blend[blend.index>='2006-10-01']
    tw=((W-W.shift(1)).abs()*0.5).sum(axis=1)
    b,sb=vt(blend,TGT)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=b.index); b=b*sc; dsc=sc.diff().abs()*0.5
    r_out=b-(tw.reindex(b.index).fillna(0)+dsc.fillna(0))*6e-4
    htb=pd.Series(0.0,index=Sn10.index)
    for n in POOL:
        sf=SHORTF[n]
        if sf>0:
            gn=Sn10[n]/N*sc*sf; htb=htb+gn*(0.005+(0.03 if n=='dualmom' else 0.0)*0.2)
    return (r_out-htb/252).dropna(),sb
A,sbA=build10(0.11,0.14); SA=A
oldX=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11X804_BALANCED_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
jj=pd.concat([oldX.rename('o'),SA.rename('n')],axis=1,join='inner').dropna()
print(f"X804 BAL repro max|d|={float((jj.o-jj.n).abs().max()):.3e}")
Sd10=pd.DataFrame({n:vt(sn(p),0.10)[1] for n,p in POOL.items()})
g_all=(Sd10.mean(axis=1)*sbA)  # all-in
print(f"X804: ann {(  (1+SA).prod()**(252/len(SA))-1)*100:.1f}%  all-in gross mean {g_all.reindex(SA.index).mean():.2f}x max {g_all.reindex(SA.index).max():.2f}x")
y=oldX.groupby(oldX.index.year).apply(lambda x:(1+x).prod()-1)
print(f"X804 committed: negyrs {int((y<0).sum())} worst {y.min()*100:.1f}% MDD {(((1+oldX).cumprod()/(1+oldX).cumprod().cummax()-1).min()*100):.2f}%")

# T+1 probe: shift all sleeve inputs +1 day (execute one day later) -> champion should degrade not collapse; and corr structure
def build8_shift(TGT,THR,sh=1):
    V={}
    for n in POOL:
        r=sn(POOL[n]); r2=r.shift(sh)
        v,s=vt(r2,0.08)
        V[n]=v-capW[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4)
    Vn=pd.DataFrame(V)
    W=Sn.div(Sn.sum(axis=1),axis=0).fillna(0)
    blend=Vn.mean(axis=1); blend=blend[blend.index>='2006-10-01']
    tw=((W-W.shift(1)).abs()*0.5).sum(axis=1)
    b=vt(blend,TGT)[0]
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=b.index); b=b*sc; dsc=sc.diff().abs()*0.5
    r_out=b-(tw.reindex(b.index).fillna(0)+dsc.fillna(0))*6e-4
    htb=pd.Series(0.0,index=Sn.index)
    for n in POOL:
        sf=SHORTF[n]
        if sf>0:
            gn=Sn[n]/N*sc*sf; htb=htb+gn*(0.005+(0.03 if n=='dualmom' else 0.0)*0.2)
    return (r_out-htb/252).dropna()
As=build8_shift(0.07,0.04); Bs=build8_shift(0.091,0.03); Bs_=((As+Bs)/2).dropna()
eq=(1+Bs_).cumprod(); m=(1+Bs_).resample('ME').prod()-1
print(f"T+1-lagged execution probe: ann {(eq.iloc[-1]**(252/len(Bs_))-1)*100:.1f}% SR_d {Bs_.mean()/Bs_.std()*np.sqrt(252):.2f} (vs 47.6%/4.18 unlagged)")
