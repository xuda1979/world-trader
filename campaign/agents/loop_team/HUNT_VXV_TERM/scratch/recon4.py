"""recon4: SATELLITE — ONE clean instrument: SPY (twelve_big/SPY.csv, REAL closes).
Term-structure state -> T+1 SPY position via bt.backtest.sleeve (6.4bps, borrow 0.5%,
cap 1.6x capital-real). Gates: SR>=0.6 (2008+), |corr|<0.15 vs champion, H1/H2>=0.3,
200x poslag-scramble p<0.05."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_VXV_TERM/scratch')
from bt.backtest import sleeve
from bt.gates import run as gate_run, scramble_positions
from bt.metrics import sharpe_d, ann_geo, max_dd, neg_years
import recon1

df = recon1.load(); s = recon1.signals(df)
spy = pd.read_csv('/Users/daxu/software/world-trader/tools/quant/data/twelve_big/SPY.csv',
                  index_col=0, parse_dates=True)
spy_close = spy['close'].rename('spy_close')
spy_r = spy['close'].pct_change().rename('spy_r')
print('SPY: n=%d %s..%s REAL close (twelve_big), fwd ret last=%s' % (
    len(spy_r), spy_r.index.min().date(), spy_r.index.max().date(), spy_r.index.max().date()))

# align: signal index = champion/index dates; returns frame for sleeve = SPY daily ret
R = spy_r.to_frame('spy_r')
champ = df.champ

def sat(name, sig):
    net = sleeve(sig, R, target=0.10, cost_bps=6.4, borrow=0.005, max_lev=1.6)
    post = net.index >= '2008-01-01'
    n08 = net[post]
    g = gate_run(n08, ref=champ)
    p, real_sr = scramble_positions(net.values, R['spy_r'].reindex(net.index).fillna(0.0).values,
                                    n=200, block=10)
    print('%-28s SR08 %+0.3f (g%0.3f) ann %s MDD %+0.3f neg %d H1 %+0.2f H2 %+0.2f '
          'corr %+.3f ac1 %0.3f uniq %0.3f | scramb p %0.3f (realSR %0.2f) %s' % (
        name, sharpe_d(n08), g['sr'], ('%0.3f' % ann_geo(n08)), max_dd(n08), g['neg_years'],
        g['h1'], g['h2'], g['corr'], g['ac1'], g['uniq'], p, real_sr,
        'PASS' if (g['pass'] and p < 0.05) else 'FAIL'))

cont = s.contango
back = 1 - cont
sat('A long contango flat back', cont)
sat('B short backwardation', -back)
sat('C long/short contango sign', 2 * cont - 1)
z = s.ratio_z
sat('D zrev SPY ratio_z', -z.fillna(0).clip(-3, 3))
sat('E mom SPY ratio_z', z.fillna(0).clip(-3, 3))
sat('F long SPY dvxv21>0', (s.dvxv21 > 0).astype(float))
sat('G long SPY always-on control', pd.Series(1.0, index=s.index))
sat('H short SPY always-on control', pd.Series(-1.0, index=s.index))
