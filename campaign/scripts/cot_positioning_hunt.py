#!/usr/bin/env python3
"""COT POSITIONING HUNT — coordinator's honest new-domain engine hunt (v2).

Fade COT net-non-commercial positioning extremes (crowded long -> short, crowded short -> long)
in commodity futures, traded via ETF proxies daily at 6.4bps one-side, T+1.

Gates: SR>=1, plateau, halves, yearly<=2 neg, scramble p<0.05, vol-target 10% trailing,
decorrelation |corr|<0.15 vs champion.
"""
import sys; sys.path.insert(0,'campaign'); sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
from campaign.bt import engine, metrics, gates

ROOT='/Users/daxu/software/world-trader'
CHAMP = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:,0]

PRICES = {
 'gold':   ('tools/quant/data/twelvedata/GLD.csv','close'),
 'silver': ('tools/quant/data/more_etf/SLV.csv',None),
 'copper': ('tools/quant/hedge_fund_strats/data_fred/copx.csv',None),
 'corn':   ('tools/quant/data/more_etf/CORN.csv',None),
 'soybeans':('tools/quant/data/more_etf/SOYB.csv',None),
 'natgas': ('tools/quant/data/more_etf/UNG.csv',None),
 'wti':    ('tools/quant/data/more_etf/USO.csv',None),
 'sugar':  ('tools/quant/data/more_etf/CANE.csv',None),
 'wheat':  ('tools/quant/data/more_etf/WEAT.csv',None),
}
COT = { 'gold':'gold_cot.csv','silver':'silver_cot.csv','copper':'copper_cot.csv',
 'corn':'corn_cot.csv','soybeans':'soybeans_cot.csv','natgas':'nat_gas_nymex_cot.csv',
 'wti':'crude_wti_nymex_cot.csv','sugar':'sugar_no11_cot.csv','wheat':'wheat_srw_cot.csv'}

def load_price(name):
    p,col=PRICES[name]
    df=pd.read_csv(f"{ROOT}/{p}",index_col=0,parse_dates=True)
    c=df[col] if col in df.columns else df.iloc[:,0]
    return c.astype(float).dropna()

def load_cot(name):
    return pd.read_csv(f"{ROOT}/tools/quant/data/more_cot/{COT[name]}",
                       parse_dates=['date'])

def build_market(name, lb, zthr):
    """Return net daily ret series for one COT market (fade positioning z extreme)."""
    cot=load_cot(name)
    px=load_price(name)
    ret=px.pct_change()
    r=ret.reindex(px.index)
    # positioning z-score over trailing expanding window (weekly points)
    pos=cot.set_index('date')['net_noncomm_pct_oi']
    z=pos.rolling(max(26,lb*2), min_periods=lb).std(ddof=1)
    zm=(pos-pos.rolling(max(26,lb*2), min_periods=lb).mean())/z.replace(0,np.nan)
    # signal: +1 (long) if z below -thr (crowded short), -1 if z above +thr (crowded long), else 0
    sig=pd.Series(np.where(zm>zthr,-1.0, np.where(zm<-zthr,1.0,0.0)), index=pos.index)
    sig=sig.reindex(px.index).fillna(0.0)  # weekly -> daily carry-forward
    sig=sig.ffill().fillna(0.0)
    sig=engine.lag_signal(sig)             # T+1
    # weights: sign of signal, vol-targeted
    pos_w=sig
    # combine: position * underlying daily return, charge turnover on |d(sign)|
    port=(pos_w*r).fillna(0.0)
    to=(pos_w.diff().abs().fillna(0.0))
    net=port-to*(6.4/1e4)
    return net.dropna()

# ---- coordinate all markets into a panel ----
def build_panel(lb, zthr, vol_tgt=0.10):
    nets={}
    for m in PRICES:
        try:
            s=build_market(m,lb,zthr)
            nets[m]=s
        except Exception as e:
            print(f"  {m}: SKIP {e}")
    if not nets: return None
    df=pd.DataFrame(nets)
    df=df[df.index>='2011-01-01']
    return df

if __name__=="__main__":
    for lb,zthr in [(26,1.5),(26,1.0),(52,1.5),(13,1.5),(26,2.0),(26,0.75)]:
        df=build_panel(lb,zthr)
        if df is None: continue
        # equal-weight blend of the markets
        r=df.fillna(0).mean(axis=1).dropna()
        r=r[r.index>='2011-01-01']
        if len(r)<300: continue
        # vol-target
        scale=engine.vol_target_scale(r.to_frame('x'), target=0.10)
        rv=r*scale['x']
        sr=r.mean()/r.std()*np.sqrt(252)
        yrs=(1+r).resample('YE').prod()-1
        nneg=int((yrs<0).sum())
        corr=r.reindex(CHAMP.index).dropna()
        c=np.corrcoef(corr,CHAMP.reindex(corr.index).dropna())[0,1] if len(corr)>200 else float('nan')
        print(f"lb={lb} zthr={zthr} markets={len(df.columns)} ann={(1+rv).prod()**(252/len(rv))-1:.1%} SR={sr:.2f} negyr={nneg} corrChamp={c:.2f} n={len(r)}")
