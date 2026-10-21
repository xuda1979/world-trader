import numpy as np, pandas as pd, os, json
exec(open("/Users/daxu/software/world-trader/campaign/scripts/i1_stockecon.py").read().split("# ---------- portfolio builders")[0].replace('print(f"twelve_big','print(f"twelve_big'))

def run(sigW):
    Wt=sigW.shift(1).fillna(0.0)
    gross=Wt.abs().sum(axis=1); short=(Wt.clip(upper=0)).abs().sum(axis=1)
    dW=Wt.diff().abs().sum(axis=1); dW.iloc[0]=Wt.iloc[0].abs().sum()
    port=(Wt*r).sum(axis=1)
    net=port-(COST*dW+BORROW*short+MARGIN*(gross-1).clip(lower=0))
    return net,dW

def xz(df):
    m=df.mean(axis=1); s=df.std(axis=1)
    return df.sub(m,axis=0).div(s.replace(0,np.nan),axis=0)

def zweights(sig):
    z=xz(sig); g=z.abs().sum(axis=1).replace(0,np.nan)
    return z.div(g,axis=0)

def stats(rr,label):
    rr=rr.dropna(); n=len(rr)
    ann=(1+rr).prod()**(252/n)-1; sr=rr.mean()/rr.std()*np.sqrt(252)
    dd=((1+rr).cumprod()/(1+rr).cumprod().cummax()-1).min()
    return dict(label=label,n=n,ann=round(float(ann),4),sr=round(float(sr),3),maxdd=round(float(dd),4))

# components and reversed signs
sks=xz(skew); ess=xz(es)
variants={
 "D_rev_combined": -(sks-ess),      # short lottery: low skew, high tail loss
 "E_rev_skewonly": -(sks),          # short high-skew only
 "F_rev_esonly":   +(ess),          # long high tail-loss only (crash-prone long)
}
res={}
for nm,s in variants.items():
    W_=zweights(s); net,_=run(W_)
    st=stats(net,nm); res[nm]=st
    # subperiods
    for a,b in [("2007","2013"),("2013","2019"),("2019","2023"),("2023","2027")]:
        seg=net.loc[a:b]; st[f"sr_{a[:4]}"]=round(float(stats(seg,seg.index[0].date())[ 'sr']),2) if len(seg)>250 else None
    res[nm]=st; print(nm, st)
# champion corr for D and E
ch=pd.read_csv("/Users/daxu/software/world-trader/campaign/results/GOAL100_CHAMPION_daily.csv",parse_dates=["date"]).set_index("date")["ret"]
for nm in variants:
    s=variants[nm]; W_=zweights(s); net,_=run(W_)
    both=pd.concat([net,ch],axis=1,join="inner").dropna()
    res[nm]["champ_corr"]=round(float(both.iloc[:,0].corr(both.iloc[:,1])),4)
    print(nm,"corr",res[nm]["champ_corr"])
json.dump(res,open("/Users/daxu/software/world-trader/campaign/agents/I1_stockecon_results/i1_stats_flip.json","w"),indent=1)
