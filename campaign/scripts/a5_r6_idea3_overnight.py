"""A5 r6 idea3 (charter): overnight premium in SPX. Charter said 2016+-only unless
extendable — twelvedata SPY.csv has clean OHLC 2006-09..2026-08 (recon err ~0), so
full 20y window is testable. Sleeve: long close->open, flat intraday. T+1 n/a
(session split, no signal). Costs: 12bps round-trip per traded day. Gates r6."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import data as D
from a5_r6_lib import gates_r6

df = pd.read_csv("tools/quant/data/twelvedata/SPY.csv", index_col=0, parse_dates=True).sort_index()
o, c = df["open"], df["close"]
r_on  = (o / c.shift(1) - 1)            # overnight leg (hold from close to next open)
r_cc  = c.pct_change()
r_on = r_on.dropna(); r_cc = r_cc.reindex(r_on.index)

print("== cost arithmetic ==")
print(f"overnight mean {r_on.mean()*1e4:.2f} bp/d (ann {r_on.mean()*252*100:.1f}%), vol {r_on.std()*np.sqrt(252)*100:.1f}%, gross SR {(r_on.mean()/r_on.std()*np.sqrt(252)):.2f}")
print(f"round-trip cost 12bp/d = {0.0012*252*100:.1f}%/yr -> net mean {r_on.mean()*252*100 - 30.2:.1f}%/yr. DEAD at daily frequency.")

def net_of(sig, r):
    sig = sig.reindex(r.index).fillna(0.0).astype(float)
    p = sig.shift(1).fillna(0.0)
    to = p.diff().abs(); to.iloc[0] = abs(p.iloc[0])
    return (p * r.fillna(0.0) - to * D.COST / 1e4).dropna()

dow = pd.Series(r_on.index.dayofweek, index=r_on.index)
print("\n== conditional overnight means (bp/d) by weekday ==")
print((r_on.groupby(dow).mean()*1e4).round(2).to_string())

# variant A: always-on overnight (honest daily round trip)
netA = net_of(pd.Series(1.0, index=r_on.index), r_on)
ok, l = gates_r6("overnight always-on", netA); print(l)

# variant B: Monday-only overnight (LPS strongest day): 2 round trips/wk
sigB = (dow == 0).astype(float)
netB = net_of(sigB, r_on); ok, l = gates_r6("overnight Mon-only", netB, posf=sigB, R=r_on); print(l)

# variant C: only when overnight z (252d trailing mean) positive — trailing-only signal
mu = r_on.shift(1).rolling(252).mean(); sd = r_on.shift(1).rolling(252).std()
sigC = ((mu / sd) > 0).astype(float)
netC = net_of(sigC, r_on); ok, l = gates_r6("overnight trailing-z gate", netC, posf=sigC, R=r_on); print(l)

# variant D: vol-targeted always-on (same cost drag, report SR)
vol = netA.expanding(60).std(); sc = (0.10/np.sqrt(252)/vol).clip(0,2).shift(1).fillna(0.0)
netD = netA * sc
ok, l = gates_r6("overnight always-on vt10", netD, posf=sc, R=r_on); print(l)

# reference: what the intraday leg looks like (short intraday = short vol, ignore)
r_in = (c/o - 1).reindex(r_on.index)
print(f"\nref intraday mean {r_in.mean()*1e4:.2f} bp/d (ann {r_in.mean()*252*100:.1f}%)")
print(f"ref close-close mean {r_cc.mean()*1e4:.2f} bp/d")
