#!/usr/bin/env python3
"""GOAL100 CHAMPION — canonical build script (v1.0, frozen 2026-09-01).

Regenerates ALL THREE champion return series from the 16 validated sleeve files:
  campaign/results/GOAL100_CHAMPION_daily.csv            (SAFE,    config A)
  campaign/results/GOAL100_CHAMPION_AGGRESSIVE_daily.csv (AGGRESSIVE, config B)
  campaign/results/GOAL100_CHAMPION_BALANCED_daily.csv   (BALANCED, headline: 50/50 A+B)

Construction (trailing-only everywhere; T+1; no lookahead):
  1. per sleeve: scale_t = clip(0.10 / vol_t, <=8), vol_t = std(60d trailing).shift(1)
     => sleeve contribution r_i * scale_i  (scale NaN -> 0, warmup)
  2. blend_t = mean_i( r_i*scale_i )                      (plain EW, 1/16 each)
  3. global:   b_t = blend_t * clip(TGT / volblend_t, <=8), volblend = std(60d).shift(1)
  4. throttle: trailing 126d rolling max of b-equity, shifted 1 day;
               if trailing DD < -THR: exposure x 0.5   (switch cost charged)
  5. costs:    6bps one-side on (0.5 * sum_i |d(s_i|16)|) + 0.5*|d(throttle)|
  6. config A: TGT=0.085 THR=0.04   (IS margin rule, GOAL80-frozen throttle family)
     config B: TGT=0.11  THR=0.03   (C4 IS rule: max IS SR s.t. IS DD<=8% & every
                                      IS calendar-year DD<=8%; argmax stable for
                                      IS-ends 2016/2019/2022/2023)
     BALANCED: 0.5*(A + B) daily average.
Weight sum: EW of 16 sleeves with vol-normalization = capital allocated 1/16 per sleeve;
scale>1 on low-vol sleeves mirrors vol-targeting (see VERIFICATION.md for the gross-
exposure/financing disclosure — charged-free convention consistent with GOAL80).

Usage:  python3 campaign/scripts/champion_build.py [--verify]
--verify: compares regenerated CSVs byte-wise to the committed ones and prints stats.
"""
import sys, json
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
COST = 6 / 10000

POOL = {
 "H21_f5":  "tools/quant/reports/xgb_horizons/h21_book_daily_f5.csv",
 "H21_br":  "tools/quant/reports/xgb_horizons/h21_breadth_gate_daily.csv",
 "A5r7":    "campaign/agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv",
 "a6r7":    "campaign/agents/A6_reversal/sleeves/a6_r7_bond2y_trend.csv",
 "A1inf":   "campaign/agents/A1_trend_cta/sleeves/A1_infl_breadth_mom.csv",
 "QAxasts": "campaign/agents/A3_xs_quality/sleeves/QA_xasts_tsmom189.csv",
 "A5r2":    "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 "A1credit":"campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv",
 "XGB1y":   "campaign/results/sleeve_library/XGB1y_deploy.csv",
 "dualmom": "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
 "carryv2": "campaign/agents/A1_trend_cta/sleeves/A1_carry_seasonal_v2.csv",
 "A5r4":    "campaign/agents/A5_vol_cond/sleeves/A5_r4_vt15_contango.csv",
 "brwt":    "campaign/agents/B2_highfreq/sleeves/brwt_spread_rev15.csv",
 "B3momhml":"campaign/agents/B3_antiregime/ref_momhml_composite.csv",
 "C5ng":    "campaign/agents/C5_newdata/sleeves/C5_ng_weekday_prem.csv",
 "C5ngsum": "campaign/agents/C5_newdata/sleeves/C5_ng_summer_weekday.csv",
}

def load(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)

def vt(r, tgt, min_win=60, cap=8.0):
    vol = r.rolling(min_win).std().shift(1) * np.sqrt(252)   # trailing only (T+1)
    s = (tgt / vol).clip(upper=cap)
    s[vol.isna()] = 0
    return r * s.fillna(0), s

def construct(TGT, THR, FR=0.5, LB=126):
    V, S = {}, {}
    for n, p in POOL.items():
        r = load(p)
        v, s = vt(r, 0.10)
        V[n] = v; S[n] = s
    Vn = pd.DataFrame(V); Sn = pd.DataFrame(S)
    W = Sn.div(Sn.sum(axis=1), axis=0).fillna(0)      # turnover-accounting weights
    blend = Vn.mean(axis=1)                            # plain EW of normalized returns
    blend = blend[blend.index >= "2008-09-01"]
    tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)    # one-side turnover (frac of NAV)
    b, _ = vt(blend, TGT)                              # global vol target
    eq = (1 + b.fillna(0)).cumprod()
    rm = eq.rolling(LB).max().shift(1)                 # trailing peak (shift 1)
    tdd = eq.shift(1) / rm - 1                         # trailing DD (shift 1)
    sc = pd.Series(np.where(tdd < -THR, FR, 1.0), index=b.index)
    b = b * sc
    dsc = sc.diff().abs() * 0.5                        # throttle switching turnover
    tot = tw.reindex(b.index).fillna(0) + dsc.fillna(0)
    return (b - tot * COST).dropna()

def stats(r):
    eq = (1 + r).cumprod(); dd = (eq / eq.cummax() - 1).min()
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    o = r[r.index >= "2017-01-01"]
    return dict(ann=round(r.mean()*252*100, 1), sr=round(r.mean()/r.std()*np.sqrt(252), 2),
                mdd=round(dd*100, 1), negy=int((yr < 0).sum()), worst=round(yr.min()*100, 1),
                oos_ann=round(o.mean()*252*100, 1),
                oos_sr=round(float(o.mean()/o.std()*np.sqrt(252)), 2),
                oos_mdd=round(( (1+o).cumprod()/ (1+o).cumprod().cummax() - 1).min()*100, 1))

def main(verify=False):
    A = construct(0.085, 0.04)
    B = construct(0.11, 0.03)
    BAL = ((A + B) / 2).dropna()
    outs = {
        "GOAL100_CHAMPION_daily.csv": A,
        "GOAL100_CHAMPION_AGGRESSIVE_daily.csv": B,
        "GOAL100_CHAMPION_BALANCED_daily.csv": BAL,
    }
    for fn, r in outs.items():
        path = f"{ROOT}/campaign/results/{fn}"
        old = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
        j = pd.concat([old.rename("old"), r.rename("new")], axis=1, join="inner").dropna()
        md = float((j.old - j.new).abs().max())
        if verify:
            print(f"{fn}: max|new-old| = {md:.3e}  n={len(j)}  {'IDENTICAL' if md < 1e-12 else 'DIFF'}")
            print(f"   stats: {stats(r)}")
        else:
            r.to_frame("ret").to_csv(path)
            print(f"wrote {path} n={len(r)}")
    if not verify:
        json.dump({"pool": list(POOL), "A": "vt.085 thr.04 fr.5 lb126",
                   "B": "vt.11 thr.03 fr.5 lb126",
                   "A_stats": stats(A), "B_stats": stats(B), "BAL_stats": stats(BAL)},
                  open(f"{ROOT}/campaign/results/GOAL100_CHAMPION.json", "w"), indent=1)
        print("wrote GOAL100_CHAMPION.json")

if __name__ == "__main__":
    main(verify="--verify" in sys.argv)
