"""A6 r2 mission 1: faster regime exit for gated resid-mom.
Variants: VIX 21d-pct exit gate / 2-tier MA150+VIX veto / MA126 / DD-cautious re-entry."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from lib6 import closes, stats, halves_sr, vol_target
from idea234_engine import resid_momentum, weights_long, rets, px

FRED = "/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred"
vix = pd.read_csv(f"{FRED}/vix.csv", parse_dates=["date"], index_col="date")["value"]
vix = vix[~vix.index.duplicated(keep="last")].sort_index()
vix21p = vix.rolling(21).apply(lambda x: (x[-1] >= x).mean(), raw=True)  # trailing pct-rank incl today
vix63ma = vix.rolling(63, min_periods=40).mean()

_, resid_mom, _ = resid_momentum()
ok = rets.notna() & (px.notna().cumsum() >= 120)
W = weights_long(resid_mom, ok, frac=1/3, cadence=21)
mkt = px.mean(axis=1)

def ma_gate(ma_len=150, confirm=10, band=0.98, dd_len=252, dd_entry_confirm=None, dd_thresh=None):
    ma = mkt.rolling(ma_len, min_periods=ma_len//2).mean()
    above = (mkt > ma).values; below = (mkt < ma*band).values
    dd = (mkt / mkt.rolling(dd_len, min_periods=126).max() - 1.0).values
    n = len(mkt); state = np.zeros(n); s = 0; cnt = 0
    for i in range(n):
        if np.isnan(ma.iloc[i]): s = 0; cnt = 0; continue
        need = confirm
        if dd_entry_confirm is not None and s == 0 and not np.isnan(dd[i]) and dd[i] < dd_thresh:
            need = dd_entry_confirm   # deep-drawdown regime: demand longer re-entry confirmation
        if s == 1 and below[i]: s = 0; cnt = 0
        elif s == 0:
            cnt = cnt + 1 if above[i] else 0
            if cnt >= need: s = 1
        state[i] = s
    return pd.Series(state, index=mkt.index)

def vix_off(pct=0.70, confirm=1, use_level=False):
    trig = ((vix > vix63ma) if use_level else (vix21p > pct)).reindex(px.index).ffill().fillna(False).values
    n = len(trig); off = np.zeros(n); cnt = 0
    for i in range(n):
        cnt = cnt + 1 if trig[i] else 0
        off[i] = 1.0 if cnt >= confirm else 0.0
    return pd.Series(off, index=px.index)

def apply_veto(base, veto):
    b, v = base.values, veto.values
    out = np.zeros(len(b)); latch = 0
    for i in range(len(b)):
        if v[i] == 1: latch = 1
        if b[i] == 0: latch = 0
        out[i] = 0.0 if latch else b[i]
    return pd.Series(out, index=base.index)

def run(Wg, tag, vt=0.10, ret_out=False):
    gross = (Wg.shift(1) * rets).sum(axis=1)["2007-01-01":]
    turn = (Wg.shift(1) - Wg.shift(2)).abs().sum(axis=1)["2007-01-01":].fillna(0.0)
    net = gross - turn * 6 / 1e4
    if vt: net, _ = vol_target(net, vt)
    net = net.dropna()
    s = stats(net); h = halves_sr(net)
    yr = net.groupby(net.index.year).apply(lambda x: (1 + x).prod() - 1)
    g = lambda y: (yr.get(y, np.nan) * 100)
    print(f"{tag:44s} SR={s['sr']:.2f} ann={s['ann_ret']:5.1f}% H1={h['H1']:.2f} H2={h['H2']:.2f} "
          f"negYr={s['neg_years']} worst={s['worst_year']:6.1f}% 08={g(2008):6.1f} 15={g(2015):5.1f} 18={g(2018):5.1f} 22={g(2022):6.1f}")
    return net if ret_out else None

print("=== baseline & mission-1 variants (vol-target 10%) ===")
g0 = ma_gate(150, 10)
run(W.mul(g0, axis=0), "base MA150 c10 (r1 control)")
for mapl in [126, 150, 180]:
    run(W.mul(ma_gate(mapl, 10), axis=0), f"MA{mapl} c10")
run(W.mul(ma_gate(150, 5), axis=0), "MA150 c5 (faster both ways)")
# pure VIX exit gate (re-enter via same MA rule): vix-off acts as veto on MA150 gate
for pct in [0.60, 0.70, 0.80]:
    for cf in [1, 2]:
        run(W.mul(apply_veto(g0, vix_off(pct, cf)), axis=0), f"2tier MA150c10 + vix21p>{pct:.2f} cf{cf}")
run(W.mul(apply_veto(g0, vix_off(0.70, 1, use_level=True)), axis=0), "2tier MA150c10 + vix>vix63ma")
# pure vix gate without MA (entry still MA-gated): veto applied always (no reset needed) -> same as 2tier
# DD-cautious re-entry (kills Dec-2022 bear-rally trap)
for ddc, ddth in [(25, -0.12), (20, -0.15), (25, -0.15)]:
    run(W.mul(ma_gate(150, 10, dd_entry_confirm=ddc, dd_thresh=ddth), axis=0), f"MA150c10 + ddEntry({ddc}d,{ddth:.0%})")
run(W.mul(apply_veto(ma_gate(150, 10, dd_entry_confirm=25, dd_thresh=-0.12), vix_off(0.70, 1)), axis=0),
    "2tier vixp70 + ddEntry(25d,-12%)")
