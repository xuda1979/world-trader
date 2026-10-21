"""HUNT_MACRO2 ROUND 5: macro-regime covariates (Eurostat / BLS / WorldBank keyless
cubes) as champion OVERLAYS - charter corner (a), GATES_CONTRACT_V2 section 8.

Design (pre-registered in tests/test_macro_r5_regime.py BEFORE any evaluation):

Covariates (all trailing-only, PIT lags documented in fetch_regime_data.py):
  hicp_yoy   EA HICP headline annual rate, monthly, m_end+40 cal d lag
  cpi_us_m   US CPI-U SA index yoy, monthly, m_end+45 cal d lag   (2024+ only, keyless BLS)
  ppi_m      PPI commodities index yoy, monthly, m_end+45 cal d lag (2024+ only)
  gdp_yoy    US GDP growth, annual, Y_end+240 cal d lag
  cpi_us_y   US CPI inflation, annual, Y_end+240 cal d lag

Overlay families (book-level; R2/R4 established the dd lives in DEF slots, so
slot-level forms were excluded at pre-registration, matching R2/R4 honesty):
  DEFLev:    m = scale when regime says de-risk (inflation/growth breaching trailing
             expanding quantiles), 1.0 otherwise - V2 §8 battery on the scale grid.
  REGROT:    risk-appetite tilt by the SIGN of a trailing regime composite (CPI
             surprise vs trailing median), +5%/-5% on RISK_ON slots (rotation).

Primary falsifier (HUNT_CREDIT2-R2 / R4 lesson): own-vol control matched to each
macro trigger's on-frequency (fail-closed matcher, tol 0.3pp).

Evidence in work_r5/data/ (5 live keyless sources, sha-pinned fetch_summary.json).

Run: python3 HUNT_MACRO2_round5.py
"""
import json
import os
import sys

sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/"
                   "HUNT_MACRO2/work_r1")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/"
                   "HUNT_MACRO2/work_r2")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/"
                   "HUNT_MACRO2/work_r4")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import HUNT_MACRO2_round2 as R2  # noqa: E402
import HUNT_MACRO2_round4 as R4  # noqa: E402

W5 = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(W5, "data")
OUT = os.path.join(W5, "r5_overlay_results.csv")

SCALES = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]       # pre-registered scale ladder (8g plateau)
Q_LO, Q_HI = 0.15, 0.85                        # expanding-quantile regime bands
ERAS = [(2008, 2013), (2014, 2019), (2020, 2026)]

RAW_FIRST = {                                  # first raw observation per covariate
    "hicp_yoy": "2000-12-01", "cpi_us_m": "2024-01-01", "ppi_m": "2024-01-01",
    "gdp_yoy": "1990-01-01", "cpi_us_y": "1990-01-01",
}
LAGS = {"hicp_yoy": 40, "cpi_us_m": 45, "ppi_m": 45, "gdp_yoy": 240, "cpi_us_y": 240}


# ------------------------------------------------------------------ data / panel
def _read_tv(fname):
    df = pd.read_csv(os.path.join(DATA, fname))
    if "series" in df.columns:                 # BLS layout
        df = df[["period", "value"]]
    df["period"] = df["period"].astype(str)
    return df


def _month_end(ym):
    return (pd.Timestamp(ym + "-01") + pd.offsets.MonthEnd(0))


def pit_monthly(df, lag_days):
    """(ym, value) -> daily PIT series: value for month m becomes visible at
    m_end + lag_days and stays (no revision; trailing-only reads)."""
    idx = pd.to_datetime([_month_end(m) for m in df["period"]]) + pd.Timedelta(days=lag_days)
    s = pd.Series(pd.to_numeric(df["value"], errors="coerce").values, index=idx)
    return s[~s.index.duplicated(keep="last")].sort_index()


def pit_annual(df, lag_days):
    idx = pd.to_datetime([p + "-12-31" for p in df["period"]]) + pd.Timedelta(days=lag_days)
    s = pd.Series(pd.to_numeric(df["value"], errors="coerce").values, index=idx)
    return s[~s.index.duplicated(keep="last")].sort_index()


def regime_panel(cal, upto=None, bump_shift=0):
    """Daily PIT covariate panel on the champion calendar.

   upto:   build as if only data published <= upto existed (truncation invariance).
   bump_shift: drop the LAST k observations of each raw series before construction
            (leak sanity: panel through t must not depend on future obs).
    All derived series are yoy/level as-published (Eurostat RCH_A and WB ZG are
    already rates; BLS indices get a 12m yoy computed TRAILING-only)."""
    cal = pd.DatetimeIndex(cal)

    def clip(s):
        if bump_shift and len(s) > bump_shift:
            s = s.iloc[:-bump_shift]
        if upto is not None:
            s = s[s.index <= pd.Timestamp(upto)]
        return s

    out = pd.DataFrame(index=cal)

    hicp = pit_monthly(_read_tv("eurostat_hicp_ea20_cp00_rch_a.csv"), LAGS["hicp_yoy"])
    out["hicp_yoy"] = clip(hicp).reindex(cal).ffill()

    cpi = pit_monthly(_read_tv("bls_cusr0000sa0.csv"), LAGS["cpi_us_m"])
    yoy = (cpi / cpi.shift(12) - 1.0) * 100      # trailing 12m on PIT stamps: safe
    out["cpi_us_m"] = clip(yoy).reindex(cal).ffill()

    ppi = pit_monthly(_read_tv("bls_wpsfd49207.csv"), LAGS["ppi_m"])
    ppi_yoy = (ppi / ppi.shift(12) - 1.0) * 100
    out["ppi_m"] = clip(ppi_yoy).reindex(cal).ffill()

    gdp = pit_annual(_read_tv("worldbank_usa_gdp_growth.csv"), LAGS["gdp_yoy"])
    out["gdp_yoy"] = clip(gdp).reindex(cal).ffill()

    cpiy = pit_annual(_read_tv("worldbank_usa_cpi_annual.csv"), LAGS["cpi_us_y"])
    out["cpi_us_y"] = clip(cpiy).reindex(cal).ffill()

    return out


# ------------------------------------------------------------------ triggers
def expanding_band_trigger(s, q, side, min_obs=252):
    """PIT band trigger: True when s_t is beyond its EXPANDING quantile q through
    t-1 (trailing-only; shift(1) inside), on `side` in {'hi','lo'}."""
    qv = s.shift(1).expanding(min_periods=min_obs).quantile(q)
    if side == "hi":
        return (s > qv).fillna(False)
    return (s < qv).fillna(False)


def deflev_trigger(panel, cal):
    """De-risk when US CPI (annual, WB) is above its expanding 85th pct OR GDP growth
    below its expanding 15th pct (stagnation/stagflation de-risk). PIT, trailing-only."""
    hi = expanding_band_trigger(panel["cpi_us_y"], Q_HI, "hi")
    lo = expanding_band_trigger(panel["gdp_yoy"], Q_LO, "lo")
    return (hi | lo).reindex(cal).fillna(False)


def deflev2_trigger(panel, cal):
    """Variant: EA HICP above expanding 85th pct (euro inflation shock) OR US GDP
    below expanding 15th pct."""
    hi = expanding_band_trigger(panel["hicp_yoy"], Q_HI, "hi")
    lo = expanding_band_trigger(panel["gdp_yoy"], Q_LO, "lo")
    return (hi | lo).reindex(cal).fillna(False)


def deflev3_trigger(panel, cal):
    """Variant on the short BLS monthly spans (2024+ only; span-disciplined as such):
    US CPI yoy above its expanding 85th pct."""
    hi = expanding_band_trigger(panel["cpi_us_m"], Q_HI, "hi", min_obs=60)
    return hi.reindex(cal).fillna(False)


def regrot_sign(panel, cal, min_obs=252):
    """Rotation sign: +1 when US CPI yoy (annual) below expanding median (cooling ->
    risk-on), -1 above (heating -> de-risk), 0 in warmup."""
    med = panel["cpi_us_y"].shift(1).expanding(min_periods=min_obs).median()
    s = pd.Series(0.0, index=cal)
    v = panel["cpi_us_y"].reindex(cal)
    s[v < med.reindex(cal)] = 1.0
    s[v > med.reindex(cal)] = -1.0
    return s.fillna(0.0)


# ------------------------------------------------------------------ reporting (V2)
def _sr(x):
    x = x.astype(float).dropna()
    sd = float(x.std(ddof=1))
    return float(x.mean() / sd * np.sqrt(252)) if sd > 0 else np.nan


def era_split(champ, ov, eras=None):
    """V2 §8j: dSR per era. Returns {"2008_2013": {dSR, n, SR_c, SR_o}, ...}."""
    eras = eras or ERAS
    out = {}
    for y0, y1 in eras:
        j = champ.index[(champ.index.year >= y0) & (champ.index.year <= y1)]
        sr_c, sr_o = _sr(champ.loc[j]), _sr(ov.loc[j])
        out[f"{y0}_{y1}"] = dict(dSR=sr_o - sr_c, SR_c=sr_c, SR_o=sr_o, n=len(j))
    return out


def delta_halves(champ, ov):
    """V2 §8f: delta SR by half of the champion window."""
    mid = champ.index[len(champ) // 2]
    out = {}
    for tag, j in [("dSR_H1", champ.index[: len(champ) // 2]),
                   ("dSR_H2", champ.index[champ.index.get_loc(mid):])]:
        out[tag] = _sr(ov.loc[j]) - _sr(champ.loc[j])
    return out


def leak_gate(r, sig):
    """V2 §6 Step 1 wrapper: gates.run(..., leak_check=True, sig=...) explicit.
    Fails closed when sig is None (gates already does; we pin the keys)."""
    from bt import gates
    kw = dict(leak_check=True)
    if sig is not None:
        kw["sig"] = sig
    res = gates.run(r, **kw)
    leak = res.get("leak")
    return dict(leak_ok=res.get("leak_ok"), leak=leak,
                same_period_corr=(leak or {}).get("same_period_corr"),
                composite_pass=res.get("pass"))


def plateau_ok(rows, key, arm, half_of_neighbors=0.5):
    """8g: >= half of the OTHER scale rungs must keep the same raw arm."""
    keep = [r for r in rows if r["name"] != key and r.get("raw_arm")]
    return len(keep) >= half_of_neighbors * (len(rows) - 1)


def perf(net):
    from bt import metrics
    net = net.dropna()
    neg, worst = metrics.neg_years(net)
    return dict(ann=metrics.ann_geo(net), sr=metrics.sharpe_d(net),
                mdd=metrics.max_dd(net), neg=neg, n=len(net),
                h1=metrics.half_split(net)[0], h2=metrics.half_split(net)[1])


# ------------------------------------------------------------------ main grid
def main():
    champ = R2.CHAMP
    net, Wg, df = R2.build_champion()
    pc = perf(champ)
    print(f"champion rebuilt: ann={pc['ann']*100:.4f}% SR={pc['sr']:.4f} "
          f"MDD={pc['mdd']*100:.4f}% neg={pc['neg']} n={pc['n']} "
          f"(committed: 37.1954/3.1810/-6.6922/0)")
    dev = (net.reindex(champ.index) - champ).abs().max()
    print(f"rebuild dev vs committed: {dev:.3e}")

    cal = champ.index
    panel = regime_panel(cal)
    print("\npanel coverage (non-NaN days):")
    for c in panel.columns:
        v = panel[c]
        cov = v.notna().mean()
        print(f"  {c:10s} {100*cov:5.1f}%  span {v.dropna().index.min().date()}.."
              f"{v.dropna().index.max().date()}")

    # ---- triggers + matched own-vol controls
    net_rets = net.diff().fillna(0.0)
    variants = [
        ("DEFLev wb-cpi-hi | wb-gdp-lo", deflev_trigger(panel, cal)),
        ("DEFLev2 hicp-hi | wb-gdp-lo", deflev2_trigger(panel, cal)),
        ("DEFLev3 bls-cpi-hi (2024+ span)", deflev3_trigger(panel, cal)),
    ]
    rows = []
    for name, trig in variants:
        freq = float(trig.mean())
        rows.append(dict(name=f"{name} [ownvol control matched]",
                         trig=R4.ownvol_trigger(
                             net_rets, win=21,
                             qtarget=R4.match_quantile_for_freq(
                                 net_rets, win=21, target_freq=freq, tol=0.003)),
                         control=True, base_name=name))
        rows.append(dict(name=name, trig=trig, control=False, base_name=name))

    out_rows = []
    for v in rows:
        for scale in SCALES:
            # R2 overlay contract: m=1.0 normal exposure, m=scale on de-risk days.
            # [BUG FIX, mine, caught by inspection of first run] v1 built
            # m = trig*scale, which makes the book FLAT (m=0) off-trigger - the
            # -29..-37pp dAnn pathology in the first printed grid.
            m = pd.Series(1.0, index=cal)
            m[v["trig"].reindex(cal).fillna(False).values] = scale
            ov = R2.overlay_book(champ, m)
            po, pcc = perf(ov), pc
            d_ann = po["ann"] - pcc["ann"]
            d_mdd = po["mdd"] - pcc["mdd"]
            d_sr = po["sr"] - pcc["sr"]
            dh = delta_halves(champ, ov)
            es = era_split(champ, ov)
            row = dict(name=v["name"], scale=scale, on_freq=float(v["trig"].mean()),
                       ann=po["ann"], sr=po["sr"], mdd=po["mdd"], neg=po["neg"],
                       d_ann=d_ann, d_mdd=d_mdd, dSR=d_sr,
                       dSR_H1=dh["dSR_H1"], dSR_H2=dh["dSR_H2"],
                       era_dSR_2008_2013=es["2008_2013"]["dSR"],
                       era_dSR_2014_2019=es["2014_2019"]["dSR"],
                       era_dSR_2020_2026=es["2020_2026"]["dSR"],
                       control_flag=v["control"])
            row["raw_arm"] = bool(d_ann >= 0.003 or d_mdd >= 0.005) \
                and po["neg"] == 0 and po["mdd"] > -0.07
            out_rows.append(row)
            print(f"  {v['name']:44s} s={scale:.1f} on={row['on_freq']*100:5.2f}% "
                  f"dAnn={d_ann*100:+7.3f}pp dMDD={d_mdd*100:+6.3f}pp dSR={d_sr:+.3f} "
                  f"neg={po['neg']} raw={row['raw_arm']}"
                  f"{' [CONTROL]' if v['control'] else ''}")

    res = pd.DataFrame(out_rows)
    res.to_csv(OUT, index=False)
    print(f"\nwrote {OUT} ({len(res)} rows)")

    # ---- rotation variant (sign tilt, slot-level RISK_ON only)
    sgn = regrot_sign(panel, cal)
    M = pd.DataFrame(1.0, index=Wg.index, columns=Wg.columns)
    up = (sgn > 0).reindex(Wg.index).fillna(False)
    dn = (sgn < 0).reindex(Wg.index).fillna(False)
    for c in R2.RISK_ON:
        M.loc[up, c] = 1.05
        M.loc[dn, c] = 0.95
    ov = R2.apply_slot_overlay(Wg, df, M)
    po = perf(ov)
    dh, es = delta_halves(champ, ov), era_split(champ, ov)
    print(f"\nREGROT cpi-median tilt (riskon +5%/-5%): ann={po['ann']*100:.3f}% "
          f"dAnn={(po['ann']-pc['ann'])*100:+.3f}pp dMDD={(po['mdd']-pc['mdd'])*100:+.3f}pp "
          f"dSR={po['sr']-pc['sr']:+.4f} neg={po['neg']} "
          f"H halves {dh['dSR_H1']:+.4f}/{dh['dSR_H2']:+.4f} "
          f"eras {[round(es[k]['dSR'],4) for k in es]}")
    regrot_row = dict(name="REGROT cpi-median tilt (riskon +5/-5)", scale=np.nan,
                      on_freq=float((sgn != 0).mean()), ann=po["ann"], sr=po["sr"],
                      mdd=po["mdd"], neg=po["neg"], d_ann=po["ann"] - pc["ann"],
                      d_mdd=po["mdd"] - pc["mdd"], dSR=po["sr"] - pc["sr"],
                      dSR_H1=dh["dSR_H1"], dSR_H2=dh["dSR_H2"],
                      era_dSR_2008_2013=es["2008_2013"]["dSR"],
                      era_dSR_2014_2019=es["2014_2019"]["dSR"],
                      era_dSR_2020_2026=es["2020_2026"]["dSR"],
                      control_flag=False, raw_arm=bool(
                          (po["ann"] - pc["ann"]) >= 0.003
                          or (po["mdd"] - pc["mdd"]) >= 0.005) and po["neg"] == 0)
    res = pd.concat([res, pd.DataFrame([regrot_row])], ignore_index=True)
    res.to_csv(OUT, index=False)

    # ---- V2 §6 leak probe on the champion book itself (baseline; any submission re-runs)
    lg = leak_gate(champ, Wg.sum(axis=1))
    print(f"\nleak_probe(champion, sig=book positions): leak_ok={lg['leak_ok']} "
          f"corr={lg['same_period_corr']}")
    with open(os.path.join(W5, "r5_leak_probe.json"), "w") as f:
        json.dump(lg, f, indent=1, default=str)
    return res


if __name__ == "__main__":
    main()
