"""Idea 13 (charter 1b): asset-manager net 6m-change momentum follow, TFF 2010+."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import a2_lib
from a2_lib import cot_weekly, weekly_pos_from_change, asset_sleeve, run_book, report
import numpy as np

nets = cot_weekly("tff", "am")
for lb in (13, 26, 52):
    for mf in (0.0, 0.05):
        book = {}
        for a, net in nets.items():
            sig = weekly_pos_from_change(net, lb, min_frac=mf)
            book[a] = asset_sleeve(sig, a)
        combo = run_book(book)
        report(f"1b AM-mom lb={lb} mf={mf}", combo)
# also lev-fund change (levs as momentum too)
print("-- lev-fund change variant --")
nets_lf = cot_weekly("tff", "lf")
for lb in (26, 52):
    book = {}
    for a, net in nets_lf.items():
        sig = weekly_pos_from_change(net, lb, min_frac=0.0)
        book[a] = asset_sleeve(sig, a)
    report(f"1b' LF-change lb={lb}", run_book(book))
