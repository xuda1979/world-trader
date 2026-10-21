#!/usr/bin/env python3
"""HUNT_INTERNATIONAL2 round-1 independent EXTENSIONS (2026-09-07, agent re-run).

The predecessor's 12-name panel omitted EWJ-adjacent DM names the charter explicitly lists
(EWA is in more_etf but starts 2012; EWH/EWM start 2006-10). Charter also names index series
(NIKKEI225 / NASDAQCOM). These extensions test whether the predecessor's negative was an
artifact of universe choice or is robust:

 EXT-A: momentum with 14-name universe (UNIV + EWH + EWM), 12m & 12-1m, k=3.
 EXT-B: NIKKEI225 vs NASDAQCOM long-history pair rotation (12m, 1972->), L/S and long-only.
 EXT-C: carry panel extension: IRLTLT01AUM156N(AUD)/CAM156N(CAD) exist but no matching
        single-country ETF pre-2006 -> NOT testable with the equity leg. Logged as data gap.
Honesty: identical machinery as HUNT_INTL2_round1.py (imported, not copied).
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
import importlib.util
from bt import metrics
import bt.gates as bgates

spec = importlib.util.spec_from_file_location(
    "hintl", "/Users/daxu/software/world-trader/campaign/scripts/HUNT_INTL2_round1.py")
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)

CHAMP = H.CHAMP

print('=== no-lookahead spot check (14-name univ, 12m,k3) ===')
UNIV14 = H.UNIV + ['EWH', 'EWM']
px14 = H.px_frame(UNIV14)
R14 = px14.pct_change()
ok = H.no_lookahead_check(px14, 12, 3)
print('weights identical with future truncated:', ok)
assert ok, 'LOOKAHEAD DETECTED'

print('\n=== EXT-A: 14-name country momentum, chosen + neighbor configs ===')
for months, topk, skip, tag in [(12, 3, 0, '12m_k3'), (12, 3, 1, '12-1m_k3'),
                                (9, 3, 0, '9m_k3'), (15, 3, 0, '15m_k3'),
                                (12, 2, 0, '12m_k2'), (12, 4, 0, '12m_k4')]:
    net, We, g, W = H.run_momentum(px14, R14, months, topk, skip=skip)
    r = H.evaluate(f'EXTA_{tag}', net, We, R14, verbose=False)
    print(f"  {tag:9s} n={r['n']} {r['start']}->{r['end']} SR={r['sr']:6.2f} H1={r['h1']:6.2f} "
          f"H2={r['h2']:6.2f} negyr={r['neg']:2d} worst={r['worst']*100:6.1f}% "
          f"p={r['p']:.3f} corr={r['corr']:6.3f} PASS={r['pass']}")

print('\n=== EXT-A sweep (net SR, eval from first live day, 2007-12+ rule kept off to see raw) ===')
sweep = {}
for months in [6, 9, 12, 15, 18]:
    for topk in [2, 3, 4]:
        net, We, g, W = H.run_momentum(px14, R14, months, topk)
        net = net.dropna(); net = net[net.index >= '2007-12-01']
        sweep[(months, topk)] = metrics.sharpe_d(net)
peak = max(sweep.values()); pk = [k for k, v in sweep.items() if v == peak][0]
print(f"  peak SR={peak:.2f} at {pk} (all 15 configs negative: {all(v < 1.0 for v in sweep.values())})")
for k in sorted(sweep):
    print(f"    lookback={k[0]:>2}m topk={k[1]}  SR={sweep[k]:6.2f}")

print('\n=== EXT-B: NIKKEI225 vs NASDAQCOM rotation (long history) ===')
def load_idx(name):
    df = pd.read_csv(f"{H.ROOT}/tools/quant/data/newdata/{name}.csv", index_col=0, parse_dates=True)
    s = df.iloc[:, 0].astype(float)
    s = s[~s.index.duplicated(keep='last')].sort_index()
    return s

NIK, NAS = load_idx('NIKKEI225'), load_idx('NASDAQCOM')
print(f"  NIKKEI225 {NIK.index[0].date()}->{NIK.index[-1].date()}  "
      f"NASDAQCOM {NAS.index[0].date()}->{NAS.index[-1].date()}")
pxi = pd.concat({'NIK': NIK, 'NAS': NAS}, axis=1).dropna().sort_index()
Ri = pxi.pct_change()
print(f"  common window: {pxi.index[0].date()} -> {pxi.index[-1].date()}  n={len(pxi)}")
okb = H.no_lookahead_check(pxi, 12, 1)
print('  no-lookahead (pair) :', okb)
assert okb
for months, skip, tag in [(12, 0, '12m'), (12, 1, '12-1m'), (6, 0, '6m'), (18, 0, '18m')]:
    for ls, tag2 in [(True, 'LS'), (False, 'LO')]:
        net, We, g, W = H.run_emdm(Ri.iloc[:, 0], Ri.iloc[:, 1], months, skip=skip,
                                   longshort=ls, gross=2.0)
        r = H.evaluate(f'EXTB_NIKvNAS_{tag}_{tag2}', net, We, Ri, verbose=False)
        print(f"  {tag:6s} {tag2} n={r['n']} {r['start']}->{r['end']} SR={r['sr']:6.2f} "
              f"H1={r['h1']:6.2f} H2={r['h2']:6.2f} negyr={r['neg']:2d} worst={r['worst']*100:6.1f}% "
              f"p={r['p']:.3f} corr={r['corr']:6.3f} PASS={r['pass']}")

print('\n=== EXT-C: data-gap check (charter-carry extension) ===')
for f in ['IRLTLT01AUM156N', 'IRLTLT01CAM156N']:
    s = pd.read_csv(f"{H.ROOT}/tools/quant/data/more_fred/{f}.csv", index_col=0, parse_dates=True)['value']
    print(f"  {f}: {s.index[0].date()}->{s.index[-1].date()} — no pre-2006 single-country ETF "
          f"(EWA starts 2012, EWC absent) -> carry extension untestable")
