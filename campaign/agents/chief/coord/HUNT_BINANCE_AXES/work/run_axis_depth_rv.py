"""HUNT_BINANCE_AXES axis 2: binance_bookdepth (microstructure) + axis 3: BTC-vs-ETH
cross-sectional RV. Pre-registered (CHARTER.md):
- depth: imbalance_1pct / imbalance_5pct levels + 21d z, 5d mean; depth-change momentum
  (total_notional_1pct 21/63d) both signs.
- RV: relative metric (BTC z minus ETH z) applied long-short BTC vs ETH, 21/63d.
T+1, 6.4bps, vol-target 10%. SHORT-SPAN honesty flag on depth (2023+).
"""
import hunt_lib as H
import pandas as pd, numpy as np, json

OUT = {}
CHAMP = H.load_csv('/Users/daxu/software/world-trader/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv')


def next_ret_from(px_close):
    return px_close.pct_change().shift(-1)


for asset in ("BTC", "ETH"):
    px = H.prices(asset)
    bd = H.bookdepth(asset)
    r = next_ret_from(px["close"])
    fams = {
        "imb1_lvl": bd["imbalance_1pct"],
        "imb1_z21": H.zscore(bd["imbalance_1pct"], 21),
        "imb5_lvl": bd["imbalance_5pct"],
        "imb5_z21": H.zscore(bd["imbalance_5pct"], 21),
        "depth_mom21": bd["total_notional_1pct"].pct_change(21),
        "depth_mom63": bd["total_notional_1pct"].pct_change(63),
    }
    for fname, s in fams.items():
        for dname in ("+", "-"):
            sig = s if dname == "+" else -s
            w = sig.clip(-1.0, 1.0).fillna(0.0)
            net = H.run_signal(w, r)
            srs = H.sr(net)
            h1, h2 = H.halves_sr(net)
            c = H.corr_vs(net, CHAMP["ret"])
            key = f"{asset}/depth/{fname}/{dname}"
            OUT[key] = {"sr": None if np.isnan(srs) else round(float(srs), 3),
                        "h1": None if np.isnan(h1) else round(float(h1), 2),
                        "h2": None if np.isnan(h2) else round(float(h2), 2),
                        "corr_champ": None if np.isnan(c) else round(float(c), 3),
                        "n": int((net != 0).sum())}

# ---- cross-sectional RV: relative metric -> long winner / short loser, beta-neutral 1:1 ----
pb, pe = H.prices("BTC")["close"], H.prices("ETH")["close"]
rb, re = next_ret_from(pb), next_ret_from(pe)
mb, me = H.metrics("BTC"), H.metrics("ETH")
for col in ("toptrader_ls_position_ratio", "global_ls_account_ratio", "taker_buy_sell_ratio"):
    for win in (21, 63):
        zb, ze = H.zscore(mb[col], win), H.zscore(me[col], win)
        rel = (zb - ze).dropna()
        idx = rel.index
        w_long_btc = rel.clip(-1, 1).reindex(idx).fillna(0.0)     # +rel -> long BTC
        w_eth = (-rel.clip(-1, 1)).reindex(idx).fillna(0.0)       # and short ETH
        netb = H.run_signal(w_long_btc, rb)
        nete = H.run_signal(w_eth, re)
        net = (netb + nete) / 2.0
        srs = H.sr(net)
        h1, h2 = H.halves_sr(net)
        c = H.corr_vs(net, CHAMP["ret"])
        key = f"RV/BTC-ETH/{col}/w{win}"
        OUT[key] = {"sr": None if np.isnan(srs) else round(float(srs), 3),
                    "h1": None if np.isnan(h1) else round(float(h1), 2),
                    "h2": None if np.isnan(h2) else round(float(h2), 2),
                    "corr_champ": None if np.isnan(c) else round(float(c), 3),
                    "n": int((net != 0).sum())}

print(json.dumps(OUT, indent=0))
