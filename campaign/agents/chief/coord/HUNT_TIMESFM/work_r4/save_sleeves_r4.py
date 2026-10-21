"""Save ROUND 4 evidence sleeves (both families are NEGATIVE -> DEAD, saved for audit)."""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_TIMESFM/work_r4")
import eval_sleeves as E
import eval_b_overlay as B
from bt import metrics, gates as G

SLV = "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_TIMESFM/sleeves"
champ = E.champion()

# EW6 book: rebuild + scramble p
books = {}
for a in E.ASSETS:
    f = pd.read_csv(f"{E.OUT}/fcst_{a}.csv", parse_dates=["date"]).set_index("date")
    m = f["f"] - f["last"]
    px = E.close(a)
    r = px.pct_change().reindex(m.index)
    pos = pd.Series(np.sign(m.values), index=m.index)
    books[a] = E.net_of_positions(pos, r, vt="on")
book = pd.concat(books, axis=1).dropna().mean(axis=1)
# scramble on the raw per-unit book (unit positions vs avg ret, T+1 applied)
rets = {}
for a in E.ASSETS:
    f = pd.read_csv(f"{E.OUT}/fcst_{a}.csv", parse_dates=["date"]).set_index("date")
    rets[a] = E.close(a).pct_change().reindex(f.index)
# FIX r4 (bug found by failing run, see FINDINGS): build per-asset Series with their OWN
# date indices so pandas outer-aligns; different assets have different fcst lengths.
sig_s = {}
for a in E.ASSETS:
    f = pd.read_csv(f"{E.OUT}/fcst_{a}.csv", parse_dates=["date"]).set_index("date")
    sig_s[a] = pd.Series(np.sign((f["f"] - f["last"]).values), index=f.index)
raw = pd.DataFrame(sig_s).reindex(book.index).shift(1).fillna(0.0)
rmat = pd.DataFrame(rets).reindex(book.index).fillna(0.0)
p_agg = raw.mean(axis=1).values
r_agg = rmat.mean(axis=1).values
pv, real = G.scramble_positions(p_agg, r_agg, n=200)
print(f"EW6 scramble p={pv} real_sr={real:.3f}")
book.to_csv(f"{SLV}/TIMESFM_DIR_EW6_daily.csv", header=False)
with open(f"{SLV}/TIMESFM_DIR_EW6_daily.csv.meta", "w") as fh:
    fh.write("""name=TIMESFM_DIR_EW6_daily
status=DEAD
family=TimesFM forecast-direction L/S equal-weight 6 ETFs (QQQ,XLE,XLF,TLT,GLD,EEM)
window=2009-03..2026-09-03 (fcst ctx512 h1 walk-forward, strict T+1)
SR=-0.848 H1=-0.715 H2=-0.963 negyr=15 worst=-13.34% ann=-4.13% corr_vs_champ=-0.064
costs=6.4bps full |dW| + borrow 0.5%/yr + margin 4.5%/yr; VT 10% trailing clip3
per-asset net SR: QQQ -0.173 XLE -0.188 XLF -0.196 TLT -0.750 GLD -0.800 EEM -0.566
scramble_p(per-asset)=0.455..0.94; EW6 scramble_p=""" + f"{pv:.3f}" + """
verdict=DEAD: fails SR>=1.0, halves, negyears; dir-hit ~0.50 (5/6 assets p>0.26); NOT a momentum re-test (agree w/ naive 1d mom 0.488-0.513) - novel but alpha-less
""")

# (b) candidate overlay net book
cand = B.pct_rank_mask(B.mag_pool)
_, net_c, _ = B.ovl_delta(cand)
net_c.to_csv(f"{SLV}/TIMESFM_MAG_OVL_daily.csv", header=False)
with open(f"{SLV}/TIMESFM_MAG_OVL_daily.csv.meta", "w") as fh:
    fh.write("""name=TIMESFM_MAG_OVL_daily
status=NOT-ADOPTED (fails plateau + era-fragility despite dSR +0.174)
family=TimesFM |forecast| pct>0.8 -> 0.7x overlay on champion (N=252 trailing pct, PIT)
book: SR=3.355 (champ 3.181, dSR +0.174) h1=3.534 h2=3.235 negyr=0 ann=35.62%
controls: b1 own-vol mask dSR +0.099; b2 constant 0.993x dSR -0.006
plateau(thr 0.8): neighbors 0.7:+0.098 0.9:+0.118 vs thr 0.1395 -> FAIL
plateau(scale 0.7): neighbor 0.8:+0.120 vs thr 0.1767 -> FAIL
era-fragility: dSR excl Mar-Apr2020 = -0.039; excl all-2020 = -0.037 -> entire lift is 2020-03/04 (HUNT_CREDIT2(d) kill pattern)
days_on=112/4805 (2.3%); corr to champ 0.987 (overlay)
verdict=NOT-ADOPTED: fails gate (b) plateau + delta not robust out of one crisis era
""")
print("sleeves saved")
