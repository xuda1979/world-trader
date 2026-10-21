"""Idea 2c: bond-family blend 0.5*2y-trend + 0.5*2s10s-carryLF (both corr~0 to champion)."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
import r7_lib as L
DUR = {"2": 1.9, "10": 7.5}
def streams():
    y2 = L.fnew("DGS2") / 100.0; y10 = L.fnew("DGS10") / 100.0
    cal = pd.bdate_range("1989-12-29", pd.Timestamp.today().normalize())
    y2 = y2.reindex(cal).ffill(); y10 = y10.reindex(cal).ffill()
    tr2 = (-DUR["2"] * y2.diff() + y2 / 252.0).fillna(0.0)
    tr10 = (-DUR["10"] * y10.diff() + y10 / 252.0).fillna(0.0)
    # 2y trend LF k378 cad42
    sig2 = (tr2.rolling(378).mean() > 0).astype(float)
    W2 = L.freeze(pd.DataFrame({"b": sig2}), 42)
    r_trend, _ = L.from_W(W2, pd.DataFrame({"b": tr2}), vt=0.12)
    # 2s10s carry LF
    Nl, Ns = DUR["2"] / (DUR["10"] + DUR["2"]), DUR["10"] / (DUR["10"] + DUR["2"])
    steep = Nl * tr10 - Ns * tr2
    carry_st = (Nl * y10 - Ns * y2) / 252.0
    sigc = pd.Series(np.where(carry_st > 0, 0, -1.0), index=cal)
    Wc = L.freeze(pd.DataFrame({"b": sigc}), 63)
    r_carry, _ = L.from_W(Wc, pd.DataFrame({"b": steep}), vt=0.12)
    return r_trend, r_carry

rt, rc = streams()
df = pd.concat([rt, rc], axis=1, sort=True).fillna(0.0)
for w in [0.5, 0.6, 0.7]:
    rb = w * df.iloc[:, 0] + (1 - w) * df.iloc[:, 1]
    L.report(rb, f"blend {w:.1f} trend + {1-w:.1f} carry")
# also equal-risk: scale carry leg up to same realized vol as trend
sc = rt.std() / rc.std()
rb = 0.5 * df.iloc[:, 0] + 0.5 * df.iloc[:, 1] * sc
L.report(rb, f"blend 50/50 vol-matched (carry x{sc:.1f})")
