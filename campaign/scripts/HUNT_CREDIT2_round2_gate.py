#!/usr/bin/env python3
"""HUNT_CREDIT2 round 2, part 2: validation battery.

1. Sign-flip DIAGNOSTIC on (a)(b)(c): are the negatives an artifact of signal sign? (report
   only — post-hoc sign inversion is data-snooping and NOT adoptable; it is run to make the
   negative airtight: if the flipped book also fails SR>=1.0, the idea is dead both ways).
2. (d) HY-stress gate deep-dive — the only live candidate (delta +0.198 SR):
     - plateau over N x z_thr grid (contract gate b), delta as the objective
     - era split of the delta (2008-12 / 2013-19 / 2020+): is it one-regime or persistent?
     - scramble 200x: permute gate VALUES across dates (count preserved, timing broken),
       recompute delta; p = P(delta_scr >= delta_real)
     - cost bound of de-gearing (weights unknown -> upper bound at GEAR16 gross)
     - BAMLH0A0HYM2 (true HY OAS) on its 2023+ overlap: noted, unjudgeable by design
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
from bt import metrics
import bt.gates as bgates
import HUNT_CREDIT2_round2 as cr2

CHAMP = cr2.CHAMP
GEAR = 1.6          # champion gross (GEAR16), upper bound for |sum w|


def delta_of(gate):
    ov, gg = cr2.overlay_on_champion(gate)
    b, o = CHAMP.dropna(), ov.dropna()
    return metrics.sharpe_d(o) - metrics.sharpe_d(b), gg


print('=== 1. sign-flip DIAGNOSTICS on (a)(b)(c) — report only, NOT adoptable ===')
for nm, fn in (('a_lqdltt', cr2.credit_book), ('b_be', cr2.breakeven_book),
               ('c_curve', cr2.curve_book)):
    W, R = fn()
    for sgn, tag in ((+1.0, 'asis'), (-1.0, 'FLIPPED(post-hoc, banned)')):
        net, We, _ = cr2.net_of(sgn * W, R)
        r = net.dropna()
        print(f'  {nm} {tag:28s} SR={metrics.sharpe_d(r):+.2f} '
              f'H1={metrics.half_split(r)[0]:+.2f} H2={metrics.half_split(r)[1]:+.2f} '
              f'negyr={metrics.neg_years(r)[0]} (gate: SR>=1.0)')

print('\n=== 2d. gate plateau over N x z_thr (objective = champion SR delta) ===')
base_sr = metrics.sharpe_d(CHAMP.dropna())
grid = {}
for N in (126, 252, 504):
    for zt in (1.5, 2.0, 2.5, 3.0):
        g, _ = cr2.stress_gate('BAA10Y', N=N, z_thr=zt, scale=0.7)
        d, gg = delta_of(g)
        grid[(N, zt)] = (d, int((gg < 1.0).sum()))
        print(f'  N={N:3d} z>{zt:.1f}: delta={d:+.3f}  days_on={int((gg<1.0).sum()):4d}')
best = max(v[0] for v in grid.values())
for (N, zt), (d, _) in grid.items():
    if abs(d - best) < 1e-12:
        chosen = (N, zt)
nb = []
for (N, zt) in grid:
    if (N, zt) == chosen:
        continue
    if abs(N - chosen[0]) + abs(zt - chosen[1]) == 1:
        nb.append(((N, zt), grid[(N, zt)][0]))
print(f'  chosen (peak delta): {chosen} delta={best:+.3f}; 4-neighbors: '
      + ', '.join(f'{k}:{v:+.3f}' for k, v in nb))
print(f'  plateau(>=80% of peak): {all(v >= 0.8 * best for _, v in nb)}')

print('\n=== 2d. era split of the delta (chosen N=252, z>2.0) ===')
g, _ = cr2.stress_gate('BAA10Y', N=252, z_thr=2.0, scale=0.7)
ov, gg = cr2.overlay_on_champion(g)
j = pd.concat({'c': CHAMP, 'o': ov, 'g': gg}, axis=1).dropna()
j['on'] = j.g < 1.0
for lo, hi in (('2008', '2012'), ('2013', '2019'), ('2020', '2026')):
    sl = j[(j.index.year >= int(lo)) & (j.index.year <= int(hi))]
    dbc = metrics.sharpe_d(sl.o) - metrics.sharpe_d(sl.c)
    nd = int(sl.on.sum())
    m_on = sl.loc[sl.on, 'c'].mean() * 252
    print(f'  {lo}-{hi}: champSR={metrics.sharpe_d(sl.c):+.2f} gateSR={metrics.sharpe_d(sl.o):+.2f} '
          f'delta={dbc:+.3f} days_on={nd:4d} champ_annret_on_gated_days={m_on*100:+.1f}%')

print('\n=== 2d. scramble 200x (gate values permuted across dates, count preserved) ===')
delta_real, gg = delta_of(g)
on_mask = (gg < 1.0).values
n_on = int(on_mask.sum())
idx = gg.index
arr = CHAMP.reindex(idx).values
rng = np.random.default_rng(11)
cnt = 0
NS = 200
scaled = np.where(on_mask, 0.7, 1.0)
real_book = arr * scaled
for _ in range(NS):
    perm = rng.permutation(len(idx))
    scr_mask = np.zeros(len(idx), bool)
    scr_mask[perm[:n_on]] = True
    book = arr * np.where(scr_mask, 0.7, 1.0)
    d = metrics.sharpe_d(pd.Series(book, index=idx).dropna()) \
        - metrics.sharpe_d(pd.Series(arr, index=idx).dropna())
    if d >= delta_real:
        cnt += 1
print(f'  delta_real={delta_real:+.4f}  scramble p={cnt/NS:.3f}  (pass: p<=0.05)')

print('\n=== 2d. cost bound of the de-gear ===')
turn = (0.3 * GEAR * n_on)                      # worst case: full 1.6x gross, 30% traded
one_side = turn * 6.4e-4
yrs = (idx[-1] - idx[0]).days / 365.25
print(f'  days_on={n_on} worst-case traded notional={turn:.1f}x -> {one_side*1e4:.0f}bps one-off '
      f'= {one_side/yrs*1e4:.2f}bps/yr over {yrs:.1f}y (vs delta {delta_real*1e4:.0f} SR-bps)')

print('\n=== 2d. true HY OAS (BAMLH0A0HYM2, 2023+) on its overlap — unjudgeable by design ===')
g2, _ = cr2.stress_gate('BAMLH0A0HYM2', N=252, z_thr=2.0, scale=0.7)
ov2, gg2 = cr2.overlay_on_champion(g2)
ov2 = ov2.dropna()
print(f'  overlap n={len(ov2)} {ov2.index[0].date()}->{ov2.index[-1].date()} '
      f'delta={metrics.sharpe_d(ov2)-metrics.sharpe_d(CHAMP.reindex(ov2.index)):+.3f} '
      f'days_on={int((gg2.reindex(ov2.index)<1.0).sum())}/{len(ov2)} '
      f'(contract needs full-window gates; 3y overlap cannot pass -> NOT adoptable)')
