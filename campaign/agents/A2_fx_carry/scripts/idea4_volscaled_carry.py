"""Idea 4: vol-scaled carry (inverse 21d pair vol weights) + tsmom lookback sweep for context."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A2_fx_carry/scripts")
import numpy as np, pandas as pd
import fx_lib as F

px = F.spots("2006-01-01")
y = F.yields8()
diff = y.sub(y["USD"], axis=0).drop(columns=["USD"]).ffill()
sig = diff.reindex(px.index).ffill()

def ranks_to_signed(sig):
    ranks = sig.rank(axis=1, ascending=False); n_ok = sig.notna().sum(axis=1)
    out = pd.DataFrame(0.0, index=sig.index, columns=sig.columns)
    for c in sig.columns:
        out[c] = np.where(ranks[c] <= 2, 1.0, np.where(ranks[c] > n_ok-2, -1.0, 0.0))
    return out.where(sig.notna(), 0.0)

def monthly(pos):
    m = pos.groupby([pos.index.year, pos.index.month]).head(1).index
    return pos.loc[m].reindex(pos.index).ffill().fillna(0.0)

signed = ranks_to_signed(sig)
vol = px.pct_change().rolling(21).std()*np.sqrt(252)
w = signed.div(vol.clip(0.05), axis=0)
w = w.div(w.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)  # gross=1
for cols, tag, start in [(list(sig.columns), "7pair", "2018-07-02"),
                         (["EUR","GBP","JPY","CAD"], "4pair", "2006-01-03")]:
    p = monthly(w[cols]).loc[start:]
    r = F.net_of(F.t1_pnl(p, px[cols]), p)
    F.report(f"volcarry_{tag}", r)

# context sweep: ts-mom lookbacks on 4-pair 2000+ (monthly, gross=1)
pxl = F.spots("2000-01-01")
for L in (21, 252):
    mom = pxl.pct_change(L)
    pos = np.sign(mom).div(1.0, axis=0)  # equal-weight signs, gross=1
    pos = pos.div(pos.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    pos = monthly(pos).loc["2000-06-01":]
    r = F.net_of(F.t1_pnl(pos, pxl), pos)
    F.report(f"tsmom{L}_mon_eqw", r)
