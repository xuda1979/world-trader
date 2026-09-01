"""Idea 2: term-structure carry/trend, DV01-neutral curve books on synthetic TRs.
steepener ret = N_l*TR_long - N_s*TR_short with N_l*D_l = N_s*D_s (DV01-neutral);
carry of steepener = (N_l*y_l - N_s*y_s)/252 per unit DV01-pair (positive when short end yield-rich
in notional terms). Signals: (a) curve TREND (spread 63/126/252d change), (b) CARRY sign,
(c) trend AND carry>0 combo. Long/flat (LF) and L/S forms."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
import r7_lib as L

DUR = {"1": 0.98, "2": 1.9, "10": 7.5, "30": 19.0}
def tr_series(ten):
    y = L.fnew(f"DGS{ten}") / 100.0
    return (-DUR[ten] * y.diff() + y / 252.0), y

def book(pair, mode, k, cad):
    tl, yl = tr_series(pair[0]); ts, ys = tr_series(pair[1])
    cal = pd.bdate_range(max(tl.index[0], ts.index[0]), pd.Timestamp.today().normalize())
    tl = tl.reindex(cal).fillna(0.0); ts = ts.reindex(cal).fillna(0.0)
    yl = yl.reindex(cal).ffill(); ys = ys.reindex(cal).ffill()
    Dl, Ds = DUR[pair[0]], DUR[pair[1]]
    Nl, Ns = Ds / (Dl + Ds), Dl / (Dl + Ds)   # normalized DV01-neutral: Nl*Dl = Ns*Ds
    steep = Nl * tl - Ns * ts                  # steepener daily excess ret per 1 unit risk
    flat = -steep
    spread = (yl - ys)                         # curve slope (y_l - y_s), negative normally
    carry_st = (Nl * yl - Ns * ys) / 252.0     # steepener daily carry
    if mode == "trend":
        sig = np.sign((spread.diff(k)).rolling(1).mean())  # >0 = steepening over k days
        sig = pd.Series(np.where(spread.diff(k) > 0, 1, -1), index=cal)
    elif mode == "carry":
        sig = pd.Series(np.where(carry_st > 0, 1, -1), index=cal)
    elif mode == "trendcarry":
        tr_ = (spread.diff(k) > 0).astype(int) * 2 - 1
        cy = (carry_st > 0).astype(int) * 2 - 1
        sig = pd.Series(np.where((tr_ > 0) & (cy > 0), 1, np.where((tr_ < 0) & (cy < 0), -1, 0)), index=cal)
    W = L.freeze(pd.DataFrame({"b": sig * flat * 0 + sig * steep * 0 + sig}), cad)  # placeholder
    # honest: weights are +/-1 on the COMPOSITE steepener series
    Wc = L.freeze(pd.DataFrame({"b": sig}), cad)
    rets = pd.DataFrame({"b": sig * 0 + flat * 0 + steep})  # steepener return stream
    return Wc, rets

if __name__ == "__main__":
    print("=== IDEA 2: DV01-neutral curve books (eval 2007+, VT12, 6bps) ===")
    for pair in [("10", "2"), ("30", "10"), ("30", "2")]:
        for mode in ["trend", "carry", "trendcarry"]:
            for k in ([63, 126, 252] if mode != "carry" else [0]):
                for cad in [21, 63]:
                    W, rets = book(pair, mode, k, cad)
                    r, _ = L.from_W(W, rets, vt=0.12)
                    tag = f"{pair[1]}s{pair[0]}y {mode}" + (f" k{k}" if k else "    ") + f" cad{cad}"
                    L.report(r, tag)
