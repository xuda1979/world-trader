#!/usr/bin/env python3
"""HUNT_FXCARRY2 R4 audit, row 63: reproduce the sw-FOLLOW lb=12 mirror (FINDINGS R1 (b):
'MIRRORs: sw-follow lb=12 SR +0.287 halves(-0.14,+0.58) negyr 4, scramble 0.652').
Uses HUNT_COT2's own lib_hunt + hunt_r1.book_backtest unchanged; the ONLY difference from
their hedger_fade_positions is the documented sign flip (mirror = +z/cap, not -z/cap)."""
import sys
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_COT2')
import pandas as pd
import lib_hunt as L
import hunt_r1 as H

pan = H.build_panels()
z = L._zscore_frame(pan['sw'], 12)
pos_follow = (z / 2.0).clip(-1.0, 1.0).fillna(0.0)   # mirror: +z/cap
g, r = H.book_backtest(pos_follow, pan, vt=True, label='MIRROR sw-follow lb=12')
print(f"sw-follow lb=12: SR={g['sr_full']:.3f} halves=({g['sr_h1']:.2f},{g['sr_h2']:.2f}) "
      f"negyr={g['neg_years']} scramble_p={g['scramble_p']:.3f} corr={g.get('corr_champ', float('nan')):.3f}")
print("claimed: SR=+0.287 halves(-0.14,+0.58) negyr 4 scramble 0.652")
