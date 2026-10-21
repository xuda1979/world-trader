"""Auction-demand regime screen: btc + indirect share gates on QQQ/DIA (+ EWJ/EWU intl)."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "campaign"))
import numpy as np, pandas as pd
import ta_eng
from bt import gates

df = ta_eng.load_auctions()
print("auctions:", len(df), df.auction_date.min().date(), "->", df.auction_date.max().date())

rows = []
def add(tag, net):
    if net is None or len(net) < 500: return
    rep = gates.run(net)
    rows.append((tag, len(net), round(float(rep["sr"]), 3), rep["neg_years"],
                 round(float(rep["worst"]), 3)))

btc_all = ta_eng.daily_btc(df)
btc_note = ta_eng.daily_btc(df, kind="Note")
ind_note = ta_eng.indirect_share(df, "Note")
ind_bill = ta_eng.indirect_share(df, "Bill")

SERIES = {"btc_all": btc_all, "btc_note": btc_note, "ind_note": ind_note, "ind_bill": ind_bill}
for sname, s in SERIES.items():
    for win in (252, 504):
        for invert in (False, True):
            sig = ta_eng.zgate(s, win=win, invert=invert)
            for sym in ("QQQ", "DIA"):
                try:
                    add(f"{sname}_w{win}{'_inv' if invert else ''}_{sym}", ta_eng.run_on_equity(sig, sym))
                except FileNotFoundError:
                    pass
                # long-flat version: only hold when demand strong
                if invert:
                    lf = sig.where(sig > 0, 0.0)
                    add(f"{sname}_w{win}_longflat_{sym}", ta_eng.run_on_equity(lf, sym))
                else:
                    lf = sig.where(sig > 0, 0.0)
                    add(f"{sname}_w{win}_longflat_{sym}", ta_eng.run_on_equity(lf, sym))

d = pd.DataFrame(rows, columns=["tag","n","sr","neg","worst"]).sort_values("sr", ascending=False)
print(d.head(20).to_string(index=False))
print("variants:", len(d), "| sr>=0.3:", (d.sr >= 0.3).sum(), "| sr>0:", (d.sr > 0).sum())
d.to_csv("screen_auction.csv", index=False)
