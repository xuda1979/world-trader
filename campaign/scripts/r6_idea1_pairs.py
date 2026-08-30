"""A6 r6 Idea 1 — Pair-trading lite on twelve_big.
Top-40 same-cluster pairs (correlation clustering proxy for sector), 126d corr window,
refreshed monthly. Spread = log(p_i)-log(p_j); z = (spread - mean252)/std252 trailing.
Enter |z|>2, exit z crossing 0. Dollar-neutral, 6bps/side on turnover, T+1, VT10 expanding.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
from r6_lib import closes, volumes, panel_hygiene, gate_report, scramble_p, yearly, stats, halves_sr, vol_target, START

px = closes(); dv = volumes() * px
rets = px.pct_change(fill_method=None).clip(-0.5, 0.5)
ok = panel_hygiene(px, dv)
lpx = np.log(px)

def pick_pairs(t, topn=40, maxper=2):
    """greedy top-N pairs by 126d corr at date t among hygiene-OK names with full window."""
    i = rets.index.get_loc(t)
    if i < 130: return []
    w = rets.iloc[i-125:i+1]
    use = [c for c in w.columns
           if c in ok.columns and w[c].notna().sum() >= 100 and bool(ok.loc[t, c])]
    w = w[use]
    c = w.corr()
    pairs = []
    cnt = {n: 0 for n in use}
    # stack corr, exclude diagonal
    s = c.where(np.triu(np.ones(c.shape), 1).astype(bool)).stack().sort_values(ascending=False)
    for (a, b), v in s.items():
        if v < 0.6 or len(pairs) >= topn: break
        if cnt[a] >= maxper or cnt[b] >= maxper: continue
        pairs.append((a, b)); cnt[a] += 1; cnt[b] += 1
    return pairs

def run(topn=40, zentry=2.0, zexit=0.0, zwin=252, refresh="M", vt_lvl=0.10, verbose=False):
    idx = rets.index
    reb_dates = set(idx[idx.to_series().dt.is_month_end].dropna())
    if refresh == "W":
        reb_dates |= set(idx[idx.to_series().dt.dayofweek == 0].dropna())
    # state per pair
    pairs = []
    W = pd.DataFrame(0.0, index=idx, columns=px.columns)
    open_state = {}  # key -> +1/-1/0 dir
    cur_pairs = {}
    zcache = {}
    for t in idx:
        if t in reb_dates or t == idx[-1]:
            newp = pick_pairs(t, topn=topn)
            cur_pairs = {k: k for k in newp}
        # maintain z & state for current pairs
        i = idx.get_loc(t)
        active = {}
        for (a, b) in cur_pairs:
            j0 = max(0, i - zwin + 1)
            sa = lpx[a].iloc[j0:i+1]; sb = lpx[b].iloc[j0:i+1]
            sp = (sa - sb).dropna()
            if len(sp) < zwin // 2: continue
            m, sd = sp.mean(), sp.std()
            if not np.isfinite(sd) or sd < 1e-6: continue
            z = (sp.iloc[-1] - m) / sd
            key = (a, b)
            d = open_state.get(key, 0)
            if d == 0:
                if z < -zentry: d = +1     # spread low -> long a short b
                elif z > zentry: d = -1
            elif d == +1 and z >= zexit: d = 0
            elif d == -1 and z <= -zexit: d = 0
            open_state[key] = d
            if d != 0: active[key] = d
        if active:
            n = len(active)
            for (a, b), d in active.items():
                W.loc[t, a] += d / n; W.loc[t, b] -= d / n
        if verbose and t == idx[300]: pass
    gross = (W.shift(1) * rets).sum(axis=1)[START:]
    turn = (W.shift(1) - W.shift(2)).abs().sum(axis=1)[START:].fillna(0.0)
    net = (gross - turn * 6 / 1e4).dropna()
    lev = (vt_lvl / np.sqrt(252) / net.expanding(60).std().shift(1)).clip(0, 5).fillna(0.0)
    return net * lev, W

if __name__ == "__main__":
    for topn, zw in [(40, 252), (40, 126), (20, 252)]:
        r, W = run(topn=topn, zwin=zw)
        gate_report(r.dropna(), f"PAIRS top{topn} zwin{zw} z2/exit0 VT10")
    # turnover diagnostics
    r, W = run()
    print("mean daily one-side turnover bps:", (W.diff().abs().sum(axis=1).mean() * 1e4).round(1))
