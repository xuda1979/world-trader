"""Idea 3: cross-sectional commodity momentum, 6 assets (WTI, Brent, gold, silver, copper, natgas).
Long top-2 / short bottom-2 by trailing k-day momentum, EW within legs, cadence freeze 5/21,
VT12. Variants: LS, long-only-top2. Copper is monthly-ffilled (stale-but-known, flagged)."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
import r7_lib as L

ASSETS = {"WTI": ("fnew", "DCOILWTICO"), "Brent": ("fnew", "DCOILBRENTEU"),
          "gold": ("fold", "xau"), "silver": ("fold", "slv"),
          "copper": ("fold", "copper_monthly"), "natgas": ("fold", "natgas")}

def prices():
    ser = {}
    for nm, (src, f) in ASSETS.items():
        s = (L.fnew(f) if src == "fnew" else L.fold(f)).astype(float)
        ser[nm] = s[~s.index.duplicated(keep="last")].sort_index()
    cal = pd.bdate_range("2006-01-01", pd.Timestamp.today().normalize())
    px = pd.DataFrame({nm: s.reindex(cal).ffill() for nm, s in ser.items()}).dropna(how="all")
    return px

def book(px, k, ntop, cad, longonly=False):
    rets = px.pct_change(fill_method=None)
    mom = px.pct_change(k, fill_method=None)
    ranks = mom.rank(axis=1, ascending=False)
    n = px.shape[1]
    W = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    W[ranks <= ntop] = 1.0 / ntop
    if not longonly:
        W[ranks > n - ntop] = -1.0 / ntop
    W = L.freeze(W, cad)
    return W, rets

if __name__ == "__main__":
    px = prices()
    print("assets live:", px.apply(lambda c: c.first_valid_index()).to_dict())
    for k in [21, 63, 126, 252]:
        for cad in [5, 21]:
            W, rets = book(px, k, 2, cad)
            r, _ = L.from_W(W, rets, vt=0.12)
            L.report(r, f"xs-mom k{k} cad{cad} L/S top2/bot2")
    for k in [63, 126]:
        W, rets = book(px, k, 2, 21, longonly=True)
        r, _ = L.from_W(W, rets, vt=0.12)
        L.report(r, f"xs-mom k{k} cad21 LONG-ONLY top2")
    # control: single-asset time-series momentum pool (each asset +/- its own k-trend, risk-pared)
    print("--- TSMOM controls per asset (k63, LS, VT pooled EW) ---")
    rets = px.pct_change(fill_method=None)
    sig = pd.DataFrame(np.sign(rets.rolling(63).mean().values), px.index, px.columns)
    W = L.freeze(sig / 6.0, 21)
    r, _ = L.from_W(W, rets, vt=0.12)
    L.report(r, "TSMOM EW k63 (control)")
