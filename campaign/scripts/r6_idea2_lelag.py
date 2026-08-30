"""A6 r6 Idea 2 — Lead-lag: mega-caps' 1d return -> small-cap next-day returns.
'Large' = top-50 by trailing 126d median dollar-vol; 'small' = bottom-50 of hygiene-OK names.
Long small-caps that follow positive-mega days (and skip/negative after negative-mega days),
weekly rebalance + daily overlay variants. T+1, 6bps, VT10 expanding.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
from r6_lib import closes, volumes, panel_hygiene, gate_report, START

px = closes(); dv = volumes() * px
rets = px.pct_change(fill_method=None).clip(-0.5, 0.5)
ok = panel_hygiene(px, dv)
dv_med = dv.rolling(126, min_periods=60).median()

# daily liquidity ranks (trailing only)
_rk = dv_med.rank(axis=1, ascending=False)
big = _rk <= 50
elig = ok & dv_med.notna()
small = _rk.gt(ok.notna().sum(axis=1) - 50, axis=0) & elig

# mega-cap market move at t (equal weight of big caps with data)
mret = rets.where(big).mean(axis=1)

def run(mode="longwin", hold=5, topq=0.5, vt_lvl=0.10):
    """Each day t: signal = mean mega return over (t-hold..t-1] (all known at t).
    If signal > 0: hold EW book of topq small caps (by dollar vol) else flat (longwin)
    or short their EW (both) / long the losers' side (reverse)."""
    sig = mret.rolling(hold, min_periods=1).sum()
    cols = px.columns
    W = pd.DataFrame(0.0, index=rets.index, columns=cols)
    cap = rets.notna().rolling(1).sum()
    for t in rets.index[126:]:
        s = sig.get(t, np.nan)
        if not np.isfinite(s): continue
        row_ok = ok.loc[t]
        scr = small.loc[t] if isinstance(small.loc[t], pd.Series) else small.loc[t]
        # score small caps: default = liquidity rank (deepest names)
        cand = [c for c in cols if scr.get(c, False)]
        if not cand: continue
        liq = dv_med.loc[t, cand].fillna(0.0)
        k = max(5, int(len(cand) * topq))
        picks = liq.sort_values(ascending=False).index[:k]
        if mode == "longwin":
            d = 1.0 if s > 0 else 0.0
        elif mode == "both":
            d = 1.0 if s > 0 else -1.0
        else:  # reverse
            d = -1.0 if s > 0 else 0.0
        if d == 0: continue
        for c in picks:
            W.loc[t, c] = d / len(picks)
    gross = (W.shift(1) * rets).sum(axis=1)[START:]
    turn = (W.shift(1) - W.shift(2)).abs().sum(axis=1)[START:].fillna(0.0)
    net = (gross - turn * 6 / 1e4).dropna()
    sd = net.expanding(60).std().shift(1)
    lev = (vt_lvl / np.sqrt(252) / sd).clip(0, 5).fillna(0.0)
    return (net * lev).dropna(), W

if __name__ == "__main__":
    for mode in ["longwin", "both", "reverse"]:
        for hold in [1, 5]:
            r, W = run(mode=mode, hold=hold)
            gate_report(r, f"LEADLAG {mode} hold{hold}")
