"""Idea 2b: 2s10s carry book — LF form (flat when steepener-carry>0), static flattener control,
and sign diagnostics."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
import r7_lib as L

DUR = {"2": 1.9, "10": 7.5}
def book():
    y2 = L.fnew("DGS2") / 100.0; y10 = L.fnew("DGS10") / 100.0
    tr2 = (-DUR["2"] * y2.diff() + y2 / 252.0)
    tr10 = (-DUR["10"] * y10.diff() + y10 / 252.0)
    cal = pd.bdate_range(max(tr2.index[0], tr10.index[0]), pd.Timestamp.today().normalize())
    tr2 = tr2.reindex(cal).fillna(0.0); tr10 = tr10.reindex(cal).fillna(0.0)
    y2 = y2.reindex(cal).ffill(); y10 = y10.reindex(cal).ffill()
    Nl, Ns = DUR["2"] / (DUR["10"] + DUR["2"]), DUR["10"] / (DUR["10"] + DUR["2"])
    steep = Nl * tr10 - Ns * tr2               # steepener excess ret, DV01-neutral
    carry_st = (Nl * y10 - Ns * y2) / 252.0
    return steep, carry_st, cal

if __name__ == "__main__":
    steep, carry_st, cal = book()
    rets = pd.DataFrame({"b": steep})
    print(f"days steepener-carry>0: {(carry_st>0).mean():.2f}")
    print("=== variants ===")
    for tag, sig in [
        ("carry L/S (r7a best, cad63)", pd.Series(np.where(carry_st > 0, 1, -1), index=cal)),
        ("carry LF (flat when steep-carry>0)", pd.Series(np.where(carry_st > 0, 0, -1), index=cal)),
        ("STATIC flattener", pd.Series(-1.0, index=cal)),
        ("STATIC steepener", pd.Series(1.0, index=cal)),
    ]:
        W = L.freeze(pd.DataFrame({"b": sig}), 63)
        r, _ = L.from_W(W, rets, vt=0.12)
        L.report(r, tag)
