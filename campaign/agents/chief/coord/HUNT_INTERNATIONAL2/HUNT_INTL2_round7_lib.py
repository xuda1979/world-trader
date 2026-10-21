"""HUNT_INTERNATIONAL2 ROUND 7 audit library — MY OWN implementations for the CAMP_COST-R6
HOBR adoption-study audit (charter R7a). Nothing imported from rawew13v2_build /
rawew14_candidate / adoption_study (the modules under audit); the only shared dependencies
are (i) the raw sleeve CSVs on disk (sha-pinned identical for both sides) and (ii) bt.engine
cost helpers (the framework's TRADE_RECORD_STANDARD implementations, themselves test-pinned).

Conventions from GATES_CONTRACT_V2 + the committed-champion construction:
  - relw_i = max(IS_SR_i, 0)^0.55 on the IS window < 2017-01-01.
  - NAV-drift weights row-normalized to K columns then scaled to gross exactly 1.6;
    T+1 causal via nav.shift(1) (weights at t see NAV through t-1 only).
  - book costs: FULL |dW| one-side at 6.4bps + 4.5%/yr margin on (gross-1); sleeve files
    carry their own borrow (champion builder convention).
  - ann = CAGR on 252-day years; MDD on compounded NAV; halves split at n//2.
  - leak probe: |corr0|>=0.20 AND Fisher p<0.05 AND lag-0 argmax (V2 s6b), own code.
"""
from __future__ import annotations

from math import erfc, sqrt

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"

ANN = 252.0
GEAR, RATE, BPS = 1.6, 0.045, 6.4
IS_END = pd.Timestamp("2017-01-01")
P = 0.55
START = "2008-03-31"

SLEEVES13 = {
    "brwt15": "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
    "brwt10": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv",
    "brwt7": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv",
    "brwt5": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv",
    "C5ng": "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
    "C5ngsum": "campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
    "A5r2": "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
    "a6r7": "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
    "QAxasts": "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
    "carryv2": "campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
    "dualmom": "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
    "diescrack": "campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
    "CFX4": "campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
}
HOBR = "campaign/team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv"
NAMES13 = list(SLEEVES13)
NAMES14 = NAMES13 + ["RB_hobr"]

# HOBR sleeve generator constants (RES_BASIS/hunt_r1.py, disclosed in the sleeve .meta)
VT_TARGET, VT_CAP = 0.08, 3.0
GAL_PER_BBL = 42.0


# ---------------------------------------------------------------- data + metrics (own)

def load_ret(path):
    s = pd.read_csv(f"{ROOT}/{path}", index_col=0, parse_dates=True)
    col = "ret" if "ret" in s.columns else s.columns[0]
    s = s[col].astype(float)
    return s[~s.index.duplicated(keep="last")].sort_index()


def sr_d(r) -> float:
    r = pd.Series(r).dropna()
    s = r.std(ddof=1)
    if not len(r) or not np.isfinite(s) or s < 1e-12:
        return 0.0
    return float(r.mean() / s * np.sqrt(ANN))


def stats_own(r) -> dict:
    r = pd.Series(r).dropna()
    nav = (1 + r).cumprod()
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    return {
        "n": int(len(r)), "start": str(r.index[0].date()), "end": str(r.index[-1].date()),
        "ann_cagr_pct": float(((1 + r).prod() ** (ANN / len(r)) - 1) * 100),
        "sr": sr_d(r), "mdd_pct": float((nav / nav.cummax() - 1).min() * 100),
        "neg_years": int((yr < 0).sum()), "worst_year_pct": float(yr.min() * 100),
        "n_years": int(len(yr)),
    }


def halves_sr_own(r) -> tuple:
    r = pd.Series(r).dropna()
    k = len(r) // 2
    return sr_d(r.iloc[:k]), sr_d(r.iloc[k:])


def mdd_own(r) -> float:
    r = pd.Series(r).dropna()
    nav = (1 + r).cumprod()
    return float((nav / nav.cummax() - 1).min())


def neg_years_own(r) -> int:
    r = pd.Series(r).dropna()
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    return int((yr < 0).sum())


def ann_cagr_own(r) -> float:
    r = pd.Series(r).dropna()
    return float(((1 + r).prod() ** (ANN / len(r)) - 1) * 100)


def is_sr_own(r) -> float:
    r = pd.Series(r).dropna()
    if len(r) < 200 or r.std(ddof=1) <= 1e-12:
        return 0.0
    return sr_d(r)


# ---------------------------------------------------------------- book builders (own)

def _book_from_frame(frame: pd.DataFrame, relw: pd.Series):
    """Champion algebra: nav.shift(1) causal NAV-drift weights, row-normalized to K, scaled
    to gross exactly 1.6; costs FULL |dW| @6.4bps + 4.5%/yr margin on (1.6-1)."""
    nav = (1 + frame.fillna(0)).cumprod().shift(1).fillna(1.0)
    K = frame.shape[1]
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * K
    Wg = d2 * (GEAR / K)
    port = (frame.fillna(0).values * Wg.values).sum(axis=1)
    to = Wg.diff().abs().sum(axis=1).fillna(0.0)
    net = (pd.Series(port, index=frame.index) - to * BPS / 1e4
           - max(GEAR - 1, 0) * RATE / ANN)
    gross = Wg.abs().sum(axis=1)
    return net, relw, gross, to, Wg


def _frame(names):
    df = pd.DataFrame({n: load_ret(SLEEVES13.get(n, HOBR)).dropna() for n in names})
    return df[df.index >= START]


def solve_relw(frame: pd.DataFrame) -> pd.Series:
    isr = frame[frame.index < IS_END]
    return pd.Series({n: max(is_sr_own(isr[n]), 0.0) ** P for n in frame.columns})


def build13_own():
    """My 13-slot champion rebuild: (net, relw, gross, to, df)."""
    df = _frame(NAMES13)
    return _book_from_frame(df, solve_relw(df))


def build14_own(weights=False):
    """My 14-slot re-solve (HOBR as 14th slot): (net, relw, gross, to, df[, Wg])."""
    df = _frame(NAMES14)
    net, relw, gross, to, Wg = _book_from_frame(df, solve_relw(df))
    return (net, relw, gross, to, df, Wg) if weights else (net, relw, gross, to, df)


# ---------------------------------------------------------------- delta stats (own)

def delta_stats(net14, net13) -> dict:
    champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                        index_col=0, parse_dates=True).iloc[:, 0].astype(float)
    jj = pd.concat([champ.rename("c13"), net14.rename("c14")], axis=1, join="inner").dropna()
    s13, s14 = stats_own(jj.c13), stats_own(jj.c14)
    mid = jj.index[len(jj) // 2]
    is_m = jj.index < IS_END
    out = {
        "dSR": s14["sr"] - s13["sr"],
        "dAnn_pp": s14["ann_cagr_pct"] - s13["ann_cagr_pct"],
        "dMDD_pp": s14["mdd_pct"] - s13["mdd_pct"],
        "neg_years_c14": s14["neg_years"],
        "dSR_H1_byhalf": sr_d(jj.c14[jj.index < mid]) - sr_d(jj.c13[jj.index < mid]),
        "dSR_H2_byhalf": sr_d(jj.c14[jj.index >= mid]) - sr_d(jj.c13[jj.index >= mid]),
        "c14_is_sr": sr_d(jj.c14[is_m]), "c14_oos_sr": sr_d(jj.c14[~is_m]),
        "c13_is_sr": sr_d(jj.c13[is_m]), "c13_oos_sr": sr_d(jj.c13[~is_m]),
    }
    return out


# ---------------------------------------------------------------- HOBR sleeve rebuild (own)

def hobr_sleeve_rebuild_own():
    """Rebuild RB_hobr_crack_hyst_w63_z10_zo10 from source prices with MY OWN code (signal
    spec from the published .meta: log(HO*42/Brent) z63 trailing-shift(1), hysteresis
    z_in=1.0/z_out=1.0 meanrev, T+1, vt 0.08 trailing cap 3 on gross, 6.4bps full |dW| +
    0.5%/yr borrow). Returns (net, gross_path)."""
    ho = load_ret("tools/quant/data/newdata/DHOILNYH.csv")
    br = load_ret("tools/quant/data/newdata/DCOILBRENTEU.csv")
    j = pd.concat({"a": ho * GAL_PER_BBL, "b": br}, axis=1).dropna()
    j = j[(j > 0).all(axis=1)]
    j = j[j.index >= "2008-01-01"]
    sp = np.log(j["a"] / j["b"])

    # zscore_trailing: rolling(63, min_periods=31) stats, shifted 1
    m = sp.rolling(63, min_periods=31).mean().shift(1)
    s = sp.rolling(63, min_periods=31).std().shift(1)
    z = (sp - m) / s.replace(0, np.nan)

    # hysteresis_state(z, 1.0, 1.0)
    st = np.zeros(len(z))
    cur = 0.0
    for i, zv in enumerate(z.values):
        if not np.isfinite(zv):
            st[i] = cur
        elif cur == 0.0:
            if zv > 1.0:
                cur = 1.0
            elif zv < -1.0:
                cur = -1.0
            st[i] = cur
        elif cur == 1.0 and zv < 1.0:
            cur = 0.0
            st[i] = cur
        elif cur == -1.0 and zv > -1.0:
            cur = 0.0
            st[i] = cur
        else:
            st[i] = cur
    st = pd.Series(st, index=z.index)[z.notna()]  # warmup rows (z NaN) never trade

    idx = st.index
    # meanrev: W = [-st, +st]; T+1 via shift(1)
    W = pd.DataFrame({"a": -st, "b": st}, index=idx)
    We = W.shift(1).fillna(0.0)
    r_a = j["a"].reindex(idx).pct_change().fillna(0.0)
    r_b = j["b"].reindex(idx).pct_change().fillna(0.0)
    R = pd.concat({"a": r_a, "b": r_b}, axis=1)
    gross_raw = (We * R.fillna(0.0)).sum(axis=1)  # vt operates on this gross path

    # vol_target_scale (bt.engine semantics, reimplemented): expanding(60) std of the gross
    # path, target/vol clipped [0.2, cap], shift(1), fillna(1.0)
    vols = gross_raw.expanding(min_periods=60).std(ddof=1) * np.sqrt(ANN)
    scale = (VT_TARGET / vols.replace(0.0, np.nan)).clip(upper=VT_CAP).clip(lower=0.2)
    scale = scale.shift(1).fillna(1.0)
    Wv = We.mul(scale, axis=0)

    port = (Wv * R.fillna(0.0)).sum(axis=1)
    prev = Wv.shift(1)
    prev.iloc[0] = 0.0
    cost = (Wv - prev).abs().sum(axis=1) * 6.4 / 1e4
    borr = (-Wv.clip(upper=0.0)).sum(axis=1) * 0.005 / ANN
    net = (port - cost - borr).rename("ret")
    gross = Wv.abs().sum(axis=1)
    return net, gross


# ---------------------------------------------------------------- fill-0 blend (own)

def fill0_blend(net13, net_h, gross_h, w) -> dict:
    """The standup convention: champ + w*sleeve RETURNS (sleeve zero where champ has no
    data), UNRELEVERED -> book gross = 1.6 + w*sleeve_gross (the 8e breach check)."""
    net13 = pd.Series(net13).dropna()
    nh = pd.Series(net_h).reindex(net13.index).fillna(0.0)
    gh = pd.Series(gross_h).reindex(net13.index).fillna(0.0)
    blend = net13 + w * nh
    s13 = stats_own(net13)
    s = stats_own(blend)
    return {
        "dAnn_pp": s["ann_cagr_pct"] - s13["ann_cagr_pct"],
        "dSR": s["sr"] - s13["sr"],
        "dMDD_pp": s["mdd_pct"] - s13["mdd_pct"],
        "neg_years": s["neg_years"],
        "book_gross_mean": 1.6 + w * float(gh.mean()),
        "blend_n": s["n"],
    }


# ---------------------------------------------------------------- rung grid (own)

def rung_grid_capital_real(rungs=(0.05, 0.10, 0.15)) -> list:
    """Capital-real rungs: scale HOBR's relw so the book's MEAN HOBR gross-share ~= w,
    iterate the share calibration 3x (their convention), full re-solve algebra, delta vs
    the committed champion."""
    df = _frame(NAMES14)
    relw14 = solve_relw(df)
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    # natural-share calibration seed (their convention: share measured on natural weights)
    d2n = nav.div(nav.mean(axis=1), axis=0).mul(relw14, axis=1)
    d2n = d2n.div(d2n.sum(axis=1), axis=0) * 14
    Wg_nat = d2n * (GEAR / 14)
    champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                        index_col=0, parse_dates=True).iloc[:, 0].astype(float)
    rows = []
    for w in rungs:
        fac = w / float((Wg_nat["RB_hobr"] / Wg_nat.abs().sum(axis=1)).mean())
        for _ in range(3):
            rw = relw14.copy()
            rw["RB_hobr"] = relw14["RB_hobr"] * fac
            d2 = nav.div(nav.mean(axis=1), axis=0).mul(rw, axis=1)
            d2 = d2.div(d2.sum(axis=1), axis=0) * 14
            Wg = d2 * (GEAR / 14)
            sh = float((Wg["RB_hobr"] / Wg.abs().sum(axis=1)).mean())
            fac *= w / sh
        port = (df.fillna(0).values * Wg.values).sum(axis=1)
        to = Wg.diff().abs().sum(axis=1).fillna(0.0)
        net = (pd.Series(port, index=df.index) - to * BPS / 1e4 - (GEAR - 1) * RATE / ANN)
        j = pd.concat([champ.rename("c13"), net.rename("r")], axis=1, join="inner").dropna()
        sc, sv = stats_own(j.c13), stats_own(j.r)
        rows.append({
            "w": float(w), "achieved_share": sh,
            "dAnn_pp": sv["ann_cagr_pct"] - sc["ann_cagr_pct"],
            "dSR": sv["sr"] - sc["sr"],
            "dMDD_pp": sv["mdd_pct"] - sc["mdd_pct"],
            "neg_years": sv["neg_years"],
        })
    return rows


# ---------------------------------------------------------------- 8i exclusion (own)

def excl_8i_own(net14, net13) -> dict:
    champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                        index_col=0, parse_dates=True).iloc[:, 0].astype(float)
    jj = pd.concat([champ.rename("c13"), net14.rename("c14")], axis=1, join="inner").dropna()
    nav14 = (1 + jj.c14).cumprod()
    runmax = nav14.cummax()
    trough_date = (nav14 / runmax).idxmin()
    start_loc = int(jj.index.get_loc(runmax[:trough_date].idxmax()))
    peak_val = float(nav14.iloc[start_loc])
    after = nav14.iloc[start_loc + 1:]
    rec = after[after >= peak_val]
    end_loc = int(jj.index.get_loc(rec.index[0])) if len(rec) else len(jj) - 1
    lo, hi = jj.index[start_loc], jj.index[end_loc]
    excl = jj[(jj.index < lo) | (jj.index > hi)]
    d = (mdd_own(excl.c14) - mdd_own(excl.c13)) * 100
    return {
        "window": (str(lo.date()), str(hi.date())),
        "trough_date": str(trough_date.date()),
        "window_days": int(end_loc - start_loc + 1),
        "dMDD_pp_excl": float(d),
        "relief_ge_0.5pp": bool(d >= 0.5),
        "dMDD_pp_full": (mdd_own(jj.c14) - mdd_own(jj.c13)) * 100,
    }


# ---------------------------------------------------------------- gross-neutral blend (own)

def gross_neutral_blend(net13, w) -> float:
    """Capital-real gross-neutral delevered blend: (1-w)*champ-book + w*HOBR-as-own-book,
    both at gross 1.6 -> total gross 1.6. Returns dAnn_pp (negative = 8c fail)."""
    champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                        index_col=0, parse_dates=True).iloc[:, 0].astype(float)
    net14, _, _, _, _ = build14_own()
    jj = pd.concat([champ.rename("c13"), net14.rename("c14")], axis=1, join="inner").dropna()
    blend = (1 - w) * jj.c13 + w * jj.c14
    return ann_cagr_own(blend) - ann_cagr_own(jj.c13)


# ---------------------------------------------------------------- leak probes (own)

def _fisher_p(c, n):
    if not np.isfinite(c) or n < 3:
        return np.nan
    if abs(c) >= 1.0:
        return 0.0
    t = c * sqrt((n - 2) / (1 - c * c))
    return erfc(abs(t) / sqrt(2))


def leak_probe_scalar_own(score, ret) -> dict:
    s = pd.Series(score).astype(float)
    r = pd.Series(ret).astype(float)
    j = pd.concat([s.rename("s"), r.rename("r")], axis=1).dropna()
    n = len(j)
    if n < 30 or j.s.std(ddof=1) <= 0 or j.r.std(ddof=1) <= 0:
        return dict(measurable=False, leak=np.nan, same_period_corr=np.nan,
                    same_period_p=np.nan, lag_scan={}, argmax_lag=None)
    c0 = float(j.s.corr(j.r))
    p0 = _fisher_p(c0, n)
    lag_scan = {}
    for lag in (-2, -1, 0, 1, 2):
        rr = r.shift(-lag) if lag != 0 else r
        jj = pd.concat([s.rename("s"), rr.rename("r")], axis=1).dropna()
        lag_scan[lag] = float(jj.s.corr(jj.r)) if len(jj) >= 30 else np.nan
    others = [abs(v) for k, v in lag_scan.items() if k != 0 and np.isfinite(v)]
    argmax = max(lag_scan, key=lambda k: abs(lag_scan[k])) if others else 0
    leak = bool(np.isfinite(c0) and np.isfinite(p0) and abs(c0) >= 0.20 and p0 < 0.05
                and abs(c0) >= max(others))
    return dict(measurable=True, leak=leak, same_period_corr=c0, same_period_p=p0,
                lag_scan=lag_scan, argmax_lag=int(argmax))


def leak_probe_wide_own(Wg, R) -> dict:
    """AUDIT_RECON statistic: per-day cross-sectional corr(dW_i, r_i), averaged over days,
    at lags -2..+2. Convention matches bt.leakcheck (finite mask, >=3 valid, both stds>0,
    np.corrcoef, mean of daily corr, p from a t-stat of the daily-corr mean); verdict as in
    V2 s6b with the lag-0-argmax leg."""
    Wg = pd.DataFrame(Wg)
    R = pd.DataFrame(R).reindex(Wg.index)
    dW = Wg.diff()

    def xsec(lag):
        rr = R.shift(-lag) if lag != 0 else R
        cs = []
        for i in range(len(dW)):
            a = dW.iloc[i].to_numpy(dtype=float)
            b = rr.iloc[i].to_numpy(dtype=float)
            m = np.isfinite(a) & np.isfinite(b)
            a, b = a[m], b[m]
            if len(a) >= 3 and a.std() > 0 and b.std() > 0:
                cs.append(float(np.corrcoef(a, b)[0, 1]))
        return cs

    per_day = {lag: xsec(lag) for lag in (-2, -1, 0, 1, 2)}
    lag_scan = {lag: float(np.mean(v)) for lag, v in per_day.items() if v}
    c0 = lag_scan[0]
    others = [abs(v) for k, v in lag_scan.items() if k != 0 and np.isfinite(v)]
    argmax = max(lag_scan, key=lambda k: abs(lag_scan[k]))
    v0 = np.asarray(per_day[0], dtype=float)
    n_days = len(v0)
    sd0 = v0.std(ddof=1)
    t0 = float(v0.mean() / (sd0 / sqrt(n_days))) if sd0 > 0 else np.nan
    p0 = erfc(abs(t0) / sqrt(2)) if np.isfinite(t0) else np.nan
    leak = bool(np.isfinite(c0) and np.isfinite(p0) and abs(c0) >= 0.20 and p0 < 0.05
                and abs(c0) >= max(others))
    return dict(measurable=True, leak=leak, same_period_corr=c0, same_period_p=p0,
                lag_scan=lag_scan, argmax_lag=int(argmax), n_days=n_days)
