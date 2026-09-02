import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_H11FIX/scratch")
from rebuild_fix import build, vt, sn, POOL, EXEC, SHORTF, N, ROOT

TGT,THR = 0.07,0.04
r_no,_  = build(TGT,THR,REBAL=False,KEEP=True)
r_reb,s = build(TGT,THR,REBAL=True, KEEP=True)
print(f"len no={len(r_no)} reb={len(r_reb)}; dup idx: no={r_no.index.duplicated().sum()} reb={r_reb.index.duplicated().sum()}")
same = r_no.index.equals(r_reb.index)
print(f"index identical: {same}")
if not same:
    mo = r_no.index.difference(r_reb.index); mr = r_reb.index.difference(r_no.index)
    print("only in noreb:", [str(d.date()) for d in mo[:10]], " only in reb:", [str(d.date()) for d in mr[:10]])
Sd, gs = s['Sd'], s['gs']
reb = (Sd.diff().abs().sum(axis=1)/N + gs.diff().abs().fillna(0)).reindex(r_reb.index).fillna(0)
expected = -reb*6e-4
d = (r_reb - r_no)
if not same:
    jj = pd.concat([r_no.rename('no'), r_reb.rename('re'), expected.rename('ex')], axis=1, join='inner').dropna()
else:
    jj = pd.concat([r_no.rename('no'), r_reb.rename('re'), expected.rename('ex')], axis=1)
jj['resid'] = jj.re - jj.no - jj.ex
print(f"n rows {len(jj)}; resid max|{jj.resid.abs().max():.3e}| at {jj.resid.abs().idxmax().date()}")
bad = jj[jj.resid.abs() > 1e-15]
print(f"rows with resid>1e-15: {len(bad)}")
print(bad[['no','re','ex','resid']].head(10).applymap(lambda x: f"{x*1e4:.2f}bp"))
