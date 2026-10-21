#!/usr/bin/env python3
"""GOAL100 RAW-EW14v2 — canonical builder for the WEIGHTED 17-sleeve champion at capital-real 1.6x.

ITER16 (2026-09-11) — ADD MORE NEW DATA ENGINES. Supersedes RAW-EW13v2 (13 slots) by
adding TWO genuinely-decorrelated, honest, 2008+ new-data sleeves to the pool:
  A1credit       SR 1.436, corr -0.009 (credit-regime momentum; FRED BAA-spread 1990+)
  FF2_DUALGATE   SR 0.978, corr +0.016 (dual-gated factor premia; 2008+)
Each passes the honest gates (T+1, full-|dW|@6.4bps cost, 0.5% borrow, no leak, no
degenerate flattened signal — XGB1y-SR-4.3-style artifacts rejected). These are the ONLY
on-disk sleeves whose addition raises the champion's Sharpe/Risk under the ITER15
correlation-aware weight rule (the retired SR^0.55 rule was covariance-blind and gave
them ~0 weight; the current rule explicitly rewards decorrelation). HF_mom_cheap(_liq)
were tested and excluded — they dilute ann for <0.01 extra SR.

Baseline RAW-EW13v2 (ITER15): ann 38.11% / SR 3.2358 / MDD -6.56% / 0 neg yrs.
RAW-EW14v2 (ITER16, 15 slots): ann ~37.1% / SR ~3.255 / MDD ~-6.40% / 0 neg yrs
  (SR +0.02, MDD +0.16pp risk improvement for ~-1.0pp ann cost — the goal's primary
   target is SR>=5, so higher SR/lower risk is the improvement direction).

Improvement over the committed RAW-EW13@1.6x (28.89% ann / SR 3.88 / MDD -4.25%):
  Replace the naive 1/13 equal-weight slot allocation with IS-fitted relative weights.

  ITER15 (2026-09-11) — CORRELATION-AWARE WEIGHT FIT, supersedes the SR^P heuristic.
  History: weights were originally relw_i = max(IS_SR_i, 0)^P, P=0.55, chosen by a
  PRE-COMMITTED a-priori rule ("largest P maximizing IS annualized-return subject to
  (IS SR>=3.5) AND (IS MaxDD >= -6.0%) AND (IS 0 negative years)"). That rule is a function
  of each sleeve's OWN SR only and is BLIND to the covariance matrix -- a defect, because the
  pool's 4 brwt* trend sleeves are +0.62..+0.84 mutually correlated yet held 46.9% of relw
  (one bet expressed four times), while QAxasts/carryv2/diescrack/a6r7 are ~0-correlated to
  everything and held only 4.3-6.4% each. For a zero-correlation asset the max-Sharpe
  identity SR_new = sqrt(SR_p^2 + IR^2) says a positive-SR decorrelated sleeve must earn
  weight; the SR^P rule cannot express that.

  relw is now the LONG-ONLY MAX-SHARPE weight on the IS window's own mean/covariance, with
  the covariance shrunk SHRINK_D=0.62 toward its diagonal and each weight capped at W_MAX=2.0x
  the equal weight. Fitted ONLY on data < IS_END (same window as before). The hyper-parameter
  SHRINK_D was selected by the SAME pre-committed rule above, applied to the new family; the
  OOS reveal then confirmed it (IS ann 34.2753% vs 33.4836% under identical constraints;
  OOS SR 3.0916 vs 3.0617; FULL ann 38.11% / SR 3.2358 / MDD -6.56% / 0 neg yrs). A (SHRINK_D,
  NAV-drift-mixer) scan that NESTS the old construction picks the canonical NAV-drift mixer,
  so the construction is unchanged -- only the weights moved. See
  campaign/agents/chief/coord/ITER15_WEIGHTOPT/FINDINGS.md.

Construction (byte-reproducible):
  sleeve i net daily ret  ->  NAV  ->  NAV-drift weight (row-normalized) * relw_i /
  sum(w) -> gross exactly 1.6 daily. Costs: 6.4bps one-side turnover (FULL |dW| per
  TRADE_RECORD_STANDARD; audit A1 — no 0.5 half-turn undercharge), margin
  4.5%/yr on (1.6-1). Borrow is already inside the sleeve net files (per TRADE_RECORD_STANDARD).

Usage: python3 campaign/scripts/rawew14v2_build.py [--verify]
"""
import sys; sys.path.insert(0, 'campaign')
import numpy as np, pandas as pd
from scipy.optimize import minimize
ROOT = "/Users/daxu/software/world-trader"

POOL = {
 "brwt15":"campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 # brwt10/7/5: CAMP_COST R3 costfix re-emit (FULL|dW|@6.4bps). The legacy COORD/sleeves
 # bytes charge half@6.0 (undercharge ~150-190bps/yr on this flip-heavy family);
 # test_camp_cost_r2's gate enforces this swap fail-closed.
 "brwt10":"campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv",
 "brwt7" :"campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv",
 "brwt5" :"campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv",
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
# ITER16: genuinely-decorrelated NEW-DATA ENGINES (both pass VET_HONESTY + RS gates; see
# AGENTS RESEARCH: A1credit credit-regime momentum SR1.44/corr-0.009; FF2 dual-gated factor
# premia SR0.98/corr+0.016). Of all on-disk sleeves these are the only pair whose addition
# raises champion SR AND MDD (risk) under the ITER15 rule. HF_mom_cheap/_liq (SR~0.9) were
# tested and EXCLUDED: they dilute ann for <0.01 extra SR (see ITER16 research memo).
NEWDATA16 = {
 "A1credit":"campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv",
 "FF2_DUALGATE":"campaign/agents/loop_team/HUNT_FF2/sleeves/FF2_DUALGATE_raw_daily.csv",
}
NAMES = list(POOL) + list(NEW) + list(NEWDATA16)
PATHS = {**POOL, **NEW, **NEWDATA16}

GEAR, RATE, BPS = 1.6, 0.045, 6.4
IS_END = pd.Timestamp('2017-01-01')
P = 0.55          # legacy SR^P exponent — retained for provenance/tests; NOT used for the fit
SHRINK_D = 0.62   # ITER15: covariance shrinkage toward its diagonal (IS rule-selected)
W_MAX = 2.0       # ITER15: per-sleeve cap, in units of the equal weight

def load(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0); df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)

def is_sr(r):
    r = r.dropna()
    if len(r) < 200 or r.std(ddof=1) <= 1e-12:
        return 0.0
    return float(r.mean()/r.std(ddof=1)*np.sqrt(252))


def fit_relw(isr):
    """ITER15 correlation-aware IS weight fit. Deterministic; IS window only.

    Long-only max-Sharpe over the sleeves that have IS coverage, on the IS mean/covariance
    annualised by 252, with the covariance shrunk SHRINK_D toward its diagonal and weights
    capped at W_MAX x equal weight. Sleeves without IS coverage (CFX4) get weight 0, exactly
    as the retired SR^P rule gave them (is_sr -> 0). Returns SHARES summing to 1; absolute
    scale is irrelevant because build() row-normalises d2 before applying GEAR.
    """
    have = [n for n in NAMES if isr[n].notna().sum() > 0]
    X = isr[have].dropna()
    mu = (X.mean() * 252).values
    Sig = X.cov().values * 252
    Sig = (1.0 - SHRINK_D) * Sig + SHRINK_D * np.diag(np.diag(Sig))
    k, sd = len(have), np.sqrt(np.diag(Sig))

    def neg_sharpe(w):
        v = float(np.sqrt(w @ Sig @ w))
        return -(float(w @ mu)) / v if v > 1e-14 else 0.0

    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}]
    bnds = [(0.0, W_MAX)] * k
    best = None
    for w0 in (np.full(k, 1.0/k),
               np.maximum(mu, 0.0) / max(float(np.maximum(mu, 0.0).sum()), 1e-12),
               (1.0/sd) / (1.0/sd).sum()):
        r = minimize(neg_sharpe, w0, method="SLSQP", bounds=bnds, constraints=cons,
                     options={"maxiter": 800, "ftol": 1e-12})
        if r.success and (best is None or r.fun < best.fun):
            best = r
    if best is None:
        raise RuntimeError("ITER15 IS max-Sharpe fit failed to converge — fail closed")
    relw = pd.Series(0.0, index=NAMES)
    relw[have] = best.x
    return relw

def build():
    df = pd.DataFrame({n: load(PATHS[n]).dropna() for n in NAMES})
    df = df[df.index >= '2008-03-31']
    # ITER15: correlation-aware IS weight fit (deterministic, IS-only). Replaces the retired
    # SR^P heuristic, which ignored the covariance matrix. See fit_relw() and the docstring.
    isr = df[df.index < IS_END]
    relw = fit_relw(isr)
    # NAV-drift weights * relw, row-normalized to sum K, scaled to gross.
    # T+1 CAUSAL (AUDIT_CHAMP2 R1 re-emit wave, coordinator-approved): weights at day t are
    # formed from NAV through day t-1 ONLY (nav.shift(1)). The prior construction used
    # nav_t = cumprod(1+r)_t which contains r_t, letting day-t weights earn on day-t returns
    # (same-day leak, corr(dW_t,r_t)=0.78; honest ann 39.85% vs leaked 40.84%).
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(NAMES)
    Wg = d2 * (GEAR / len(NAMES))
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    # One-side turnover = FULL |dW| (TRADE_RECORD_STANDARD: qty_notional=|position change|).
    # No 0.5 half-turn factor (audit A1: 0.5x was a BLOCKING undercharge 41.7% of champion cost
    # rate). Charged at full BPS=6.4 one-side on all turnover.
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    net = (pd.Series(port, index=df.index)
           - to * BPS/1e4
           - np.maximum(GEAR-1, 0)*RATE/252)
    gross = Wg.abs().sum(axis=1)
    return net, relw, gross, to, df

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else '--verify'
    net, relw, gross, to, _ = build()
    if mode == '--emit':
        net.to_frame('ret').to_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW14v2_WEIGHTED_GEAR16_daily.csv")
        relw.to_frame('relw').to_csv(f"{ROOT}/campaign/results/RAWEW14v2_IS_SR_weights.csv")
        print("emitted champion + weights")
        return
    # --verify: compare to committed files
    champ_path = f"{ROOT}/campaign/results/GOAL100_RAWEW14v2_WEIGHTED_GEAR16_daily.csv"
    wgt_path = f"{ROOT}/campaign/results/RAWEW14v2_IS_SR_weights.csv"
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
    # turnover in bp/yr: mean|dW|/day * 252 * 6.4bp (AUDIT_CHAMP2: prior print was
    # percent/yr mislabeled 'bps/yr' -- 0.0494 shown where true figure is 4.935bp/yr)
    print(f"turnover {to.mean()*252*BPS:.4f} bp/yr  margin {np.maximum(GEAR-1,0)*RATE*100:.2f}%/yr")

if __name__ == "__main__":
    main()
