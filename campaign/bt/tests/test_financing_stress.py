"""CAMP_BORROW round 4 — bt/financing_stress.py reusable financing-stress tool (TDD RED).

Charter (coordinator standup 2026-09-07 17:2x): extract the R3 scenario ladder into a
reusable tool — given a sleeve/champion NET series + GROSS path, emit the IBKR call-rate
/ borrow-tier stress table (per +1pp rung: ann/SR/MDD delta) as JSON. Validation pins:
  * tool output on the committed champion reproduces the R3 ops JSON
    (campaign/results/CAMP_BORROW_FINANCING_R3.json) to 1e-12;
  * tool output on the pre-costfix stream reproduces the R1/R2 4.5/5.5/6.5% call-rate
    table (-0.84pp geometric ann per +1pp);
  * fail-closed on missing/misaligned inputs.

Single algebra convention, shared with bt/borrow.py and the champion builder:
    net_t(r) = port_t - |dW_t|*bps/1e4 - max(gross_t - 1, 0) * r_t / 252
so re-pricing ONLY the margin term (costs and port are financing-invariant) is exactly
    stressed_t = net_t - max(gross_t - 1, 0) * (r_t - base_rate) / 252
A HIGHER rate must LOWER the net (drag). A stub that adds the delta instead (subsidy) or
flattens a rate PATH to its mean must FAIL these tests; so must a stub that accepts
missing/misaligned inputs.
"""
import json
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from bt.financing_stress import (ANN, DEFAULT_RUNGS, DEFAULT_TIERS, GATE_MDD,
                                 stress_net, rung_ladder, path_scenarios,
                                 borrow_tier_block, stress_table)
from bt.borrow import rate_path, spike_window, borrow_tier_uplift

ROOT = "/Users/daxu/software/world-trader"
R3_JSON = f"{ROOT}/campaign/results/CAMP_BORROW_FINANCING_R3.json"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
R2_STREAM = f"{ROOT}/campaign/agents/chief/coord/CAMP_BORROW/work_r3/champion_committed_e6d8b9c0.csv"
GEAR, RATE, BPS = 1.6, 0.045, 6.4


def _synth(n=500, seed=11, gross=GEAR):
    """Synthetic already-costed net at gross `gross`, priced at RATE=4.5%."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2015-01-01", periods=n)
    g = pd.Series(float(gross), index=idx)
    port = pd.Series(rng.normal(4e-4, 8e-3, n), index=idx)
    to = pd.Series(np.abs(rng.normal(0.02, 0.008, n)), index=idx)
    net = port - to * BPS / 1e4 - np.maximum(g - 1.0, 0.0) * RATE / ANN
    return idx, net, g


# ---------- core algebra: stress_net ----------

def test_stress_net_at_base_rate_is_bit_identical_identity():
    """Pricing at the base rate must return the input net EXACTLY (delta term is 0)."""
    idx, net, g = _synth()
    out = stress_net(net, g, RATE, RATE)
    assert out.equals(pd.Series(net)), "base-rate re-price must be the identity, bit for bit"


def test_stress_net_subtracts_higher_rate_never_subsidizes():
    """+1pp call rate must LOWER the net by exactly (gross-1)*0.01/252 per day.
    RED fixture for the round: a stub that ADDS the delta (margin as a subsidy) or
    charges per-sleeve at full notional fails the exact-value assert here."""
    idx, net, g = _synth(n=50)
    up = stress_net(net, g, 0.055, RATE)
    d = up - net
    assert (d <= 1e-15).all(), "a higher call rate must LOWER net (drag), never raise it"
    expect = -(GEAR - 1.0) * 0.010 / ANN
    assert np.allclose(d, expect, atol=1e-15, rtol=0)
    # and the round trip back down restores the original net exactly
    back = stress_net(up, g, RATE, 0.055)
    assert np.allclose(back, net, atol=1e-15, rtol=0)


def test_stress_net_is_elementwise_not_mean_rate_flattened():
    """A spiked PATH must be charged ON the spike days at the spike rate. Flattening a
    path to its time-mean (classic bug) charges the wrong days — caught here."""
    idx, net, g = _synth(n=8)
    r = rate_path(idx, RATE, {str(idx[3].date()): (0.12, 2)})
    out = stress_net(net, g, r, RATE)
    d = out - net
    moved = d.abs() > 1e-15
    assert list(np.flatnonzero(moved.values)) == [3, 4], "exactly the 2 spike days move"
    assert np.allclose(d.iloc[[3, 4]], -(GEAR - 1) * (0.12 - RATE) / ANN, atol=1e-15)
    # mean-rate flattening would move ALL 8 days: assert it does not
    assert int(moved.sum()) != len(idx)


def test_stress_net_honors_a_varying_gross_path():
    """`gross` is a PATH: each day's stress is proportional to that day's (gross-1)."""
    idx = pd.bdate_range("2020-01-01", periods=4)
    net = pd.Series(0.0, index=idx)
    g = pd.Series([1.6, 1.3, 1.0, 0.8], index=idx)
    out = stress_net(net, g, 0.065, RATE)
    expect = -pd.Series([0.6, 0.3, 0.0, 0.0], index=idx) * 0.020 / ANN
    assert np.allclose(out, expect, atol=1e-15, rtol=0), (
        "de-levered days must feel proportionally less stress; gross<=1 feels none")


def test_stress_net_accepts_float_or_series_rate_only():
    idx, net, g = _synth(n=4)
    assert isinstance(stress_net(net, g, 0.065, RATE), pd.Series)
    assert isinstance(stress_net(net, g, pd.Series(0.065, index=idx), RATE), pd.Series)
    with pytest.raises(ValueError):
        stress_net(net, g, pd.Series(0.065, index=idx[:2]), RATE)  # misaligned path
    with pytest.raises(ValueError):
        stress_net(net, g, [0.065] * 4, RATE)                      # list: no index


# ---------- fail-closed on missing / bad inputs (charter requirement) ----------

@pytest.mark.parametrize("mut", ["net_none", "net_empty", "gross_none", "gross_misaligned",
                                 "gross_nan", "gross_nonpositive", "net_not_series",
                                 "base_rate_none", "bad_rung", "base_not_in_rungs"])
def test_fail_closed_on_missing_or_invalid_inputs(mut):
    idx, net, g = _synth(n=30)
    net = pd.Series(net)
    with pytest.raises(ValueError):
        if mut == "net_none":
            stress_net(None, g, 0.065, RATE)
        elif mut == "net_empty":
            stress_net(pd.Series(dtype=float), g, 0.065, RATE)
        elif mut == "gross_none":
            stress_net(net, None, 0.065, RATE)
        elif mut == "gross_misaligned":
            stress_net(net, g.iloc[:-2], 0.065, RATE)
        elif mut == "gross_nan":
            gg = g.copy(); gg.iloc[5] = np.nan
            stress_net(net, gg, 0.065, RATE)
        elif mut == "gross_nonpositive":
            gg = g.copy(); gg.iloc[5] = 0.0
            stress_net(net, gg, 0.065, RATE)
        elif mut == "net_not_series":
            stress_net(np.asarray(net), g, 0.065, RATE)
        elif mut == "base_rate_none":
            stress_net(net, g, 0.065, None)
        elif mut == "bad_rung":
            rung_ladder(net, g, RATE, rungs=(RATE, -0.01))
        elif mut == "base_not_in_rungs":
            rung_ladder(net, g, RATE, rungs=(0.055, 0.065))


# ---------- rung ladder ----------

def test_rung_ladder_rows_and_deltas_vs_base():
    idx, net, g = _synth()
    rows = rung_ladder(net, g, RATE, rungs=(0.045, 0.055, 0.065, 0.08))
    assert [r["rate"] for r in rows] == [0.045, 0.055, 0.065, 0.08]
    for r in rows:
        for f in ("rate", "margin_drag_ann_pct", "ann", "ann_arith", "sr_d", "mdd",
                  "neg_years", "worst_year", "delta_ann_pp", "delta_ann_arith_pp",
                  "delta_sr_d", "delta_mdd_pp", "gate_moves"):
            assert f in r, f"ladder row missing {f}"
    # base row is the committed pricing, bit-identical
    assert np.allclose(stress_net(net, g, RATE, RATE), net)
    assert rows[0]["delta_ann_pp"] == 0.0 and rows[0]["delta_ann_arith_pp"] == 0.0
    # ARITHMETIC ann delta is EXACTLY -0.60pp per +1pp on a 1.6-gross book (closed form)
    for r in rows[1:]:
        assert abs(r["delta_ann_arith_pp"] + 0.60 * (r["rate"] - RATE) / 0.01) < 1e-9, (
            f"arithmetic slope at {r['rate']:.3f} must be -0.60pp per +1pp")
    # margin bookkeeping: 2.70%/yr at base, +0.60%/yr per +1pp
    assert abs(rows[0]["margin_drag_ann_pct"] - 2.70) < 1e-9
    assert abs(rows[2]["margin_drag_ann_pct"] - 3.90) < 1e-9
    # monotone: higher call rate never raises ann or SR-metric expectations
    assert rows[1]["ann"] < rows[0]["ann"] and rows[2]["ann"] < rows[1]["ann"]


def test_rung_ladder_gate_moves_flag_flips_on_a_broken_book():
    """gate_moves = neg_years>0 or MDD <= -7% must actually fire on a book that breaks.
    seed=49 is chosen because its BASE book is genuinely gate-healthy (MDD -5.37%,
    0 neg years — the default seed's book already breaches -7%, which would make the
    'healthy' assertion vacuous)."""
    idx, net, g = _synth(n=500, seed=49)
    rows = rung_ladder(net, g, RATE, rungs=(RATE, 0.055))
    assert all(r["gate_moves"] is False for r in rows), "healthy synth book must not flag"
    ruined = net.copy()
    ruined.iloc[:20] = -0.02                      # 20x -2% days -> deep drawdown
    rows2 = rung_ladder(ruined, g, RATE, rungs=(RATE,))
    assert rows2[0]["gate_moves"] is True, "a -7%-breaching book must be flagged"


def test_rung_ladder_on_unlevered_book_is_an_honest_noop():
    """A gross-1.0 sleeve pays no margin: every rung must equal base EXACTLY (0 deltas),
    not a fabricated sensitivity."""
    idx, net, _ = _synth(n=100)
    net1 = net + (GEAR - 1) * RATE / ANN          # same book, unlevered: no margin charge
    rows = rung_ladder(net1, pd.Series(1.0, index=idx), RATE, rungs=DEFAULT_RUNGS)
    for r in rows:
        assert r["margin_drag_ann_pct"] == 0.0
        assert r["delta_ann_pp"] == 0.0 and r["delta_ann_arith_pp"] == 0.0
        assert r["delta_sr_d"] == 0.0


# ---------- named rate-path scenarios ----------

def test_path_scenarios_match_spike_window_and_closed_form():
    idx, net, g = _synth(n=400)
    scs = {"crash": dict(rate=0.12, start=str(idx[100].date()), days=30)}
    out = path_scenarios(net, g, RATE, scs)
    row = out["crash"]
    for f in ("rate", "base_rate", "window_start", "window_end", "n_days",
              "extra_margin_drag_pct_of_nav", "ann", "sr_d", "mdd", "neg_years",
              "delta_ann_pp", "delta_sr_d", "delta_mdd_pp", "gate_moves"):
        assert f in row, f"path row missing {f}"
    assert row["window_start"] == str(idx[100].date())
    assert row["n_days"] == 30
    m = spike_window(idx, row["window_start"], 30)
    closed = float(((g[m] - 1.0).clip(lower=0.0) / ANN).sum() * (0.12 - RATE) * 100.0)
    assert abs(row["extra_margin_drag_pct_of_nav"] - closed) < 1e-12
    # row metrics == manual re-price through the same identity
    manual = path_metrics_checked(stress_net(net, g, rate_path(idx, RATE, scs_rate_map(scs)), RATE))
    assert abs(row["ann"] - manual["ann"]) < 1e-15


def scs_rate_map(scs):
    return {s["start"]: (s["rate"], s["days"]) for s in scs.values()}


def path_metrics_checked(r):
    from bt.borrow import path_metrics
    return path_metrics(r)


def test_path_scenarios_fail_closed_on_impossible_window():
    idx, net, g = _synth(n=100)
    with pytest.raises(ValueError):
        path_scenarios(net, g, RATE, {"late": dict(rate=0.12, start=str(idx[-1].date()),
                                                   days=50)})
    with pytest.raises(ValueError):
        path_scenarios(net, g, RATE, {"past": dict(rate=0.12, start="1990-01-01", days=10)})


# ---------- borrow-tier block ----------

def test_borrow_tier_block_matches_borrow_tier_uplift_closed_form():
    # seed=49: base book must be gate-healthy (MDD -5.37%, 0 neg yrs) so gate_moves=False
    # is a real assertion about the TIER stress, not a leftover from an already-broken book
    idx, net, g = _synth(seed=49)
    sn = 0.0103                      # R2's measured diescrack short notional on short days
    rows = borrow_tier_block(net, sn, base_borrow=0.005, tiers=(0.02, 0.08))
    assert [r["tier"] for r in rows] == [0.02, 0.08]
    for r in rows:
        assert abs(r["uplift_bps_yr"]
                   - borrow_tier_uplift(sn, 0.005, r["tier"]) * 1e4) < 1e-12
        assert r["gate_moves"] is False
    # closed form: 0.0103 * (0.08-0.005) = 0.07725%/yr = 7.725 bps (unmasked, all days)
    assert abs(rows[1]["uplift_bps_yr"] - 7.725) < 1e-9


def test_borrow_tier_mask_charges_only_masked_days():
    """R2 census shape: the short leg exists on only ~15.8% of days -> the annual uplift
    must scale by the mask, and the stressed ann must reflect the masked daily charge."""
    idx, net, g = _synth(n=1000, seed=3)
    mask = pd.Series(False, index=idx)
    mask.iloc[::6] = True                       # ~16.7% of days
    rows = borrow_tier_block(net, 0.0103, base_borrow=0.005, tiers=(0.02, 0.08), mask=mask)
    frac = float(mask.mean())
    for r in rows:
        expect_bps = 0.0103 * (r["tier"] - 0.005) * frac * 1e4
        assert abs(r["uplift_bps_yr"] - expect_bps) < 1e-9, "mask must scale the uplift"
    # R2's recorded champion-level numbers: 0.24bps (MEDIUM) / 1.22bps (HARD) at 15.8% days
    mask2_frac = 0.158
    assert abs(0.0103 * 0.015 * mask2_frac * 1e4 - 0.244) < 0.01
    assert abs(0.0103 * 0.075 * mask2_frac * 1e4 - 1.221) < 0.01


def test_borrow_tier_series_short_notional_and_alignment():
    idx, net, g = _synth(n=50)
    sn = pd.Series(0.01, index=idx)
    rows = borrow_tier_block(net, sn, base_borrow=0.005, tiers=(0.02,))
    assert abs(rows[0]["uplift_bps_yr"] - 0.01 * 0.015 * 1e4) < 1e-9
    with pytest.raises(ValueError):
        borrow_tier_block(net, sn.iloc[:-3], base_borrow=0.005, tiers=(0.02,))
    with pytest.raises(ValueError):
        borrow_tier_block(net, -0.01, base_borrow=0.005, tiers=(0.02,))


# ---------- stress_table: the JSON-able deliverable ----------

def test_stress_table_json_round_trip_and_keys():
    idx, net, g = _synth(n=300)
    t = stress_table(net, g, RATE,
                     scenarios={"s": dict(rate=0.12, start=str(idx[50].date()), days=20)},
                     short_notional=0.01, meta={"who": "test"})
    s = json.dumps(t)                          # must be JSON-serializable end to end
    t2 = json.loads(s)
    for k in ("convention", "inputs", "gross_check", "base", "rungs", "rate_paths"):
        assert k in t2 and k in t
    assert "borrow_tiers" in t2 and len(t2["borrow_tiers"]) == len(DEFAULT_TIERS)
    assert isinstance(t2["rungs"][0]["gate_moves"], bool)
    assert t2["inputs"]["n_days"] == 300 and t2["meta"]["who"] == "test"
    # no NaN/Infinity leaks into the JSON (strict parse)
    json.loads(s, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))


def test_stress_table_gross_check_reports_and_flags():
    idx, net, g = _synth(n=50)
    t = stress_table(net, g, RATE)
    assert t["gross_check"]["n_days"] == 50 and t["gross_check"]["gross_min"] > 0
    gb = g.copy(); gb.iloc[10] = np.nan
    with pytest.raises(ValueError):
        stress_table(net, gb, RATE)


def test_stress_table_forwards_borrow_mask_to_tier_block():
    """R2 census shape must survive the table wrapper: a masked short leg scales the
    uplift by the mask fraction, exactly as borrow_tier_block does standalone."""
    idx, net, g = _synth(seed=49)
    mask = pd.Series(False, index=idx)
    mask.iloc[::6] = True
    t = stress_table(net, g, RATE, short_notional=0.0103, base_borrow=0.005,
                     tiers=(0.08,), mask=mask)
    frac = float(mask.mean())
    expect_bps = 0.0103 * 0.075 * frac * 1e4
    assert abs(t["borrow_tiers"][0]["uplift_bps_yr"] - expect_bps) < 1e-9, (
        "stress_table must forward the borrow mask to the tier block, not ignore it")


# ---------- VALIDATION PINS on the real books (skipif: artifacts must exist) ----------

def _load_net(path):
    return pd.read_csv(path, index_col=0, parse_dates=True)["ret"].dropna()


@pytest.mark.skipif(not os.path.exists(R3_JSON), reason="R3 ops JSON not generated")
@pytest.mark.skipif(not os.path.exists(CHAMP), reason="committed champion CSV missing")
def test_tool_reproduces_r3_json_rate_paths_to_1e12():
    """Charter validation #1: tool output on the COMMITTED champion must reproduce every
    R3 rate_paths row (named scenarios AND both oracle windows, priced at their recorded
    placements) to 1e-12."""
    d = json.load(open(R3_JSON))
    net = _load_net(CHAMP)
    g = pd.Series(GEAR, index=net.index)
    for name, row in d["rate_paths"].items():
        r = rate_path(net.index, RATE, {row["window_start"]: (row["rate"], row["n_days"])})
        m = path_metrics_checked(stress_net(net, g, r, RATE))
        for f in ("ann", "sr_d", "mdd"):
            assert abs(m[f] - row[f]) < 1e-12, (
                f"{name}.{f}: tool {m[f]!r} vs R3 JSON {row[f]!r}")
        assert m["neg_years"] == row["neg_years"]


@pytest.mark.skipif(not os.path.exists(CHAMP), reason="committed champion CSV missing")
def test_tool_base_rung_equals_committed_champion_exactly():
    """The tool's base rung on the committed CSV must be the committed headline, bit-exact,
    matching the R3 JSON base_headline to 1e-12."""
    net = _load_net(CHAMP)
    g = pd.Series(GEAR, index=net.index)
    rows = rung_ladder(net, g, RATE, rungs=(RATE, 0.055, 0.065))
    assert rows[0]["ann"] == pytest.approx(0.3811446920924182, abs=1e-12)   # ITER15/RAWEW15
    assert rows[0]["sr_d"] == pytest.approx(3.235753053577948, abs=1e-12)
    assert rows[0]["mdd"] == pytest.approx(-0.06561964559361821, abs=1e-12)
    assert rows[0]["neg_years"] == 0 and rows[0]["gate_moves"] is False
    d = json.load(open(R3_JSON))
    assert abs(rows[0]["ann"] - d["base_headline"]["ann"]) < 1e-12
    # arithmetic slope pin: exactly -0.60pp per +1pp on the real champion too
    assert abs(rows[1]["delta_ann_arith_pp"] + 0.60) < 1e-9
    assert abs(rows[2]["delta_ann_arith_pp"] + 1.20) < 1e-9


@pytest.mark.skipif(not os.path.exists(R2_STREAM), reason="pre-costfix stream CSV missing")
def test_tool_reproduces_r1_r2_call_rate_table_minus0p84pp_per_pp():
    """Charter validation #2: on the pre-costfix stream (the R1/R2 book, ann 39.85%),
    the tool's 4.5/5.5/6.5% rungs must reproduce the R1/R2 table: 39.85 / 39.02 / 38.18
    geometric ann, i.e. ~-0.84pp per +1pp geometric, and the EXACT -0.60pp/+1pp
    arithmetic slope (0.6 gross-1)."""
    net = _load_net(R2_STREAM)
    g = pd.Series(GEAR, index=net.index)
    rows = rung_ladder(net, g, RATE, rungs=(0.045, 0.055, 0.065))
    anns = [r["ann"] for r in rows]
    # R2 FINDINGS table (2dp-rounded): 39.85 / 39.02 / 38.18
    for got, want in zip(anns, (0.39851, 0.3902, 0.3818)):
        assert abs(got - want) < 5e-4, f"rung ann {got:.6f} vs R1/R2 table {want}"
    steps = np.diff(anns) * 100.0
    assert abs(steps[0] - (-0.84)) < 0.02 and abs(steps[1] - (-0.83)) < 0.02, (
        f"geometric slope {steps} must be ~-0.84pp per +1pp")
    assert abs(rows[1]["delta_ann_arith_pp"] + 0.60) < 1e-9
    assert abs(rows[2]["delta_ann_arith_pp"] + 1.20) < 1e-9
    # SR/MDD deltas land on the R2 table too (3.296/3.238/3.180; MDD -6.84/-6.85/-6.86%)
    assert abs(rows[0]["sr_d"] - 3.296) < 2e-3 and abs(rows[2]["sr_d"] - 3.180) < 2e-3
    assert abs(rows[0]["mdd"] + 0.0684) < 2e-4 and abs(rows[2]["mdd"] + 0.0686) < 2e-4


# ---------- CLI entry point (r4, this session): fleet-reusable without reading source ----------

def _write_csv(path, idx, ret):
    pd.DataFrame({"ret": ret.values}, index=idx).to_csv(path)


def test_cli_emits_json_table_for_a_net_csv(tmp_path):
    """python3 -m bt.financing_stress --net x.csv --json y.json must emit the full table
    (base + rungs + gross_check) with the base ann matching the CSV's own metrics."""
    import subprocess, sys, json as _json
    idx, net, g = _synth(n=200)
    csv = tmp_path / "net.csv"; out = tmp_path / "table.json"
    _write_csv(csv, idx, net)
    r = subprocess.run([sys.executable, "-m", "bt.financing_stress",
                        "--net", str(csv), "--gear", str(GEAR), "--base-rate", str(RATE),
                        "--json", str(out)],
                       capture_output=True, text=True, cwd=os.path.dirname(
                           os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    assert r.returncode == 0, f"CLI failed: {r.stderr[-400:]}"
    t = _json.loads(out.read_text())
    for k in ("base", "rungs", "gross_check", "inputs", "convention"):
        assert k in t
    from bt.metrics import ann_geo
    assert abs(t["base"]["ann"] - ann_geo(net)) < 1e-12
    assert t["inputs"]["n_days"] == 200 and t["gross_check"]["ok"] is True


def test_cli_fail_closed_nonzero_exit_on_missing_file(tmp_path):
    import subprocess, sys
    r = subprocess.run([sys.executable, "-m", "bt.financing_stress",
                        "--net", str(tmp_path / "nope.csv"), "--json", str(tmp_path / "o.json")],
                       capture_output=True, text=True, cwd=os.path.dirname(
                           os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    assert r.returncode != 0, "missing --net file must exit nonzero (fail-closed)"
    assert "nope.csv" in (r.stderr + r.stdout)
