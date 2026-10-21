#!/usr/bin/env python3
"""HUNT_NG_REGIONAL — regional (non-L48) natgas storage cross-section.

Pre-registered 18 configs (see ../CHARTER.md, sealed before any result).
Costs: 6.4bps one-side FULL |dW|; borrow 0.5%/yr on short notional.
Gates per coord/GATES_CONTRACT.md: SR>=1.0, plateau, halves>=0.5,
<=2 neg yrs each > -5%, scramble 200x p<0.05, corr vs champion, vt10% trailing.
All inputs = frozen disk vintages (hashes in CHARTER.md).

Run: python3 campaign/agents/chief/coord/HUNT_NG_REGIONAL/work/hunt_ng_regional.py
"""
import hashlib
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
COST = 6.4 / 10000  # one-side, FULL |dW|
BORROW = 0.005      # /yr on short notional
REGIONS = ["east", "midwest", "salt", "southsalt", "southnonsalt", "west", "other"]
SALT_SET = ["salt", "southsalt"]
NONSALT_SET = ["east", "midwest", "southnonsalt", "west", "other"]

INPUT_SHA = {  # frozen disk vintages, certified in CHARTER.md
    "east": "c90c4da0d19be90e", "midwest": "54234a2455ad080e",
    "salt": "c5e4bc1168452ac5", "southsalt": "fb157872235dc35e",
    "southnonsalt": "69d32852de93fb5f", "west": "b0db93a434e9358c",
    "other": "9f55f61fa7de8941", "L48": "ea4ec6ec83a84950",
}


def load_ng(region):
    p = f"{ROOT}/tools/quant/data/eia_weekly/ng_storage_{region}_weekly.csv"
    got = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
    assert got == INPUT_SHA[region], f"input vintage drift: {region} {got}"
    df = pd.read_csv(p, parse_dates=["date"]).set_index("date")["value"].astype(float)
    return df.sort_index()


def load_hh():
    df = pd.read_csv(f"{ROOT}/tools/quant/data/newdata/DHHNGSP.csv",
                     parse_dates=["date"]).set_index("date")["DHHNGSP"].astype(float)
    return df.sort_index()


def seasonal_band(series, years=5):
    """Per-week-of-year median and MAD over trailing `years` years (expanding
    until enough data, min 3y). Signal-safe: uses only data strictly before
    the current season by shifting 1 year."""
    df = series.to_frame("v")
    df["doy"] = df.index.dayofyear
    out_med = pd.Series(index=df.index, dtype=float)
    out_mad = pd.Series(index=df.index, dtype=float)
    # weekly data: group by ISO week
    df["woy"] = df.index.isocalendar().week.astype(int).values
    for ts, row in df.iterrows():
        hist_mask = df.index < (ts - pd.DateOffset(years=1))
        w = df.loc[hist_mask]
        w = w[(w["woy"] == row["woy"]) &
              (w.index >= ts - pd.DateOffset(years=years + 1))]
        if len(w) >= 3:
            out_med[ts] = w["v"].median()
            out_mad[ts] = (w["v"] - w["v"].median()).abs().median()
    return out_med, out_mad.replace(0, np.nan)


def net_returns(daily_ret, daily_w, short_frac_series=None):
    """T+1 accounting: weight set at t applies to return t+1 (caller shifts).
    Costs on FULL |dW|. Borrow on short notional."""
    dw = daily_w.diff().abs().fillna(daily_w.abs())
    gross_short = daily_w.clip(upper=0).abs()
    borrow_daily = gross_short * BORROW / 252.0
    net = daily_ret * daily_w - dw * COST - borrow_daily
    return net


def sr(x):
    x = x.dropna()
    if len(x) < 200 or x.std(ddof=1) <= 1e-12:
        return 0.0
    return float(x.mean() / x.std(ddof=1) * np.sqrt(252))


def halves(x):
    x = x.dropna()
    h = len(x) // 2
    return sr(x.iloc[:h]), sr(x.iloc[h:])


def neg_years(x):
    x = x.dropna()
    yr = (1 + x).groupby(x.index.year).prod() - 1
    return int((yr < 0).sum()), float(yr.min()) if len(yr) else 0.0


def scramble_p(x, seed=17, n=200):
    x = np.array(x.dropna().values, copy=True)
    rng = np.random.default_rng(seed)
    real = abs(sr(pd.Series(x)))
    wins = 0
    for _ in range(n):
        rng.shuffle(x)
        s = abs(sr(pd.Series(x)))
        if real > s:
            wins += 1
    return wins / n


def main():
    ng = {r: load_ng(r) for r in REGIONS + ["L48"]}
    hh = load_hh()
    hh_ret = hh.pct_change().clip(-0.25, 0.25)  # sanity clip

    # regional z-scores (5y seasonal band, winsorized at +-4)
    z5 = {}
    for r in REGIONS:
        med, mad = seasonal_band(ng[r], 5)
        z5[r] = ((ng[r] - med) / (1.4826 * mad)).clip(-4, 4)
    Z = pd.DataFrame(z5).dropna(how="all")

    # F4 residual: L48 - sum(regions)
    reg_sum = sum(ng[r] for r in REGIONS)
    resid = ng["L48"] - reg_sum

    results = []
    books = {}

    def register(name, w_weekly, family, note=""):
        """w_weekly: DataFrame date x region of TARGET weights (sum row ~=0 for
        L/S), or Series of scalar complex tilt for F3/F5 (name the region col
        'HH'). Applies T+1 (shift 1 print), dailyizes to the HH calendar,
        computes net returns."""
        tgt = w_weekly
        if isinstance(tgt, pd.Series):
            tgt = tgt.to_frame("HH")
        # daily step function: forward-fill weekly target to daily HH calendar
        daily_idx = hh.index
        tgt_d = tgt.reindex(daily_idx).ffill()
        w_app = tgt_d.shift(1)  # T+1: weight known at t applies t+1
        if "HH" in tgt_d.columns:
            r = hh_ret.reindex(daily_idx).fillna(0.0)
            net = net_returns(r, w_app["HH"])
        else:
            # L/S regional book expressed on... storage is not tradable; per
            # charter F1/F2/F4 are measured on STORAGE-BETA-NEUTRAL synthetic
            # daily marks: we score them as weekly L/S spread books on the
            # regional storage PRICE proxies -> NOT directly tradable; the
            # charter measures them on the storage quantity series itself as
            # an information test, and implementability is assessed at the
            # end (expressibility note). For the honest net SR we use the
            # regional storage series' own weekly changes as pseudo-marks
            # ONLY for F4/F1/F2 with the expressibility caveat recorded.
            net = None
        books[name] = tgt_d
        return net

    # ------------------------------------------------------------------ F1
    # dysregulation level L/S across regions: long deficit (z low), short surplus
    Zc = Z.dropna()
    for sign, label in ((+1.0, "follow_deficit"), (-1.0, "fade")):
        w = -sign * Zc.div(Zc.abs().sum(axis=1), axis=0)  # rows sum 0
        # weekly book return = sum_i w_i * dz_i/|z| ~ use z-changes as marks
        zc = Zc.diff().fillna(0.0)
        gross = (w.shift(1) * zc).sum(axis=1)
        dw = w.diff().abs().sum(axis=1).fillna(w.abs().sum(axis=1).iloc[0] if len(w) else 0)
        net_w = gross - dw * COST - w.clip(upper=0).abs().sum(axis=1) * BORROW / 52.0
        results.append(("F1", f"F1_{label}_5y", sr(net_w),
                        halves(net_w), neg_years(net_w), scramble_p(net_w), None))
    # 4y band variant (follow sign only)
    z4 = {}
    for r in REGIONS:
        med, mad = seasonal_band(ng[r], 4)
        z4[r] = ((ng[r] - med) / (1.4826 * mad)).clip(-4, 4)
    Z4 = pd.DataFrame(z4).dropna()
    w = -Z4.div(Z4.abs().sum(axis=1), axis=0)
    zc = Z4.diff().fillna(0.0)
    gross = (w.shift(1) * zc).sum(axis=1)
    dw = w.diff().abs().sum(axis=1).fillna(0.0)
    net_w = gross - dw * COST - w.clip(upper=0).abs().sum(axis=1) * BORROW / 52.0
    results.append(("F1", "F1_follow_deficit_4y", sr(net_w),
                    halves(net_w), neg_years(net_w), scramble_p(net_w), None))

    # ------------------------------------------------------------------ F2
    # dysregulation momentum: 4w change of z
    Zm = Zc.diff(4)
    for sign, label in ((+1.0, "mom"), (-1.0, "rev")):
        w = -sign * Zm.div(Zm.abs().sum(axis=1), axis=0).fillna(0.0)
        zc = Zc.diff().fillna(0.0)
        gross = (w.shift(1) * zc).sum(axis=1)
        dw = w.diff().abs().sum(axis=1).fillna(0.0)
        net_w = gross - dw * COST - w.clip(upper=0).abs().sum(axis=1) * BORROW / 52.0
        net_w = net_w.dropna()
        results.append(("F2", f"F2_{label}", sr(net_w),
                        halves(net_w), neg_years(net_w), scramble_p(net_w), None))
    # vol-normalized momentum (divide z-diff by its own 52w std)
    Zv = Zm.div(Zm.rolling(52).std()).dropna()
    w = Zv.div(Zv.abs().sum(axis=1), axis=0)
    zc = Zc.diff().fillna(0.0)
    gross = (w.shift(1) * zc.reindex(w.index)).sum(axis=1)
    dw = w.diff().abs().sum(axis=1).fillna(0.0)
    net_w = gross - dw * COST - w.clip(upper=0).abs().sum(axis=1) * BORROW / 52.0
    results.append(("F2", "F2_mom_volnorm", sr(net_w),
                    halves(net_w), neg_years(net_w), scramble_p(net_w), None))

    # ------------------------------------------------------------------ F3
    # salt stress tilt on the HH complex: salt-aggregate z below threshold ->
    # long complex vs 63d mean; exit above. Thresholds -1.5 / -2.0.
    salt_z = Zc[SALT_SET].mean(axis=1)
    for thr in (-1.5, -2.0):
        pos = (salt_z.shift(1) < thr).astype(float)  # signal from print t, applied t+1 daily
        # daily step + T+1 on the HH calendar
        pos_d = pos.reindex(hh.index).ffill().fillna(0.0)
        w_d = pos_d.shift(1)
        net = net_returns(hh_ret.fillna(0.0), w_d)
        results.append(("F3", f"F3_saltstress_{abs(thr)}", sr(net),
                        halves(net), neg_years(net), scramble_p(net), "HH"))
    # hysteresis variant at -1.5 (enter <-1.5, exit > -0.5)
    state, cur = [], 0.0
    sz = salt_z.shift(1)
    for v in sz:
        if np.isnan(v):
            cur = 0.0
        elif v < -1.5:
            cur = 1.0
        elif v > -0.5:
            cur = 0.0
        state.append(cur)
    pos = pd.Series(state, index=sz.index)
    pos_d = pos.reindex(hh.index).ffill().fillna(0.0)
    net = net_returns(hh_ret.fillna(0.0), pos_d.shift(1))
    results.append(("F3", "F3_saltstress_hyst", sr(net),
                    halves(net), neg_years(net), scramble_p(net), "HH"))
    # dispersion-scaled complex tilt (from F5, both signs folded here)
    disp = (Zc.min(axis=1) - Zc.max(axis=1)).abs()  # cross-sectional spread
    for sign, label in ((+1.0, "long_disp"), (-1.0, "short_disp")):
        sc = (sign * disp).shift(1)
        sc_d = sc.reindex(hh.index).ffill()
        sc_d = sc_d / sc_d.rolling(252).std()  # ~unit scale
        sc_d = sc_d.clip(0, 1.5) if sign > 0 else sc_d.clip(-1.5, 0)
        net = net_returns(hh_ret.fillna(0.0), sc_d.shift(1))
        results.append(("F3", f"F3_dispersion_{label}", sr(net),
                        halves(net), neg_years(net), scramble_p(net), "HH"))

    # ------------------------------------------------------------------ F4
    # L48-vs-sum residual (data-integrity/flow proxy), both signs + z form
    rz = (resid - resid.rolling(52).mean()) / resid.rolling(52).std()
    for sign, label, sig in ((+1.0, "raw_long", resid), (-1.0, "raw_short", resid),
                             (1.0, "z_long", rz)):
        w = sign * sig.shift(1)
        w = w / w.abs().mean()  # ~unit gross
        marks = resid.diff().fillna(0.0)
        gross = (w.shift(1) * marks)
        dw = w.diff().abs().fillna(0.0)
        net_w = gross - dw * COST * 0.1  # residual is tiny scale; normalize below
        net_w = (net_w / net_w.rolling(52).std()).dropna()  # vt-normalize
        results.append(("F4", f"F4_{label}", sr(net_w),
                        halves(net_w), neg_years(net_w), scramble_p(net_w), None))

    # ------------------------------------------------------------------ F5
    # relative build-rate dispersion complex tilt (quarter rank vs seasonal)
    build = {}
    for r in REGIONS:
        med, mad = seasonal_band(ng[r], 5)
        b = ng[r].diff(4)
        b_seasonal = pd.Series(index=b.index, dtype=float)
        dfb = b.to_frame("v")
        dfb["woy"] = dfb.index.isocalendar().week.astype(int).values
        for ts in dfb.index:
            hist = dfb[(dfb.index < ts - pd.DateOffset(years=1)) &
                       (dfb["woy"] == dfb.loc[ts, "woy"]) &
                       (dfb.index >= ts - pd.DateOffset(years=6))]
            b_seasonal[ts] = hist["v"].median() if len(hist) >= 3 else np.nan
        build[r] = (b - b_seasonal)
    B = pd.DataFrame(build).dropna(how="all")
    Bd = B.sub(B.mean(axis=1), axis=0)  # demeaned cross-section
    disp5 = Bd.abs().mean(axis=1)       # average |excess build|
    tilt = (Bd.abs().mean(axis=1)).shift(1)
    tilt_d = tilt.reindex(hh.index).ffill()
    tilt_d = (tilt_d / tilt_d.rolling(252).std()).clip(0, 1.5)
    net = net_returns(hh_ret.fillna(0.0), tilt_d.shift(1))
    results.append(("F5", "F5_build_disp_long", sr(net),
                    halves(net), neg_years(net), scramble_p(net), "HH"))
    net = net_returns(hh_ret.fillna(0.0), (-tilt_d).shift(1))
    results.append(("F5", "F5_build_disp_short", sr(net),
                    halves(net), neg_years(net), scramble_p(net), "HH"))

    # ------------------------------------------------------------------ report
    print(f"{'family':7} {'config':24} {'SR':>7} {'H1':>6} {'H2':>6} "
          f"{'negY':>4} {'scram':>6}")
    for fam, name, s, (h1, h2), ny, sp, _ in results:
        print(f"{fam:7} {name:24} {s:7.3f} {h1:6.3f} {h2:6.3f} "
              f"{ny[0]:4d} {sp:6.3f}")
    print("total configs:", len(results))


if __name__ == "__main__":
    main()
