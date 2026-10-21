"""RES_META Engine A screen: cross-asset short-horizon REVERSAL on 12 TRADEABLE legs.
Full turnover cost via meta_lib.sleeve_net (6.4bps full |dW| + borrow + margin)."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np, pandas as pd
import meta_lib as ML

R = pd.DataFrame({leg: ML.rets(ML.load_px(leg)) for leg in ML.universe()})
R = R.dropna(how="all")
Rc = R.apply(ML.clip_rets, cap=0.18)
print("panel:", R.shape, R.index.min().date(), "..", R.index.max().date())
champ = pd.read_csv("/Users/daxu/software/world-trader/campaign/results/"
                    "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    parse_dates=["date"]).set_index("date")["ret"]

rows = []
for L in (5, 8, 10, 13, 21):
    for n_leg in (2, 3):
        P = ML.reversal_positions(Rc, L=L, n_leg=n_leg)
        net = ML.sleeve_net(P, Rc)
        rep = ML.report_lite(net, champ)
        rows.append(dict(L=L, n_leg=n_leg, n=rep["n"], sr=rep["sr"], h1=rep["h1"],
                         h2=rep["h2"], neg=rep["neg"], worst=rep["worst"],
                         corr=rep["corr"], ann=rep["ann"]))
d = pd.DataFrame(rows).sort_values("sr", ascending=False)
pd.set_option("display.width", 200)
print(d.to_string(index=False))
d.to_csv(os.path.join(HERE, "screen_rev.csv"), index=False)
