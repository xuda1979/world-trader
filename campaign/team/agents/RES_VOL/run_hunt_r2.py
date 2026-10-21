#!/usr/bin/env python3
"""RES_VOL R2: extend the hunt with the splice that HUNT_VOL2/A5 used (FRED spy_early
1993-2005 + SPY 2006-09+, seam nulled) -> RVX (2009-09) AND VIX9D (2011-01) slopes and VRP
get 20y/15y windows instead of 9y. Also: VIX9D RV-lead inversion book (shortening back),
and VRP on the spliced index. Same gates/costs/vt as R1 (vol_r1.long_book / slope_book).
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/team")

import numpy as np
import pandas as pd
from campaign.harness import data as D
from team.agents.RES_VOL.vol_r1 import (load_vol, realized_vol, vrp_series, slope_series,
                                        long_book, slope_book)
from team.agents.RES_VOL.vol_r2 import spliced_spx as spliced_spx_levels
from team.agents.RES_VOL.run_hunt import champ_rets, benchmark_series, evaluate


def main():
    champ = champ_rets(); spy, ief, cta = benchmark_series()
    px = spliced_spx_levels()
    vix = load_vol('VIX'); rvx = load_vol('RVX'); v9 = load_vol('VIX9D')
    v3 = load_vol('VIX3M'); v6 = load_vol('VIX6M'); vvix = load_vol('VVIX')
    out = {}
    print("=== E. VRP long book on spliced SPX (VIX 1990+ x RV 1993+) ===")
    for lb in (10, 21, 63):
        vrp = vrp_series(vix, realized_vol(px.dropna(), lb))
        for thr in (0.0, 2.0, 4.0, -2.0):
            nm = f"W_spx_vrp{lb}_thr{thr:+.0f}"
            net, We, r = long_book(vrp, px.dropna(), thr=thr, hold=5, return_rpu=True)
            r = evaluate(nm, net, We, champ, spy, ief, cta, rpu=r)
            if r:
                out[nm] = r
    print("=== F. slope books on spliced SPX: 3m/6m (2008+), 9d/3m (2011+) ===")
    for nm, a, b in (('W_s3m6m', v3, v6), ('W_s9d3m', v9, v3), ('W_s9d6m', v9, v6)):
        sl = slope_series(a, b)
        for side in ('short', 'long'):
            nm2 = f"{nm}_{side}"
            net, We, r = slope_book(sl, px.dropna(), enter=0.0, exit_=0.0, side=side,
                                    return_rpu=True)
            r = evaluate(nm2, net, We, champ, spy, ief, cta, rpu=r)
            if r:
                out[nm2] = r
    print("=== G. 9d RV-lead: VIX9D > trailing RV21 (fast vol bid ahead of realized) ===")
    pxn = px.dropna()
    rv21 = realized_vol(pxn, 21)
    lead = (v9.shift(1) - rv21.reindex(v9.index)).dropna()
    for side in ('short', 'long'):
        nm = f"W_9dlead_{side}"
        net, We, r = slope_book(lead, pxn, enter=0.0, exit_=0.0, side=side, return_rpu=True)
        r = evaluate(nm, net, We, champ, spy, ief, cta, rpu=r)
        if r:
            out[nm] = r
    npass = sum(1 for v in out.values() if all(v['ok'].values()))
    v2p = sum(1 for v in out.values() if v['pass_'])
    print(f"\n=== SCORECARD R2: {len(out)} books | local-pass {npass} | V2-pass {v2p} ===")
    for k, v in sorted(out.items(), key=lambda kv: -(kv[1]['sr'] if np.isfinite(kv[1]['sr']) else -9))[:20]:
        print(f"  {k}: SR={v['sr']:.2f} corr={v['corr']:+.3f} neg={v['neg']} "
              f"H1={v['h1']:.2f} H2={v['h2']:.2f} worst={v['worst']*100:.1f}% v2pass={v['pass_']}")


if __name__ == '__main__':
    main()
