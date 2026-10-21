"""HUNT_TIMESFM ROUND 4 family (b): forecast-magnitude champion overlay + content-free
controls (HUNT_CREDIT2 (d) kill-test machinery, a-priori params: pct 0.8 -> 0.7x, N=252).
Adoptable ONLY if candidate delta > control deltas (b1 vol-mask, b2 constant scale)."""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_TIMESFM/work_r4")
import eval_sleeves as E
import tfm_engine_r4 as eng
from bt import metrics

OUT = E.OUT
GEAR = 1.6
champ = E.champion()
CH = champ.dropna()


def ovl_delta(scale):
    """FIXED overlay convention (TDD tests/test_overlay_tdd_r4.py): champ*g with extra
    turnover cost |d(1.6*g)|*6.4bps ONLY — champion CSV is already net of financing;
    charging margin on (w-1) again double-counts (old E.overlay_net did this)."""
    s = scale.shift(1).fillna(0.0).reindex(CH.index)
    w = s * GEAR
    to_extra = w.diff().abs().fillna(w.abs())
    net = (CH * s - to_extra * 6.4e-4).dropna()
    return (metrics.sharpe_d(net) - metrics.sharpe_d(CH), net, metrics.sharpe_d(net))


def pct_rank_mask(series_pct: pd.Series, pct_thr=0.8, lo=0.7):
    """1.0 default; -> lo when rolling percentile of the signal > pct_thr (decision day t)."""
    z = series_pct.fillna(0.0)
    m = pd.Series(np.where(z > pct_thr, lo, 1.0), index=z.index)
    return m


print("=== (b) forecast-magnitude 0.7x overlay on champion (a-priori: pct>0.8 -> 0.7x, N=252) ===")
mags = {}
for a in E.ASSETS:
    f = pd.read_csv(f"{OUT}/fcst_{a}.csv", parse_dates=["date"]).set_index("date")
    m = (f["f"] - f["last"]).abs()
    # rolling 252d percentile rank of |predicted move| (PIT: rank vs trailing only)
    def roll_pct(x):
        s = pd.Series(x)
        return (s.expanding(min_periods=252).rank(pct=True))  # expanding = trailing incl self? no:
    # trailing-only percentile: rank of x_t among x_{t-252..t}; computed on series ending at t
    r = m.rolling(252).apply(lambda w: (w <= w[-1]).mean(), raw=True)
    mags[a] = r
mag_pool = pd.concat(mags, axis=1).mean(axis=1)   # breadth: mean of 6 trailing percentiles
mag_pool = mag_pool.reindex(CH.index).ffill(limit=5)

cand = pct_rank_mask(mag_pool)
d_c, net_c, sr_c = ovl_delta(cand)
n_on = int((cand.shift(1).fillna(1.0) < 1.0).sum())
print(f"cand  (|fcst| pct>0.8 ->0.7x): dSR={d_c:+.3f} SR={sr_c:.3f} days_on={n_on}")

# b1 CONTENT-FREE CONTROL: champion own trailing 252d realized-vol percentile, same machinery
rv = CH.rolling(252).std()
rvp = rv.rolling(252).apply(lambda w: (w <= w[-1]).mean(), raw=True)
b1 = pct_rank_mask(rvp)
d_1, net_1, sr_1 = ovl_delta(b1)
print(f"b1    (champ own vol pct>0.8): dSR={d_1:+.3f} SR={sr_1:.3f} days_on={int((b1.shift(1).fillna(1.0)<1.0).sum())}")

# b2 CONSTANT control: scale matched to candidate mean exposure (incl T+1 hold semantics)
held = cand.shift(1).fillna(1.0)
const = pd.Series(held.mean(), index=CH.index)
d_2, net_2, sr_2 = ovl_delta(const)
print(f"b2    (constant {held.mean():.3f}x):        dSR={d_2:+.3f} SR={sr_2:.3f}")

# plateau: pct_thr neighbors 0.6/0.7/0.8/0.9 and scale 0.6/0.7/0.8
print("  -- plateau (objective dSR; neighbors within 20% of peak required) --")
grid = {}
for thr in (0.6, 0.7, 0.8, 0.9):
    m_ = pct_rank_mask(mag_pool, pct_thr=thr)
    d_, _, _ = ovl_delta(m_)
    grid[thr] = d_
    print(f"  thr={thr}: dSR={d_:+.3f}")
grid2 = {}
for lo in (0.6, 0.7, 0.8, 0.9):
    m_ = pct_rank_mask(mag_pool, lo=lo)
    d_, _, _ = ovl_delta(m_)
    grid2[lo] = d_
    print(f"  scale={lo}: dSR={d_:+.3f}")

# era split + win/loss-day anatomy of the candidate (HUNT_CREDIT2 C-anatomy)
net_c = net_c.dropna()
delta = (net_c - CH.reindex(net_c.index)).dropna()
print("  -- era split of dSR contribution --")
for name, lo, hi in [("08-12", "2008-03-31", "2009-12-31"), ("13-19", "2013-01-01", "2019-12-31"),
                     ("20-26", "2020-01-01", "2026-08-27")]:
    dpart = delta[(delta.index >= lo) & (delta.index <= hi)]
    chpart = CH.reindex(dpart.index)
    srp = metrics.sharpe_d(net_c[(net_c.index >= lo) & (net_c.index <= hi)]) - \
        metrics.sharpe_d(chpart)
    print(f"  {name}: dSR={srp:+.3f} days_on={int((held.reindex(dpart.index) < 1.0).sum())}")

on_days = held.reindex(delta.index) < 1.0
ch_on = CH.reindex(delta.index)[on_days]
print(f"  gated days: n={int(on_days.sum())}, mean champ ret={ch_on.mean()*100:+.1f}bp, "
      f"share positive={float((ch_on > 0).mean())*100:.0f}%")
top = delta.abs().sort_values(ascending=False).head(6)
print("  top-6 |dSR contrib| days (champ ret, gated?):")
for d in top.index:
    print(f"    {d.date()} champ={CH.loc[d]*100:+.2f}% on={bool(on_days.loc[d])}")
EOF_MARKER = True
