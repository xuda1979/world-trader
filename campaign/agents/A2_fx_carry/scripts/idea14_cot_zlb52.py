"""Idea 14: refine the two promising families (z-fade lb>=52, AM-mom lb=52): try
per-market vs extremes-only, tighter thresholds, gold+silver via legacy overlay, blended."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
from a2_lib import cot_weekly, weekly_pos_from_z, weekly_pos_from_change, asset_sleeve, run_book, report
import pandas as pd, numpy as np

# A) z-fade with different zcaps, blend lb=52 & lb=104 (plateau check)
nets = cot_weekly("tff", "lf")
for lb in (78, 104, 156):
    for thr in (1.25, 1.5, 1.75, 2.0):
        book = {}
        for a, net in nets.items():
            sig = weekly_pos_from_z(net, lb, thr)
            book[a] = asset_sleeve(sig, a)
        report(f"A zfade lb={lb} thr={thr}", run_book(book))

# B) AM-mom longer lookbacks
nets_am = cot_weekly("tff", "am")
for lb in (78, 104):
    book = {}
    for a, net in nets_am.items():
        sig = weekly_pos_from_change(net, lb, 0.0)
        book[a] = asset_sleeve(sig, a)
    report(f"B AM-mom lb={lb}", run_book(book))
