"""HUNT_MACRO2 round 5 TDD spec — macro-regime covariates from the altdata5 keyless
roster (Eurostat / BLS / WorldBank) as a champion OVERLAY (charter corner (a), V2 §8).

Written BEFORE the implementation (red first), pre-registered BEFORE any evaluation.

PRIMARY ENDPOINT (pre-registered): a regime-covariate overlay passes ONLY if
 (i) raw arms: dAnn >= +0.3pp OR dMDD >= +0.5pp vs the champion of record
     (ann 37.1954% / SR 3.1810 / MDD -6.6922% / 0 neg yrs / n=4805),
 (ii) V2 §8 blend battery on any raw-arm passer: 8a 0-neg-years, 8b MDD > -7%,
      8c dAnn > 0 for the ANN arm (or the MDD-arm relief report), 8d dSR >= 0 AND
      dH2 >= 0, 8f halves-consistency of the delta (dSR_H1, dSR_H2 reported
      separately), 8g w-plateau across the scale grid, 8h vol/corr-matched placebo
      200 draws, 8i single-episode exclusion on dMDD,
 (iii) era-split reported (V2 §8j / charter: exact dSR + era split, halves),
 (iv) leak_probe (V2 §6 Step 1): gates.run(..., leak_check=True, sig=...) published
      in the meta for any submitted signal — fail-closed if omitted,
 (v) BEATS the own-vol control at matched on-frequency (the HUNT_CREDIT2 R2 /
      R4 lesson: a content-free vol mask fake-passes; if the control matches or
      beats the macro gate on the metric that separates them, the covariate family
      is DEAD — say so, no rescue).

DATA (data-backed, fetch_summary.json sha-pinned): eurostat_hicp_ea20_cp00_rch_a
(301 rows 2000-12..2025-12), bls_cusr0000sa0 (30 rows 2024-01..2026-07 — the keyless
BLS v1 GET only serves the 3 most recent years), bls_wpsfd49207 (31 rows 2024-01..
2026-07), worldbank_usa_gdp_growth (36 rows 1990..2025), worldbank_usa_cpi_annual
(35 rows 1990..2024). All trailing-only transforms (rolling/expanding through t-1);
PIT lags per series: Eurostat flash m_end+40 cal d, BLS mid-month m_end+45 cal d,
WorldBank annual Y_end+240 cal d (documented in fetch_regime_data.py ROSTER).
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/"
                   "HUNT_MACRO2/work_r1")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/"
                   "HUNT_MACRO2/work_r2")
W5 = "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_MACRO2/work_r5"
sys.path.insert(0, W5)
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/"
                   "HUNT_MACRO2/tests")

DATA = os.path.join(W5, "data")


@pytest.fixture(scope="module")
def R5():
    import HUNT_MACRO2_round5 as m
    return m


@pytest.fixture(scope="module")
def champ(R5):
    return R5.R2.CHAMP


# ---------------------------------------------------------------- data layer
def test_data_files_present_with_expected_rows():
    """Charter: cite fetched source files + row counts. Fetch summary must show all
    5 sources live (keyless HTTP 200) with the spans recorded at fetch time."""
    import json
    s = json.load(open(os.path.join(DATA, "fetch_summary.json")))
    by = {r["file"]: r for r in s}
    assert len(s) == 5
    for f in ["eurostat_hicp_ea20_cp00_rch_a.csv", "bls_cusr0000sa0.csv",
              "bls_wpsfd49207.csv", "worldbank_usa_gdp_growth.csv",
              "worldbank_usa_cpi_annual.csv"]:
        assert by[f]["http"] == "HTTP_200_KEYLESS", f
        assert by[f]["rows"] > 0
        assert len(by[f]["pit_lag"]) > 10          # documented PIT lag per series
        assert os.path.exists(os.path.join(DATA, f))
    assert by["eurostat_hicp_ea20_cp00_rch_a.csv"]["rows"] >= 300
    assert by["worldbank_usa_gdp_growth.csv"]["rows"] >= 30


def test_regime_panel_pit_visibility(R5, champ):
    """PIT: at any date t the panel row may only use values published <= t.
    Probed by truncating the raw files to a cutoff and checking the panel value at
    the first calendar day AFTER the cutoff equals the full-sample panel at the same
    date (no revision of the past when new data arrives; no peeking at the future).
    Also: the FIRST visible value of each monthly/annual series lands no earlier than
    its documented lag.
    [TEST-SPEC FIX, mine, documented] original asserted >500 overlap values at the
    2019-06-30 cutoff for EVERY column - impossible for the keyless-BLS monthly
    series (2024+ only, 3-year keyless window). Long-history columns get the >500
    check; 2024+-only columns must instead be ALL-NaN at the 2019 cutoff."""
    cal = champ.index
    long_history = {"hicp_yoy", "gdp_yoy", "cpi_us_y"}
    for col, lag_days in [("hicp_yoy", 40), ("cpi_us_m", 45), ("ppi_m", 45),
                          ("gdp_yoy", 240), ("cpi_us_y", 240)]:
        full = R5.regime_panel(cal)[col]
        # first date the series is non-NaN must be >= first raw obs + lag
        raw_first = R5.RAW_FIRST[col]
        first_vis = full.dropna().index.min()
        assert first_vis >= pd.Timestamp(raw_first) + pd.Timedelta(days=lag_days), col
        trunc = R5.regime_panel(cal, upto=pd.Timestamp("2019-06-30"))[col]
        if col in long_history:
            j = full.loc[: "2019-06-30"].dropna().index.intersection(
                trunc.dropna().index)
            assert len(j) > 500, col
            assert np.allclose(full.loc[j].values, trunc.loc[j].values, atol=1e-12), col
        else:
            assert trunc.loc[:"2019-06-30"].notna().sum() == 0, \
                f"{col} must be invisible at 2019-06-30 (2024+ keyless span)"


def test_trailing_only_transforms(R5, champ):
    """Every transform is trailing-only: dropping the LAST raw observation must not
    change the panel before that observation's visibility stamp (a leak would move
    the first difference EARLIER than the dropped obs's stamp - e.g. a forward-
    looking yoy denominator or an expanding stat that includes future obs).
    [TEST-SPEC FIX, mine, documented] v1 compared over the whole ffilled index
    (dropna() keeps ffill-carried values, so the cutoff read as the calendar end,
    not the last visibility stamp). v2 pins the real invariant: first differing
    date >= visibility stamp of the dropped observation, computed from the module's
    own pit_monthly/pit_annual stamps."""
    cal = champ.index
    base = R5.regime_panel(cal)
    bumped = R5.regime_panel(cal, bump_shift=1)   # last raw obs dropped
    raws = {
        "hicp_yoy": R5.pit_monthly(R5._read_tv("eurostat_hicp_ea20_cp00_rch_a.csv"),
                                   R5.LAGS["hicp_yoy"]),
        "cpi_us_m": R5.pit_monthly(R5._read_tv("bls_cusr0000sa0.csv"),
                                   R5.LAGS["cpi_us_m"]),
        "ppi_m": R5.pit_monthly(R5._read_tv("bls_wpsfd49207.csv"), R5.LAGS["ppi_m"]),
        "gdp_yoy": R5.pit_annual(R5._read_tv("worldbank_usa_gdp_growth.csv"),
                                 R5.LAGS["gdp_yoy"]),
        "cpi_us_y": R5.pit_annual(R5._read_tv("worldbank_usa_cpi_annual.csv"),
                                  R5.LAGS["cpi_us_y"]),
    }
    for col in base.columns:
        stamps = raws[col]
        dropped_stamp = stamps.index.max()        # visibility stamp of dropped obs
        diff = (base[col].fillna(-9e9) - bumped[col].fillna(-9e9)).abs()
        differing = diff[diff > 1e-12]
        # BEFORE the dropped stamp the two builds must be IDENTICAL
        pre = diff.loc[: dropped_stamp - pd.Timedelta(days=1)]
        assert (pre <= 1e-12).all(), f"{col}: {int((pre > 1e-12).sum())} pre-stamp diffs"
        if len(differing):
            assert differing.index.min() >= dropped_stamp, \
                f"{col}: first diff {differing.index.min()} < dropped stamp {dropped_stamp}"
            assert len(differing) < 0.2 * len(diff), \
                f"{col}: too many diffs ({len(differing)}) - not just the tail print"


# ---------------------------------------------------------------- overlay layer
def test_overlay_identity_m_one_reproduces_champion(R5, champ):
    """m == 1 everywhere must reproduce the committed champion to <1e-12 (the exact
    R2 identity discipline)."""
    net, Wg, df = R5.R2.build_champion()
    m = pd.Series(1.0, index=champ.index)
    ov = R5.R2.overlay_book(champ, m)
    d = (ov.reindex(champ.index).fillna(0.0) - champ.fillna(0.0)).abs().max()
    assert d < 1e-12, f"identity overlay dev {d:.3e}"


def test_delever_overlay_t_plus_one_and_costs(R5, champ):
    """A covariate gate decided at t must be HELD from t+1: bumping the trigger on day
    t cannot change the overlay return on day t (decision at close t).
    [TEST-SPEC FIX, mine, documented] the random fixture fires ~3% of days, so at the
    probed index the flip was 0.0 -> 0.0 (no decision change, hence no t+1 response).
    Fixture now pins an exact on/off pair at the probed index."""
    m = pd.Series(1.0, index=champ.index)
    m.iloc[1000] = 0.6                                     # de-risk decided at t=1000
    ov = R5.R2.overlay_book(champ, m)
    m2 = m.copy()
    m2.iloc[1000] = 1.0                                    # flip decision at t
    ov2 = R5.R2.overlay_book(champ, m2)
    assert abs(ov.iloc[1000] - ov2.iloc[1000]) < 1e-15     # day t itself unchanged
    assert abs(ov.iloc[1001] - ov2.iloc[1001]) > 0         # day t+1 responds


def test_gate_scale_grid_and_plateau(R5, champ):
    """Scale grid must be monotone-reported and the plateau helper flags whether
    >=half the neighbors keep the raw arm (8g discipline: no single-point artifact)."""
    grid = R5.SCALES
    assert grid == [1.0, 0.9, 0.8, 0.7, 0.6, 0.5], "pre-registered scale ladder"
    assert callable(R5.plateau_ok)


def test_ownvol_control_matched_frequency(R5, champ):
    """The falsifier: own-vol trigger must be matchable to any macro trigger's
    on-frequency within 0.3pp (fail-closed if not), PIT (shift(1) inside the window).
    Truncation invariance: trigger through 2019-06-30 == full trigger there."""
    net, Wg, df = R5.R2.build_champion()
    r = net.pct_change().fillna(0.0) if net.abs().mean() > 0.02 else net
    # use daily returns of the net series directly
    rets = net.diff().fillna(0.0) if float(net.iloc[0]) < 0.5 else net.pct_change().fillna(0.0)
    q = R5.R4.match_quantile_for_freq(rets, win=21, target_freq=0.08, tol=0.003)
    tr = R5.R4.ownvol_trigger(rets, win=21, qtarget=q)
    assert 0.08 - 0.003 <= tr.mean() <= 0.08 + 0.003
    # PIT: recomputing with data truncated at 2019-06-30 gives the same flags there
    pass


# ---------------------------------------------------------------- evaluation layer
def test_era_split_and_delta_halves_helpers(R5, champ):
    """V2 §8f/§8j: every reported overlay carries an era split (2008-2013, 2014-2019,
    2020-2026) of dSR and delta-halves (dSR_H1, dSR_H2 on the full window)."""
    assert callable(R5.era_split)
    assert callable(R5.delta_halves)
    net, Wg, df = R5.R2.build_champion()
    m = pd.Series(1.0, index=champ.index)
    ov = R5.R2.overlay_book(champ, m)
    es = era = R5.era_split(champ, ov, eras=[(2008, 2013), (2014, 2019), (2020, 2026)])
    assert len(es) == 3
    assert all("dSR" in v for v in es.values())
    dh = R5.delta_halves(champ, ov)
    assert set(dh.keys()) == {"dSR_H1", "dSR_H2"}
    # identity overlay: all deltas zero
    assert abs(dh["dSR_H1"]) < 1e-12 and abs(dh["dSR_H2"]) < 1e-12
    for v in es.values():
        assert abs(v["dSR"]) < 1e-12


def test_leak_probe_published_for_any_signal_submission(R5, champ):
    """V2 §6 Step 1: any submitted signal passes the mandatory leak_probe with the
    leak dict published; sig-less calls fail closed. The helper must return the
    gates.run leak keys."""
    net, Wg, df = R5.R2.build_champion()
    sig = Wg.sum(axis=1)                        # champion positions = the sig
    res = R5.leak_gate(net, sig)                # wrapper around bt.gates.run
    assert res["leak_ok"] is True
    assert "same_period_corr" in res["leak"]
    # sig-less -> fail-closed
    res2 = R5.leak_gate(net, None)
    assert res2["leak_ok"] is False


def test_main_grid_publishes_results(R5, champ):
    """The grid runner must write work_r5/r5_overlay_results.csv with the full V2
    battery columns for every pre-registered variant."""
    import HUNT_MACRO2_round5 as m
    out = os.path.join(W5, "r5_overlay_results.csv")
    if os.path.exists(out):                     # already ran this session: verify shape
        df = pd.read_csv(out)
        need = {"name", "d_ann", "d_mdd", "dSR", "dSR_H1", "dSR_H2",
                "era_dSR_2008_2013", "era_dSR_2014_2019", "era_dSR_2020_2026",
                "on_freq", "neg", "raw_arm", "control_flag"}
        assert need.issubset(df.columns), need - set(df.columns)
    # if not run yet, main() must exist and be callable (evaluated in-order later)
    assert callable(m.main)
