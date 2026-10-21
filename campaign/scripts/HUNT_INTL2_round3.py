"""HUNT_INTERNATIONAL2 round 3 — reproducible evidence script.

(a) Apply the new MANDATORY beats-passive gate (bt.beats_passive, TDD 21 green) to
    representative real sleeves + the committed champion.
(b) Cross-verify HUNT_CREDIT2's round-2 negatives from their SAVED sleeve CSVs
    (independent recompute of SR / halves / neg-years / worst-year / corr-to-champion
    from campaign/agents/chief/coord/HUNT_CREDIT2/sleeves/*.csv), comparing to the
    numbers they published in their FINDINGS.md, sleeves/*.meta and DEAD_IDEAS rows.

Run:  python3 campaign/scripts/HUNT_INTL2_round3.py
"""
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, 'campaign')
from bt import beats_passive as BP          # noqa: E402
from bt.metrics import sharpe_d, half_split, neg_years  # noqa: E402
from bt.gates import corr_to                # noqa: E402

ROOT = '/Users/daxu/software/world-trader'
CHAMP = f'{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv'


def load_ret(p):
    d = pd.read_csv(p, parse_dates=['date']).set_index('date')['ret']
    return d[~d.index.duplicated(keep='last')].sort_index()


def part_a():
    print('=' * 78)
    print('(a) MANDATORY beats-passive gate on real sleeves + champion')
    print('=' * 78)
    spy_px = pd.read_csv(f'{ROOT}/tools/quant/data/twelvedata/SPY.csv',
                         parse_dates=['date']).set_index('date')['close'].sort_index()
    spy = spy_px.pct_change().rename('ret')          # returns, value-detect keeps them
    ief = pd.read_csv(f'{ROOT}/tools/quant/data/more_etf/IEF.csv', parse_dates=['date']
                      ).set_index('date')['close'].sort_index().pct_change().rename('ret')
    cta = load_ret(f'{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv')

    cases = {
        'INTL_R2_RS252_LS (R2 best intl config, DEAD)':
            f'{ROOT}/campaign/agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R2_RS252_LS.csv',
        'CHAMPION RAWEW13v2 WEIGHTED GEAR16': CHAMP,
    }
    for name, p in cases.items():
        r = load_ret(p).dropna()
        ev = BP.evaluate(r, spy=spy, ief=ief, cta=cta)
        print(f"\n== {name}  n={len(r)} span {r.index[0].date()} -> {r.index[-1].date()}")
        print(f"   candidate net SR {ev['candidate_sr']:.3f}")
        for k, v in ev['benchmarks'].items():
            print(f"   {k:12s} SR {v['sr']:7.3f}  n={v['n']}  {v.get('note', '')}")
        m = ev.get('margin')
        print(f"   best passive = {ev['best']}   margin = "
              f"{'NA' if m is None else f'{m:+.3f}'}   PASS={ev['pass']}  "
              f"reason={ev['reason']}")


def part_b():
    print()
    print('=' * 78)
    print('(b) Cross-verify HUNT_CREDIT2 round-2 negatives from their SAVED sleeve CSVs')
    print('=' * 78)
    champ = load_ret(CHAMP)
    published = {   # numbers as published in HUNT_CREDIT2 FINDINGS/DEAD_IDEAS/meta
        'CREDIT2_lqdltt_k126':    dict(sr=-0.31, h1=-0.24, h2=-0.44, neg=13,
                                       worst=-0.327, corr=0.142),
        'CREDIT2_be_tlttip_k63':  dict(sr=-0.80, h1=-1.10, h2=-0.45, neg=21,
                                       worst=-0.353, corr=-0.050),
        'CREDIT2_curve2s10s_k21': dict(sr=-0.54, h1=-0.59, h2=-0.50, neg=21,
                                       worst=-0.179, corr=-0.128),
    }
    base = f'{ROOT}/campaign/agents/chief/coord/HUNT_CREDIT2/sleeves'
    rows = []
    for name, pub in published.items():
        r = load_ret(f'{base}/{name}.csv')
        r = r.iloc[1:] if r.iloc[0] == 0.0 else r   # drop the day-1 placeholder zero
        neg, worst = neg_years(r)
        h1, h2 = half_split(r)
        got = dict(sr=round(sharpe_d(r), 2), h1=round(h1, 2), h2=round(h2, 2),
                   neg=neg, worst=round(worst, 3),
                   corr=round(corr_to(champ, r), 3))
        mism = [f'{k}: published {pub[k]} vs recomputed {got[k]}'
                for k in pub if abs(float(pub[k]) - float(got[k])) > 0.015 + (
                    0.5 if k == 'neg' else 0.0)]
        rows.append((name, got, mism))
        print(f"\n== {name}  n={len(r)} span {r.index[0].date()} -> {r.index[-1].date()}")
        print(f"   recomputed SR {got['sr']:.2f}  H1 {got['h1']:.2f}  H2 {got['h2']:.2f}  "
              f"negyr {got['neg']}  worst {got['worst']:+.1%}  corrChamp {got['corr']:+.3f}")
        print(f"   published   SR {pub['sr']:.2f}  H1 {pub['h1']:.2f}  H2 {pub['h2']:.2f}  "
              f"negyr {pub['neg']}  worst {pub['worst']:+.1%}  corrChamp {pub['corr']:+.3f}")
        print(f"   MISMATCH: {mism if mism else 'none (all within rounding)'}")

    # fails-closed logic check: recomputed numbers must still FAIL the contract gates
    ok_fail = all(g['sr'] < 1.0 for _, g, _ in rows)
    print(f"\nAll three recomputed sleeves still fail SR>=1.0: {ok_fail}")
    n_mism = sum(len(m) for _, _, m in rows)
    print(f"CROSS-VERIFY VERDICT: {'MATCH' if n_mism == 0 else str(n_mism) + ' MISMATCHES'}"
          f" — HUNT_CREDIT2 round-2 negatives {'CONFIRMED' if n_mism == 0 else 'ESCALATE'}")
    return n_mism


if __name__ == '__main__':
    part_a()
    n = part_b()
    sys.exit(0 if n == 0 else 1)
