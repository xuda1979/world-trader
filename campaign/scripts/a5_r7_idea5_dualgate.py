"""A5 r7 idea 5 (follow-through): fix r7i3-A's gate-d failure — AA/BBB synth
carry (tight-spread gate) AND DGS10 trend gate (flat when 10y above own MA =
rate sell-off). Economic story: IG carry accrues when credit calm; cut when
rates trending up (bond bear)."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
from a5_r7_lib import *

aaa = fred_new("DAAA"); baa = fred_new("DBAA"); y10 = fred_new("DGS10")
for s in (aaa, baa, y10): s.index = s.index.tz_localize(None)

def run(yc, dur, lb, th, hyst, ma_r, hyst_r, label):
    cr = pd.concat([yc, y10], axis=1, join="inner").ffill()
    spr = cr.iloc[:, 1] - cr.iloc[:, 0]
    y = cr.iloc[:, 0] / 100.0
    TR = (dur * (-y.diff()) + y / 252.0).dropna()
    z = ((spr - spr.rolling(lb).mean()) / spr.rolling(lb).std()).reindex(TR.index).ffill()
    p_tight = hysteresis_pos(z, th, hyst)
    yr_ = cr.iloc[:, 1].reindex(TR.index).ffill()
    m = yr_.rolling(ma_r).mean()
    p_rate = hysteresis_pos(-(yr_ - m), 0.0, hyst_r)  # long when yield < MA
    p = p_tight * p_rate
    net, posf = build_net(p, TR)
    s = stats(net); h1, h2 = halves(net)
    return net, posf, TR, s, h1, h2, p, p_tight, p_rate

rows = []
for dur, yn in ((7.0, "AAA"), (7.5, "BAA")):
    yc = aaa if yn == "AAA" else baa
    for lb in (252,):
        for th in (0.25, 0.5):
            for ma_r in (63, 126, 252, 504):
                for hyst_r in (0.0, 0.05, 0.10):
                    net, posf, TR, s, h1, h2, *_ = run(yc, dur, lb, th, 0.25, ma_r, hyst_r, "")
                    rows.append((yn, dur, lb, th, ma_r, hyst_r, s["sr"], h1, h2, s["ann"], s["neg_yr"], s["worst"]))
df = pd.DataFrame(rows, columns=["y","dur","lb","th","ma_r","hyst_r","SR","H1","H2","ann","negyr","worst"]).sort_values("SR", ascending=False)
print(df.to_string())
