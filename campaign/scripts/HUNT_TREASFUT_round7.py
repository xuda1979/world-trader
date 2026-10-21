#!/usr/bin/env python3
"""HUNT_TREASFUT ROUND 7 — ECB SDMX euro-area AAA yield-curve family (charter corner).

Corner (coordinator pre-registration, R7 standup 2026-09-08 18:3x): NEW data source —
ECB SDMX, dataflow YC, series B.U2.EUR.4F.G_N_A.SV_C_YM.SR_<T> = euro-area AAA-rated
government bond spot par yields, daily, 2004-09-06..2026-09-07 (n=5625 per tenor,
zero blanks; sha16 pinned in work_r7/yields/manifest.json). Publication: ECB publishes
the AAA curve the same business day (~18:00 CET) => PIT rule = decision may use prints
up to and including (decision_date - 1 business day). Weekly (Wednesday) rebalance.

Family (conventions pinned a-priori, NO sweep):
  slope  = y10 - y2            -> DV01-neutral steepener weights w2=+1/DUR2, w10=-1/DUR10
  fly    = y10 - 0.5(y2 + y30) -> DV01-neutral weights -0.5/DUR2, +1/DUR10, -0.5/DUR30
  signal = sign(delta_k), k=63 business days (one quarter — the weekly-cadence class
           analogue of the R1/R2 k=63; NOT chosen from any scan) — momentum variant;
           the SIGN-FLIPPED reversion variant is reported as the pre-registered control.
  book   = weekly decision weights, daily-held; T+1 shift; VT 10% ann expanding clip 3.0;
           costs 6.4bps FULL |dW| + 0.5%/yr borrow on shorts.
Decorrelation: |corr| < 0.15 vs champion (0.15-0.35 = secondary); watch corr to a6r7
bond-2y trend (0.15/0.35) and A1credit. Mandatory sub-span stability: pre-2010,
2010-2013, post-2010, post-2013 — a post-2013-only effect is a FAIL with the number.
"""
import json
import sys

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/campaign")
sys.path.insert(0, f"{ROOT}/campaign/scripts")

import numpy as np
import pandas as pd

import bt.engine as E
import bt.gates as bgates
from bt.metrics import ann_geo, half_split, neg_years, sharpe_d

YC = f"{ROOT}/campaign/agents/chief/coord/HUNT_TREASFUT/work_r7/yields"
OUT = f"{ROOT}/campaign/agents/chief/coord/HUNT_TREASFUT/work_r7"
SLEEVES = f"{ROOT}/campaign/agents/chief/coord/HUNT_TREASFUT/sleeves"
CHAMPP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
A6R7P = f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv"
A1CRP = f"{ROOT}/campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv"
SPYP = f"{ROOT}/tools/quant/data/twelvedata/SPY.csv"
IEFP = f"{ROOT}/tools/quant/data/more_etf/IEF.csv"
CTAP = f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv"

DURS = {"1": 1.0, "2": 1.9, "5": 4.6, "10": 8.5, "30": 19.0}   # campaign modDur convention
K = 63                      # a-priori: 1 quarter of business days
PUB_LAG_BD = 1              # ECB AAA curve same-day ~18:00 CET print => 1 bd PIT lag
COST_BPS = 6.4


# ------------------------------------------------------------------- data ----
def load_yc():
    ys = {}
    for t in ("1Y", "2Y", "5Y", "10Y", "30Y"):
        s = pd.read_csv(f"{YC}/ECBAAA_YC_{t}.csv", index_col=0, parse_dates=True)["yield_pct"]
        ys[t[:-1]] = s.astype(float)
    df = pd.DataFrame(ys).sort_index()
    df = df[~df.index.duplicated(keep="last")]
    return df


def slope(ys):
    return ys["10"] - ys["2"]


def fly(ys):
    return ys["10"] - 0.5 * (ys["2"] + ys["30"])


def fly_weights(durs):
    """DV01-neutral body/wings: +1 body, -0.5 each wing scaled by 1/dur."""
    return {"2": -0.5 / durs["2"], "10": 1.0 / durs["10"], "30": -0.5 / durs["30"]}


# ------------------------------------------------------------ PIT timing ----
def weekly_decisions(v, k=K):
    """v: daily series (yield construct). Returns the k-day change evaluated at WEDNESDAY
    decision dates, using data up to (decision - PUB_LAG_BD business days) — the
    publication-calendar PIT rule."""
    lagged = v.copy()
    lagged.index = lagged.index + pd.offsets.BusinessDay(PUB_LAG_BD)   # print visible T+1bd
    sig = np.sign(lagged.diff(k))
    dec = sig[(sig.index.dayofweek == 2) & sig.notna()]
    return dec


def _weekly_index(ys):
    return pd.date_range(ys.index[0], ys.index[-1], freq="W-WED")


def weights_slope(ys, k=K, sym=True, flip=False):
    d = weekly_decisions(slope(ys), k=k)
    s = d * (-1.0 if flip else 1.0)
    W = pd.DataFrame({"2": s / DURS["2"], "10": -s / DURS["10"]})
    # missing weekly print (ECB holiday WED): HOLD the prior decision (ffill) — a
    # fillna(0) here bakes phantom flat weeks into the book (R7 defect, tests 9/10)
    W = W.reindex(sorted(set(W.index) | set(_weekly_index(ys)))).sort_index().ffill()
    return W.fillna(0.0)


def weights_fly(ys, k=K, flip=False):
    d = weekly_decisions(fly(ys), k=k)
    s = d * (-1.0 if flip else 1.0)
    fw = fly_weights(DURS)
    W = pd.DataFrame({"2": s * fw["2"], "10": s * fw["10"], "30": s * fw["30"]})
    W = W.reindex(sorted(set(W.index) | set(_weekly_index(ys)))).sort_index().ffill()
    return W.fillna(0.0)


# ------------------------------------------------------------ book engine ----
def leg_returns(ys, per_year=252.0):
    """Synthetic TR per DV01 unit: r = -DUR*dy + y/per_year (campaign convention)."""
    R = pd.DataFrame({c: -DURS[c] * ys[c].diff() + ys[c] / per_year for c in ys.columns})
    return R


def book(W, R, vt=True, tplus1=True, target=0.10):
    """W: WEEKLY decision-weight rows. R7 defect fix (tests 9/10, TDD): weekly decisions
    must be HELD daily — W is forward-filled onto R's daily grid BEFORE the T+1 shift.
    (The old code filled non-Wed days with 0.0 => book flat 4512/5625 days, unwind
    costs stranded on flat days, battery feed (sig*r_pu) zeroed them => SR inflated
    0.029 -> 0.121. FXCARRY2-R7 same defect class.)"""
    Wd = W.reindex(index=R.index, columns=R.columns)
    Wd = Wd.ffill().fillna(0.0)          # hold the position daily between decisions
    We = (Wd.shift(1) if tplus1 else Wd).fillna(0.0)
    gross = (We * R.fillna(0.0)).sum(axis=1)
    if vt:
        s = E.vol_target_scale(gross.to_frame("g"), target=target)["g"]
        We = We.mul(s, axis=0)
    port = (We * R.fillna(0.0)).sum(axis=1)
    cost = E.cost_turnover(We, cost_bps=COST_BPS)
    borr = E.borrow_cost(We)
    return (port - cost - borr).rename("ret"), We, gross


# ---------------------------------------------------------------- battery ----
def era_table(net):
    eras = {}
    for lbl, a in (("full", net.index[0]), ("pre2010", "2004-09-06"), ("2010_2013", "2010-01-01"),
                   ("post2010", "2010-01-01"), ("post2013", "2013-10-01"), ("post2015", "2015-01-01")):
        e = net[net.index >= pd.Timestamp(a)] if lbl != "pre2010" else net[net.index < pd.Timestamp("2010-01-01")]
        if lbl == "2010_2013":
            e = net[(net.index >= pd.Timestamp("2010-01-01")) & (net.index < pd.Timestamp("2013-10-01"))]
        eras[lbl] = dict(n=len(e), sr=float(sharpe_d(e)) if len(e) > 1 else float("nan"),
                         ann=float(ann_geo(e)) if len(e) > 1 else float("nan"))
    return eras


def battery(name, net, We, R, champ, a6, a1, spy, ief, cta):
    """Full V2 battery (explicit sig= and leak_check=True per charter) + decorrelation
    vs a6r7/A1credit + era table."""
    held = net.dropna()
    sig = We.abs().sum(axis=1).reindex(held.index).fillna(0.0)
    r_pu = (held / sig.replace(0.0, np.nan)).replace([np.inf, -np.inf], 0.0).fillna(0.0)
    gr = bgates.run(r_pu, ref=champ, sig=sig, leak_check=True, scramble_n=200,
                    beats_passive=True, spy=spy, ief=ief, cta=cta)
    lp = gr.get("leak") or {}
    bp = gr.get("beats_passive") or {}
    c_a6 = float(bgates.corr_to(a6, held))
    c_a1 = float(bgates.corr_to(a1, held))
    h1, h2 = half_split(held)
    neg, worst = neg_years(held)
    eras = era_table(held)
    corr_gate = "primary" if abs(gr["corr"]) < 0.15 else ("secondary" if abs(gr["corr"]) < 0.35 else "FAIL")
    a6_gate = "primary" if abs(c_a6) < 0.15 else ("secondary" if abs(c_a6) < 0.35 else "FAIL")
    out = dict(name=name, n=len(held), start=str(held.index[0].date()), end=str(held.index[-1].date()),
               sr=float(gr["sr"]), ann=float(ann_geo(held)), vol=float(held.std() * np.sqrt(252)),
               h1=float(h1), h2=float(h2), neg_years=int(neg), worst=float(worst),
               corr_champ=float(gr["corr"]), corr_gate=corr_gate, corr_a6r7=c_a6, a6r7_gate=a6_gate,
               corr_a1credit=c_a1, scr_p=float(gr["scr_p"]),
               leak=dict(same_period_corr=float(lp.get("same_period_corr")),
                         same_period_p=float(lp.get("same_period_p")),
                         leak_ok=bool(gr["leak_ok"])),
               beats_passive=dict(ok=bool(gr["beats_passive_ok"]),
                                  best=str(bp.get("best_passive_name")),
                                  best_sr=float(bp.get("best_passive_sr")) if bp.get("best_passive_sr") == bp.get("best_passive_sr") else None),
               v2_pass=bool(gr["pass"]), eras=eras)
    return out, gr


def save(name, net, We, meta):
    net.to_csv(f"{SLEEVES}/{name}.csv")
    We.to_csv(f"{SLEEVES}/{name}_positions.csv")
    with open(f"{SLEEVES}/{name}.meta.json", "w") as fh:
        json.dump(meta, fh, indent=1, default=str)


def main():
    ys = load_yc()
    print(f"ECB AAA curve panel: n={len(ys)} {ys.index[0].date()}..{ys.index[-1].date()} "
          f"cols={list(ys.columns)}")
    R = leg_returns(ys)
    champ = pd.read_csv(CHAMPP, index_col=0, parse_dates=True).iloc[:, 0].astype(float)
    a6 = pd.read_csv(A6R7P, index_col=0, parse_dates=True).iloc[:, 0].astype(float)
    a1 = pd.read_csv(A1CRP, index_col=0, parse_dates=True).iloc[:, 0].astype(float)
    spy = pd.read_csv(SPYP, index_col=0, parse_dates=True)["close"].astype(float).pct_change()
    ief = pd.read_csv(IEFP, index_col=0, parse_dates=True)["close"].astype(float).pct_change()
    cta = pd.read_csv(CTAP, index_col=0, parse_dates=True)["ret"].astype(float)

    results = {}
    for fam, wfun in (("SLOPE", weights_slope), ("CURV", weights_fly)):
        for tag, flip in (("mom", False), ("rev", True)):
            name = f"TREASFUT7_ECB_{fam}_{tag}"
            W = wfun(ys, k=K, flip=flip)
            net, We, _ = book(W, R)
            res, gr = battery(name, net, We, R, champ, a6, a1, spy, ief, cta)
            results[name] = res
            e = res["eras"]
            print(f"\n[{name}] n={res['n']} {res['start']}->{res['end']} SR={res['sr']:.3f} "
                  f"ann={res['ann']*100:.2f}% vol={res['vol']*100:.1f}% H1={res['h1']:.2f} "
                  f"H2={res['h2']:.2f} negyr={res['neg_years']} worst={res['worst']*100:.1f}%")
            print(f"    corrChamp={res['corr_champ']:+.3f}({res['corr_gate']}) "
                  f"corrA6R7={c_a6_disp(res):+.3f}({res['a6r7_gate']}) "
                  f"corrA1CR={res['corr_a1credit']:+.3f} scr_p={res['scr_p']:.3f} "
                  f"leak_ok={res['leak']['leak_ok']} "
                  f"(leak_corr={res['leak']['same_period_corr']:+.3f} p={res['leak']['same_period_p']:.3f}) "
                  f"bp_ok={res['beats_passive']['ok']} vs {res['beats_passive']['best']}"
                  f":{res['beats_passive']['best_sr']} V2pass={res['v2_pass']}")
            print("    eras: " + " | ".join(
                f"{k}: n={v['n']} SR={v['sr']:+.3f}" for k, v in e.items()))
            save(name, net, We, dict(family=f"{fam}_{tag}",
                                     source="ECB SDMX YC B.U2.EUR.4F.G_N_A.SV_C_YM (AAA euro-area govt)",
                                     manifest=f"work_r7/yields/manifest.json",
                                     k=K, pub_lag_bd=PUB_LAG_BD, rebalance="WEEKLY (Wednesday)",
                                     convention="DV01-neutral; sign(delta63); flip=mean-reversion control",
                                     durs=DURS, cost_bps_full_dw=COST_BPS, vt=0.10, clip=3.0,
                                     champion_sha16="4358dfab95679b97", result=res))

    with open(f"{OUT}/r7_ecb_curve_results.json", "w") as fh:
        json.dump(results, fh, indent=1, default=str)
    print("\nsaved ->", f"{OUT}/r7_ecb_curve_results.json")
    return results


def c_a6_disp(res):
    return res["corr_a6r7"]


if __name__ == "__main__":
    main()
