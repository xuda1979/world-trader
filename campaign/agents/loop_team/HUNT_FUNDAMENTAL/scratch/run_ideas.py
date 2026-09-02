"""HUNT_FUNDAMENTAL idea runner: value/growth/profitability screens from
fundamentals_annual.parquet on the twelve_extend daily panel (true daily hold)."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
from hf_engine import *
import numpy as np, pandas as pd

px, rets = load_panel()
print("panel:", px.shape, px.index.min().date(), px.index.max().date())

def wins(x, lo=0.01, hi=0.99):
    q1, q2 = x.quantile(lo), x.quantile(hi)
    return x.clip(q1, q2)

def zscore(f, col):
    x = f.groupby("fy")[col].transform(lambda s: (s - s.median()) / (s.std() if s.std() and s.std() > 0 else 1.0))
    return wins(x)

IDEAS = {}

# --- Idea 1: VALUE composite ---
# E/B = net_income/equity ; OI/IC = op_income/(equity+debt-cash) ; S/TA = revenue/total_assets
def score_value(f):
    eb = f.net_income / f.equity.replace(0, np.nan)
    ic = (f.equity + f.debt - f.cash).where(lambda s: s > 0)
    oic = f.op_income / ic
    sta = f.revenue / f.total_assets.where(lambda s: s > 0)
    df = pd.DataFrame({"eb": eb, "oic": oic, "sta": sta})
    out = pd.Series(np.nan, index=f.index)
    # winsorize+standardize each leg cross-sectionally within fy
    for c in df.columns:
        x = df[c].copy()
        grp = f["fy"]
        med = x.groupby(grp).transform("median")
        sd = x.groupby(grp).transform(lambda s: s.std())
        zx = ((x - med) / sd.where(sd > 0)).clip(-3, 3)
        out = out.add(zx, fill_value=0)
        # count legs
    nlegs = df.notna().sum(axis=1)
    out = out / nlegs.where(nlegs > 0)
    return out.where(nlegs > 0)
IDEAS["value_comp"] = (score_value, 1/3, 1/3, 2.0)

# --- Idea 2: GROWTH (1y change scaled by assets) ---
def score_growth(f):
    f2 = f.sort_values(["symbol", "fy"]).copy()
    g2 = f2.groupby("symbol")
    d_rev = (f2.revenue - g2.revenue.shift(1)) / f2.total_assets.where(lambda s: s > 0)
    d_oi = (f2.op_income - g2.op_income.shift(1)) / f2.total_assets.where(lambda s: s > 0)
    df = pd.DataFrame({"d_rev": d_rev, "d_oi": d_oi})
    out = pd.Series(np.nan, index=f2.index)
    for c in df.columns:
        x = df[c]
        med = x.groupby(f2["fy"]).transform("median")
        sd = x.groupby(f2["fy"]).transform(lambda s: s.std())
        zx = ((x - med) / sd.where(sd > 0)).clip(-3, 3)
        out = out.add(zx, fill_value=0)
    nlegs = df.notna().sum(axis=1)
    return (out / nlegs.where(nlegs > 0)).where(nlegs > 0)
IDEAS["growth_comp"] = (score_growth, 1/3, 1/3, 2.0)

# --- Idea 3: PROFITABILITY composite (op/TA, NI/TA, (rev-cogs)/TA where avail) ---
def score_prof(f):
    oi = f.op_income / f.total_assets.where(lambda s: s > 0)
    ni = f.net_income / f.total_assets.where(lambda s: s > 0)
    gp = (f.revenue - f.cogs) / f.total_assets.where(lambda s: s > 0)
    df = pd.DataFrame({"oi": oi, "ni": ni, "gp": gp})
    out = pd.Series(np.nan, index=f.index)
    for c in df.columns:
        x = df[c]
        med = x.groupby(f["fy"]).transform("median")
        sd = x.groupby(f["fy"]).transform(lambda s: s.std())
        zx = ((x - med) / sd.where(sd > 0)).clip(-3, 3)
        out = out.add(zx, fill_value=0)
    nlegs = df.notna().sum(axis=1)
    return (out / nlegs.where(nlegs > 0)).where(nlegs > 0)
IDEAS["prof_comp"] = (score_prof, 1/3, 1/3, 2.0)

# --- Idea 4: COMPOSITE all three ---
def score_all(f):
    v = score_value(f); g = score_growth(f.sort_values(["symbol", "fy"])); p = score_prof(f)
    v = v.reindex(f.index); p = p.reindex(f.index)
    g = pd.Series(g.values, index=f.sort_values(["symbol","fy"]).index).reindex(f.index)
    df = pd.DataFrame({"v": v, "g": g, "p": p})
    out = pd.Series(0.0, index=f.index)
    nlegs = df.notna().sum(axis=1).where(lambda s: s > 0)
    for c in df.columns:
        out = out.add(df[c].fillna(0) / nlegs)
    return out.where(nlegs.notna())
IDEAS["comp_vgp"] = (score_all, 1/3, 1/3, 2.0)

# --- Idea 5: VALUE quartiles 30/30 (more extreme) ---
IDEAS["value_q3030"] = (score_value, 0.3, 0.3, 2.0)

results = {}
for name, (fn, lf, sf, lev) in IDEAS.items():
    try:
        sig = build_signal(px, fn)
        n_cov = sig.notna().any(axis=1).sum()
        net, w, turn = backtest(sig, rets, lf, sf, lev)
        r = vol_target(net).iloc[5:].dropna()
        ok, g = full_gates(r, name)
        fg = flatten_gate(r)
        print(f"   {name}: cov_days={n_cov} turnover_bps/d={turn.mean()*6:.2f} flatten={fg}")
        results[name] = (ok, g, fg, r, sig)
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"   {name}: ERROR {e}")
