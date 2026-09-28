"""HUNT_BINANCE_AXES: full gate documentation for the top 3 finalists (honest negatives).
Runs the 200x signal-scramble + neg-years + plateau check on each, per GATES_CONTRACT.
"""
import hunt_lib as H
import pandas as pd, numpy as np, json

CHAMP = H.load_csv('/Users/daxu/software/world-trader/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv')


def nret(px):
    return px.pct_change().shift(-1)


results = {}

# 1) BTC glob_ls fade w21 / w63 (plateau pair)
pb = H.prices("BTC")
rb = nret(pb["close"])
mb = H.metrics("BTC")
g21 = H.zscore(mb["global_ls_account_ratio"], 21)
g63 = H.zscore(mb["global_ls_account_ratio"], 63)
for name, sig in (("BTC_glob_ls_fade_w21", -g21), ("BTC_glob_ls_fade_w63", -g63)):
    w = sig.clip(-1.0, 1.0).fillna(0.0)
    net = H.run_signal(w, rb)
    sr = H.sr(net); h1, h2 = H.halves_sr(net)
    ny, yearly = H.neg_years(net)
    fails, real = H.scramble_pvalue(w, rb, n=200)
    results[name] = dict(sr=round(float(sr), 3), h1=round(float(h1), 2), h2=round(float(h2), 2),
                         neg_years=ny, worst_year=round(float(yearly.min()), 3),
                         scramble_fail_pct95=bool(fails), real_sr=round(float(real), 3),
                         corr_champ=round(float(H.corr_vs(net, CHAMP['ret'])), 3),
                         ann_vol=round(float(net.std() * np.sqrt(252)), 4))

# 2) BTC imb5_lvl depth (short-span flag)
bd = H.bookdepth("BTC")
sig = bd["imbalance_5pct"]
w = sig.clip(-1.0, 1.0).fillna(0.0)
net = H.run_signal(w, rb.reindex(w.index).fillna(0.0))
sr = H.sr(net); h1, h2 = H.halves_sr(net)
ny, yearly = H.neg_years(net)
fails, real = H.scramble_pvalue(w, rb.reindex(w.index).fillna(0.0), n=200)
results["BTC_depth_imb5_lvl_SHORTSPAN"] = dict(sr=round(float(sr), 3), h1=round(float(h1), 2), h2=round(float(h2), 2),
                                               neg_years=ny, worst_year=round(float(yearly.min()), 3),
                                               scramble_fail_pct95=bool(fails), real_sr=round(float(real), 3),
                                               corr_champ=round(float(H.corr_vs(net, CHAMP['ret'])), 3),
                                               ann_vol=round(float(net.std() * np.sqrt(252)), 4))

print(json.dumps(results, indent=1))
