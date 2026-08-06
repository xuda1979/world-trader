"""HIGH-SHARPE PORTFOLIO from successful replicated strategies @ 3.8 bps.

Directive 2026-08-06 (keep research): replicate best published strategies and
assemble a high-Sharpe DE PL portfolio out of the SUCCESSFUL (positive-OOS,
meaningful-history) legs at 3.8 bps one-side (costs embedded in each stream).

Honest rules (no selection bias):
  - Gate: keep a leg only if it has (a) >= 250 bars of full-sample OOS AND
    (b) full-sample Sharpe > 0 (it survives realistic cost).
  - Combine on common overlap with equal-weight (no params) and inverse-vol
    risk-parity; report split-half to expose regime dependence.
"""
import os
import pandas as pd, numpy as np
ROOT="/Users/daxu/software/world-trader"; RES=os.path.join(ROOT,"tools/quant/ls/results")
TD=252; MIN_BARS=250

# candidate legs: label -> (path, dataframe-column)
CAND = {
 "LS_GBRT": (os.path.join(RES,"live_signal/daily_returns.csv"), "daily_return"),
 "tsmom":   (os.path.join(RES,"cross_asset_tsmom/daily_real.csv"), "daily_return"),
 "gold":    (os.path.join(RES,"gold_trend/daily_real.csv"), "daily_return"),
 "fx":      (os.path.join(RES,"fx_momentum/daily_real.csv"), "daily_return"),
 "etf_mom": (os.path.join(RES,"etf_xs/daily_mom_real.csv"), "daily_return"),
 "RV_h10":  (os.path.join(RES,"rv2_h10_n13/daily_returns.csv"), "daily_return"),
 "WINNER_LS":(os.path.join(RES,"WINNER_rev3_n13/daily_returns.csv"), "daily_return"),
}

def sharpe(r):
    r=r.dropna()
    return (r.mean()/r.std())*np.sqrt(TD) if len(r)>30 and r.std()>0 else np.nan

def load():
    streams={}
    for k,(p,c) in CAND.items():
        if not os.path.exists(p): print(f"[skip] {k}: missing {p}"); continue
        df=pd.read_csv(p,parse_dates=[0],index_col=0)
        col=c if c in df.columns else df.columns[0]
        r=df[col].dropna()
        streams[k]=r
    return streams

def main():
    S=load()
    print("Leg screening (full-history, cost embedded @3.8bps):")
    print(f"{'leg':10s} {'n':>5s} {'start':>10s} {'Sharpe':>7s} {'gate':>8s}")
    # SCRAMBLE-VALIDATED gate (2026-08-06): a leg must beat a price-lag noise
    # control (cointegration/momentum destroyed) to qualify as real alpha.
    # Multi-seed tests: tsmom/gold/fx fail (P(null>real)~44-52%), pairs fail
    # (scrambled SR 4.0-4.8 ~ real 6.96). Only LS_GBRT (deep 8y walk-forward
    # IC/ICIR validated, overfitting_flags=[]) qualifies today.
    SCRAMBLE_OK = {"LS_GBRT"}
    passed={}
    for k,r in sorted(S.items()):
        s=sharpe(r)
        sc_ok = k in SCRAMBLE_OK
        ok = len(r)>=MIN_BARS and not np.isnan(s) and s>0 and sc_ok
        flag=("VALID" if sc_ok else "no-scramble") if ok else ("short" if len(r)<MIN_BARS else
              ("no-scramble" if not sc_ok else "sh<=0"))
        print(f"{k:10s} {len(r):5d} {str(r.index.min().date()):>10s} {s:7.2f} -> {flag:>8s}")
        if ok: passed[k]=r
    if len(passed)<2:
        print("\nFewer than 2 scramble-validated legs => cannot build an honest high-Sharpe")
        print("multi-leg portfolio from current candidates. All non-LS legs (tsmom/gold/fx/")
        print("etf_mom/pairs/WINNER-LS-variants) fail a price-lag noise control; their high")
        print("raw Sharpe is regime/market-beta artifact, NOT robust alpha.")
        print("Requirement: acquire genuinely independent, scramble-validated alpha legs")
        print("(true cross-sectional stat-arb, long/short factor probes that beat noise).")
        return

    A=pd.DataFrame(passed).dropna()
    print(f"\nSurviving successful legs combined on common window: "
          f"{A.shape[0]}d ({A.index.min().date()}..{A.index.max().date()})")
    print("\nCorrelation:")
    print(A.corr().round(2).to_string())

    ev=A.mean(axis=1)
    vols=A.std(); rpw=(1/vols)/(1/vols).sum()
    rp=pd.Series(A.values@rpw.values,index=A.index)
    print("\n"+"-"*72)
    for nm,s in [("equal-weight (1/N)",ev),("risk-parity (inv-vol)",rp)]:
        sh=sharpe(s); ann=(1+s).prod()**(TD/len(s))-1
        eq=(1+s).cumprod(); dd=(eq/eq.cummax()-1).min()
        h=len(s)//2
        print(f"  {nm:22s} Sharpe {sh:6.2f} | AnnRet {ann:6.1%} | MaxDD {dd:6.1%} "
              f"| split-half {sharpe(s.iloc[:h]):5.2f}/{sharpe(s.iloc[h:]):5.2f} | n={len(s)}")

    best_nm = "equal-weight (1/N)"
    best = ev
    # deployable vol-target to 8%
    rv=best.rolling(60).std()*np.sqrt(TD); sc=(0.08/rv.shift(1)).fillna(1).clip(0,10)
    bvt=best*sc
    print(f"\nRecommended book: {best_nm} (no params). Vol-targeted to 8%: "
          f"Sharpe {sharpe(bvt):.2f} | AnnRet {(1+bvt).prod()**(TD/len(bvt))-1:.1%}")
    out=pd.DataFrame({"date":bvt.index,"ret":bvt.values})
    od=os.path.join(RES,"high_sharpe_portfolio"); os.makedirs(od,exist_ok=True)
    out.to_csv(os.path.join(od,"recommended_book_vt8.csv"),index=False)
    print(f"saved -> {od}/recommended_book_vt8.csv")

if __name__=="__main__":
    main()
