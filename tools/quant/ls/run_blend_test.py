
import os, sys, json
import numpy as np
import pandas as pd
ROOT = os.path.abspath('.')
sys.path.insert(0, ROOT)
from tools.quant.ls.config import Config
from tools.quant.ls import data, backtest, diagnostics
gbrt_pred = pd.read_csv('tools/quant/ls/results/gbrt_tune/s05_d2/predictions.csv', index_col=0)
rf_pred = pd.read_csv('tools/quant/ls/results/rf_d8_n500_bypass/predictions.csv', index_col=0)
with open('tools/quant/ls/results/gbrt_tune/s05_d2/config.json') as f:
    cfg_dict = json.load(f)
cfg_dict['slippage_bps'] = 0.0
cfg_dict['plot'] = False
cfg_dict['verbose'] = False
cfg_dict['save_intermediate'] = False
cfg = Config.from_dict(cfg_dict)
panel = data.load_panel(cfg)

def cs_zscore(df):
    mu = df.mean(axis=1); sd = df.std(axis=1); sd = sd.replace(0, 1.0)
    return df.sub(mu, axis=0).div(sd, axis=0)

gbrt_z = cs_zscore(gbrt_pred.fillna(0))
rf_z = cs_zscore(rf_pred.fillna(0))

results = []
out_dir = 'tools/quant/ls/results/blend_gbrt_rf'
os.makedirs(out_dir, exist_ok=True)

weights_dummy = pd.DataFrame()
ic_dummy = pd.DataFrame()

for alpha in [0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0]:
    blended = alpha * gbrt_z + (1 - alpha) * rf_z
    cfg.name = 'blend_%.1f' % alpha
    result = backtest.run_backtest(panel, blended, cfg)
    metrics = backtest.compute_metrics(result, cfg, panel['prices'])
    try:
        diag = diagnostics.run_diagnostics(result, panel, blended, weights_dummy, ic_dummy, {}, cfg, [], {})
        verdict = diag['verdict']['assessment']
        n_flags = diag['verdict']['n_flags']
    except Exception as e:
        verdict = 'diag_err'
        n_flags = -1
    r = {'alpha': alpha, 'sharpe': metrics.get('sharpe',0), 'ann_ret': metrics.get('annual_return',0),
         'ann_vol': metrics.get('annual_volatility',0), 'max_dd': metrics.get('max_drawdown',0),
         'turnover': metrics.get('annual_turnover',0), 'sortino': metrics.get('sortino',0),
         'verdict': verdict, 'n_flags': n_flags}
    results.append(r)
    print('a=%.1f: Sharpe=%.3f ret=%.3f DD=%.3f TO=%.1f %s(%d)' % (alpha, r['sharpe'], r['ann_ret'], r['max_dd'], r['turnover'], verdict, n_flags))

df = pd.DataFrame(results)
df.to_csv(os.path.join(out_dir, 'blend_results.csv'), index=False)
print()
print(df.to_string())
