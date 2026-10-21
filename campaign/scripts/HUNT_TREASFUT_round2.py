#!/usr/bin/env python3
"""HUNT_TREASFUT round 2 — duration-matched cash-yield engine + steepener kink + level-momentum.

Charter R2 (coordinator standup 2026-09-07 01:3x), on FRED cash yields DGS2/DGS10/DGS30:
 (a) Duration-matched cash-yield engine: convert DGS yield changes to futures-comparable returns
     via modified duration (charter DUR 4.4/7.7/15.5 for 2y/10y/30y proxies), rerun the R1
     momentum/curve machinery with 2008+ depth and REAL vol-targeting.
 (b) Steepener kink-trade: 2s10s + 10s30s combos, vol-targeted, cost-honest.
 (c) Yield LEVEL momentum with regime filter (T5YIFR direction): long-duration when inflation
     expectations falling, tested as overlay AND standalone.

A-PRIORI PRE-REGISTERED (written before any round-2 scan output; scans reported for plateau only):
 momentum k=126d (6m trend, matches standard TSMOM convention); curve/kink k=126d; kink combo
 equal-weight 0.5/0.5; level-momentum k=126d; regime = T5YIFR.diff(63) (falling => long-duration
 permitted); overlay zeroes long-duration exposure when T5YIFR rising (shorts kept); VT 10% ann
 expanding clip<=3.0 (engine default); 6.4bps FULL|dW| + 0.5%/yr borrow; T+1 shift(1).
 Charter note: DUR 4.4 on the 2y leg is a FUTURES-proxy convention (per charter) — DV01-neutral
 weights 1/dur make the steepener's yield-exposure (-dy2 + dy10) dur-invariant, only the carry
 term scales; single-leg momentum is dur-invariant after vol targeting (sign unchanged).
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
from bt import engine, metrics
import bt.gates as bgates
import HUNT_TREASFUT_round1 as r1      # reuse load_yield/synth_tr/units_guard/evaluate/save_sleeve

ROOT = "/Users/daxu/software/world-trader"
FRED = f"{ROOT}/tools/quant/data/more_fred"
DUR2 = {'2': 4.4, '10': 7.7, '30': 15.5}      # charter R2 futures-proxy modified durations
K_MOM = 126                                    # a-priori
K_REG = 63                                     # a-priori regime lookback
load_yield, synth_tr, units_guard = r1.load_yield, r1.synth_tr, r1.units_guard
evaluate, save_sleeve, net_of = r1.evaluate, r1.save_sleeve, r1.net_of
zscore = r1.zscore


def ys_frame(legs):
    ys = pd.DataFrame({k: load_yield(sid) for k, sid in legs.items()}).dropna(how='all').sort_index()
    return ys


def combine_W(*Ws):
    """R2 BUGFIX (test_combined_mom_weights_not_all_nan): plain `+` between weight frames with
    DISJOINT columns union-joins to all-NaN (NaN + x = NaN); a downstream .fillna(0) then silently
    produces a DEAD all-zero book (mom1030 saved as SR=0.00/p=1.00). Always combine with
    .add(fill_value=0.0) on the column union and assert the result is alive."""
    out = Ws[0]
    for W in Ws[1:]:
        out = out.add(W, fill_value=0.0)
    alive = (out.abs().sum(axis=1) > 0).any()
    assert alive, 'combine_W produced an all-zero book — check leg signals'
    return out


def make_R(ys, durs=DUR2, per_year=252.0):
    R = pd.concat({k: synth_tr(ys[k], durs[k], per_year) for k in ys.columns}, axis=1).dropna()
    units_guard(R, per_year=per_year)
    return R


# ---------------- (a) time-series momentum on the synth TR legs ------------------------------
def w_mom(R, col, k=K_MOM, allow_short=True):
    """TS momentum: long leg when its past-k synth TR sum > 0, short otherwise (or flat)."""
    mom = R[col].rolling(k).sum()
    sig = np.sign(mom)
    if not allow_short:
        sig = sig.clip(lower=0.0)
    return pd.DataFrame({col: sig})


def w_curve_steep2(ys, k=K_MOM, long_leg='10', short_leg='2', sym=False):
    """DV01-neutral steepener under charter durs: w_s=+1/dur_s, w_l=-1/dur_l * slope-momentum sig."""
    slope = ys[long_leg] - ys[short_leg]
    sig = (slope.diff(k) > 0).astype(float)
    if sym:
        sig = np.sign(slope.diff(k))
    return pd.DataFrame({short_leg: sig / DUR2[short_leg], long_leg: -sig / DUR2[long_leg]})


# ---------------- (b) steepener kink combos --------------------------------------------------
def w_kink_eq(ys, k=K_MOM):
    """EQ combo: 0.5 * steep(2s10s) + 0.5 * steep(10s30s), each sig from own slope momentum."""
    w1 = w_curve_steep2(ys, k, '10', '2')
    w2 = w_curve_steep2(ys, k, '30', '10')
    return 0.5 * w1.add(w2, fill_value=0.0).fillna(0.0)


def w_kink_fly(ys, k=K_MOM):
    """KINK = curvature momentum: curv = (y10-y2) - (y30-y10); long body when curv rising.
    DV01-matched fly weights E10=+1, E2=E30=-0.5 (each /dur)."""
    curv = 2 * ys['10'] - ys['2'] - ys['30']
    sig = np.sign(curv.diff(k))
    w = pd.DataFrame(index=curv.index)
    w['10'] = sig / DUR2['10']
    w['2'] = -0.5 * sig / DUR2['2']
    w['30'] = -0.5 * sig / DUR2['30']
    return w


def w_kink_2s30(ys, k=K_MOM):
    """2s30s steepener (the analytic sum long-2s10s + short-10s30s; 10y leg cancels)."""
    slope = ys['30'] - ys['2']
    sig = (slope.diff(k) > 0).astype(float)
    return pd.DataFrame({'2': sig / DUR2['2'], '30': -sig / DUR2['30']})


# ---------------- (c) yield LEVEL momentum + T5YIFR regime ----------------------------------
def t5ifr():
    return load_yield('T5YIFR')          # percent->decimal; only direction/level used


def w_level_mom(ys, col, k=K_MOM, regime=None, longdur_ok=None):
    """Yield level momentum: long duration (pos +1) when yield FELL over k days, short when rose.
    regime: optional boolean Series (True = long-duration permitted). Overlay zeroes LONG
    positions when regime is False (shorts kept); shorts always kept."""
    dy = ys[col].diff(k)
    sig = np.where(dy < 0, 1.0, -1.0)
    s = pd.Series(sig, index=ys.index, name=col)
    if regime is not None:
        r = regime.reindex(s.index)
        # fail-closed: NO position before regime data exists (T5YIFR starts 2003-01) — restrict
        # the book to the regime-valid window instead of ffill-fabricating pre-2003 regime flags.
        s = s[r.notna()]
        r = r.dropna()
        s = s.where(~((s > 0) & (~r.astype(bool))), 0.0)   # zero long-duration when regime off
    return pd.DataFrame({col: s})


def regime_t5(k_reg=K_REG):
    """A-priori regime: T5YIFR falling over k_reg days => long-duration permitted."""
    t5 = t5ifr()
    return t5.diff(k_reg) < 0


# ---------------- no-lookahead probes (truncated rebuild == full-sample prefix) --------------
def probe_no_lookahead():
    out = []
    legs = {'2': 'DGS2', '10': 'DGS10', '30': 'DGS30'}
    ys = ys_frame(legs)
    R = make_R(ys)
    pr = ys.index.searchsorted(pd.Timestamp('2015-06-30'))
    Wf = w_mom(R, '10'); Wc = w_mom(R.iloc[:pr], '10')
    out.append(('mom10', Wf.iloc[:pr].round(10).equals(Wc.round(10))))
    Wf = w_kink_eq(ys); Wc = w_kink_eq(ys.iloc[:pr])
    out.append(('kink_eq', Wf.iloc[:pr].round(10).equals(Wc.round(10))))
    Wf = w_kink_fly(ys); Wc = w_kink_fly(ys.iloc[:pr])
    out.append(('kink_fly', Wf.iloc[:pr].round(10).equals(Wc.round(10))))
    reg = regime_t5()
    pr2 = reg.index.searchsorted(pd.Timestamp('2015-06-30'))
    Wf = w_level_mom(ys, '30', regime=reg); Wc = w_level_mom(ys.iloc[:pr], '30', regime=reg.iloc[:pr2])
    # NOTE: the regime-restricted series starts 2003 (T5YIFR onset), so position-slicing the
    # FULL frame by the 1977-based `pr` overshoots the prefix — compare on the probe DATE,
    # EXCLUSIVE of it on both sides (searchsorted side='left' already excludes it in Wc).
    out.append(('level_mom_regime',
                Wf[Wf.index < pd.Timestamp('2015-06-30')].round(10).equals(Wc.round(10))))
    return out


if __name__ == '__main__':
    pd.set_option('display.width', 200)
    print('=== no-lookahead probes ===')
    for nm, okk in probe_no_lookahead():
        print(f'  {nm}: {okk}')
        assert okk, f'LOOKAHEAD DETECTED in {nm}'

    legs = {'2': 'DGS2', '10': 'DGS10', '30': 'DGS30'}
    ys = ys_frame(legs)
    R = make_R(ys)
    print(f'\nengine window: {R.index[0].date()} -> {R.index[-1].date()} n={len(R)} '
          f'post-champ-start n={(R.index >= r1.CHAMP.index[0]).sum()}')

    results = {}

    print('\n=== (a1) TS momentum on synth TR legs, k-scan {21,42,63,126,252} (a-priori 126) ===')
    for col in ['2', '10', '30']:
        scan = {}
        for k in [21, 42, 63, 126, 252]:
            W = w_mom(R, col, k)
            net, We, g = net_of(W, R)
            scan[k] = metrics.sharpe_d(net.dropna())
        star = {126: ' *a-priori'}.get(126 if col == '10' else -1, '')
        print(f'  leg {col}: ' + '  '.join(f'k={k}:{v:.2f}{"*" if k == 126 else ""}' for k, v in scan.items()))
        okp, info = bgates.plateau_ok(scan, 126)
        print(f'    plateau@126: {okp} {info["neighbors"]}')
    print('--- (a1) chosen k=126 full gates ---')
    for col in ['2', '10', '30']:
        W = w_mom(R, col, 126)
        net, We, g = net_of(W, R)
        results[f'mom{col}_k126'] = evaluate(f'TREASFUT2_mom{col}_k126', net, We, R)
    # combined 10y+30y momentum (half/half) — the classic long-end trend book
    Wc = combine_W(0.5 * w_mom(R, '10'), 0.5 * w_mom(R, '30')).fillna(0.0)
    netc, Wec, gc = net_of(Wc, R)
    results['mom1030_k126'] = evaluate('TREASFUT2_mom1030_k126', netc, Wec, R)

    print('\n--- (a2) R1 curve machinery rerun under charter durs (k=21 a-priori from R1, scan) ---')
    scan_c = {}
    for k in [5, 10, 21, 42, 63, 126]:
        W = w_curve_steep2(ys, k)
        net, We, g = net_of(W, R)
        scan_c[k] = metrics.sharpe_d(net.dropna())
    print('  2s10s steep: ' + '  '.join(f'k={k}:{v:.2f}{"*" if k == 21 else ""}' for k, v in scan_c.items()))
    okp, info = bgates.plateau_ok(scan_c, 21)
    print(f'    plateau@21: {okp} {info["neighbors"]}')
    W = w_curve_steep2(ys, 21)
    net, We, g = net_of(W, R)
    results['curve2s10s_d2_k21'] = evaluate('TREASFUT2_curve2s10s_k21', net, We, R)

    print('\n=== (b) steepener kink combos (a-priori k=126, EQ 0.5/0.5) ===')
    scan_b = {}
    for k in [21, 42, 63, 126, 252]:
        net, _, _ = net_of(w_kink_eq(ys, k), R)
        scan_b[k] = metrics.sharpe_d(net.dropna())
    print('  kink EQ: ' + '  '.join(f'k={k}:{v:.2f}{"*" if k == 126 else ""}' for k, v in scan_b.items()))
    okp, info = bgates.plateau_ok(scan_b, 126)
    print(f'    plateau@126: {okp} {info["neighbors"]}')
    net, We, g = net_of(w_kink_eq(ys, 126), R)
    results['kink_eq_k126'] = evaluate('TREASFUT2_kink_eq_k126', net, We, R)
    net, We, g = net_of(w_kink_fly(ys, 126), R)
    results['kink_fly_k126'] = evaluate('TREASFUT2_kink_fly_k126', net, We, R)
    net, We, g = net_of(w_kink_2s30(ys, 126), R)
    results['kink_2s30_k126'] = evaluate('TREASFUT2_kink_2s30_k126', net, We, R)

    print('\n=== (c) yield LEVEL momentum +/- T5YIFR regime (a-priori k=126, regime diff63) ===')
    reg = regime_t5()
    for col in ['10', '30']:
        # standalone
        W = w_level_mom(ys, col, 126)
        net, We, g = net_of(W, R)
        results[f'lvl{col}_k126'] = evaluate(f'TREASFUT2_lvl{col}_k126', net, We, R)
        # overlay (regime zeroes long-duration when T5YIFR rising) — window starts at T5YIFR 2003;
        # trim_coverage so gates are computed ONLY on the tradable window (R2 BUGFIX: the old
        # untrimmed call diluted SR with 61% dead zero rows, H1=0.00 pure artifact)
        W = w_level_mom(ys, col, 126, regime=reg)
        net, We, g = net_of(W, R, trim_coverage=True)
        net = net.dropna()
        print(f'    (overlay window starts {net.index[0].date()} — T5YIFR begins 2003-01)')
        results[f'lvl{col}_k126_reg'] = evaluate(f'TREASFUT2_lvl{col}_k126_reg', net, We, R)

    print('\n=== SUMMARY (FULL-window gates, fail-closed) ===')
    for nm, r in results.items():
        print(f"  {nm:18s} SR={r['sr']:6.2f} H1={r['h1']:6.2f} H2={r['h2']:6.2f} negyr={r['neg']:2d} "
              f"worst={r['worst']*100:7.1f}% p={r['p']:.3f} lag_p={r['lag_p'] if isinstance(r['lag_p'],float) else float('nan'):.3f} "
              f"corr={r['corr']:6.3f} cA6R7={r['c_a6r7']:6.3f} SR_08+={r['sr_ov']:6.2f} PASS={r['pass']}")

    print('\n=== save sleeves (best-of-family; NEG-tagged when they fail) ===')
    save = [
        ('TREASFUT2_mom10_k126', results['mom10_k126'], [
            f'HUNT_TREASFUT r2 (a) TS momentum on charter-dur synth TR (DGS10, dur 7.7), k=126 a-priori,',
            'T+1, VT10% clip3, 6.4bps FULL|dW| + 0.5%/yr borrow.']),
        ('TREASFUT2_mom1030_k126', results['mom1030_k126'], [
            'HUNT_TREASFUT r2 (a) 0.5*mom(10y)+0.5*mom(30y) synth TR, k=126 a-priori, VT10% clip3,',
            'T+1, 6.4bps FULL|dW| + borrow.']),
        ('TREASFUT2_kink_eq_k126', results['kink_eq_k126'], [
            'HUNT_TREASFUT r2 (b) kink EQ combo 0.5*steep(2s10s)+0.5*steep(10s30s), slope-momentum',
            'k=126 a-priori, DV01-neutral per charter durs 4.4/7.7/15.5, VT10% clip3, T+1, cost-honest.']),
        ('TREASFUT2_lvl10_k126_reg', results['lvl10_k126_reg'], [
            'HUNT_TREASFUT r2 (c) yield LEVEL momentum DGS10 k=126 with T5YIFR.diff(63)<0 regime overlay',
            '(long-duration zeroed when 5y5y fwd infl expectations rising; shorts kept), T5YIFR window',
            '2003+, T+1, VT10% clip3, 6.4bps FULL|dW| + borrow.']),
    ]
    for name, r, meta in save:
        neg = '' if r['pass'] else '_NEG'
        # recompute net for the exact config (evaluate consumed net; rebuild deterministically)
        if name.endswith('mom10_k126'):
            Wx = w_mom(R, '10', 126)
        elif name.endswith('mom1030_k126'):
            Wx = combine_W(0.5 * w_mom(R, '10'), 0.5 * w_mom(R, '30')).fillna(0.0)
        elif name.endswith('kink_eq_k126'):
            Wx = w_kink_eq(ys, 126)
        else:
            Wx = w_level_mom(ys, '10', 126, regime=reg)
        netx, _, _ = net_of(Wx, R, trim_coverage=name.endswith('k126_reg'))
        save_sleeve(name + neg, netx, meta + [
            f"r2 gates: SR={r['sr']:.2f} H1={r['h1']:.2f} H2={r['h2']:.2f} negyr={r['neg']} "
            f"worst={r['worst']*100:.1f}% scram_p={r['p']:.3f} corrChamp={r['corr']:.3f} PASS={r['pass']}"])
