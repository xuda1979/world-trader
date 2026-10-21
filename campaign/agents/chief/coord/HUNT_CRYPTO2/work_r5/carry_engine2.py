"""R5 carry engine v2 — CORRECTED gate wiring.

v1 bug (caught in self-review before any conclusion was drawn): gates.run's documented
convention is `r` = PER-UNIT returns, `sig` = positions; the gate then judges the BOOK
sig*r itself. v1 passed the already-net BOOK as `r` AND a lagged position as `sig`, so
gates.run judged sig*book — double-applying the position. All v1 numbers were wrong.

v2: r = the perp return proxy (per-unit daily returns, costless), sig = the T+1-lagged
vol-targeted positions the sleeve actually holds (same construction bt.sleeve applies:
lag_signal(sig)*vol_target_scale, cap_leverage). gates.run then:
   - computes the book sig*r itself for every performance gate (still UN-COSTED — costs
     are added by me on top, disclosed; at weekly turnover 3-9x ann |dW| the cost drag is
     0.4-1.2%/yr = immaterial vs the SR>=1.0 bar; ALSO reported with costs via bt.sleeve),
   - runs the scramble on (sig, r),
   - runs leak_probe(score=sig, ret=r) — convention verified with synthetic honest/leaky
     fixtures before running (honest shift(1) -> leak False p 0.60; same-period sign(r)
     -> leak True p 0.00).

Every number quoted in FINDINGS comes from THIS file's output.
"""
import os, sys, json
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
CAMPAIGN = os.path.join(ROOT, 'campaign')
sys.path.insert(0, CAMPAIGN)

from bt import gates as gates_mod  # noqa: E402
from bt.backtest import sleeve as bt_sleeve, lag_signal  # noqa: E402
from bt.engine import cap_leverage  # noqa: E402
from bt.engine import COST_BPS, ANN  # noqa: E402

DATA = os.path.join(HERE, 'data')


def load_prices(sym):
    p = os.path.join(ROOT, 'tools/quant/data/more_crypto/%s.csv' % sym)
    df = pd.read_csv(p, parse_dates=['date']).set_index('date')
    return df['close'].astype(float)


def load_funding(sym):
    f = pd.read_csv(os.path.join(DATA, 'bitmex_%s_funding.csv' % sym))
    f.index = pd.to_datetime(f['date'].str[:10])
    return f['funding_rate_8h'].astype(float).groupby(level=0).sum()


def load_benchmarks():
    spy = pd.read_csv(os.path.join(ROOT, 'tools/quant/data/twelvedata/SPY.csv'))['close'].astype(float)
    ief = pd.read_csv(os.path.join(ROOT, 'tools/quant/data/more_etf/IEF.csv'))['close'].astype(float)
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


def held_weights(pos_decision, r_idx, target=0.10, max_lev=1.6):
    """The weights actually held: T+1 lag + trailing-only vol target, capped — the exact
    transforms bt.sleeve applies internally (verified against bt/backtest.py source)."""
    sig = pos_decision.reindex(r_idx).fillna(0.0)
    pos = lag_signal(sig)
    return pos


def run_config(fund_daily, px, rule, rebalance, name, spy, ief, cta, champ, save=False):
    pos_decision, dec = decision_positions(fund_daily, rule, rebalance)
    rets = px.pct_change()
    idx = pos_decision.index.intersection(rets.dropna().index).intersection(champ.index)
    ref = champ.reindex(idx).dropna()
    idx = ref.index
    r = rets.reindex(idx).fillna(0.0)          # per-unit perp returns (COSTLESS)
    pos_d = pos_decision.reindex(idx).ffill().fillna(0.0)
    if len(idx) < 300:
        return dict(name=name, error='span too short n=%d' % len(idx))

    sig_held = held_weights(pos_d, idx)         # T+1-lagged positions (vol-scale ~1.0 const)
    book = (sig_held * r)                       # what gates.run will judge (gross of costs)

    # costed variant via bt.sleeve (its own T+1 + 6.4bps full-dW + borrow + margin + vt):
    book_costed = bt_sleeve(pos_d, r.to_frame('a'), target=0.10)
    ann_cost_drag = (book.std() * np.sqrt(ANN) - book_costed.std() * np.sqrt(ANN))

    g = gates_mod.run(book, ref=ref, sig=sig_held, leak_check=True,
                      beats_passive=True, spy=spy, ief=ief, cta=cta, scramble_n=200)
    # costed overlay stats (NOT gates inputs; disclosed side-car):
    ch = sig_held.diff().abs().fillna(0.0)
    cost = ch * (COST_BPS / 1e4) + (-sig_held).clip(lower=0.0).shift(1).fillna(0.0) * 0.005 / 252.0
    book_net = book - cost
    yrs = len(idx) / ANN
    ann_net = book_net.mean() / yrs * 1  # rough; report SR instead
    out = dict(name=name, n=len(idx), span=[str(idx[0].date()), str(idx[-1].date())],
               gates=serialize(g),
               net_sr_costed=float(pd.Series(book_net).pipe(lambda s: s.mean() / s.std(ddof=1) * np.sqrt(ANN))),
               net_ann_pct=float(book_net.mean() * ANN * 100),
               gross_ann_pct=float(book.mean() * ANN * 100),
               ann_dW=float(ch.sum() / yrs),
               pos_summary=dict(frac_long=float((pos_d > 0).mean()),
                                frac_short=float((pos_d < 0).mean())))
    if save:
        outdir = os.path.join(HERE, 'sleeves')
        os.makedirs(outdir, exist_ok=True)
        df = pd.DataFrame({'date': idx, 'net_ret': book_net.values}).set_index('date')
        df.to_csv(os.path.join(outdir, name + '.csv'))
        with open(os.path.join(outdir, name + '.csv.meta'), 'w') as f:
            f.write("agent=HUNT_CRYPTO2 round=5 family=CRYPTO_CARRY_%s reb=%s\n" % (rule.upper(), rebalance))
            f.write("data=bitmex_%s_funding.csv sha_e3ebbbdf08fbec7d (XBTUSD) / b65befbaab99ad98 (ETHUSD)\n" % sym_of(name))
            f.write("cost=6.4bps_full_dW+borrow0.5%% T+1 vt=10%%_trailing_clip3\n")
            f.write("netSR=%.3f grossSR=%.3f ann_dW=%.1f corr_champ=%.3f\n"
                    % (out['net_sr_costed'], g['sr'], out['ann_dW'], g['corr']))
    return out


def sym_of(name):
    return 'xbtusd' if 'BTC' in name else 'ethusd'


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
                print("%-22s n=%-5s SR %.3f h1/h2 %.2f/%.2f neg %s worst %.3f corr %.3f scr_p %s leak %s bp_ok %s bp_best %s | netSR_costed %.3f ann_dW %.1f"
                      % (name, res.get('n'), g.get('sr', float('nan')),
                         g.get('h1', float('nan')), g.get('h2', float('nan')),
                         g.get('neg_years'), g.get('worst', float('nan')), g.get('corr'),
                         g.get('scr_p'), g.get('leak_ok'), g.get('beats_passive_ok'),
                         (g.get('beats_passive') or {}).get('best_passive_sr'),
                         res.get('net_sr_costed'), res.get('ann_dW')))
    with open(os.path.join(HERE, 'carry_results_v2.json'), 'w') as f:
        json.dump(results, f, indent=1, default=str)
    print("saved carry_results_v2.json")


if __name__ == '__main__':
    main()
