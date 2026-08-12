#!/usr/bin/env python3
import os, sys, json, time
import numpy as np
import pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if ROOT not in sys.path: sys.path.insert(0, ROOT)
from tools.quant.ls.config import Config
from tools.quant.ls import data, factors, ic_screen, model, backtest, diagnostics
from tools.quant.ls.factors_v2 import compute_v2_factors, process_v2_factors

def _base(name):
    return Config(name=name, seed=42,
        data_dir='tools/quant/data/polygon', benchmark='SPY', fill_method='ffill',
        return_horizon_fwd=10, return_type='log', predict_horizon=10,
        model_method='rf', train_window=120, refit_freq=5, rebalance_freq=5,
        model_min_train_obs=80, model_min_factors=2,
        bypass_ic_screen=True,
        gbrt_label_residual='demean', gbrt_label_transform='zscore',
        gbrt_label_winsorize=0.01, gbrt_pred_clip=4.0, gbrt_pred_smooth=0.0,
        rf_n_estimators=200, rf_max_depth=6, rf_min_samples_leaf=20,
        rf_max_features='sqrt',
        use_extra_factors=True, use_ohlc_factors=True,
        use_interaction_features=False,
        n_long=10, n_short=10, weighting='mean_var', opt_lambda_risk=0.5,
        opt_method='scipy_slsqp', long_short_balance=True, beta_max_abs=0.05,
        position_cap_pct=0.20, gross_leverage=1.0, max_gross_leverage=1.6,
        cost_bps_one_side=3.8, slippage_bps=1.0,
        use_call_rate_financing=True, short_rebate_paid_bps=150.0,
        short_borrow_fee_etb_bps=25.0, short_borrow_apply=True,
        long_financing_apply=True, long_financing_spread_bps=50.0,
        t_plus_1=True, diag_window_sweep=(100, 120, 140),
        plot=False, verbose=False, out_dir='tools/quant/ls/results')

def _export(bundle, cfg):
    d = os.path.join(ROOT, cfg.out_dir, cfg.name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'config.json'), 'w') as f: f.write(cfg.to_json())
    m = bundle['metrics']
    with open(os.path.join(d, 'metrics.json'), 'w') as f:
        json.dump({k: float(v) if isinstance(v, (int,float,np.floating)) else v for k,v in m.items()}, f, indent=2, default=str)
    with open(os.path.join(d, 'verdict.json'), 'w') as f:
        json.dump(bundle['diagnostics']['verdict'], f, indent=2, default=str)
    bundle['result']['equity_curve'].to_csv(os.path.join(d, 'equity_curve.csv'))
    bundle['result']['daily_returns'].to_csv(os.path.join(d, 'daily_returns.csv'))
    ws = bundle['diagnostics'].get('window_sweep')
    if isinstance(ws, dict):
        rows = []
        for w, v in ws.items():
            r = {'window': w}
            r.update({k: val for k, val in v.items() if k != 'factor_weights'})
            rows.append(r)
        pd.DataFrame(rows).to_csv(os.path.join(d, 'diag_window_sweep.csv'), index=False)
    print(f'  artifacts -> {d}')

print('Script module loaded.')
