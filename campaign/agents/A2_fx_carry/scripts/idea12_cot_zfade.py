"""Idea 12 (charter 1a): lev-fund net z-score contrarian fade, weekly, TFF 2010+."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import a2_lib
from a2_lib import cot_weekly, weekly_pos_from_z, asset_sleeve, run_book, report
import pandas as pd, numpy as np

nets = cot_weekly("tff", "lf")
for lb in (26, 52, 104):
    for thr in (1.0, 1.5, 2.0):
        book = {}
        for a, net in nets.items():
            sig = weekly_pos_from_z(net, lb, thr, contrarian=True)
            book[a] = asset_sleeve(sig, a)
        combo = run_book(book)
        if len(combo) > 2000:
            report(f"1a zfade lb={lb} thr={thr}", combo)
        else:
            print(f"1a zfade lb={lb} thr={thr}: too short n={len(combo)}")
