"""A6 r2 mission 1c: combine ddEntry + market-vol scaling; grid cap/floor. Target negYr<=2, 2022>-5%, SR>=0.9."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from lib6 import closes, stats, halves_sr, vol_target
from idea234_engine import resid_momentum, weights_long, rets, px

FRED = "/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred"
vix = pd.read_csv(f"{FRED}/vix.csv", parse_dates=["date"], index_col="date")["value"]
vix = vix[~vix.index.duplicated(keep="last")].sort_index().reindex(px.index).ffill()
vix21p = vix.rolling(21).apply(lambda x: (x[-1] >= x).mean(), raw=True)

_, resid_mom, _ = resid_momentum()
ok = rets.notna() & (px.notna().cumsum() >= 120)
W = weights_long(resid_mom, ok, frac=1/3, cadence=21)
mkt = px.mean(axis=1)

def gate_dual(ma_len=150, confirm=10, dd_entry=None, dd_thresh=-0.15):
    ma_s = mkt.rolling(ma_len, min_periods=ma_len//2).mean()
    above = (mkt > ma_s).values; below = (mkt < ma_s*0.98).values
    dd = (mkt / mkt.rolling(252, min_periods=126).max() - 1.0)
    n = len(mkt); state = np.zeros(n); s = 0; cnt = 0
    for i in range(n):
        if np.isnan(ma_s.iloc[i]): continue
        need = dd_entry if (dd_entry is not None and not np.isnan(dd.iloc[i]) and dd.iloc[i] < dd_thresh) else confirm
        if s == 1 and below[i]: s = 0; cnt = 0
        elif s == 0:
            cnt = cnt + 1 if above[i] else 0
            if cnt >= need: s = 1
        state[i] = s
    return pd.Series(state, index=mkt.index)

g = gate_dual(150, 10, dd_entry=20, dd_thresh=-0.15)
mvol = mkt.rolling(63, min_periods=40).std() * np.sqrt(252)

def run(Wg, tag, vt=0.10, quiet=False):
    gross = (Wg.shift(1) * rets).sum(axis=1)["2007-01-01":]
    turn = (Wg.shift(1) - Wg.shift(2)).abs().sum(axis=1)["2007-01-01":].fillna(0.0)
    net = gross - turn * 6 / 1e4
    if vt: net, _ = vol_target(net, vt)
    net = net.dropna(); s = stats(net); h = halves_sr(net)
    yr = net.groupby(net.index.year).apply(lambda x: (1 + x).prod() - 1)
    neg = {int(k): round(v*100,1) for k,v in yr.items() if v < 0}
    okgate = s['sr']>=0.6 and h['H1']>=0.3 and h['H2']>=0.3 and s['neg_years']<=2 and s['worst_year']>-5
    print(f"{tag:44s} SR={s['sr']:.2f} H1={h['H1']:.2f} H2={h['H2']:.2f} negYr={s['neg_years']}{neg} {'PASS(d+halves+full)' if okgate else ''}")
    return net

print("=== mktvol scale grid on gated sleeve (ddEntry 20/-15%) ===")
for cap in [0.15, 0.18, 0.20, 0.22, 0.25, 0.30]:
    for fl in [1.0, 0.6, 0.4]:
        lev = (cap / mvol).clip(0, fl)
        run(W.mul(g, axis=0).mul(lev, axis=0), f"ddE20 cap{cap:.0%} floor{fl if fl<1 else 'none'}")
print("=== same but VIX-based scaling ===")
for cap in [0.20, 0.25]:
    lev = (cap / (vix/100)).clip(0, 1.0)
    run(W.mul(g, axis=0).mul(lev, axis=0), f"vixScale cap{cap:.0%}")
print("=== vix21p>0.95 hard spike veto (no latch, event-level) ===")
for th in [0.95, 0.98]:
    vok = (vix21p <= th).astype(float)
    run(W.mul(g, axis=0).mul(vok, axis=0), f"vix21p<={th} veto")
