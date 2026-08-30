"""Charter 5: 2s10s steepener/flattener z-book. DV01-neutral synth: pos w in UST10-TR,
-h*w*dur10/dur2 in UST2-TR (or the reverse). Signal = z of curve level (fade) or curve momentum.
Costs billed on BOTH legs' turnover. vt15 documented."""
import sys; sys.path.insert(0, __file__.rsplit("/",1)[0])
from r4_lib import *
from a2_lib import _bday
from a2_lib import px_series

U2 = px_series("UST2"); U10 = px_series("UST10")
curve = fred("t10y2y")
curve_d = _bday(curve)
D2, D10 = 1.8, 7.5
h = D10 / D2  # 2y units per 1y unit for DV01 neutrality

def spread_sleeve(pos10, vt=0.15):
    """pos10: +1 = long UST10 TR + DV01-neutral SHORT UST2 TR (flattener bet: long duration).
       pos10 negative = steepener."""
    idx = U10.index.intersection(U2.index)
    p10 = pos10.reindex(idx).ffill().fillna(0.0)
    p2 = -h * p10
    fr10 = U10.reindex(idx).pct_change().shift(-1)
    fr2 = U2.reindex(idx).pct_change().shift(-1)
    gross = (p10 * fr10 + p2 * fr2).dropna()
    to = (p10.diff().abs() + p2.diff().abs()).fillna(0).reindex(gross.index).fillna(0)
    net = cost(gross, to)
    return net, vol_target(net, vt).dropna()

z = (curve_d - curve_d.rolling(756).mean()) / curve_d.rolling(756).std()
z = z.clip(-2, 2)
mom63 = curve_d / curve_d.shift(63) - 1.0
mom252 = curve_d / curve_d.shift(252) - 1.0

variants = {
  "fade-z756-b1": -np.sign(z).where(z.abs() >= 1.0, 0.0),
  "fade-z756-band": (-z).clip(-1, 1),
  "mom63-ls": np.sign(mom63),
  "mom252-ls": np.sign(mom252),
  "flat-always": pd.Series(1.0, index=curve_d.index),
  "steep-always": pd.Series(-1.0, index=curve_d.index),
}
for nm, pos in variants.items():
    net, netvt = spread_sleeve(pos)
    g = full_gates(netvt); c, n = corr_to_champ(netvt)
    pr(f"2s10s-{nm}-vt15", g, c, f"n={n}")
