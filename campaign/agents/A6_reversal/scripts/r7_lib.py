"""A6 r7 shared: macro/data_fred_new loaders, single-calendar protocol (no axis bugs),
gates (brief a-g + charter corr<0.25), scramble via r6_lib (repriced costs+VT).
Convention (identical to r1-r6): W decided at t on data<=t, earns r_{t+1} via W.shift(1)*rets;
net = gross - 6bps*|dW| one-side; VT = expanding(60).std().shift(1) on net, target, cap 5."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from lib6 import stats, halves_sr
import r3_lib as R3, r6_lib as R6

ROOT = "/Users/daxu/software/world-trader"
FNEW = f"{ROOT}/tools/quant/hedge_fund_strats/data_fred_new"
FOLD = f"{ROOT}/tools/quant/hedge_fund_strats/data_fred"
START = "2007-01-01"

def _rd(path):
    df = pd.read_csv(path, index_col=0)
    df.index = pd.to_datetime(df.index)
    s = df["value"] if "value" in df.columns else df.iloc[:, 0]
    return s.astype(float)[~s.index.duplicated(keep="last")].sort_index()

def fnew(n): return _rd(f"{FNEW}/{n}.csv")
def fold(n): return _rd(f"{FOLD}/{n}.csv")

def bcal(*series):
    """common bday calendar from the latest series start; ffill each onto it (no lookahead: ffill)."""
    lo = max(s.index[0] for s in series)
    cal = pd.bdate_range(lo, pd.Timestamp.today().normalize())
    return [s.reindex(cal).ffill() for s in series]

def from_W(W, rets, start=START, vt=0.12, cap=5.0, cost=6.0):
    idx = rets.index
    W = W.reindex(idx).fillna(0.0)
    gross = (W.shift(1) * rets.fillna(0.0)).sum(axis=1)[start:]
    turn = (W.shift(1) - W.shift(2)).abs().sum(axis=1)[start:].fillna(0.0)
    net = (gross - turn * cost / 1e4)
    sd = net.expanding(60).std().shift(1)
    lev = (vt / np.sqrt(252) / sd).clip(0, cap).fillna(0.0)
    return (net * lev).dropna(), turn[turn > 0]

def report(r, tag):
    r = r.dropna()
    s = stats(r); h = halves_sr(r)
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    neg = {int(y): round(v * 100, 1) for y, v in yr.items() if v < 0}
    c6, c5 = R6.corr_to_champ(r)
    g = {"a_SR>=0.6": s["sr"] >= 0.6, "c_H1>=0.3": h["H1"] >= 0.3, "c_H2>=0.3": h["H2"] >= 0.3,
         "d_negYr<=2": s["neg_years"] <= 2, "d_worst>-5%": s["worst_year"] > -5.0,
         "corr<0.25": abs(c6) < 0.25}
    print(f"{tag:38s} SR={s['sr']:5.2f} ann={s['ann_ret']:5.1f}% vol={s['ann_vol']:4.1f}% "
          f"H1={h['H1']:.2f} H2={h['H2']:.2f} negYr={s['neg_years']}{neg} worst={s['worst_year']:5.1f}% "
          f"corr6={c6:+.2f} corr5={c5:+.2f} | fail={ [k for k,v in g.items() if not v] }")
    return dict(sr=s["sr"], ann=s["ann_ret"], vol=s["ann_vol"], h=h, neg=neg,
                worst=s["worst_year"], c6=c6, c5=c5, gates=g, yearly={int(k): v*100 for k, v in yr.items()})

def scramble(r, W, rets, n=200, seed=13, vt=0.12):
    Wr = W.reindex(rets.index).fillna(0.0)
    return R6.scramble_p(stats(r)["sr"], Wr, rets, start=START, n=n, seed=seed, vt_lvl=vt)

def freeze(W, cad):
    """freeze weights to a cadence grid (decisions every `cad` bdays), ffill between."""
    return W.iloc[::cad].reindex(W.index).ffill().fillna(0.0)
