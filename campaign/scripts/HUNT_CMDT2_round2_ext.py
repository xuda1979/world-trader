#!/usr/bin/env python3
"""HUNT_CMDT2 ROUND 2 follow-ups:
 PLATEAU: fine grid for the COT-gated momentum family around its best cell (9m k2 thr0.2) —
          gate (b) requires the chosen param to sit on a plateau (neighbors >= 80% of peak).
 ABLATION-VALUE: does the crowded gate add value ACROSS the grid (paired deltas), not just at
          one lucky cell?
 EXT-F: UNG decay harvest — both seasonal legs were negative (winter -44%/yr, summer -10%/yr),
          so test the constant SHORT UNG book the seasonal info implies (charter item (c)
          adjacent; honest check, borrow already in net_of).
 EXT-G: COT gate on the CPER trend + ratio books (positioning-confirmed copper), since copper
          has its own COT market and (b) is a trend book.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
import HUNT_CMDT2_round2 as M
import HUNT_CMDT2_round1 as H


def main():
    px = M.px_frame(M.COT_ETFS)
    R = px.pct_change()

    print('=== PLATEAU: COT-gated momentum fine grid months x k x thr ===')
    grid = {}
    for months in [6, 9, 12]:
        for topk in [2, 3]:
            for thr in [0.0, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4]:
                net, We, _, _ = M.run_cot_gated_momentum(px, R, months=months, topk=topk,
                                                         hold=3, thr=thr)
                res = M.evaluate(f'P {months}m k{topk} thr{thr}', net, We, R, verbose=False)
                grid[(months, topk, thr)] = res['sr']
                print(f"  {months}m k{topk} thr{thr}: SR={res['sr']:.3f}")

    # plateau at the family peak
    peak = max(v for v in grid.values() if np.isfinite(v))
    pk = [k for k, v in grid.items() if v == peak][0]
    print(f"\npeak SR={peak:.3f} at {pk}")
    mo, k, th = pk
    neigh = []
    for dmo, dk, dth in [(0, 0, 0.05), (0, 0, -0.05), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0),
                         (3, 0, 0), (-3, 0, 0)]:
        key = (mo + dmo, k + dk, round(th + dth, 2))
        if key in grid and np.isfinite(grid[key]):
            neigh.append((key, grid[key]))
    n_ok = sum(1 for _, v in neigh if v >= 0.8 * peak)
    print(f"plateau: {n_ok}/{len(neigh)} neighbors >= 80% of peak ({0.8*peak:.3f})")
    for key, v in sorted(neigh, key=lambda x: -x[1]):
        print(f"  {key}: {v:.3f} {'OK' if v >= 0.8*peak else 'FAIL'}")

    print('\n=== ABLATION-VALUE: gate ON vs OFF, paired across the grid ===')
    wins = ties = losses = 0
    for months in [6, 9, 12]:
        for topk in [2, 3]:
            off = grid[(months, topk, 0.0)]
            best_gated = max(grid[(months, topk, t)] for t in [0.1, 0.15, 0.2, 0.25, 0.3, 0.4])
            d = best_gated - off
            wins += d > 0.05
            losses += d < -0.05
            ties += abs(d) <= 0.05
            print(f"  {months}m k{topk}: ungated={off:.3f} best-gated={best_gated:.3f} delta={d:+.3f}")
    print(f"  gate helps on {wins}/6 cells, hurts {losses}, ties {ties}")

    print('\n=== EXT-F: UNG constant SHORT (decay harvest), vol-scaled ===')
    pxg = M.px_frame(['UNG'])
    Rg = pxg.pct_change()
    vol = pxg['UNG'].pct_change().rolling(60, min_periods=40).std() * np.sqrt(252)
    scale = (0.10 / vol.replace(0, np.nan)).clip(upper=3.0).shift(1)
    scale = scale.where(vol.shift(1).notna(), 0.0).fillna(0.0)
    for gross in [1.0]:
        W = pd.DataFrame(0.0, index=pxg.index, columns=['UNG'])
        W['UNG'] = -scale * gross
        net, We, _ = M.net_of(W, Rg)
        M.evaluate(f'EXT-F UNG short-only vscale', net, We, Rg)
        # unscaled variant
        W2 = pd.DataFrame({'UNG': -1.0}, index=pxg.index)
        net2, We2, _ = M.net_of(W2, Rg, vt=False)
        M.evaluate(f'EXT-F UNG short-only raw', net2, We2, Rg)
        # long-only for reference
        W3 = pd.DataFrame({'UNG': 1.0}, index=pxg.index)
        net3, We3, _ = M.net_of(W3, Rg, vt=False)
        M.evaluate(f'EXT-F UNG long-only raw (ref)', net3, We3, Rg)

    print('\n=== EXT-G: COT-crowded gate on copper trend + CPER/GLD ratio ===')
    pxc = M.px_frame(['CPER'])
    Rc = pxc.pct_change()
    pxr = M.px_frame(['CPER', 'GLD'])
    Rr = pxr.pct_change()
    cotg_c = M.cot_gate_series('copper', thr=0.2).reindex(pxc.index).ffill().fillna(0.0)
    cotg_r = M.cot_gate_series('copper', thr=0.2).reindex(pxr.index).ffill().fillna(0.0)
    for win in [126, 252]:
        net, We, _, W = M.run_cper_trend(pxc, Rc, win=win)
        Wg = W.mul(cotg_c, axis=0)
        netg, Weg, _ = M.net_of(Wg, Rc)
        M.evaluate(f'EXT-G cper trend {win}d gate0.2', netg, Weg, Rc)
    for win in [126, 252]:
        net, We, _, W = M.run_ratio_momentum(pxr, Rr, win=win)
        g2 = pd.DataFrame({'CPER': cotg_r, 'GLD': cotg_r})
        Wg = W.mul(g2, axis=0)
        netg, Weg, _ = M.net_of(Wg, Rr)
        M.evaluate(f'EXT-G ratio CPER/GLD {win}d gate0.2', netg, Weg, Rr)

    print('\n=== EXT-H: gate thr robustness on 9m k2 (hold 1/2/3) ===')
    for hold in [1, 2, 3]:
        for thr in [0.1, 0.15, 0.2, 0.25, 0.3]:
            net, We, _, _ = M.run_cot_gated_momentum(px, R, months=9, topk=2, hold=hold, thr=thr)
            res = M.evaluate(f'EXT-H 9m k2 h{hold} thr{thr}', net, We, R, verbose=False)
            print(f"  h{hold} thr{thr}: SR={res['sr']:.3f} H1={res['h1']:.2f} H2={res['h2']:.2f}")


if __name__ == '__main__':
    main()
