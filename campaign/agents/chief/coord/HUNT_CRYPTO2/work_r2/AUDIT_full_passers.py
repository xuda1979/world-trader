#!/usr/bin/env python3
"""R2 audit: EVERY nominal passer (dAnn>=+0.3pp or dMDD>=+0.5pp), with
scramble p on the CLAIMED metric + charter-window de-risk check (2018-06 / 2022)."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_CRYPTO2/work_r2")
import numpy as np, pandas as pd
from bt import metrics
from HUNT_CRYPTO2_round2_lib import load_env, all_configs, gate_metrics, binary_gate

env = load_env()
CHAMP = env['CHAMP']
res = {}
for name, cond, sc in all_configs():
    g, _ = binary_gate(cond, sc)
    res[name] = (g, gate_metrics(g, env))

rows = [(n, m['d_sr'], m['d_ann'] * 100, m['d_mdd'] * 100) for n, (g, m) in res.items()]
df = pd.DataFrame(rows, columns=['cfg', 'dSR', 'dAnn_pp', 'dMDD_pp']).set_index('cfg')
nom = df[(df.dAnn_pp >= 0.3) | (df.dMDD_pp >= 0.5)]
print(f"configs={len(df)}  NOMINAL PASSERS (dAnn>=+0.3pp OR dMDD>=+0.5pp): {len(nom)}/{len(df)}")
print(nom.sort_values('dMDD_pp', ascending=False).to_string(float_format=lambda v: f"{v:+.3f}"))

print("\nscramble (200x, live span) on the CLAIMED metric, bar p<=0.05; window de-risk check:")
print(f"champ in-window MDD: 2018 {metrics.max_dd(CHAMP.loc['2018':'2018'])*100:.2f}% | "
      f"2022 {metrics.max_dd(CHAMP.loc['2022':'2022'])*100:.2f}%")
for name, r in nom.sort_values('dMDD_pp', ascending=False).iterrows():
    g, m = res[name]
    claims_dd = r.dMDD_pp >= 0.5
    live = (g < 1.0).idxmax() if (g < 1.0).any() else g.index[-1]
    idx = g.index[g.index >= live]
    rv = CHAMP.reindex(idx).fillna(0.0)
    gv = g.reindex(idx).fillna(1.0)
    real_sr = metrics.sharpe_d(gv * rv)
    real_mdd = metrics.max_dd(gv * rv)
    rng = np.random.default_rng(7)
    cs = cm = 0
    for _ in range(200):
        s = np.roll(gv.values, rng.integers(10, len(rv) - 10))
        b = pd.Series(s * rv.values, index=idx)
        cs += metrics.sharpe_d(b) >= real_sr
        cm += metrics.max_dd(b) >= real_mdd
    p_sr, p_mdd = cs / 200, cm / 200
    w18 = float((g.loc['2018-05-15':'2018-07-31'] < 1.0).mean())
    w22 = float((g.loc['2022-01-01':'2022-12-31'] < 1.0).mean())
    claim_p = p_mdd if claims_dd else p_sr
    verdict = "PASS-claim" if claim_p <= 0.05 else "fail-claim"
    print(f"{name:22s} dMDD={r.dMDD_pp:+.3f} dAnn={r.dAnn_pp:+7.3f} | p_SR={p_sr:.3f} "
          f"p_MDD={p_mdd:.3f} -> {verdict:10s} | off%2018win={w18*100:3.0f} off%2022={w22*100:3.0f}")
