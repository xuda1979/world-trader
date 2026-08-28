"""Idea 15: which markets drive the lb=104 thr=1.5 z-fade result? Per-asset breakdown + sub-books."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
from a2_lib import cot_weekly, weekly_pos_from_z, asset_sleeve, report, vol_target
import pandas as pd, numpy as np

nets = cot_weekly("tff", "lf")
sigs = {a: weekly_pos_from_z(net, 104, 1.5) for a, net in nets.items()}
sleeves = {a: asset_sleeve(sig, a) for a, sig in sigs.items()}
for a, r in sleeves.items():
    report(f"  per-asset {a}", r)
# sub-books: bonds only, fx only, equity only
for nm, assets in [("bonds", ["UST10","UST2","UST30"]), ("fx", ["EUR","JPY","GBP","CAD"]),
                   ("equity", ["SPY","QQQ"])]:
    df = pd.DataFrame({a: sleeves[a] for a in assets}).fillna(0)
    combo = vol_target(df.mean(axis=1), 0.10)
    report(f"sub-book {nm}", combo)
# bonds-only with thr sweep (is it a plateau?)
for thr in (1.0, 1.25, 1.75, 2.0):
    book = {a: asset_sleeve(weekly_pos_from_z(net, 104, thr), a) for a, net in nets.items() if a in ("UST10","UST2","UST30")}
    df = pd.DataFrame(book).fillna(0)
    report(f"bonds zfade thr={thr}", vol_target(df.mean(axis=1), 0.10))
