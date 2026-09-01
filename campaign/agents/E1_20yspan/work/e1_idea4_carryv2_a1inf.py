"""E1 idea4: de-truncate carryv2 (GLD from twelvedata 2006-09 for xau; brent floor 2000; NO 2008 cut)
and A1inf (GLD for xau; floor 2006-10). Frozen params; disclose floor-driven changes."""
import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
from campaign.harness.data import fred, save_sleeve
from campaign.agents.B2_highfreq.gates import vol_target, full_stats, halves_sr

ROOT="/Users/daxu/software/world-trader"
COST=6.0
BLEND=pd.read_csv(f'{ROOT}/campaign/results/GOAL100_CHAMPION20Y_BALANCED_daily.csv',index_col=0,parse_dates=True).iloc[:,0]

def bd(s):
    s=s.astype(float).dropna(); s=s[~s.index.duplicated(keep="last")].sort_index()
    return s.reindex(pd.bdate_range(s.index[0], s.index[-1])).ffill()

GLD=pd.read_csv(f"{ROOT}/tools/quant/data/twelvedata/GLD.csv",index_col=0,parse_dates=True)["close"].dropna()
GLD.index=pd.to_datetime(GLD.index)

# ================= carryv2 rebuild =================
P={"natgas":bd(fred("natgas")),"xau":bd(GLD)}
R={k:v.pct_change() for k,v in P.items()}
wti,br=bd(fred("wti_full")),bd(fred("brent"))
idx=wti.index; w=wti.reindex(idx); b=br.reindex(idx)
valid=w.notna()&b.notna(); w=w.where(valid).ffill(); b=b.where(valid).ffill()
bad=((w<5)|(b<5)).fillna(True)
spr=(w-b).mask(bad)
z=(spr-spr.rolling(126).mean())/spr.rolling(126).std()
tb=bd(fred("tbill3m")).resample("D").ffill()
def vtclip(x,tgt,cap):
    v=x.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
    return (x*(tgt/v).clip(0,cap)).fillna(0)
psp=np.sign(-z).where(z.abs()>1.0,np.nan)
psp=psp.where(z.abs()>0.75,0).ffill().fillna(0).shift(1).fillna(0)
bm=bad|bad.shift(1).fillna(True)
psp=psp.where(~bm,0.0)
fwd=(spr.diff()/w).shift(-1)
n1=psp*fwd-psp.diff().abs().fillna(0)*2*COST/1e4
n1=vtclip(n1,0.10,3.0)     # NO truncation
p2,r2=P["natgas"],R["natgas"]
sig2=pd.Series(0.0,index=p2.index); sig2[p2.index.month.isin([11,12,1,2])]=1.0
vol2=r2.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
w2=(sig2*(0.10/vol2).clip(upper=1.0)).replace([np.inf,-np.inf],0.0).fillna(0.0)
rf=(tb.reindex(r2.index).ffill().fillna(0)/100.0/252.0)
n2=((w2.shift(1)*r2).fillna(0)+(1-w2.shift(1).clip(0,1))*rf-w2.diff().abs().fillna(0)*COST/1e4)
p3,r3=P["xau"],R["xau"]
sig3=(p3/p3.shift(252)-1>0).astype(float)*(p3/p3.shift(84)-1>0).astype(float)
vol3=r3.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
w3=(sig3*(0.10/vol3).clip(upper=1.0)).replace([np.inf,-np.inf],0.0).fillna(0.0)
n3=((w3.shift(1)*r3).fillna(0)+(1-w3.shift(1).clip(0,1))*rf-w3.diff().abs().fillna(0)*COST/1e4)
jj=pd.concat([n1,n2,n3],axis=1).sort_index().dropna()
m=jj.mean(axis=1)
rv=m.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
sleeve=(m*(0.08/rv).clip(0,3)).fillna(0)
e=sleeve[sleeve.index>='2007-06-01']   # 252d trend warmup from 2006-09 -> signal from ~2007-09
st=full_stats(e); h1,h2=halves_sr(e); pv,_=__import__('campaign.agents.B2_highfreq.gates',fromlist=['scramble_pval']).scramble_pval(e,200)
a,bb=e.align(BLEND,join='inner'); c=a.corr(bb)
print(f"== carryv2GLD (eval 2007-06+): SR={st['sr']:.2f} ann={st['ann']:.1f}% MDD={st['mdd']:.1f}% negy={st['negy']}/{st['years']} worst={st['worst']:.1f}% H1={h1:.2f} H2={h2:.2f} corr_blend={c:.3f}")
print(f"   yearly={st['yearly']}")
ov=pd.read_csv(f"{ROOT}/campaign/agents/A1_trend_cta/sleeves/A1_carry_seasonal_v2.csv",index_col=0,parse_dates=True).iloc[:,0]
j=pd.concat([sleeve.rename('new'),ov.rename('old')],axis=1,join='inner').dropna()
print(f"   overlap corr vs orig = {j.corr().iloc[0,1]:.4f} n={len(j)}")

# ================= A1inf rebuild with GLD =================
L,THR,VT,CAP=126,0.5,0.10,2.0
xau,slv,wti2=bd(GLD),bd(fred("slv")),bd(fred("wti"))
cop_raw=fred("copper_monthly").astype(float).dropna()
cop=cop_raw.copy(); cop.index=cop.index+pd.offsets.MonthBegin(1)
cop=cop[~cop.index.duplicated(keep="last")]
cop=cop.reindex(pd.bdate_range(cop.index[0],cop.index[-1])).ffill()
PX=pd.DataFrame({"xau":xau,"slv":slv,"wti":wti2,"cop":cop}).dropna().ffill()
tb=bd(fred("tbill3m")); rf2=(tb.reindex(PX.index).ffill()/100/252).fillna(0.0)
rets=PX.pct_change().mean(axis=1)
trends=pd.concat([(PX[mm]/PX[mm].shift(L)-1) for mm in PX.columns],axis=1)
sig=(((trends>0).mean(axis=1))>THR).astype(float)
ex=(sig*rets-rf2).fillna(0)
v=ex.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
lev=(VT/v).clip(0,CAP).fillna(0)
net2=lev.shift(1)*ex-lev.diff().abs().shift(1).fillna(0)*COST/1e4+rf2
e2=net2.dropna()
st2=full_stats(e2); h12,h22=halves_sr(e2); pv2,_=__import__('campaign.agents.B2_highfreq.gates',fromlist=['scramble_pval']).scramble_pval(e2,200)
a2,b2=e2.align(BLEND,join='inner'); c2=a2.corr(b2)
print(f"== A1infGLD (full, floor 2006-10): SR={st2['sr']:.2f} ann={st2['ann']:.1f}% MDD={st2['mdd']:.1f}% negy={st2['negy']}/{st2['years']} worst={st2['worst']:.1f}% H1={h12:.2f} H2={h22:.2f} corr_blend={c2:.3f} start={e2.index.min().date()}")
print(f"   yearly={st2['yearly']}")
ov2=pd.read_csv(f"{ROOT}/campaign/agents/A1_trend_cta/sleeves/A1_infl_breadth_mom.csv",index_col=0,parse_dates=True).iloc[:,0]
j2=pd.concat([net2.dropna().rename('new'),ov2.rename('old')],axis=1,join='inner').dropna()
print(f"   overlap corr vs orig = {j2.corr().iloc[0,1]:.4f} n={len(j2)}")
save_sleeve(sleeve,f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
"E1 carryv2 de-truncated: A1_carry_seasonal_v2 frozen construction with xau->GLD(twelvedata 2006-09) and no 2008 cut; brent floor 2000-01. Eval 2007-06+.")
save_sleeve(net2.dropna(),f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_A1inf_GLD_2006.csv",
"E1 A1_infl_breadth_mom de-truncated: frozen construction with xau->GLD(twelvedata 2006-09), floor 2006-10 (was 2008-01 FRED xau floor). 126d breadth>0.5 -> EW energy/metals basket long-or-cash, T+1, 6bps, vt10 cap2.")
