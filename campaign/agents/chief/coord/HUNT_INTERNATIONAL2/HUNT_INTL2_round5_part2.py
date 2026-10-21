#!/usr/bin/env python3
"""HUNT_INTERNATIONAL2 round 5 part 2 — honesty evidence on real NKY data.

(a) end-to-end no-lookahead spot check (truncate at mid-sample, weights identical)
(b) plateau_ok on the natural family grids (momentum lookback; calendar k)
(c) decade-by-decade net SR per config (the charter's sub-span decay evidence)
(d) beats-nothing audit: passive long-NKY B&H net (vt10, 6.4bps full |dW|) on each
    config's matched span + post-1990 + champion-era sub-spans.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np
import pandas as pd
import bt.gates as bgates
from bt import metrics, engine
import HUNT_INTL2_round5 as R5

pxs = R5.load_nky()
R = pxs.pct_change().to_frame("NKY")
print(f"NKY n={len(pxs)} {pxs.index[0].date()} -> {pxs.index[-1].date()}")

print("\n=== (a) no-lookahead spot check (real data, mid-sample truncation) ===")
probe = pxs.index[len(pxs) // 2]
# PRIMARY builders must be STRICTLY truncation-invariant; RANK secondaries are
# published-calendar variants whose only allowed diffs are inside the cut's final
# partial month (the mask of day t in month m uses the month's total bday count).
for fn, args in [("cal_tom_weights", ()), ("cal_toy_weights", ()),
                 ("cal_sellmay_weights", ()), ("mom_weights", (252, "LS")),
                 ("mom_weights", (252, "LF")), ("mom_weights", (126, "LF")),
                 ("mom_weights", (63, "LF"))]:
    f = getattr(R5, fn)
    a = f(pxs, *args).loc[:probe].round(10)
    b = f(pxs.loc[:probe], *args).round(10)
    print(f"  PRIMARY {fn}{args}: identical={a.equals(b)}")
    assert a.equals(b), f"LOOKAHEAD in {fn}"
for fn, args in [("cal_tom_rank_weights", (3, 3)), ("cal_toy_rank_weights", (5,))]:
    f = getattr(R5, fn)
    a = f(pxs, *args).loc[:probe].round(10)
    b = f(pxs.loc[:probe], *args).round(10)
    diff = (a != b).any(axis=1)
    in_last = diff[diff].index.to_period("M") == probe.to_period("M")
    confined = bool(diff.sum() == 0 or in_last.all())
    print(f"  SECONDARY {fn}{args}: diffs={int(diff.sum())} all-in-cut-final-partial-month={confined}")
    assert confined, f"LOOKAHEAD OUTSIDE PARTIAL MONTH in {fn}"

print("\n=== (b) plateau grids (net SR, full 77y span) ===")
def net_sr(W):
    net, We, _ = R5.net_of(W, R)
    net = R5.trim_warmup(net, We)
    return metrics.sharpe_d(net)

mom_grid = {}
for lb in [63, 126, 189, 252, 378, 504]:
    mom_grid[lb] = net_sr(R5.mom_weights(pxs, lb, "LF"))
    print(f"  MOM LF lb={lb}: SR {mom_grid[lb]:.3f}")
ok, info = bgates.plateau_ok(mom_grid, 252)
print(f"  plateau_ok(chosen=252): {ok} neighbors={ {k: round(v,3) for k,v in info['neighbors'].items()} } peak={info['peak']:.3f} thr={info['threshold']:.3f}")

tom_grid = {}
for k in [1, 2, 3, 5]:
    tom_grid[k] = net_sr(R5.cal_tom_rank_weights(pxs, k, k))
    print(f"  TOM-rank k={k}: SR {tom_grid[k]:.3f}")
ok2, info2 = bgates.plateau_ok(tom_grid, 3)
print(f"  plateau_ok(chosen=3): {ok2} neighbors={ {k: round(v,3) for k,v in info2['neighbors'].items()} } peak={info2['peak']:.3f}")

toy_grid = {}
for k in [3, 5, 7]:
    toy_grid[k] = net_sr(R5.cal_toy_rank_weights(pxs, k))
    print(f"  TOY-rank k={k}: SR {toy_grid[k]:.3f}")
ok3, info3 = bgates.plateau_ok(toy_grid, 5)
print(f"  plateau_ok(chosen=5): {ok3} neighbors={ {k: round(v,3) for k,v in info3['neighbors'].items()} }")

print("\n=== (c) decade-by-decade net SR (charter sub-span decay evidence) ===")
configs = [("CAL_TOM_dates", R5.cal_tom_weights(pxs)),
           ("CAL_TOM_rank3", R5.cal_tom_rank_weights(pxs, 3, 3)),
           ("CAL_TOY_dates", R5.cal_toy_weights(pxs)),
           ("CAL_TOY_rank5", R5.cal_toy_rank_weights(pxs, 5)),
           ("CAL_SELLMAY", R5.cal_sellmay_weights(pxs)),
           ("MOM_252_LS", R5.mom_weights(pxs, 252, "LS")),
           ("MOM_252_LF", R5.mom_weights(pxs, 252, "LF")),
           ("MOM_126_LF", R5.mom_weights(pxs, 126, "LF")),
           ("MOM_63_LF", R5.mom_weights(pxs, 63, "LF"))]
dec_rows = {}
for name, W in configs:
    net, We, _ = R5.net_of(W, R)
    net = R5.trim_warmup(net, We)
    decs = net.groupby(net.index.year // 10 * 10).apply(metrics.sharpe_d)
    dec_rows[name] = decs.round(2)
dec = pd.DataFrame(dec_rows)
print(dec.to_string())
dec.to_csv("/Users/daxu/software/world-trader/campaign/agents/chief/coord/"
           "HUNT_INTERNATIONAL2/work_r5/decade_sr_r5.csv")

print("\n=== (d) beats-nothing audit: passive long-NKY B&H (vt10, same costs) ===")
def bh_net(span=None):
    W = pd.DataFrame({"NKY": 1.0}, index=pxs.index)
    net, We, _ = R5.net_of(W, R)
    net = R5.trim_warmup(net, We)
    return net if span is None else net[span[0]:span[1]]

post90 = (pd.Timestamp("1990-01-01"), pxs.index[-1])
champ_era = (pd.Timestamp("2008-03-31"), pd.Timestamp("2026-08-27"))
bh_full = bh_net()
print(f"  long-NKY B&H net full span : SR {metrics.sharpe_d(bh_full):.3f} n={len(bh_full)}")
print(f"  long-NKY B&H net post-1990 : SR {metrics.sharpe_d(bh_net(post90)):.3f}")
print(f"  long-NKY B&H net champ-era : SR {metrics.sharpe_d(bh_net(champ_era)):.3f}")
for name, W in configs:
    net, We, _ = R5.net_of(W, R)
    net = R5.trim_warmup(net, We)
    sub = net[post90[0]:post90[1]]
    subc = net[champ_era[0]:champ_era[1]]
    print(f"  {name:14s} full {metrics.sharpe_d(net):+.3f} | post-1990 {metrics.sharpe_d(sub):+.3f}"
          f" | champ-era(2008+) {metrics.sharpe_d(subc):+.3f}")
print("\npart2 done")
