"""PDA screen: PD/SOMA/FIMA shares -> SPY/QQQ/DIA gates + longflat, 1-day lag built-in."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "campaign"))
import numpy as np, pandas as pd
import pda_eng
from bt import gates

df = pda_eng.load_a()
rows = []
def add(tag, net):
    if net is None or len(net) < 500: return
    rep = gates.run(net)
    rows.append((tag, len(net), round(float(rep["sr"]), 3), rep["neg_years"], round(float(rep["worst"]), 3)))

SIGNALS = {
    "pd_share": (df, "primary_dealer_accepted_mmn"),
    "soma_share": (df, "soma_accepted_mmn"),
    "fima_share": (df, "fima_accepted_mmn"),
    "pd_indirect": None,   # ratio below
}
d = df[df["type"].isin(("Note","Bond"))].dropna(subset=["primary_dealer_accepted_mmn","indirect_accepted_mmn","total_accepted_mmn"])
d = d[d["total_accepted_mmn"] > 0]
ratio = (d["primary_dealer_accepted_mmn"] / d["indirect_accepted_mmn"]).clip(0, 10)
ratio.index = d["date"]
SIGNALS["pd_indirect"] = ratio

for name, obj in SIGNALS.items():
    if name == "pd_indirect":
        s = obj[~obj.index.duplicated(keep="last")].sort_index()
        daily = pd.date_range(s.index[0], s.index[-1], freq="D")
        base = s.reindex(daily).ffill()
        base.index = base.index + pd.Timedelta(days=1)
    else:
        base = pda_eng.share_daily(obj[0], obj[1])
    zs = pda_eng.z(base)
    for zname, sig in (("zinv", -np.sign(zs).fillna(0)), ("z", np.sign(zs).fillna(0)),
                       ("lf_hi", (base > base.rolling(252, min_periods=126).median()).astype(float)),
                       ("lf_lo", (base < base.rolling(252, min_periods=126).median()).astype(float))):
        for sym in ("SPY", "QQQ", "DIA"):
            try:
                add(f"{name}_{zname}_{sym}", pda_eng.run_gate(sig, sym))
            except FileNotFoundError:
                pass

out = pd.DataFrame(rows, columns=["tag","n","sr","neg","worst"]).sort_values("sr", ascending=False)
print(out.head(20).to_string(index=False))
print("variants:", len(out), "| sr>=0.3:", (out.sr >= 0.3).sum(), "| sr>0:", (out.sr > 0).sum())
out.to_csv("screen_pda.csv", index=False)
