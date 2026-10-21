"""I1_stockecon: DIRECTION 5 cross-sectional stock tail L/S.
Long high-skew / low-ES95-loss (stable), short low-skew / high-ES95-loss (crash-prone).
T+1 causal. Costs: 6bps/full |dW| + 0.5%/yr borrow on shorts + 4.5%/yr margin on (gross-1).
Universe: twelve_big (299 large caps) ∩ spy_holdings snapshot (survivorship disclosed).
"""
import numpy as np, pandas as pd, os, json

ROOT="/Users/daxu/software/world-trader"
BIG=f"{ROOT}/tools/quant/data/twelve_big"
CHAMP=f"{ROOT}/campaign/results/GOAL100_CHAMPION_daily.csv"
OUT=f"{ROOT}/campaign/agents/I1_stockecon_results"
COST=0.0006; BORROW=0.005/252; MARGIN=0.045/252

# ---------- universe ----------
hold=pd.read_csv(f"{ROOT}/tools/quant/data/spy_holdings/spy_holdings.csv")
spy_tickers=set(hold["ticker"].astype(str))
files=[f for f in os.listdir(BIG) if f.endswith(".csv")]
tickers=[f[:-4] for f in files]
univ=[t for t in tickers if t in spy_tickers]
dropped=[t for t in tickers if t not in spy_tickers]
print(f"twelve_big tickers={len(tickers)} spy_holdings={len(spy_tickers)} universe(intersection)={len(univ)} dropped_nonSPX={len(dropped)}")

# ---------- load closes ----------
closes={}
for t in univ:
    df=pd.read_csv(f"{BIG}/{t}.csv",parse_dates=["date"]).set_index("date")["close"]
    closes[t]=df
px=pd.DataFrame(closes).sort_index()
px=px[~px.index.duplicated(keep="first")]
px=px.loc["2007-01-01":]
print(f"px panel {px.shape}, {px.index[0].date()}..{px.index[-1].date()}")
r=px.pct_change()
n_names=px.notna().sum(axis=1)

# ---------- signals (causal, rolling 60d incl. day t; applied T+1) ----------
W=60
skew=r.rolling(W,min_periods=W).skew()
def es95_loss(x):  # positive = worse tail (magnitude of mean of worst 5% returns)
    q=np.quantile(x,0.05); return float(-x[x<=q].mean())
es=r.rolling(W,min_periods=W).apply(es95_loss,raw=True)

def xz(df):
    m=df.mean(axis=1); s=df.std(axis=1)
    return df.sub(m,axis=0).div(s.replace(0,np.nan),axis=0)
sig=xz(skew)-xz(es)   # + = high skew & small tail loss (stable) -> long
sig[n_names<100]=np.nan  # fail-closed breadth floor: no trade before 100 names have data
print(f"signal coverage: first valid {sig.notna().any(axis=1).idxmax().date()}, mean names/day {sig.notna().sum(axis=1).mean():.0f}")

# ---------- portfolio builders ----------
def run(sigW, name):
    """sigW: target gross-normalized weights at close t (sum|.|=gross). T+1 shift inside."""
    Wt=sigW.shift(1).fillna(0.0)                 # T+1 causal application
    gross=Wt.abs().sum(axis=1)
    port=(Wt.shift(0)*0).iloc[:,0] if False else (Wt*r).sum(axis=1)  # close-to-close ret t
    # note: Wt already shifted; r is day-t close-to-close -> causal
    dW=Wt.diff().abs().sum(axis=1); dW.iloc[0]=Wt.iloc[0].abs().sum()
    short=(Wt.clip(upper=0)).abs().sum(axis=1)
    cost=COST*dW + BORROW*short + MARGIN*(gross-1).clip(lower=0)
    net=port-cost
    return net.rename(name), pd.DataFrame({"gross":gross,"short_not":short,"turn":dW})

def zweights(sig, top=None):
    """gross-1 dollar-neutral z-weights (variant A) or 20% quantile book (variant B)."""
    if top is None:
        z=xz(sig)
        g=z.abs().sum(axis=1).replace(0,np.nan)
        return z.div(g,axis=0)
    q_hi=sig.quantile(0.8,axis=1); q_lo=sig.quantile(0.2,axis=1)
    W_=pd.DataFrame(0.0,index=sig.index,columns=sig.columns)
    W_=W_.mask(sig.ge(q_hi,axis=0),1.0).mask(sig.le(q_lo,axis=0),-1.0)
    W_=W_.where(sig.notna(),0.0)
    nz=(W_!=0).sum(axis=1).replace(0,np.nan)
    W_=W_.mul(0.5/nz,axis=0)   # 0.5 per side -> gross 1
    return W_

def stats(rr, label):
    rr=rr.dropna()
    ann=(1+rr).prod()**(252/len(rr))-1
    sr=rr.mean()/rr.std()*np.sqrt(252)
    dd=((1+rr).cumprod()/(1+rr).cumprod().cummax()-1).min()
    vd=rr.std()*np.sqrt(252)
    print(f"{label}: n={len(rr)} ann={ann:+.4f} vol={vd:.4f} SR={sr:.3f} MaxDD={dd:+.4f}")
    return dict(label=label,n=len(rr),ann=round(ann,4),sr=round(sr,3),maxdd=round(dd,4),vol=round(vd,4))

res={}; dfs={}
Wz=zweights(sig); netA,infoA=run(Wz,"A_z_daily");  res["A"]=stats(netA,"A z-weight daily gross1"); dfs["A"]=(netA,infoA)
Wq=zweights(sig,top=0.2); netB,infoB=run(Wq,"B_q20_daily"); res["B"]=stats(netB,"B q20% daily gross1"); dfs["B"]=(netB,infoB)
# variant C: weekly rebalance z-weight (turnover cut) - sensitivity
Wz5=Wz.copy(); idx5=Wz.index[::5]
mask5=pd.Series(False,index=Wz.index); mask5[idx5]=True
Wz5[~mask5]=np.nan; Wz5=Wz5.ffill().fillna(0.0)
netC,infoC=run(Wz5,"C_z_weekly"); res["C"]=stats(netC,"C z-weight weekly gross1"); dfs["C"]=(netC,infoC)

# champion correlation on overlap
ch=pd.read_csv(CHAMP,parse_dates=["date"]).set_index("date")["ret"]
print("\n--- champion corr (overlap daily rets) ---")
for k,(net,info) in dfs.items():
    both=pd.concat([net,ch],axis=1,join="inner").dropna()
    c=both.iloc[:,0].corr(both.iloc[:,1])
    res[k]["champ_corr"]=round(float(c),4); res[k]["overlap_n"]=len(both)
    print(f"{k}: corr={c:.4f} n={len(both)}")
    # champion stats on same window for context
    cb=both.iloc[:,1]
    ann=(1+cb).prod()**(252/len(cb))-1; sr=cb.mean()/cb.std()*np.sqrt(252)
    if k=="A": print(f"  [champion in-window: ann={ann:+.4f} SR={sr:.2f}]")

# cost diagnostics (pre-cost SR sanity for variant A)
prA=((Wz.shift(1).fillna(0.0)*r).sum(axis=1))
print(f"\nA pre-cost: SR={prA.dropna().mean()/prA.dropna().std()*np.sqrt(252):.3f}; "
      f"mean gross={infoA['gross'].mean():.3f} short={infoA['short_not'].mean():.3f} "
      f"turn/day={infoA['turn'].mean():.4f} (={infoA['turn'].mean()*252:.1f}/yr), "
      f"cost drag={ (COST*infoA['turn']).mean()*252:.4f}/yr")
json.dump(res,open(f"{OUT}/i1_stats.json","w"),indent=1)
dfs["A"][0].to_frame("ret").to_csv(f"{OUT}/i1_retA.csv")
