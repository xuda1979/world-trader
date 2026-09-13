"""CAMP_BORROW round 3 — financing stress runbook v2 + blend support (TDD RED first).

Charter (coordinator standup 2026-09-07 07:2x):
  (a) call-rate PATH scenarios on the champion via bt/borrow.py: sustained 12%/yr for
      90 trading days (2008-style), 8%/yr for 30 days (2020-style), sustained 6%/yr for
      1 year; report ann/MDD/neg_years per scenario; CAMP_BORROW ops JSON gains a
      rate_paths block + pin tests.
  (b) blend support: bt helper blending levered champion + unlevered sleeve — EXACT
      margin-delta algebra when gross changes. RED fixture: a wrong-margin-sign
      implementation (margin added back as a subsidy) must FAIL these tests.

Convention notes (pinned by tests below):
  * Margin is charged per day on max(gross_t - 1, 0) * r_t / 252 — the rate r_t is now a
    PATH (Series), not a scalar. A constant path must reduce exactly to the round-2
    scalar algebra (and to the committed champion at 4.5%).
  * A blend is a daily-rebalanced constant-mix capital split: blended net return
    B_t = w*N_c,t + (1-w)*N_s,t. Margin on the blended book is charged on the BLENDED
    gross-1 (not re-charged per sleeve): this is an EXACT identity, tested to 1e-12.
"""
import importlib.util
import json
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from bt.borrow import (ANN, GROSS_TOL, margin_daily, margin_ann, gross_exact,
                       rate_path, margin_daily_path, scenario_net, path_metrics,
                       spike_window)
from bt.blend import (blend_gross, blend_margin_daily, blend_margin_ann,
                      blend_nets, blend_rebuild, blend_ladder_row)

ROOT = "/Users/daxu/software/world-trader"
BUILDER = f"{ROOT}/campaign/scripts/rawew13v2_build.py"
JSON_PATH = f"{ROOT}/campaign/results/CAMP_BORROW_FINANCING_R3.json"
CHAMP_PATH = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
GEAR, RATE, BPS = 1.6, 0.045, 6.4
# Book of record: ITER15 correlation-aware minsharpe re-emit (2026-09-11) on RAWEW15-refreshed
# sleeves — FULL |dW|@6.4bps on all 13 sleeves, sha256 ee03f5c096aabb6d. The earlier SR^P
# costfix blob (4358dfab95679b97, ann 37.195%) used the retired weight rule and pre-RAWEW15
# sleeves; any scenario table priced on it is superseded by the re-priced R3 JSON.
# Pinned by test_json_base_headline_is_the_costfix_book_of_record.
CHAMP_SHA16 = "ee03f5c096aabb6d"
BASE_ANN = 0.381144692092          # 38.114% honest (post-ITER15/RAWEW15)
BASE_SR_D = 3.235753
BASE_MDD = -0.065620


def _champ_builder():
    spec = importlib.util.spec_from_file_location("rawew13v2_rb3", BUILDER)
    b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
    return b


def _causal_weights(df, relw):
    """Independent reconstruction of the shipped causal weight stream (nav.shift(1)) —
    same construction as the round-2 test: never derived from `net`, so margin checks
    cannot pass tautologically."""
    k = len(relw)
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * k
    return d2 * (GEAR / k)


def _champ_pieces():
    """(port, to, gross, df) recomputed from the RAW sleeve frame — and the committed
    champion CSV for cross-checking."""
    b = _champ_builder()
    net, relw, gross_b, to, df = b.build()
    Wg = _causal_weights(df, relw)
    port = pd.Series((df.fillna(0).values * Wg.values).sum(axis=1), index=df.index)
    gross = Wg.abs().sum(axis=1)
    to = Wg.diff().abs().sum(axis=1).fillna(0.0)
    committed = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                            index_col=0, parse_dates=True)["ret"]
    return port, to, gross, df, committed


# ---------- (a1) rate paths: elementwise margin on a time-varying call rate ----------

def test_rate_path_constant_reduces_to_scalar_round2_algebra():
    idx = pd.date_range("2020-01-01", periods=5)
    g = pd.Series(GEAR, index=idx)
    flat = rate_path(idx, RATE)
    assert isinstance(flat, pd.Series) and np.allclose(flat, RATE)
    # EXACT reduction: path margin == round-2 scalar margin, elementwise, to 1e-15
    assert np.allclose(margin_daily_path(g, flat), margin_daily(g, RATE), atol=1e-15, rtol=0)


def test_margin_daily_path_is_elementwise_not_mean_rate():
    """A spike must be charged ON the spike days at the spike rate: charging the
    time-AVERAGE rate (a classic flattening bug) gives a different answer."""
    idx = pd.date_range("2020-01-01", periods=4)
    g = pd.Series(GEAR, index=idx)
    r = pd.Series([RATE, 0.12, RATE, RATE], index=idx)
    expect = (GEAR - 1) * pd.Series([RATE, 0.12, RATE, RATE], index=idx) / ANN
    got = margin_daily_path(g, r)
    assert np.allclose(got, expect, atol=1e-15, rtol=0)
    # and it differs from the flattened mean-rate charge on the spike day
    assert got.iloc[1] > (GEAR - 1) * float(r.mean()) / ANN


def test_margin_daily_path_fails_closed_on_misaligned_or_non_series_rate():
    idx = pd.date_range("2020-01-01", periods=3)
    with pytest.raises(ValueError):
        margin_daily_path(pd.Series(GEAR, index=idx), pd.Series(RATE, index=idx[:2]))
    with pytest.raises(ValueError):
        margin_daily_path(pd.Series(GEAR, index=idx), [RATE, RATE, RATE])  # no index


def test_scenario_net_identity_port_minus_costs_minus_path_margin():
    """net_path = port - full|dW|*6.4bps - max(gross-1,0)*r_t/252, elementwise; the ONLY
    term that may move vs base is the margin term (charter: financing stress only)."""
    idx = pd.date_range("2020-01-01", periods=6)
    rng = np.random.default_rng(7)
    port = pd.Series(rng.normal(4e-4, 1e-2, 6), index=idx)
    to = pd.Series(rng.uniform(0, 0.05, 6), index=idx)
    gross = pd.Series(GEAR, index=idx)
    base = scenario_net(port, to, gross, rate_path(idx, RATE), BPS)
    hand = port - to * BPS / 1e4 - (GEAR - 1) * RATE / ANN
    assert np.allclose(base, hand, atol=1e-15, rtol=0)
    # spiking day 2 to 12%: delta vs base must be EXACTLY -(gross-1)*(0.12-0.045)/252 on
    # that day and 0 elsewhere (wrong sign here = subsidy, caught by the sign check)
    r = rate_path(idx, RATE).copy(); r.iloc[2] = 0.12
    spiked = scenario_net(port, to, gross, r, BPS)
    d = (spiked - base)
    assert d.iloc[2] < 0, "a call-rate SPIKE must LOWER net (drag), never raise it"
    assert abs(d.iloc[2] + (GEAR - 1) * (0.12 - RATE) / ANN) < 1e-15
    assert float(d.drop(idx[2]).abs().max()) == 0.0


def test_closed_form_extra_drag_2008_style_pin():
    """2008-style: 12% vs 4.5% for 90 trading days on (gross-1)=0.6 costs
    0.6 * 0.075 * 90/252 = 1.6071...% of NAV in total extra margin — the closed form the
    scenario table must match."""
    extra = (GEAR - 1) * (0.12 - RATE) * 90 / ANN
    assert abs(extra - 0.01607142857142857) < 1e-12
    assert abs((GEAR - 1) * (0.08 - RATE) * 30 / ANN - 0.0025) < 1e-12   # 2020-style: 25bps
    assert abs((GEAR - 1) * (0.06 - RATE) * 1.0 - 0.009) < 1e-12         # 1y at 6%: 90bps/yr


def test_spike_window_anchors_and_counts_trading_days():
    idx = pd.DatetimeIndex([t for t in pd.date_range("2008-09-01", "2009-06-30")
                            if t.weekday() < 5])
    m = spike_window(idx, "2008-09-15", 90)
    assert isinstance(m, pd.Series) and m.dtype == bool
    assert int(m.sum()) == 90, "window must cover exactly 90 TRADING days"
    assert m.idxmax() == pd.Timestamp("2008-09-15")
    assert float(m.sum() / len(m)) < 0.5


# ---------- (a2) real champion: constant path == committed; scenario gates pinned ----------

def test_constant_rate_path_reproduces_committed_champion_exactly():
    """The path machinery at a constant 4.5% must reproduce the committed CSV (independent
    reconstruction) — else the scenario table is not measuring the shipped champion."""
    port, to, gross, df, committed = _champ_pieces()
    net_path = scenario_net(port, to, gross, rate_path(gross.index, RATE), BPS)
    j = pd.concat([committed.rename("c"), net_path.rename("p")], axis=1).dropna()
    dev = float((j.c - j.p).abs().max())
    assert dev < 1e-10, f"path machinery does not reproduce committed champion: {dev:.2e}"


def test_book_of_record_sha_is_the_costfix_champion():
    """Guard: the scenario table is only meaningful against the CURRENT book of record.
    A champion re-emit (like the 11:24 costfix) invalidates every previously published
    number — this test refuses to let a stale JSON silently carry them."""
    import hashlib
    got = hashlib.sha256(open(CHAMP_PATH, "rb").read()).hexdigest()[:16]
    assert got == CHAMP_SHA16, (
        f"champion re-emitted (sha {got} != {CHAMP_SHA16}): round-3 scenario numbers "
        "MUST be re-priced before they carry")


@pytest.mark.skipif(not os.path.exists(JSON_PATH), reason="financing JSON not generated yet")
def test_json_base_headline_is_the_costfix_book_of_record():
    """The JSON's base headline must be the costfix champion (37.195% honest), not the
    superseded 39.85% blob. A JSON still saying 39.85% is stale and must fail."""
    d = json.load(open(JSON_PATH))
    bh = d["base_headline"]
    assert abs(bh["ann"] - BASE_ANN) < 5e-4, f"stale base ann {bh['ann']:.6f} != {BASE_ANN:.6f}"
    assert abs(bh["sr_d"] - BASE_SR_D) < 5e-3
    assert abs(bh["mdd"] - BASE_MDD) < 5e-4
    assert bh["neg_years"] == 0
    assert d["champion_drift"]["worktree_sha256_16"] == CHAMP_SHA16
    assert d["champion_drift"]["drifted"] is False, (
        "worktree and book of record must be the same blob when scenarios are priced")


@pytest.mark.skipif(not os.path.exists(JSON_PATH), reason="financing JSON not generated yet")
def test_json_rate_paths_block_pins_scenarios_and_gates():
    """Charter (a) pin: the ops JSON carries a rate_paths block with the three named
    scenarios + the oracle worst-window bound, each with ann/MDD/neg_years, and every
    scenario stays inside the goal gates (0 negative years, MDD above -7%)."""
    d = json.load(open(JSON_PATH))
    rp = d["rate_paths"]
    for k in ("crash_2008_style_12pct_90d", "covid_2020_style_8pct_30d",
              "hike_cycle_6pct_1y", "oracle_worst_window"):
        assert k in rp, f"rate_paths missing {k}"
    for k, row in rp.items():
        for f in ("rate", "window_start", "window_end", "n_days", "ann", "sr_d",
                  "mdd", "neg_years", "delta_ann_vs_base_pp", "extra_margin_drag_pct_of_nav"):
            assert f in row, f"rate_paths/{k} missing {f}"
        assert row["neg_years"] == 0, f"{k}: a financing path created a negative year"
        assert row["mdd"] > -0.07, f"{k}: MDD {row['mdd']:.4f} breached the -7% goal line"
    # closed-form extra drag must match the JSON's own numbers
    assert abs(rp["crash_2008_style_12pct_90d"]["extra_margin_drag_pct_of_nav"] - 1.607142857142857) < 1e-6
    assert abs(rp["covid_2020_style_8pct_30d"]["extra_margin_drag_pct_of_nav"] - 0.25) < 1e-9
    assert abs(rp["hike_cycle_6pct_1y"]["extra_margin_drag_pct_of_nav"] - 0.90) < 1e-9
    # base headline in the JSON must equal the costfix champion headline
    assert abs(d["base_headline"]["ann"] - BASE_ANN) < 5e-4


@pytest.mark.skipif(not os.path.exists(JSON_PATH), reason="financing JSON not generated yet")
def test_json_oracle_bound_is_the_worst_placement_not_a_random_one():
    d = json.load(open(JSON_PATH))
    rp = d["rate_paths"]
    o = rp["oracle_worst_window"]
    named = rp["crash_2008_style_12pct_90d"]
    assert o["n_days"] == 90 and o["rate"] == 0.12
    assert o["ann"] <= named["ann"], "oracle worst-window must be no better than the 2008 anchoring"
    assert o["window_in_drawdown"] is True, "oracle window must be placed where the book is actually losing"


# ---------- (b) blend: EXACT margin-delta algebra when gross changes ----------

def _synth_books(n=400, seed=3):
    """Champion-like levered book (gross 1.6) + unlevered sleeve (gross 1.0), synthetic."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2015-01-01", periods=n)
    port_c = pd.Series(rng.normal(6e-4, 8e-3, n), index=idx)
    port_s = pd.Series(rng.normal(2e-4, 5e-3, n), index=idx)
    to_c = pd.Series(np.abs(rng.normal(0.02, 0.01, n)), index=idx)
    to_s = pd.Series(np.abs(rng.normal(0.01, 0.005, n)), index=idx)
    net_c = port_c - to_c * BPS / 1e4 - (GEAR - 1) * RATE / ANN
    net_s = port_s - to_s * BPS / 1e4            # unlevered: no margin
    return idx, port_c, port_s, to_c, to_s, net_c, net_s


def test_blend_gross_and_margin_exact_linear_algebra():
    """Blended gross = w*G_c + (1-w)*G_s; with G_c>1>=G_s the blended margin equals
    w * champion margin EXACTLY (the unlevered sleeve carries no margin). A 'charge
    margin on each sleeve separately at full notional' implementation would double it;
    a 'subtract' (rebate) implementation would flip its sign — both fail here."""
    w, g_s = 0.7, 1.0
    assert abs(blend_gross(w, GEAR, g_s) - 1.42) < 1e-15
    got = blend_margin_daily(w, GEAR, g_s, RATE)
    assert abs(got - w * (GEAR - 1) * RATE / ANN) < 1e-15
    assert got > 0, "blended margin must remain a positive DRAG"
    assert abs(blend_margin_ann(w, GEAR, g_s, RATE) - w * 0.027) < 1e-12


def test_blend_margin_floors_at_zero_no_subsidy_below_gross_1():
    """A blend whose gross falls BELOW 1 pays no margin — and must NOT be paid one
    (negative margin = subsidy = the wrong-sign bug this fixture exists to catch)."""
    for w in (0.0, 0.2, 0.5):
        assert blend_margin_daily(w, GEAR, 1.0, RATE) >= 0.0
    # w=0 on a 1.0-gross sleeve: no leverage, no margin
    assert blend_margin_daily(0.0, GEAR, 1.0, RATE) == 0.0
    # a <1-gross sleeve blended at low w stays unlevered -> margin exactly 0
    assert blend_margin_daily(0.1, GEAR, 0.8, RATE) == 0.0   # gross 0.98 < 1


def test_wrong_margin_sign_fixture_subsidized_blend_is_rejected():
    """THE RED FIXTURE. A sign-flipped blender (margin ADDED to the book, i.e. the
    borrow desk pays US) produces a strictly HIGHER net than the true blend. bt's blend
    must match the correct-sign identity and must differ from the subsidized one."""
    idx, port_c, port_s, to_c, to_s, net_c, net_s = _synth_books()
    w = 0.7
    true_b = blend_nets(net_c, net_s, w)
    port_b = w * port_c + (1 - w) * port_s
    to_b = w * to_c + (1 - w) * to_s
    m_b = blend_margin_daily(w, GEAR, 1.0, RATE)
    correct = port_b - to_b * BPS / 1e4 - m_b
    subsidized = port_b - to_b * BPS / 1e4 + m_b          # WRONG sign
    assert np.allclose(true_b, correct, atol=1e-15, rtol=0)
    assert not np.allclose(true_b, subsidized, atol=1e-12)
    # the two differ by exactly 2x the blended margin — sign is unambiguous
    assert np.allclose((subsidized - true_b), 2 * m_b, atol=1e-15, rtol=0)
    # and a blended NET that beats its own gross-of-costs port is impossible
    assert float((true_b - port_b).max()) < 0.0


def test_blend_rebuild_matches_linear_blend_exactly_on_real_champion():
    """On the REAL champion + its unlevered twin (same signals, gross 1.0, no margin):
    linear NAV blend == full rebuild of the blended book (blended gross, blended
    turnover, margin charged ONCE on blended gross-1) to 1e-10. This is the
    margin-delta-algebra-exactness claim, not an approximation."""
    port, to, gross, df, committed = _champ_pieces()
    Wg_gross1 = None  # unlevered twin = same weights normalized to gross 1.0
    b = _champ_builder()
    net_c, relw, _, _, dfb = b.build()
    Wg = _causal_weights(dfb, relw)
    W1 = Wg / GEAR
    port1 = pd.Series((dfb.fillna(0).values * W1.values).sum(axis=1), index=dfb.index)
    to1 = W1.diff().abs().sum(axis=1).fillna(0.0)
    net1 = port1 - to1 * BPS / 1e4
    net_c = net_c.reindex(net1.index)
    for w in (0.9, 0.7, 0.5, 0.3):
        lin = blend_nets(net_c, net1, w)
        reb = blend_rebuild(net_c, net1, w, GEAR, 1.0, RATE, BPS)
        dev = float((lin - reb).abs().max())
        assert dev < 1e-10, f"w={w}: linear blend != rebuilt blend (dev {dev:.2e})"
        # margin-delta algebra: blended margin drag == w * champion margin drag (G_s=1)
        assert abs(blend_margin_ann(w, GEAR, 1.0, RATE) - w * (GEAR - 1) * RATE) < 1e-12


def test_blend_ladder_row_schema_and_monotone_leverage_tradeoff():
    idx = pd.bdate_range("2015-01-01", periods=50)
    row = blend_ladder_row(pd.Series(1e-3, index=idx), pd.Series(5e-4, index=idx),
                           0.8, GEAR, 1.0, RATE, BPS)
    for f in ("w_champ", "gross", "margin_drag_ann_pct", "ann", "sr_d", "mdd", "neg_years"):
        assert f in row, f"blend ladder row missing {f}"
    assert abs(row["w_champ"] - 0.8) < 1e-12 and abs(row["gross"] - 1.48) < 1e-12
    assert abs(row["margin_drag_ann_pct"] - 0.8 * 2.70) < 1e-9


@pytest.mark.skipif(not os.path.exists(JSON_PATH), reason="financing JSON not generated yet")
def test_json_blend_block_present_and_margin_scales_linearly():
    d = json.load(open(JSON_PATH))
    bl = d["blend"]
    assert "convention" in bl and "constant-mix" in bl["convention"]
    rows = bl["ladder"]
    assert {r["w_champ"] for r in rows} >= {1.0, 0.9, 0.8, 0.7, 0.5}
    m = {round(r["w_champ"], 3): r["margin_drag_ann_pct"] for r in rows}
    for w in (0.9, 0.8, 0.7, 0.5):
        assert abs(m[w] - w * m[1.0]) < 1e-9, f"margin drag not linear in w at {w}"
    assert all(rows[i]["gross"] < rows[i - 1]["gross"] for i in range(1, len(rows)))


@pytest.mark.skipif(not os.path.exists(JSON_PATH), reason="financing JSON not generated yet")
def test_json_ops_runbook_carries_rate_path_escalation():
    d = json.load(open(JSON_PATH))
    rb = d["ops_runbook"]
    for k in ("scenario_file", "rate_path_escalation", "gate_move_threshold",
              "repro_command"):
        assert k in rb, f"ops_runbook missing {k}"
    assert "run_financing_r3.py" in rb["repro_command"]
