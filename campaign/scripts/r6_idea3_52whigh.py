"""A6 r6 Idea 3 — 52-week-high momentum (r1 idea 5, never fully worked).
Signal at t: CR = close_t / 252d-max_close (trailing); trade top tercile, long-only,
MA150 market gate, VT15, T+1, 6bps. Monthly + weekly cadence.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
from r6_lib import closes, volumes, panel_hygiene, gate_report, scramble_p, START

px = closes(); dv = volumes() * px
rets = px.pct_change(fill_method=None).clip(-0.5, 0.5)
ok = panel_hygiene(px, dv)
hi = px.rolling(252, min_periods=200).max()
CR = px / hi
mom = px.pct_change(126, fill_method=None)

def run(k=3, frac=1/3, cad=21, gate="MA150", vt_lvl=0.15, wmode="ew"):
    idx = rets.index
    W = pd.DataFrame(0.0, index=idx, columns=px.columns)
    mes = set(idx[idx.to_series().dt.is_month_end].dropna())
    if cad == 5:
        mes |= set(idx[idx.to_series().dt.dayofweek == 4].dropna())
    mkt = px.mean(axis=1)
    ma = mkt.rolling(150, min_periods=75).mean()
    for t in idx:
        if t not in mes and t != idx[-1]: continue
        i = idx.get_loc(t)
        if i < 300: continue
        if gate == "MA150" and not (mkt.iloc[i] > ma.iloc[i]):
            continue
        cr = CR.iloc[i]; eligible = ok.iloc[i] & cr.notna() & mom.iloc[i].notna()
        names = [c for c in px.columns if bool(eligible.get(c, False))]
        if len(names) < 20: continue
        ser = cr[names]
        n = max(5, int(round(len(names) * frac)))
        picks = ser[names].nlargest(n).index
        if wmode == "ivw":
            v = rets[picks].iloc[i-62:i+1].std().clip(1e-4)
            wgt = (1 / v); wgt = wgt / wgt.sum()
        else:
            wgt = pd.Series(1.0 / n, index=picks)
        for c in picks: W.loc[t, c] = wgt[c]
    gross = (W.shift(1) * rets).sum(axis=1)[START:]
    turn = (W.shift(1) - W.shift(2)).abs().sum(axis=1)[START:].fillna(0.0)
    net = (gross - turn * 6 / 1e4).dropna()
    sd = net.expanding(60).std().shift(1)
    lev = (vt_lvl / np.sqrt(252) / sd).clip(0, 5).fillna(0.0)
    return (net * lev).dropna(), W

if __name__ == "__main__":
    for cad in [21, 5]:
        for wm in ["ew", "ivw"]:
            r, W = run(cad=cad, wmode=wm)
            gate_report(r, f"52WH cad{cad} {wm} frac1/3 MA150 VT15")
    r, W = run()
    print("turnover bps/day:", (W.diff().abs().sum(axis=1).mean() * 1e4).round(1))
