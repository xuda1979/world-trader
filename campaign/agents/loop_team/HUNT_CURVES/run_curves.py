"""Screen curve features x tradables. JGB slopes -> USD_JPY/EWJ; GBP -> GBP_USD/EWU;
EUR AAA -> EUR_USD/EWG/EWL/EWA; BIS NEER mom -> UUP/EW-intl; all full honesty stack."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "campaign"))
import numpy as np, pandas as pd
import curve_eng
from bt import gates

rows = []
def add(tag, net):
    if net is None or len(net) < 500:
        return
    rep = gates.run(net)
    rows.append((tag, len(net), round(float(rep["sr"]), 3), rep["neg_years"],
                 round(float(rep["worst"]), 3), round(float(rep["ac1"]), 3)))

# --- JGB curves (1974+) ---
jgb = curve_eng.load_jgb()
for short, long in (("1Y","10Y"), ("2Y","10Y"), ("2Y","30Y"), ("5Y","30Y")):
    if short in jgb.columns and long in jgb.columns:
        feat = curve_eng.slope_spread(jgb, short, long)
        for mode in ("mom", "rev"):
            for sym in ("USD_JPY", "EWJ"):
                try:
                    px = curve_eng.load_fx(sym) if sym == "USD_JPY" else curve_eng.load_etf(sym)
                except FileNotFoundError:
                    continue
                try:
                    add(f"jgb_{short}{long}_{mode}_{sym}", curve_eng.run_curve_sleeve(feat, px, mode=mode))
                except Exception as e:
                    pass

# butterfly 2-5-10
if all(c in jgb.columns for c in ("2Y","5Y","10Y")):
    fly = jgb["5Y"] - 0.5*(jgb["2Y"] + jgb["10Y"])
    for mode in ("mom", "rev"):
        for sym in ("USD_JPY", "EWJ"):
            try:
                px = curve_eng.load_fx(sym) if sym == "USD_JPY" else curve_eng.load_etf(sym)
                add(f"jgb_fly_{mode}_{sym}", curve_eng.run_curve_sleeve(fly, px, mode=mode))
            except Exception:
                pass

# --- ECB AAA curve (2004+) ---
yc = pd.read_csv(os.path.join(ROOT, "tools/quant/data/ecb_yc/ecb_eur_yc_aaa.csv"), parse_dates=["date"]).set_index("date").sort_index()
yc.columns = [c.replace("SR_","") for c in yc.columns]
for short, long in (("1Y","10Y"), ("2Y","30Y"), ("5Y","30Y")):
    feat = yc[long] - yc[short]
    for mode in ("mom", "rev"):
        for sym in ("EUR_USD", "EWG", "EWA", "EWL"):
            try:
                px = curve_eng.load_fx(sym) if sym == "EUR_USD" else curve_eng.load_etf(sym)
                add(f"euryc_{short}{long}_{mode}_{sym}", curve_eng.run_curve_sleeve(feat, px, mode=mode))
            except Exception:
                pass

# --- BIS NEER daily: momentum/reversion of own index is FX carry-adjacent; trade via UUP/EW ---
for ccy in ("US", "JP", "GB", "EU" if False else "CN", "AU", "CA"):
    f = os.path.join(ROOT, "tools/quant/data/bis_eer", f"bis_neerd_broad_{ccy}.csv")
    if not os.path.exists(f):
        continue
    s = pd.read_csv(f, parse_dates=["date"]).set_index("date")["value"].astype(float).sort_index()
    for lb, mode in ((21, "mom"), (63, "mom"), (21, "rev"), (63, "rev")):
        mom = s.pct_change(lb)
        pxs = {"US": ("UUP", None), "JP": ("USD_JPY", None), "GB": ("GBP_USD", None)}.get(ccy)
        if not pxs:
            continue
        sym = pxs[0]
        px = curve_eng.load_fx(sym) if sym.endswith("USD") or sym.startswith("USD") else curve_eng.load_etf(sym)
        # align: signal on NEER, trade the pair
        r = px.pct_change()
        sig = np.sign(mom if mode == "mom" else -mom)
        from bt.engine import lag_signal
        net = __import__("bt").backtest.sleeve(sig, r.to_frame("a"))
        add(f"eer_{ccy}_{mode}{lb}_{sym}", net)

df = pd.DataFrame(rows, columns=["tag","n","sr","neg","worst","ac1"]).sort_values("sr", ascending=False)
print(df.to_string(index=False))
print("\nvariants:", len(df), "| sr>=0.6:", (df.sr >= 0.6).sum(), "| sr>=0.3:", (df.sr >= 0.3).sum())
df.to_csv("screen_curves.csv", index=False)
