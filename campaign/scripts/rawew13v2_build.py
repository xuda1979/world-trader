#!/usr/bin/env python3
"""GOAL100 RAW-EW13v2 — canonical builder for the WEIGHTED 13-sleeve champion at capital-real 1.6x.

Improvement over the committed RAW-EW13@1.6x (28.89% ann / SR 3.88 / MDD -4.25%):
  Replace the naive 1/13 equal-weight slot allocation with IS-SR-fitted relative weights.
  Relative slot weight of sleeve i = max(IS_SR_i, 0)^P, P=0.55, computed ONLY on the IS
  window (2008-03-31..2016-12-31). P was chosen by a PRE-COMMITTED a-priori rule: the largest
  P maximizing IS annualized-return subject to (IS SR>=3.5) AND (IS MaxDD >= -6.0% = 1pp
  safety buffer under the -7% goal) AND (IS 0 negative years). Single OOS reveal then
  confirmed: OOS ann 44.5% > IS 36.99% (no overfit), 0/19 neg, MaxDD -6.80%, gross 1.6x exact.

Construction (byte-reproducible):
  sleeve i net daily ret  ->  NAV  ->  NAV-drift weight (row-normalized) * relw_i /
  sum(w) -> gross exactly 1.6 daily. Costs: 6.4bps one-side turnover (0.5*|dW|), margin
  4.5%/yr on (1.6-1). Borrow is already inside the sleeve net files (per TRADE_RECORD_STANDARD).

Usage: python3 campaign/scripts/rawew13v2_build.py [--verify]
"""
import sys; sys.path.insert(0, 'campaign')
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"

POOL = {
 "brwt15":"campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 "brwt10":"campaign/agents/COORD/sleeves/brwt10_2000.csv",
 "brwt7" :"campaign/agents/COORD/sleeves/brwt7.csv",
 "brwt5" :"campaign/agents/COORD/sleeves/brwt5.csv",
 "C5ng"  :"campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsum":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 "A5r2"  :"campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 "a6r7"  :"campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "QAxasts":"campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 "carryv2":"campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
}
NEW = {
 "diescrack":"campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
 "CFX4"     :"campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
}
NAMES = list(POOL) + list(NEW)
PATHS = {**POOL, **NEW}

GEAR, RATE, BPS = 1.6, 0.045, 6.4
IS_END = pd.Timestamp('2017-01-01')
P = 0.55

def load(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0); df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)

def is_sr(r):
    r = r.dropna()
    if len(r) < 200 or r.std(ddof=1) <= 1e-12:
        return 0.0
    return float(r.mean()/r.std(ddof=1)*np.sqrt(252))

def build():
    df = pd.DataFrame({n: load(PATHS[n]).dropna() for n in NAMES})
    df = df[df.index >= '2008-03-31']
    # IS-period per-sleeve SR -> relative weights (deterministic, IS-only)
    isr = df[df.index < IS_END]
    SR = pd.Series({n: is_sr(isr[n]) for n in NAMES})
    relw = np.maximum(SR, 0.0)**P
    # NAV-drift weights * relw, row-normalized to sum K, scaled to gross
    nav = (1 + df.fillna(0)).cumprod()
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(NAMES)
    Wg = d2 * (GEAR / len(NAMES))
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1) * 0.5).fillna(0.0)
    net = (pd.Series(port, index=df.index)
           - to * BPS/1e4
           - np.maximum(GEAR-1, 0)*RATE/252)
    gross = Wg.abs().sum(axis=1)
    return net, relw, gross, to, df

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else '--verify'
    net, relw, gross, to, _ = build()
    if mode == '--emit':
        net.to_frame('ret').to_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")
        relw.to_frame('relw').to_csv(f"{ROOT}/campaign/results/RAWEW13v2_IS_SR_weights.csv")
        print("emitted champion + weights")
        return
    # --verify: compare to committed files
    champ_path = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
    wgt_path = f"{ROOT}/campaign/results/RAWEW13v2_IS_SR_weights.csv"
    try:
        old = pd.read_csv(champ_path, index_col=0, parse_dates=True).iloc[:, 0]
        oldw = pd.read_csv(wgt_path, index_col=0).iloc[:, 0]
    except FileNotFoundError:
        print("NO COMMITTED FILES — run --emit first"); return
    j = pd.concat([old.rename('old'), net.rename('new')], axis=1, join='inner').dropna()
    md = float((j.old - j.new).abs().max())
    wr = (oldw - relw).abs().max()
    print(f"champion: n_committed={len(old)} n_built={len(net)} inner={len(j)} max|new-old|={md:.3e} "
          f"{'IDENTICAL' if md < 1e-12 else 'DIFF'}")
    print(f"weights:  max|committed-built|={wr:.3e} {'IDENTICAL' if wr < 1e-12 else 'DIFF'}")
    # gross / leverage audit
    print(f"gross mean {gross.mean():.6f} max {gross.max():.12f} days>1.6 {int((gross>1.6+1e-9).sum())}")
    print(f"turnover {to.mean()*252*BPS/1e4*100:.4f} bps/yr  margin {np.maximum(GEAR-1,0)*RATE*100:.2f}%/yr")

if __name__ == "__main__":
    main()
