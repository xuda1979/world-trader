"""Final research push (2026-08-04) -- systematic Sharpe maximization."""
from __future__ import annotations
import os, sys, time, json
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from tools.quant.ls import runner
from tools.quant.ls.config import Config
import pandas as pd

BASE = {
    'model_method': 'gbrt', 'bypass_ic_screen': True,
    'use_extra_factors': True, 'use_ohlc_factors': False,
    'use_interaction_features': False,
    'gbrt_max_depth': 3, 'gbrt_n_estimators': 400,
    'gbrt_learning_rate': 0.05, 'gbrt_min_samples_leaf': 20,
    'gbrt_subsample': 1.0, 'gbrt_max_features': 'sqrt',
    'gbrt_loss': 'squared_error', 'gbrt_alpha': 0.9,
    'gbrt_pred_clip': 4.0, 'gbrt_pred_smooth': 0.5,
    'gbrt_label_transform': 'zscore',
    'gbrt_label_residual': 'demean',
    'gbrt_label_winsorize': 0.01,
    'n_long': 10, 'n_short': 10, 'use_fixed_n': True,
    'weighting': 'mean_var', 'opt_lambda_risk': 0.5,
    'long_short_balance': True, 'beta_target': 0.0,
    'beta_max_abs': 0.05, 'position_cap_pct': 0.20,
    'vol_target_active': False, 'gross_leverage': 1.6,
    'max_gross_leverage': 2.0,
    'train_window': 120, 'refit_freq': 5,
    'predict_horizon': 10, 'return_horizon_fwd': 10,
    'rebalance_freq': 5, 't_plus_1': True,
    'hold_zone_top_pct': 0.03, 'hold_zone_bot_pct': 0.03,
    'hold_to_reduce_turnover': True,
    'cost_bps_one_side': 3.8, 'slippage_bps': 0.0,
    'use_call_rate_financing': True,
    'short_borrow_apply': True, 'long_financing_apply': True,
    'short_rebate_paid_bps': 150.0, 'short_borrow_fee_etb_bps': 25.0,
    'long_financing_spread_bps': 50.0,
    'diag_window_sweep': (100, 120, 140),
    'diag_regime_split': True,
    'save_intermediate': True, 'plot': False, 'verbose': False,
}

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results', 'final_push')
os.makedirs(RESULTS_DIR, exist_ok=True)

def run_config(name, **overrides):
    cfg_dict = dict(BASE, name=name, **overrides)
    cfg_dict['out_dir'] = os.path.join(RESULTS_DIR, name)
    cfg = Config.from_dict(cfg_dict)
    t0 = time.time()
    try:
        bundle = runner.run(cfg, export=True)
        dt = time.time() - t0
        m = bundle['metrics']
        v = bundle['diagnostics']['verdict']
        nf = len(bundle.get('kept_factors', []))
        return {
            'config': name, 'sharpe': m.get('sharpe', 0),
            'ann_ret': m.get('annual_return', 0),
            'ann_vol': m.get('annual_volatility', 0),
            'turnover': m.get('annual_turnover', 0),
            'max_dd': m.get('max_drawdown', 0),
            'verdict': v.get('assessment', '?'),
            'n_flags': v.get('n_flags', 99),
            'flags': '; '.join(v.get('overfitting_flags', [])),
            'n_factors': nf, 'runtime_s': dt,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'config': name, 'error': str(e), 'runtime_s': time.time() - t0}

def main():
    all_results = []
    t_total = time.time()

    print('STAGE 1: Model capacity sweep')
    stage1 = []
    for n in [400, 600, 800]:
        for lr in [0.05, 0.08]:
            stage1.append((f'd2_n{n}_lr{lr:.2f}', {'gbrt_max_depth': 2, 'gbrt_n_estimators': n, 'gbrt_learning_rate': lr}))
    for n in [200, 400, 600, 800]:
        for lr in [0.03, 0.05, 0.08]:
            stage1.append((f'd3_n{n}_lr{lr:.2f}', {'gbrt_max_depth': 3, 'gbrt_n_estimators': n, 'gbrt_learning_rate': lr}))
    for n in [400, 600]:
        for lr in [0.03, 0.05]:
            stage1.append((f'd4_n{n}_lr{lr:.2f}', {'gbrt_max_depth': 4, 'gbrt_n_estimators': n, 'gbrt_learning_rate': lr}))

    for i, (name, over) in enumerate(stage1):
        print(f'[{i+1}/{len(stage1)}] {name}', flush=True)
        r = run_config(name, **over)
        all_results.append(r)
        if 'sharpe' in r:
            print(f'  Sharpe={r["sharpe"]:.4f} Ret={r["ann_ret"]*100:.1f}% TO={r["turnover"]:.1f} DD={r["max_dd"]*100:.1f}% {r["verdict"]}({r["n_flags"]}) dt={r["runtime_s"]:.0f}s', flush=True)
        else:
            print(f'  ERROR: {r.get("error", "?")}', flush=True)

    print('\nSTAGE 2: Portfolio optimization')
    ok = [r for r in all_results if 'sharpe' in r and r['sharpe'] > 0]
    model_overrides = {}
    if ok:
        best = max(ok, key=lambda x: x['sharpe'])
        print(f'Best Stage 1: {best["config"]} (Sharpe={best["sharpe"]:.4f})')
        cfg_path = os.path.join(RESULTS_DIR, best['config'], 'config.json')
        if os.path.exists(cfg_path):
            with open(cfg_path) as f:
                bc = json.load(f)
            model_overrides = {'gbrt_max_depth': bc['gbrt_max_depth'], 'gbrt_n_estimators': bc['gbrt_n_estimators'], 'gbrt_learning_rate': bc['gbrt_learning_rate']}

    stage2 = []
    for nl in [8, 10, 13, 15]:
        stage2.append((f'pf_n{nl}', {'n_long': nl, 'n_short': nl}))
    for rb in [3, 5, 7, 10]:
        stage2.append((f'pf_rb{rb}', {'rebalance_freq': rb}))
    for lam in [0.3, 0.5, 0.8, 1.0, 2.0]:
        stage2.append((f'pf_lam{lam:.1f}', {'opt_lambda_risk': lam}))
    for sm in [0.0, 0.3, 0.5, 0.7]:
        stage2.append((f'pf_sm{sm:.1f}', {'gbrt_pred_smooth': sm}))
    for bm in [0.05, 0.10, 0.15, 0.25]:
        stage2.append((f'pf_beta{bm:.2f}', {'beta_max_abs': bm}))
    for lw in [0.005, 0.01, 0.02, 0.05]:
        stage2.append((f'pf_lw{int(lw*1000):d}', {'gbrt_label_winsorize': lw}))

    for i, (name, over) in enumerate(stage2):
        full_over = {**model_overrides, **over}
        print(f'[{i+1}/{len(stage2)}] {name}', flush=True)
        r = run_config(name, **full_over)
        all_results.append(r)
        if 'sharpe' in r:
            print(f'  Sharpe={r["sharpe"]:.4f} Ret={r["ann_ret"]*100:.1f}% TO={r["turnover"]:.1f} DD={r["max_dd"]*100:.1f}% {r["verdict"]}({r["n_flags"]}) dt={r["runtime_s"]:.0f}s', flush=True)
        else:
            print(f'  ERROR: {r.get("error", "?")}', flush=True)

    print('\nSTAGE 3: Combo')
    s2 = [r for r in all_results if 'sharpe' in r and r['sharpe'] > 0 and r['config'].startswith('pf_')]
    if len(s2) >= 4:
        def best_of(prefix):
            candidates = [r for r in s2 if prefix in r['config']]
            return max(candidates, key=lambda x: x['sharpe']) if candidates else None
        best_nl = best_of('pf_n')
        best_rb = best_of('pf_rb')
        best_lam = best_of('pf_lam')
        best_sm = best_of('pf_sm')
        best_beta = best_of('pf_beta')
        best_lw = best_of('pf_lw')
        combo = {**model_overrides}
        if best_nl:
            v = int(best_nl['config'].replace('pf_n', '').split('_')[0])
            combo.update({'n_long': v, 'n_short': v})
        if best_rb:
            combo['rebalance_freq'] = int(best_rb['config'].replace('pf_rb', ''))
        if best_lam:
            combo['opt_lambda_risk'] = float(best_lam['config'].replace('pf_lam', ''))
        if best_sm:
            combo['gbrt_pred_smooth'] = float(best_sm['config'].replace('pf_sm', ''))
        if best_beta:
            combo['beta_max_abs'] = float(best_beta['config'].replace('pf_beta', ''))
        if best_lw:
            combo['gbrt_label_winsorize'] = float(best_lw['config'].replace('pf_lw', '')) / 1000
        print(f'Combo: {combo}')
        r = run_config('final_combo', **combo)
        all_results.append(r)
        if 'sharpe' in r:
            print(f'  FINAL: Sharpe={r["sharpe"]:.4f} Ret={r["ann_ret"]*100:.1f}% TO={r["turnover"]:.1f} DD={r["max_dd"]*100:.1f}% {r["verdict"]}({r["n_flags"]}) dt={r["runtime_s"]:.0f}s')

    df = pd.DataFrame(all_results)
    csv_path = os.path.join(RESULTS_DIR, '_summary.csv')
    df.to_csv(csv_path, index=False)
    dt_total = (time.time() - t_total) / 60
    print(f'\nDONE in {dt_total:.1f} min. -> {csv_path}')
    ok2 = df[df['sharpe'].notna() & (df['sharpe'] > 0)].sort_values('sharpe', ascending=False)
    print('\nTOP CONFIGS:')
    for _, row in ok2.head(15).iterrows():
        print(f'  {row["config"]:35s} Sharpe={row["sharpe"]:.4f}  Ret={row["ann_ret"]*100:.1f}%  TO={row["turnover"]:.1f}  DD={row["max_dd"]*100:.1f}%  {row["verdict"]}({row["n_flags"]}f)')
    return 0

if __name__ == '__main__':
    sys.exit(main())
