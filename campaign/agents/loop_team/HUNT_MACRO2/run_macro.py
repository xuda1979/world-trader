"""Macro2 screen: new-FRED series gates on equity/ETFs."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "campaign"))
import numpy as np, pandas as pd
import macro_eng
from bt import gates

rows = []
def add(tag, net):
    if net is None or len(net) < 500: return
    rep = gates.run(net)
    rows.append((tag, len(net), round(float(rep["sr"]), 3), rep["neg_years"], round(float(rep["worst"]), 3)))

SERIES = ["RRPONTSYD", "WALCL", "T10Y3M", "TEDRATE", "NFCICREDIT", "NFCIRISK", "STLFSI4",
          "JTSJOL", "JTSQUR", "GFDEGDQ188S", "MORTGAGE30US", "SOFR", "T10YIE", "USEPUINDXD"]
FORMS = {
    "z":     lambda s: macro_eng.zsig(s, 252, 126),
    "zinv":  lambda s: macro_eng.zsig(s, 252, 126, invert=True),
    "med":   lambda s: macro_eng.longflat(s, 252, 126),
    "medinv":lambda s: 1.0 - macro_eng.longflat(s, 252, 126),
    "mom":   lambda s: macro_eng.mom_gate(s, 63),
    "mominv":lambda s: macro_eng.mom_gate(s, 63) * -1,
}
for sid in SERIES:
    try:
        s = macro_eng.load(sid)
    except FileNotFoundError:
        continue
    for fname, fn in FORMS.items():
        try:
            sig = fn(s)
        except Exception:
            continue
        for sym in ("QQQ", "DIA"):
            try:
                add(f"{sid}_{fname}_{sym}", macro_eng.run(sig, sym))
            except FileNotFoundError:
                pass

d = pd.DataFrame(rows, columns=["tag","n","sr","neg","worst"]).sort_values("sr", ascending=False)
print(d.head(22).to_string(index=False))
print("variants:", len(d), "| sr>=0.3:", (d.sr >= 0.3).sum(), "| sr>0:", (d.sr > 0).sum())
d.to_csv("screen_macro.csv", index=False)
