#!/usr/bin/env python3
"""R2(b) AUDIT_RECON: DEAD_IDEAS.csv spot-audit — re-run 3 sampled dead configs and verify
the 'dead' verdict reproduces against the exact numbers quoted in the ledger.

 1. COT sw-follow lb=12  (HUNT_COT2, DEAD_IDEAS row 64): expect SR 0.287, halves (-0.14,+0.58),
    negyr 4, scramble p 0.652 -> FAIL (SR<1.0 gate).
 2. TIPS real-yield reversion DFII10 N=252 th=1.0 (HUNT_TREASFUT, row 61): expect SR -0.11,
    13 neg years, worst -26.6%; full 4x3 scan every cell in [-0.30,-0.09] -> FAIL.
 3. Intl 10y yield-spread carry lag0 (HUNT_TREASFUT row 63 / HUNT_INTERNATIONAL2 row 65):
    expect blend SR 0.77 ann 1.2% << 1.0 gate, corrChamp 0.319-0.328 > 0.15 -> FAIL.
"""
import sys, math
sys.path.insert(0, '/Users/daxu/software/world-trader')
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/scripts')
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_COT2')
import numpy as np, pandas as pd

import HUNT_TREASFUT_round1 as T
from bt import metrics
import bt.gates as bgates

fails = []
def check(name, cond, detail):
    tag = "PASS" if cond else "FAIL"
    print(f"[{tag}] {name}: {detail}")
    if not cond: fails.append(name)

print("=" * 78)
print("DEAD-IDEA 1: COT sw-follow lb=12 (ledger: SR 0.287, halves -0.14/+0.58, negyr 4, scr 0.652)")
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_COT2')
import hunt_r1 as HC
pan = HC.build_panels()
pos_fade = HC.L.hedger_fade_positions(pan['sw'], lookback=12)
g, r = HC.book_backtest(-pos_fade, pan, vt=True, label='R2-audit sw-follow lb=12')
print(f"  reproduced: SR={g['sr_full']:.3f} ann={g['ann_ret']:.3%} halves=({g['sr_h1']:.2f},{g['sr_h2']:.2f}) "
      f"negyr={g['neg_years']} scramble_p={g['scramble_p']:.3f} corr={g.get('corr_champ', float('nan')):.3f}")
check("DEAD1-verdict", (abs(g['sr_full'] - 0.287) < 0.02 and g['sr_full'] < 1.0
                        and g['sr_h1'] < 0.5 and abs(g['sr_h2'] - 0.58) < 0.05 and g['neg_years'] > 2),
      "ledger numbers reproduce within tolerance AND config fails SR>=1.0 / halves>=0.5 / yearly gates -> dead verdict CONFIRMED")

print("=" * 78)
print("DEAD-IDEA 2: TIPS reversion DFII10 N=252 th=1.0 (ledger: SR -0.11, 13 negyr, worst -26.6%)")
Rt, yt = T.bond_frame({'10': 'DFII10'})
W = T.w_tips_rev(yt['10'], 252, 1.0)
net, We, gg = T.net_of(W, Rt)
res = T.evaluate('R2-audit tipsrev_N252_t10', net, We, Rt)
print(f"  reproduced: SR={res['sr']:.2f} H1={res['h1']:.2f} H2={res['h2']:.2f} negyr={res['neg']} "
      f"worst={res['worst']*100:.1f}% corrChamp={res['corr']:.3f} PASS={res['pass']}")
scan = {}
for N in [63, 126, 252, 504]:
    for th in [0.5, 1.0, 1.5]:
        Ws = T.w_tips_rev(yt['10'], N, th)
        ns, Wse, _ = T.net_of(Ws, Rt)
        scan[(N, th)] = metrics.sharpe_d(ns.dropna())
allneg = all(-0.35 <= v <= -0.05 for v in scan.values())
check("DEAD2-verdict", (abs(res['sr'] - (-0.11)) < 0.02 and res['neg'] == 13
                        and abs(res['worst'] - (-0.266)) < 0.01 and res['pass'] is False and allneg),
      f"SR {res['sr']:.2f}/13 negyr/worst {res['worst']*100:.1f}% reproduce; full 4x3 scan "
      f"SR range [{min(scan.values()):.2f},{max(scan.values()):.2f}] every cell negative -> dead CONFIRMED")

print("=" * 78)
print("DEAD-IDEA 3: intl 10y yield-spread carry lag0 (ledger: blend SR 0.77 ann 1.2%, corr 0.319-0.328)")
Rs_d, Ws_d = T.run_intl_carry(lag_m=0)
comb, nets_d = T.net_intl(lag_m=0)
for k, n in nets_d.items():
    print(f"  pair US-{k}: SRm*sqrt12={metrics.sharpe_m(n):6.2f} negyr={metrics.neg_years(n)[0]}")
res_d = T.evaluate_monthly('R2-audit intlcarry3_lag0', comb, Ws_d, Rs_d)
best_pair = max(metrics.sharpe_m(n) for n in nets_d.values())
print(f"  reproduced: blend SR={res_d['sr']:.2f} ann={res_d['ann']*100:.2f}% negyr={res_d['neg']} "
      f"corrChamp={res_d['corr']:.3f} best-pair={best_pair:.2f} PASS={res_d['pass']}")
check("DEAD3-verdict", (abs(res_d['sr'] - 0.77) < 0.03 and res_d['ann'] < 0.02
                        and abs(res_d['corr'] - 0.319) < 0.015 and abs(best_pair - 0.48) < 0.03
                        and res_d['pass'] is False),
      f"blend SR {res_d['sr']:.2f} / ann {res_d['ann']*100:.2f}% << 1.0 gate; corrChamp {res_d['corr']:.3f} > 0.15; "
      f"best pair {best_pair:.2f} -> dead CONFIRMED")

print("=" * 78)
print("FAILS:", fails if fails else "none — all 3 dead verdicts REPRODUCE (dead is dead)")
sys.exit(1 if fails else 0)
