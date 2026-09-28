"""HUNT_BINANCE_AXES axis 1: binance_metrics (positioning + taker flow).
Pre-registered families (CHARTER.md): z-fade and z-mom of toptrader_ls_position_ratio,
global_ls_account_ratio, taker_buy_sell_ratio at 21/63d, sign both ways; oi and oi_value
change momentum (21/63d) both ways. T+1, 6.4bps, vol-target 10%, scramble 200x on finalists.
"""
import hunt_lib as H
import pandas as pd, numpy as np, json

OUT = {}
CHAMP = H.load_csv('/Users/daxu/software/world-trader/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv')


def next_ret_from(px_close):
    return px_close.pct_change().shift(-1)   # ret t->t+1, aligned at t


for asset in ("BTC", "ETH"):
    px = H.prices(asset)
    me = H.metrics(asset)
    r = next_ret_from(px["close"])
    fams = {
        "tt_pos": me["toptrader_ls_position_ratio"],
        "glob_ls": me["global_ls_account_ratio"],
        "taker": me["taker_buy_sell_ratio"],
        "oi_chg": me["oi"].pct_change(),
        "oival_chg": me["oi_value"].pct_change(),
    }
    for fname, s in fams.items():
        for win in (21, 63):
            z = H.zscore(s, win)
            for dname, sig in (("+mom", z), ("-fade", -z)):
                w = (sig.clip(-1.0, 1.0)).fillna(0.0)
                net = H.run_signal(w, r)
                srs = H.sr(net)
                h1, h2 = H.halves_sr(net)
                c = H.corr_vs(net, CHAMP["ret"])
                key = f"{asset}/{fname}/w{win}/{dname}"
                OUT[key] = {"sr": None if np.isnan(srs) else round(float(srs), 3),
                            "h1": None if np.isnan(h1) else round(float(h1), 2),
                            "h2": None if np.isnan(h2) else round(float(h2), 2),
                            "corr_champ": None if np.isnan(c) else round(float(c), 3),
                            "n": int((net != 0).sum())}

print(json.dumps(OUT, indent=0))
