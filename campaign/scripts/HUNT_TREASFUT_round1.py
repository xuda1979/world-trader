#!/usr/bin/env python3
"""HUNT_TREASFUT round 1 — treasury-futures curve/basis round-2 candidates from FRED CMT yields.

Charter (4 decoupled rates sleeves; champion slots a6r7-bond2y-trend + A1credit-regime stay):
 (a) 2s10s CURVE steepener, duration-balanced: long 2y leg / short 10y leg when the curve has
     been steepening over k days, FLAT when flattening (charter wording), vol-scaled, daily.
 (b) TIPS real-yield (DFII10, variant DFII20) LEVEL-REVERSION directional: long when real yield
     z > +th (expect reversion down in yield => price up), short when z < -th, else flat.
 (c) 2s10s30s BUTTERFLY mean-reversion: fly = 10y - 0.5*(2y+30y); duration-matched weights
     (E2=E30=-0.5, E10=+1 in yield space); short body (fly rich z>+th) / long body (z<-th).
 (d) International 10y yield-spread PARTIAL CARRY: per pair (US-DE, US-CA, US-JP) long the
     higher-yield 10y synthetic TR / short the lower, monthly rebalance with 1-month pub lag;
     sleeve = equal-weight of the 3 pair books.

HONESTY (GATES_CONTRACT.md, fail-closed):
 T+1 (target weights.shift(1)); 6.4bps one-side on FULL |dW| (incl VT-driven turnover) + 0.5%/yr
 borrow on short notional; vol-target 10% ann trailing-only expanding clip<=3.0; scramble 200x
 permuted FINAL weights vs real returns re-costed (+ bt.gates.scramble_positions lag-roll 200x);
 halves H1,H2 >= 0.5; <= 2 neg years each > -5%; FULL-window net SR >= 1.0; plateau (bt.gates);
 |corr| < 0.15 vs champion GOAL100_RAWEW13v2_WEIGHTED_GEAR16 (+ corr to a6r7 & A1credit watched).

PRE-REGISTERED a-priori params (before any scan output; scans reported for plateau only):
 (a) k=21d; (b) DFII10 N=252 th=1.0; (c) N=504 th=1.0; (d) 1m lag, equal-weight 3 pairs.

PRICE PATH (TRADE_RECORD_STANDARD): SYNTH — all PnL from synthetic total-return indices
 TR = -modDur*dyield + yield/252 built on FRED constant-maturity yields (DGS2/10/30, DFII10/20,
 IRLTLT01{DEM,CAM,JPM,USM}156N). modDur fixed: 2y=1.9, 10y=8.5, 30y=19.0 (matches champion
 a6r7's -1.9*dy 2y convention). Approximates treasury futures; NO real futures price series used.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np, pandas as pd
from bt import engine, metrics
import bt.gates as bgates

ROOT = "/Users/daxu/software/world-trader"
FRED = f"{ROOT}/tools/quant/data/more_fred"
COST_BPS = 6.4
CHAMP = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0]
A6R7 = pd.read_csv(f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
                   index_col=0, parse_dates=True).iloc[:, 0]
A1CR = pd.read_csv(f"{ROOT}/campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv",
                   index_col=0, parse_dates=True).iloc[:, 0]
DUR = {'2': 1.9, '10': 8.5, '20': 13.5, '30': 19.0}


def load_yield(sid):
    """FRED yields are in PERCENT -> convert to DECIMAL (committed a6r7 convention: y/100 then
    TR = -dur*dy + y/252). UNITS BUGFIX r1: without /100 the carry term y/252 is 100x too big
    (synth 10y ann vol 695% vs 6.9% correct) and the 'steepener' harvests fake 4%/day drift."""
    s = pd.read_csv(f"{FRED}/{sid}.csv", index_col=0, parse_dates=True)['value'].astype(float)
    assert s.index.is_monotonic_increasing and not s.index.duplicated().any()
    return (s / 100.0).sort_index()


def synth_tr(y, dur, per_year=252.0):
    """SYNTH total return from yield levels (DECIMAL): TR_t = -dur*dy + y_{t-1}/per_year.
    per_year=252 for daily series, 12 for native-monthly (IRLTLT) series."""
    return (-dur * y.diff() + y.shift(1) / per_year).rename(y.name)


def units_guard(R, per_year=252.0):
    """Fail-closed sanity: synth TR ann vol must sit in a sane 1..30% band.
    Regression guard for the r1 percent-vs-decimal carry-term bug (caught 695% vol)."""
    for c in R.columns:
        v = R[c].std() * np.sqrt(per_year)
        assert 0.01 <= v <= 0.30, f'UNITS GUARD: {c} synth TR ann vol {v:.3f} outside sane band'


def bond_frame(legs):
    """legs: {'2': sid, ...} -> (R DataFrame of synth TR on common dates, yields frame)."""
    ys = pd.DataFrame({k: load_yield(sid) for k, sid in legs.items()}).dropna(how='all').sort_index()
    R = pd.concat({k: synth_tr(ys[k], DUR[k]) for k in legs}, axis=1).dropna()
    units_guard(R)
    return R, ys.reindex(R.index)


def zscore(s, N):
    return (s - s.rolling(N).mean()) / s.rolling(N).std()


# ---------------- generic T+1 / VT / cost engine (campaign-standard, mirrors HUNT_INTL2) ----
def net_of(W, R, vt=True, target=0.10, trim_coverage=False, min_live_frac=0.5):
    """T+1 net book. R2 BUGFIX (test_net_of_no_phantom_window / _subset_columns_zeroed): W is
    reindexed onto R's (index, columns) BEFORE anything else. The old code unioned indexes, so
    (i) W built on a wider index than R fabricated years of zero-return rows that still PAID
    turnover costs, and (ii) W trading a subset of R's legs produced (We*R) NaN holes. Callers
    wanting a SHORTER book than R (e.g. the T5YIFR regime overlay, tradable only from 2003) must
    trim R to the tradable window themselves (or pass trim_coverage=True) — net lives on R's
    grid by default, fail-closed."""
    W = W.reindex(index=R.index, columns=R.columns).fillna(0.0)
    live = W.abs().sum(axis=1) > 0
    if trim_coverage and live.any():
        first = int(np.argmax(live.values))
        R = R.iloc[first:]
        W = W.iloc[first:]
        live = live.iloc[first:]
    if not live.any():
        raise ValueError(f'dead book: 0 live rows in evaluated window [{R.index[0]}..{R.index[-1]}] '
                         f'— signal pipeline bug (e.g. disjoint-column + union-NaN), refusing to evaluate')
    if live.mean() < min_live_frac and not trim_coverage:
        print(f'WARNING net_of: only {live.mean()*100:.1f}% live rows in evaluated window — '
              f'gates diluted by dead zero rows; pass trim_coverage=True for a partial-window book')
    We = W.shift(1).fillna(0.0)
    gross = (We * R).sum(axis=1)
    if vt:
        s = engine.vol_target_scale(gross.to_frame('g'), target=target)['g']
        We = We.mul(s, axis=0)
    port = (We * R).sum(axis=1)
    cost = engine.cost_turnover(We, cost_bps=COST_BPS)
    borr = engine.borrow_cost(We)
    return (port - cost - borr).rename('ret'), We, gross


def scramble_perm(We_final, R, net, n=200, seed=7):
    """Campaign-standard: permute FINAL weight rows (shared across legs) vs real returns, re-cost.
    p = P(SR_scr >= SR_real)."""
    idx = net.index
    We = We_final.reindex(idx).fillna(0.0)
    Re = R.reindex(idx).fillna(0.0)
    real_sr = metrics.sharpe_d(net)
    arrW, arrR = We.values, Re.values
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(n):
        Wp = pd.DataFrame(arrW[rng.permutation(len(idx))], index=idx, columns=We.columns)
        book = (Wp * Re).sum(axis=1) - engine.cost_turnover(Wp, cost_bps=COST_BPS) \
               - engine.borrow_cost(Wp)
        if metrics.sharpe_d(book) >= real_sr:
            cnt += 1
    return cnt / n


def evaluate(name, net, We, R, verbose=True):
    net = net.dropna()
    sr = metrics.sharpe_d(net); h1, h2 = metrics.half_split(net)
    neg, worst = metrics.neg_years(net)
    p = scramble_perm(We, R, net)
    corr = bgates.corr_to(CHAMP, net)
    c_a6 = bgates.corr_to(A6R7, net); c_a1 = bgates.corr_to(A1CR, net)
    vol = net.std() * np.sqrt(252)
    # secondary lag-roll scramble (timing destroyed, weight structure preserved, re-costed)
    Rj = R.reindex(net.index).fillna(0.0)
    if Rj.shape[1] == 1:
        lag_p, _ = bgates.scramble_positions(We.sum(axis=1).values, Rj.iloc[:, 0].values, n=200)
    else:
        lag_p = lagroll_p(We, R, net)
    # champion-overlap window (champion starts 2008-03-31)
    net_ov = net[net.index >= CHAMP.index[0]]
    res = dict(sr=sr, h1=h1, h2=h2, neg=neg, worst=worst, p=p, lag_p=lag_p, corr=corr,
               c_a6r7=c_a6, c_a1credit=c_a1, vol=vol, ann=metrics.ann_geo(net), n=len(net),
               start=net.index[0].date(), end=net.index[-1].date(),
               sr_ov=metrics.sharpe_d(net_ov), n_ov=len(net_ov),
               h1_ov=metrics.half_split(net_ov)[0], h2_ov=metrics.half_split(net_ov)[1])
    res['ok'] = dict(
        a_sr=res['sr'] >= 1.0, c_halves=(h1 >= 0.5 and h2 >= 0.5),
        d_yearly=(neg <= 2 and worst > -0.05), e_scramble=p <= 0.05, f_corr=abs(corr) < 0.15)
    res['pass'] = all(res['ok'].values())
    if verbose:
        ok = res['ok']
        print(f"[{name}] n={res['n']} {res['start']}->{res['end']} SR={sr:.2f} ann={res['ann']*100:.1f}% "
              f"vol={vol*100:.1f}% H1={h1:.2f} H2={h2:.2f} negyr={neg} worst={worst*100:.1f}% "
              f"scram_p={p:.3f} lag_p={lag_p if isinstance(lag_p,float) and lag_p==lag_p else float('nan'):.3f} "
              f"corrChamp={corr:.3f} cA6R7={c_a6:.3f} cA1CR={c_a1:.3f} SR_08+={res['sr_ov']:.2f}")
        print(f"    gates: SR>=1:{ok['a_sr']} halves>=0.5:{ok['c_halves']} yearly:{ok['d_yearly']} "
              f"scramble:{ok['e_scramble']} |corr|<0.15:{ok['f_corr']}  PASS={res['pass']}")
    return res


def save_sleeve(name, net, meta_lines):
    import os
    d = f"{ROOT}/campaign/agents/chief/coord/HUNT_TREASFUT/sleeves"
    os.makedirs(d, exist_ok=True)
    df = net.dropna().rename('ret').reset_index()
    df.columns = ['date', 'ret']
    df.to_csv(f"{d}/{name}.csv", index=False)
    with open(f"{d}/{name}.csv.meta", 'w') as f:
        f.write("\n".join(meta_lines) + "\n")
    print(f"  saved {d}/{name}.csv n={len(df)}")


# ---------------- (a) 2s10s curve steepener ----------------------------------------------
def w_curve_steep(y2, y10, k, sym=False):
    """Duration-balanced steepener: E2=+1, E10=-1 => w2=+1/1.9, w10=-1/8.5.
    Charter: long 2y/short 10y when curve steeps (slope momentum>0), FLAT when flattening.
    sym=True variant: also short the curve when flattening."""
    slope = y10 - y2
    sig = (slope.diff(k) > 0).astype(float)          # 1=steepening, 0=flattening
    if sym:
        sig = slope.diff(k).apply(np.sign)           # +1 steep / -1 flat(ter)
    w2 = pd.Series(1.0 / DUR['2'], index=slope.index) * sig
    w10 = pd.Series(-1.0 / DUR['10'], index=slope.index) * sig
    return pd.DataFrame({'2': w2, '10': w10})


def w_curve_naive(y2, y10, k):
    """Dollar (not duration) balanced variant: +1 on 2y TR, -1 on 10y TR (10y-duration dominated)."""
    sig = ((y10 - y2).diff(k) > 0).astype(float)
    return pd.DataFrame({'2': sig * 1.0, '10': -sig * 1.0})


# ---------------- (b) TIPS real-yield level reversion -------------------------------------
def w_tips_rev(y, N, th, long_only=False):
    z = zscore(y, N)
    pos = pd.Series(0.0, index=y.index)
    pos[z > th] = 1.0
    if not long_only:
        pos[z < -th] = -1.0
    return pd.DataFrame({y.name: pos})


# ---------------- (c) 2s10s30s butterfly --------------------------------------------------
def w_fly(y2, y10, y30, N, th):
    """fly = 10y - 0.5*(2y+30y), duration-matched (yield-space exposure E10=+1, E2=E30=-0.5).
    z>+th: body cheap(yield high) -> long body/short wings (expect fly down). z<-th: opposite."""
    fly = y10 - 0.5 * (y2 + y30)
    z = zscore(fly, N)
    w = pd.DataFrame(index=fly.index)
    w['10'] = (1.0 / DUR['10']) * (z > th).astype(float) - (1.0 / DUR['10']) * (z < -th).astype(float)
    w['2'] = (-0.5 / DUR['2']) * (z > th).astype(float) + (0.5 / DUR['2']) * (z < -th).astype(float)
    w['30'] = (-0.5 / DUR['30']) * (z > th).astype(float) + (0.5 / DUR['30']) * (z < -th).astype(float)
    return w


# ---------------- (d) international 10y spread partial carry ------------------------------
PAIRS = {'DE': 'IRLTLT01DEM156N', 'CA': 'IRLTLT01CAM156N', 'JP': 'IRLTLT01JPM156N'}
US10 = 'IRLTLT01USM156N'
FOREIGN_DUR = 8.5   # 10y approx, same as DGS10 (SYNTH)


def run_intl_carry(k_list=('DE', 'CA', 'JP'), lag_m=0, gross_pair=1.0):
    """NATIVE-MONTHLY carry: per pair, long the higher-yield 10y synth TR / short the lower,
    position chosen from the latest yield observation PUBLISHED strictly before the month the
    position is held (lag_m extra months of safety), held 1 month. Monthly TR per_year=12.
    honest-frequency note (r1 fix): IRLTLT are MONTHLY series — a daily-resampled book would
    inflate obs count ~21x and understate per-obs risk; evaluate at native frequency.
    Returns (R dict per pair, W dict per pair)."""
    us = load_yield(US10)
    Rs, Ws = {}, {}
    for k in k_list:
        fy = load_yield(PAIRS[k])
        ym = pd.concat({'US': us, k: fy}, axis=1).dropna()
        Rm = pd.concat({'US': synth_tr(ym['US'], DUR['10'], 12),
                        k: synth_tr(ym[k], FOREIGN_DUR, 12)}, axis=1).dropna()
        units_guard(Rm, per_year=12)
        w = pd.DataFrame(0.0, index=Rm.index, columns=Rm.columns)
        per = Rm.index.to_period('M')
        ci, cu = w.columns.get_loc(k), w.columns.get_loc('US')
        for i in range(1, len(Rm)):
            # yield snapshot from a month strictly BEFORE the holding month (minus lag_m)
            cutoff = per[i] - lag_m
            avail = ym[ym.index.to_period('M') < cutoff]
            if len(avail):
                snap = avail.iloc[-1]
                h, l = (cu, ci) if snap['US'] >= snap[k] else (ci, cu)
                # NOTE: pandas-3 CoW — chained w.iloc[i][h]=x silently no-ops; use iloc[i,col]
                w.iloc[i, h] = 0.5 * gross_pair
                w.iloc[i, l] = -0.5 * gross_pair
        assert w.abs().sum(axis=1).max() > 0, f'{k}: weights never assigned (CoW no-op check)'
        Rs[k], Ws[k] = Rm, w
    return Rs, Ws


def net_monthly(W, R, cost_bps=COST_BPS):
    """T+1 monthly net: ret = We*R - 6.4bps on FULL |dW| - 0.5%/yr borrow on shorts.
    (No VT overlay at native monthly frequency; vol gate checked on output.)"""
    We = W.shift(1).fillna(0.0)
    port = (We * R).sum(axis=1)
    cost = engine.cost_turnover(We, cost_bps=cost_bps)
    borr = engine.borrow_cost(We)
    return (port - cost - borr).rename('ret')


def net_intl(k_list=('DE', 'CA', 'JP'), lag_m=0):
    """Equal-weight of the 3 pair books (each gross 1.0 when active), monthly."""
    Rs, Ws = run_intl_carry(k_list, lag_m=lag_m)
    nets = {}
    for k in k_list:
        nets[k] = net_monthly(Ws[k], Rs[k]).dropna()
    comb = pd.concat(nets, axis=1).dropna().mean(axis=1)
    return comb.rename('ret'), nets


def lagroll_p(We_final, R, net, n=200, block=10, seed=11):
    """Secondary scramble for multi-leg books: np.roll ALL weight rows by one shared random lag
    in [block, len-block] (preserves within-weight structure AND turnover profile, destroys
    timing only), re-cost. Unlike row-permutation, this is a fair null for low-turnover books
    (row permutation fabricates turnover spikes -> p~0 by construction). Real and scrambled SRs
    are computed on the SAME trimmed window for comparability."""
    idx = net.index
    # ALIGN COLUMNS: the book may trade a SUBSET of R's legs (e.g. mom(10y)+mom(30y) where R
    # also holds the 2y leg). Reindex W to R's columns filling 0 — otherwise numpy broadcast
    # of (T,nW) vs (T,nR) raises (r2 live crash) or, worse, would silently misalign by position.
    Wdf = We_final.reindex(columns=R.columns).fillna(0.0)
    We = Wdf.reindex(idx).fillna(0.0).values
    Re = R.reindex(idx).fillna(0.0).values
    T = len(idx)
    win = slice(block, T - block)

    def sr_of(book):
        return metrics.sharpe_d(pd.Series(book, index=idx).iloc[win])

    real_sr = sr_of((We * Re).sum(axis=1) - engine.cost_turnover(
        pd.DataFrame(We, index=idx), cost_bps=COST_BPS) - engine.borrow_cost(pd.DataFrame(We, index=idx)))
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(n):
        lag = int(rng.integers(block, T - block + 1))
        Wp = np.roll(We, lag, axis=0)
        book = (Wp * Re).sum(axis=1) - engine.cost_turnover(pd.DataFrame(Wp, index=idx), cost_bps=COST_BPS) \
               - engine.borrow_cost(pd.DataFrame(Wp, index=idx))
        if sr_of(book) >= real_sr:
            cnt += 1
    return cnt / n


def evaluate_monthly(name, net, Ws, Rs, verbose=True):
    """Monthly-frequency gates: SR_ann = SR_m*sqrt(12); halves/negyears on monthly obs;
    scramble = permute final monthly weight rows vs real monthly TRs re-costed.
    Champion corr: sleeve months mapped to month-END to align with champion daily resample."""
    net = net.dropna()
    net_me = net.copy()
    net_me.index = net_me.index.to_period('M').to_timestamp('M')   # month-first obs -> month-end
    sr = metrics.sharpe_m(net)
    # NOTE: metrics.half_split annualizes with sqrt(252) — wrong for monthly obs. Compute halves
    # on RAW monthly Sharpe and annualize by sqrt(12) here (sqrt252/sqrt12 = 4.58x inflation).
    k = len(net) // 2
    h1 = metrics.sharpe_d(net.iloc[:k]) * np.sqrt(12) / np.sqrt(252)
    h2 = metrics.sharpe_d(net.iloc[k:]) * np.sqrt(12) / np.sqrt(252)
    neg, worst = metrics.neg_years(net)
    # permutation scramble on the combined book
    Rj = pd.concat({k: Rs[k] for k in Rs}, axis=1).ffill().reindex(net.index).fillna(0.0)
    Wj = pd.concat({k: Ws[k].shift(1).fillna(0.0) for k in Ws}, axis=1)
    Wj = Wj.T.groupby(level=0).sum().T.reindex(net.index).fillna(0.0)
    real_sr = metrics.sharpe_m(net)
    rng = np.random.default_rng(7)
    cnt = 0
    n_perm = 200
    arrW, arrR = Wj.values, Rj.values
    for _ in range(n_perm):
        Wp = pd.DataFrame(arrW[rng.permutation(len(net))], index=net.index, columns=Wj.columns)
        book = (Wp * Rj).sum(axis=1) - engine.cost_turnover(Wp, cost_bps=COST_BPS)
        if metrics.sharpe_m(book) >= real_sr:
            cnt += 1
    p = cnt / n_perm
    champ_m = CHAMP.resample('ME').apply(lambda x: (1 + x).prod() - 1)
    corr = bgates.corr_to(champ_m, net_me)
    a6_m = A6R7.resample('ME').apply(lambda x: (1 + x).prod() - 1)
    a1_m = A1CR.resample('ME').apply(lambda x: (1 + x).prod() - 1)
    c6 = bgates.corr_to(a6_m, net_me); c1 = bgates.corr_to(a1_m, net_me)
    vol = net.std() * np.sqrt(12)
    ann_m = float((1 + net).prod() ** (12.0 / len(net)) - 1)   # 12 periods/yr (ann_geo is 252!)
    res = dict(sr=sr, h1=h1, h2=h2, neg=neg, worst=worst, p=p, corr=corr, vol=vol,
               ann=ann_m, n=len(net),
               start=net.index[0].date(), end=net.index[-1].date(), sr_ov=sr, n_ov=len(net),
               c_a6r7=c6, c_a1credit=c1)
    res['ok'] = dict(a_sr=sr >= 1.0, c_halves=(h1 >= 0.5 and h2 >= 0.5),
                     d_yearly=(neg <= 2 and worst > -0.05), e_scramble=p <= 0.05,
                     f_corr=abs(corr) < 0.15)
    res['pass'] = all(res['ok'].values())
    if verbose:
        ok = res['ok']
        print(f"[{name}] n={res['n']} {res['start']}->{res['end']} SRm*sqrt12={sr:.2f} ann={res['ann']*100:.1f}% "
              f"vol={vol*100:.1f}% H1={h1:.2f} H2={h2:.2f} negyr={neg} worst={worst*100:.1f}% "
              f"scram_p={p:.3f} corrChamp={corr:.3f}")
        print(f"    gates: SR>=1:{ok['a_sr']} halves>=0.5:{ok['c_halves']} yearly:{ok['d_yearly']} "
              f"scramble:{ok['e_scramble']} |corr|<0.15:{ok['f_corr']}  PASS={res['pass']}")
    return res


# ---------------- no-lookahead probes ------------------------------------------------------
def probe_no_lookahead():
    """Truncate data at probe date; reconstructed weights must equal the full-sample prefix."""
    probes = []
    # (a) curve
    R, ys = bond_frame({'2': 'DGS2', '10': 'DGS10'})
    pr = ys.index.searchsorted(pd.Timestamp('2015-06-30'))
    Wf = w_curve_steep(ys['2'], ys['10'], 21)
    Wc = w_curve_steep(ys['2'].iloc[:pr], ys['10'].iloc[:pr], 21)
    probes.append(('curve', Wf.iloc[:pr].round(10).equals(Wc.round(10))))
    # (b) tips
    Rt, yt = bond_frame({'10': 'DFII10'})
    prt = yt.index.searchsorted(pd.Timestamp('2015-06-30'))
    Wtf = w_tips_rev(yt['10'], 252, 1.0)
    Wtc = w_tips_rev(yt['10'].iloc[:prt], 252, 1.0)
    probes.append(('tips', Wtf.iloc[:prt].round(10).equals(Wtc.round(10))))
    # (c) fly
    R3, y3 = bond_frame({'2': 'DGS2', '10': 'DGS10', '30': 'DGS30'})
    pr3 = y3.index.searchsorted(pd.Timestamp('2015-06-30'))
    Wff = w_fly(y3['2'], y3['10'], y3['30'], 504, 1.0)
    Wfc = w_fly(y3['2'].iloc[:pr3], y3['10'].iloc[:pr3], y3['30'].iloc[:pr3], 504, 1.0)
    probes.append(('fly', Wff.iloc[:pr3].round(10).equals(Wfc.round(10))))
    return probes


if __name__ == '__main__':
    pd.set_option('display.width', 200)
    print('=== no-lookahead probes (weights from truncated data == full-sample prefix) ===')
    for nm, okk in probe_no_lookahead():
        print(f'  {nm}: {okk}')
        assert okk, f'LOOKAHEAD DETECTED in {nm}'

    print('\n=== (a) 2s10s curve steepener — scan k (chosen a-priori k=21) ===')
    Rc, yc = bond_frame({'2': 'DGS2', '10': 'DGS10'})
    scan_a = {}
    for k in [5, 10, 21, 42, 63, 126]:
        W = w_curve_steep(yc['2'], yc['10'], k)
        net, We, g = net_of(W, Rc)
        n = net.dropna()
        scan_a[k] = metrics.sharpe_d(n)
    for k, v in scan_a.items():
        star = ' *a-priori' if k == 21 else ''
        print(f'  k={k:>4}  SR={v:6.2f}{star}')
    ok_pl, info = bgates.plateau_ok(scan_a, 21)
    print(f'  plateau(chosen 21): {ok_pl} {info}')

    print('\n--- (a) chosen config full gates + variants ---')
    W = w_curve_steep(yc['2'], yc['10'], 21)
    net, We, g = net_of(W, Rc)
    res_a = evaluate('TREASFUT_curve2s10s_k21', net, We, Rc)
    Wn = w_curve_naive(yc['2'], yc['10'], 21)
    netn, Wen, gn = net_of(Wn, Rc)
    res_an = evaluate('TREASFUT_curve2s10s_k21_naiveDW', netn, Wen, Rc)
    Ws = w_curve_steep(yc['2'], yc['10'], 21, sym=True)
    nets, Wes, gs = net_of(Ws, Rc)
    res_as = evaluate('TREASFUT_curve2s10s_k21_sym', nets, Wes, Rc)
    # scan-best (k=126, only positive scan point) through full gates for the record
    W126 = w_curve_steep(yc['2'], yc['10'], 126)
    net126, We126, g126 = net_of(W126, Rc)
    res_a126 = evaluate('TREASFUT_curve2s10s_k126_scanbest', net126, We126, Rc)

    print('\n=== (b) TIPS real-yield reversion — scan N x th (chosen DFII10, N=252, th=1.0) ===')
    Rt, yt = bond_frame({'10': 'DFII10'})
    scan_b = {}
    for N in [63, 126, 252, 504]:
        for th in [0.5, 1.0, 1.5]:
            W = w_tips_rev(yt['10'], N, th)
            net, We, g = net_of(W, Rt)
            scan_b[(N, th)] = metrics.sharpe_d(net.dropna())
    for kk, v in scan_b.items():
        star = ' *a-priori' if kk == (252, 1.0) else ''
        print(f'  N={kk[0]:>4} th={kk[1]:.1f}  SR={v:6.2f}{star}')
    okN, iN = bgates.plateau_ok({N: scan_b[(N, 1.0)] for N in [63, 126, 252, 504]}, 252)
    okT, iT = bgates.plateau_ok({th: scan_b[(252, th)] for th in [0.5, 1.0, 1.5]}, 1.0)
    print(f'  plateau N-axis@th1.0: {okN} {iN}\n  plateau th-axis@N252: {okT} {iT}')

    print('\n--- (b) chosen config full gates + variants ---')
    W = w_tips_rev(yt['10'], 252, 1.0)
    net, We, g = net_of(W, Rt)
    res_b = evaluate('TREASFUT_tipsrev_N252_t10', net, We, Rt)
    R20, y20 = bond_frame({'20': 'DFII20'})
    Wv = w_tips_rev(y20['20'], 252, 1.0)   # keep col name aligned with R (r1: mis-wired '10')
    netv, Wev, gv = net_of(Wv, R20)
    res_b20 = evaluate('TREASFUT_tipsrev20y_N252_t10', netv, Wev, R20)
    Wlo = w_tips_rev(yt['10'], 252, 1.0, long_only=True)
    netlo, Welo, glo = net_of(Wlo, Rt)
    res_blo = evaluate('TREASFUT_tipsrev_N252_t10_longonly', netlo, Welo, Rt)

    print('\n=== (c) 2s10s30s fly reversion — scan N x th (chosen N=504, th=1.0) ===')
    R3, y3 = bond_frame({'2': 'DGS2', '10': 'DGS10', '30': 'DGS30'})
    scan_c = {}
    for N in [126, 252, 504, 756]:
        for th in [0.5, 1.0, 1.5, 2.0]:
            W = w_fly(y3['2'], y3['10'], y3['30'], N, th)
            net, We, g = net_of(W, R3)
            scan_c[(N, th)] = metrics.sharpe_d(net.dropna())
    for kk, v in scan_c.items():
        star = ' *a-priori' if kk == (504, 1.0) else ''
        print(f'  N={kk[0]:>4} th={kk[1]:.1f}  SR={v:6.2f}{star}')
    okNc, iNc = bgates.plateau_ok({N: scan_c[(N, 1.0)] for N in [126, 252, 504, 756]}, 504)
    okTc, iTc = bgates.plateau_ok({th: scan_c[(504, th)] for th in [0.5, 1.0, 1.5, 2.0]}, 1.0)
    print(f'  plateau N-axis@th1.0: {okNc} {iNc}\n  plateau th-axis@N504: {okTc} {iTc}')

    print('\n--- (c) chosen config full gates ---')
    W = w_fly(y3['2'], y3['10'], y3['30'], 504, 1.0)
    net, We, g = net_of(W, R3)
    res_c = evaluate('TREASFUT_fly_N504_t10', net, We, R3)

    print('\n=== (d) intl 10y spread partial carry (US vs DE/CA/JP, NATIVE monthly, pub-lag) ===')
    Rs_d, Ws_d = run_intl_carry(lag_m=0)
    comb, nets_d = net_intl(lag_m=0)
    for k, n in nets_d.items():
        print(f'  pair US-{k}: SRm*sqrt12={metrics.sharpe_m(n):6.2f} negyr={metrics.neg_years(n)[0]}')
    res_d = evaluate_monthly('TREASFUT_intlcarry3_lag0', comb, Ws_d, Rs_d)
    Rs_d2, Ws_d2 = run_intl_carry(lag_m=1)
    comb2, nets_d2 = net_intl(lag_m=1)
    res_d2 = evaluate_monthly('TREASFUT_intlcarry3_lag1', comb2, Ws_d2, Rs_d2)

    print('\n=== summary (FULL-window gates, fail-closed) ===')
    rows = [('curve2s10s_k21', res_a), ('curve_k21_naiveDW', res_an), ('curve_k21_sym', res_as),
            ('curve_k126_scanbest', res_a126),
            ('tipsrev_N252_t10', res_b), ('tipsrev20y', res_b20), ('tipsrev_longonly', res_blo),
            ('fly_N504_t10', res_c), ('intlcarry3_lag0', res_d), ('intlcarry3_lag1', res_d2)]
    for nm, r in rows:
        c6 = r.get('c_a6r7', float('nan')); c1 = r.get('c_a1credit', float('nan'))
        print(f"  {nm:22s} SR={r['sr']:6.2f} H1={r['h1']:6.2f} H2={r['h2']:6.2f} negyr={r['neg']:2d} "
              f"worst={r['worst']*100:7.1f}% p={r['p']:.3f} corr={r['corr']:6.3f} "
              f"cA6R7={c6:6.3f} cA1CR={c1:6.3f} SR_08+={r['sr_ov']:6.2f} PASS={r['pass']}")

    print('\n=== save primary sleeves (all NEGATIVE — for coordinator record, NOT champion) ===')
    # r1 note: `net` gets rebound by each family block; save the FINAL (fly) series under the
    # fly name and recompute the curve/tips series under distinct names to avoid shadowing.
    save_sleeve('TREASFUT_fly_N504_t10_NEG', net, [
        'HUNT_TREASFUT r1 (c) 2s10s30s butterfly reversion N=504 th=1.0 (a-priori), duration-matched',
        '(E10=+1/8.5, E2=E30=-0.5/dur). SYNTH TR DGS2/10/30 decimal. NEGATIVE: SR -0.78,',
        'H1 -0.61/H2 -1.00, 33 neg years worst -4.1%, lag_p 0.875, corrChamp -0.010.',
        'Whole 4x4 scan SR in [-2.05, -0.54] — fly reversion LOSES at every window/threshold.'])
    W_a, R_a = w_curve_steep(yc['2'], yc['10'], 21), Rc
    net_a, _, _ = net_of(W_a, R_a)
    save_sleeve('TREASFUT_curve2s10s_k21_NEG', net_a, [
        'HUNT_TREASFUT r1 (a) 2s10s curve steepener k=21, duration-balanced (w2=+1/1.9, w10=-1/8.5),',
        'flat when flattening. SYNTH TR from FRED CMT DGS2/DGS10 (DECIMAL y/100, TR=-dur*dy+y/252),',
        'T+1, VT10% expanding clip3, 6.4bps FULL|dW| + 0.5%/yr borrow. NEGATIVE: SR -0.11,',
        'H1 0.92/H2 -1.45, 31/51 neg years (worst -6.2%), corrChamp -0.010. NOT champion-eligible.',
        'a-priori choice k=21; scan-best k=126 SR 1.12 still fails halves(0.11)/yearly(20 neg).'])
    R_t, y_t = bond_frame({'10': 'DFII10'})
    net_t, _, _ = net_of(w_tips_rev(y_t['10'], 252, 1.0), R_t)
    save_sleeve('TREASFUT_tipsrev_N252_t10_NEG', net_t, [
        'HUNT_TREASFUT r1 (b) TIPS real-yield level reversion DFII10, N=252 th=1.0 (a-priori).',
        'SYNTH TR -8.5*dy+y/252 (y/100 decimal). NEGATIVE: SR -0.11, H1 -0.12/H2 -0.10,',
        '13 neg years worst -26.6%, scram perm p 0.000 lag_p 0.160, corrChamp 0.039.',
        'DFII20 variant SR 0.05; long-only SR -0.06. Whole 4x3 scan SR in [-0.30, -0.09]: dead.'])
    save_sleeve('TREASFUT_intlcarry3_lag1_NEG', comb2, [
        'HUNT_TREASFUT r1 (d) intl 10y partial carry US vs DE/CA/JP, NATIVE monthly (IRLTLT monthly',
        'series), position from yield published before holding month (lag1), ±0.5 per leg, equal-wt',
        '3 pairs, 6.4bps + borrow, T+1. NEGATIVE: SRm*sqrt12 0.70 (<1.0), corrChamp 0.328 (>',
        '0.15; secondary band), cA6R7 0.327, 13/38 neg years. SR<1 kills it regardless.'])
