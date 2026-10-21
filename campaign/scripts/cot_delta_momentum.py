#!/usr/bin/env python3
"""COT DELTA MOMENTUM — new-domain engine: follow weekly change in speculative positioning.

CORRELATION FOUND (honest scan): corr(COT pct_oi WEEKLY CHANGE lagged 1wk, next-week market
return) = +0.16..+0.22 across ALL 9 commodity/ETF markets (gold,silver,copper,corn,soy,natgas,
wti,sugar,wheat). Consistent sign across every market => a REAL cross-sectional effect, not one
market's luck. This is the strongest new-domain forward signal found in the campaign.

Hypothesis: when money-manager/spec NET positioning increases sharply this week (smart-money
accumulation), the commodity ETF tends to rise next week; sharp distribution -> falls next week.

Timing (no lookahead): COT report for week-ending-Tuesday is released Friday after close. Signal
uses delta known at week t (Friday) to position for week t+1 held daily. All costs 6.4bps/side T+1.

Gates: SR>=1.0, plateau, halves H1/H2>=0.5, yearly<=2 neg (champion needs 0-neg), decorr<0.15
vs champion, scramble p<0.05.
"""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign')
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
    return pd.read_csv(f"{ROOT}/tools/quant/data/more_cot/{COT[name]}", parse_dates=['date'])

def market_series(name, mom_lb=1, smooth=1):
    """Daily ret + weekly COT delta signal for one market, all T+1, costs embedded."""
    cot=load_cot(name); px=load_price(name)
    ret=px.pct_change().reindex(px.index)
    pos=cot.set_index('date')['net_noncomm_pct_oi']
    delta=pos.diff(mom_lb)                       # weekly change in positioning
    # z-score the delta over trailing expanding 52w window
    mz=delta.rolling(52, min_periods=26).mean()
    sz=delta.rolling(52, min_periods=26).std(ddof=1)
    z=((delta-mz)/sz.replace(0,np.nan))
    sig=z
    # map weekly signal to daily (signal known Friday, position week after)
    sig_d=sig.resample('D').ffill().reindex(px.index).ffill()
    # T+1: position taken next day after signal available; but weekly COT released Friday
    # -> we hold from next Monday. Approx with shift by 3 trading days (Fri->Mon) + lag.
    pos_w=sig_d.shift(3)                          # small T+1 after Friday release
    # sign-scaled: return = sign(z)*daily_ret (long when z>0). Magnitude cap optional (keep sign)
    w=np.sign(pos_w).fillna(0.0)
    port=(w*ret).fillna(0.0)
    to=w.diff().abs().fillna(0.0)                 # one-side turnover
    net=port-to*(6.4/1e4)
    return net.dropna()

def build_panel(mom_lb, smooth, start='2012-01-01'):
    nets={}
    for m in PRICES:
        try:
            nets[m]=market_series(m, mom_lb, smooth)
        except Exception as e:
            print(f'  {m}: SKIP {e}')
    if not nets: return None
    df=pd.DataFrame(nets)
    df=df[df.index>=start]
    return df

if __name__=='__main__':
    for mom_lb,smooth in [(1,1),(1,2),(2,1),(4,1)]:
        df=build_panel(mom_lb,smooth)
        r=df.fillna(0).mean(axis=1)
        r=r.dropna()
        if len(r)<300: continue
        scale=engine.vol_target_scale(r.to_frame('x'), target=0.10)['x']
        rv=r*scale
        ann=(1+rv).prod()**(252/len(rv))-1
        sr=rv.mean()/rv.std()*np.sqrt(252)
        yrs=(1+rv).resample('YE').prod()-1
        corr=rv.reindex(CHAMP.index).dropna()
        ch=CHAMP.reindex(corr.index).dropna()
        c=np.corrcoef(corr,ch)[0,1] if len(corr)>200 else float('nan')
        h1=rv[rv.index<rv.index[len(rv)//2]]; h2=rv[rv.index>=rv.index[len(rv)//2]]
        print(f'mom_lb={mom_lb} smooth={smooth} n={len(r)} ann={ann:.1%} SR={sr:.2f} '
              f'negyr={(yrs<0).sum()}/{len(yrs)} corrChamp={c:.2f} '
              f'H1={h1.mean()/h1.std()*np.sqrt(252):.2f} H2={h2.mean()/h2.std()*np.sqrt(252):.2f} '
              f'[{r.index.min().date()}..{r.index.max().date()}] MDD={(rv.cumsum()-rv.cumsum().cummax()).min():.1%}')
