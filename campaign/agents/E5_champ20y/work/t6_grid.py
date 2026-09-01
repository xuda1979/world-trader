import numpy as np, pandas as pd, json, itertools
from e5lib import *

TGTS = [0.07, 0.075, 0.08, 0.085, 0.09]
THRS = [0.03, 0.035, 0.04, 0.045]
ENDS = [(2016, 12, 31), (2019, 12, 31), (2022, 12, 31), (2023, 12, 31)]

def sr(x):
    return x.mean() / x.std() * np.sqrt(252)

def ddwin(r, a, b=None):
    w = r[r.index >= a] if b is None else r[(r.index >= a) & (r.index <= b)]
    return dd_series(w).min()

print("grid: FULL stats + IS(2007-2016) selection inputs")
rows = []
for t, h in itertools.product(TGTS, THRS):
    r, s, u = construct20(t, h)
    full = stats(r)
    is_r = r[r.index <= "2016-12-31"]
    is_sr = sr(is_r); is_dd = dd_series(is_r).min()
    yr_dd = dd_series(is_r).groupby(is_r.index.year).min()
    is_ok = (is_dd >= -0.08) and (yr_dd >= -0.08).all()
    oos_dd = dd_series(r[r.index >= "2017-01-01"]).min()
    stab = []
    for (y, m, d) in ENDS:
        w = r[r.index <= f"{y}-{m:02d}-{d:02d}"]
        stab.append((sr(w), dd_series(w).min(), bool((dd_series(w).groupby(w.index.year).min() >= -0.08).all())))
    rows.append(dict(t=t, h=h, full=full, is_sr=is_sr, is_dd=is_dd, is_ok=is_ok,
                     oos_dd=oos_dd, stab=stab))
    print(f"vt={t:.3f} thr={h:.3f}: FULL ann={full['ann']:5.1f} sr={full['sr']:4.2f} dd={full['mdd']:5.1f} | "
          f"IS sr={is_sr:4.2f} dd={is_dd*100:5.1f} ok={int(is_ok)} oosDD={oos_dd*100:5.1f} | "
          f"stabSR(end2016/19/22/23)={stab[0][0]:.2f}/{stab[1][0]:.2f}/{stab[2][0]:.2f}/{stab[3][0]:.2f}")

# coordinator's choices for reference (A outside grid)
print("\ncoordinator A (vt.065 thr.04):", stats(construct20(0.065, 0.04)[0]))
print("coordinator B (vt.08 thr.03):", stats(construct20(0.08, 0.03)[0]))

# IS-selection: argmax IS SR s.t. IS DD<=8% & all IS calendar-yr DD<=8%, per IS-end
print("\n-- IS selection per IS-end (argmax IS SR subject to IS DD<=8% & every IS yr DD<=8%) --")
sel = {}
for i, (y, m, d) in enumerate(ENDS):
    cand = [r_ for r_ in rows if r_["stab"][i][1] >= -0.08 and r_["stab"][i][2]]
    if not cand:
        print(f"end {y}: NO candidate passes IS DD rule"); continue
    best = max(cand, key=lambda r_: r_["stab"][i][0])
    sel[y] = (best["t"], best["h"])
    print(f"end {y}: chosen vt={best['t']:.3f} thr={best['h']:.3f} IS_SR={best['stab'][i][0]:.2f}")

json.dump([{k: v for k, v in r_.items() if k != 'stab'} | {"stab": [list(x) for x in r_["stab"]]} for r_ in rows],
          open("/Users/daxu/software/world-trader/campaign/agents/E5_champ20y/work/t6_grid.json", "w"), indent=1, default=float)
