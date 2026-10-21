#!/usr/bin/env python3
"""HUNT_INTERNATIONAL2 round 1 — international equity cross-momentum / carry / EM-DM rotation.

Charter tests:
 (a) Country momentum: rank single-country ETFs by trailing 12m, long winners short losers, monthly.
 (b) Country carry: IRLTLT 10y yield differentials -> weighted equity ETFs, monthly.
 (c) EM vs DM relative rotation (12m mom), L/S and long-only, vol overlay.

Honesty per GATES_CONTRACT.md:
 T+1 (weights = target.shift(1)); costs 6.4bps on FULL |dW| + 0.5%/yr borrow on short notional;
 vol-target 10% trailing expanding (clip <= 3.0); scramble 200x on FINAL weights with re-costing;
 halves H1,H2 >= 0.5; <= 2 neg years each > -5%; FULL net SR >= 1.0; |corr| < 0.15 vs champion.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np, pandas as pd
from bt import engine, metrics
import bt.gates as bgates

ROOT = "/Users/daxu/software/world-trader"
COST_BPS = 6.4
CHAMP = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0]

DM = ['EWJ', 'EWG', 'EWU', 'EWP', 'EWL', 'EWS', 'EWY', 'EWK']   # JP DE UK ES CH SG KR BE
EM = ['EWT', 'EWZ', 'EWW', 'FXI']                                # TW BR MX CN
UNIV = DM + EM                                                   # 12 single-country ETFs, all 2006-10 starts
CARRY = {'IRLTLT01CHM156N': 'EWL', 'IRLTLT01DEM156N': 'EWG', 'IRLTLT01GBM156N': 'EWU',
         'IRLTLT01JPM156N': 'EWJ', 'IRLTLT01KRM156N': 'EWY', 'IRLTLT01USM156N': 'DIA'}

def load_close(sym):
    df = pd.read_csv(f"{ROOT}/tools/quant/data/more_etf/{sym}.csv", index_col=0, parse_dates=True)
    return df['close'].astype(float)

def px_frame(syms):
    return pd.concat({s: load_close(s) for s in syms}, axis=1).sort_index()

def month_first_positions(index):
    per = pd.Series(index, index=index).groupby(index.to_period('M')).first()
    return set(index.searchsorted(per.values))

def mom_signal(px, months, skip=0):
    """Trailing momentum using data <= t only. skip months excluded from the window front... :
    mom = P.shift(skip*21)/P.shift(months*21) - 1  (skip>0 => classic 12-1m)."""
    return px.shift(skip * 21) / px.shift(months * 21) - 1.0

def rank_weights(mom, topk, reb_pos, min_assets_frac=0.9):
    """Equal-weight long top-k / short bottom-k by momentum. Target weights updated on the first
    trading day of each month using the PREVIOUS day's (month-end close) momentum. Flat until
    >= min_assets_frac of the universe has valid momentum."""
    W = pd.DataFrame(0.0, index=mom.index, columns=mom.columns)
    prev = None
    n = mom.shape[1]
    for i in range(len(mom)):
        if i in reb_pos and i > 0:
            m = mom.iloc[i - 1]
            if m.notna().sum() >= min_assets_frac * n:
                r = m.rank(ascending=False, na_option='keep')
                w = pd.Series(0.0, index=mom.columns)
                w[r <= topk] = 1.0 / topk
                w[r > n - topk] = -1.0 / topk
                prev = w
        if prev is not None:
            W.iloc[i] = prev.values
    return W

def net_of(W, R, vt=True, target=0.10):
    """T+1 effective weights, trailing vol-target, 6.4bps full |dW| + borrow on shorts."""
    We = W.shift(1).fillna(0.0)
    gross = (We * R).sum(axis=1)
    if vt:
        s = engine.vol_target_scale(gross.to_frame('g'), target=target)['g']
        We = We.mul(s, axis=0)
    port = (We * R).sum(axis=1)
    cost = engine.cost_turnover(We, cost_bps=COST_BPS)
    borr = engine.borrow_cost(We)
    return (port - cost - borr).rename('ret'), We, gross

def scramble_p(We_final, R, net, n=200, seed=7):
    """Campaign-standard signal scramble: permute FINAL weight rows (shared permutation across
    assets) against real date-aligned returns, RE-APPLY costs, compare SRs. p = P(SR_scr >= real)."""
    idx = net.index
    We = We_final.reindex(idx).fillna(0.0)
    Re = R.reindex(idx).fillna(0.0)
    real_sr = metrics.sharpe_d(net)
    arrW, arrR = We.values, Re.values
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(n):
        Wp = pd.DataFrame(arrW[rng.permutation(len(idx))], index=idx, columns=We.columns)
        book = (Wp * Re).sum(axis=1) - engine.cost_turnover(Wp, cost_bps=COST_BPS) - engine.borrow_cost(Wp)
        if metrics.sharpe_d(book) >= real_sr:
            cnt += 1
    return cnt / n

def trim_warmup(net, We):
    """Trim net series to the first day the book is actually live (|W|>0) — otherwise years of
    flat-zero rows (EWT starts 2000, rest 2006-10) dilute the SR with synthetic flat days."""
    live = (We.fillna(0.0) != 0).any(axis=1)
    if not live.any():
        return net.iloc[0:0]
    first = live.idxmax()  # index label of first True
    return net[net.index >= first]


def evaluate(name, net, We, R, verbose=True):
    net = trim_warmup(net, We)
    sr = metrics.sharpe_d(net); h1, h2 = metrics.half_split(net)
    neg, worst = metrics.neg_years(net)
    p = scramble_p(We, R, net)
    corr = bgates.corr_to(CHAMP, net)
    vol = net.std() * np.sqrt(252)
    res = dict(sr=sr, h1=h1, h2=h2, neg=neg, worst=worst, p=p, corr=corr, vol=vol,
               ann=metrics.ann_geo(net), n=len(net),
               start=net.index[0].date(), end=net.index[-1].date())
    # scramble gate: p<=0.05 only counts as a pass if the real book BEATS random (SR>0);
    # a significantly-worse-than-random book (SR<0, small p) must FAIL (TDD 2026-09-06).
    res['ok'] = dict(
        a_sr=res['sr'] >= 1.0, c_halves=(h1 >= 0.5 and h2 >= 0.5),
        d_yearly=(neg <= 2 and worst > -0.05),
        e_scramble=(p <= 0.05 and res['sr'] > 0),
        f_corr=abs(corr) < 0.15)
    res['pass'] = all(res['ok'].values())
    if verbose:
        ok = res['ok']
        print(f"[{name}] n={res['n']} {res['start']}->{res['end']} SR={sr:.2f} ann={res['ann']*100:.1f}% "
              f"vol={vol*100:.1f}% H1={h1:.2f} H2={h2:.2f} negyr={neg} worst={worst*100:.1f}% "
              f"scram_p={p:.3f} corrChamp={corr:.3f}")
        print(f"    gates: SR>=1:{ok['a_sr']} halves>=0.5:{ok['c_halves']} yearly:{ok['d_yearly']} "
              f"scramble:{ok['e_scramble']} |corr|<0.15:{ok['f_corr']}  PASS={res['pass']}")
    return res

# ---------------- (a) country momentum ----------------
def run_momentum(px, R, months, topk, skip=0, vt=True):
    mom = mom_signal(px, months, skip)
    reb = month_first_positions(px.index)
    W = rank_weights(mom, topk, reb)
    return net_of(W, R, vt=vt) + (W,)

# ---------------- (b) country carry ----------------
def run_carry(px, R, gross=2.0, lag_m=1, vt=True):
    ys = {}
    for f in CARRY:
        s = pd.read_csv(f"{ROOT}/tools/quant/data/more_fred/{f}.csv", index_col=0, parse_dates=True)['value'].astype(float)
        ys[CARRY[f]] = s
    Y = pd.DataFrame(ys).sort_index()
    Y_lag = Y.shift(lag_m)                      # publication-lag safety: use last month's yield
    dev = Y_lag.sub(Y_lag.mean(axis=1), axis=0)
    wts = dev.div(dev.abs().sum(axis=1), axis=0).mul(gross)   # gross-normalized L/S
    # carry daily: weight effective on first trading day of the month after yield publication
    W = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    prev = None
    reb = month_first_positions(px.index)
    for i, d in enumerate(px.index):
        if i in reb:
            # latest published yield with period < current month
            avail = Y_lag[Y_lag.index.to_period('M') < d.to_period('M')]
            if len(avail) and avail.iloc[-1].notna().sum() == len(CARRY):
                # TDD fix (2026-09-06): apply the GROSS-NORMALIZED deviation weights,
                # NOT raw yield levels (raw 4.5% yield => 4.5x book = 22.6x gross).
                prev = wts.loc[avail.index[-1]].reindex(W.columns).fillna(0.0)
        if prev is not None:
            W.iloc[i] = prev.values
    return net_of(W, R, vt=vt) + (W,)

# ---------------- (c) EM/DM rotation ----------------
def run_emdm(R_em, R_dm, months, skip=0, longshort=True, vt=True, gross=2.0):
    em_px = (1 + R_em.fillna(0)).cumprod(); dm_px = (1 + R_dm.fillna(0)).cumprod()
    mom_em = em_px.shift(skip * 21) / em_px.shift(months * 21) - 1
    mom_dm = dm_px.shift(skip * 21) / dm_px.shift(months * 21) - 1
    idx = R_em.index
    W = pd.DataFrame({'EM': 0.0, 'DM': 0.0}, index=idx)
    reb = month_first_positions(idx)
    prev = None
    for i, d in enumerate(idx):
        if i in reb and i > 0:
            e, m = mom_em.iloc[i - 1], mom_dm.iloc[i - 1]
            if np.isfinite(e) and np.isfinite(m):
                if e >= m:
                    prev = pd.Series({'EM': gross / 2 if longshort else gross, 'DM': -gross / 2 if longshort else 0.0})
                else:
                    prev = pd.Series({'EM': -gross / 2 if longshort else 0.0, 'DM': gross / 2 if longshort else gross})
        if prev is not None:
            W.iloc[i] = prev.values
    R2 = pd.DataFrame({'EM': R_em, 'DM': R_dm})
    return net_of(W, R2, vt=vt) + (W,)

def no_lookahead_check(px, months, topk, probe='2015-06-30'):
    """TDD spot-check: weights through probe date must be identical when future data is removed."""
    reb = month_first_positions(px.index)
    W_full = rank_weights(mom_signal(px, months), topk, reb)
    px_cut = px.loc[:probe]
    W_cut = rank_weights(mom_signal(px_cut, months), topk, month_first_positions(px_cut.index))
    a = W_full.loc[:probe].round(10); b = W_cut.round(10)
    return a.equals(b)

if __name__ == '__main__':
    print('=== no-lookahead spot check (12m,k3) ===')
    px = px_frame(UNIV)
    R = px.pct_change()
    common_ok = no_lookahead_check(px, 12, 3)
    print('weights identical with future truncated:', common_ok)
    assert common_ok, 'LOOKAHEAD DETECTED'

    print('\n=== (a) country momentum sweep: net SR (vol-targeted, T+1, 6.4bps+borrow) ===')
    results = {}
    grid = []
    for months in [6, 9, 12, 15, 18]:
        for topk in [2, 3, 4]:
            net, We, gross, W = run_momentum(px, R, months, topk)
            net = net.dropna(); net = net[net.index >= '2007-12-01']
            results[(months, topk)] = metrics.sharpe_d(net)
            grid.append((months, topk))
    for k in grid:
        star = ' *' if k == (12, 3) else ''
        print(f"  lookback={k[0]:>2}m topk={k[1]}  SR={results[k]:6.2f}{star}")
    peak = max(results.values()); pk = [k for k, v in results.items() if v == peak][0]
    print(f"  peak SR={peak:.2f} at {pk}; chosen (12,3) SR={results[(12,3)]:.2f} "
          f"-> within 20% of peak: {results[(12,3)] >= 0.8*peak}")
    nb_ok = all(results.get(k, -9) >= 0.8 * peak for k in [(9,3),(15,3),(12,2),(12,4)])
    print(f"  neighbors (9,3),(15,3),(12,2),(12,4) all >= 0.8*peak: {nb_ok}")

    print('\n=== (a) chosen config full gates: 12m, topk3 ===')
    net, We, gross, W = run_momentum(px, R, 12, 3)
    res_a = evaluate('INTL_CountryMom_12m_k3', net, We, R)
    net121, We121, _, W121 = run_momentum(px, R, 12, 3, skip=1)
    res_a121 = evaluate('INTL_CountryMom_12-1m_k3', net121, We121, R)

    print('\n=== (b) country carry (IRLTLT 10y diff-weighted equity, 1m pub lag) ===')
    pxc = px_frame(list(CARRY.values()))
    Rc = pxc.pct_change()
    netb, Web, grossb, Wb = run_carry(pxc, Rc)
    res_b = evaluate('INTL_Carry10y_6ccy', netb, Web, Rc)
    netb0, Web0, _, Wb0 = run_carry(pxc, Rc, lag_m=2)
    res_b2 = evaluate('INTL_Carry10y_6ccy_lag2m', netb0, Web0, Rc)

    print('\n=== (c) EM vs DM rotation 12m ===')
    R_em, R_dm = R[EM].mean(axis=1), R[DM].mean(axis=1)
    netc, Wec, _, Wc = run_emdm(R_em, R_dm, 12, longshort=True)
    resc = evaluate('INTL_EMDM_LS_12m', netc, Wec, pd.DataFrame({'EM': R_em, 'DM': R_dm}))
    netd, Wed, _, Wd = run_emdm(R_em, R_dm, 12, longshort=False)
    resd = evaluate('INTL_EMDM_LongOnly_12m', netd, Wed, pd.DataFrame({'EM': R_em, 'DM': R_dm}))

    print('\n=== summary ===')
    for nm, r in [('mom12k3', res_a), ('mom12-1k3', res_a121), ('carry', res_b), ('carry_lag2', res_b2),
                  ('emdm_ls', resc), ('emdm_lo', resd)]:
        print(f"  {nm:12s} SR={r['sr']:5.2f} H1={r['h1']:5.2f} H2={r['h2']:5.2f} negyr={r['neg']:2d} "
              f"worst={r['worst']*100:6.1f}% p={r['p']:.3f} corr={r['corr']:6.3f} PASS={r['pass']}")
