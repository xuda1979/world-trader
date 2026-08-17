"""Drawdown-filter search for the 1-month XGB L/S (find overlays that cut
maxDD while preserving return). Reads the 20y cached book and FRED risk data.
All signals causal (lagged 1+ day). Reports SR / ann / maxDD / Calmar."""
from __future__ import annotations
import os, sys, pickle
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from xgb_horizon_portfolio import vol_target, stats
import pipeline_common as pc
ROOT = "/Users/daxu/software/world-trader"
FRED = os.path.join(ROOT, "tools/quant/hedge_fund_strats", "data_fred")

def load_series(name):
    df = pd.read_csv(os.path.join(FRED, name), parse_dates=["date"])
    df.columns = ["date", "val"]
    return df.set_index("date")["val"].reindex(
        pd.bdate_range(df.date.min(), df.date.max()), method="ffill")

def build():
    with open(os.path.join(HERE, "data", "horizon_preds_20y.pkl"), "rb") as f:
        c = pickle.load(f)
    frame, preds = c["frame"], c["preds"]
    frame["date"] = pd.to_datetime(frame["date"])
    fw = frame.copy(); fw["pred"] = preds[21]; fw = fw[np.isfinite(fw["pred"])]
    close = pc.load_ohlcv()["close"]
    orig = close.apply(lambda s: s.first_valid_index()); orig = orig[pd.notna(orig)]
    early = set(orig[orig <= pd.Timestamp("2007-02-01")].index)
    fws = fw[fw["ticker"].isin(early)]
    from xgb_horizon_portfolio import build_position_book
    res = build_position_book(fws, fws["pred"].to_numpy(), 21, K=10, cost=0.0006).sort_index()
    rvt = vol_target(res.copy())
    # risk data
    vix = load_series("vix.csv"); spx = load_series("spx.csv")
    idx = rvt.index
    vix_z = (vix - vix.rolling(252).mean())/vix.rolling(252).std(); vix_z = vix_z.reindex(idx).shift(1)
    mt20 = spx.pct_change(20).reindex(idx).shift(1)
    breadth = fws.groupby("date")["pred"].apply(lambda s: (s > 0).mean()).reindex(idx).shift(1)
    return rvt, dict(vix_z=vix_z, mt20=mt20, breadth=breadth)

def report(name, ex):
    out = rvt * ex.fillna(1.0).clip(0, 1); s = stats(out)
    print(f"  {name:<46} SR {s['sr']:.2f} ann {s['ann']:.1%} DD {s['dd']:.1%} Calmar {s['calmar']} act {ex.fillna(1).clip(0,1).mean():.0%}")
    return s

if __name__ == "__main__":
    rvt, R = build()
    print("BASELINE: SR1.92 ann32.9% DD-23.9% Calmar1.38")
    vz, mt, br = R["vix_z"], R["mt20"], R["breadth"]
    print("--- Return-preserving DD filters ---")
    report("VIXz<2 OFF & |mt20|<.01->0.5", (vz < 2.0).astype(float) * ((1-(mt.abs()<0.01).astype(float)) + ((mt.abs()<0.01).astype(float)*0.5)))
    report("VIXz<2 OFF", (vz < 2.0).astype(float))
    print("--- Softer breadth gates ---")
    for lo, hi, frac in [(0.40,0.75,0.3),(0.40,0.75,0.5),(0.35,0.80,0.5),(0.45,0.70,0.3),(0.45,0.70,0.5)]:
        ex = (1-((br<lo)|(br>hi)).astype(float)) + ((br<lo)|(br>hi)).astype(float)*frac
        report(f"breadth<{lo}|>{hi}->{frac}", ex)
    print("--- Combined best ---")
    exv = (vz < 2.0).astype(float)
    exm = (1-(mt.abs()<0.01).astype(float)) + ((mt.abs()<0.01).astype(float)*0.5)
    ext = ((br<0.45)|(br>0.70)).astype(float); exb = (1-ext)+ext*0.5
    report("VIXz<2 & |mt20|<.01->.5 & br<.45|>.7->.5", exv*exm*exb)
