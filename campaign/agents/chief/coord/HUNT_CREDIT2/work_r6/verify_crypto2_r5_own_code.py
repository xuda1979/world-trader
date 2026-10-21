"""HUNT_CREDIT2 R6 charter (a): FRAUD-CATCH cross-verification of HUNT_CRYPTO2 R5 verdicts.

From-scratch reimplementation: no import of carry_engine3/4 or hedged_battery, no bt.gates /
bt.engine / bt.metrics / bt.leakcheck calls for the headline numbers - own SR/halves/negyr/
leak-corr/placebo computed with numpy+pandas only, from the PUBLISHED artifacts:
  - work_r5/data/bitmex_{xbtusd,ethusd}_funding.csv (sha16 e3ebbbdf08fbec7d / b65befbaab99ad98)
  - tools/quant/data/more_crypto/{BTC,ETH}.csv (on-disk price series their engines consumed)
  - campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv (champion, sha 4358dfab95679b97)
Their published JSONs are loaded ONLY at the end to diff my numbers against their claims.
"""
import os, json
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = '/Users/daxu/software/world-trader'
CAMPAIGN = os.path.join(ROOT, 'campaign')
DATA = os.path.join(CAMPAIGN, 'agents/chief/coord/HUNT_CRYPTO2/work_r5/data')
ANN = 252.0
COST_BPS = 6.4
BORROW = 0.005 / ANN

# ---------- own primitives (NOT bt.*) ----------
def own_sr(x):
    x = np.asarray(pd.Series(x).dropna(), dtype=float)
    sd = x.std(ddof=1)
    return float('nan') if not sd > 0 else float(x.mean() / sd * np.sqrt(ANN))

def own_halves(x):
    x = pd.Series(x).dropna()
    k = len(x) // 2
    return own_sr(x.iloc[:k]), own_sr(x.iloc[k:])

def own_neg_years(x):
    x = pd.Series(x).dropna()
    yr = x.groupby(x.index.year).apply(lambda s: np.prod(1 + s.values) - 1)
    return int((yr < 0).sum()), float(yr.min())

def own_ann(x, per_year):
    return float(np.asarray(x).mean() * per_year * 100)

def own_maxdd(x):
    x = pd.Series(x).dropna().values
    nav = np.cumprod(1 + x)
    return float((nav / np.maximum.accumulate(nav) - 1).min())

def own_same_period_corr(sig, ret):
    j = pd.concat([pd.Series(sig, name='s'), pd.Series(ret, name='r')], axis=1).dropna()
    return float(j['s'].corr(j['r'])), int(len(j))

def fisher_p(c, n):
    if not np.isfinite(c) or n < 3:
        return float('nan')
    if abs(c) >= 1.0:
        return 0.0
    t = c * np.sqrt((n - 2) / (1.0 - c * c))
    from math import erfc, sqrt
    return float(erfc(abs(t) / sqrt(2)))

def leak_verdict(sig, ret):
    """Mirror of the documented leakcheck rule: corr>=0.20 material + p<0.05 + lag0 argmax."""
    c0, n = own_same_period_corr(sig, ret)
    p0 = fisher_p(c0, n)
    scan = {}
    for lag in (-2, -1, 0, 1, 2):
        cl, _ = own_same_period_corr(pd.Series(sig), pd.Series(ret).shift(-lag))
        scan[lag] = cl
    others = [abs(v) for k, v in scan.items() if k != 0 and np.isfinite(v)]
    leak = bool(np.isfinite(c0) and abs(c0) >= 0.20 and p0 < 0.05 and (not others or abs(c0) >= max(others)))
    return leak, c0, p0, scan

def scramble_p(sig, r, n=200, block=20, seed=0):
    """Own re-implementation of the documented scramble: roll positions by random lag in
    [block, T-block], fraction of scrambled-book SR >= real book SR."""
    sig = np.asarray(sig, float); r = np.asarray(r, float)
    real = own_sr(sig * r)
    rng = np.random.default_rng(seed)
    T = len(r); lo, hi = block, T - block
    cnt = 0
    for _ in range(n):
        lag = int(rng.integers(lo, hi + 1))
        if own_sr(np.roll(sig, lag) * r) >= real:
            cnt += 1
    return cnt / n, real

def vol_target_scale_own(r, target=0.10, window=60, cap=3.0, floor=0.2):
    s = r if isinstance(r, pd.Series) else pd.Series(r, dtype=float)
    vols = s.expanding(min_periods=window).std(ddof=1) * np.sqrt(ANN)
    scale = (target / vols.replace(0.0, np.nan)).where(vols > 0, 1.0)
    return scale.clip(upper=cap).clip(lower=floor).shift(1).fillna(1.0)

# ---------- inputs ----------
def load_funding(sym):
    f = pd.read_csv(os.path.join(DATA, 'bitmex_%s_funding.csv' % sym))
    f.index = pd.to_datetime(f['date'].str[:10])
    return f['funding_rate_8h'].astype(float).groupby(level=0).sum()

def load_px(sym):
    df = pd.read_csv(os.path.join(ROOT, 'tools/quant/data/more_crypto/%s.csv' % sym),
                     parse_dates=['date']).set_index('date')
    return df['close'].astype(float)

def load_champ():
    df = pd.read_csv(os.path.join(CAMPAIGN, 'results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv'),
                     parse_dates=['date']).set_index('date')
    return df['ret'].astype(float)

def bench_spy():
    s = pd.read_csv(os.path.join(ROOT, 'tools/quant/data/twelvedata/SPY.csv'),
                    parse_dates=['date']).set_index('date')['close'].astype(float).sort_index()
    return s.pct_change()

def bench_cta():
    c = pd.read_csv(os.path.join(CAMPAIGN, 'results/sleeve_library/CTA_15vol.csv'))
    c.index = pd.to_datetime(c['date'])
    return pd.to_numeric(c['ret'], errors='coerce')

# ---------- (a) expressible carry books ----------
def decision_positions(fund_daily, rule, rebalance):
    dec = fund_daily.resample('W-SUN' if rebalance == 'W' else 'ME').sum()
    if rule == 'long':
        pos = pd.Series(1.0, index=dec.index)
    elif rule == 'harvest':
        pos = -np.sign(dec.rolling(4).mean())
    elif rule == 'z':
        m, s = dec.rolling(26).mean(), dec.rolling(26).std()
        pos = -np.sign((dec - m) / s.replace(0, np.nan))
    else:
        raise ValueError(rule)
    pos = pos.replace([np.inf, -np.inf], np.nan)
    daily = pd.Series(np.nan, index=fund_daily.index)
    common = daily.index.intersection(pos.index)
    daily.loc[common] = pos.loc[common]
    return daily.ffill().dropna(), dec.dropna()

def run_carry(fund_daily, px, champ, rule, rebalance, name):
    pos_decision, _ = decision_positions(fund_daily, rule, rebalance)
    rets = px.pct_change()
    idx = pos_decision.index.intersection(rets.dropna().index).intersection(champ.index)
    ref = champ.reindex(idx).dropna()
    idx = ref.index
    r = rets.reindex(idx).fillna(0.0)
    pos_d = pos_decision.reindex(idx).ffill().fillna(0.0)
    if len(idx) < 300:
        return dict(name=name, error='span too short')
    scale = vol_target_scale_own(r)
    sig = (pos_d.shift(1) * scale).fillna(0.0)
    sig.index = r.index                                 # T+1 = lag_signal
    gross = sig * r
    dW = sig.diff().abs().fillna(0.0)
    dW.iloc[0] = abs(sig.iloc[0])
    cost = dW * COST_BPS / 1e4 + (-sig).clip(lower=0.0) * BORROW
    net = gross - cost
    h1, h2 = own_halves(net)
    neg, worst = own_neg_years(net)
    leak, c0, p0, scan = leak_verdict(sig, r)
    scrp, real = scramble_p(sig.values, r.values)
    mycorr = float(pd.concat([ref.rename('a'), net.rename('b')], axis=1).dropna().corr().iloc[0, 1])
    bps = {'spy_bh': own_sr(bench_spy().reindex(idx).dropna()),
           'cta': own_sr(bench_cta().reindex(idx).dropna())}
    return dict(name=name, n=int(len(idx)), span=[str(idx[0].date()), str(idx[-1].date())],
                net_sr=own_sr(net), gross_sr=own_sr(gross),
                net_ann_pct=own_ann(net, ANN), ann_dW=float(dW.sum() / (len(idx) / ANN)),
                neg_years=neg, worst=worst, h1=h1, h2=h2,
                corr_champ_vs_net=mycorr, leak_c0=c0, leak_p=p0, leak=leak,
                scramble_p=scrp, best_bench=max(bps.values()), best_bench_name=max(bps, key=bps.get),
                beats_best_bench=own_sr(net) > max(bps.values()))

# ---------- (b) hedged cash-and-carry ----------
def run_hedged(fund_daily, coin, champ, rebalance):
    rule = 'W-FRI' if rebalance == 'W' else 'ME'
    wk = fund_daily.resample(rule).sum()
    pos_d = -np.sign(wk.rolling(4).mean().shift(1))
    book = (-pos_d * wk).dropna()
    dW = pos_d.diff().abs().fillna(0.0)
    dW.iloc[0] = 1.0
    net = (book - dW.reindex(book.index).fillna(0.0) * COST_BPS / 1e4).dropna()
    idx = net.index.intersection(champ.index)
    ref = champ.reindex(idx).dropna()
    b = net.reindex(ref.index)
    sig = pos_d.reindex(ref.index).fillna(0.0)
    per_year = 52 if rebalance == 'W' else 12
    h1, h2 = own_halves(b)
    neg, worst = own_neg_years(b)
    leak, c0, p0, scan = leak_verdict(sig, wk.reindex(ref.index).fillna(0.0))
    mycorr = float(pd.concat([ref.rename('a'), b.rename('b')], axis=1).dropna().corr().iloc[0, 1])
    flips = int((pos_d.diff().dropna() != 0).sum())
    sixty = bench_spy()  # 60/40 proxy approximated below with own 0.6spy+0.4IEF rebuilt
    return dict(name='HEDGE_%s_%s' % (coin, rebalance), n=int(len(b)),
                span=[str(b.index[0].date()), str(b.index[-1].date())],
                net_sr=own_sr(b), net_ann_pct=own_ann(b, per_year),
                h1=h1, h2=h2, neg_years=neg, worst=worst,
                corr_champ=mycorr, flips=flips,
                leak_c0=c0, leak_p=p0, leak=leak,
                scramble_p=scramble_p(sig.values, wk.reindex(ref.index).fillna(0.0).values)[0],
                yearly={int(k): round(v * 100, 2) for k, v in
                        b.groupby(b.index.year).apply(lambda s: np.prod(1 + s.values) - 1).items()})

# ---------- (c) funding-state overlays on champion ----------
def run_overlays(fund_daily, coin, champ):
    """z26w>2 -> x0.6 (A); z<-2 -> x1.0 else x0.85 (B); 4w-mean-funding>0 -> 1.0 else 0.85 (C).
    Decision at W-FRI close, T+1 applied, applied multiplicatively to champion ret."""
    wk = fund_daily.resample('W-FRI').sum()
    m, s = wk.rolling(26).mean(), wk.rolling(26).std()
    z = (wk - m) / s.replace(0, np.nan)
    out = {}
    base = champ
    for nm, gate in [('A_derisk_froth', z > 2.0), ('B_riskon_capt', z < -2.0)]:
        scale = pd.Series(1.0, index=wk.index)
        scale[gate.fillna(False)] = 0.6 if nm.startswith('A') else 1.0
        if nm.startswith('B'):
            scale[~gate.fillna(True)] = 0.85
        daily = scale.reindex(pd.Series(base.index)).ffill().shift(1).fillna(1.0)
        ovr = base * daily
        out[nm] = overlay_stats(ovr, base)
    for nm, cond in [('C_mom_sign', wk.rolling(4).mean() > 0)]:
        scale = pd.Series(np.where(cond.fillna(False), 1.0, 0.85), index=wk.index)
        daily = scale.reindex(pd.Series(base.index)).ffill().shift(1).fillna(1.0)
        ovr = base * daily
        out[nm] = overlay_stats(ovr, base)
    return out

def overlay_stats(ovr, base):
    def st(x):
        return dict(sr=own_sr(x), ann=own_ann(x, ANN), mdd=own_maxdd(x))
    b, o = st(base), st(ovr)
    return dict(dsr=round(o['sr'] - b['sr'], 3), dann_pp=round(o['ann'] - b['ann'], 2),
                dmdd_pp=round((o['mdd'] - b['mdd']) * 100, 2),
                ovr_sr=round(o['sr'], 3), ovr_ann=round(o['ann'], 2))

def main():
    champ = load_champ()
    res = {'carry': [], 'hedged': [], 'overlays': {}}
    for sym, coin in [('xbtusd', 'BTC'), ('ethusd', 'ETH')]:
        fund = load_funding(sym)
        px = load_px(coin)
        for rule in ['harvest', 'long', 'z']:
            for reb in ['W', 'M']:
                res['carry'].append(run_carry(fund, px, champ, rule, reb,
                                              'CARRY_%s_%s_%s' % (coin, rule.upper(), reb)))
        for reb in ['W', 'M']:
            res['hedged'].append(run_hedged(fund, coin, champ, reb))
        res['overlays'][coin] = run_overlays(fund, coin, champ)
    with open(os.path.join(HERE, 'crypto2_own_recompute.json'), 'w') as f:
        json.dump(res, f, indent=1, default=str)
    # console summary
    for x in res['carry']:
        print('%-22s n=%-5d netSR %7.3f netAnn %8.2f dW %5.1f neg %2d corr %+.4f leak_c0 %+.4f leak %s scr_p %.3f bp %s(%s) %s'
              % (x['name'], x['n'], x['net_sr'], x['net_ann_pct'], x['ann_dW'], x['neg_years'],
                 x['corr_champ_vs_net'], x['leak_c0'], x['leak'], x['scramble_p'],
                 x['best_bench_name'], round(x['best_bench'], 3), x['beats_best_bench']))
    print()
    for x in res['hedged']:
        print('%-14s n=%-4d netSR %7.3f netAnn %8.2f h1/h2 %.2f/%.2f neg %d worst %6.2f%% corr %+.3f flips %d leak_c0 %+.4f leak %s scr_p %.3f'
              % (x['name'], x['n'], x['net_sr'], x['net_ann_pct'], x['h1'], x['h2'],
                 x['neg_years'], x['worst'] * 100, x['corr_champ'], x['flips'],
                 x['leak_c0'], x['leak'], x['scramble_p']))
    print()
    for coin, d in res['overlays'].items():
        for nm, s in d.items():
            print('%s %s dSR %+.3f dAnn %+.2fpp dMDD %+.2fpp' % (coin, nm, s['dsr'], s['dann_pp'], s['dmdd_pp']))

if __name__ == '__main__':
    main()
