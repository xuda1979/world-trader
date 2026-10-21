"""A1 r3 FINAL: A1_carry_seasonal_v2 — SAVED sleeve. EW 1/3 of three near-orthogonal
macro premium books (crude-brent honest z-fade, natgas winter, gold carry-trend),
single trailing 8% book vol target. ALL GATES PASS (SR 0.82, 0 neg years, scramble p=0.0000).
NOTE: charter idea 1 (vol-of-vol seasoned CTA) FAILED gates -> not saved (see FINDINGS r3).
"""
import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
import numpy as np, pandas as pd
from data import fred, save_sleeve, COST

ROOT = "/Users/daxu/software/world-trader"

def bd(s):
    s = s.astype(float).dropna()
    s = s[~s.index.duplicated(keep="last")].sort_index()
    b = pd.bdate_range(s.index[0], s.index[-1])
    return s.reindex(b).ffill()

P = {"natgas": bd(fred("natgas")), "xau": bd(fred("xau"))}
R = {k: v.pct_change() for k, v in P.items()}
wti, br = bd(fred("wti")), bd(fred("brent"))
idx = wti.index
w = wti.reindex(idx); b = br.reindex(idx)
valid = w.notna() & b.notna()
w = w.where(valid).ffill(); b = b.where(valid).ffill()
bad = ((w < 5) | (b < 5)).fillna(True)          # Apr-2020 negative WTI print = unpriceable
spr = (w - b).mask(bad)
z = (spr - spr.rolling(126).mean()) / spr.rolling(126).std()
tb = bd(fred("tbill3m")).resample("D").ffill()

def vtclip(x, tgt, cap):
    v = x.expanding(min_periods=60).std().shift(1) * np.sqrt(252)
    return (x * (tgt / v).clip(0, cap)).fillna(0)

# ---- member 1: crude-brent spread z-fade (honest publication lag) ----
psp = np.sign(-z).where(z.abs() > 1.0, np.nan)
psp = psp.where(z.abs() > 0.75, 0).ffill().fillna(0).shift(1).fillna(0)  # decide at t from z(t-1) (public at t)
bm = bad | bad.shift(1).fillna(True)
psp = psp.where(~bm, 0.0)
fwd = (spr.diff() / w).shift(-1)                # earn spr(t+1)-spr(t) booked on decision row t
n1 = psp * fwd - psp.diff().abs().fillna(0) * 2 * COST / 1e4
n1 = vtclip(n1, 0.10, 3.0)
n1 = n1[n1.index >= "2008-01-03"]

# ---- member 2: natgas winter (long Nov-Feb, vol-sized, tbill accrual otherwise) ----
p2, r2 = P["natgas"], R["natgas"]
sig2 = pd.Series(0.0, index=p2.index); sig2[p2.index.month.isin([11, 12, 1, 2])] = 1.0
vol2 = r2.expanding(min_periods=60).std().shift(1) * np.sqrt(252)
w2 = (sig2 * (0.10 / vol2).clip(upper=1.0)).replace([np.inf, -np.inf], 0.0).fillna(0.0)
rf = (tb.reindex(r2.index).ffill().fillna(0) / 100.0 / 252.0)
n2 = ((w2.shift(1) * r2).fillna(0) + (1 - w2.shift(1).clip(0, 1)) * rf - w2.diff().abs().fillna(0) * COST / 1e4)
n2 = n2[n2.index >= "2008-01-03"]

# ---- member 3: gold carry-trend (252d & 84d trend gate, tbill accrual when flat) ----
p3, r3 = P["xau"], R["xau"]
sig3 = (p3 / p3.shift(252) - 1 > 0).astype(float) * (p3 / p3.shift(84) - 1 > 0).astype(float)
vol3 = r3.expanding(min_periods=60).std().shift(1) * np.sqrt(252)
w3 = (sig3 * (0.10 / vol3).clip(upper=1.0)).replace([np.inf, -np.inf], 0.0).fillna(0.0)
n3 = ((w3.shift(1) * r3).fillna(0) + (1 - w3.shift(1).clip(0, 1)) * rf - w3.diff().abs().fillna(0) * COST / 1e4)
n3 = n3[n3.index >= "2008-01-03"]

jj = pd.concat([n1, n2, n3], axis=1).sort_index().dropna()
m = jj.mean(axis=1)
rv = m.expanding(min_periods=60).std().shift(1) * np.sqrt(252)
sleeve = (m * (0.08 / rv).clip(0, 3)).fillna(0)

if __name__ == "__main__":
    yr = sleeve.groupby(sleeve.index.year).apply(lambda x: (1 + x).prod() - 1)
    print(f"SR={sleeve.mean()/sleeve.std()*252**0.5:.2f} vol={sleeve.std()*np.sqrt(252)*100:.1f}% "
          f"ann={sleeve.mean()*252*100:.1f}% negyr={int((yr<0).sum())}/{len(yr)}")
