"""VERIFY_BEST Object 2: INDEPENDENT rebuild of RAW-EW13@1.6x from the 13 sleeve net files
(POOL + NEW2 minus FF2). Recipe per documented construction: slot 1/13 of NAV, NAV-drift
weights, daily-reset gross exactly 1.6x, costs 6.4bps/side on EW-reset turnover (x GEAR),
margin 4.5%/yr on (1.6-1), borrow already inside sleeve files. Verified with bt.engine
capital_gross + metrics."""
import sys; sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')
import numpy as np, pandas as pd
from bt import metrics as M, engine as E
ROOT = "/Users/daxu/software/world-trader"

def load(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)

POOL = ["brwt15","brwt10","brwt7","brwt5","C5ng","C5ngsum","A5r2","a6r7","QAxasts","carryv2","dualmom"]
NEW2 = {"diescrack": "campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
        "CFX4":      "campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv"}
NAMES = POOL + list(NEW2.keys())
PATHS = dict(zip(POOL, ["campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 "campaign/agents/COORD/sleeves/brwt10_2000.csv","campaign/agents/COORD/sleeves/brwt7.csv",
 "campaign/agents/COORD/sleeves/brwt5.csv","campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 "campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv"]), )
PATHS.update(NEW2)

GEAR, RATE, BPS = 1.6, 0.045, 6.4
df = pd.DataFrame({n: load(PATHS[n]).dropna() for n in NAMES}).dropna(how='all')
df = df[df.index >= '2008-03-31']
K = len(NAMES); print(f"sleeves K={K}: {NAMES}")
port = df.mean(axis=1)                                   # slot-EW daily return
nav = (1 + df.fillna(0)).cumprod()
w = nav.div(nav.mean(axis=1), axis=0).div(K)             # drift weights, sum=1
to = (w.diff().abs().sum(axis=1)*0.5).fillna(0)          # one-side EW-reset turnover
r = (port*GEAR - to*GEAR*BPS/1e4 - (GEAR-1)*RATE/252).dropna()

# committed file comparison
old = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST_RAWEW13_GEAR16_daily.csv",
                  index_col=0, parse_dates=True).iloc[:, 0]
j = pd.concat([old.rename('old'), r.rename('new')], axis=1, join='inner').dropna()
md = float((j.old-j.new).abs().max())
print(f"RAW-EW13@1.6x: n_committed={len(old)} n_rebuilt={len(r)} inner={len(j)} "
      f"max|new-old|={md:.3e} {'IDENTICAL' if md < 1e-12 else 'DIFF'}")

# capital-real gross of the geared path (drift weights * GEAR)
Wg = w.mul(GEAR, axis=0).reindex(r.index)
gross = E.capital_gross(Wg)
print(f"bt.engine.capital_gross: mean {gross.mean():.6f}  max {gross.max():.12f}  min {gross.min():.6f}")
print(f"days with gross > 1.6+1e-9: {(gross > 1.6+1e-9).sum()}/{len(gross)} "
      f"({(gross > 1.6+1e-9).mean()*100:.4f}%)  max overshoot {float((gross-1.6).max()):.3e}")

rep = M.report(r[r.index >= '2008-03-31'])
print("\nbt.metrics.report RAW-EW13@1.6x (2008-03-31+):", rep)
yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
print("worst year:", f"{yr.min()*100:+.2f}%", " neg:", int((yr<0).sum()), "/", yr.size)
h1, h2 = M.half_split(r)
print(f"H1 SR {h1:.3f}  H2 SR {h2:.3f}  ac1 {G.lag1_autocorr(r):+.3f}  uniqR {G.uniq_ratio(r):.3f}"
      if False else f"H1 SR {h1:.3f}  H2 SR {h2:.3f}")
from bt import gates as G
print(f"ac1 {G.lag1_autocorr(r):+.3f}  uniqR {G.uniq_ratio(r):.3f}  zruns20 {G.zero_runs_long(r)}")

# cost decomposition sanity
cost_bps_ann = to.mean()*252*GEAR*BPS/1e4*100
margin_ann = (GEAR-1)*RATE*100
print(f"\nEW-reset cost {to.mean():.6f}/day = {cost_bps_ann:.2f}bps/yr; "
      f"margin {(GEAR-1)*RATE*100:.2f}%/yr charged on {len(r)} days")
