"""R7 DVOL diagnostic engine — HUNT_CRYPTO2 round 7 (charter corner (a), DVOL leg).

DATA BASIS (pre-registered corner requires citing sources + row counts + PIT basis):
  - tools/quant/data/deribit_dvol/btc_dvol.csv  n=1801 2021-10-03..2026-09-07
    sha256[:16] a5ac2cc1443ccaae  (fetched 2026-09-07 10:23 by tools/quant/data/
    deribit_dvol/deribit_dvol.py from
    https://www.deribit.com/api/v2/public/get_volatility_index_data, keyless)
  - tools/quant/data/deribit_dvol/eth_dvol.csv  n=1801 2021-10-03..2026-09-07
    sha256[:16] 2c3cb8a0f8e36e90
  - Live Deribit is UNREACHABLE from this env (see work_r7/deribit_blocked_evidence.json
    + r7_blocked_evidence.py): UDP-DNS poisoned per-query, TCP-DNS reset, DoH dead,
    direct-IP TLS/:80/v6 time out; DeFiLlama/CNBC controls pass in-session. So the
    vintages above are the ONLY DVOL data available, and the OPTIONS CHAIN (term
    structure) has NO history at all -> that half of the corner is charter-(b) blocked.

  PIT timestamp basis: DVOL daily bars are stamped by bar-open ms epoch (UTC midnight);
  the fetcher (deribit_dvol.py parse()) converts to UTC calendar dates, so bar date D =
  the day whose UTC window produced the OHLC. Trading decisions in this engine use only
  bars with date <= D-1 at decision time (T+1 via lag_signal), which is strictly PIT
  w.r.t. the daily bar stamp even under the most conservative reading (full-day bar).

  span_class (V2 section 9a): inception 2021-10-03 > 2013-01-01 bound =>
  INCEPTION_FAIL. NOT hunt-eligible, NOT champion-eligible. This engine therefore
  publishes a DIAGNOSTIC, not an acceptance submission: the full V2 battery is run for
  honesty and comparability, and any 'pass' would still be span-dead.

  What the corner CAN ask with DVOL alone (term structure unavailable):
   (i) vol-of-vol: std/AR1 of DVOL changes -> de-risk/risk-on gate on BTC/ETH carry,
       weekly rebalance (charter R7 freq rule).
  (ii) vol-level regime: DVOL z / level bands -> long-BTC/ETH risk-on per regime.
  Costs: 6.4 bps full-|dW| one-side (contract v1 item 2) + 0.5%/yr borrow on shorts.
  Decorrelation: ref = champion GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily (sha
  4358dfab95679b97) AND the A5r2 vol sleeve A5_r2_contango_rateshock (charter names it
  as the vol sleeve to differ from).
"""
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
CAMPAIGN = os.path.join(ROOT, 'campaign')
sys.path.insert(0, CAMPAIGN)

from bt import gates as gates_mod  # noqa: E402
from bt.engine import lag_signal, vol_target_scale, COST_BPS, ANN  # noqa: E402

DVOL_DIR = os.path.join(ROOT, 'tools/quant/data/deribit_dvol')
A5R2 = os.path.join(ROOT, 'campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv')
CHAMP = os.path.join(CAMPAIGN, 'results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv')


def sha16(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def load_dvol(sym):
    df = pd.read_csv(os.path.join(DVOL_DIR, '%s_dvol.csv' % sym.lower()),
                     parse_dates=['date']).set_index('date')
    return df['dvol_close'].astype(float).sort_index()


def load_benchmarks():
    spy = pd.read_csv(os.path.join(ROOT, 'tools/quant/data/twelvedata/SPY.csv'),
                      parse_dates=['date']).set_index('date')['close'].astype(float).sort_index()
    spy = spy.pct_change()
    ief = pd.read_csv(os.path.join(ROOT, 'tools/quant/data/more_etf/IEF.csv'),
                      parse_dates=['date']).set_index('date')['close'].astype(float).sort_index()
    ief = ief.pct_change()
    cta = pd.read_csv(os.path.join(CAMPAIGN, 'results/sleeve_library/CTA_15vol.csv'))
    cta.index = pd.to_datetime(cta['date'])
    return spy, ief, pd.to_numeric(cta['ret'], errors='coerce')


def weekly_positions(dvol_daily, rule, param):
    """Decision positions at W-FRI rebalance held forward daily (NOT yet lagged).
    All rules use only information available at decision time (rolling windows)."""
    if rule == 'vov':
        # vol-of-vol de-risk: std of DVOL 1d changes over `param` days, expanding
        # trailing percentile rank; high vol-of-vol = stress = flat (0), else long.
        chg = dvol_daily.diff()
        vov = chg.rolling(param).std()
        pct = vov.rolling(520, min_periods=260).apply(
            lambda a: (a[-1] <= a).mean(), raw=True)  # trailing percentile of current vov
        pos = (pct < 0.75).astype(float)             # risk-on unless vov in top quartile
    elif rule == 'zlevel':
        # vol-level regime: DVOL z vs `param`-day rolling; high IV = fear = flat.
        z = (dvol_daily - dvol_daily.rolling(param).mean()) / dvol_daily.rolling(param).std()
        pos = (z < 1.0).astype(float)                # long unless IV stretched > +1z
    elif rule == 'levelband':
        # absolute level bands (IV mean-reversion regime gate): long under lo, flat above.
        pos = (dvol_daily < param).astype(float)
    elif rule == 'trend':
        # vol trend: DVOL above its `param`-day mean = rising vol regime = flat.
        pos = (dvol_daily < dvol_daily.rolling(param).mean()).astype(float)
    else:
        raise ValueError(rule)
    pos = pos.replace([np.inf, -np.inf], np.nan)
    wk = pos.resample('W-FRI').last()
    daily = pd.Series(np.nan, index=dvol_daily.index)
    common = daily.index.intersection(wk.index)
    daily.loc[common] = wk.loc[common]
    return daily.ffill(), wk.dropna()


def run_config(dvol, px, rule, param, name, spy, ief, cta, champ, a5r2):
    pos_decision, _wk = weekly_positions(dvol, rule, param)
    rets = px.pct_change()
    idx = pos_decision.dropna().index.intersection(rets.dropna().index).intersection(champ.index)
    ref = champ.reindex(idx).dropna()
    a5 = a5r2.reindex(idx)
    idx = ref.index
    r = rets.reindex(idx).fillna(0.0)                      # per-unit, COSTLESS
    pos_d = pos_decision.reindex(idx).ffill().fillna(0.0)
    if len(idx) < 300:
        return dict(name=name, error='span too short n=%d' % len(idx))

    scale = vol_target_scale(r.to_frame('a')).iloc[:, 0]   # trailing-only, clip 3, shift(1)
    sig = (lag_signal(pos_d) * scale).fillna(0.0)          # HELD positions (T+1)
    book_gross = sig * r

    dW = sig.diff().abs().fillna(0.0)
    dW.iloc[0] = abs(sig.iloc[0])                          # entry notional charged
    cost = dW * COST_BPS / 1e4 + (-sig).clip(lower=0.0) * 0.005 / ANN
    book_net = book_gross - cost

    g = gates_mod.run(book_gross, ref=ref, sig=sig, leak_check=True,
                      beats_passive=True, spy=spy, ief=ief, cta=cta, scramble_n=200)
    corr_a5 = float(pd.concat([a5.rename('a'), book_net.rename('b')], axis=1)
                    .dropna().corr().iloc[0, 1])

    def sr(x):
        x = pd.Series(x).dropna()
        return float(x.mean() / x.std(ddof=1) * np.sqrt(ANN)) if x.std(ddof=1) > 0 else float('nan')

    ch = dW.sum() / (len(idx) / ANN)
    return dict(name=name, rule=rule, param=param, n=len(idx),
                span=[str(idx[0].date()), str(idx[-1].date())],
                span_class='inception_fail (2021-10-03 > 2013-01-01, V2 9a)',
                gates=serialize(g), net_sr=round(sr(book_net), 3),
                gross_sr=round(sr(book_gross), 3),
                net_ann_pct=round(float(book_net.mean() * ANN * 100), 2),
                ann_dW=round(float(ch), 1), corr_A5r2=round(corr_a5, 4),
                corr_champ=round(float(g['corr']), 4))


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
    champ = pd.read_csv(CHAMP, parse_dates=['date']).set_index('date')['ret']
    a5r2 = pd.read_csv(A5R2, parse_dates=['date']).set_index('date')['ret']
    spy, ief, cta = load_benchmarks()
    px = {s: pd.read_csv(os.path.join(ROOT, 'tools/quant/data/more_crypto/%s.csv' % s),
                         parse_dates=['date']).set_index('date')['close'].astype(float)
          for s in ('BTC', 'ETH')}
    pins = dict(btc_dvol_sha16=sha16(os.path.join(DVOL_DIR, 'btc_dvol.csv')),
                eth_dvol_sha16=sha16(os.path.join(DVOL_DIR, 'eth_dvol.csv')),
                champ_sha16=sha16(CHAMP),
                a5r2_span=None)
    results = []
    for sym in ('BTC', 'ETH'):
        dvol = load_dvol(sym)
        for rule, params in [('vov', [20, 60]), ('zlevel', [30, 90]),
                             ('levelband', [50.0, 70.0]), ('trend', [20, 60])]:
            for p in params:
                name = 'DVOL_%s_%s_%s' % (sym, rule.upper(), p)
                res = run_config(dvol, px[sym], rule, p, name, spy, ief, cta, champ, a5r2)
                results.append(res)
                g = res.get('gates', {})
                bp = g.get('beats_passive') or {}
                print("%-26s n=%-5s grossSR %.3f netSR %.3f h1/h2 %.2f/%.2f neg %s "
                      "corr_champ %s corr_A5 %s scr_p %s leak %s(c%.3f) bp_ok %s "
                      "netAnn %.2f%% dW %.1f pass %s"
                      % (name, res.get('n'), g.get('sr', float('nan')), res.get('net_sr'),
                         g.get('h1', float('nan')), g.get('h2', float('nan')),
                         g.get('neg_years'), res.get('corr_champ'), res.get('corr_A5r2'),
                         g.get('scr_p'), g.get('leak_ok'),
                         (g.get('leak') or {}).get('same_period_corr', float('nan')),
                         g.get('beats_passive_ok'), res.get('net_ann_pct'),
                         res.get('ann_dW'), g.get('pass')))
    with open(os.path.join(HERE, 'r7_dvol_results.json'), 'w') as f:
        json.dump(dict(pins=pins, results=results), f, indent=1, default=str)
    print("saved r7_dvol_results.json ; pins:", pins)


if __name__ == '__main__':
    main()
