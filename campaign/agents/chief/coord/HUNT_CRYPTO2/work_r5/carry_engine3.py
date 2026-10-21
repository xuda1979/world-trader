"""R5 carry engine v3 — canonical gate wiring, verified against gates.run source.

Contract (bt/gates.py docstring): `r` = PER-UNIT returns; `sig` = positions; gates.run
judges the BOOK r_eff = sig*r for every performance gate, scrambles (sig, r), and probes
leak_probe(score=sig, ret=r). v1/v2 passed the book as `r` (judged sig^2*r = r — the sig
had no effect and every rule within a coin collapsed to raw returns). v3 fixes it:

  r   = perp return proxy, per-unit daily close-to-close (costless)
  sig = held positions = lag_signal(decision) * vol_target_scale(r)   [T+1 + trailing-only
        vt clip 3, the contract 3g transforms; |sig| ~ 1.0 scale so per-unit book = the
        unlevered carry book]
  book judged by gates = sig*r  (GROSS of costs)
  costs are charged EXPLICITLY on top: 6.4bps x full |dW| + 0.5%/yr short borrow, and the
  NET series (not the gross) is what the .meta/.csv publish; both reported.

leak_probe convention was fixture-verified before running (honest shift(1) => leak=False
p 0.60; same-period sign(r) => leak=True p 0.00).
"""
import os, sys, json
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
CAMPAIGN = os.path.join(ROOT, 'campaign')
sys.path.insert(0, CAMPAIGN)

from bt import gates as gates_mod  # noqa: E402
from bt.engine import lag_signal, vol_target_scale, COST_BPS, ANN  # noqa: E402

DATA = os.path.join(HERE, 'data')


def load_prices(sym):
    df = pd.read_csv(os.path.join(ROOT, 'tools/quant/data/more_crypto/%s.csv' % sym),
                     parse_dates=['date']).set_index('date')
    return df['close'].astype(float)


def load_funding(sym):
    f = pd.read_csv(os.path.join(DATA, 'bitmex_%s_funding.csv' % sym))
    f.index = pd.to_datetime(f['date'].str[:10])
    return f['funding_rate_8h'].astype(float).groupby(level=0).sum()


def load_benchmarks():
    # CANONICAL convention (AUDIT_GATES2 r3c load_benchmarks): pct_change() RETURN series
    # for spy/ief — beats_passive._as_ret_series' >1e3 curve heuristic does NOT trigger on
    # SPY price levels (133..773), so raw prices flow through as "returns" (the SR-101
    # pathology v3 hit). Library CTA csv is already [date,ret].
    spy = pd.read_csv(os.path.join(ROOT, 'tools/quant/data/twelvedata/SPY.csv'),
                      parse_dates=['date']).set_index('date')['close'].astype(float).sort_index()
    spy = spy.pct_change()
    ief = pd.read_csv(os.path.join(ROOT, 'tools/quant/data/more_etf/IEF.csv'),
                      parse_dates=['date']).set_index('date')['close'].astype(float).sort_index()
    ief = ief.pct_change()
    cta = pd.read_csv(os.path.join(CAMPAIGN, 'results/sleeve_library/CTA_15vol.csv'))
    cta.index = pd.to_datetime(cta['date'])
    return spy, ief, pd.to_numeric(cta['ret'], errors='coerce')


def decision_positions(fund_daily, rule, rebalance):
    """Decision-time positions at rebalance frequency, held forward daily (NOT yet lagged)."""
    dec = fund_daily.resample('W-SUN' if rebalance == 'W' else 'ME').sum()
    if rule == 'long':
        pos = pd.Series(1.0, index=dec.index)
    elif rule == 'harvest':
        pos = -np.sign(dec.rolling(4).mean())
    elif rule == 'z':
        m = dec.rolling(26).mean()
        s = dec.rolling(26).std()
        z = (dec - m) / s.replace(0, np.nan)
        pos = -np.sign(z)
    else:
        raise ValueError(rule)
    pos = pos.replace([np.inf, -np.inf], np.nan)
    daily = pd.Series(np.nan, index=fund_daily.index)
    common = daily.index.intersection(pos.index)
    daily.loc[common] = pos.loc[common]
    return daily.ffill().dropna(), dec.dropna()


def run_config(fund_daily, px, rule, rebalance, name, spy, ief, cta, champ):
    pos_decision, dec = decision_positions(fund_daily, rule, rebalance)
    rets = px.pct_change()
    idx = pos_decision.index.intersection(rets.dropna().index).intersection(champ.index)
    ref = champ.reindex(idx).dropna()
    idx = ref.index
    r = rets.reindex(idx).fillna(0.0)                       # per-unit, COSTLESS
    pos_d = pos_decision.reindex(idx).ffill().fillna(0.0)   # decision positions
    if len(idx) < 300:
        return dict(name=name, error='span too short n=%d' % len(idx))

    scale = vol_target_scale(r.to_frame('a')).iloc[:, 0]     # trailing-only, clip 3, shift(1)
    sig = (lag_signal(pos_d) * scale).fillna(0.0)            # HELD positions (T+1)
    book_gross = sig * r                                     # what gates.run judges

    # explicit campaign costs on the HELD weights (same formulas as bt.engine):
    dW = sig.diff().abs().fillna(0.0)                        # includes entry (prev seeded 0)
    dW.iloc[0] = abs(sig.iloc[0])                            # entry notional charged
    cost = dW * COST_BPS / 1e4 + (-sig).clip(lower=0.0) * 0.005 / ANN
    book_net = book_gross - cost

    g = gates_mod.run(book_gross, ref=ref, sig=sig, leak_check=True,
                      beats_passive=True, spy=spy, ief=ief, cta=cta, scramble_n=200)

    def sr(x):
        x = pd.Series(x).dropna()
        return float(x.mean() / x.std(ddof=1) * np.sqrt(ANN)) if x.std(ddof=1) > 0 else float('nan')

    ch = dW.sum() / (len(idx) / ANN)
    out = dict(name=name, n=len(idx), span=[str(idx[0].date()), str(idx[-1].date())],
               gates=serialize(g),
               net_sr=round(sr(book_net), 3), gross_sr=round(sr(book_gross), 3),
               net_ann_pct=round(float(book_net.mean() * ANN * 100), 2),
               gross_ann_pct=round(float(book_gross.mean() * ANN * 100), 2),
               ann_dW=round(float(ch), 1),
               frac_long=round(float((pos_d > 0).mean()), 3),
               frac_short=round(float((pos_d < 0).mean()), 3))
    return out


def serialize(g):
    out = {}
    for k, v in g.items():
        if isinstance(v, dict):
            out[k] = serialize(v)
        elif isinstance(v, (np.floating, np.integer)):
            out[k] = float(v)
        elif isinstance(v, (bool, np.bool_)):
            out[k] = bool(v)
        else:
            out[k] = v
    return out


def main():
    champ = pd.read_csv(os.path.join(CAMPAIGN, 'results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv'),
                        parse_dates=['date']).set_index('date')['ret']
    spy, ief, cta = load_benchmarks()
    results = []
    for sym, coin in [('xbtusd', 'BTC'), ('ethusd', 'ETH')]:
        fund = load_funding(sym)
        px = load_prices(coin)
        for rule in ['harvest', 'long', 'z']:
            for reb in ['W', 'M']:
                name = 'CARRY_%s_%s_%s' % (coin, rule.upper(), reb)
                res = run_config(fund, px, rule, reb, name, spy, ief, cta, champ)
                results.append(res)
                g = res.get('gates', {})
                bp = g.get('beats_passive') or {}
                print("%-22s n=%-5s grossSR %.3f netSR %.3f h1/h2 %.2f/%.2f neg %s corr %.3f scr_p %s leak %s(c%.3f) bp_ok %s candSR %.3f bp_best %s(%s) | netAnn %.2f%% dW %.1f pass %s"
                      % (name, res.get('n'), g.get('sr', float('nan')), res.get('net_sr'),
                         g.get('h1', float('nan')), g.get('h2', float('nan')),
                         g.get('neg_years'), g.get('corr'), g.get('scr_p'),
                         g.get('leak_ok'), (g.get('leak') or {}).get('same_period_corr'),
                         g.get('beats_passive_ok'), bp.get('candidate_sr'),
                         bp.get('best_passive_sr'), bp.get('best_passive_name'),
                         res.get('net_ann_pct'), res.get('ann_dW'), g.get('pass')))
    with open(os.path.join(HERE, 'carry_results_v3.json'), 'w') as f:
        json.dump(results, f, indent=1, default=str)
    print("saved carry_results_v3.json")


if __name__ == '__main__':
    main()
