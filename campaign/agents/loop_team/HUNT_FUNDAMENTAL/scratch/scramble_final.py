"""Scramble test (200x) for HF_mom_cheap: permute fundamentals-filter link (keep mom panel)
and permute mom xs (keep filter) — decompose. Also full-destroy permutation."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
from hf_engine import *
from run_ideas2_lib import (px, F, sigv, sigp, month_ends)
import numpy as np, pandas as pd

rets_raw = px.pct_change(fill_method=None)
rets_w = rets_raw.clip(-0.5, 0.5)
bad25 = (rets_raw.abs() > 0.25)
bad_tr = bad25.rolling(504, min_periods=1).max().shift(1).fillna(0.0)
idx = px.index
mes = [pd.Timestamp(d) for d in month_ends(idx)]

def run(sigframe_or_none, perm_mode, seed):
    """perm_mode: 'mom' permute momentum cross-section; 'filter' permute value filter xs;
       'both' permute both."""
    rng = np.random.default_rng(seed)
    srs = []
    for rep in range(200):
        mom_p = (px.shift(21)/px.shift(252)-1).clip(-0.95, 3.0)
        val = sigv
        if perm_mode in ("mom", "both"):
            vals = mom_p.values.copy(); mask = ~np.isnan(vals)
            flat = vals[mask]
            rng.shuffle(flat)
            p2 = np.full_like(vals, np.nan); p2[mask] = flat
            mom_p = pd.DataFrame(p2, index=idx, columns=px.columns)
        if perm_mode in ("filter", "both"):
            v = val.values.copy(); mask = ~np.isnan(v)
            flat = v[mask]; rng.shuffle(flat)
            p3 = np.full_like(v, np.nan); p3[mask] = flat
            val = pd.DataFrame(p3, index=idx, columns=px.columns)
        rs = []
        for k, t in enumerate(mes):
            m = mom_p.loc[t]
            v = val.loc[t].dropna()
            if len(v) >= 20:
                m = m.where(v.le(v.quantile(0.5)).reindex(px.columns).fillna(False))
            row = m.dropna()
            row = row[~bad_tr.loc[t].astype(bool).reindex(row.index).fillna(False)]
            srs_rep = None
            if len(row) >= 10:
                rsl = row.sort_values(); nl = max(int(np.floor(len(rsl)/2)),1)
                pick = rsl.index[-nl:]
                nxt = mes[k+1] if k+1<len(mes) else idx[-1]
                i0 = idx.get_loc(t)+1
                i1 = min(idx.get_loc(nxt)+1, len(idx))
                rr = rets_w.iloc[i0:i1][list(pick)].mean(axis=1)
                rs.append(rr)
        if not rs: 
            srs.append(0.0); continue
        daily = pd.concat(rs).sort_index()
        daily = daily.groupby(level=0).mean()
        vol = daily.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
        scale = (0.10/vol).clip(upper=5.0).fillna(0.0)
        rr = (daily*scale).iloc[5:]
        rr = rr[rr.index>='2009-07-01'].dropna()
        srs.append(rr.mean()/rr.std()*np.sqrt(252) if rr.std()>0 else 0.0)
    return np.array(srs)

real = pd.read_csv("/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch/HF_mom_cheap_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
sr_real = real.mean()/real.std()*np.sqrt(252)
print(f"real SR = {sr_real:.3f}")
for mode in ["mom", "filter", "both"]:
    srs = run(None, mode, 42)
    p = (srs < sr_real).mean()
    q95 = np.percentile(srs, 95)
    print(f"perm[{mode:6s}]: p={p:.3f} q95={q95:.3f} mean_scrambled={srs.mean():.3f}")
