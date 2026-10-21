"""recon5: gvzovx_z regime -> ONE commodity instrument each (IAU gold, USO oil; REAL closes).
Also gold-vol satellite via GVZ z on IAU. Same machinery as recon4b."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_VXV_TERM/scratch')
from bt.engine import lag_signal, cap_leverage
from bt.gates import run as gate_run, scramble_positions
from bt.metrics import sharpe_d, ann_geo, max_dd, half_split
import recon1

df = recon1.load(); s = recon1.signals(df)
champ = df.champ
B = '/Users/daxu/software/world-trader/tools/quant/data/more_etf/'

def sat(name, sig, inst):
    px = pd.read_csv(B + inst + '.csv', index_col=0, parse_dates=True)['close']
    r = px.pct_change()
    idx = r.index
    pos = lag_signal(sig).reindex(idx).fillna(0.0)
    wc = cap_leverage(pos.to_frame('w'), max_lev=1.6)['w']
    net = (wc * r.fillna(0.0) - wc.diff().abs().fillna(wc.abs()) * 6.4e-4
           - (-wc.clip(upper=0)) * 0.005 / 252.0).dropna()
    n08 = net[net.index >= '2008-01-01']
    if len(n08) < 1500:
        print('%-30s %s: span too short n=%d (%s..%s) — skip' % (name, inst, len(n08), n08.index.min().date(), n08.index.max().date())); return
    g = gate_run(n08, ref=champ)
    p, real_sr = scramble_positions(wc.reindex(net.index).values, r.reindex(net.index).fillna(0.0).values, n=200, block=10)
    h1, h2 = half_split(n08)
    yrs = n08.groupby(n08.index.year).apply(lambda x: (1 + x).prod() - 1)
    print('%-30s %-4s SR08 %+0.3f ann %+0.3f MDD %+0.3f neg %d H1 %+0.2f H2 %+0.2f corr %+.3f | poslag p %0.3f (realSR %+0.2f) | %s' % (
        name, inst, g['sr'], ann_geo(n08), max_dd(n08), g['neg_years'], h1, h2, g['corr'], p, real_sr,
        'PASS' if (g['pass'] and p < 0.05) else 'FAIL'))

go = s.gvzovx_z
sat('L long IAU gvzovx_z<0', (go < 0).astype(float), 'IAU')
sat('M long IAU gvzovx_z>0', (go > 0).astype(float), 'IAU')
sat('N long/short gvzovx_z', np.sign(go.fillna(0)), 'IAU')
sat('O long USO gvzovx_z<0', (go < 0).astype(float), 'USO')
sat('P long USO gvzovx_z>0', (go > 0).astype(float), 'USO')
gz = ((df.gvz - df.gvz.rolling(252, min_periods=126).mean())
      / df.gvz.rolling(252, min_periods=126).std())
sat('Q long IAU gvz_z<0 (lowvol)', (gz < 0).astype(float), 'IAU')
sat('R long USO ovx_z<0', (df.ovx < df.ovx.rolling(252, min_periods=126).mean()).astype(float), 'USO')
# controls
sat('CTRL long IAU always', pd.Series(1.0, index=s.index), 'IAU')
sat('CTRL long USO always', pd.Series(1.0, index=s.index), 'USO')
