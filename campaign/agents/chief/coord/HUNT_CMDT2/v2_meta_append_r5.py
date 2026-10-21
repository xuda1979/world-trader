#!/usr/bin/env python3
"""R5 post-audit: the in-sweep v2_battery was called with r=NET (so gates.run's internal
sig*r book and its beats-passive candidate were distorted diagnostics). This script re-runs
the battery CONTRACT-CORRECT (r = per-unit return, sig*r == the held gross book) and APPENDS
the corrected v2 line to every R5 sleeve .meta — the original (distorted) line is retained
above it, labeled. Both verdicts agree: 0/28 pass. Evidence: /tmp/cmdt2_r5_v2_correct.json.
"""
import sys, json
sys.path.insert(0, '/Users/daxu/software/world-trader')
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/scripts')
import HUNT_CMDT2_round5 as M
import HUNT_CMDT2_round1 as H1

champ = M.champ_rets(); spy, ief, cta = M.benchmark_series()
r, r2 = M.prop_ung_returns()
spread_ret = (r2['prop'] - r2['ung'])
OUT = json.load(open('/tmp/cmdt2_r5_v2_correct.json'))

def configs():
    for months in M.GRID_SEASON:
        for vt in (True, False):
            yield (f"prop_seas_{months[0]:02d}-{months[-1]:02d}{'_vt' if vt else '_novt'}",
                   lambda m=months, v=vt: M.run_seasonal(r, months_long=m, vt=v), 'leg', r)
    for win, lo in M.GRID_TREND:
        for vt in (True, False):
            yield (f"prop_trend_w{win}_{'lo' if lo else 'ls'}{'_vt' if vt else '_novt'}",
                   lambda w=win, l=lo, v=vt: M.run_trend(r, win=w, long_only=l, vt=v), 'leg', r)
    for win, zi in M.GRID_SPREAD:
        yield (f"prop_spreadmr_w{win}_z{zi:.0f}_vt",
               lambda w=win, z=zi: M.run_spread_book(r2, win=w, z_in=z, z_out=0.0), 'spr', spread_ret)

for nm, fn, kind, r_per in configs():
    if kind == 'spr':
        net, We, gross, W = fn()
    else:
        net, We, gross = fn()
    net = H1.trim_warmup(net, We)
    idx = net.index
    rp = r_per.reindex(idx).fillna(0.0)
    sig = (We['prop'] if kind == 'spr' else We['p']).reindex(idx).fillna(0.0)
    g2 = M.v2_battery(rp, sig=sig, ref=champ.reindex(idx).fillna(0.0), spy=spy, ief=ief, cta=cta)
    d = OUT[nm]['v2_gross']
    line = (f"v2_corrected: r=per-unit (sig*r==held book) leak_corr={d['leak_corr']:.4f} "
            f"leak_p={d['leak_p']:.2e} leak_ok={d['leak_ok']} bp_ok={d['bp_ok']} "
            f"best_passive={d['bp_best']}:{d['bp_best_sr']:.3f} v2sr={g2['sr']:.3f} "
            f"corr={d['corr']:.4f} pass={str(d['pass_']).lower()} "
            f"[supersedes the distorted in-sweep 'v2:' line above; both verdicts FAIL]\n")
    with open(f"{M.SLEEVES}/{nm}.csv.meta", 'a') as f:
        f.write(line)
    print(nm, 'appended: pass=%s' % d['pass_'])
