"""R5 (a) part 2: the HEDGED funding-leg book (cash-and-carry) — full V2 battery for the
record. Pre-registered construction: perp side -sign(trailing funding), spot side
+sign(trailing funding) -> price legs cancel (same index), book return = collected funding.
This is a synthetic data finding, NOT an expressible campaign sleeve (no perp/spot
instrument pair exists in the campaign tradeable universe) — published under the row-109
'data-acquired' convention. Battery run anyway, fail-closed rules intact."""
import os, sys, json
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
CAMPAIGN = os.path.join(ROOT, 'campaign')
sys.path.insert(0, CAMPAIGN)
from bt import gates as gates_mod  # noqa: E402
from bt.engine import COST_BPS, ANN  # noqa: E402
from bt.metrics import half_split, neg_years  # noqa: E402


def load_funding(sym):
    f = pd.read_csv(os.path.join(HERE, 'data', 'bitmex_%s_funding.csv' % sym))
    f.index = pd.to_datetime(f['date'].str[:10])
    return f['funding_rate_8h'].astype(float).groupby(level=0).sum()


def load_benchmarks():
    spy = pd.read_csv(os.path.join(ROOT, 'tools/quant/data/twelvedata/SPY.csv'),
                      parse_dates=['date']).set_index('date')['close'].astype(float).sort_index().pct_change()
    ief = pd.read_csv(os.path.join(ROOT, 'tools/quant/data/more_etf/IEF.csv'),
                      parse_dates=['date']).set_index('date')['close'].astype(float).sort_index().pct_change()
    cta = pd.read_csv(os.path.join(CAMPAIGN, 'results/sleeve_library/CTA_15vol.csv'))
    cta.index = pd.to_datetime(cta['date'])
    return spy, ief, pd.to_numeric(cta['ret'], errors='coerce')


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


def sr(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(ANN)) if x.std(ddof=1) > 0 else float('nan')


def run(sym, coin, champ, spy, ief, cta):
    f = load_funding(sym)
    rows = []
    for reb, rule in [('W', 'W-FRI'), ('M', 'ME')]:  # W-FRI: champ trades weekdays only; Sunday stamps never intersect
        wk = f.resample(rule).sum()                       # funding yield per period
        # harvest: pos = -sign(f_trailing) (short perp when funding positive); the funding
        # LEG of a perp position pays -pos*f (long pays f>0) => collected funding =
        # -pos*f = sign(f_trailing) * f_next. (v1 of this file had the leg sign flipped.)
        pos_d = -np.sign(wk.rolling(4).mean().shift(1))   # decision for NEXT period
        book = (-pos_d * wk).dropna() * 1.0
        # costs: entry + one flip when sign changes (rare): 6.4bps per unit turnover
        dW = pos_d.diff().abs().fillna(0.0)
        dW.iloc[0] = 1.0
        to = float(dW.reindex(book.index).fillna(0.0).sum())
        cost_total = to * COST_BPS / 1e4
        book_net = book - dW.reindex(book.index).fillna(0.0) * COST_BPS / 1e4
        idx = book_net.index.intersection(champ.index)
        ref = champ.reindex(idx).dropna()
        b = book_net.reindex(ref.index)
        # V2 battery: sig = the HELD positions (re-expanded daily would be flat; supply the
        # per-period positions; scramble + leak run on these, fail-closed semantics intact)
        sig = pos_d.reindex(ref.index).fillna(0.0)   # held positions (perp leg)
        r_period = wk.reindex(ref.index).fillna(0.0)  # (probe runs on sig vs wk: the leg the book prices)
        g = gates_mod.run(b, ref=ref, sig=sig, leak_check=True,
                          beats_passive=True, spy=spy, ief=ief, cta=cta, scramble_n=200)
        h1, h2 = half_split(b)
        neg, worst = neg_years(b)
        yrs = b.groupby(b.index.year).apply(lambda x: (1 + x).prod() - 1)
        # era split for decay disclosure
        eras = {}
        for lo, hi in [('2018', '2020'), ('2021', '2022'), ('2023', '2024'), ('2025', '2026')]:
            m = b[(b.index >= '%s-01-01' % lo) & (b.index <= '%s-12-31' % hi)]
            eras['%s-%s' % (lo, hi)] = round(float(m.mean()) * (52 if reb == 'W' else 12) * 100, 2) if len(m) else None
        rows.append(dict(name='HEDGE_%s_%s' % (coin, reb), n=len(b),
                         span=[str(b.index[0].date()), str(b.index[-1].date())],
                         gross_sr=round(sr(book), 3), net_sr=round(sr(b), 3),
                         net_ann_pct=round(float(b.mean()) * (52 if reb == 'W' else 12) * 100, 2),
                         h1=round(h1, 3), h2=round(h2, 3), neg_years=neg, worst=round(worst, 4),
                         corr_champ=round(float(g['corr']), 4), total_turnover=round(to, 2),
                         cost_total_pct=round(cost_total * 100, 3),
                         yearly={str(k): round(v * 100, 2) for k, v in yrs.items()},
                         era_net_ann_pct=eras, gates=serialize(g)))
        gk = g
        print("HEDGE_%s_%s n=%d netSR %.3f netAnn %.2f%% h1/h2 %.2f/%.2f neg %d worst %.2f%% corr %.3f scr_p %s leak_ok %s bp_ok %s pass %s"
              % (coin, reb, len(b), sr(b), rows[-1]['net_ann_pct'], h1, h2, neg, worst * 100,
                 g['corr'], g['scr_p'], g.get('leak_ok'), g.get('beats_passive_ok'), gk['pass']))
    return rows


def main():
    champ = pd.read_csv(os.path.join(CAMPAIGN, 'results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv'),
                        parse_dates=['date']).set_index('date')['ret']
    spy, ief, cta = load_benchmarks()
    out = []
    for sym, coin in [('xbtusd', 'BTC'), ('ethusd', 'ETH')]:
        out += run(sym, coin, champ, spy, ief, cta)
    with open(os.path.join(HERE, 'hedged_results.json'), 'w') as f:
        json.dump(out, f, indent=1, default=str)
    print("saved hedged_results.json")


if __name__ == '__main__':
    main()
