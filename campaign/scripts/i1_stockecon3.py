import numpy as np, pandas as pd, os, json
exec(open("/Users/daxu/software/world-trader/campaign/scripts/i1_stockecon.py").read().split("# ---------- portfolio builders")[0].replace('print(f"twelve_big','print(f"twelve_big'))
def run(sigW):
    Wt=sigW.shift(1).fillna(0.0)
    gross=Wt.abs().sum(axis=1); short=(Wt.clip(upper=0)).abs().sum(axis=1)
    dW=Wt.diff().abs().sum(axis=1); dW.iloc[0]=Wt.iloc[0].abs().sum()
    return (Wt*r).sum(axis=1)-(COST*dW+BORROW*short+MARGIN*(gross-1).clip(lower=0))
def xz(df):
    m=df.mean(axis=1); s=df.std(axis=1); return df.sub(m,axis=0).div(s.replace(0,np.nan),axis=0)
def zw(sig):
    z=xz(sig); return z.div(z.abs().sum(axis=1).replace(0,np.nan),axis=0)
ch=pd.read_csv("/Users/daxu/software/world-trader/campaign/results/GOAL100_CHAMPION_daily.csv",parse_dates=["date"]).set_index("date")["ret"]
ess=xz(es)
tests={
 "G_es_smooth5": zw(ess.rolling(5).mean()),
 "H_es_smooth21": zw(ess.rolling(21).mean()),
 "I_es_q10": (ess.rank(axis=1,pct=True)>0.9)*1.0-(ess.rank(axis=1,pct=True)<0.1)*1.0,
 "J_es_skew_rev_signed": zw(-(xz(skew)*0.5)+(ess*1.0)),
 "K_es_vol_scaled": zw(ess),
}
out={}
for nm,s in tests.items():
    net=run(s)
    # K: vol-target 10% ann on trailing 252d (causal, on strategy's own raw ret)
    if nm=="K_es_vol_scaled":
        raw=(s.shift(1).fillna(0.0)*r).sum(axis=1)
        lev=(0.10/raw.rolling(252,min_periods=126).std()*np.sqrt(252)).shift(1).clip(0,3)
        net=run(s.mul(lev,axis=0))
    rr=net.dropna(); n=len(rr)
    ann=(1+rr).prod()**(252/n)-1; sr=rr.mean()/rr.std()*np.sqrt(252)
    dd=((1+rr).cumprod()/(1+rr).cumprod().cummax()-1).min()
    seg23=net.loc["2023":]
    sr23=seg23.mean()/seg23.std()*np.sqrt(252) if len(seg23)>250 else float("nan")
    both=pd.concat([net,ch],axis=1,join="inner").dropna()
    c=float(both.iloc[:,0].corr(both.iloc[:,1]))
    out[nm]=dict(ann=round(float(ann),4),sr=round(float(sr),3),maxdd=round(float(dd),4),sr_2023=round(float(sr23),2),corr=round(c,4))
    print(nm,out[nm])
json.dump(out,open("/Users/daxu/software/world-trader/campaign/agents/I1_stockecon_results/i1_stats_sens.json","w"),indent=1)
print("GATE: SR>=1.5 required. Best found =", max(v["sr"] for v in out.values()), "-> REJECT" if max(v["sr"] for v in out.values())<1.5 else "-> PASS")
