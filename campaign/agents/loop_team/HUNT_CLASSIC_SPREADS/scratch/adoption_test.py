"""Adoption gate 8c — does adding HUNT_CLASSIC_SPREADS sleeves raise champion dAnn
at capital-real (fixed gross 1.6x)? Local replication of the canonical ITER15 max-Sharpe fit
(so the name list can be extended with candidates) — same math, same IS window, same caps.
"""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
from scipy.optimize import minimize
ROOT="/Users/daxu/software/world-trader"
HS=f"{ROOT}/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves"

POOL={
 "brwt10":"campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv",
 "brwt7" :"campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv",
 "brwt5" :"campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv",
 "C5ng"  :"campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsum":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 "A5r2"  :"campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 "a6r7"  :"campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "QAxasts":"campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 "carryv2":"campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
}
NEW={"diescrack":"campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
     "CFX4"     :"campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv"}
BASE_NAMES=list(POOL)+list(NEW)
BASE_PATHS=[f"{ROOT}/{p}" for p in (list(POOL.values())+list(NEW.values()))]
MY=[("crack321","crack_crack321_nyh_L60Z1.5.csv"),
    ("crack211","crack_crack211_nyh_L15Z1.5.csv"),
    ("gascrack","crack_gas_crack_nyh_L30Z1.5.csv"),
    ("gasreg","inter_gasreg_nyh_gulf_L30Z1.0.csv"),
    ("dieseljet","inter_dieseljet_L60Z1.5.csv"),
    ("vixterm","calendar_vixterm_9_3_L20Z1.0.csv")]
GEAR,RATE,BPS,IS_END=1.6,0.045,6.4,pd.Timestamp('2017-01-01')
SHRINK_D=0.98; W_MAX=2.0

def load(p):
    df=pd.read_csv(p,index_col=0); df.index=pd.to_datetime(df.index)
    c='ret' if 'ret' in df.columns else df.columns[0]
    return df[c].astype(float)

def fit_relw(isr,names,shrink_d=SHRINK_D):
    have=[n for n in names if isr[n].notna().sum()>0]
    X=isr[have].dropna()
    mu=(X.mean()*252).values; Sig=X.cov().values*252
    Sig=(1.0-shrink_d)*Sig+shrink_d*np.diag(np.diag(Sig))
    k=len(have); sd=np.sqrt(np.diag(Sig)); cap=W_MAX/k
    def neg_sharpe(w):
        v=float(np.sqrt(w@Sig@w)); return -(float(w@mu))/v if v>1e-14 else 0.0
    cons=[{"type":"eq","fun":lambda w:w.sum()-1.0}]
    def solve(bounds):
        best=None
        for w0 in (np.full(k,1.0/k), np.maximum(mu,0.0)/max(float(np.maximum(mu,0.0).sum()),1e-12),
                   (1.0/sd)/(1.0/sd).sum()):
            r=minimize(neg_sharpe,w0,method="SLSQP",bounds=bounds,constraints=cons,
                       options={"maxiter":800,"ftol":1e-12})
            if r.success and (best is None or r.fun<best.fun): best=r
        return best
    best=solve([(0.0,W_MAX)]*k)
    if best is not None and float(best.x.max())>cap+1e-9: best=solve([(0.0,cap)]*k)
    relw=pd.Series(0.0,index=names); relw[have]=best.x
    return relw

def run(names,paths):
    df=pd.DataFrame({n:load(p).dropna() for n,p in zip(names,paths)})
    df=df[df.index>='2008-03-31']
    isr=df[df.index<IS_END]
    relw=fit_relw(isr,names)
    nav=(1+df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2=nav.div(nav.mean(axis=1),axis=0).mul(relw,axis=1)
    d2=d2.div(d2.sum(axis=1),axis=0)*len(names)
    Wg=d2*(GEAR/len(names))
    port=(df.fillna(0).values*Wg.values).sum(axis=1)
    to=Wg.diff().abs().sum(axis=1).fillna(0)
    net=pd.Series(port,index=df.index)-to*BPS/1e4-np.maximum(GEAR-1,0)*RATE/252
    s=net.dropna(); eq=(1+s).cumprod()
    ann=eq.iloc[-1]**(252/len(s))-1 if eq.iloc[-1]>0 else np.nan
    sr=s.mean()/s.std()*np.sqrt(252)
    yr=s.groupby(s.index.year).apply(lambda x:(1+x).prod()-1)
    return ann,sr,(eq/eq.cummax()-1).min(),int((yr<0).sum()),relw

ann0,sr0,mdd0,neg0,relw0=run(BASE_NAMES,BASE_PATHS)
print(f"INCUMBENT: ann={ann0*100:.3f}% SR={sr0:.4f} MDD={mdd0*100:.2f}% neg={neg0} (expect 39.500/3.2176/-6.52/0)")
print(f"  top weights: {sorted([(n,round(float(relw0[n]),4)) for n in BASE_NAMES],key=lambda x:-x[1])[:3]}")
print(f"  energy-family total (brwt5/7/10): {float(relw0['brwt5']+relw0['brwt7']+relw0['brwt10'])*100:.1f}% of book")
for cname,csv in MY:
    cpath=f"{HS}/{csv}"
    try:
        ann,sr,mdd,neg,relw=run(BASE_NAMES+[cname],BASE_PATHS+[cpath])
        dAnn=(ann-ann0)*100
        ci=load(cpath); cisr=ci[ci.index<IS_END].dropna()
        isr_c=cisr.mean()/cisr.std()*np.sqrt(252) if len(cisr)>200 and cisr.std()>0 else 0
        # energy weight after adding
        en=float(relw['brwt5']+relw['brwt7']+relw['brwt10'])
        print(f"+{cname:9s}: ann={ann*100:6.3f}%  dAnn={dAnn:+6.3f}pp  SR={sr:.4f}  MDD={mdd*100:6.2f}%  "
              f"neg={neg}  w={float(relw[cname]):.4f}  IS_SR={isr_c:.2f}  | brwt-total {en*100:.1f}%")
    except Exception as e:
        print(f"+{cname:9s}: ERR {type(e).__name__} {str(e)[:70]}")
