"""A5 r7 idea 2: Rate-shock defensive tilts on DGS10 1990+.
A) Bond timing: long synth 7.5y TR when DGS10 below own MA (yield falling), flat else;
   grid MA {63,126,252,504} x hyst bps {0,5,10} — first honest test on 1990+ window
   (r5/r6 tested 2000+ only and found nothing).
B) Equity defensive tilt: SPY long only when 21d yield change z < th (rates not
   rising fast), else cash. Grid th."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
from a5_r7_lib import *

y10 = fred_new("DGS10"); y10.index = y10.index.tz_localize(None)
R_sp = spy93()

def synth(y, dur):
    y = y / 100.0
    return (dur * (-y.diff()) + y / 252.0).reindex(y.index)

# A) bond timing on synth TR, window 1990+ (also report 2000+ for honesty)
y_for_tr = y10[y10.index >= "1990-01-01"]
TR = synth(y_for_tr, 7.5)
rows = []
for ma in (63, 126, 252, 504):
    for hyst in (0.0, 0.05, 0.10, 0.25):
        m = y_for_tr.rolling(ma).mean()
        z = hysteresis_pos(-(y_for_tr - m), 0.0, hyst)  # long when yield<MA-hyst
        net, posf = build_net(z, TR.dropna())
        s = stats(net); h1, h2 = halves(net)
        rows.append(("A", ma, hyst, s["sr"], h1, h2, s["ann"], s["neg_yr"], s["worst"], s["n"], str(net.index[0].date())))
dfA = pd.DataFrame(rows, columns=["fam","ma","hyst","SR","H1","H2","ann","negyr","worst","n","start"]).sort_values("SR", ascending=False)
print("== A: bond timing DGS10 1990+ =="); print(dfA.to_string())

# 2000+ subset honesty check for best cell
def rerun_best(start):
    best = dfA.iloc[0]
    m = y_for_tr.rolling(int(best.ma)).mean()
    z = hysteresis_pos(-(y_for_tr - m), 0.0, best.hyst)
    TRs = synth(y_for_tr, 7.5).dropna()
    net, posf = build_net(z, TRs[TRs.index >= start])
    ok, line, s = gates_r7("r7i2A", net, posf, TRs[TRs.index >= start], extra=f"ma={best.ma} hyst={best.hyst} start={start}")
    print(line)
    ct, own = corr_all(net)
    print("corr lib:", ct)
rerun_best("2000-01-01")

# B) equity tilt: SPY long when 21d dY z < th
dy = y10.diff(21)
rows = []
for lb in (252, 504):
    z = ((dy - dy.rolling(lb).mean()) / dy.rolling(lb).std()).reindex(R_sp.index).ffill()
    for th in (-0.5, 0.0, 0.5, 1.0, 1.5, 99.0):
        p = (z < th).astype(float).where(~z.isna(), 0.0)
        net, posf = build_net(p, R_sp)
        s = stats(net); h1, h2 = halves(net)
        rows.append(("B", lb, th, s["sr"], h1, h2, s["ann"], s["neg_yr"], s["worst"]))
dfB = pd.DataFrame(rows, columns=["fam","lb","th","SR","H1","H2","ann","negyr","worst"]).sort_values("SR", ascending=False)
print("\n== B: equity tilt on 21d yield-change z =="); print(dfB.to_string())
