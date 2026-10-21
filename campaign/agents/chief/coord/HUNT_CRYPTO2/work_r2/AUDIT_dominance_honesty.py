#!/usr/bin/env python3
"""R2 honesty stack on the BTC-dominance-proxy gate family (charter idea a2).
Components: prefix no-lookahead, T+1 extra-lag 0..3, flip costs (in gate_metrics),
scramble 200x (both metrics), param plateau (MA axis x scale axis on the CLAIMED metrics),
WHERE-does-the-gain-come-from attribution (on/off-day means+vols, off-episode PnL,
yearly dAnn, gated DD depth at 2018-06, n-episodes), and crypto-specificity check
(alt-basket-vs-BTC inverted = same info? SPY-MA generic gate comparison is R1 (d) ref).
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_CRYPTO2/work_r2")
import numpy as np, pandas as pd
from bt import metrics
from HUNT_CRYPTO2_round2_lib import (load_env, compare, binary_gate, gate_metrics, COST)

env = load_env()
CHAMP, IDX = env['CHAMP'], env['IDX']
dom = (env['BTCi'] / env['alt_px_i']).dropna()

print(f"champ: SR={env['CHAMP_SR']:.4f} ann={env['CHAMP_ANN']*100:.2f}% mdd={env['CHAMP_MDD']*100:.2f}%")
print(f"champ 2008 episode DD: {metrics.max_dd(CHAMP.loc[:'2017'])*100:.2f}%  "
      f"(gate warmup=1.0 pre-2018 -> this is the dMDD floor; cap = "
      f"{(metrics.max_dd(CHAMP.loc[:'2017']) - env['CHAMP_MDD'])*100:.2f}pp)")


def cond_dom(ma):
    return compare(dom, '>', dom.rolling(ma).mean())


def prefix_probe(ma, sc, cut="2023-06-30"):
    full, _ = binary_gate(cond_dom(ma), sc)
    dom_t = dom[dom.index < pd.Timestamp(cut)]
    trunc, _ = binary_gate(compare(dom_t, '>', dom_t.rolling(ma).mean()), sc)
    j = pd.concat([full.rename('a'), trunc.rename('b')], axis=1).loc[:cut].fillna(1.0)
    same = bool(np.allclose(j['a'], j['b']))
    print(f"  prefix-no-lookahead ma{ma} sc{sc} identical to {cut}: {same}")
    assert same


def scramble(g):
    live = (g < 1.0).idxmax() if (g < 1.0).any() else g.index[-1]
    idx = g.index[g.index >= live]
    rv = CHAMP.reindex(idx).fillna(0.0)
    gv = g.reindex(idx).fillna(1.0)
    real_sr, real_mdd = metrics.sharpe_d(gv * rv), metrics.max_dd(gv * rv)
    rng = np.random.default_rng(7)
    cs = cm = 0
    for _ in range(200):
        s = np.roll(gv.values, rng.integers(10, len(rv) - 10))
        b = pd.Series(s * rv.values, index=idx)
        cs += metrics.sharpe_d(b) >= real_sr
        cm += metrics.max_dd(b) >= real_mdd
    return cs / 200, cm / 200, real_sr, real_mdd


print("\n=== (1) fuller dominance grid: MA x scale on dSR / dAnn / dMDD ===")
grid = {}
for ma in [20, 50, 100, 150, 200]:
    for sc in [0.3, 0.5, 0.7, 0.9]:
        g, _ = binary_gate(cond_dom(ma), sc)
        m = gate_metrics(g, env)
        grid[(ma, sc)] = m
        print(f"  ma{ma:3d} sc{sc:.1f}: dSR={m['d_sr']:+.3f} dAnn={m['d_ann']*100:+7.3f}pp "
              f"dMDD={m['d_mdd']*100:+.3f}pp off%={m['off']*100:3.0f} flips={m['n_flip']}")

print("\n=== (2) plateau on the CLAIMED metrics ===")
for metric in ['d_sr', 'd_mdd']:
    for ma in [20, 50, 100, 150, 200]:
        scs = [0.3, 0.5, 0.7, 0.9]
        vals_sc = {s: grid[(ma, s)][metric] for s in scs}
        peak = max(vals_sc.values())
        ok = all(v >= 0.8 * peak for v in vals_sc.values())
        mas = [20, 50, 100, 150, 200]
        i = mas.index(ma)
        nb = [m for m in (mas[i - 1] if i > 0 else None, mas[i + 1] if i + 1 < 5 else None) if m]
        v_nb = {m2: grid[(m2, 0.5)][metric] for m2 in nb}
        peak2 = max(grid[(m2, 0.5)][metric] for m2 in mas)
        ok2 = all(v >= 0.8 * peak2 for v in v_nb.values())
        print(f"  ma{ma:3d}: scale-axis plateau({metric})={ok} {  {k: round(v,3) for k,v in vals_sc.items()} } | "
              f"MA-axis nb(sc.5)={ok2} { {k: round(v,3) for k,v in v_nb.items()} } (family peak {peak2:.3f})")

print("\n=== (3) honesty stack on the three nominal passers ===")
for ma in [20, 50, 100]:
    sc = 0.5
    g, n_nan = binary_gate(cond_dom(ma), sc)
    m = gate_metrics(g, env)
    print(f"\n--- dom_ma{ma}_sc{sc}: dSR={m['d_sr']:+.3f} dAnn={m['d_ann']*100:+.3f}pp "
          f"dMDD={m['d_mdd']*100:+.3f}pp (warmup NaN days={n_nan}) ---")
    prefix_probe(ma, sc)
    print("  extra-lag 0..3 (3h-late BTC close):")
    for lag in [0, 1, 2, 3]:
        g2, _ = binary_gate(cond_dom(ma), sc, extra_lag=lag)
        m2 = gate_metrics(g2, env)
        print(f"    lag{lag}: dSR={m2['d_sr']:+.3f} dAnn={m2['d_ann']*100:+.3f}pp "
              f"dMDD={m2['d_mdd']*100:+.3f}pp")
    p_sr, p_mdd, rsr, rmdd = scramble(g)
    print(f"  scramble200x(live span): real SR={rsr:.3f} p_SR={p_sr:.3f} | "
          f"real MDD={rmdd*100:.2f}% p_MDD={p_mdd:.3f}")

    # attribution: on/off-day champ stats
    off = g < 1.0
    on = g >= 1.0
    live = g.index[g.index >= (off.idxmax() if off.any() else g.index[-1])]
    o, n = CHAMP.reindex(live)[off.reindex(live).fillna(False)], CHAMP.reindex(live)[on.reindex(live).fillna(True)]
    print(f"  attribution: off n={len(o)} mean={o.mean()*1e4:+.1f}bp/d vol={o.std()*100:.2f}% | "
          f"on n={len(n)} mean={n.mean()*1e4:+.1f}bp/d vol={n.std()*100:.2f}%")

    # off-episodes and the champ PnL inside each
    of = off.reindex(live).fillna(False).astype(int)
    eps = (of.diff() != 0).cumsum()[of == 1]
    pnl = CHAMP.reindex(live).groupby(eps).apply(lambda x: (1 + x).prod() - 1)
    lens = of.groupby(eps).sum()[of.groupby(eps).sum() > 0]
    print(f"  off-episodes n={len(pnl)}; champ cum-PnL inside episodes: "
          f"{ {int(k): f'{v*100:+.1f}%' for k, v in pnl.items()} }")
    print(f"  episode lens(d): min={lens.min()} med={int(lens.median())} max={lens.max()}")
    tot = pnl.sum()
    print(f"  sum of champ PnL over off-episodes = {tot*100:+.1f}%  (negative => gate avoids bad PnL)")

    # gated DD depth around 2018-06 vs floor
    eq = (1 + m['costed']).cumprod()
    dd = eq / eq.cummax() - 1
    w18 = dd.loc['2018':'2018']
    print(f"  gated full-window MDD={dd.min()*100:.2f}% @{dd.idxmin().date()} | "
          f"gated DD trough in 2018: {w18.min()*100:.2f}% @{w18.idxmin().date()}")

    yr = pd.DataFrame({'c': CHAMP, 'g': m['costed']}).groupby(lambda d: d.year).apply(
        lambda x: pd.Series({'dAnn': metrics.ann_geo(x['g']) - metrics.ann_geo(x['c'])}))
    print("  yearly dAnn: " + " ".join(f"{y}:{v*100:+.1f}" for y, v in yr['dAnn'].items()))
