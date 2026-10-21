#!/usr/bin/env python3
"""HUNT_CREDIT2 round 2, part 3: adversarial controls on the (d) HY-stress gate overlay.

If the gate's +0.198 champion delta is real credit information, it must survive:
 C1 concentration: not >50% of the delta from the top-5 gated days (single-event fit).
 C2 generic-vol control: a NON-credit stress gate (champion's own trailing realized-vol z>2,
    same 0.7x/252d machinery) giving a similar-or-bigger delta means credit adds nothing.
 C3 lag robustness: extra T+2/T+5 lag should leave most of the delta intact.
 C4 day-count/transition cost: actual on<->off transitions * 0.3*1.6 gross * 6.4bps.
 C5 return/vol/DD accounting: does the delta come from vol reduction with ann-return GIVE-UP?
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
from bt import metrics
import HUNT_CREDIT2_round2 as cr2

CHAMP = cr2.CHAMP
GEAR, BPS = 1.6, 6.4e-4


def apply_scale(s):
    ov, gg = cr2.overlay_on_champion(s)
    return ov.dropna(), gg.reindex(ov.index)


def delta(a, b=CHAMP.dropna()):
    return metrics.sharpe_d(a) - metrics.sharpe_d(b)


print('=== C1 delta concentration over gated days ===')
g, z = cr2.stress_gate('BAA10Y', N=252, z_thr=2.0, scale=0.7)
ov, gg = apply_scale(g)
contrib = (ov - CHAMP.reindex(ov.index)).dropna()          # per-day delta contribution
tot = contrib.sum()
cs = contrib.abs().sort_values(ascending=False)
top5 = cs.head(5).sum()
top20 = cs.head(20).sum()
print(f'  sum |contrib|={cs.sum():.4f} net={tot:+.4f}  top5 share={top5/cs.sum()*100:.0f}%  '
      f'top20 share={top20/cs.sum()*100:.0f}%')
print('  top-6 |contrib| days:')
for d in cs.head(6).index:
    print(f'    {d.date()} champ={CHAMP.loc[d]*100:+.2f}% z={z.reindex([d]).iloc[0]:.2f}')

print('\n=== C2 generic-vol control (champion own trailing vol z>2 -> 0.7x, same machinery) ===')
rv = CHAMP.rolling(252).std()
zv = (rv - rv.rolling(252).mean()) / rv.rolling(252).std()
gv = pd.Series(np.where(zv > 2.0, 0.7, 1.0), index=CHAMP.index).where(zv.notna(), 1.0).shift(1)
ovv, ggv = apply_scale(gv)
print(f'  vol-gate delta={delta(ovv):+.3f} days_on={int((ggv<1.0).sum())} '
      f'(credit-gate delta={delta(ov):+.3f} days_on={int((gg<1.0).sum())})')
ovb, _ = apply_scale(gv.combine_first(g).fillna(1.0) if False else
                     pd.Series(np.minimum(g.reindex(CHAMP.index).fillna(1.0),
                                          gv.reindex(CHAMP.index).fillna(1.0)),
                               index=CHAMP.index).shift(0))
print(f'  both-gates (min scale) delta={delta(ovb):+.3f}')

print('\n=== C2b other-credit-indicator controls (same gate machinery, N=252 z>2 ->0.7x) ===')
for sid in ('BAA', 'DAAA', 'AAA', 'BAA10Y', 'DBAA'):
    try:
        s = cr2.yld(sid)
    except Exception as e:
        print(f'  {sid}: unavailable ({e})'); continue
    zz = (s - s.rolling(252).mean()) / s.rolling(252).std()
    gg2 = pd.Series(np.where(zz > 2.0, 0.7, 1.0), index=s.index).where(zz.notna(), 1.0).shift(1)
    ov2, g2 = apply_scale(gg2)
    print(f'  {sid:8s} delta={delta(ov2):+.3f} days_on={int((g2<1.0).sum())}')

print('\n=== C3 lag robustness (extra days of delay on top of T+1) ===')
for lag in (1, 2, 3, 5, 10):
    gg3 = g.shift(lag - 1)
    ov3, _ = apply_scale(gg3)
    print(f'  T+{lag}: delta={delta(ov3):+.3f}')

print('\n=== C4 transition cost (actual on<->off switches) ===')
on = (gg < 1.0).astype(int)
trans = int((on.diff().abs() > 0).sum())
notional = trans * 0.3 * GEAR
cost = notional * BPS
yrs = (ov.index[-1] - ov.index[0]).days / 365.25
print(f'  transitions={trans} traded={notional:.1f}x notional -> {cost*1e4:.0f}bps one-off '
      f'= {cost/yrs*1e4:.2f}bps/yr; SR drag approx {cost/yrs/ov.std().mean()/np.sqrt(1):.3f} '
      f'(ann_ret basis {cost/yrs:.4%} / vol {ov.std()*np.sqrt(252):.2%})')

print('\n=== C5 accounting: what does the gate cost/gain in ann ret, vol, drawdown ===')
b = CHAMP.reindex(ov.index)


def dd(x):
    # R4 audit fix: cumprod the WEALTH (1+r), not the returns themselves. The old
    # x.cumprod() decayed to ~0 and alternated sign on negative-return days, printing
    # maxDD=100.1% on a champion whose true maxDD is -6.69% (cosmetic; SR/ann/vol were
    # unaffected). Pinned by work_r2/test_credit2_r2.py::test_gate2_C5_dd_uses_wealth_not_returns
    cp = (1 + x).cumprod()
    return float(1 - (cp / cp.cummax()).min())


for nm, x in (('champion', b), ('gated', ov)):
    print(f'  {nm:9s} ann={metrics.ann_geo(x)*100:+.2f}% vol={x.std()*np.sqrt(252)*100:.2f}% '
          f'SR={metrics.sharpe_d(x):+.3f} maxDD={dd(x)*100:.1f}%')
