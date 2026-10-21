"""V3 Research Sweep: higher-Sharpe strategies."""
import os, sys, time
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls import runner, data, factors, ic_screen, model, backtest, diagnostics
from tools.quant.ls.config import Config
from tools.quant.ls.factors_v2 import compute_v2_factors, process_v2_factors

def base_cfg(name, use_v2=True):
    return Config().copy(**{
        'name': name, 'predict_horizon': 10, 'return_horizon_fwd': 10,
        'train_window': 120, 'refit_freq': 5, 'rebalance_freq': 5,
        'model_method': 'gbrt', 'gbrt_n_estimators': 200, 'gbrt_max_depth': 2,
        'gbrt_learning_rate': 0.05, 'gbrt_min_samples_leaf': 20,
        'gbrt_max_features': 'sqrt', 'gbrt_pred_clip': 4.0, 'gbrt_pred_smooth': 0.5,
        'gbrt_label_transform': 'zscore', 'gbrt_label_residual': 'demean',
        'gbrt_label_winsorize': 0.01, 'bypass_ic_screen': True,
        'use_extra_factors': True, 'n_long': 10, 'n_short': 10,
        'weighting': 'mean_var', 'opt_lambda_risk': 0.5,
        'position_cap_pct': 0.20, 'gross_leverage': 1.6, 'max_gross_leverage': 2.0,
        'use_call_rate_financing': True, 'long_financing_apply': True,
        'cost_bps_one_side': 3.8, 'slippage_bps': 1.0,
        'diag_window_sweep': (100, 120, 140),
        'out_dir': 'tools/quant/ls/results',
        'save_intermediate': False, 'plot': False, 'verbose': False,
    })

def run_one(cfg):
    t0 = time.time()
    panel = data.load_panel(cfg)
    processed, stacked, fnames = factors.all_factors(panel, cfg)
    if getattr(cfg, 'use_extra_factors', True):
        extra_raw = factors.compute_extra_raw_factors(panel, cfg)
        extra_processed = factors.process_cross_section(extra_raw, panel, cfg)
        processed.update(extra_processed)
    if getattr(cfg, 'use_ohlc_factors', True):
        ohlc_raw = factors.compute_ohlc_factors(panel, cfg)
        ohlc_p = factors.process_cross_section(ohlc_raw, panel, cfg)
        processed.update(ohlc_p)
    use_v2 = getattr(cfg, 'use_v2_factors', True)
    if use_v2:
        v2r = compute_v2_factors(panel, cfg)
        v2p = process_v2_factors(v2r, panel, cfg)
        processed.update(v2p)
    fnames = list(processed.keys())
    fwd = ic_screen.forward_returns(panel['prices'], cfg.return_horizon_fwd)
    ic_df = ic_screen.compute_all_ic(processed, fwd, cfg)
    if getattr(cfg, 'bypass_ic_screen', False):
        kept = list(fnames)
        _, stats, icir_full = ic_screen.screen_factors(ic_df, cfg, fnames)
        sign_flips = {}
    else:
        kept, stats, icir_full = ic_screen.screen_factors(ic_df, cfg, fnames)
        sign_flips = {f: s.get('sign_flip', False) for f, s in stats.items()}
        if not kept:
            kept = fnames[:10]
    om = model.roll_forward_dispatch(processed, panel, cfg, kept_factors=kept, sign_flips=sign_flips)
    bt = backtest.run_backtest(panel, om['predictions'], cfg)
    m = backtest.compute_metrics(bt, cfg, panel['prices'])
    diag = diagnostics.run_diagnostics(bt, panel, om['predictions'], om['weights'], ic_df, processed, cfg, kept, sign_flips)
    dt = time.time() - t0
    return {'metrics': m, 'verdict': diag['verdict'], 'kept': kept, 'runtime_s': dt}

def main():
    configs = []
    for d in [1, 2, 3]:
        for n in [200, 500, 1000]:
            configs.append(base_cfg(f'v3_d{d}_n{n}').set(gbrt_max_depth=d, gbrt_n_estimators=n))
    for d in [2, 3]:
        configs.append(base_cfg(f'v3_d{d}_huber').set(gbrt_max_depth=d, gbrt_loss='huber', gbrt_alpha=0.9))
        configs.append(base_cfg(f'v3_d{d}_vs').set(gbrt_max_depth=d, gbrt_label_vol_scale=True, gbrt_label_winsorize=0.02))
    for h in [5, 21]:
        configs.append(base_cfg(f'v3_h{h}').set(predict_horizon=h, return_horizon_fwd=h))
    for s in [0.6, 0.7, 0.8]:
        configs.append(base_cfg(f'v3_s{int(s*100)}').set(gbrt_pred_smooth=s))
    configs.append(base_cfg('v3_nov2', use_v2=False).set(gbrt_max_depth=2))
    try:
        import lightgbm
        for d in [2, 3, 4]:
            configs.append(base_cfg(f'v3_lgb_d{d}').set(model_method='gbrt', gbrt_max_depth=d, gbrt_n_estimators=500))
    except ImportError:
        pass
    try:
        import xgboost
        for d in [3, 4, 5]:
            configs.append(base_cfg(f'v3_xgb_d{d}').set(model_method='xgb', gbrt_max_depth=d, xgb_reg_alpha=0.5))
    except ImportError:
        pass
    configs.append(base_cfg('v3_icir').set(model_method='icir', bypass_ic_screen=False, icir_threshold=0.08, ic_mean_threshold=0.005))
    configs.append(base_cfg('v3_conc').set(n_long=6, n_short=6, gross_leverage=2.0, max_gross_leverage=2.5, position_cap_pct=0.30, gbrt_max_depth=2, gbrt_n_estimators=300))

    print(f'Running {len(configs)} configs...')
    results = []
    t0 = time.time()
    for i, cfg in enumerate(configs):
        try:
            b = run_one(cfg)
            m = b['metrics']
            v = b['verdict']
            r = {'name': cfg.name, 'depth': getattr(cfg,'gbrt_max_depth',None),
                 'n_est': getattr(cfg,'gbrt_n_estimators',None),
                 'sharpe': m.get('sharpe', float('nan')),
                 'ann_ret': m.get('annual_return', float('nan')),
                 'ann_vol': m.get('annual_volatility', float('nan')),
                 'max_dd': m.get('max_drawdown', float('nan')),
                 'sortino': m.get('sortino', float('nan')),
                 'calmar': m.get('calmar', float('nan')),
                 'turnover': m.get('annual_turnover', float('nan')),
                 'verdict': v.get('assessment','?'), 'n_flags': v.get('n_flags',-1),
                 'flags': '; '.join(v.get('overfitting_flags',[])),
                 'n_kept': len(b['kept']), 'runtime_s': b['runtime_s']}
            results.append(r)
            print(f'[{i+1}/{len(configs)}] {cfg.name:25s} S={r["sharpe"]:.3f} '
                  f'ret={r["ann_ret"]:.2%} dd={r["max_dd"]:.2%} '
                  f'to={r["turnover"]:.1f} {r["verdict"]}({r["n_flags"]}f) '
                  f'nf={r["n_kept"]} dt={b["runtime_s"]:.0f}s')
        except Exception as e:
            import traceback
            traceback.print_exc()
            results.append({'name': cfg.name, 'error': str(e)[:200]})
            print(f'[{i+1}/{len(configs)}] {cfg.name} ERROR: {e}')

    print(f'\n=== DONE in {(time.time()-t0)/60:.1f} min ===')
    ok = [r for r in results if 'sharpe' in r and np.isfinite(r['sharpe'])]
    ok.sort(key=lambda r: r['sharpe'], reverse=True)
    for rank, r in enumerate(ok[:15]):
        print(f'{rank+1:2d}. {r["name"]:30s} S={r["sharpe"]:.3f} '
              f'ret={r["ann_ret"]:.2%} dd={r["max_dd"]:.2%} to={r["turnover"]:.1f}')

    df = pd.DataFrame(results)
    df.to_csv(os.path.join(ROOT, 'tools/quant/ls/results/research_v3_sweep.csv'), index=False)
    return results

if __name__ == '__main__':
    main()
