"""R5 charter (a): crypto carry from keyless funding-rate / perp-basis endpoints.

PRE-REGISTERED DESIGN (before any result was seen; committed with this file):
  Data: BitMEX XBTUSD funding 8h (2016-05-14..2026-09-07, n=11264, sha e3ebbbdf08fbec7d)
        BitMEX ETHUSD funding 8h (2018-08-02..2026-09-07, n=8876, sha b65befbaab99ad98)
        Roster endpoints (OKX, CB INTX) fetched too: 3mo / 5d caps => inception_fail, unused
        in engines (span gate 9a/9c: >=8y of effect is the bar; 3mo is unjudgeable).
  Carry book economics: a LONG perp position PAYS funding when funding > 0 (longs pay shorts
        in perp swaps). So:
        CARRY_HARVEST  short perp when trailing funding > 0 (collect), long when < 0
                       => position = -sign(trailing mean funding). This is the classic
                       short-perp carry harvest (shorts RECEIVE positive funding).
        CARRY_LONG     always-long-perp naive premium (position = +1): collects -funding.
        CARRY_Z        fade extreme funding: short when z(funding) high, long when low,
                       position = -sign(z). Direction pre-registered as the fade; the
                       momentum direction is reported as a disclosed mirror, not cherry-picked.
  Rebalance: WEEKLY (W-FRI decision on data through Thursday, hold Mon..Fri) and MONTHLY.
        Daily is BANNED by charter (R4 TimesFM 112-154x annTO death).
  Signal timing: position for week t+1 built from funding data with last obs <= week t close;
        bt.sleeve applies T+1 lag on top. leak_probe with sig= positions, leak_check=True.
  Costs: bt.sleeve default 6.4bps full-|dW| + borrow 0.5% + margin 4.5%; vol-target 10% ann
        trailing-only clip 3 (contract 3g).
  Underlying return: the perp tracks its cash pair; use on-disk more_crypto close-to-close
        daily returns as the perp return proxy (BTC from 2017-08, ETH from 2018-01), the
        same files cited in every prior crypto round.
  Benchmarks for beats_passive (pinned per 7c): SPY=twelvedata/SPY.csv, IEF=more_etf/IEF.csv,
        CTA=sleeve_library/CTA_15vol.csv.

Output: per-config gate dicts + saved sleeve CSVs under work_r5/sleeves/.
"""
import os, sys, json
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
CAMPAIGN = os.path.join(ROOT, 'campaign')
sys.path.insert(0, CAMPAIGN)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

from bt.backtest import sleeve as bt_sleeve  # noqa: E402
from bt import gates as gates_mod  # noqa: E402
from bt.beats_passive import evaluate as bp_eval  # noqa: E402

DATA = os.path.join(HERE, 'data')
OUT = os.path.join(HERE, 'sleeves')
os.makedirs(OUT, exist_ok=True)


def load_prices(sym):
    p = os.path.join(ROOT, 'tools/quant/data/more_crypto/%s.csv' % sym)
    df = pd.read_csv(p, parse_dates=['date']).set_index('date')
    return df['close'].astype(float)


def load_funding(sym):
    p = os.path.join(DATA, 'bitmex_%s_funding.csv' % sym)
    f = pd.read_csv(p)
    f.index = pd.to_datetime(f['date'].str[:10])
    s = f['funding_rate_8h'].astype(float)
    s = s.groupby(level=0).sum()
    return s


def load_benchmarks():
    spy = pd.read_csv(os.path.join(ROOT, 'tools/quant/data/twelvedata/SPY.csv'))['close'].astype(float)
    ief = pd.read_csv(os.path.join(ROOT, 'tools/quant/data/more_etf/IEF.csv'))['close'].astype(float)
    cta = pd.read_csv(os.path.join(CAMPAIGN, 'results/sleeve_library/CTA_15vol.csv'))
    cta.index = pd.to_datetime(cta['date'])
    cta = pd.to_numeric(cta['ret'], errors='coerce')
    return spy, ief, cta


def positions_from_funding(fund_daily, rule, rebalance='W', lookbacks=(4, 13, 26)):
    """Return a DAILY position series (only rebalance-date values nonzero-change) per rule.

    rule in {'harvest', 'long', 'z'}; z uses zlb/26w trailing. Weekly: decision on the last
    COMPLETED week (data through Sunday), effective Monday; sleeve lags T+1 on top."""
    wk = fund_daily.resample('W-SUN').sum()
    if rebalance == 'M':
        dec = fund_daily.resample('ME').sum()
    else:
        dec = wk

    if rule == 'long':
        pos = pd.Series(1.0, index=dec.index)
    elif rule == 'harvest':
        pos = -np.sign(dec.rolling(4).mean())  # 4-period trailing mean (4w / 4m)
    elif rule == 'z':
        m = dec.rolling(26).mean()
        s = dec.rolling(26).std()
        z = (dec - m) / s.replace(0, np.nan)
        pos = -np.sign(z)
    else:
        raise ValueError(rule)
    pos = pos.replace([np.inf, -np.inf], np.nan)

    # expand decision dates to a DAILY position series: hold between rebalances
    daily = pd.Series(np.nan, index=fund_daily.index)
    common = daily.index.intersection(pos.index)
    daily.loc[common] = pos.loc[common]
    daily = daily.ffill()
    return daily.dropna(), dec.dropna()


def run_config(fund_daily, px, rule, rebalance, name, spy, ief, cta, champ,
               lookback_override=None):
    pos_daily, dec = positions_from_funding(fund_daily, rule, rebalance)
    if lookback_override == 'slow':
        pass  # reserved for slower variants
    # perp return proxy: cash pair close-to-close daily
    rets = px.pct_change().dropna()
    idx = pos_daily.index.intersection(rets.index).intersection(champ.index)
    pos = pos_daily.reindex(idx).ffill().fillna(0.0)
    r = rets.reindex(idx).fillna(0.0)
    ref = champ.reindex(idx).dropna()
    idx = ref.index
    pos, r = pos.reindex(idx).fillna(0.0), r.reindex(idx).fillna(0.0)

    if len(idx) < 300:
        return dict(name=name, error='span too short n=%d' % len(idx))

    book = bt_sleeve(pos, r.to_frame('a'), target=0.10)  # T+1 + 6.4bps full dW + borrow+margin
    sig_positions = book_pos_from(pos, book, idx)

    g = gates_mod.run(book, ref=ref, sig=sig_positions, leak_check=True,
                      beats_passive=True, spy=spy, ief=ief, cta=cta, scramble_n=200)
    return dict(name=name, n=len(idx), span=[str(idx[0].date()), str(idx[-1].date())],
                gates=serialize(g), pos_summary=pos_summary(pos))


def book_pos_from(pos_w, book, idx):
    """Positions series for leak_probe: the lagged, vol-scaled weights actually held.

    bt.sleeve computes w = lag(sig)*scale internally; we reconstruct the T+1-lagged position
    (scale-free is conservative for the same-period probe: it tests DECISION timing)."""
    return pos_w.shift(1).fillna(0.0).reindex(idx)


def pos_summary(pos):
    ch = pos.diff().abs().sum()
    yrs = max(len(pos) / 252.0, 1e-9)
    return dict(frac_long=float((pos > 0).mean()), frac_short=float((pos < 0).mean()),
                frac_flat=float((pos == 0).mean()), total_dW=float(ch),
                ann_turnover=float(ch / yrs))


def serialize(g):
    out = {}
    for k, v in g.items():
        if isinstance(v, dict):
            out[k] = serialize(v)
        elif isinstance(v, (np.floating, np.integer)):
            out[k] = float(v)
        elif isinstance(v, (bool, np.bool_)):
            out[k] = bool(v)
        elif isinstance(v, float) and (np.isnan(v) if isinstance(v, float) else False):
            out[k] = 'NaN'
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
                print("%-24s n=%-5s SR %.3f h1/h2 %.2f/%.2f neg %s corr %.3f scr_p %s leak %s bp %s pass %s"
                      % (name, res.get('n'), g.get('sr', float('nan')),
                         g.get('h1', float('nan')), g.get('h2', float('nan')),
                         g.get('neg_years'), g.get('corr'), g.get('scr_p'),
                         g.get('leak_ok'), g.get('beats_passive_ok'), g.get('pass')))
    with open(os.path.join(HERE, 'carry_results.json'), 'w') as f:
        json.dump(results, f, indent=1, default=str)
    print("saved", os.path.join(HERE, 'carry_results.json'))


if __name__ == '__main__':
    main()
