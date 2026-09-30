#!/usr/bin/env python3
"""HUNT_MACRO2 ROUND 7 (a) — RED-first spec: every published CAMP_SHORT-R6 scorecard
number my own re-derivation must reproduce.

These are pytest tests over MY OWN re-derivation module (r7_repro_engine.py). Nothing
here imports CAMP_SHORT / CAMP_BORROW / CAMP_COST code — only published ARTIFACTS are
read for the "their side" values; the "my side" values come from my own algebra over
the raw sleeve CSVs + champion CSV.

Run:  cd /Users/daxu/software/world-trader && python3 -m pytest
      campaign/agents/chief/coord/HUNT_MACRO2/work_r7/test_r7_repro_published.py -q
"""
import json
import pathlib

import pandas as pd
import pytest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[5]  # .../world-trader

ENGINE = None  # populated by module-scoped fixture


@pytest.fixture(scope="module")
def eng():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "r7_repro_engine", HERE / "r7_repro_engine.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ----------------------------------------------------------------- published claims
# CAMP_SHORT work_r6/r6_borrow_repro.json (75 checks) + r6_cost_repro.json (46 checks)
BORROW = json.load(open(ROOT / "campaign/agents/chief/coord/CAMP_SHORT/work_r6/r6_borrow_repro.json"))
COST = json.load(open(ROOT / "campaign/agents/chief/coord/CAMP_SHORT/work_r6/r6_cost_repro.json"))
LEAK_PUB = json.load(open(ROOT / "campaign/agents/chief/coord/CAMP_COST/work_r5/leak_probe_r5.json"))


def test_published_scorecards_stand_as_claimed():
    """Precondition: the R6 scorecards themselves are internally consistent
    (75/75 match, 0 mismatches; 46 checks 0 mismatches). If the published
    artifacts changed under us, everything below is judged against the new text."""
    assert BORROW["mismatches_count"] == 0
    assert len(BORROW["verdicts"]) == 75
    assert all(v["match"] for v in BORROW["verdicts"].values())
    assert len(COST["mismatches"]) == 0
    assert len(COST["verdicts"]) == 46
    # the escalated scalar-probe flag must be present in the COST artifact
    assert any("+0.2034" in f and "+0.0156" in f for f in COST["flags"])


# ----------------------------------------------------------------- BORROW side
def test_borrow_every_check_reproduces_independently(eng):
    mine = eng.borrow()
    bad = []
    for k, v in BORROW["verdicts"].items():
        if k not in mine:
            bad.append(f"{k}: MISSING from my derivation")
            continue
        dev = abs(mine[k] - v["theirs"])
        if not dev <= v["tol"]:
            bad.append(f"{k}: mine={mine[k]!r} theirs={v['theirs']!r} dev={dev:.3e} tol={v['tol']}")
    assert not bad, "MISMATCH vs published scorecard:\n" + "\n".join(bad)


def test_borrow_check_count_is_75(eng):
    mine = eng.borrow()
    assert len(mine) == 75, f"my derivation covers {len(mine)} checks, expected 75"


def test_borrow_immaterial_figure_0_2195(eng):
    """The charter-named borrow-immaterial figure: champion embedded drag 0.2195 bps/yr."""
    mine = eng.borrow()
    assert abs(mine["B9.embedded_bps_yr"] - 0.2195) <= 5e-4
    assert abs(mine["B11.borrow100_bps_yr"] - 0.2196) <= 5e-4


# ----------------------------------------------------------------- COST side
def test_cost_every_check_reproduces_independently(eng):
    mine = eng.cost()
    bad = []
    for k, v in COST["verdicts"].items():
        if k not in mine:
            bad.append(f"{k}: MISSING from my derivation")
            continue
        dev = abs(mine[k] - v["theirs"])
        if not dev <= v["tol"]:
            bad.append(f"{k}: mine={mine[k]!r} theirs={v['theirs']!r} dev={dev:.3e} tol={v['tol']}")
    assert not bad, "MISMATCH vs published scorecard:\n" + "\n".join(bad)


def test_cost_check_count_is_46(eng):
    mine = eng.cost()
    assert len(mine) == 46, f"my derivation covers {len(mine)} checks, expected 46"


def test_scalar_probe_distinction_reproduces(eng):
    """CHARTER-NAMEd: the escalated CAMP_COST scalar-probe faithful |dWg| +0.2034 vs
    signed +0.0156 distinction must re-derive from raw inputs with my own algebra."""
    m = eng.scalar_probe()
    # faithful aggregate |dWg| on the champion span:
    assert abs(m["faithful_champ_span"]["corr"] - 0.203364329618237) < 1e-9
    assert m["faithful_champ_span"]["argmax"] == -1
    assert m["faithful_champ_span"]["leak"] is False
    assert abs(m["faithful_full_history"]["corr"] - 0.13945926418482243) < 1e-9
    # published pair +0.0156 / p 0.2796:
    pub = LEAK_PUB["scalar_agg_turnover_vs_champ_ret"]
    assert abs(pub["same_period_corr"] - 0.015600155730274267) < 1e-12
    assert abs(pub["same_period_p"] - 0.2795726814471842) < 1e-12
    # the published pair must NOT equal the faithful |dWg| number:
    assert abs(pub["same_period_corr"] - m["faithful_champ_span"]["corr"]) > 0.1
    # nearest construction: signed float-noise sum
    assert abs(m["signed_noise_sum"]["corr"] - pub["same_period_corr"]) < 1.5e-3
    assert abs(m["signed_noise_sum"]["p"] - pub["same_period_p"]) < 1.5e-2
    assert m["signed_noise_sum"]["std"] < 1e-12  # degenerate series
    # and my faithful probe must carry the causal lag-(-1) signature
    assert abs(m["faithful_champ_span"]["lag_m1"] - 0.46123290259832483) < 1e-9


def test_wide_probe_conventions_bracket_published(eng):
    m = eng.wide_probe()
    pub = LEAK_PUB["wide_13sleeve_weights_vs_returns"]
    vals = [v["corr"] for v in m.values()]
    assert min(vals) - 0.005 <= pub["same_period_corr"] <= max(vals) + 0.005
    assert all(v["leak"] is False for v in m.values()) and pub["leak"] is False
    # their lag-(-1) dominates
    assert abs(pub["lag_scan"]["-1"]) == max(abs(v) for v in pub["lag_scan"].values())


def test_champion_of_record_intact(eng):
    """Champion sha + headline must match the R7 charter quote."""
    h, sha = eng.champion_headline()
    assert sha.startswith("4358dfab95679b97")
    assert abs(h["ann"] * 100 - 37.19539675684982) < 1e-9
    assert abs(h["sr"] - 3.180994199561701) < 1e-9
    assert abs(h["mdd"] * 100 + 6.692185534307193) < 1e-9
    assert h["neg"] == 0 and h["n"] == 4805
