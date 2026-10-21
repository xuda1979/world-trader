"""ROUND 4 kill-test diagnostics: formal gates for (a) and (b) using bt.gates/metrics."""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_TIMESFM/work_r4")
import eval_sleeves as E
import tfm_engine_r4 as eng
import eval_b_overlay as B
from bt import gates as G, metrics

print("=== (a) gross vs net, direction hit-rate ===")
champ = E.champion()
for a in E.ASSETS:
    f = pd.read_csv(f"{E.OUT}/fcst_{a}.csv", parse_dates=["date"]).set_index("date")
    m = f["f"] - f["last"]
    px = E.close(a)
    r = px.pct_change().reindex(m.index)
    pos = pd.Series(np.sign(m.values), index=m.index)
    p = pos.shift(1).fillna(0.0)
    to = p.diff().abs(); to.iloc[0] = abs(p.iloc[0])
    gross = (p * r.fillna(0.0)).dropna()
    net = E.net_of_positions(pos, r, vt="off").dropna()
    nxt = np.sign(r.shift(-1).fillna(0.0).values)  # NOT used for trade; diag only
    hit = float((np.sign(m.values)[1:] == r.shift(-1).values[:-1]).mean())
    print(f"  {a}: grossSR={metrics.sharpe_d(gross):+.3f} netSR(vt off)={metrics.sharpe_d(net):+.3f} "
          f"dir-hit={hit:.3f} annTO={to.mean()*252:.1f}x")

print("=== (b) formal plateau gates (bt.gates.plateau_ok) on dSR grids ===")
mag_pool = B.mag_pool
def thr_dsr(thr):
    return B.ovl_delta(B.pct_rank_mask(mag_pool, pct_thr=thr))[0]
def lo_dsr(lo):
    return B.ovl_delta(B.pct_rank_mask(mag_pool, lo=lo))[0]
gthr = {t: thr_dsr(t) for t in (0.6, 0.7, 0.8, 0.9)}
glo = {l: lo_dsr(l) for l in (0.6, 0.7, 0.8, 0.9)}
print(f"  thr grid {gthr} -> plateau_ok={G.plateau_ok(gthr, 0.8)}")
print(f"  scale grid {glo} -> plateau_ok={G.plateau_ok(glo, 0.7)}")

print("=== (b) candidate vs b1 control: robustness of the DELTA ===")
cand = B.pct_rank_mask(mag_pool)
b1 = B.pct_rank_mask(B.rvp)
_, net_c, _ = B.ovl_delta(cand)
_, net_1, _ = B.ovl_delta(b1)
idx = net_c.index
excl = (idx < "2020-03-01") | (idx > "2020-04-30")
CHm = B.CH.reindex(idx)
d_c = (net_c - CHm)[excl].dropna(); d_1 = (net_1 - CHm)[excl].dropna()
print(f"  excl 2020-03/04: cand dSR={metrics.sharpe_d((net_c-CHm)[excl].dropna()):+.3f} "
      f"b1 dSR={metrics.sharpe_d((net_1-CHm)[excl].dropna()):+.3f}")
k = len(net_c) // 2
for nm, part in [("H1", slice(0, k)), ("H2", slice(k, None))]:
    dc = (net_c - CHm).iloc[part].dropna(); d1 = (net_1 - CHm).iloc[part].dropna()
    print(f"  {nm}: cand dSR={metrics.sharpe_d(dc):+.3f} b1 dSR={metrics.sharpe_d(d1):+.3f}")
# bootstrap the cand-vs-b1 delta difference (paired, 2000x)
diff = ((net_c - CHm) - (net_1 - CHm)).dropna()
rng = np.random.default_rng(0)
sr0 = metrics.sharpe_d(diff)
bs = [metrics.sharpe_d(diff.sample(len(diff), replace=True, random_state=int(i))) for i in range(2000)]
lo95, hi95 = np.percentile(bs, [2.5, 97.5])
print(f"  cand-minus-b1 dSR diff: point={sr0:+.3f} 95%CI=[{lo95:+.3f},{hi95:+.3f}] "
      f"P(diff>0)={float(np.mean(np.array(bs) > 0)):.3f}")
# scramble p on the overlay DELTA book (mask position vs champ ret)
p_c = cand.shift(1).fillna(1.0).reindex(B.CH.index).fillna(1.0).values
r_c = B.CH.fillna(0.0).values
pv, real = G.scramble_positions(p_c, r_c, n=200)
print(f"  overlay mask scramble p={pv} (real masked-book SR={real:.3f})")
