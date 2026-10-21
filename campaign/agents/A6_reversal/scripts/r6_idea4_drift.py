"""A6 r6 Idea 4 — Earnings-drift proxy: new 52w-high names x revenue growth (annual fundamentals).
PIT: fy data assumed public at Dec-31 of fy + 6 months (10-K filed 60-90d; 6mo = conservative).
Signal at month-end t: revgrowth(fy*) = rev[fy*]/rev[fy*-1]-1 (latest fy* public at t);
names with revgrowth > thr AND CR (=c/252d high) > 0.95. Long EW, monthly, T+1, 6bps, VT.
NOTE: fundamentals file = current constituents (survivorship risk flagged in report).
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
from r6_lib import closes, volumes, panel_hygiene, gate_report, scramble_p, START

FMP = "/Users/daxu/software/world-trader/alphaportfolio_replication/data/fundamentals_annual.parquet"
px = closes(); dv = volumes() * px
rets = px.pct_change(fill_method=None).clip(-0.5, 0.5)
ok = panel_hygiene(px, dv)
hi = px.rolling(252, min_periods=200).max()
CR = px / hi

fund = pd.read_parquet(FMP)
rev = fund[["symbol", "fy", "revenue"]].dropna()
rev = rev[rev.revenue > 0]
rev = rev.sort_values(["symbol", "fy"])
rev["g"] = rev.groupby("symbol")["revenue"].pct_change()
rev = rev.dropna(subset=["g"])
# public date = FY-end (assume Dec-31) + 182d
rev["pub"] = pd.to_datetime(rev["fy"].astype(int).astype(str) + "1231") + pd.Timedelta(days=182)
rev = rev.set_index("pub")

def revg_at(t):
    sub = rev[rev.index <= t]
    sub = sub[sub.symbol.isin(px.columns)]
    return sub.groupby("symbol")["g"].last()

def run(thr=0.10, crmin=0.95, frac_cap=40, gate="MA150", vt_lvl=0.15, use_fund=True, use_high=True):
    idx = rets.index
    W = pd.DataFrame(0.0, index=idx, columns=px.columns)
    mes = set(idx[idx.to_series().dt.is_month_end].dropna())
    mkt = px.mean(axis=1); ma = mkt.rolling(150, min_periods=75).mean()
    for t in sorted(mes):
        i = idx.get_loc(t)
        if i < 300: continue
        if gate == "MA150" and not (mkt.iloc[i] > ma.iloc[i]): continue
        elig = ok.iloc[i] & CR.iloc[i].notna()
        if use_high: elig &= (CR.iloc[i] > crmin)
        if use_fund:
            g = revg_at(t)
            elig = elig & pd.Series(False, index=px.columns)
            gg = g[g > thr]
            elig.loc[gg.index] = True
        names = [c for c in px.columns if bool(elig.get(c, False))]
        if len(names) < 5: continue
        if len(names) > frac_cap:
            # deepest liquidity among eligible
            names = dv.iloc[i][names].nlargest(frac_cap).index.tolist()
        n = len(names)
        for c in names: W.loc[t, c] = 1.0 / n
    gross = (W.shift(1) * rets).sum(axis=1)[START:]
    turn = (W.shift(1) - W.shift(2)).abs().sum(axis=1)[START:].fillna(0.0)
    net = (gross - turn * 6 / 1e4).dropna()
    sd = net.expanding(60).std().shift(1)
    lev = (vt_lvl / np.sqrt(252) / sd).clip(0, 5).fillna(0.0)
    return (net * lev).dropna(), W

if __name__ == "__main__":
    r, W = run()
    gate_report(r, "DRIFT g>10% & CR>0.95 cap40 MA150 VT15")
    r, W = run(thr=0.0)
    gate_report(r, "DRIFT g>0%  & CR>0.95 cap40 MA150 VT15")
    r, W = run(thr=0.20)
    gate_report(r, "DRIFT g>20% & CR>0.95 cap40 MA150 VT15")
    r, W = run(thr=0.10, gate="none")
    gate_report(r, "DRIFT g>10% & CR>0.95 cap40 no-gate VT15")
    r, W = run(use_high=False, thr=0.10)
    gate_report(r, "DRIFT g>10% only (no CR) cap40 MA150")
    r, W = run(use_fund=False)
    gate_report(r, "CTRL CR>0.95 only (no fund) cap40 MA150")
