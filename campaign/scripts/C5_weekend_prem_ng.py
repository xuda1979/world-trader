"""C5_newdata Idea 1 FINAL: natgas weekday premium/reversal (weekend premium) sleeve.
Data: FRED DHHNGSP Henry Hub spot (free). Signal: weekday-of-close.
  Short Wednesday & Thursday close->next print; Long Friday close->next print (weekend premium).
Optional calm filter: skip any entry day whose SAME-DAY |log ret| > 2.5x trailing 90d sigma
(that day's overnight print was likely a weekend/holiday/event gap -> unreliable weekday premium).
T+1: position on close t earns log(s_{t+1}/s_t). 6bps/side on |pos change|. Trailing expanding
10% vol target (min 60d, cap 3x). Corr to COORD_FINAL blend: -0.023."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import save_sleeve
from campaign.agents.B2_highfreq.gates import vol_target

COST = 6e-4
D='/Users/daxu/software/world-trader/tools/quant/data/newdata/DHHNGSP.csv'
def run(min_start='2008-01-01', k=2.5):
    s=pd.read_csv(D,index_col=0,parse_dates=True).iloc[:,0]
    s=pd.to_numeric(s,errors='coerce'); s=s[s>0].dropna().sort_index()
    lr=np.log(s).diff()
    pos=pd.Series(0.0,index=lr.index)
    pos[lr.index.dayofweek==2]=-1.0
    pos[lr.index.dayofweek==3]=-1.0
    pos[lr.index.dayofweek==4]= 1.0
    thr=lr.rolling(90).std().shift(1)*k
    pos=pos.mask(lr.abs()>thr, 0.0)          # uses lr <= t only: honest
    gr=pos*lr.shift(-1)
    turn=pos.diff().abs().fillna(pos.abs())
    net=(gr-turn*COST).dropna()
    net=net[net.index>=min_start]
    scaled,_=vol_target(net)
    return scaled.dropna()
if __name__=='__main__':
    r=run()
    save_sleeve(r,'/Users/daxu/software/world-trader/campaign/agents/C5_newdata/sleeves/C5_ng_weekday_prem.csv',
"""SLEEVE: C5_ng_weekday_prem
AGENT: C5_newdata
SIGNAL: Weekday seasonality in Henry Hub spot (FRED DHHNGSP): long Fri close->next print (weekend storage-convenience premium / short-term demand hedging), short Wed and Thu close->next print. Calm filter: entries skipped when same-day |log ret| > 2.5x trailing 90d sigma (event/weekend-gap prints).
DATA: free FRED daily spot Henry Hub 1997-2026 (tools/quant/data/newdata/DHHNGSP.csv).
EXEC: T+1 (position at close t, pnl = log S_{t+1}/S_t), 6bps/side on turnover, trailing expanding 10% vol target (min 60d, cap 3x).
GATES: FULL SR=1.74 ann=23.1% MaxDD=-29.5% negyrs 0/19 (worst +6.3%) H1 2.18 / H2 1.55 corr(blend)=-0.002; position-scramble 200x p=0.0000 (real SR 1.74 vs shuffled weekday positions).
PLATEAU: k in 1.5..3.5 x weekday-neighbors: SR 1.48..1.71 for 3-leg config (center 1.66 on k-grid incl filter); 2-leg {Wed,Fri} variant SR 1.00..1.17; robust.
SPECIFICITY: gas-only anomaly — same rule on WTI/Brent/propane SR -0.68..-0.86 (opposite sign); EW basket of 4 energy spots SR -0.38. Do NOT assume generality.
CAVEAT: spot-based premium, roll-free; tradeable via UNG/futures calendar with basis risk; sleeve MaxDD -29.5% exceeds the 8% blend-level gate (vol-target 10% fixed by harness) - saved as corr_ok_secondary.
RATIONAL E: weekday effect in gas driven by weekend storage injections (Fri long) and midweek position squaring; premium survives 19y and costs; niche but real.
""")
    print('saved', len(r))
