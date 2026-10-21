#!/usr/bin/env python3
"""HUNT_CRYPTO2 round 1 — family (d) adversarial robustness: BTC-MA gate on champion.

Initial hit: MA50 scale0.5 -> dSR +0.230. Questions before any pass claim:
 R1 timing: BTC kline closes 3h after NYSE close. Gate flipped at close t applied to
    champion ret_{t+1} => does it survive an extra day of lag? (lag2)
 R2 costs: champion is ALREADY net of its own costs; gate flips create extra turnover in the
    UNDERLYING book. Charge a full round-trip 6.4bps on every gate-state change (conservative
    upper bound since partial closes would cost less).
 R3 specificity: is BTC the signal, or does ANY risk proxy (SPY MA, BTC ret, trailing BTC vol)
    give the same lift? If SPY-MA matches it, this is a beta gate, not crypto alpha.
 R4 stability: recent years (2023-26) — prior satellite died on 2025-26 detriment. Yearly table
    + split halves + leave-1-year-out dSR.
 R5 plateau: MA x scale grid; chosen point must sit on a plateau.
 R6 scramble: position-lag scramble on the GATE series (the actual tradable object).
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np, pandas as pd
from bt import engine, metrics
import bt.gates as bgates

ROOT = "/Users/daxu/software/world-trader"
CHAMP = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0]
BTC = pd.read_csv(f"{ROOT}/tools/quant/data/more_crypto/BTC.csv",
                  index_col=0, parse_dates=True)['close'].astype(float)
SPY = pd.read_csv(f"{ROOT}/tools/quant/data/twelve_big/SPY.csv",
                  index_col=0, parse_dates=True)['close'].astype(float)
champ_sr = metrics.sharpe_d(CHAMP)
IDX = CHAMP.index


def gate_series(px, ma, scale, extra_lag=0):
    state = (px > px.rolling(ma).mean()).astype(float)
    g = (1 - scale) * state + scale                      # on=1.0, off=scale
    g = g.reindex(IDX.union(g.index)).ffill().reindex(IDX)
    g = g.shift(1 + extra_lag).fillna(1.0)               # T+1 (+ extra lag for 3h-close honesty)
    return g


def gated_stats(g, name='', cost_flip=False):
    gated = CHAMP * g
    if cost_flip:
        flip = (g.diff().abs() > 0).astype(float)        # each gate change: partial liquidation
        gated = gated - flip * (g.diff().abs().fillna(0) * 6.4 / 1e4)
    sr = metrics.sharpe_d(gated)
    h1, h2 = metrics.half_split(gated)
    neg, worst = metrics.neg_years(gated)
    corr = bgates.corr_to(CHAMP, gated)
    return dict(name=name, sr=sr, dsr=sr - champ_sr, h1=h1, h2=h2, neg=neg, worst=worst,
                corr=corr, ann=metrics.ann_geo(gated))


print(f"champion SR={champ_sr:.4f} n={len(CHAMP)} {CHAMP.index[0].date()}->{CHAMP.index[-1].date()}")
print(f"BTC span {BTC.index[0].date()}->{BTC.index[-1].date()} "
      f"champ days covered={len(gate_series(BTC, 50, 0.5).dropna())}")

print("\n=== R5 plateau: dSR grid (rows=MA, cols=scale) ===")
grid = {}
for ma in [20, 50, 100, 150, 200]:
    for sc in [0.3, 0.5, 0.7, 0.9]:
        g = gate_series(BTC, ma, sc)
        grid[(ma, sc)] = gated_stats(g)['dsr']
        print(f"  MA={ma:4d} scale={sc:.1f}  dSR={grid[(ma,sc)]:+.3f}")
print(f"  (plateau if neighbors within 20% of peak dSR around chosen point)")

print("\n=== R1 lag robustness (MA50 sc0.5) ===")
for lag in [0, 1, 2, 3]:
    st = gated_stats(gate_series(BTC, 50, 0.5, extra_lag=lag), f'lag{lag}')
    print(f"  extra_lag={lag}: SR={st['sr']:.3f} dSR={st['dsr']:+.3f} H1={st['h1']:.2f} H2={st['h2']:.2f}")

print("\n=== R2 cost of gate flips (MA50 sc0.5; full 6.4bps round-trip on state change) ===")
g = gate_series(BTC, 50, 0.5)
n_flip = int((g.diff().abs() > 0).sum())
print(f"  gate flips 2017-2026: n={n_flip} ({n_flip/9.5:.0f}/yr); "
      f"mean |gate change|={g.diff().abs().mean():.3f}")
st = gated_stats(g, 'costed', cost_flip=True)
print(f"  with flip costs: SR={st['sr']:.3f} dSR={st['dsr']:+.3f}")

print("\n=== R3 specificity: BTC-MA vs generic risk proxies (all MA50 sc0.5) ===")
btc_ret = BTC.pct_change().reindex(IDX.union(BTC.index)).ffill().reindex(IDX)
btc_vol = BTC.pct_change().rolling(20).std().reindex(IDX.union(BTC.index)).ffill().reindex(IDX)
proxies = {
    'BTC>MA50 (ours)': gate_series(BTC, 50, 0.5),
    'SPY>MA50': gate_series(SPY.dropna(), 50, 0.5),
    'BTC>MA200': gate_series(BTC, 200, 0.5),
    'BTC 20d vol gate': (1 - 0.5) * (btc_vol < btc_vol.expanding(100).median()).astype(float) + 0.5,
    'always-on (no gate)': pd.Series(1.0, index=IDX),
}
for nm, gp in proxies.items():
    st = gated_stats(gp, nm)
    print(f"  {nm:22s} SR={st['sr']:.3f} dSR={st['dsr']:+.3f} negyr={st['neg']:2d} "
          f"worst={st['worst']*100:5.1f}% corr={st['corr']:.3f}")

print("\n=== R4 yearly (MA50 sc0.5 gated) + contribution by year ===")
gated = CHAMP * gate_series(BTC, 50, 0.5)
yr = pd.DataFrame({'champ': CHAMP, 'gated': gated}).groupby(
    lambda d: d.year).apply(lambda x: pd.Series({
        'champ': metrics.ann_geo(x['champ']), 'gated': metrics.ann_geo(x['gated'])}))
yr['dAnn'] = yr['gated'] - yr['champ']
print(yr.map(lambda v: f"{v*100:+.1f}%").to_string())

print("\n=== R6 scramble on gate series (MA50 sc0.5): p = P(roll-lag SR >= real) ===")
g = gate_series(BTC, 50, 0.5)
live = gated[g != 1.0].index[0]
r_sub = gated[gated.index >= live]
g_sub = g[g.index >= live]
p, real = bgates.scramble_positions(g_sub.values, r_sub.values, side=0, n=200)
print(f"  real SR={real:.3f}  scramble p={p:.3f}  (gate: p<=0.05)")

print("\n=== R7 anchor: what does the gate DO? exposure stats ===")
on = (g == 1.0)
print(f"  days on={on.sum()} off={(~on).sum()} ({on.mean()*100:.0f}% on)")
for nm, mask in [('on', on), ('off', ~on)]:
    r = CHAMP[mask]
    print(f"  champ on {nm}-days: mean={r.mean()*1e4:+.1f}bp/day n={len(r)}")
