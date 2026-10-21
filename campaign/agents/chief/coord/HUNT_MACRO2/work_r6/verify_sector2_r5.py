#!/usr/bin/env python3
"""HUNT_MACRO2 ROUND 6 (a) fraud-catch: independent cross-verification of HUNT_SECTOR2's R5
verdict from published artifacts with OWN code (no import of hunt_sector2_lib /
hunt_sector2_r5). Base leg = their published A11 net CSV (their own R3 precedent, quoted in
their FINDINGS: an in-line rebuild reproduced only corr 0.844 -> artifact is authoritative).
Everything else is mine: attention panel/z, gate/scale, costs, battery numbers, placebo,
delta halves, exclusion test.
"""
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
WIKI = f"{ROOT}/tools/quant/data/wiki_attention"
A11 = f"{ROOT}/campaign/agents/chief/coord/HUNT_SECTOR2/sleeves/A11_rs_ratio#lb126k4.csv"
ANN = 252.0
COST = 6.4e-4
NICKS = ["aapl", "nvda", "tsla", "spx", "vix", "fomc", "cpi"]

# --- my own attention covariate (spec from their FINDINGS: cross-nick mean of 252d z,
# then 252d z of that mean; trailing-only)
panel = pd.concat(
    [pd.read_csv(f"{WIKI}/{k}.csv", parse_dates=["date"]).set_index("date")["views"].rename(k)
     for k in NICKS], axis=1).sort_index()
z = (panel - panel.rolling(252).mean()) / panel.rolling(252).std()
cross = z.mean(axis=1, skipna=True)
att = ((cross - cross.rolling(252).mean()) / cross.rolling(252).std()).rename("att_z")

# --- base = published artifact
base = pd.read_csv(A11, parse_dates=["date"]).set_index("date")["ret"]
sr_base = float(base.mean() / base.std(ddof=1) * np.sqrt(ANN))

# --- my own gate: att_z > +1 -> 0.25x, else 1.0; strict PIT shift(2)
gate = (att > 1.0).reindex(base.index).fillna(False)
scale = pd.Series(np.where(gate, 0.25, 1.0), index=base.index).shift(2).fillna(1.0)
cost = scale.diff().abs().fillna(0.0) * COST
net_on = base * scale - cost
sr_on = float(net_on.mean() / net_on.std(ddof=1) * np.sqrt(ANN))
dsr = sr_on - sr_base

# --- delta honesty: halves + single-year exclusion (their convention: SR of delta stream d)
d = (net_on - base)
k = len(d) // 2
sr_d = lambda x: float(x.mean() / x.std(ddof=1) * np.sqrt(ANN))
dh1, dh2 = sr_d(d.iloc[:k]), sr_d(d.iloc[k:])
yr = d.groupby(d.index.year).apply(lambda x: x.sum())
best = int(yr.idxmax())
d_ex = d[d.index.year != best]
dsr_ex = sr_d(d_ex)

# --- MY OWN matched placebo (200 draws, matched fire-frac + flip-count, shift(2), 0.25x)
fire = (scale < 1.0).to_numpy()
frac, nflip = fire.mean(), int(np.abs(np.diff(fire.astype(int))).sum())
rng = np.random.default_rng(20260908)   # MY seed, not theirs
beats = 0
for _ in range(200):
    g = (rng.random(len(base)) < frac).astype(int)
    for _ in range(50):
        if abs(int(np.abs(np.diff(g)).sum()) - nflip) <= max(2, nflip // 20):
            break
        g = (rng.random(len(base)) < frac).astype(int)
    sc = pd.Series(np.where(pd.Series(g, index=base.index).shift(2).fillna(0.0) > 0, 0.25, 1.0),
                   index=base.index)
    if sr_d(base * sc - sc.diff().abs().fillna(0.0) * COST) >= sr_on:
        beats += 1
p_placebo = beats / 200

# --- gate stats + span facts
fire_frac = float(fire.mean())
flips = int(np.abs(np.diff(fire.astype(int))).sum())
span = f"{base.index.min().date()}..{base.index.max().date()}"
# my wiki span check
wiki_first = panel.index.min().date()

print(f"span            {span}   n={len(base)}")
print(f"wiki_attention first bar (7-nick union): {wiki_first}")
print(f"sr_base         {sr_base:.4f}   (claim 0.679)")
print(f"sr_overlay      {sr_on:.4f}   (claim 0.821)")
print(f"dSR             {dsr:+.4f}   (claim +0.141)")
print(f"gate fire_frac  {fire_frac:.3f}  flips {flips}   (claim 0.223 / 300)")
print(f"dSR halves      ({dh1:+.3f}, {dh2:+.3f})   (claim +0.407, -1.087)")
print(f"excl {best} dSR   {dsr_ex:+.3f}   (claim -0.979 excl 2020)")
print(f"placebo p (my seed): {p_placebo:.3f}  ({beats}/200)   (claim p=0.000)")

# leak probe MY OWN: corr(decision quantity shift-relevance, r_t). Their leak dict: corr
# +0.084 p 0.000127, lag0 not argmax (lag-2 0.088), leak=False. I reproduce the probe:
# decision at t uses att_{t-2}; same-period corr = corr(scale_t, base_t) via r_pu contract.
sig_arr = scale.to_numpy()
r_pu = (base - cost / scale).to_numpy()
same = np.corrcoef(sig_arr, r_pu)[0, 1]
from scipy import stats as st
tstat = same * np.sqrt((len(sig_arr) - 2) / (1 - same ** 2))
p_same = 2 * (1 - st.t.cdf(abs(tstat), df=len(sig_arr) - 2))
lags = {}
for L in (-2, -1, 0, 1, 2):
    s2 = pd.Series(sig_arr).shift(L)
    lags[L] = float(np.corrcoef(pd.Series(s2).fillna(0.0), r_pu)[0, 1])
argmax = max(lags, key=lags.get)
leak = abs(same) >= 0.20 and p_same < 0.05 and argmax == 0
print(f"my leak probe: same_period_corr {same:+.4f} p {p_same:.2e} argmax lag {argmax} "
      f"leak={leak}  (claim +0.084 / 0.000127 / lag-2 / False)")

out = dict(span=span, n=len(base), sr_base=sr_base, sr_overlay=sr_on, dsr=dsr,
           fire_frac=fire_frac, flips=flips, dh1=dh1, dh2=dh2, excl_year=best,
           dsr_excl=dsr_ex, placebo_p=p_placebo, same_corr=same, p_same=p_same, leak=leak)
import json
json.dump(out, open(f"{ROOT}/campaign/agents/chief/coord/HUNT_MACRO2/work_r6/sector2_r5_verify.json", "w"), indent=1, default=str)
print("saved work_r6/sector2_r5_verify.json")
