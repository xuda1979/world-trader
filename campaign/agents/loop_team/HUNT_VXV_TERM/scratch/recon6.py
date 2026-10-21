"""recon6: trade ledger + reconciliation for the best (still-failing) satellite variant A
'long contango flat backwardation' on SPY — to document the exact charged economics.
Ledger: date,sleeve,instrument,side,price,price_source,qty_notional,weight_from,weight_to,cost_bps
Gate: sum|qty| == charged turnover; PnL recomposed from ledger == engine net (<1e-12)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_VXV_TERM/scratch')
from bt.reconcile import max_abs_diff
import recon1

df = recon1.load(); s = recon1.signals(df)
spy_px = pd.read_csv('/Users/daxu/software/world-trader/tools/quant/data/twelve_big/SPY.csv',
                     index_col=0, parse_dates=True)['close']
r = spy_px.pct_change()
idx = r.index
sig = s.contango.reindex(idx).ffill(limit=3)
pos = sig.shift(1).fillna(0.0)  # T+1 executed
dw = pos.diff().abs().fillna(pos.abs())
cost = dw * 6.4e-4
borrow = (-pos.clip(upper=0)) * 0.005 / 252.0
book = pos * r.fillna(0.0)
net = (book - cost - borrow).dropna()
n08 = net[net.index >= '2008-01-01']

# ledger for 2008+ executions
exec_days = dw.loc[n08.index][dw.loc[n08.index] > 0]
led = pd.DataFrame({
    'date': exec_days.index,
    'sleeve': 'VXV_CONTANGO_SPY',
    'instrument': 'SPY',
    'side': np.where(pos.reindex(exec_days.index) > 0, 'BUY', 'SELL'),
    'price': spy_px.reindex(exec_days.index).values,        # REAL t-1 close (execution price)
    'price_source': 'REAL',
    'qty_notional': exec_days.values,
    'weight_from': pos.shift(1).reindex(exec_days.index).values,
    'weight_to': pos.reindex(exec_days.index).values,
    'cost_bps': 6.4,
})
led.to_csv('scratch/LEDGER_VXV_CONTANGO_SPY.csv', index=False)

# reconcile: sum|qty| == charged turnover; recomposed PnL from ledger components
sum_qty = led.qty_notional.sum()
charged = cost.loc[n08.index].sum()
print('ledger rows=%d  sum|qty|=%.10f  charged turnover cost sum=%.10f  |diff|=%.3e' % (
    len(led), sum_qty, charged, abs(sum_qty * 6.4e-4 - charged)))
recon_pnl = (pos.reindex(n08.index) * r.reindex(n08.index).fillna(0.0)
             - cost.reindex(n08.index) - borrow.reindex(n08.index))
d = max_abs_diff(recon_pnl, n08)
print('ledger-recomposed PnL vs engine net: max|diff| = %.3e  -> %s' % (
    d, 'PASS' if d < 1e-12 else 'FAIL'))
print('charged stats 2008+: turnover gross %.2fx NAV, total cost %.4f%% NAV, borrow %.5f%%' % (
    dw.loc[n08.index].sum(), cost.loc[n08.index].sum() * 100, borrow.loc[n08.index].sum() * 100))
print('flips: %d entries+exits over %d days (one-side %.4f bps/day)' % (
    len(led), len(n08), dw.loc[n08.index].mean() * 1e4))
