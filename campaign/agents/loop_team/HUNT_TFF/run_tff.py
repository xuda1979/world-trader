"""TFF screen: 13 families x 4 categories + dealer-assetmgr diff + lev-money fade/mom
-> index futures proxies + rates + sectors. Full honesty; sort by SR."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "campaign"))
import numpy as np, pandas as pd
import tff_eng
from bt import gates

FAMS = ["sp500_emini","nasdaq_emini","dow_emini","us_2y_note","us_5y_note","us_10y_note",
        "us_tbond","eur","jpy","gbp","vix","sofr_3m","eurodollar_3m"]
CATS = ["dealer","asset_mgr","lev_money","other_rept"]
SYMS = {"sp500_emini":"SPY","nasdaq_emini":"QQQ","dow_emini":"DIA","us_2y_note":"IEF",
        "us_5y_note":"IEF","us_10y_note":"TLT","us_tbond":"TLT","eur":"SPY","jpy":"SPY",
        "gbp":"SPY","vix":"SPY","sofr_3m":"TLT","eurodollar_3m":"TLT"}

rows = []
def add(tag, net):
    if net is None or len(net) < 400: return
    rep = gates.run(net)
    rows.append((tag, len(net), round(float(rep["sr"]), 3), rep["neg_years"], round(float(rep["worst"]), 3)))

for fam in FAMS:
    sym = SYMS[fam]
    for cat in CATS:
        try:
            s = tff_eng.load_tff(fam, cat)
        except FileNotFoundError:
            continue
        zs = tff_eng.z(s)
        for name, fn in (("fade", tff_eng.fade), ("mom", tff_eng.mom_sig)):
            sig = fn(zs)
            try:
                add(f"{fam}/{cat}_{name}_{sym}", tff_eng.run(sig, sym))
            except Exception:
                pass
    # category DIFF: dealer vs asset_mgr (inventory stress), lev fade
    try:
        d = tff_eng.diff_series(fam, "dealer", "asset_mgr")
        zs = tff_eng.z(d)
        add(f"{fam}/DIFF-dealer-am_mom_{sym}", tff_eng.run(tff_eng.mom_sig(zs), sym))
        add(f"{fam}/DIFF-dealer-am_fade_{sym}", tff_eng.run(tff_eng.fade(zs), sym))
        lv = tff_eng.load_tff(fam, "lev_money")
        zlv = tff_eng.z(lv)
        add(f"{fam}/levfade_{sym}", tff_eng.run(tff_eng.fade(zlv), sym))
        add(f"{fam}/levmom_{sym}", tff_eng.run(tff_eng.mom_sig(zlv), sym))
    except FileNotFoundError:
        pass

d = pd.DataFrame(rows, columns=["tag","n","sr","neg","worst"]).sort_values("sr", ascending=False)
print(d.head(24).to_string(index=False))
print("variants:", len(d), "| sr>=0.6:", (d.sr >= 0.6).sum(), "| sr>=0.3:", (d.sr >= 0.3).sum(), "| sr>0:", (d.sr > 0).sum())
d.to_csv("screen_tff.csv", index=False)
