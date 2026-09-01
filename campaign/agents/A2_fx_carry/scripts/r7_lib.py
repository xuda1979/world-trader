"""r7 honest mechanics lib: new FRED FX/macro data (data_fred_new), PIT-safe, T+1, 6bps/side."""
import numpy as np, pandas as pd, os, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
from harness import util as U
from harness.data import save_sleeve

ROOT="/Users/daxu/software/world-trader"
NEW=f"{ROOT}/tools/quant/hedge_fund_strats/data_fred_new"
OLD=f"{ROOT}/tools/quant/hedge_fund_strats/data_fred"
LIB=f"{ROOT}/campaign/results/sleeve_library"

def _csv(path):
    df=pd.read_csv(path,index_col=0,parse_dates=True)
    s=pd.to_numeric(df.iloc[:,0],errors="coerce").replace(0,np.nan).dropna()
    s=s.sort_index(); s.index=pd.DatetimeIndex(s.index)
    return s[~s.index.duplicated(keep="last")]

def new_s(n): return _csv(f"{NEW}/{n}.csv")
def old_s(n): return _csv(f"{OLD}/{n}.csv")

def monthly_to_daily(s, lag_months=1):
    """PIT: monthly value dated M-01 usable at first bday of M+lag (r2b lesson: pub lag)."""
    s=s.copy(); s.index=s.index+pd.DateOffset(months=lag_months)
    idx=pd.bdate_range(s.index.min(), s.index.max())
    return s.reindex(idx).ffill()

# quote conventions: +1 position = long foreign currency vs USD
def load_pair_rets():
    ser={
      "JPY":-new_s("DEXJPUS").pct_change(),      # DEXJPUS = JPY per USD
      "EUR": new_s("DEXUSEU").pct_change(),      # DEXUSEU = USD per EUR
      "GBP": old_s("gbp").pct_change(),          # USD per GBP
      "CAD":-old_s("cad").pct_change(),          # CAD per USD
    }
    return pd.concat(ser,axis=1).sort_index()

def load_ydiff(us2=None):
    """annualized rate diff (foreign10y - US2y) in %, long-fx carry accrual basis; foreign yields monthly w/ 1mo lag."""
    us2 = new_s("DGS2") if us2 is None else us2
    out={
      "JPY":monthly_to_daily(old_s("jp10y"))-us2,
      "EUR":monthly_to_daily(old_s("ez10y"))-us2,
      "GBP":monthly_to_daily(old_s("gb10y"))-us2,
      "CAD":monthly_to_daily(old_s("ca10y"))-us2,
    }
    return pd.concat(out,axis=1).sort_index()

def rebal_anchors(index, rule="M"):
    s=pd.Series(1,index=index)
    a=s.groupby(pd.Grouper(freq={"M":"ME","W":"W-FRI","Q":"QE"}.get(rule,rule))).last().index
    idx=s.index; out=[]
    for d in a:
        sub=idx[idx<=d]
        if len(sub): out.append(sub[-1])
    return sorted(set(out))

def backtest(pos,R,cost_bps=6.0):
    fr=R.shift(-1)
    gross=(pos*fr).sum(axis=1,min_count=1)
    to=pos.diff().abs().sum(axis=1).fillna(0)
    net=gross-to*cost_bps/1e4
    return net, float(to.mean())

def metrics(net,label="",vt=0.10,verbose=True,ret_to=None):
    nv=U.vol_target(net,vt)
    g=U.gates(nv)
    r=nv.dropna()
    sr=r.mean()/r.std()*np.sqrt(252) if r.std()>0 else 0.0
    ann=r.mean()*252; vol=r.std()*np.sqrt(252)
    dd=(1+r).cumprod(); mdd=(dd/dd.cummax()-1).min()
    yr=U.yearly(nv); neg=yr[yr<0]
    ok="PASS" if g["pass_"] else g.get("why","?")
    if verbose:
        print(f"--- {label}: n={len(r)} SR={sr:.2f} ann={ann*100:.1f}% vol={vol*100:.1f}% maxDD={mdd*100:.1f}% negyr={len(neg)} worst={(neg.min()*100 if len(neg) else 0):.1f}% | {ok}")
        print("    yearly:", " ".join(f"{k}:{v*100:+.1f}" for k,v in yr.items()))
    if ret_to is not None: ret_to.append((label,nv,g,sr))
    return nv,g,sr

def scramble_df(pos,R,n=200,seed=7):
    """circular-shift each pair's positions independently; SR on PRE-vt net (r2 lesson)."""
    fr=R.shift(-1)
    def sr_of(P):
        g=(P*fr).sum(axis=1,min_count=1)
        net=g-P.diff().abs().sum(axis=1).fillna(0)*6e-4
        return net.mean()/net.std()*np.sqrt(252) if net.std()>0 else 0.0
    real=sr_of(pos)
    rng=np.random.default_rng(seed); null=[]
    v=pos.values.copy()
    for _ in range(n):
        P2=v.copy()
        for c in range(P2.shape[1]):
            k=int(rng.integers(1,len(P2)))
            P2[:,c]=np.roll(v[:,c],k)
        null.append(sr_of(pd.DataFrame(P2,index=pos.index,columns=pos.columns)))
    return real, float((np.array(null)>=real).mean())

def corr_to_library(nv):
    out={}
    for f in os.listdir(LIB):
        if f.endswith(".csv") and not f.endswith(".meta"):
            d=pd.read_csv(os.path.join(LIB,f),index_col=0,parse_dates=True)["ret"]
            j=pd.concat([nv.rename("a"),d.rename("b")],axis=1).dropna()
            if len(j)>500: out[f[:-4]]=j["a"].corr(j["b"])
    s=pd.Series(out).sort_values()
    return s, float(s.abs().max()) if len(s) else float("nan")

def carry_ls_pos(yd,top=1,bot=1,rule="M"):
    anchors=rebal_anchors(yd.dropna(how="all").index,rule)
    pos=pd.DataFrame(0.0,index=yd.index,columns=yd.columns)
    for i,a in enumerate(anchors):
        nxt=anchors[i+1] if i+1<len(anchors) else yd.index[-1]
        row=yd.loc[a]
        if row.isna().all(): continue
        longs=list(row.nlargest(top).index)
        pos.loc[a:nxt,longs]=1.0/top
        if bot>0:
            shorts=list(row.nsmallest(bot).index)
            pos.loc[a:nxt,shorts]=-1.0/bot
    return pos

def carry_ls_pos_daily(yd,top=1,bot=1):
    pos=pd.DataFrame(0.0,index=yd.index,columns=yd.columns)
    rank=yd.rank(axis=1,ascending=False)
    n=yd.shape[1]
    pos[rank<=top]=1.0/top
    if bot>0: pos[rank>(n-bot)]=-1.0/bot
    return pos

def short_all_pos(yd,rule="M"):
    return -carry_ls_pos(-yd,top=yd.shape[1],bot=0,rule=rule)  # long all (used with -yd) -> here: short all foreign

def tsmom_pos(R,lb,rule="M"):
    mom=R.rolling(lb).sum()
    anchors=rebal_anchors(R.dropna(how="all").index,rule)
    pos=pd.DataFrame(0.0,index=R.index,columns=R.columns)
    for i,a in enumerate(anchors):
        nxt=anchors[i+1] if i+1<len(anchors) else R.index[-1]
        row=mom.loc[a].dropna()
        w=pd.Series(0.0,index=R.columns)
        if len(row): w[row.index]=np.sign(row)/len(row)
        pos.loc[a:nxt,:]=w.values
    return pos

def trend_gate(carry_pos,R,lb=63):
    mom=R.rolling(lb).sum()
    sig=np.sign(carry_pos)
    ok=(np.sign(mom)==sig)
    return carry_pos.where(ok,0.0)

def dollar_z(lb=126):
    exb=new_s("DTWEXBGS")
    m=exb.rolling(lb).mean(); sd=exb.rolling(lb).std()
    return (exb-m)/sd

def dollar_pos(z,cols,dirn=-1,cap=1.5,rule="W",dead=0.0):
    anchors=rebal_anchors(z.dropna().index,rule)
    pos=pd.DataFrame(0.0,index=z.index,columns=cols)
    zz=z.copy(); zz=zz.clip(-cap,cap)*dirn/2.0
    if dead>0: zz=zz.where(zz.abs()>dead,0.0)
    for i,a in enumerate(anchors):
        nxt=anchors[i+1] if i+1<len(anchors) else z.index[-1]
        pos.loc[a:nxt,:]=zz.loc[a]
    return pos
