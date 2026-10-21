#!/usr/bin/env python3
"""CAMP_SHORT R4: re-run R1's MHX borrow-impact + re-run the library L_S books
under the FIXED strat_ls_equity (neg branch no longer flips shorts long).

Part A — MHX (charter: "re-run YOUR R1 MHX impact numbers under the fixed code
and state what changed"):
  MHX's short leg is built at the RETURN level in xgb_multi_horizon.py:143
  (perday = (los - sis) - 2*cost; bottom-K EW subtracted) — sign-correct, and the
  module imports nothing from hedge_fund_strats.strat_ls_equity. The fix is
  therefore a no-op for MHX; we PROVE it: (A0) AST import audit; (A1) rebuild the
  MHX blend from the surviving prediction pickle and byte-validate against the
  committed sleeve CSV (tol 2e-4) — proving the committed bytes do not depend on
  the buggy code path; (A2) re-price the R1 borrow-tier ladder on the MEASURED
  short-notional stream (K/n * vol-target scale), and restate the champion
  impact (MHX is not in the champion pool).

Part B — library L_S books: the four L_S_* books WERE the flip bug's products
  (R3 census: measured |short| = 0.0000 in the committed bytes). Under the fix
  they regain real short legs. Report per book: committed (buggy) vs fixed
  rebuild ann/SR/MDD, mean |short|/NAV, borrow drag at EASY/MEDIUM/HARD, and the
  NONE-tier drop scenario. Also re-derive the volmanaged variant.

Every number is measured from artifacts on disk. No committed file is modified.
Writes: work_r4/r4_impact.json (this script is the repro).
"""
import ast
import json
import os
import pickle
import sys

import numpy as np
import pandas as pd

ROOT = '/Users/daxu/software/world-trader'
HERE = f'{ROOT}/campaign/agents/chief/coord/CAMP_SHORT/work_r4'
LIB = f'{ROOT}/campaign/results/sleeve_library'
HFS = f'{ROOT}/tools/quant/hedge_fund_strats'
for p in (ROOT, f'{ROOT}/campaign', f'{ROOT}/campaign/bt', f'{ROOT}/tools/quant',
          HFS, f'{HERE}/../work_r3'):
    if p not in sys.path:
        sys.path.insert(0, p)

from lib_census import panel_12big, rets_12big, engine_run, RENET_TOL  # noqa: E402
from bt.shortability import TIERS, ANN, shortability_pregate  # noqa: E402

RES = {}


def perf(r):
    r = pd.Series(r).dropna()
    if len(r) < 20 or r.std() == 0:
        return dict(ann_pct=None, sr=None, mdd_pct=None, n=int(len(r)))
    eq = (1 + r).cumprod()
    ann = (1 + r).prod() ** (252 / len(r)) - 1
    sr = float(r.mean() / r.std() * np.sqrt(252))
    mdd = float((eq / eq.cummax() - 1).min())
    return dict(ann_pct=round(ann * 100, 4), sr=round(sr, 4),
                mdd_pct=round(mdd * 100, 4), n=int(len(r)))


def committed_stream(name, d=LIB):
    df = pd.read_csv(f'{d}/{name}.csv', index_col=0, parse_dates=True)
    return pd.to_numeric(df.iloc[:, 0], errors='coerce').dropna()


def inner_max_diff(a, b):
    j = pd.concat([a.rename('c'), b.rename('n')], axis=1, join='inner').dropna()
    if len(j) < 200:
        return float('nan'), int(len(j))
    return float((j.c - j.n).abs().max()), int(len(j))


# ================================================================= PART A
def part_a():
    out = {}
    print('=' * 72)
    print('PART A — MHX under the fixed strat_ls_equity')
    print('=' * 72)

    # ---- A0: AST import audit
    src = open(f'{ROOT}/tools/quant/bigmove/xgb_multi_horizon.py').read()
    mods = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            mods |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            mods.add(node.module or '')
    uses_strat_ls = any('strat_ls' in m for m in mods)
    uses_hfs = any('hedge_fund_strats' in m for m in mods)
    print(f'[A0] xgb_multi_horizon.py imports: {sorted(mods)}')
    print(f'[A0] imports strat_ls_equity: {uses_strat_ls}; hedge_fund_strats: {uses_hfs}')
    out['A0_import_audit'] = dict(imports=sorted(mods),
                                  imports_strat_ls_equity=uses_strat_ls,
                                  imports_hedge_fund_strats=uses_hfs)

    # ---- A1: rebuild blend from each candidate prediction cache; validate vs committed
    committed = committed_stream('MHX_multihorizon_xgb',
                                 d=f'{ROOT}/campaign/agents/COORD/sleeves')
    HORIZONS = [1, 5, 21]
    K, COST, VT = 10, 0.0006, 0.13

    def daily_longshort(frame, pred, H):
        fw = frame.copy()
        fw['pred'] = pred
        fw['fwd'] = fw[f'ret_{H}']
        fw = fw[np.isfinite(fw['pred']) & np.isfinite(fw['fwd'])]
        rows, sn = [], []
        for date, g in fw.groupby('date'):
            n = len(g)
            if n < 2 * K + 2:
                continue
            g = g.sort_values('pred', ascending=False)
            # book convention (xgb_multi_horizon.py:141-143): EW mean of top-K fwd
            # minus EW mean of bottom-K fwd => each name weight = 1/K of NAV =>
            # long notional 1.0, SHORT notional 1.0 (gross 2.0, dollar-neutral).
            rows.append((date, (g['fwd'].iloc[:K].mean() - g['fwd'].iloc[n - K:].mean()) - 2 * COST))
            sn.append((date, 1.0))
        return (pd.Series(dict(rows)).sort_index(),
                pd.Series(dict(sn)).sort_index())

    def vol_scale(ds):
        rv = ds.rolling(20, min_periods=10).std().shift(1) * np.sqrt(252)
        return (VT / rv).clip(upper=3.0, lower=0.0).fillna(1.0)

    caches = ['horizon_preds_20y.pkl', 'horizon_preds_20y_f5.pkl',
              'horizon_preds_20y_f5fix.pkl', 'horizon_preds_20y_f6.pkl']
    best = None
    for c in caches:
        p = f'{ROOT}/tools/quant/bigmove/data/{c}'
        if not os.path.exists(p):
            continue
        with open(p, 'rb') as fh:
            d = pickle.load(fh)
        frame = d['frame'].copy()
        frame['date'] = pd.to_datetime(frame['date'])
        alld = pd.bdate_range(frame['date'].min(), frame['date'].max())
        blend = None
        for H in HORIZONS:
            ds, sn = daily_longshort(frame, d['preds'][H], H)
            vt = (ds * vol_scale(ds)).reindex(alld, fill_value=0.0)
            blend = vt if blend is None else blend + vt
        blend /= len(HORIZONS)
        blend = blend[blend.index >= '2008-09-02']
        md, n = inner_max_diff(committed, blend.dropna())
        print(f'[A1] cache {c}: max|diff| vs committed = {md:.3e} (n={n})')
        if best is None or (md == md and md < best[1]):
            best = (c, md, n, blend)
    cache, md, n, blend = best
    ok = md == md and md <= RENET_TOL
    print(f'[A1] generator-of-record cache: {cache}  byte-valid: {ok}')
    out['A1_rebuild_validation'] = dict(cache=cache, max_diff=md, n=n,
                                        valid_at_2e4=ok,
                                        committed='COORD/sleeves/MHX_multihorizon_xgb.csv')

    # ---- A2: R1 borrow-tier ladder on measured short notional
    with open(f"{ROOT}/tools/quant/bigmove/data/{cache}", 'rb') as fh:
        d = pickle.load(fh)
    frame = d['frame'].copy()
    frame['date'] = pd.to_datetime(frame['date'])
    alld = pd.bdate_range(frame['date'].min(), frame['date'].max())
    sn_mean = None
    for H in HORIZONS:
        ds, sn = daily_longshort(frame, d['preds'][H], H)
        sc = vol_scale(ds)
        sn_vt = (sn.reindex(sc.index) * sc).reindex(alld, fill_value=0.0)
        sn_mean = sn_vt if sn_mean is None else sn_mean + sn_vt
    sn_mean = (sn_mean / len(HORIZONS))
    sn_mean = sn_mean[sn_mean.index >= '2008-09-02']
    mean_sn = float(sn_mean.mean())
    ladder = {t: round(mean_sn * rate * 100, 4) for t, rate in TIERS.items() if rate}
    print(f'[A2] mean |short|/NAV (vol-targeted, live window) = {mean_sn:.6f}')
    print(f'[A2] borrow drag if priced at tier: {ladder} pct/yr')
    print(f'[A2] champion impact: MHX NOT in champion pool (removed_after_audit) -> 0.000pp')
    out['A2_borrow_ladder'] = dict(mean_short_frac=mean_sn, drag_pct_per_yr=ladder,
                                   base_R1_flag='~75bps/yr borrow-tier uplift (R1 FINDINGS)',
                                   champion_impact_pp=0.0,
                                   champion_note='MHX removed from champion (failed retrain); '
                                                 'champion stock-loan slots already priced in R2/R3')
    out['A_fix_changes_mhx'] = ('NO-OP: strat_ls_equity not in MHX import graph; committed '
                                'MHX bytes reproduced from the XGB prediction cache '
                                f'(max|diff| {md:.3e}) without touching strat_ls_equity.')
    return out, dict(cache=cache, blend=blend)


# ================================================================= PART B
def part_b():
    out = {}
    print('=' * 72)
    print('PART B — library L_S books: committed (buggy) vs FIXED rebuild')
    print('=' * 72)
    from hedge_fund_strats.strat_ls_equity import compute_ls_signals
    pr, rt = panel_12big(), rets_12big()
    W0 = compute_ls_signals(pr, rt, n_long=30, n_short=30)   # shorts NEGATIVE
    W0b = compute_ls_signals(pr, rt, n_long=40, n_short=10)
    books = {'L_S_130_30': (W0, 1.6, 0.625), 'L_S_120_20': (W0b, 1.2, 0.833),
             'L_S_Market_Neutral': (W0, 2.0, 0.0), 'L_S_Dollar_Neutral': (W0, 2.0, 0.0)}
    COST_ERAS = (12.0 / 1e4, 6.0 / 1e4)

    def book_weights(W0v, gross, net, fixed):
        ls_, ss_ = gross * (1 + net) / 2, gross * (1 - net) / 2
        pos, neg = W0v.clip(lower=0.0), W0v.clip(upper=0.0)
        short_mult = (+ss_) if fixed else (-ss_)   # fixed keeps negatives; bug flipped to +
        return (pos.div(pos.sum(axis=1).replace(0, np.nan), axis=0).mul(ls_, axis=0).fillna(0.0)
                + neg.div(neg.abs().sum(axis=1).replace(0, np.nan), axis=0)
                .mul(short_mult, axis=0).fillna(0.0))

    for name, (W0v, gross, net) in books.items():
        rec = {}
        # committed bytes vs a buggy-sign replication (provenance re-check today)
        W_bug = book_weights(W0v, gross, net, fixed=False)
        best_bug = None
        for cf in COST_ERAS:
            r, _ = engine_run(pr, W_bug, 21, cost_frac=cf)
            md, n = inner_max_diff(committed_stream(name), r.dropna())
            if best_bug is None or (md == md and md < best_bug[0]):
                best_bug = (md, n, cf, r.dropna())
        rec['committed_provenance'] = dict(replicated_max_diff=best_bug[0], n=best_bug[1],
                                           cost_frac=best_bug[2], tol=RENET_TOL,
                                           byte_valid=best_bug[0] <= RENET_TOL)
        # fixed-sign rebuild
        W_fix = book_weights(W0v, gross, net, fixed=True)
        sf_fix = (-W_fix.clip(upper=0.0)).sum(axis=1)
        best_fix = None
        for cf in COST_ERAS:
            r, _ = engine_run(pr, W_fix, 21, cost_frac=cf)
            md, n = inner_max_diff(committed_stream(name), r.dropna())
            if best_fix is None or (md == md and md < best_fix[0]):
                best_fix = (md, n, cf, r.dropna())
        r_fix = best_fix[3]
        rec['fixed_vs_committed'] = dict(max_diff=best_fix[0], n=best_fix[1],
                                         cost_frac=best_fix[2])
        rec['committed_perf'] = perf(committed_stream(name))
        rec['fixed_perf'] = perf(r_fix)
        rec['fixed_mean_short_frac'] = float(sf_fix.mean())
        rec['buggy_mean_short_frac'] = float((-W_bug.clip(upper=0.0)).sum(axis=1).mean())
        # borrow pricing on the FIXED book (it charged zero borrow in the library)
        rec['fixed_borrow_drag_pct_per_yr'] = {
            t: round(rec['fixed_mean_short_frac'] * rate * 100, 4)
            for t, rate in TIERS.items() if rate}
        # NONE-tier drop scenario: shorts dropped, longs re-levered to preserve gross
        tier_map = {c: 'NONE' for c in W_fix.columns}
        W_drop, _, info = shortability_pregate(W_fix, tier_map)
        r_drop = None
        for cf in COST_ERAS:
            r, _ = engine_run(pr, W_drop, 21, cost_frac=cf)
            r_drop = r.dropna()
            break
        rec['none_drop_perf'] = perf(r_drop)
        print(f"\n[{name}] committed {rec['committed_perf']} ")
        print(f"[{name}] fixed     {rec['fixed_perf']}  mean|short|={rec['fixed_mean_short_frac']:.4f}")
        print(f"[{name}] borrow drag (EASY/MEDIUM/HARD): {rec['fixed_borrow_drag_pct_per_yr']}")
        out[name] = rec

    # volmanaged variant = ex-post 21d rescale (cap 2.0) of the 130/30 stream
    r130 = out['L_S_130_30']
    rec = {}
    raw_fixed, _ = engine_run(pr, book_weights(W0, 1.6, 0.625, fixed=True), 21,
                              cost_frac=r130['fixed_vs_committed']['cost_frac'])
    rv = raw_fixed.rolling(21).std() * np.sqrt(252)
    sc = (0.20 / rv.replace(0, np.nan)).clip(upper=2.0)
    r2 = (raw_fixed * sc.shift(1)).dropna()
    rec['fixed_perf'] = perf(r2)
    raw_bug, _ = engine_run(pr, book_weights(W0, 1.6, 0.625, fixed=False), 21,
                            cost_frac=r130['committed_provenance']['cost_frac'])
    rec['committed_perf'] = perf(committed_stream('L_S_130_30_volmanaged'))
    rec['fixed_vs_committed_max_diff'], rec['n'] = inner_max_diff(
        committed_stream('L_S_130_30_volmanaged'), r2)
    print(f"\n[L_S_130_30_volmanaged] committed {rec['committed_perf']}")
    print(f"[L_S_130_30_volmanaged] fixed     {rec['fixed_perf']}")
    out['L_S_130_30_volmanaged'] = rec
    return out


if __name__ == '__main__':
    a, aux = part_a()
    RES['part_A_mhx'] = a
    RES['part_B_ls_books'] = part_b()
    RES['conventions'] = dict(
        fix='strat_ls_equity.py:139 neg / |neg|.sum() * short_scale  (shorts stay NEGATIVE)',
        docstring_contract='core.py BacktestEngine.run: target_weights '
                           '"(positive=long, negative=short, sum=net exposure)"; module '
                           'docstring: 130/30 = 130% long + 30% short',
        tol=RENET_TOL)
    os.makedirs(HERE, exist_ok=True)
    with open(f'{HERE}/r4_impact.json', 'w') as fh:
        json.dump(RES, fh, indent=1, default=str)
    print('\nWROTE', f'{HERE}/r4_impact.json')
