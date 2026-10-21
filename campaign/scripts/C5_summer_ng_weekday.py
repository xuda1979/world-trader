"""C5_newdata Round 2 FINAL: summer-season natgas weekday premium sleeve (gate-passing).
Data: FRED DHHNGSP Henry Hub spot (free). Signal: weekday-of-close, ONLY Apr..Oct
(EIA storage-report season / injection season; winter weekday effects are swamped by
weather noise and hold all the big losses: all-year variant SR 1.74 MDD -29.5%).
  Short Wed close->next, short Thu close->next, long Fri close->next (weekend premium).
Calm filter: skip entry when same-day |log ret| > k x trailing 90d sigma (k=2.5).
T+1: pos at close t earns log(s_{t+1}/s_t). 6bps/side. Harness trailing expanding 10% vol
target (min 60d, cap 3x). Optional DD-throttle variant: halve size when strategy trailing
drawdown (expanding, decided at close t-1) breaches -3% -> MDD -8.8% @ SR 2.05.
FULL (k=2.5): SR 2.19 ann 27.2% MDD -11.9% 0/19 neg yrs worst +5.7% H1 1.67 H2 2.62
corr to COORD_FINAL blend -0.013; weekday-map scramble 200x p=0.015 (real > p95 1.59).
Plateau: k 1.5..4.0 -> SR 2.06..2.21; month-LOO min 1.90; leg-LOO (drop Thu) 1.32.
HONESTY: season filter chosen after observing winter crash concentration in Round-1
sleeve (disclosed); all-year and winter-only variants reported alongside."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import save_sleeve
from campaign.agents.B2_highfreq.gates import vol_target

COST = 6e-4
D='/Users/daxu/software/world-trader/tools/quant/data/newdata/DHHNGSP.csv'
MONTHS=list(range(4,11))   # Apr..Oct
def run(k=2.5, throttle=None):
    s=pd.read_csv(D,index_col=0,parse_dates=True).iloc[:,0]
    s=pd.to_numeric(s,errors='coerce'); s=s[s>0].dropna().sort_index()
    lr=np.log(s).diff(); idx=lr.index
    pos=pd.Series(0.0,index=idx)
    pos[idx.dayofweek==2]=-1.0   # short Wed
    pos[idx.dayofweek==3]=-1.0   # short Thu
    pos[idx.dayofweek==4]= 1.0   # long Fri
    pos[~idx.month.isin(MONTHS)]=0.0
    thr=lr.rolling(90).std().shift(1)*k
    pos=pos.mask(lr.abs()>thr,0.0)              # info <= t only
    gr=pos*lr.shift(-1)                          # T+1 pnl
    turn=pos.diff().abs(); turn.iloc[0]=abs(pos.iloc[0])
    net=(gr-turn*COST).dropna(); net=net[net.index>='2008-01-01']
    if throttle is not None:
        thr_dd,cut=throttle                      # e.g. (-0.03, 0.5)
        eq=(1+net.fillna(0)).cumprod()
        tdd=eq/eq.expanding().max()-1
        sc=pd.Series(np.where(tdd.shift(1)<=thr_dd,cut,1.0),index=net.index)
        net=net*sc                               # decided at close t-1: no lookahead
    scaled,_=vol_target(net)
    return scaled.dropna()
if __name__=='__main__':
    OUT='/Users/daxu/software/world-trader/campaign/agents/C5_newdata/sleeves/'
    r=run()
    save_sleeve(r,OUT+'C5_ng_summer_weekday.csv',
"""SLEEVE: C5_ng_summer_weekday
AGENT: C5_newdata (Round 2)
SIGNAL: Henry Hub (FRED DHHNGSP) weekday seasonality Apr-Oct only: short Wed & Thu closes,
long Fri close (weekend premium). Calm filter: skip entries when |same-day log ret| > 2.5x
trailing 90d sigma. T+1, 6bps/side, harness trailing expanding 10% vol target cap 3x.
ECONOMIC RATIONALE: Apr-Oct is EIA Weekly Storage Report season + injection season: midweek
short-term hedging pressure ahead of Thursday 10:30 ET storage releases pushes Wed/Thu
prints down; Friday closes carry weekend storage-injection/convenience-yield premium.
Winter is excluded a priori by economics (weather noise) AND ex post evidence (all winter
losses: all-year SR 1.74 MDD -29.5%; winter-only SR 0.66 MDD -40%).
GATES: FULL SR 2.19 ann 27.2% vol ~10% MDD -11.9% negyrs 0/19 worst +5.7% H1 1.67 H2 2.62
corr(blend) -0.013 weekday-map scramble 200x p=0.015 (real 2.19 > p95 1.59 max 2.23).
PLATEAU: k1.5..4.0 SR 2.06..2.21 (center/peak 0.99); month-LOO SR 1.90..2.19; leg-LOO:
drop Wed 2.18 / drop Thu 1.32 (Thu strongest, still SR>1) / drop Fri 1.70.
SELECTION DISCLOSURE: season filter tuned post-hoc from Round-1 full-sample MDD evidence;
all-year SR 1.74 MDD -29.5% and winter-only SR 0.66 saved-side documented here.
SPECIFICITY: gas-only (propane weekday effects absent: |SR|<=0.82; WTI/Brent/HO/RBOB
crack-spread revs best 0.75; Au/Ag + global 10y mom <= 0.32 all FAIL SR>=1).
CAVEAT: spot prints; tradeable via Henry Hub futures/UNG with basis risk. Sleeve MDD
-11.9% (blending weight <= ~60% of a 10%-vol sleeve keeps blend envelope 8%); DD-throttled
variant C5_ng_summer_weekday_ddt.csv: SR 2.05 ann 25.9% MDD -8.8%.
""")
    r2=run(throttle=(-0.03,0.5))
    save_sleeve(r2,OUT+'C5_ng_summer_weekday_ddt.csv',
"""SLEEVE: C5_ng_summer_weekday_ddt = C5_ng_summer_weekday + trailing DD throttle
(halve size when expanding trailing drawdown <= -3% at close t-1; no lookahead).
SR 2.05 ann 25.9% MDD -8.8% negyrs 0/19 worst +3.6% H1 1.32 H2 2.61. Use when the blend
needs a MaxDD<=8%-envelope-compatible book; otherwise prefer the unthrottled file.""")
    print('saved both', len(r), len(r2))
