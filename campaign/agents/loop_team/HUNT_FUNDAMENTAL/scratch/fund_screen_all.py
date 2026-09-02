"""Systematic screen: ALL single + paired fundamental legs -> 12m fwd IC (vintage level),
on union panel. Uses same windows as engine. Report top/bottom combos."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
from hf_engine import load_panel, FUND
import numpy as np, pandas as pd

px, _ = load_panel()
F = pd.read_parquet(FUND)
F = F[F.symbol.isin(px.columns)].copy()
F["avail"] = pd.to_datetime((F.fy + 1).astype(str) + "-07-01")

# forward 12m returns at avail
fwd = {}
for sym in px.columns:
    s = px[sym].dropna()
    fwd[sym] = s
rows = []
for _, r in F.iterrows():
    s = fwd.get(r.symbol)
    if s is None: continue
    a = r.avail
    w = s[(s.index >= a)]
    if len(w) < 21: continue
    a0 = w.index[0]
    w2 = w[w.index <= a0 + pd.DateOffset(years=1)]
    if len(w2) < 200: continue
    f12 = w2.iloc[-1]/w2.iloc[0] - 1
    rows.append((r.symbol, int(r.fy), r.avail, f12,
                 r.equity, r.total_assets, r.debt, r.cash, r.net_income, r.op_income,
                 r.revenue, r.cogs, r.retained, r.shares, r.capex, r.dep_amort,
                 r.current_assets, r.current_liab, r.payables, r.receivables, r.inventory))
D = pd.DataFrame(rows, columns=["symbol","fy","avail","f12","equity","ta","debt","cash","ni","oi",
                                "rev","cogs","retained","shares","capex","da","ca","cl","pay","rec","inv"])
LEGS = {
 "eb": D.ni/D.equity.where(lambda s: s>0),
 "oi_ta": D.oi/D.ta.where(lambda s: s>0),
 "ni_ta": D.ni/D.ta.where(lambda s: s>0),
 "gross_prof": (D.rev-D.cogs)/D.ta.where(lambda s: s>0),
 "s_ta": D.rev/D.ta.where(lambda s: s>0),
 "roic": D.oi/(D.equity+D.debt-D.cash).where(lambda s: s>0),
 "lev": (D.debt-D.cash)/D.ta.where(lambda s: s>0),
 "accrual": (D.rec.diff().fillna(0) if False else (D.rec-D.rec)) ,
 "d_rev_ta": D.groupby("symbol")["rev"].diff()/D.ta.where(lambda s: s>0),
 "d_oi_ta": D.groupby("symbol")["oi"].diff()/D.ta.where(lambda s: s>0),
 "d_margin": (D.oi/D.rev.where(lambda s: s>0)).groupby(D.symbol).diff(),
 "retain_ta": D.retained/D.ta.where(lambda s: s>0),
 "cacl": D.ca/D.cl.where(lambda s: s>0),
 "capex_ta": D.capex/D.ta.where(lambda s: s>0),
 "asset_turn": D.rev/D.ta.where(lambda s: s>0),
}
res = []
fy_g = D.groupby("fy")
for name, x in LEGS.items():
    if x is None or isinstance(x, float): continue
    zz = x.groupby(D["fy"]).transform(lambda s: (s-s.median())/s.std()).clip(-3,3)
    D["_z"] = zz
    ic = D.dropna(subset=["_z","f12"]).groupby("fy").apply(lambda g: g._z.corr(g.f12, method="spearman") if len(g)>15 else np.nan)
    ic = ic.dropna()
    if len(ic) >= 8:
        res.append((name, ic.mean(), ic.mean()/ic.std() if ic.std()>0 else 0, len(ic)))
res.sort(key=lambda t: -abs(t[1]))
print("single legs: name meanIC IR n")
for name, m, ir, n in res:
    print(f"  {name:12s} {m:+.4f} {ir:+.2f} {n}")
# 2-leg combos (equal weight z)
keys = [k for k,_,_,_ in res[:10]]
import itertools
best = []
for a, b in itertools.combinations([k for k in LEGS if not isinstance(LEGS[k], float)], 2):
    za = LEGS[a].groupby(D["fy"]).transform(lambda s: (s-s.median())/s.std()).clip(-3,3)
    zb = LEGS[b].groupby(D["fy"]).transform(lambda s: (s-s.median())/s.std()).clip(-3,3)
    zz = (za+zb)/2
    D["_z"] = zz
    ic = D.dropna(subset=["_z","f12"]).groupby("fy").apply(lambda g: g._z.corr(g.f12, method="spearman") if len(g)>15 else np.nan).dropna()
    if len(ic) >= 8:
        best.append((f"{a}+{b}", ic.mean(), ic.mean()/ic.std() if ic.std()>0 else 0))
best.sort(key=lambda t: -abs(t[1]))
print("\ntop 10 pairs:")
for name, m, ir in best[:10]:
    print(f"  {name:28s} {m:+.4f} {ir:+.2f}")
