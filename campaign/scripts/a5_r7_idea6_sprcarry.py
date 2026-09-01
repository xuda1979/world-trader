"""A5 r7 idea 6: DV01-neutral IG spread carry 1990+ (DAAA-DBAA).
TR = dur*(-d(spread)) + spread/252 -> pure credit carry, zero rate beta.
Gate: tight-spread z hysteresis (r7i3-A winner direction, honestly noted as
inverse of charter). Grid lb x th x hyst for plateau."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
from a5_r7_lib import *

aaa = fred_new("DAAA"); baa = fred_new("DBAA")
for s in (aaa, baa): s.index = s.index.tz_localize(None)
cr = pd.concat([aaa.rename("a"), baa.rename("b")], axis=1, join="inner").ffill()
spr = (cr.b - cr.a) / 100.0
DUR = 7.0
TR = (DUR * (-spr.diff()) + spr / 252.0).dropna()
print(f"pure spread TR: mean={TR.mean()*252*100:.2f}%/yr vol={TR.std()*np.sqrt(252)*100:.2f}% n={len(TR)}")

rows = []
for lb in (126, 252, 504, 1260):
    z = ((spr - spr.rolling(lb).mean()) / spr.rolling(lb).std()).reindex(TR.index).ffill()
    for th in (-0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0):
        for hyst in (0.1, 0.25):
            p = hysteresis_pos(z, th, hyst)
            net, posf = build_net(p, TR)
            s = stats(net); h1, h2 = halves(net)
            rows.append((lb, th, hyst, s["sr"], h1, h2, s["ann"], s["neg_yr"], s["worst"], s["vol"]))
df = pd.DataFrame(rows, columns=["lb","th","hyst","SR","H1","H2","ann","negyr","worst","vol"]).sort_values("SR", ascending=False)
print(df.head(20).to_string())
print("...")
print(df.tail(6).to_string())

# always-long reference + best-cell detail
net0, _ = build_net(pd.Series(1.0, index=TR.index), TR)
s0 = stats(net0); h1, h2 = halves(net0)
print(f"\nalways-long: SR={s0['sr']:.2f} ann={s0['ann']:.2f}% H1={h1:.2f} H2={h2:.2f} negyr={s0['neg_yr']}/{s0['n_yr']} worst={s0['worst']:.1f}%")
b = df.iloc[0]
z = ((spr - spr.rolling(int(b.lb)).mean()) / spr.rolling(int(b.lb)).std()).reindex(TR.index).ffill()
p = hysteresis_pos(z, b.th, b.hyst)
net, posf = build_net(p, TR)
ok, line, s = gates_r7("r7i6", net, posf, TR, extra=f"lb={int(b.lb)} th={b.th} hyst={b.hyst}")
print(line); print("yearly:", s["yearly"])
ct, own = corr_all(net)
print("corr lib:", ct); print("corr own:", own)
