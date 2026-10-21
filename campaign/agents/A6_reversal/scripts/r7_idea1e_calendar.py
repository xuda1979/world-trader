"""Idea 1e: calendar/effects forensics for the 2y trend sleeve.
A = saved (W reindexed to PANEL calendar, fillna(0) on FRED-missing days; eval on panel dates)
B = canonical (W ffilled on all bdays; eval on FRED bday calendar)
B' = B evaluated only on panel dates (isolate calendar effect)
A' = A on FRED calendar (isolate W-zero effect)"""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
import r7_lib as L
from lib6 import closes

DUR, K, CAD, VT, CAP = 1.9, 378, 42, 0.12, 5.0
y = L.fnew("DGS2") / 100.0
cal = pd.bdate_range(y.index[0], pd.Timestamp.today().normalize())
yf = y.reindex(cal).ffill()
tr_all = (-DUR * yf.diff() + yf / 252.0).fillna(0.0)
sig = (tr_all.rolling(K).mean() > 0).astype(float)
W_ffill = sig.iloc[::CAD].reindex(cal).ffill().fillna(0.0)

def evalseries(W, tr, idx):
    """generic: gross/turn/VT on given index set (idx = evaluation dates)."""
    W = W.reindex(idx).ffill()  # A-behavior = do NOT ffill -> use .reindex(idx).fillna(0)
    gross = (W.shift(1) * tr.reindex(idx).fillna(0.0))[L.START:]
    turn = (W.shift(1) - W.shift(2)).abs()[L.START:].fillna(0.0)
    net = (gross - turn * 6 / 1e4).dropna()
    sd = net.expanding(60).std().shift(1)
    lev = (VT / np.sqrt(252) / sd).clip(0, CAP).fillna(0.0)
    return (net * lev).dropna()

panel_idx = closes().index
def summ(r, tag):
    yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    neg = {int(k): round(v*100,1) for k,v in yr.items() if v<0}
    print(f"{tag:24s} SR={r.mean()/r.std()*np.sqrt(252):.2f} ann={r.mean()*252*100:5.1f}% negYr={len(neg)}{neg} worst={min(neg.values()) if neg else 0:.1f}%")

# A: W zero-filled (no ffill) on panel dates, eval panel
Wa = W_ffill.reindex(panel_idx).fillna(0.0)
grossA = (Wa.shift(1) * tr_all.reindex(panel_idx).fillna(0.0))[L.START:]
turnA = (Wa.shift(1) - Wa.shift(2)).abs()[L.START:].fillna(0.0)
netA = (grossA - turnA*6/1e4).dropna()
levA = (VT/np.sqrt(252)/netA.expanding(60).std().shift(1)).clip(0,CAP).fillna(0.0)
summ(netA*levA, "A saved-behavior")
# B: W ffilled, all bdays
grossB = (W_ffill.shift(1) * tr_all)[L.START:]
turnB = (W_ffill.shift(1) - W_ffill.shift(2)).abs()[L.START:].fillna(0.0)
netB = (grossB - turnB*6/1e4).dropna()
levB = (VT/np.sqrt(252)/netB.expanding(60).std().shift(1)).clip(0,CAP).fillna(0.0)
summ(netB*levB, "B canonical bdays")
# B': B restricted to panel dates
rB = netB*levB
summ(rB[rB.index.isin(panel_idx)], "B' on panel dates")
# A': A evaluated on bdays (W zero-filled at bdays = full anyway) -> equals B? W_ffill on bdays identical
print("note: A' == B on bday calendar by construction (W already ffilled)")
