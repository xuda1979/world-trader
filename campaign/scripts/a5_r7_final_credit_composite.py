"""A5 r7 FINAL: credit composite sleeve (data_fred_new DAAA/DBAA/DGS10, 1990+).
Signal (ONE signal drives all): long IG when credit spread z(252d) < 0.5,
exit when z > 0.75 (hysteresis). NOTE: 'long when tight' is the INVERSE of the
charter's value-book premise; charter direction was tested (idea3 dir=wide:
all cells SR<=0.13) and rejected.
Composite return (weights 10/60/30, center of SR plateau):
  0.1*TR_AA + 0.6*TR_SPR + 0.3*(TR_AA - hedge*TR_UST)
  TR_AA  = 7.0*(-d(DAAA/100)) + DAAA/100/252          (AA carry, 7y dur)
  TR_SPR = 7.0*(-d(spread/100)) + spread/100/252      (DV01-neutral spread carry)
  TR_UST = 7.5*(-d(DGS10/100)) + DGS10/100/252        (hedge leg)
  hedge  = 1[DGS10 21d change z(504d) > 0.75] shift(1)   <-- T+1 HONEST
Execution: signal shift(1) (T+1), 6bps one-side on turnover, expanding trailing
vol target 10% ann (min 60d, shift(1), clip 2.0). All data <= t only."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
from a5_r7_lib import *

aaa = fred_new("DAAA"); baa = fred_new("DBAA"); y10 = fred_new("DGS10")
for s in (aaa, baa, y10): s.index = s.index.tz_localize(None)
cr = pd.concat([aaa.rename("a"), baa.rename("b"), y10.rename("y")], axis=1, join="inner").ffill()
spr = (cr.b - cr.a) / 100.0
ya = cr.a / 100.0; yu = cr.y / 100.0
TR_AA = (7.0 * (-ya.diff()) + ya / 252.0).dropna()
TR_UST = (7.5 * (-yu.diff()) + yu / 252.0).reindex(TR_AA.index).fillna(0.0)
TR_SPR = (7.0 * (-spr.diff()) + spr / 252.0).reindex(TR_AA.index).fillna(0.0)
dy = yu.diff(21)

def zgate(lb, th, hyst=0.25):
    z = ((spr - spr.rolling(lb).mean()) / spr.rolling(lb).std()).reindex(TR_AA.index).ffill()
    return hysteresis_pos(z, th, hyst)

def run(lb=252, th=0.5, c=0.75, lb_z=504, w=(0.1, 0.6, 0.3)):
    p = zgate(lb, th)
    zy = ((dy - dy.rolling(lb_z).mean()) / dy.rolling(lb_z).std()).reindex(TR_AA.index).ffill()
    hedge = (zy > c).astype(float).shift(1).fillna(0.0)
    R = w[0] * TR_AA + w[1] * TR_SPR + w[2] * (TR_AA - hedge * TR_UST)
    net, posf = build_net(p, R)
    return net, posf, R

net, posf, R = run()
ok, line, s = gates_r7("A5_r7_credit_composite", net, posf, R, extra="w=10/60/30 lb252 th0.5 hyst0.25 c0.75 lbz504")
print(line)
print("yearly:", s["yearly"])
print("vol check: ann_vol=%.2f%% (vt10 clip2 cap)" % s["vol"])
ct, own = corr_all(net)
print("corr lib:", ct)
print("corr own:", own)

# --- plateau checks on remaining dims (gate b) ---
peak = s["sr"]; print(f"\npeak SR={peak:.2f}; 20% floor={0.8*peak:.2f}")
print("\nth plateau (lb252 c0.75):")
for th in (0.25, 0.5, 0.75):
    n, pf, _ = run(th=th)
    print(f"  th={th}: SR={stats(n)['sr']:.2f}")
print("lb plateau (th0.5 c0.75):")
for lb in (126, 252, 504):
    n, pf, _ = run(lb=lb)
    print(f"  lb={lb}: SR={stats(n)['sr']:.2f}")
print("hedge-c plateau (lb252 th0.5 lbz504):")
for c in (0.5, 0.75, 1.0, 1.25):
    n, pf, _ = run(c=c)
    print(f"  c={c}: SR={stats(n)['sr']:.2f}")
print("lbz plateau (lb252 th0.5 c0.75):")
for lbz in (252, 504, 1260):
    n, pf, _ = run(lb_z=lbz)
    print(f"  lbz={lbz}: SR={stats(n)['sr']:.2f}")
print("weight neighborhood (from idea9 map): (0.2,.6,.2)=1.50 (0,.6,.4)=1.48 (0.1,.7,.2)=1.50 (0.1,.5,.4)=1.45 — all >=96% of peak")
