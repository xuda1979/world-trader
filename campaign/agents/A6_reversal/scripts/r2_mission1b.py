"""A6 r2 mission 1b: dual-MA fast exit + no-latch VIX spike veto + continuous mkt-vol scaling."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from lib6 import closes, stats, halves_sr, vol_target
from idea234_engine import resid_momentum, weights_long, rets, px

FRED = "/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred"
vix = pd.read_csv(f"{FRED}/vix.csv", parse_dates=["date"], index_col="date")["value"]
vix = vix[~vix.index.duplicated(keep="last")].sort_index().reindex(px.index).ffill()
vix63ma = vix.rolling(63, min_periods=40).mean()

_, resid_mom, _ = resid_momentum()
ok = rets.notna() & (px.notna().cumsum() >= 120)
W = weights_long(resid_mom, ok, frac=1/3, cadence=21)
mkt = px.mean(axis=1)

def gate_dual(ma_len=150, confirm=10, exit_len=63, exit_band=0.99, dd_entry=None, dd_thresh=-0.15):
    """ON: after `confirm` days above MA(ma_len). OFF: close < exit_band*MA(exit_len) (fast exit).
    Optional dd_entry: in deep-DD regimes require `dd_entry` confirm days instead of `confirm`."""
    ma_s = mkt.rolling(ma_len, min_periods=ma_len//2).mean()
    ma_e = mkt.rolling(exit_len, min_periods=exit_len//2).mean()
    dd = (mkt / mkt.rolling(252, min_periods=126).max() - 1.0)
    above = (mkt > ma_s).values; ex = (mkt < exit_band * ma_e).values
    n = len(mkt); state = np.zeros(n); s = 0; cnt = 0
    for i in range(n):
        if np.isnan(ma_s.iloc[i]): continue
        need = confirm
        if dd_entry is not None and not np.isnan(dd.iloc[i]) and dd.iloc[i] < dd_thresh:
            need = dd_entry
        if s == 1 and ex[i]: s = 0; cnt = 0
        elif s == 0:
            cnt = cnt + 1 if above[i] else 0
            if cnt >= need: s = 1
        state[i] = s
    return pd.Series(state, index=mkt.index)

def run(Wg, tag, vt=0.10):
    gross = (Wg.shift(1) * rets).sum(axis=1)["2007-01-01":]
    turn = (Wg.shift(1) - Wg.shift(2)).abs().sum(axis=1)["2007-01-01":].fillna(0.0)
    net = gross - turn * 6 / 1e4
    if vt: net, _ = vol_target(net, vt)
    net = net.dropna(); s = stats(net); h = halves_sr(net)
    yr = net.groupby(net.index.year).apply(lambda x: (1 + x).prod() - 1)
    g = lambda y: yr.get(y, np.nan) * 100
    print(f"{tag:46s} SR={s['sr']:.2f} H1={h['H1']:.2f} H2={h['H2']:.2f} negYr={s['neg_years']} worst={s['worst_year']:6.1f}% 08={g(2008):6.1f} 15={g(2015):5.1f} 22={g(2022):6.1f}")
    return net

print("=== 1b: dual-MA fast exit ===")
for el in [40, 50, 63, 75, 100]:
    for eb in [0.99, 1.0]:
        run(W.mul(gate_dual(150, 10, el, eb), axis=0), f"MA150c10 exit MA{el}x{eb}")
print("=== 1b: fast exit + DD-cautious entry ===")
for el in [50, 63]:
    run(W.mul(gate_dual(150, 10, el, 0.99, dd_entry=20, dd_thresh=-0.15), axis=0), f"exit MA{el}x0.99 + ddEntry(20,-15%)")
print("=== 1b: no-latch VIX spike veto on base gate ===")
g0 = gate_dual(150, 10)
for mult in [1.2, 1.3, 1.5]:
    vok = (vix <= mult * vix63ma)
    run(W.mul(g0, axis=0).mul(vok.astype(float), axis=0), f"MA150c10 + vix<={mult}x vix63ma")
print("=== 1b: continuous mkt-vol scaling (trailing 63d, Moreira-Muir style) ===")
mvol = mkt.rolling(63, min_periods=40).std() * np.sqrt(252)
lev = (0.15 / mvol).clip(0, 1)  # full size if ann mkt vol <=15%, scale down above
run(W.mul(g0, axis=0).mul(lev, axis=0), "MA150c10 * mktvol scale (cap@15%)")
run(W.mul(g0, axis=0).mul(lev.clip(0.3, 1), axis=0), "MA150c10 * mktvol scale (floor 0.3)")
