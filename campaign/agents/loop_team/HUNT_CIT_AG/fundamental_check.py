"""Is lean_hogs-noncomm->SOYB a real premise or a cross-family artifact? The signal is hogs
positioning traded on SOYB — economically incoherent. Test the honest mapping: each family
on its OWN complex (hog signal -> meat proxy absent; corn signal -> CORN; wheat -> WEAT...).
Also PCPS spot momentum + CIT as designed."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "campaign"))
import numpy as np, pandas as pd
import cit_ag
from bt import gates

# economic mapping: same-complex only
MAPS = [
    ("corn", "CORN"), ("wheat_srw", "WEAT"), ("soybeans", "SOYB"),
    ("soybean_oil", "SOYB"), ("soybean_meal", "SOYB"), ("sugar_no11", "CANE"),
    ("cocoa", "DBA"), ("coffee_c", "DBA"), ("cotton_no2", "DBA"),
    ("live_cattle", "DBA"), ("lean_hogs", "DBA"), ("feeder_cattle", "DBA"),
    ("corn", "MOO"), ("soybeans", "MOO"), ("live_cattle", "MOO"), ("lean_hogs", "MOO"),
]
rows = []
for fam, sym in MAPS:
    for kind in ("cit", "noncomm"):
        try:
            cot = cit_ag.load_cot(fam, kind)
        except FileNotFoundError:
            continue
        px = cit_ag.load_close(sym)
        net = cit_ag.run_sleeve(cot, px)
        if len(net) < 400: continue
        rep = gates.run(net)
        rows.append((fam, kind, sym, len(net), round(float(rep["sr"]), 3),
                     rep["neg_years"], round(float(rep["worst"]), 3)))
df = pd.DataFrame(rows, columns=["fam","kind","sym","n","sr","neg","worst"]).sort_values("sr", ascending=False)
print(df.to_string(index=False))

# PCPS spot momentum on own ETF (the 'fundamental' family): 63d & 126d
print("\n== PCPS spot mom -> own ETF ==")
PCPS = {"PWHEAMTUSDM": "WEAT", "PMAIZMTUSDM": "CORN", "PSOYBUSDM": "SOYB",
        "PSUGAUSAUSDM": "CANE", "PCOFFOTMUSDM": "DBA", "PCOCOUSDM": "DBA", "PCOTTINDUSDM": "DBA"}
rows2 = []
for pid, sym in PCPS.items():
    f = os.path.join(ROOT, "tools/quant/data/more_fred", f"{pid}.csv")
    if not os.path.exists(f): continue
    dfp = pd.read_csv(f, parse_dates=["date"])
    s = dfp.set_index("date")["value"].astype(float).sort_index()
    px = cit_ag.load_close(sym)
    r = px.pct_change()
    for lb in (21, 63, 126):
        mom = s.pct_change(lb)
        sig_live = mom.reindex(r.index).ffill()
        from bt.engine import lag_signal, vol_target_scale, cap_leverage
        scale = vol_target_scale(r).fillna(1.0)
        w = (lag_signal(sig_live.fillna(0)) * scale).fillna(0)
        wc = cap_leverage(w.to_frame("w"), max_lev=1.6)
        from bt.engine import cost_turnover, borrow_cost, margin_cost
        net = (wc["w"] * r - cost_turnover(wc, 6.4) - borrow_cost(wc, 0.005)
               - margin_cost(wc["w"].abs(), 0.045, 1.6)).dropna()
        if len(net) < 400: continue
        rep = gates.run(net)
        rows2.append((pid, sym, lb, round(float(rep["sr"]), 3), rep["neg_years"]))
df2 = pd.DataFrame(rows2, columns=["pcps","sym","lb","sr","neg"]).sort_values("sr", ascending=False)
print(df2.head(12).to_string(index=False))
