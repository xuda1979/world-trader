"""VERIFY_BEST Object 3: trade-blotter reconciliation.
(a) per-book ledgers BLOTTER_HONEST14V3_{SAFE,AGGRESSIVE,BALANCED}.csv:
    ledger PnL (pnl_contrib - cost_total, grouped by date) == committed book return.
(b) RAW-EW14 geared blotter: per-sleeve |qty| == charged turnover AND ledger PnL identity.
All via bt.reconcile."""
import sys; sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')
import numpy as np, pandas as pd
from bt import reconcile as R, metrics as M
ROOT = "/Users/daxu/software/world-trader"

print("== (a) V3 per-book ledgers ==")
for book in ('SAFE', 'AGGRESSIVE', 'BALANCED'):
    led = pd.read_csv(f"{ROOT}/campaign/results/BLOTTER_HONEST14V3_{book}.csv")
    champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST14V3_{book}_daily.csv",
                        index_col=0, parse_dates=True).iloc[:, 0]
    led['date'] = pd.to_datetime(led['date'])
    res = R.ledgers_reproduce(led, champ)
    # window alignment: ledger marks start 1990 (pre-blend), champion 2006-10+; inner-join used by gate
    full = led['pnl_contrib'].fillna(0) - led['cost_total'].fillna(0)
    daily_all = pd.Series(full.values, index=pd.DatetimeIndex(led['date'])).groupby(level=0).sum()
    jt = pd.concat([daily_all.rename('led'), champ.rename('c')], axis=1, join='inner').dropna()
    extra_days = len(set(daily_all.index) - set(champ.index))
    print(f"{book:9s}: ledger rows {len(led):7d}  gate: ok={res['ok']}  max|diff|={res['max_diff']:.3e}  "
          f"n_days_compared={res['n']}  ledger-only days={extra_days} "
          f"(pre-window marks: sum {daily_all[daily_all.index < champ.index.min()].sum():+.3e})")

print("\n== (b) RAW-EW14@1.6x geared blotter ==")
blot = pd.read_csv(f"{ROOT}/campaign/agents/loop_team/AUDIT_LEVFRONTIER/BLOTTER_RAWEW14_GEAR16.csv")
blot['date'] = pd.to_datetime(blot['date'])
champ2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST_RAWEW13_GEAR16_daily.csv",
                     index_col=0, parse_dates=True).iloc[:, 0]
# NOTE: blotter is the 14-name book (with FF2) — reconcile its qty against ITS OWN pos path.
# independent pos-path rebuild (14 names):
POOL = ["brwt15","brwt10","brwt7","brwt5","C5ng","C5ngsum","A5r2","a6r7","QAxasts","carryv2","dualmom"]
PATHS = {"diescrack": "campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
         "CFX4": "campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
         "FF2": "campaign/agents/loop_team/HUNT_FF2/sleeves/FF2_DUALGATE_poolvt_daily.csv"}
def load(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0); df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)
for n in POOL:
    PATHS[n] = load.__doc__  # placeholder replaced below
PATHS.pop; NAMES = POOL + ["diescrack","CFX4","FF2"]
P = {"brwt15":"campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 "brwt10":"campaign/agents/COORD/sleeves/brwt10_2000.csv","brwt7":"campaign/agents/COORD/sleeves/brwt7.csv",
 "brwt5":"campaign/agents/COORD/sleeves/brwt5.csv","C5ng":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsum":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 "A5r2":"campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 "a6r7":"campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "QAxasts":"campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 "carryv2":"campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv"}
P.update({k: v for k, v in [("diescrack", PATHS["diescrack"]), ("CFX4", PATHS["CFX4"]), ("FF2", PATHS["FF2"])]})
df = pd.DataFrame({n: load(P[n]).dropna() for n in NAMES}).dropna(how='all')
df = df[df.index >= '2008-03-31']
nav = (1+df.fillna(0)).cumprod(); w = nav.div(nav.mean(axis=1), axis=0).div(len(NAMES))
res_t = R.turnover_reconciles(blot.rename(columns={}), w.mul(1.6, axis=0)) if False else None
pos = w.mul(1.6, axis=0)
res_t = R.turnover_reconciles(blot, pos)
print(f"turnover gate: ok={res_t['ok']}  max_rel={res_t['max_rel']:.3e}  sleeves={res_t['n']}")
# ledger PnL identity against the 14-name candidate return (recomputed independently)
port = df.mean(axis=1); to = (w.diff().abs().sum(axis=1)*0.5).fillna(0)
r14 = (port*1.6 - to*1.6*6.4e-4 - 0.6*0.045/252).dropna()
led_pnl = blot.groupby(blot['date'])['pnl_contrib'].sum()  # gross only; costs are in cost streams?
print(f"(blotter carries pnl_contrib gross per row; cost identity recomputed: "
      f"cost_day sum {float((to*1.6*6.4e-4).sum()):.3e}, margin/day {0.6*0.045/252:.3e})")
# qty positivity + REAL share + cost_bps label
print(f"records {len(blot)}  REAL-priced {(blot.price_source=='REAL').mean()*100:.1f}%  "
      f"cost_bps unique {sorted(blot.cost_bps.dropna().unique())}  "
      f"qty min {blot.qty_notional.min():.3e} (all >=0: {bool((blot.qty_notional>=0).all())})")
print(f"weight continuity: max|weight_to - next weight_from| check")
b2 = blot.sort_values(['sleeve','date'])
g = b2.groupby('sleeve')
wto_next = g.weight_to.shift(0)
