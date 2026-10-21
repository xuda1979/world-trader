#!/usr/bin/env python3
"""HUNT_CMDT2 round 1 — commodity ETF cross-asset momentum / carry / sector rotation / inflation regime.

Charter tests (all on tools/quant/data/more_etf + more_fred):
 (a) COMMODITY CARRY (proxied): no futures curve on disk -> carry = ETF-vs-spot basis drag.
     Spot leg = FRED global commodity price index per complex, publication-lagged; an ETF that
     persistently LAGS its spot index is bleeding roll yield (contango drag) => short-carry
     candidate; one that LAPS its spot => backwardation => long-carry candidate.
 (b) COMMODITY MOMENTUM: cross-sectional rank 12m, hold 3m, L/S top/bottom-k + long-only.
 (c) SECTOR ROTATION: energy vs precious vs agriculture sector momentum (12m), monthly hold.
 (d) INFLATION-REGIME: long the commodity book when realized inflation momentum (T10YIE trend
     or CPI y/y delta) is rising, flat/cash otherwise.

Honesty per GATES_CONTRACT.md:
 T+1 (effective weights = target.shift(1)); costs 6.4bps on FULL |dW| + 0.5%/yr borrow on short
 notional; vol-target 10% ann trailing-expanding (clip <= 3.0); scramble 200x on FINAL weights
 with re-costing (pass requires real SR > 0 AND p <= 0.05); halves >= 0.5; <= 2 neg years each
 > -5%; FULL net SR >= 1.0; |corr| < 0.15 vs champion GOAL100_RAWEW13v2_WEIGHTED_GEAR16.
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

# Core liquid single-commodity ETFs: 9 names, all live by 2011-12, common window 2011-12 -> 2026-09
CORE9 = ['USO', 'UNG', 'GLD', 'SLV', 'CPER', 'CORN', 'WEAT', 'SOYB', 'CANE']
# Extended universe for momentum sweeps (adds broad/index + agri-equity; mixed starts)
EXT12 = CORE9 + ['DBC', 'GSG', 'DBA']
# Sector buckets for rotation: (c)
SECTORS = {'ENE': ['USO', 'UNG'], 'PRE': ['GLD', 'SLV'], 'AGR': ['CORN', 'WEAT', 'SOYB', 'CANE']}
# Spot proxy per complex: FRED global spot index (commodity-agriculture/copper etc). Used for (a).
CARRY_PAIRS = {  # ETF -> FRED spot index proxying the same complex
    'CORN': 'PMAIZMTUSDM', 'WEAT': 'PWHEAMTUSDM', 'CANE': 'PSUGAUSAUSDM', 'SOYB': 'PSOYBUSDM',
    'CPER': 'PCOPPUSDM', 'USO': 'MCOILWTICO',
}
CARRY_ETFS = list(CARRY_PAIRS.keys())
SPOT_PUB_LAG_DAYS = 37        # >= 30: FRED monthly spot prints arrive mid-following-month; safety margin
CARRY_Q = 63                  # trailing window (trading days) for spot-vs-ETF gap carry


def load_close(sym):
    df = pd.read_csv(f"{ROOT}/tools/quant/data/more_etf/{sym}.csv", index_col=0, parse_dates=True)
    return df['close'].astype(float)


def px_frame(syms):
    return pd.concat({s: load_close(s) for s in syms}, axis=1).sort_index()


def spot_panel(pairs):
    """Publication-lagged daily spot panel: each FRED monthly print is delayed by
    SPOT_PUB_LAG_DAYS, then forward-filled to business days. No same-month print can be seen."""
    out = {}
    for etf, fred in pairs.items():
        s = pd.read_csv(f"{ROOT}/tools/quant/data/more_fred/{fred}.csv",
                        index_col=0, parse_dates=True)['value'].astype(float)
        s.index = s.index + pd.Timedelta(days=SPOT_PUB_LAG_DAYS)
        out[etf] = s.resample('B').ffill()
    return pd.DataFrame(out).sort_index()


def carry_signal(etf_px, S, q=CARRY_Q):
    """Annualized basis carry: q-day spot return minus q-day ETF return, divided by (q/252).
    Positive = ETF underperforms its own spot complex = roll drag = backwardation-ish => long.
    Uses ONLY lagged spot (publication-safe) and ETF closes <= t."""
    letf = np.log(etf_px)
    lspot = np.log(S.reindex(etf_px.index).ffill())
    gap = (lspot - letf).diff(q)
    return (gap / (q / 252.0)).iloc[:, :]


def quarter_starts(index):
    """Positions of the first trading day of each calendar quarter."""
    per = pd.Series(index, index=index).groupby(index.to_period('Q')).first()
    return sorted(set(index.searchsorted(per.values)))


def month_first_positions(index):
    per = pd.Series(index, index=index).groupby(index.to_period('M')).first()
    return sorted(set(index.searchsorted(per.values)))


def mom_signal(px, months=12, skip=0):
    return px.shift(skip * 21) / px.shift(months * 21) - 1.0


def live_mask(px, months):
    """True where at least min_frac of the universe has a valid 12m momentum (no stale names)."""
    m = mom_signal(px, months)
    return m.notna().sum(axis=1) >= max(2, int(round(0.8 * px.shape[1])))


def run_momentum(px, R, months=12, topk=3, hold=3, long_only=False, gross=2.0):
    """XS momentum: rank trailing `months`m return; long top-k, short bottom-k; rebalance on the
    first trading day of every `hold`-th month (hold=3 -> quarter). Weights set from the
    PREVIOUS day's momentum (data <= t-1), held constant between rebalances."""
    mom = mom_signal(px, months)
    idx = px.index
    n = px.shape[1]
    # hold = every `hold`-th month from series start (deterministic month-sequence filter)
    ms = month_first_positions(idx)
    mseq = {p: j for j, p in enumerate(sorted({idx[i].to_period('M') for i in ms}))}
    rebset = {i for i in ms if mseq[idx[i].to_period('M')] % hold == 0}
    W = pd.DataFrame(0.0, index=idx, columns=px.columns)
    prev = None
    for i in range(len(idx)):
        if i in rebset and i > 0:
            m = mom.iloc[i - 1]                      # T+1: yesterday's ranks
            ok = m.notna().sum() >= max(2, int(round(0.8 * n)))
            if ok:
                r = m.rank(ascending=False, na_option='keep')
                w = pd.Series(0.0, index=px.columns)
                w[r <= topk] = gross / (2 * topk)
                if not long_only:
                    w[r > n - topk] = -gross / (2 * topk)
                prev = w
        if prev is not None:
            W.iloc[i] = prev.values
    return net_of(W, R) + (W,)


def run_carry(px, R, S, k=2, hold=3, gross=2.0):
    """XS roll-drag carry: rank by annualized ETF-vs-spot gap carry (publication-lagged spot);
    long highest carry (backwardation), short lowest (contango). Quarterly rebalance.
    Universe = ETFs with a spot proxy (columns of S); the rest of px is ignored."""
    etfs = [c for c in S.columns if c in px.columns]
    px = px[etfs]
    R = R[etfs]
    carry = carry_signal(px, S)
    idx = px.index
    n = len(etfs)
    ms = month_first_positions(idx)
    mseq = {p: j for j, p in enumerate(sorted({idx[i].to_period('M') for i in ms}))}
    rebset = {i for i in ms if mseq[idx[i].to_period('M')] % hold == 0}
    W = pd.DataFrame(0.0, index=idx, columns=px.columns)
    prev = None
    for i in range(len(idx)):
        if i in rebset and i > 0:
            c = carry.iloc[i - 1]
            if c.notna().sum() >= max(2, int(round(0.8 * n))):
                r = c.rank(ascending=False, na_option='keep')
                w = pd.Series(0.0, index=px.columns)
                w[r <= k] = gross / (2 * k)
                w[r > n - k] = -gross / (2 * k)
                prev = w
        if prev is not None:
            W.iloc[i] = prev.values
    return net_of(W, R) + (W,)


def run_sector_rotation(px, R, months=12, hold=3, gross=2.0, long_only=False):
    """Sector momentum rotation: energy / precious / agri baskets (equal-weight of members),
    rank sector 12m momentum, long top sector (short bottom if L/S)."""
    baskets = {}
    for s, members in SECTORS.items():
        Rp = R[members].mean(axis=1)
        baskets[s] = (1 + Rp.fillna(0)).cumprod()
    B = pd.DataFrame(baskets)
    mom = mom_signal(B, months)
    idx = R.index
    ms = month_first_positions(idx)
    mseq = {p: j for j, p in enumerate(sorted({idx[i].to_period('M') for i in ms}))}
    rebset = {i for i in ms if mseq[idx[i].to_period('M')] % hold == 0}
    Ws = pd.DataFrame(0.0, index=idx, columns=list(SECTORS))
    prev = None
    for i in range(len(idx)):
        if i in rebset and i > 0:
            m = mom.iloc[i - 1]
            if m.notna().all():
                order = m.rank(ascending=False, na_option='keep')
                w = pd.Series(0.0, index=Ws.columns)
                top = order[order == 1].index
                w[top] = gross
                if not long_only:
                    bot = order[order == 3].index
                    w[bot] = -gross
                prev = w
        if prev is not None:
            Ws.iloc[i] = prev.values
    # expand sector weights to member ETFs (equal-weight inside basket)
    W = pd.DataFrame(0.0, index=idx, columns=px.columns)
    for s, members in SECTORS.items():
        if s in Ws:
            W.loc[:, members] = np.repeat(Ws[s].values[:, None], len(members), axis=1) / len(members)
    return net_of(W, R) + (W,)


def run_inflation_regime(px, R, mode='t10yie', q=63, gross=1.0, hold=1):
    """(d) Inflation-regime gate: long the equal-weight CORE9 book (scaled to gross) only when
    realized inflation momentum is RISING; flat otherwise. Signal = lagged monthly change of
    (mode='t10yie': T10YIE q-day change; mode='cpi': CPI y/y minus its own 6m-ago value).
    Gate decision uses the latest print >= 37 days old (publication lag), T+1 executed."""
    if mode == 't10yie':
        br = pd.read_csv(f"{ROOT}/tools/quant/data/more_fred/T10YIE.csv",
                         index_col=0, parse_dates=True)['value'].astype(float)
        sig = br.diff(q)                       # breakeven q-day trend
        pub_lag = 5                            # daily series, ~weekly revision lag
    else:
        cpi = pd.read_csv(f"{ROOT}/tools/quant/data/more_fred/CPIAUCSL.csv",
                          index_col=0, parse_dates=True)['value'].astype(float)
        yoy = np.log(cpi).diff(12)
        sig = (yoy - yoy.shift(6)).dropna()    # y/y acceleration vs 6m ago
        pub_lag = 37                           # CPI for month M published mid-M+1
    sig.index = sig.index + pd.Timedelta(days=pub_lag)
    sig = sig[sig.index <= px.index[-1]]
    idx = px.index
    sig_d = sig.reindex(idx).ffill()
    gate = (sig_d > 0).astype(float).shift(1).fillna(0.0)   # T+1 on the gate itself
    # hold: only allow gate to flip on month starts (avoid daily churn)
    if hold > 1:
        ms = set(month_first_positions(idx))
        g = gate.copy()
        last = 0.0
        for i in range(len(idx)):
            if i not in ms:
                g.iloc[i] = last
            else:
                last = g.iloc[i]
        gate = g
    W = pd.DataFrame(0.0, index=idx, columns=px.columns)
    W.loc[:, :] = gate.values[:, None] * gross / px.shape[1]
    return net_of(W, R) + (W, gate)


def net_of(W, R, vt=True, target=0.10):
    """T+1 effective weights, trailing vol-target, 6.4bps full |dW| + 0.5%/yr borrow on shorts."""
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
    assets) against real date-aligned returns, RE-APPLY costs, p = P(SR_scr >= real SR)."""
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
    """Trim net series to the first day the book is actually live (|We|>0)."""
    live = (We.fillna(0.0) != 0).any(axis=1)
    if not live.any():
        return net.iloc[0:0]
    return net[net.index >= live.idxmax()]


def evaluate(name, net, We, R, verbose=True):
    net = trim_warmup(net, We)
    if len(net) < 252:
        res = dict(sr=np.nan, n=len(net), ok={}, pass_=False, p=np.nan, corr=np.nan,
                   h1=np.nan, h2=np.nan, neg=np.nan, worst=np.nan, vol=np.nan, ann=np.nan)
        if verbose:
            print(f"[{name}] n={res['n']} (< 1y) -> FAIL (insufficient history)")
        return res
    sr = metrics.sharpe_d(net); h1, h2 = metrics.half_split(net)
    neg, worst = metrics.neg_years(net)
    p = scramble_p(We, R, net)
    corr = bgates.corr_to(CHAMP, net)
    vol = net.std() * np.sqrt(252)
    res = dict(sr=sr, h1=h1, h2=h2, neg=neg, worst=worst, p=p, corr=corr, vol=vol,
               ann=metrics.ann_geo(net), n=len(net),
               start=net.index[0].date(), end=net.index[-1].date())
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


if __name__ == '__main__':
    print('=== (b) CORE9 universe + data sanity ===')
    px = px_frame(CORE9)
    print(px.count().to_string())
    R = px.pct_change()
    S = spot_panel(CARRY_PAIRS)
    print('\nspot panel coverage:')
    print(S.count().to_string())

    print('\n=== full sweep ===')
    results = {}

    print('\n--- (a) carry: rank annualized ETF-vs-spot gap, quarterly ---')
    for k in [1, 2, 3]:
        for hold in [1, 3]:
            net, We, gross, W = run_carry(px, R, S, k=k, hold=hold)
            results[f'carry k{k} h{hold}'] = evaluate(f'carry k{k} h{hold}', net, We, R)

    print('\n--- (b) XS momentum 12m hold3 (charter) ---')
    for months in [6, 9, 12, 15, 18]:
        for topk in [2, 3, 4]:
            net, We, gross, W = run_momentum(px, R, months=months, topk=topk, hold=3)
            results[f'mom {months}m k{topk} h3'] = evaluate(f'mom {months}m k{topk} h3', net, We, R)
    # hold-period sensitivity on the charter config
    for hold in [1, 2, 3, 6]:
        net, We, gross, W = run_momentum(px, R, months=12, topk=3, hold=hold)
        results[f'mom 12m k3 h{hold}'] = evaluate(f'mom 12m k3 h{hold}', net, We, R)
    # long-only variant
    for months, topk in [(12, 3), (6, 2), (9, 2), (3, 2)]:
        net, We, gross, W = run_momentum(px, R, months=months, topk=topk, hold=3, long_only=True)
        results[f'momLO {months}m k{topk} h3'] = evaluate(f'momLO {months}m k{topk} h3', net, We, R)

    print('\n--- (c) sector rotation ENE/PRE/AGR ---')
    for months in [3, 6, 12]:
        for lo in [False, True]:
            net, We, gross, W = run_sector_rotation(px, R, months=months, hold=3, long_only=lo)
            tag = 'LO' if lo else 'LS'
            results[f'sector {months}m {tag}'] = evaluate(f'sector {months}m {tag}', net, We, R)

    print('\n--- (d) inflation regime gate ---')
    for mode in ['t10yie', 'cpi']:
        for gross in [1.0, 2.0]:
            net, We, gbook, W, gate = run_inflation_regime(px, R, mode=mode, gross=gross)
            results[f'infl {mode} g{gross}'] = evaluate(f'infl {mode} g{gross}', net, We, R)

    print('\n=== SUMMARY (best by SR) ===')
    rows = [(k, v.get('sr'), v.get('pass')) for k, v in results.items() if v and np.isfinite(v.get('sr', np.nan))]
    for k, sr, ps in sorted(rows, key=lambda x: -(x[1] if x[1] == x[1] else -9)):
        print(f"  {k:<22} SR={sr:6.2f}  PASS={ps}")

    # plateau check on the best momentum config vs its grid neighbors
    grid = {}
    for k, v in results.items():
        if k.startswith('mom ') and k.endswith('h3'):
            parts = k.split()
            months, topk = int(parts[1][:-1]), int(parts[2][1:])
            grid[(months, topk)] = v['sr']
    peak = max(grid.values())
    pk = [kk for kk, v in grid.items() if v == peak][0]
    print(f"\nmomentum grid peak SR={peak:.2f} at {pk}")

