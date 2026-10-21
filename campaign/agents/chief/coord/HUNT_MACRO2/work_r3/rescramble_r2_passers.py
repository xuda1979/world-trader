#!/usr/bin/env python3
"""R3 follow-up: re-scramble R2's MDD-arm passers on the costfix (37.195%) champion.

R2 measured T10Y2Y x0.6 / JOINT x0.6 against the pre-costfix champion (39.851%).
The 11:24 re-emit (b268e52) changed the base book, so R2's scramble p-values no
longer describe the committed champion. This rebuilds the champion exactly as R2
does (verified: max|rebuilt-committed| = 1e-16), rebuilds both triggers, and
recomputes the MDD-metric trigger-scramble p (200 perms, seed 11 — R2's config).
"""
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign/agents/chief/coord/HUNT_MACRO2/work_r2")
import HUNT_MACRO2_round2 as R2  # noqa: E402

net, Wg, df = R2.build_champion()
pc = R2.perf(net)
print(f"champion rebuilt: ann={pc['ann']*100:.3f}% SR={pc['sr']:.3f} MDD={pc['mdd']*100:.3f}% "
      f"max|rebuilt-committed|={float((net - R2.CHAMP.reindex(net.index).dropna()).abs().max()):.2e}")

t102 = R2.build_t10y2y_trigger()
vix_s = R2.build_vix_trigger(mode='sustained')
joint = (vix_s | t102).reindex(R2.CHAMP.index).fillna(False)

for nm, m in [("book T10Y2Y z63<-2 x0.6", t102), ("book JOINT x0.6", joint)]:
    mm = m.reindex(net.index).fillna(False).astype(float) * 0.6
    mm = m.reindex(net.index).fillna(False).astype(float)
    mm[mm > 0] = 0.6
    r, _ = R2.eval_book_overlay(nm, m, net, scale=0.6, do_scramble='mdd')
    print(f"{nm:28s} dAnn={r['d_ann']*100:+.3f}pp dMDD={r['d_mdd']*100:+.3f}pp "
          f"ann={r['ann']*100:.2f}% SR={r['sr']:.3f} MDD={r['mdd']*100:.2f}% neg={r['neg']} "
          f"scramble_p(mdd)={r['p']:.3f} accepts_raw={r['accepts_raw']}")
