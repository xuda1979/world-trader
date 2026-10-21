#!/usr/bin/env python3
"""HUNT_CREDIT2 round 3 kill-tests + honesty diagnostics (run AFTER the main hunt).

Nothing passed the main gates (best net SR +0.19 vs gate 1.0), so these close the
remaining objections rather than rescue anything:
 D1 gross-vs-net: does any sleeve have alpha BEFORE costs (R2 standard: "no alpha
    exists pre-cost to even pay for itself" is the strongest negative)?
 D2 sign-flip (banned for adoption, run to kill the idea BOTH ways, R2 convention):
    is HY-vs-IG spread momentum maybe a mean-reversion signal instead?
 D3 lag-conservatism: (ii)/(iii) carry an extra shift (T+2 effective). Does the
    T+1-corrected version change any verdict? (bias direction is against the sleeve)
 D4 generic-control kill-test (charter): the only positive cell (HYG dip-buy zt=2.0)
    vs 200 content-free random weekly masks with the same on-fraction, same cost
    machinery. Charter: a content-free vol-matched mask must NOT reproduce the effect.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np
import pandas as pd
from bt import engine, metrics
import HUNT_CREDIT2_round3 as cr3

hyg, jnk, lqd, ief = cr3.px('HYG'), cr3.px('JNK'), cr3.px('LQD'), cr3.px('IEF')
y_hyg = cr3.yld('BAMLEMHBHYCRPIOAS')
y_ig = cr3.yld('BAMLC0A0CM')


def gross_of(W, R, vt=True, target=0.10):
    """Same pipeline as net_of but WITHOUT costs/borrow -> gross SR (alpha check)."""
    We = W.shift(1).fillna(0.0)
    gross = (We * R).sum(axis=1)
    if vt:
        s = engine.vol_target_scale(gross.to_frame('g'), target=target)['g']
        We = We.mul(s, axis=0)
    return ((We * R).sum(axis=1)).rename('ret'), We


print('=== D1 gross vs net SR ===')
for nm, (W, R) in {
    'spread_HYG_LQD_k63': cr3.book_spread_momentum(hyg, lqd, k=63),
    'spread_JNK_IEF_k63': cr3.book_spread_momentum(jnk, ief, k=63),
    'carry_hyg_ief_k252': cr3.book_carry(hyg, y_hyg, ief, y_ig, k=252),
    'meanrev_HYG_k20_z1': cr3.book_meanrev(hyg, k=20, z_thr=1.0),
    'meanrev_JNK_k20_z1': cr3.book_meanrev(jnk, k=20, z_thr=1.0),
}.items():
    g, _ = gross_of(W, R)
    n, _, _ = cr3.net_of(W, R)
    print(f'  {nm:22s} grossSR={metrics.sharpe_d(g.dropna()):+.2f} '
          f'netSR={metrics.sharpe_d(n.dropna()):+.2f}')

print('\n=== D2 sign-flip kill (spread momentum both ways; NOT an adoption candidate) ===')
for pair, (hi, lo) in {'HYG_LQD': (hyg, lqd), 'JNK_IEF': (jnk, ief)}.items():
    for k in [21, 63, 126, 252]:
        W, R = cr3.book_spread_momentum(hi, lo, k=k)
        Wf = W * -1.0
        n, _, _ = cr3.net_of(Wf, R)
        print(f'  {pair} FLIPPED k={k}: netSR={metrics.sharpe_d(n.dropna()):+.2f}')

print('\n=== D3 T+1-corrected (ii)/(iii): does removing the extra shift change anything? ===')
# (ii) carry: rebuild WITHOUT the inner shift(1)
Rc = pd.concat({'HIY': cr3.total_return(hyg, y_hyg), 'IG': cr3.total_return(ief, y_ig)},
               axis=1).dropna()
sp = (y_hyg.reindex(Rc.index).ffill(limit=5) - y_ig.reindex(Rc.index).ffill(limit=5))
z = (sp - sp.rolling(252).mean()) / sp.rolling(252).std()
w = (-z).clip(-1.0, 1.0)                                  # no inner shift
Wc = pd.DataFrame({'HIY': w, 'IG': -w}).reindex(Rc.index).fillna(0.0)
n, _, _ = cr3.net_of(Wc, Rc)
print(f'  carry T+1-corrected: netSR={metrics.sharpe_d(n.dropna()):+.2f} '
      f'(as-built T+2: -0.78), n={len(n.dropna())}')
# (iii) meanrev: apply the Friday decision to the NEXT session without the extra net_of shift
for sym, s in (('HYG', hyg), ('JNK', jnk)):
    R = s.pct_change().to_frame('HIY').dropna()
    sig_d = cr3.meanrev_signal(s, k=20, z_thr=1.0)
    wk = cr3.to_weekly(sig_d)
    wk = wk[wk.index < R.index[-1]]
    trade_days = R.index.to_series()
    pos = pd.Series(0.0, index=R.index)
    for fri, v in wk.dropna().items():
        later = trade_days[trade_days.index > fri]
        if len(later):
            pos.loc[later.iloc[0]:] = v
    W = pos.to_frame('HIY').reindex(R.index).fillna(0.0)
    We = W.copy()                                          # already next-session aligned
    gross = (We * R).sum(axis=1)
    sc = engine.vol_target_scale(gross.to_frame('g'))['g']
    We = We.mul(sc, axis=0)
    net = (We * R).sum(axis=1) - engine.cost_turnover(We) - engine.borrow_cost(We)
    print(f'  meanrev {sym} T+1-corrected: netSR={metrics.sharpe_d(net.dropna()):+.2f} '
          f'(as-built T+2: {"-0.13" if sym == "HYG" else "-0.35"})')
    # also the zt=2.0 best cell, corrected
    sig_d2 = cr3.meanrev_signal(s, k=20, z_thr=2.0)
    wk2 = cr3.to_weekly(sig_d2)
    wk2 = wk2[wk2.index < R.index[-1]]
    pos2 = pd.Series(0.0, index=R.index)
    for fri, v in wk2.dropna().items():
        later = trade_days[trade_days.index > fri]
        if len(later):
            pos2.loc[later.iloc[0]:] = v
    W2 = pos2.to_frame('HIY').reindex(R.index).fillna(0.0)
    We2 = W2.copy()
    gross2 = (We2 * R).sum(axis=1)
    sc2 = engine.vol_target_scale(gross2.to_frame('g'))['g']
    We2 = We2.mul(sc2, axis=0)
    net2 = (We2 * R).sum(axis=1) - engine.cost_turnover(We2) - engine.borrow_cost(We2)
    print(f'  meanrev {sym} zt=2.0 T+1-corrected: netSR={metrics.sharpe_d(net2.dropna()):+.2f} '
          f'(as-built T+2: +0.19)' if sym == 'HYG' else
          f'  meanrev {sym} zt=2.0 T+1-corrected: netSR={metrics.sharpe_d(net2.dropna()):+.2f}')

print('\n=== D4 generic-control kill-test on the only positive cell (HYG dip-buy zt=2.0) ===')
# 200 content-free random WEEKLY masks (same on-fraction as the real dip signal), same
# T+1/cost/VT machinery. Real must beat the 95th pctile for the cell to mean anything.
s = hyg
R = s.pct_change().to_frame('HIY').dropna()
sig_d = cr3.meanrev_signal(s, k=20, z_thr=2.0)
wk = cr3.to_weekly(sig_d)
wk = wk[wk.index < R.index[-1]]
trade_days = R.index.to_series()


def build(mask_fri):
    pos = pd.Series(0.0, index=R.index)
    for fri, v in mask_fri.dropna().items():
        later = trade_days[trade_days.index > fri]
        if len(later):
            pos.loc[later.iloc[0]:] = v
    W = pos.to_frame('HIY').reindex(R.index).fillna(0.0)
    We = W.shift(1).fillna(0.0)                            # same T+1 as as-built
    gross = (We * R).sum(axis=1)
    sc = engine.vol_target_scale(gross.to_frame('g'))['g']
    We = We.mul(sc, axis=0)
    return ((We * R).sum(axis=1) - engine.cost_turnover(We)
            - engine.borrow_cost(We)).dropna()


real = build(wk)
real_sr = metrics.sharpe_d(real)
on_frac = float(wk.dropna().mean())
rng = np.random.default_rng(7)
srs = []
for _ in range(200):
    rnd = pd.Series((rng.random(len(wk)) < on_frac).astype(float), index=wk.index)
    srs.append(metrics.sharpe_d(build(rnd)))
srs = np.array(srs)
p = float((srs >= real_sr).mean())
print(f'  real dip-mask: SR={real_sr:+.3f} on_frac={on_frac:.2f} '
      f'({int(wk.dropna().sum())}/{len(wk.dropna())} weeks on)')
print(f'  random masks: mean SR={srs.mean():+.3f} sd={srs.std():.3f} '
      f'95th pct={np.percentile(srs, 95):+.3f} max={srs.max():+.3f}')
print(f'  p = P(random >= real) = {p:.3f} -> '
      f'{"KILLED (content-free)" if p > 0.05 else "survives"}')
print(f'  HYG buy-and-hold same window SR={metrics.sharpe_d(R["HIY"].dropna()):+.2f} '
      f'(context: is even the asset worth holding?)')
