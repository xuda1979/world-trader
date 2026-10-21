"""Focused sweep: verify and extend all14f_d3 (Sharpe 1.582)."""
import sys, os, time
sys.path.insert(0, '.')
import numpy as np

ROOT = os.path.abspath('.')
from tools.quant.ls import runner
from tools.quant.ls.config import Config

BASE = dict(
    name='tmp', model_method='gbrt', predict_horizon=10, return_horizon_fwd=10,
    train_window=120, refit_freq=5, rebalance_freq=5,
    gbrt_max_depth=3, gbrt_n_estimators=200, gbrt_learning_rate=0.05,
    gbrt_min_samples_leaf=20, gbrt_max_features='sqrt', gbrt_subsample=1.0,
    gbrt_pred_clip=4.0, gbrt_pred_smooth=0.5,
    gbrt_label_transform='zscore', gbrt_label_residual='demean',
    gbrt_label_winsorize=0.01, gbrt_loss='squared_error',
    bypass_ic_screen=None, icir_threshold=0.0, ic_mean_threshold=0.0,
    ic_bonferroni=False,
    use_extra_factors=False, use_ohlc_factors=False, use_interaction_features=False,
    n_long=13, n_short=13, weighting='mean_var', opt_lambda_risk=0.5,
    position_cap_pct=0.20, gross_leverage=1.0, max_gross_leverage=1.0,
    long_short_balance=True, beta_max_abs=0.05,
    use_call_rate_financing=True, short_borrow_apply=True,
    long_financing_apply=True, short_rebate_paid_bps=150.0,
    short_borrow_fee_etb_bps=25.0, long_financing_spread_bps=50.0,
    cost_bps_one_side=3.8, slippage_bps=1.0,
    t_plus_1=True, diag_window_sweep=(100,120,140),
    save_intermediate=False, plot=False, verbose=False,
    out_dir='tools/quant/ls/results/v4_sweep',
)

configs = [
    ('v4_verify_d3', dict()),
    ('v4_d3_n500', dict(gbrt_n_estimators=500)),
    ('v4_d3_n1000', dict(gbrt_n_estimators=1000)),
    ('v4_d4_n500', dict(gbrt_max_depth=4, gbrt_n_estimators=500, gbrt_min_samples_leaf=30)),
    ('v4_d3_n13_lev12', dict(n_long=13, n_short=13, gross_leverage=1.2, max_gross_leverage=1.2)),
    ('v4_d3_n15', dict(n_long=15, n_short=15)),
    ('v4_d3_huber', dict(gbrt_loss='huber', gbrt_alpha=0.9)),
    ('v4_d3_bonf', dict(ic_bonferroni=True)),
]

results = []
for name, overrides in configs:
    cfg_dict = dict(BASE, name=name)
    cfg_dict.update(overrides)
    cfg_dict['out_dir'] = 'tools/quant/ls/results/v4_sweep/' + name
    cfg = Config.from_dict(cfg_dict)
    print('Running: %s' % name)
    t0 = time.time()
    try:
        bundle = runner.run(cfg, export=True)
        dt = time.time() - t0
        m = bundle['metrics']
        v = bundle['diagnostics']['verdict']
        r = {'name': name, 'sharpe': m.get('sharpe',np.nan), 'ann_ret': m.get('annual_return',np.nan),
             'ann_vol': m.get('annual_volatility',np.nan), 'max_dd': m.get('max_drawdown',np.nan),
             'sortino': m.get('sortino',np.nan), 'calmar': m.get('calmar',np.nan),
             'turnover': m.get('annual_turnover',np.nan), 'verdict': v['assessment'],
             'n_flags': v['n_flags'], 'n_kept': len(bundle['kept_factors'])}
        results.append(r)
        print('  S=%.3f  ret=%.2f%%  dd=%.2f%%  TO=%.1f  nF=%d  %s(%df) dt=%ds' % (
            r['sharpe'], r['ann_ret']*100, r['max_dd']*100, r['turnover'],
            r['n_kept'], r['verdict'], r['n_flags'], int(dt)))
    except Exception as e:
        import traceback; traceback.print_exc()
        results.append({'name': name, 'error': str(e)[:200]})

print('
=== RESULTS ===')
ok = sorted([r for r in results if 'sharpe' in r and np.isfinite(r['sharpe'])], key=lambda r: r['sharpe'], reverse=True)
for i, r in enumerate(ok):
    print('%d. %-25s S=%.3f  ret=%.2f%%  dd=%.2f%%  TO=%.1f  %s(%df)' % (
        i+1, r['name'], r['sharpe'], r['ann_ret']*100, r['max_dd']*100,
        r['turnover'], r['verdict'], r['n_flags']))

import pandas as pd
pd.DataFrame(results).to_csv('tools/quant/ls/results/v4_sweep_summary.csv', index=False)
