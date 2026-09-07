"""AUDIT_RECON round 3 — ACCEPTANCE TOOL tests for bt/verify_champion.py.

Charter: build the re-emit ACCEPTANCE TOOL, independent of engine internals, verifying
  byte-repro from builder arithmetic; FULL-|dW| cost reconciliation from the weights
  themselves (own algebra, NOT engine.cost_turnover); causality (weights == f(nav.shift(1)));
  daily gross <= gear; negy + MDD + worst-year gates. Exit 0/1, JSON report, fail-closed on
  missing input. TDD here on a synthetic 3-sleeve mini-champion fixture: GREEN on the honest
  build, RED on each injected defect (half-turn cost, same-day weights, gross 1.7, one neg
  year) + missing-input fail-closed.

Fixture construction mirrors the CHAMPION RECIPE (rawew13v2_build semantics: IS-SR^P relw,
nav-drift row-normalized weights, nav.shift(1) causal, full |dW| x 6.4bp with day-1 entry
NOT charged, margin (gear-1)*rate/252) but is written OUTSIDE the tool under test so the
tool's own algebra is what gets exercised.
"""
import json
import os
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "campaign"))

from bt.verify_champion import verify_champion  # noqa: E402

GEAR, RATE, BPS = 1.6, 0.045, 6.4
IS_END = pd.Timestamp("2016-01-01")
P = 0.55
NAMES = ["sa", "sb", "sc"]


# ---------------------------------------------------------------- fixture builders
def _sleeve_frames():
    """3 deterministic sleeves, strongly positive IS SRs (drift dominates noise)."""
    idx = pd.bdate_range("2014-01-01", periods=1250)
    rng = np.random.default_rng(7)
    drift = {"sa": 4.0e-3, "sb": 2.0e-3, "sc": 1.0e-3}
    vol = {"sa": 3.0e-4, "sb": 2.0e-4, "sc": 1.5e-4}
    return pd.DataFrame(
        {n: drift[n] + vol[n] * rng.standard_normal(len(idx)) for n in NAMES}, index=idx
    )


def _is_sr(x):
    x = x.dropna()
    if len(x) < 200 or x.std(ddof=1) <= 1e-12:
        return 0.0
    return float(x.mean() / x.std(ddof=1) * np.sqrt(252))


def _relw(df):
    isr = df[df.index < IS_END]
    return pd.Series({n: max(_is_sr(isr[n]), 0.0) ** P for n in NAMES})


def _weights_path(df, relw, causal=True):
    """Champion weight path per the recipe (shift(1) = causal; False = same-day leak)."""
    nav = (1 + df.fillna(0)).cumprod()
    if causal:
        nav = nav.shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(NAMES)
    return d2 * (GEAR / len(NAMES))


def _net_from(df, W, cost="full", gear=GEAR):
    port = (df.fillna(0).values * W.values).sum(axis=1)
    dW = W.diff().abs().sum(axis=1).fillna(0.0)  # day-1 entry NOT charged (recipe convention)
    factor = {"full": 1.0, "half": 0.5}[cost]
    return pd.Series(
        port - dW * factor * BPS / 1e4 - max(gear - 1, 0) * RATE / 252, index=df.index
    )


def _write_fixture(tmpdir, df, W, net, names=NAMES):
    cpath = os.path.join(tmpdir, "champ.csv")
    net.to_frame("ret").to_csv(cpath, index_label="date")
    wpath = os.path.join(tmpdir, "relw.csv")
    pd.DataFrame({"relw": [0.0] * len(names)}, index=names).to_csv(wpath, index_label="name")
    relw = _relw(df)
    pd.DataFrame({"relw": relw}).to_csv(wpath, index_label="name")
    spaths = {}
    for n in names:
        p = os.path.join(tmpdir, f"sleeve_{n}.csv")
        df[n].to_frame("ret").to_csv(p, index_label="date")
        spaths[n] = p
    return cpath, wpath, spaths


@pytest.fixture
def honest_fixture(tmp_path):
    df = _sleeve_frames()
    W = _weights_path(df, _relw(df), causal=True)
    return _write_fixture(str(tmp_path), df, W, _net_from(df, W))


def _defect_fixture(tmp_path, causal=True, cost="full", gear=GEAR, year_mult=None):
    df = _sleeve_frames()
    if year_mult is not None:
        yr, m = year_mult
        mask = df.index.year == yr
        df.loc[mask, :] = df.loc[mask, :] * m
    W = _weights_path(df, _relw(df), causal=causal)
    net = _net_from(df, W, cost=cost, gear=gear)
    return _write_fixture(str(tmp_path), df, W, net)


# ---------------------------------------------------------------- GREEN: honest build
def test_honest_fixture_passes(honest_fixture):
    cpath, wpath, spaths = honest_fixture
    ok, rep = verify_champion(cpath, wpath, spaths, is_end=IS_END, p_param=P)
    assert ok is True, json.dumps(rep, indent=2, default=str)
    for chk in ["weights_repro", "byte_repro", "cost_reconciliation", "causality",
                "gross", "yearly", "mdd"]:
        assert rep["checks"][chk]["ok"] is True, f"{chk}: {rep['checks'][chk]}"
    # full-|dW| model must be the one that reconciles (half-turn must NOT fit better)
    assert rep["checks"]["cost_reconciliation"]["model"] == "full_dw"


def test_honest_fixture_cli_exit0_json(honest_fixture, tmp_path):
    cpath, wpath, spaths = honest_fixture
    out = os.path.join(str(tmp_path), "rep.json")
    r = subprocess.run(
        [sys.executable, os.path.join(REPO, "bt", "verify_champion.py"),
         "--champion", cpath, "--weights", wpath, "--json", out]
         + [f"--sleeve {n}={p}" for n, p in spaths.items()],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    rep = json.load(open(out))
    assert rep["ok"] is True


# ---------------------------------------------------------------- RED defects
def test_red_half_turn_cost(tmp_path):
    """Half-turn (0.5x|dW|) cost undercharge must be CAUGHT by cost reconciliation."""
    cpath, wpath, spaths = _defect_fixture(str(tmp_path), cost="half")
    ok, rep = verify_champion(cpath, wpath, spaths, is_end=IS_END, p_param=P)
    assert ok is False
    c = rep["checks"]["cost_reconciliation"]
    assert c["ok"] is False
    assert c["model"] == "half_dw", f"tool must diagnose the half-turn model, got {c}"
    assert c["implied_over_full_ratio"] < 0.75  # clearly a 0.5x book, not float noise


def test_red_same_day_weights(tmp_path):
    """Same-day (unshifted nav) weight formation must be CAUGHT by the causality check."""
    cpath, wpath, spaths = _defect_fixture(str(tmp_path), causal=False)
    ok, rep = verify_champion(cpath, wpath, spaths, is_end=IS_END, p_param=P)
    assert ok is False
    cz = rep["checks"]["causality"]
    assert cz["ok"] is False
    # the leaky book must NOT byte-repro against the causal rebuild either
    assert cz["causal_max_dev"] > cz["tol"], "leaky champion must deviate from causal rebuild"
    assert cz["truncation"]["ok"] is False, "same-day weights are not truncation-invariant"


def test_red_gross_17(tmp_path):
    """Gross 1.7 (over the 1.6 capital-real wall) must be CAUGHT by the gross gate."""
    cpath, wpath, spaths = _defect_fixture(str(tmp_path), gear=1.7)
    ok, rep = verify_champion(cpath, wpath, spaths, is_end=IS_END, p_param=P,
                              gear=1.6)  # gate stays at the 1.6 wall while the book is 1.7
    assert ok is False
    g = rep["checks"]["gross"]
    assert g["ok"] is False
    assert g["max"] > 1.6 + 1e-9
    assert g["n_over"] > 0


def test_red_one_neg_year(tmp_path):
    """One negative year must be CAUGHT by the yearly gate (self-consistent rebuild)."""
    cpath, wpath, spaths = _defect_fixture(str(tmp_path), year_mult=(2018, -3.0))
    ok, rep = verify_champion(cpath, wpath, spaths, is_end=IS_END, p_param=P)
    y = rep["checks"]["yearly"]
    assert y["neg_years"] >= 1, json.dumps(y, default=str)
    assert y["ok"] is False
    assert ok is False


# ---------------------------------------------------------------- builder NaN semantics
def test_nan_in_sleeve_file_is_builder_legitimate(tmp_path):
    """In-file NaNs are BUILDER-LEGITIMATE: rawew13v2_build.load() dropna()s per series and
    the arithmetic fillna(0)s inside the frame; is_sr also dropna()s. A champion built FROM
    the NaN-bearing frame must be ACCEPTED and byte-reproduce — the tool must mirror that
    semantics, not reject NaN as corruption (the real brwt* files carry 59 NaNs each and
    the first R3 acceptance run fail-closed-blocked on exactly this)."""
    df = _sleeve_frames()
    df.loc[df.index[3:8], "sa"] = np.nan          # builder: load().dropna() -> NaN in frame
    relw = _relw(df)                              # is_sr dropna()s -> same as clean here
    W = _weights_path(df, relw, causal=True)      # fillna(0) inside nav arithmetic
    net = _net_from(df, W)                        # fillna(0) inside port arithmetic
    cpath, wpath, spaths = _write_fixture(str(tmp_path), df, W, net)
    ok, rep = verify_champion(cpath, wpath, spaths, is_end=IS_END, p_param=P)
    assert ok is True, json.dumps(rep, indent=2, default=str)
    assert rep["checks"]["byte_repro"]["ok"] is True
    assert rep["checks"]["weights_repro"]["ok"] is True


def test_inf_in_sleeve_file_still_fails_closed(honest_fixture):
    """True non-finite corruption (inf) must STILL be rejected — NaN carve-out only."""
    cpath, wpath, spaths = honest_fixture
    inf_path = os.path.join(str(tmp_path) if False else os.path.dirname(cpath),
                            "sleeve_sa_inf.csv")
    s = pd.read_csv(spaths["sa"], index_col=0).iloc[:, 0]
    s.iloc[5] = np.inf
    s.to_frame("ret").to_csv(inf_path, index_label="date")
    ok, rep = verify_champion(cpath, wpath, {**spaths, "sa": inf_path},
                              is_end=IS_END, p_param=P)
    assert ok is False
    assert any("non-finite" in e for e in rep["errors"]), rep["errors"]


# ---------------------------------------------------------------- fail-closed inputs
def test_fail_closed_missing_champion(honest_fixture, tmp_path):
    cpath, wpath, spaths = honest_fixture
    ok, rep = verify_champion(os.path.join(str(tmp_path), "nope.csv"), wpath, spaths,
                              is_end=IS_END, p_param=P)
    assert ok is False
    assert rep["ok"] is False and "missing" in json.dumps(rep).lower()


def test_fail_closed_missing_sleeve(honest_fixture):
    cpath, wpath, spaths = honest_fixture
    short = {n: p for n, p in spaths.items() if n != "sc"}
    ok, rep = verify_champion(cpath, wpath, short, is_end=IS_END, p_param=P)
    assert ok is False
    assert rep["ok"] is False


def test_fail_closed_weights_sleeve_mismatch(honest_fixture):
    """A weights file naming an unknown sleeve (or missing one) must fail closed."""
    cpath, wpath, spaths = honest_fixture
    bad = pd.read_csv(wpath, index_col=0)
    bad.loc["ghost"] = 1.0
    bad_path = wpath.replace("relw.csv", "relw_bad.csv")
    bad.to_csv(bad_path, index_label="name")
    ok, rep = verify_champion(cpath, bad_path, spaths, is_end=IS_END, p_param=P)
    assert ok is False


# ---------------------------------------------------------------- sensitivity (teeth)
def test_cost_check_has_signal_not_vacuous(honest_fixture):
    """On the HONEST book the implied/full ratio must sit at 1.0 (not merely 'not 0.5')."""
    cpath, wpath, spaths = honest_fixture
    ok, rep = verify_champion(cpath, wpath, spaths, is_end=IS_END, p_param=P)
    c = rep["checks"]["cost_reconciliation"]
    assert abs(c["implied_over_full_ratio"] - 1.0) < 1e-6
    assert c["max_dev"] < 1e-12
