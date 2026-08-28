"""A6 r2 mission 1f: fast VETO overlays (no latch) on the ddEntry gate. Veto only exits; MA gate controls re-entry."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from lib6 import stats, halves_sr
from idea234_engine import resid_momentum, weights_long, rets, px

FRED = "/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred"
vix = pd.read_csv(f"{FRED}/vix.csv", parse_dates=["date"], index_col="date")["value"].reindex(px.index).ffill()
us10y = pd.read_csv(f"{FRED}/us10y.csv", parse_dates=["date"], index_col="date")["value"].reindex(px.index).ffill()

_, resid_mom, _ = resid_momentum()
ok = rets.notna() & (px.notna().cumsum() >= 120)
W = weights_long(resid_mom, ok, frac=1/3, cadence=21)
mkt = px.mean(axis=1)

def gate_dual(ma_len=150, confirm=10, dd_entry=20, dd_thresh=-0.15):
    ma_s = mkt.rolling(ma_len, min_periods=ma_len//2).mean()
    dd = (mkt / mkt.rolling(252, min_periods=126).max() - 1.0)
    above = (mkt > ma_s).values; below = (mkt < ma_s*0.98).values
    n = len(mkt); state = np.zeros(n); s = 0; cnt = 0
    for i in range(n):
        if np.isnan(ma_s.iloc[i]): continue
        need = dd_entry if (not np.isnan(dd.iloc[i]) and dd.iloc[i] < dd_thresh) else confirm
        if s == 1 and below[i]: s = 0; cnt = 0
        elif s == 0:
            cnt = cnt + 1 if above[i] else 0
            if cnt >= need: s = 1
        state[i] = s
    return pd.Series(state, index=mkt.index)

G = gate_dual()
breadth20 = (px > px.rolling(20).mean()).mean(axis=1)   # frac of names above MA20
low21 = mkt.rolling(21).min()
run_report = lambda net, tag: None
def report(net, tag):
    s = stats(net); h = halves_sr(net)
    yr = net.groupby(net.index.year).apply(lambda x: (1 + x).prod() - 1)
    neg = {int(k): round(v*100,1) for k,v in yr.items() if v < 0}
    okg = s['sr']>=0.6 and h['H1']>=0.3 and h['H2']>=0.3 and s['neg_years']<=2 and s['worst_year']>-5
    print(f"{tag:50s} SR={s['sr']:.2f} H1={h['H1']:.2f} H2={h['H2']:.2f} negYr={s['neg_years']}{neg} {'<<== GATES d+halves' if okg else ''}")
    return net

def backtest(lev_series, tag, vt=True):
    Wl = W.mul(G, axis=0).mul(lev_series.fillna(1.0), axis=0)
    gross = (Wl.shift(1)*rets).sum(axis=1)["2007-01-01":]
    turn = (Wl.shift(1)-Wl.shift(2)).abs().sum(axis=1)["2007-01-01":].fillna(0.0)
    raw = gross - turn*6/1e4
    net = raw.dropna()
    report(net, tag+" raw")
    # light VT at 15% to honor contract
    sd = net.expanding(60).std().shift(1)
    lev = (0.15/np.sqrt(252)/sd).clip(0, 1.5).fillna(0.0)
    report(net*lev, tag+" vt15cap1.5")

print("=== control ===")
backtest(pd.Series(1.0, index=px.index), "gate only")
print("=== 21d-low breakdown veto (fire on day, off when back above prev low) ===")
for nb in [1, 2, 3]:  # consecutive days below
    brk = (mkt < low21)
    v = pd.Series(np.where(brk.rolling(nb).sum() >= nb, 0.0, 1.0), index=px.index)
    backtest(v, f"low21 breakdown {nb}d confirm")
print("=== breadth veto: frac names above MA20 < th for 2d ===")
for th in [0.30, 0.35, 0.40]:
    v = pd.Series(np.where(breadth20 < th, 0.0, 1.0), index=px.index)
    backtest(v, f"breadth20<{th} (any day)")
print("=== MA20 fast-exit veto with 2% band ===")
ma20 = mkt.rolling(20, min_periods=10).mean()
v = pd.Series(np.where(mkt < ma20*0.98, 0.0, 1.0), index=px.index)
backtest(v, "mkt<MA20x0.98")
print("=== us10y shock veto: 21d yield rise > 40bps ===")
d10 = us10y - us10y.shift(21)
v = pd.Series(np.where(d10 > 0.40, 0.0, 1.0), index=px.index)
backtest(v, "us10y 21d delta>+40bp")
print("=== VIX level hard veto: vix>28 (any) ===")
v = pd.Series(np.where(vix > 28, 0.0, 1.0), index=px.index)
backtest(v, "vix>28")
