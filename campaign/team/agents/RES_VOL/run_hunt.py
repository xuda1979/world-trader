#!/usr/bin/env python3
"""RES_VOL R1 pre-registered grid. Lanes (chosen BEFORE any P&L was read):
  A. VRP long book:  in-market when VIX.shift(1) > realized_vol(lb) + thr (implied rich),
     OUT when VRP <= thr. thr in {0, +2, -2}; lb in {10,21,63}; hold=5; SPY & IWM.
  B. VRP short book: -vrp (short equity when realized exceeds implied = stress regime).
  C. SLOPE-INVERSION book: VIX9D>VIX3M sustained => SHORT SPY (fast-vol-spike), exit slope<=0;
     inverse LONG variant. (HUNT_VOL2 R2 only de-risked the champion; never a standalone short.)
  D. VoV-conditioned: VVIX 21d-change tail (top/bottom quintile) gates SPY long.
Costs: 6.4bps FULL |dW| + 0.5%/yr borrow (bt.engine); T+1 shift(1); vt 10% trailing cap 3.
Gates: bt.gates.run with sig=weight (V2 sec-0), ref=champion-of-record (dates-indexed).
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/team")

import numpy as np
import pandas as pd
import bt.gates as bgates
from bt.engine import cost_turnover, borrow_cost
from bt.metrics import sharpe_d, half_split, neg_years, ann_geo
from bt.gates import corr_to
from team.agents.RES_VOL.vol_r1 import (load_vol, load_px, realized_vol, vrp_series,
                                        slope_series, long_book, slope_book)

CHAMP = "/Users/daxu/software/world-trader/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
SPY_F = "/Users/daxu/software/world-trader/tools/quant/data/twelvedata/SPY.csv"
IEF_F = "/Users/daxu/software/world-trader/tools/quant/data/more_etf/IEF.csv"
CTA_F = "/Users/daxu/software/world-trader/campaign/results/sleeve_library/CTA_15vol.csv"


def champ_rets():
    return pd.read_csv(CHAMP, parse_dates=['date'], index_col='date')['ret'].astype(float)


def benchmark_series():
    spy = pd.read_csv(SPY_F, parse_dates=['date'], index_col='date')['close'].astype(float).pct_change()
    ief = pd.read_csv(IEF_F, parse_dates=['date'], index_col='date')['close'].astype(float).pct_change()
    cta = pd.read_csv(CTA_F, parse_dates=['date'], index_col='date')['ret'].astype(float)
    return spy, ief, cta


def evaluate(name, net, We, champ, spy, ief, cta, rpu=None, verbose=True):
    """V2 sec-0 battery: rpu MUST be the TRUE per-unit underlying return series (books judge
    sig*rpu); a reconstructed rpu smears entry costs into r (bias found by test
    test_evaluate_passes_true_rpu_to_gates: 0.1269 vs 0.2319). Fail-closed without it."""
    live = (We.fillna(0.0) != 0.0).any(axis=1)
    net = net[net.index >= live.idxmax()] if live.any() else net.iloc[0:0]
    if rpu is None:
        raise ValueError(f"[{name}] evaluate() requires the true per-unit rpu (fail-closed)")
    if len(net) < 252:
        if verbose:
            print(f"[{name}] n={len(net)} <1y SKIP")
        return None
    sr = sharpe_d(net); h1, h2 = half_split(net); neg, worst = neg_years(net)
    corr = corr_to(champ, net)
    ok = dict(a_sr=sr >= 1.0, c_halves=(h1 >= 0.5 and h2 >= 0.5),
              d_yearly=(neg <= 2 and worst > -0.05), f_corr=bool(abs(corr) < 0.15),
              ac1_uniq=(bgates.lag1_autocorr(net) < 0.5 and bgates.uniq_ratio(net) >= 0.08))
    # AUDIT self-fix R3 (TDD test_evaluate_passes_true_rpu_to_gates): the battery r must be
    # the TRUE per-unit series (fail-closed above), NOT net+costs (== the book W*r, which
    # with sig=W made r_eff = W^2*r; held SR 0.2319 -> 0.0934 on the control book) and not
    # the reconstructed (net+costs)/W, which smears entry costs into r (0.1269 vs 0.2319).
    v2 = bgates.run(rpu.reindex(net.index), ref=champ, sig=We['a'].reindex(net.index).fillna(0.0),
                    scramble_n=200, beats_passive=True, spy=spy, ief=ief, cta=cta)
    res = dict(sr=sr, h1=h1, h2=h2, neg=neg, worst=worst, ann=ann_geo(net), corr=corr,
               n=len(net), start=str(net.index[0].date()), end=str(net.index[-1].date()),
               ok=ok, v2={k: v for k, v in v2.items() if k not in ('leak', 'beats_passive')},
               leak=v2.get('leak'), bp=v2.get('beats_passive'), pass_=bool(v2.get('pass')))
    if verbose:
        lp = res['leak'] or {}
        print(f"[{name}] n={res['n']} SR={sr:.2f} ann={res['ann']*100:.1f}% H1={h1:.2f} H2={h2:.2f} "
              f"negyr={neg} worst={worst*100:.1f}% corr={corr:+.3f} local={all(ok.values())} "
              f"v2pass={res['pass_']} leak_ok={v2.get('leak_ok')} bp_ok={v2.get('beats_passive_ok')}")
    return res



def reconstruct_rpu(net, We, bps=6.4, borrow=0.005):
    """Invert net + charged costs back to PER-UNIT returns (V2 sec-0 battery input).
    net = W*r - cost - borrow  =>  r = (net + cost + borrow)/W on days W != 0."""
    c = cost_turnover(We[['a']], bps).reindex(net.index).fillna(0.0)
    b = borrow_cost(We[['a']], borrow).reindex(net.index).fillna(0.0)
    w = We['a'].reindex(net.index).fillna(0.0)
    return ((net + c + b) / w.replace(0.0, np.nan)).fillna(0.0)


def main():
    champ = champ_rets(); spy, ief, cta = benchmark_series()
    px_s = load_px('SPY'); px_i = load_px('IWM')
    vix = load_vol('VIX'); rvx = load_vol('RVX'); vvix = load_vol('VVIX')
    out = {}
    print("=== A/B. VRP long/short books (SPY + IWM) ===")
    for und, px, iv in (('spx', px_s, vix), ('iwm', px_i, rvx)):
        for lb in (10, 21, 63):
            vrp = vrp_series(iv, realized_vol(px, lb))
            for thr in (0.0, 2.0, -2.0):
                for dirn, sig in (('long', vrp), ('short', -vrp)):
                    nm = f"V_{und}_vrp{lb}_{dirn}_thr{thr:+.0f}"
                    net, We, r = long_book(sig, px, thr=thr, hold=5, return_rpu=True)
                    r = evaluate(nm, net, We, champ, spy, ief, cta, rpu=r)
                    if r:
                        out[nm] = r
    print("=== C. slope-inversion books (9d/3m, 3m/6m) ===")
    v3 = load_vol('VIX3M'); v9 = load_vol('VIX9D'); v6 = load_vol('VIX6M')
    for a, b in ((v9, v3), (v3, v6), (v9, v6)):
        sl = slope_series(a, b)
        for side in ('short', 'long'):
            nm = f"V_slope{getattr(a,'name','s')[:3]}_{side}"
            net, We, r = slope_book(sl, px_s, enter=0.0, exit_=0.0, side=side, return_rpu=True)
            r = evaluate(nm, net, We, champ, spy, ief, cta, rpu=r)
            if r:
                out[nm] = r
    print("=== D. VoV-conditioned SPY long ===")
    vvc = (vvix - vvix.rolling(21).mean().shift(1)).dropna()
    q_hi, q_lo = vvc.quantile(0.80), vvc.quantile(0.20)
    for nm, sig, thr in (('V_vovhi', -vvc, -q_hi), ('V_vovlo', -vvc, -q_lo)):
        net, We, r = long_book(sig, px_s, thr=thr, hold=5, return_rpu=True)
        r = evaluate(nm, net, We, champ, spy, ief, cta, rpu=r)
        if r:
            out[nm] = r
    npass = sum(1 for v in out.values() if all(v['ok'].values()))
    v2p = sum(1 for v in out.values() if v['pass_'])
    print(f"\n=== SCORECARD: {len(out)} books | local-pass {npass} | V2-battery-pass {v2p} ===")
    for k, v in sorted(out.items(), key=lambda kv: -(kv[1]['sr'] if np.isfinite(kv[1]['sr']) else -9)):
        print(f"  {k}: SR={v['sr']:.2f} corr={v['corr']:+.3f} neg={v['neg']} v2pass={v['pass_']}")
    return out


if __name__ == '__main__':
    main()
