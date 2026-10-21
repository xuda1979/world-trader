"""K1 FAT-TAIL TREND (agent K1_tai_trend).
(a) trend sign(12-1 mom) x inverse tail-kurtosis (rolling 252d excess kurt) on CORN+QQQ.
(b) short-variance harvest gated by VIX regime (contango VIX3M>VIX, or VIX<thr), T+1 delta.
T+1 causal, no lookahead. Cost stack: 6bps per FULL one-side |dW| + 4.5%/yr margin on (gross-1)
+ 0.5%/yr borrow on short notional. Offline only."""
import numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"; D=f"{ROOT}/tools/quant/data"
COST=0.0006; MARG=0.045; BORR=0.005

def px(f,col="close"):
    s=pd.read_csv(f,parse_dates=["date"],index_col="date")[col]
    return s[~s.index.duplicated(keep="last")].sort_index()

def stats(r,name=""):
    r=r.dropna()
    if len(r)<100: return dict(name=name,n=len(r),ann=np.nan,sr=np.nan,mdd=np.nan,start="",end="")
    n=len(r); ann=(1+r).prod()**(252/n)-1
    sr=r.mean()/r.std()*np.sqrt(252) if r.std()>0 else np.nan
    dd=(1+r).cumprod(); mdd=(dd/dd.cummax()-1).min()
    return dict(name=name,n=n,start=r.index[0].date(),end=r.index[-1].date(),ann=ann,sr=sr,mdd=mdd)

def halves(r):
    r=r.dropna(); h=len(r)//2
    return stats(r.iloc[:h])["sr"],stats(r.iloc[h:])["sr"]

def yearly(r):
    r=r.dropna(); y=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1); neg=y[y<0]
    return len(neg),neg.round(3).to_dict()

def show(tag,r):
    s=stats(r,tag); h1,h2=halves(r); ny,nd=yearly(r)
    print(f"{tag:26s} n={s['n']:5d} {str(s['start'])}..{str(s['end'])} ann={s['ann']: .4f} SR={s['sr']: .2f} MaxDD={s['mdd']: .4f} halves=({h1: .2f},{h2: .2f}) negYr={ny} {nd}")
    return s

# ---------------- data ----------------
corn=px(f"{D}/more_etf/CORN.csv"); qqq=px(f"{D}/more_etf/QQQ.csv")
vix=px(f"{D}/more_vol/VIX.csv"); vix3m=px(f"{D}/more_vol/VIX3M.csv"); spy=px(f"{D}/twelve_big/SPY.csv")
rq=np.log(qqq).diff(); rc=np.log(corn).diff(); rs=np.log(spy).diff()
ch=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_CHAMPION_daily.csv",parse_dates=["date"],index_col="date")["ret"]
ch16=1.6*ch-0.0045*0.6/252

# ============ SLEEVE A ============
def sleeveA(df,look=252,skip=21,kw=252,target=None,plain=False):
    Z={}
    for k in ["rc","rq"]:
        p=(1+df[k]).cumprod(); mom=p.shift(skip)/p.shift(look)-1
        z=np.sign(mom) if plain else np.sign(mom)/(1+df[k].rolling(kw).kurt().clip(lower=0))
        Z[k]=z
    Z=pd.DataFrame(Z).dropna()
    W=Z.div(Z.abs().sum(axis=1),axis=0).replace([np.inf,-np.inf],np.nan).ffill().dropna()
    Wx=W.shift(1).dropna()                          # T+1 execution
    R=df.loc[Wx.index,["rc","rq"]]; base=(Wx*R).sum(axis=1)
    if target is not None:
        lev=(target/base.rolling(60,min_periods=60).std()*np.sqrt(252)).shift(1).clip(0,2).fillna(0)
        Wx2=Wx.mul(lev,axis=0)
        tc=COST*Wx2.abs().diff().abs().sum(axis=1).fillna(0)
        r=base*lev-tc-MARG*(lev-1).clip(lower=0)/252-BORR*Wx2.clip(upper=0).abs().sum(axis=1)/252
        return r.dropna(),Wx2,R
    tc=COST*Wx.abs().diff().abs().sum(axis=1).fillna(0)
    r=base-tc-BORR*Wx.clip(upper=0).abs().sum(axis=1)/252
    return r.dropna(),Wx,R

def scrambleA(r_net,Wx,R,nperm=200,seed=7):
    rng=np.random.default_rng(seed); out=[]
    for _ in range(nperm):
        Wp=Wx.sample(frac=1,random_state=int(rng.integers(1e9))); Wp.index=Wx.index
        tc=COST*Wp.abs().diff().abs().sum(axis=1).fillna(0)
        s=((Wp*R).sum(axis=1)-tc-BORR*Wp.clip(upper=0).abs().sum(axis=1)/252).dropna()
        out.append(s.mean()/s.std()*np.sqrt(252))
    return np.nanpercentile(out,95)

dfA=pd.DataFrame({"rc":rc,"rq":rq}).dropna()
rA,WxA,RA=sleeveA(dfA); rAvt,_,_=sleeveA(dfA,target=0.10); rApl,_,_=sleeveA(dfA,plain=True)
rA126,_,_=sleeveA(dfA,kw=126); rA378,_,_=sleeveA(dfA,kw=378); rA9,_,_=sleeveA(dfA,look=189); rA6,_,_=sleeveA(dfA,look=126)
print("=== SLEEVE A: trend x inv-tail-kurt (CORN+QQQ), net of 6bps+borrow ===")
show("A_mom12-1_kurt252",rA); show("A_vt10",rAvt); show("A_plain_trend",rApl)
show("A_kurt126",rA126); show("A_kurt378",rA378); show("A_mom9",rA9); show("A_mom6",rA6)
iA=rA.index.intersection(ch.index)
print(f"corr(A,champ)={rA.reindex(iA).corr(ch.reindex(iA)): .3f}  corr(Avt,champ)={rAvt.reindex(iA).corr(ch.reindex(iA)): .3f}  corr(Apl,champ)={rApl.reindex(iA).corr(ch.reindex(iA)): .3f}")
sc95=scrambleA(rA,WxA,RA)
sA=stats(rA)
print(f"scramble: real SR={sA['sr']:.3f} vs scrambled 95th={sc95:.3f} -> {'PASS' if sA['sr']>sc95 else 'FAIL'}")

# ============ SLEEVE B: short-variance harvest, VIX regime gate ============
def sleeveB(rv,mode="contango",vthr=25.0,target=None,cap=1.0,vt=0.10):
    iv2=(vix/100.0)**2/252.0
    if mode=="contango": g=(vix3m.reindex(iv2.index).ffill()>vix).astype(float)
    else: g=(vix<vthr).astype(float)
    idx=rv.index.intersection(g.dropna().index)
    g=g.reindex(idx).fillna(0.0); iv2=iv2.reindex(idx).ffill()
    iv_leg=(g*iv2).shift(1)                         # position fixed at t-1 close; IV accrual for day t
    pnl=iv_leg-rv**2                                # realized leg over (t-1,t]
    w=g.shift(1)                                    # executed weight (gross=|w|), decided t-1
    if target is not None:
        lev=(vt/(pnl.rolling(60,min_periods=60).std()*np.sqrt(252))).shift(1).clip(0,cap).fillna(0)
        w=lev
    tc=COST*w.diff().abs().fillna(0)
    bc=BORR*w.abs()/252                             # borrow on short exposure (conservative)
    mc=MARG*(w-1).clip(lower=0)/252                 # margin if gross>1
    r=(w*pnl-tc-bc-mc).dropna()
    return r,w.reindex(r.index),pnl.reindex(r.index)

print("=== SLEEVE B: short-variance harvest (w<=1 unit notional), net of 6bps+borrow+margin ===")
rB1,_,_=sleeveB(rq,"contango");                       show("B_qqq_contango",rB1)
rB2,_,_=sleeveB(rq,"thr");                            show("B_qqq_vix<25",rB2)
rB3,_,_=sleeveB(rs,"contango");                       show("B_spy_contango(ctrl)",rB3)
rB4,_,_=sleeveB(rs,"thr");                            show("B_spy_vix<25(ctrl)",rB4)
rB5,_,_=sleeveB(rq,"contango",target=0.02,cap=1.0);   show("B_qqq_cont_vt2",rB5)
rB6,_,_=sleeveB(rq,"contango",target=0.10,cap=10.0);  show("B_qqq_cont_vt10_cap10",rB6)
iB=rB1.index.intersection(ch.index); iB4=rB4.index.intersection(ch.index)
print(f"corr(B_qqq_cont,champ)={rB1.reindex(iB).corr(ch.reindex(iB)): .3f}  corr(B_qqq_thr,champ)={rB2.reindex(iB).corr(ch.reindex(iB)): .3f}  corr(B_spy_thr,champ)={rB4.reindex(iB4).corr(ch.reindex(iB4)): .3f}")
for tg,rr in [("B_qqq_cont",rB1),("B_qqq_thr",rB2),("B_spy_thr",rB4)]:
    rr=rr.dropna(); print(f"{tg}: worstDay={rr.min(): .4f} skew={rr.skew(): .2f} xkurt={rr.kurt(): .1f} p1={rr.quantile(0.01): .4f}")

# ============ COMBOS + CHAMPION ============
print("=== COMBOS / CHAMPION ===")
ic=rA.index.intersection(rB1.index)
rAB=0.5*rA.reindex(ic).fillna(0)+0.5*rB1.reindex(ic).fillna(0)
show("AB_5050",rAB); print(f"corr(AB_5050,champ)={rAB.reindex(ic).corr(ch.reindex(ic)): .3f}")
show("CHAMPION_1x",ch); show("CHAMPION_1.6x",ch16)

# ============ GATE EVAL (SR>=1.5, corr<0.5, halves>=0.3 both, <=2 negYr >-5%, scramble, worstDay>-20%) ============
print("=== GATES ===")
cand=[("A_mom12-1_kurt252",rA),("A_vt10",rAvt),("B_qqq_cont",rB1),("B_qqq_vix<25",rB2),("B_spy_vix<25",rB4),("AB_5050",rAB)]
for tg,rr in cand:
    s=stats(rr); h1,h2=halves(rr); ny,nd=yearly(rr)
    ii=rr.index.intersection(ch.index); co=rr.reindex(ii).corr(ch.reindex(ii))
    wd=rr.min()
    ok_sr = s["sr"]>=1.5; ok_co = co<0.5; ok_h = (h1>=0.3)and(h2>=0.3)
    ok_y = (ny<=2) and all(v>-0.05 for v in nd.values()); ok_wd = wd>-0.20
    print(f"{tg:24s} SR={s['sr']: .2f}(>=1.5:{ok_sr}) corr={co: .2f}(<0.5:{ok_co}) halvesOK={ok_h} negYrOK={ok_y} worstDay={wd: .4f}(OK:{ok_wd})")
