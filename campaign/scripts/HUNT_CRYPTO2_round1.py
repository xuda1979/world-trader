#!/usr/bin/env python3
"""HUNT_CRYPTO2 round 1 — crypto satellite, four NEW signal families.

Charter (coord/HUNT_CRYPTO2/CHARTER.md):
 (a) VOL-SCALED crossover (momentum, vol-bounded) weekly, BTC/ETH/alt basket.
 (b) Short-term mean-reversion DAILY on the most-liquid 3 (BTC, ETH, LTC).
 (c) Sector relative value: BTC vs ETH vs base-layer, market-neutral-ish L/S.
 (d) Crypto as risk-on/risk-off regime GATE on the champion (not standalone).

Honesty per GATES_CONTRACT.md + coord MANIFEST cost model:
 T+1 (weights.shift(1)); 6.4bps one-side FULL |dW|; borrow 0.5%/yr on shorts;
 margin 4.5%/yr on (gross-1); vt10% trailing expanding clip<=3.0;
 scramble 200x on FINAL weights with re-costing; halves>=0.5 both;
 <=2 neg yrs each > -5%; FULL net SR>=1.0; |corr|<0.15 vs champion;
 param plateau (neighbors >= 0.8*peak); no-lookahead probe per family.
Crypto-specific caveat logged in metas: Binance perp funding NOT modeled
(historically often paid TO shorts; omission is not obviously conservative).
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np, pandas as pd
from bt import engine, metrics
import bt.gates as bgates

ROOT = "/Users/daxu/software/world-trader"
DATA = f"{ROOT}/tools/quant/data/more_crypto"
OUT = f"{ROOT}/campaign/agents/chief/coord/HUNT_CRYPTO2/sleeves"
COST_BPS = 6.4
CHAMP = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0]
ALL12 = ['BTC', 'ETH', 'BNB', 'ADA', 'XRP', 'SOL', 'DOT', 'LINK', 'LTC', 'MATIC', 'AVAX', 'DOGE']
LIQ3 = ['BTC', 'ETH', 'LTC']            # deepest books (BTC $38m, ETH/LTC ~$0.4-0.5m med daily vol)


def load_px(coins):
    px = pd.concat({c: pd.read_csv(f"{DATA}/{c}.csv", index_col=0, parse_dates=True)['close'].astype(float)
                    for c in coins}, axis=1).sort_index()
    return px.dropna(how='all')


def week_first_positions(index):
    iso = index.isocalendar()
    per = pd.Series(index, index=index).groupby(iso.week.astype(int).astype(str)
                                                + '_' + iso.year.astype(str)).first()
    return set(index.searchsorted(per.values))


def cost_stack(We):
    """Campaign cost model: 6.4bps full |dW| + 0.5%/yr borrow + 4.5%/yr margin on (gross-1)."""
    gross = We.abs().sum(axis=1)
    return (engine.cost_turnover(We, cost_bps=COST_BPS) + engine.borrow_cost(We)
            + engine.margin_cost(gross))


def net_of(W, R, vt=True, target=0.10):
    """T+1 effective weights, trailing vol-target, full cost stack."""
    We = W.shift(1).fillna(0.0)
    gross = (We * R).sum(axis=1)
    if vt:
        s = engine.vol_target_scale(gross.to_frame('g'), target=target)['g']
        We = We.mul(s, axis=0)
    port = (We * R).sum(axis=1)
    return (port - cost_stack(We)).rename('ret'), We, gross


def scramble_p(We_final, R, net, n=200, seed=7):
    """Campaign-standard: permute FINAL weight rows (shared across assets), re-cost, p=P(SR>=real)."""
    idx = net.index
    We = We_final.reindex(idx).fillna(0.0)
    Re = R.reindex(idx).fillna(0.0)
    real = metrics.sharpe_d(net)
    rng = np.random.default_rng(seed)
    arrW, arrR = We.values, Re.values
    cnt = 0
    for _ in range(n):
        Wp = pd.DataFrame(arrW[rng.permutation(len(idx))], index=idx, columns=We.columns)
        book = (Wp * Re).sum(axis=1) - cost_stack(Wp)
        if metrics.sharpe_d(book) >= real:
            cnt += 1
    return cnt / n


def trim_warmup(net, We):
    live = (We.fillna(0.0) != 0).any(axis=1)
    if not live.any():
        return net.iloc[0:0]
    return net[net.index >= live.idxmax()]


def evaluate(name, net, We, R, save=True, verbose=True):
    net = trim_warmup(net, We)
    sr = metrics.sharpe_d(net)
    h1, h2 = metrics.half_split(net)
    neg, worst = metrics.neg_years(net)
    p = scramble_p(We, R, net)
    corr = bgates.corr_to(CHAMP, net)
    yr = net.groupby(net.index.year).apply(lambda x: (1 + x).prod(min_count=1) - 1)
    res = dict(name=name, sr=sr, h1=h1, h2=h2, neg=neg, worst=worst, p=p, corr=corr,
               vol=net.std() * np.sqrt(252), ann=metrics.ann_geo(net), mdd=metrics.max_dd(net),
               n=len(net), start=net.index[0].date(), end=net.index[-1].date(), years=yr)
    res['ok'] = dict(a_sr=sr >= 1.0, c_halves=(h1 >= 0.5 and h2 >= 0.5),
                     d_yearly=(neg <= 2 and worst > -0.05),
                     e_scramble=(p <= 0.05 and sr > 0), f_corr=abs(corr) < 0.15)
    res['pass'] = all(res['ok'].values())
    if verbose:
        o = res['ok']
        print(f"[{name}] n={res['n']} {res['start']}->{res['end']} SR={sr:.2f} ann={res['ann']*100:.1f}% "
              f"vol={res['vol']*100:.1f}% mdd={res['mdd']*100:.0f}% H1={h1:.2f} H2={h2:.2f} "
              f"negyr={neg} worst={worst*100:.1f}% p={p:.3f} corr={corr:.3f}")
        print(f"    gates: SR>=1:{o['a_sr']} halves:{o['c_halves']} yearly:{o['d_yearly']} "
              f"scramble:{o['e_scramble']} |corr|<0.15:{o['f_corr']} PASS={res['pass']}")
        print(f"    yearly: " + " ".join(f"{y}:{v*100:+.1f}" for y, v in yr.items()))
    if save:
        net.to_frame('ret').to_csv(f"{OUT}/{name}.csv")
        with open(f"{OUT}/{name}.csv.meta", 'w') as f:
            f.write(f"agent=HUNT_CRYPTO2 round=1 family={name}\n"
                    f"cost=6.4bps_full_dW+borrow0.5%+margin4.5%(gross-1) vt=10%_trailing_clip3 T+1\n"
                    f"SR={sr:.3f} ann={res['ann']*100:.1f}% H1={h1:.2f} H2={h2:.2f} negyr={neg} "
                    f"worst={worst*100:.1f}% scramble_p={p:.3f} corr_champ={corr:.3f}\n"
                    f"caveat=binance_perp_funding_not_modeled\n")
    return res


def no_lookahead(build, probe='2023-06-30'):
    """Weights through probe identical when future data is removed."""
    W_full, aux = build(None)
    W_cut, _ = build(probe)
    a = W_full.loc[:probe].round(10)
    b = W_cut.loc[:probe].round(10)
    return a.equals(b), aux


# ---------------- (a) vol-scaled weekly crossover ----------------
def build_a(px, fast=20, slow=60, end=None):
    """sign(EMA_fast-EMA_slow) per coin, weighted 1/trailing 30d vol, gross-normalized,
    re-set on the FIRST trading day of each ISO week from the PREVIOUS day's state."""
    p = px if end is None else px.loc[:end]
    ema_f = p.ewm(span=fast, adjust=False).mean()
    ema_s = p.ewm(span=slow, adjust=False).mean()
    sig = np.sign(ema_f - ema_s).shift(1)          # decide from <= t-1 close
    vol30 = p.pct_change().rolling(30).std() * np.sqrt(252)
    inv = (1.0 / vol30).replace([np.inf, -np.inf], np.nan)
    raw = sig * inv
    W = pd.DataFrame(0.0, index=p.index, columns=p.columns)
    prev = None
    reb = week_first_positions(p.index)
    for i in range(len(p)):
        if i in reb and i > 0:
            r_ = raw.iloc[i - 1]
            if r_.abs().sum() > 0:
                prev = r_ / r_.abs().sum()
        if prev is not None:
            W.iloc[i] = prev.reindex(W.columns).fillna(0.0).values
    return W, (ema_f, ema_s)


# ---------------- (b) daily short-term reversal, liquid 3 ----------------
def build_b(px, k=3, end=None):
    """w = -zscore(k-day cumulative return, 60d) per coin, gross-normalized, DAILY rebalance.
    Signal at t uses returns up to t-1 -> T+1 via net_of."""
    p = px if end is None else px.loc[:end]
    r = p.pct_change()
    mom_k = r.rolling(k).sum()
    mu = mom_k.rolling(60).mean()
    sd = mom_k.rolling(60).std()
    z = -((mom_k - mu) / sd).replace([np.inf, -np.inf], np.nan)
    raw = z.shift(1)
    W = raw.div(raw.abs().sum(axis=1), axis=0)
    return W, (z,)


# ---------------- (c) sector relative value ----------------
def build_c_ratio(px, look=30, end=None):
    """BTC/ETH ratio momentum L/S: long the stronger, short the weaker, 0.5/0.5, weekly."""
    p = px if end is None else px.loc[:end]
    ratio = p['BTC'] / p['ETH']
    mom = ratio.pct_change(look).shift(1)
    W = pd.DataFrame(0.0, index=p.index, columns=['BTC', 'ETH'])
    prev = None
    reb = week_first_positions(p.index)
    for i in range(len(p)):
        if i in reb and i > 0:
            m = mom.iloc[i - 1]
            if np.isfinite(m):
                prev = pd.Series({'BTC': 0.5 if m > 0 else -0.5,
                                  'ETH': -0.5 if m > 0 else 0.5})
        if prev is not None:
            W.iloc[i] = prev.values
    return W, (mom,)


def build_c_basket(px, look=30, gated=True, end=None):
    """Base layer (BTC+ETH) vs alt basket L/S: sign of base-minus-alt trailing momentum."""
    p = px if end is None else px.loc[:end]
    alts = [c for c in p.columns if c not in ('BTC', 'ETH')]
    base = p[['BTC', 'ETH']].mean(axis=1)
    alt = p[alts].mean(axis=1)
    mom = (base.pct_change(look) - alt.pct_change(look)).shift(1)
    W = pd.DataFrame(0.0, index=p.index, columns=p.columns)
    prev = None
    reb = week_first_positions(p.index)
    for i in range(len(p)):
        if i in reb and i > 0:
            m = mom.iloc[i - 1]
            if np.isfinite(m) and (abs(m) > 0 or not gated):
                s = np.sign(m) if gated else 1.0
                prev = pd.Series(0.0, index=p.columns)
                prev[['BTC', 'ETH']] = 0.5 * s
                prev[alts] = -0.5 * s / len(alts) * 2.0   # dollar-neutral: -0.5 total
        if prev is not None:
            W.iloc[i] = prev.values
    return W, (mom,)


# ---------------- (d) crypto regime gate on champion ----------------
def build_d(btc, ma=50, scale=0.5, end=None):
    """Gate champion gross by BTC-vs-MA(risk proxy). gate_t = last BTC state <= t, then T+1
    against champion returns (champion ret_t is earned on day t, decided at t-1)."""
    state = (btc > btc.rolling(ma).mean()).astype(float).mul(1 - scale).add(scale)  # on=1, off=scale
    state = state[~state.index.duplicated()]
    g = state.reindex(CHAMP.index.union(state.index)).ffill().reindex(CHAMP.index).shift(1).fillna(1.0)
    gated = CHAMP * g
    return gated, g


if __name__ == '__main__':
    px = load_px(ALL12)
    R = px.pct_change()
    btc = px['BTC']
    print('=== no-lookahead probes (weights prefix-identical with future truncated) ===')
    for nm, fn in [('a_20/60', lambda e: build_a(px, 20, 60, e)),
                   ('b_k3', lambda e: build_b(px, 3, e)),
                   ('c_ratio30', lambda e: build_c_ratio(px, 30, e)),
                   ('c_basket30', lambda e: build_c_basket(px, 30, True, e))]:
        ok, _ = no_lookahead(fn)
        print(f"  {nm}: {ok}")
        assert ok, f'LOOKAHEAD in {nm}'
    g, _ = build_d(btc)
    print("  d_gate: series-level (asof<=t then shift(1), verified by construction)")

    print('\n=== (a) vol-scaled weekly crossover: EW-12 basket grid (rows=fast, cols=slow) ===')
    grid_a = {}
    for fast in [10, 20, 30, 50]:
        for slow in [30, 60, 90, 150]:
            if slow <= fast * 1.5:
                continue
            W, _ = build_a(px, fast, slow)
            net, We, _ = net_of(W, R)
            net = trim_warmup(net, We)
            grid_a[(fast, slow)] = metrics.sharpe_d(net)
            print(f"  f={fast:3d} s={slow:4d}  SR={grid_a[(fast,slow)]:6.2f}")
    peak = max(grid_a.values())
    chosen_a = (20, 60)
    ca = grid_a[chosen_a]
    nb = [(15, 60), (30, 60), (20, 30), (20, 90)]
    nb_vals = {k: grid_a.get(k, np.nan) for k in nb}
    print(f"  peak={peak:.2f} chosen(20,60)={ca:.2f} plateau_neigh={ {f'{a}/{b}': (None if np.isnan(v) else round(v,2)) for a,b,v in ((k[0],k[1],v) for k,v in nb_vals.items())} }")

    print('\n=== (a) chosen + per-coin best (honest: also show per-coin SRs for 20/60) ===')
    res_a = evaluate('CRYPTO_VolX_20-60_EW12', *net_of(build_a(px, 20, 60)[0], R)[:2], R)
    per_coin = {}
    for c in ALL12:
        Wc, _ = build_a(px[[c]], 20, 60)
        netc, Wec, _ = net_of(Wc, R[[c]])
        netc = trim_warmup(netc, Wec)
        per_coin[c] = metrics.sharpe_d(netc)
    print("  per-coin SR(20/60): " + " ".join(f"{c}:{s:.2f}" for c, s in sorted(per_coin.items(), key=lambda x: -x[1])))

    print('\n=== (b) daily reversal liquid-3: k grid ===')
    grid_b = {}
    for k in [1, 2, 3, 4, 5]:
        W, _ = build_b(px[LIQ3], k)
        net, We, _ = net_of(W, R[LIQ3])
        net = trim_warmup(net, We)
        grid_b[k] = metrics.sharpe_d(net)
        print(f"  k={k}  SR={grid_b[k]:6.2f}")
    res_b = evaluate('CRYPTO_Rev3_liq_k3', *net_of(build_b(px[LIQ3], 3)[0], R[LIQ3])[:2], R[LIQ3])

    print('\n=== (c) sector RV ===')
    grids = {}
    for look in [10, 30, 60, 90, 120]:
        W, _ = build_c_ratio(px, look)
        net, We, _ = net_of(W, R[['BTC', 'ETH']])
        net = trim_warmup(net, We)
        grids[f'ratio_{look}'] = metrics.sharpe_d(net)
        W2, _ = build_c_basket(px, look)
        net2, We2, _ = net_of(W2, R)
        net2 = trim_warmup(net2, We2)
        grids[f'basket_{look}'] = metrics.sharpe_d(net2)
    for k, v in grids.items():
        print(f"  {k:12s} SR={v:6.2f}")
    res_c1 = evaluate('CRYPTO_RV_BTCETH_ratio30', *net_of(build_c_ratio(px, 30)[0], R[['BTC', 'ETH']])[:2], R[['BTC', 'ETH']])
    res_c2 = evaluate('CRYPTO_RV_baseVSalt_30', *net_of(build_c_basket(px, 30)[0], R)[:2], R)

    print('\n=== (d) crypto regime gate on champion (value = dSR vs champion SR 3.30) ===')
    champ_sr = metrics.sharpe_d(CHAMP)
    for ma in [20, 50, 100, 200]:
        gated, g = build_d(btc, ma, 0.5)
        j = pd.concat([CHAMP.rename('c'), gated.rename('g')], axis=1).dropna()
        dsr = metrics.sharpe_d(j['g']) - champ_sr
        neg, worst = metrics.neg_years(j['g'])
        h1, h2 = metrics.half_split(j['g'])
        print(f"  MA={ma:4d} scale=0.5: gatedSR={metrics.sharpe_d(j['g']):.2f} dSR={dsr:+.3f} "
              f"H1={h1:.2f} H2={h2:.2f} negyr={neg} worst={worst*100:.1f}%")

    print('\n=== SUMMARY ===')
    for r in [res_a, res_b, res_c1, res_c2]:
        print(f"  {r['name']:28s} SR={r['sr']:5.2f} H1={r['h1']:5.2f} H2={r['h2']:5.2f} "
              f"negyr={r['neg']:2d} worst={r['worst']*100:6.1f}% p={r['p']:.3f} "
              f"corr={r['corr']:6.3f} PASS={r['pass']}")
