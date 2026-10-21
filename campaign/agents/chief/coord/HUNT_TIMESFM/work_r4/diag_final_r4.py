"""Final gate lines: (a) conditional hit rates; (b) excl-Mar2020 dSR + formal book gates."""
import sys, math
import numpy as np
import pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_TIMESFM/work_r4")
import eval_sleeves as E
import eval_b_overlay as B
from bt import metrics

def binom_p_2s(hits, n, p0=0.5):
    # normal approx, honest for n>1000
    z = (hits - n * p0) / math.sqrt(n * p0 * (1 - p0))
    from math import erf
    pval = 2 * (1 - 0.5 * (1 + erf(abs(z) / math.sqrt(2))))
    return z, pval

print("=== (a) conditional hit rates (skill beyond long-bias/drift) ===")
for a in E.ASSETS:
    f = pd.read_csv(f"{E.OUT}/fcst_{a}.csv", parse_dates=["date"]).set_index("date")
    m = (f["f"] - f["last"]).values
    px = E.close(a)
    r = px.pct_change().reindex(f.index)
    nxt = np.sign(r.shift(-1).fillna(0.0).values)
    upm, dnm = m > 0, m < 0
    hit_up = float((nxt[upm] > 0).mean()); hit_dn = float((nxt[dnm] < 0).mean())
    base_up = float((nxt > 0).mean())
    both = np.sign(m) != 0
    hits = float((np.sign(m)[both] == nxt[both]).sum()); n = int(both.sum())
    z, p = binom_p_2s(hits, n)
    print(f"  {a}: hit_up={hit_up:.4f} (base {base_up:.4f}) hit_dn={hit_dn:.4f} "
          f"| overall {hits:.0f}/{n} z={z:+.2f} p={p:.4f}")

print("=== (b) era-fragility: dSR excluding 2020-03/04 window ===")
cand = B.pct_rank_mask(B.mag_pool)
b1 = B.pct_rank_mask(B.rvp)
_, net_c, _ = B.ovl_delta(cand)
_, net_1, _ = B.ovl_delta(b1)
idx = net_c.index; CHm = B.CH.reindex(idx)
for nm, keep in [("full", idx == idx),
                 ("excl Mar-Apr20", (idx < "2020-03-01") | (idx > "2020-04-30")),
                 ("excl all-2020", idx.year != 2020)]:
    k = keep if isinstance(keep, (pd.Series, np.ndarray)) else keep.reindex(idx)
    s_c = metrics.sharpe_d(net_c[k]); s_1 = metrics.sharpe_d(net_1[k]); s_ch = metrics.sharpe_d(CHm[k])
    print(f"  {nm}: cand SR={s_c:.3f} (dSR {s_c-s_ch:+.3f})  b1 SR={s_1:.3f} (dSR {s_1-s_ch:+.3f})  champ SR={s_ch:.3f}")

print("=== (b) formal gates on overlaid champion book (cand) ===")
g = E.gate_report(net_c, B.CH)
print(f"  SR={g['sr']} h1={g['h1']} h2={g['h2']} neg={g['neg']} worst={g['worst']} "
      f"corr={g['corr']} ann={g['ann']} n={g['n']} (corr~1 by construction: overlay, not new sleeve)")
print(f"  champ: SR={metrics.sharpe_d(B.CH):.3f} ann={metrics.ann_geo(B.CH):.4f}")
