"""recon4b: FIXED scramble methodology — positions (raw executed weight path, T+1)
vs RAW SPY returns; real_sr = SR(positions x returns). Same sleeve economics."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_VXV_TERM/scratch')
from bt.engine import lag_signal, vol_target_scale, cap_leverage
from bt.gates import run as gate_run, scramble_positions
from bt.metrics import sharpe_d, ann_geo, max_dd, neg_years, half_split
import recon1

df = recon1.load(); s = recon1.signals(df)
spy = pd.read_csv('/Users/daxu/software/world-trader/tools/quant/data/twelve_big/SPY.csv',
                  index_col=0, parse_dates=True)['close']
spy_r = spy.pct_change()
idx = spy_r.index
champ = df.champ

def sat(name, sig):
    pos = lag_signal(sig).reindex(idx).fillna(0.0)          # T+1 executed position
    wc = cap_leverage(pos.to_frame('w'), max_lev=1.6)['w']  # capital-real cap (|pos|<=1 so no-op)
    book = wc * spy_r.fillna(0.0)
    gross = wc.abs()
    cost = wc.diff().abs().fillna(wc.abs()) * 6.4e-4
    borrow = (-wc.clip(upper=0)) * 0.005 / 252.0
    net = (book - cost - borrow).dropna()
    n08 = net[net.index >= '2008-01-01']
    g = gate_run(n08, ref=champ)
    p, real_sr = scramble_positions(wc.reindex(net.index).values,
                                    spy_r.reindex(net.index).fillna(0.0).values,
                                    n=200, block=10)
    h1, h2 = half_split(n08)
    print('%-26s SR08 %+0.3f ann %+0.3f MDD %+0.3f neg %d/%d H1 %+0.2f H2 %+0.2f corr %+.3f '
          'ac1 %+0.3f uniq %0.3f | poslag p %0.3f (realSR %+0.2f) | %s' % (
        name, g['sr'], ann_geo(n08), max_dd(n08), g['neg_years'], 19 if False else int(
            (net[net.index>='2008-01-01'].groupby(net[net.index>='2008-01-01'].index.year)
             .apply(lambda x:(1+x).prod()-1) < 0).sum()),
        h1, h2, g['corr'], g['ac1'], g['uniq'], p, real_sr,
        'PASS' if (g['pass'] and p < 0.05) else 'FAIL'))
    return n08

cont = s.contango
sat('A long contango flat back', cont)
sat('C long/short contango sign', 2 * cont - 1)
sat('D zrev SPY ratio_z', -s.ratio_z.fillna(0).clip(-3, 3))
sat('F long SPY dvxv21>0', (s.dvxv21 > 0).astype(float))
sat('G always-on long control', pd.Series(1.0, index=s.index))
# combination: contango long / ratio_z risk-off — best-of-family composite
z = s.ratio_z
m = cont * (z <= 1.5).astype(float)
sat('K contango & ratio_z<=1.5', m)
