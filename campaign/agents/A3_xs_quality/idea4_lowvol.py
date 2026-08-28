"""Idea 4: Low-risk anomaly: long low idio_vol, short high idio_vol. Monthly."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
from engine import *
import pandas as pd, numpy as np

px, rets = load_rets()
feat = pd.read_parquet("/Users/daxu/software/world-trader/alphaportfolio_replication/data/daily_features.parquet")
feat["date"] = pd.to_datetime(feat["date"])
feat = feat[feat.symbol.isin(px.columns)]
sig = feat.pivot_table(index="date", columns="symbol", values="idio_vol")
sig = -sig                                  # low idio vol = long
sig = sig.reindex(px.index, method="ffill", limit=35).where(px.notna())
print("names/ME median:", int(sig.notna().sum(axis=1).median()))

net, w, turn = backtest(sig, rets)
vt = vol_target(net)
ok, g = full_gates(vt, "idea4_lowidiovol_1/3")
turn_bps = round(turn.mean()*6, 2)
print("turn bps/day:", turn_bps)
if ok:
    p, q = scramble_test(sig, rets, g["SR"])
    print("scramble p:", p)
    ok &= p < 0.05
if ok:
    D.save_sleeve(vt.iloc[60:], "/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality/sleeves/QA_low_idio_vol.csv",
        meta="Sleeve: QA_low_idio_vol (A3_xs_quality r1 idea4)\nSignal: negative idio_vol (252d daily residual vol, trailing) from alphaportfolio_replication/daily_features.parquet; long lowest tercile, short highest tercile, monthly rebalance, T+1, 6bps one-side, vol-target 10%% trailing expanding.\nValidation r1: %s | scramble p=%.3f | turn bps/day=%.2f\nEconomic rationale: low-risk anomaly (Baker-Haugen; Frazzini-Pedersen BAB/QMJ) — low-vol stocks deliver higher risk-adjusted returns due to leverage constraints and lottery-demand; short high-idio-vol names whose returns overpay for risk.\nCaveats: window starts 2016 (features coverage); survivorship-biased panel biases against short leg (delisted losers excluded) — estimate is conservative.\n" % (g, p, turn_bps))
    print("SAVED QA_low_idio_vol")
