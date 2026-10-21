"""C5_newdata Idea 1: Nat-gas intraday-reversal-reversal day-of-week tilt sleeve.
Data: DHHNGSP (FRED spot Henry Hub, free). Signal at t close -> position t+1 only (T+1).
Short Wednesday close->Thu + long Friday close->Monday (overnight+weekend); flat Mon/Tue.
Net of 6bps/side. Trailing expanding vol-target 10% ann (min 60d, cap 3.0)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
D='/Users/daxu/software/world-trader/tools/quant/data/newdata/DHHNGSP.csv'
from campaign.harness.data import save_sleeve
from campaign.agents.B2_highfreq.gates import vol_target

COST = 6e-4
def run(min_start='2008-01-01'):
    s=pd.read_csv(D,index_col=0,parse_dates=True).iloc[:,0]
    s=pd.to_numeric(s,errors='coerce'); s=s[s>0].dropna().sort_index()
    lr=np.log(s).diff()
    dpos=pd.Series(0.0,index=lr.index)
    dpos[lr.index.dayofweek==2]=-1.0   # Wed close -> Thu
    dpos[lr.index.dayofweek==4]= 1.0   # Fri close -> Mon
    ret=lr.shift(-1)
    gr=dpos*ret
    turn=dpos.diff().abs().fillna(dpos.abs())  # from flat each new position day
    net=(gr-turn*COST).dropna()
    net=net[net.index>=min_start]
    scaled,scale=vol_target(net)
    return scaled

if __name__=='__main__':
    r=run()
    save_sleeve(r,'/Users/daxu/software/world-trader/campaign/agents/C5_newdata/sleeves/C5_ng_wed_rev_fri.csv',
        meta="SLEEVE: C5_ng_wed_rev_fri\nAGENT: C5_newdata\n"
             "SIGNAL: Day-of-week reversal tilt on natgas spot (FRED DHHNGSP): short Wed->Thu (stats: Wed-to-Thu has strongest mean drop after Tue strength), long Fri->Mon weekend premium.\n"
             "DATA: free FRED spot Henry Hub 1997+.\nEXEC: T+1, 6bps/side, trailing expanding 10% vol target cap 3.\n")
    print('saved', len(r))
